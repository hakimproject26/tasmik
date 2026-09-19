"""Ujian untuk migrasi skema pangkalan data (v2 -> v3).

Ini ujian pertama untuk lapisan `store`, dan ia wujud kerana migrasi ialah
satu-satunya bahagian app ini yang boleh memusnahkan rekod murid yang
sebenar. Ia berjalan pada telefon guru, jauh daripada sesiapa yang boleh
membetulkannya.

Setiap ujian di sini membina pangkalan data SKEMA LAMA yang sebenar,
mengisinya dengan baris yang sebenar, menjalankan migrasi, dan kemudian
membandingkan SETIAP baris — bukan sekadar bilangan baris. Bilangan yang
sama dengan kandungan yang berubah ialah kegagalan yang paling teruk,
kerana ia kelihatan berjaya.
"""

import os
import shutil
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasmik import store  # noqa: E402


# Skema tepat seperti yang ditulis versi 2.0.0 — disalin, bukan diringkaskan.
SKEMA_LAMA = """
CREATE TABLE pelajar (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    nama    TEXT    NOT NULL UNIQUE,
    kelas   TEXT,
    aktif   INTEGER NOT NULL DEFAULT 1,
    dicipta TEXT    NOT NULL
);
CREATE TABLE rekod (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pelajar_id  INTEGER NOT NULL REFERENCES pelajar(id) ON DELETE CASCADE,
    tarikh      TEXT    NOT NULL,
    jenis       TEXT    NOT NULL,
    surah_no    INTEGER NOT NULL,
    ayat_dari   INTEGER NOT NULL,
    ayat_hingga INTEGER NOT NULL,
    juzuk       TEXT,
    nota        TEXT,
    dicipta     TEXT    NOT NULL
);
CREATE INDEX idx_rekod_pelajar ON rekod(pelajar_id, tarikh);
CREATE INDEX idx_rekod_tarikh  ON rekod(tarikh);
"""

PELAJAR_LAMA = [
    (1, "Ahmad Zaki", "Kelas pagi", 1, "2026-01-01T08:00:00"),
    (2, "Nurul Huda", "Kelas petang", 1, "2026-01-02T08:00:00"),
    (3, "Siti Aminah", None, 1, "2026-01-03T08:00:00"),
]

REKOD_LAMA = [
    (1, 1, "2026-09-01", "tilawah", 2, 1, 20, "1", "lancar", "2026-09-01T09:00:00"),
    (2, 1, "2026-09-02", "hafazan", 78, 1, 40, "30", None, "2026-09-02T09:00:00"),
    (3, 2, "2026-09-03", "tilawah", 36, 1, 83, "22-23", "perlu ulang", "2026-09-03T09:00:00"),
    (4, 3, "2026-09-04", "hafazan", 67, 1, 30, "29", "", "2026-09-04T09:00:00"),
]


class AsasMigrasi(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="tasmik-uji-")
        store.tutup()
        self._asal = (store.DIR_DATA, store.DIR_SANDARAN, store.DIR_EXPORT,
                      store.FAIL_DB, store.FAIL_CONFIG)
        store.DIR_DATA = self.tmp
        store.DIR_SANDARAN = os.path.join(self.tmp, "sandaran")
        store.DIR_EXPORT = os.path.join(self.tmp, "export")
        store.FAIL_DB = os.path.join(self.tmp, "tasmik.db")
        store.FAIL_CONFIG = os.path.join(self.tmp, "config.json")

    def tearDown(self):
        store.tutup()
        (store.DIR_DATA, store.DIR_SANDARAN, store.DIR_EXPORT,
         store.FAIL_DB, store.FAIL_CONFIG) = self._asal
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _tulis_db_lama(self):
        conn = sqlite3.connect(store.FAIL_DB)
        conn.executescript(SKEMA_LAMA)
        conn.executemany("INSERT INTO pelajar VALUES (?, ?, ?, ?, ?)", PELAJAR_LAMA)
        conn.executemany("INSERT INTO rekod VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         REKOD_LAMA)
        conn.commit()
        conn.close()

    def _baris(self, sql):
        conn = sqlite3.connect(store.FAIL_DB)
        try:
            return [tuple(r) for r in conn.execute(sql)]
        finally:
            conn.close()


class UjianMigrasi(AsasMigrasi):
    def test_setiap_baris_kekal_sama(self):
        """Pemeriksaan paling penting di sini — kandungan, bukan bilangan."""
        self._tulis_db_lama()
        store.init_db()

        lajur = store._lajur(store.db(), "rekod")
        self.assertIn("muka_surat", lajur)

        baharu = self._baris(
            "SELECT id, pelajar_id, tarikh, jenis, surah_no, ayat_dari, "
            "ayat_hingga, juzuk, muka_surat, nota, dicipta FROM rekod ORDER BY id"
        )
        dijangka = [r + (None,) for r in REKOD_LAMA]
        # Susun semula: (id, pid, tarikh, jenis, surah, dari, hingga, juzuk,
        #                 muka_surat, nota, dicipta)
        dijangka = [r[:8] + (None,) + r[8:] for r in REKOD_LAMA]
        self.assertEqual(baharu, dijangka)

    def test_pelajar_tidak_disentuh(self):
        self._tulis_db_lama()
        store.init_db()
        self.assertEqual(self._baris("SELECT * FROM pelajar ORDER BY id"),
                         PELAJAR_LAMA)

    def test_sandaran_diambil(self):
        self._tulis_db_lama()
        store.init_db()
        fail = os.path.join(store.DIR_SANDARAN, store._NAMA_SANDARAN)
        self.assertTrue(os.path.exists(fail), "sandaran tidak diambil")
        # Sandaran mesti mengandungi data LAMA, bukan yang sudah dimigrasi.
        conn = sqlite3.connect(fail)
        try:
            lajur = {r[1] for r in conn.execute("PRAGMA table_info(rekod)")}
            bil = conn.execute("SELECT COUNT(*) FROM rekod").fetchone()[0]
        finally:
            conn.close()
        self.assertNotIn("muka_surat", lajur)
        self.assertEqual(bil, len(REKOD_LAMA))

    def test_dijalankan_dua_kali_tidak_merosakkan(self):
        self._tulis_db_lama()
        self.assertTrue(store._naik_taraf())
        self.assertFalse(store._naik_taraf(), "migrasi kedua tidak dilangkau")
        self.assertEqual(len(self._baris("SELECT * FROM rekod")), len(REKOD_LAMA))

    def test_sandaran_tidak_ditimpa(self):
        """Sandaran kedua yang buruk tidak boleh memusnahkan yang pertama."""
        self._tulis_db_lama()
        store.init_db()
        fail = os.path.join(store.DIR_SANDARAN, store._NAMA_SANDARAN)
        cap = os.path.getmtime(fail)
        store.tutup()
        store.init_db()
        self.assertEqual(os.path.getmtime(fail), cap)

    def test_index_dibina_semula(self):
        self._tulis_db_lama()
        store.init_db()
        nama = {r[0] for r in self._baris(
            "SELECT name FROM sqlite_master WHERE type='index'")}
        self.assertIn("idx_rekod_pelajar", nama)
        self.assertIn("idx_rekod_tarikh", nama)


class UjianSelepasMigrasi(AsasMigrasi):
    def test_rekod_lama_masih_boleh_dibaca(self):
        self._tulis_db_lama()
        store.init_db()
        baris = store.semua_pelajar()
        self.assertEqual(len(baris), 3)
        self.assertEqual(len(store.cari_rekod()), len(REKOD_LAMA))

    def test_tilawah_ikut_halaman(self):
        """Rekod baharu: halaman diisi, julat ayat NULL."""
        self._tulis_db_lama()
        store.init_db()
        rid = store.tambah_rekod(1, "2026-09-19", store.TILAWAH, 12, None, None,
                                 juzuk="13", muka_surat=245)
        r = store.cari_rekod("r.id = ?", (rid,))[0]
        self.assertEqual(r["muka_surat"], 245)
        self.assertIsNone(r["ayat_dari"])
        self.assertIsNone(r["ayat_hingga"])

    def test_rekod_tanpa_ayat_dan_tanpa_halaman_ditolak(self):
        self._tulis_db_lama()
        store.init_db()
        with self.assertRaises(ValueError):
            store.tambah_rekod(1, "2026-09-19", store.TILAWAH, 12)

    def test_ringkasan_tidak_meletup_dengan_ayat_null(self):
        self._tulis_db_lama()
        store.init_db()
        store.tambah_rekod(1, "2026-09-19", store.TILAWAH, 12, None, None,
                           juzuk="13", muka_surat=245)
        s = store.ringkasan_pelajar(1)
        self.assertEqual(s["ayat_tilawah"], 20)      # rekod lama sahaja
        self.assertEqual(s["sesi_tilawah"], 2)
        self.assertEqual(s["halaman"], {245})

    def test_eksport_menyertakan_halaman(self):
        self._tulis_db_lama()
        store.init_db()
        store.tambah_rekod(2, "2026-09-19", store.TILAWAH, 18, None, None,
                           juzuk="15-16", muka_surat=293)
        baris = [r for r in store.rekod_untuk_eksport() if r["muka_surat"]]
        self.assertEqual(len(baris), 1)
        self.assertEqual(baris[0]["muka_surat"], 293)


class UjianDbBaharu(AsasMigrasi):
    def test_db_baharu_terus_skema_v3(self):
        store.init_db()
        self.assertIn("muka_surat", store._lajur(store.db(), "rekod"))

    def test_db_baharu_tiada_sandaran(self):
        store.init_db()
        self.assertFalse(os.path.exists(
            os.path.join(store.DIR_SANDARAN, store._NAMA_SANDARAN)))

    def test_sukatan_tidak_dibuang_oleh_baca_config(self):
        """Perangkap `_CONFIG_LALAI` — kunci yang tiada di situ hilang senyap."""
        cfg = store.baca_config()
        cfg["sukatan"] = {"Kelas petang": [63, 36]}
        store.simpan_config(cfg)
        self.assertEqual(store.baca_config()["sukatan"],
                         {"Kelas petang": [63, 36]})


if __name__ == "__main__":
    unittest.main()
