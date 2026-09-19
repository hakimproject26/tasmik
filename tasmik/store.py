"""Lapisan data — pangkalan data, tetapan, dan pertanyaan.

Semua yang tahu tentang SQL berada di sini. Skrin (`pelajar.py`,
`rekod.py`, `laporan.py`) tidak pernah menulis SQL sendiri, supaya bentuk
jadual boleh berubah tanpa menyentuh kod paparan.

Data disimpan di `~/.tasmik/` — DI LUAR folder app. Ini penting untuk
kemas kini: arkib kemas kini menimpa kod sahaja, jadi rekod guru tidak
boleh hilang walaupun pemasangan terhenti separuh jalan.
"""

import json
import os
import sqlite3
from datetime import date, datetime

from . import surah

TILAWAH = "tilawah"
HAFAZAN = "hafazan"
JENIS_NAMA = {TILAWAH: "Tilawah", HAFAZAN: "Hafazan"}

DIR_DATA = os.path.join(os.path.expanduser("~"), ".tasmik")
DIR_SANDARAN = os.path.join(DIR_DATA, "sandaran")
DIR_EXPORT = os.path.join(DIR_DATA, "export")
FAIL_DB = os.path.join(DIR_DATA, "tasmik.db")
FAIL_CONFIG = os.path.join(DIR_DATA, "config.json")

# Kunci yang dikenali oleh app. `baca_config()` menapis terhadap senarai
# ini, jadi kunci yang TIDAK disenaraikan di sini akan dibuang secara
# senyap setiap kali config dibaca — tanpa ralat, tanpa amaran, dan tanpa
# sebarang cara guru mengetahuinya. Setiap kunci baharu mesti ditambah di
# sini, bukan hanya ditulis oleh `simpan_config()`.
_CONFIG_LALAI = {
    "sumber_kemas": "",
    "semak_kemas": True,
    # Sukatan hafazan setiap kelas, cth {"Kelas pagi": [78, 79, 80]}.
    # Kunci ialah nama kelas sebagaimana ditaip pada murid.
    "sukatan": {},
}

_CONN = None


# ------------------------------------------------------------------ sambungan

def db():
    global _CONN
    if _CONN is None:
        os.makedirs(DIR_DATA, exist_ok=True)
        _CONN = sqlite3.connect(FAIL_DB)
        _CONN.row_factory = sqlite3.Row
        _CONN.execute("PRAGMA foreign_keys = ON")
    return _CONN


def tutup():
    global _CONN
    if _CONN is not None:
        _CONN.close()
        _CONN = None


def init_db():
    conn = db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS pelajar (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            nama    TEXT    NOT NULL UNIQUE,
            kelas   TEXT,
            aktif   INTEGER NOT NULL DEFAULT 1,
            dicipta TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS rekod (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            pelajar_id  INTEGER NOT NULL REFERENCES pelajar(id) ON DELETE CASCADE,
            tarikh      TEXT    NOT NULL,
            jenis       TEXT    NOT NULL,
            surah_no    INTEGER NOT NULL,
            ayat_dari   INTEGER,
            ayat_hingga INTEGER,
            juzuk       TEXT,
            muka_surat  INTEGER,
            nota        TEXT,
            dicipta     TEXT    NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_rekod_pelajar ON rekod(pelajar_id, tarikh);
        CREATE INDEX IF NOT EXISTS idx_rekod_tarikh  ON rekod(tarikh);
        """
    )
    conn.commit()
    # Jadual yang SUDAH ADA tidak disentuh oleh `CREATE TABLE IF NOT EXISTS`
    # di atas. Pangkalan data di telefon guru dicipta oleh versi lama, jadi
    # lajur baharu mesti ditambah secara eksplisit.
    _naik_taraf()


# ------------------------------------------------------------- naik taraf

# Sandaran dinamakan sempena versi yang MEMPERKENALKAN perubahan itu, bukan
# versi lama — supaya namanya memberitahu apa yang berlaku.
_NAMA_SANDARAN = "tasmik-sebelum-3.0.0.db"


def _lajur(conn, jadual):
    """Nama lajur sesuatu jadual. Set kosong kalau jadual itu tiada."""
    return {b["name"] for b in conn.execute(f"PRAGMA table_info({jadual})")}


def _naik_taraf():
    """Naik taraf pangkalan data lama ke skema v3. True kalau ia berubah.

    Versi sebelum v3 menyimpan tilawah ikut julat ayat, dan `ayat_dari` /
    `ayat_hingga` ialah NOT NULL. Tilawah ikut halaman TIADA julat ayat —
    halaman bukan bilangan ayat — jadi menyimpan nilai palsu di situ akan
    merosakkan `SUM(ayat_hingga - ayat_dari + 1)` dalam ringkasan pelajar.
    Kedua-dua lajur itu mesti jadi nullable, dan SQLite tidak boleh
    melonggarkan NOT NULL pada jadual yang sudah wujud: jadual itu mesti
    dibina semula.

    Ini menyentuh rekod murid sebenar pada telefon guru, jadi ia dilakukan
    dengan berhati-hati yang berlebihan:

      - sandaran fail penuh diambil DAHULU, melalui API sandaran SQLite dan
        bukan salinan fail biasa — salinan fail boleh menangkap fail yang
        separuh ditulis kalau app mati pada saat yang salah
      - semuanya dalam SATU transaksi; sebarang ralat membatalkannya dan
        fail asal tidak disentuh langsung
      - bilangan baris dibandingkan sebelum dan selepas menyalin
      - `foreign_key_check` dijalankan sebelum komit

    Nota: `PRAGMA foreign_keys` tidak boleh diubah di dalam transaksi, jadi
    ia ditetapkan pada sambungan BERASINGAN yang wujud hanya untuk migrasi
    ini. Sambungan utama app tidak diubah sama sekali.
    """
    conn = db()
    lajur = _lajur(conn, "rekod")
    if not lajur or "muka_surat" in lajur:
        # Pangkalan data baharu (sudah skema v3), atau tiada jadual rekod.
        return False

    conn.commit()          # pastikan fail di cakera sudah terkini

    os.makedirs(DIR_SANDARAN, exist_ok=True)
    sandaran = os.path.join(DIR_SANDARAN, _NAMA_SANDARAN)
    if not os.path.exists(sandaran):
        # Ditulis SEKALI sahaja. Menulis ganti bermakna migrasi kedua yang
        # gagal boleh memusnahkan satu-satunya salinan yang baik.
        dst = sqlite3.connect(sandaran)
        try:
            conn.backup(dst)
        finally:
            dst.close()

    mig = sqlite3.connect(FAIL_DB, isolation_level=None)
    try:
        mig.execute("PRAGMA foreign_keys = OFF")
        mig.execute("BEGIN IMMEDIATE")
        mig.execute(
            """
            CREATE TABLE rekod_baharu (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                pelajar_id  INTEGER NOT NULL
                            REFERENCES pelajar(id) ON DELETE CASCADE,
                tarikh      TEXT    NOT NULL,
                jenis       TEXT    NOT NULL,
                surah_no    INTEGER NOT NULL,
                ayat_dari   INTEGER,
                ayat_hingga INTEGER,
                juzuk       TEXT,
                muka_surat  INTEGER,
                nota        TEXT,
                dicipta     TEXT    NOT NULL
            )
            """
        )
        mig.execute(
            """
            INSERT INTO rekod_baharu
                (id, pelajar_id, tarikh, jenis, surah_no, ayat_dari,
                 ayat_hingga, juzuk, muka_surat, nota, dicipta)
            SELECT id, pelajar_id, tarikh, jenis, surah_no, ayat_dari,
                   ayat_hingga, juzuk, NULL, nota, dicipta
            FROM rekod
            """
        )
        lama = mig.execute("SELECT COUNT(*) FROM rekod").fetchone()[0]
        baharu = mig.execute("SELECT COUNT(*) FROM rekod_baharu").fetchone()[0]
        if lama != baharu:
            raise RuntimeError(
                f"Migrasi menyalin {baharu} daripada {lama} baris rekod."
            )
        mig.execute("DROP TABLE rekod")
        mig.execute("ALTER TABLE rekod_baharu RENAME TO rekod")
        rosak = mig.execute("PRAGMA foreign_key_check").fetchall()
        if rosak:
            raise RuntimeError(f"Migrasi menghasilkan {len(rosak)} rekod yatim.")
        mig.execute("CREATE INDEX idx_rekod_pelajar ON rekod(pelajar_id, tarikh)")
        mig.execute("CREATE INDEX idx_rekod_tarikh ON rekod(tarikh)")
        mig.execute("COMMIT")
    except Exception:
        try:
            mig.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        mig.close()

    # Sambungan utama masih memegang skema lama dalam cache-nya.
    tutup()
    db()
    return True


# ------------------------------------------------------------------ tetapan

def baca_config():
    """Baca ~/.tasmik/config.json. Sentiasa pulangkan dict yang lengkap."""
    # Nilai bersarang disalin, bukan dikongsi. `dict()` cetek sahaja: tanpanya
    # `cfg["sukatan"]` ialah objek YANG SAMA dengan lalai dalam
    # `_CONFIG_LALAI` selagi fail config belum pernah menyimpan kunci itu —
    # jadi mengubahnya di skrin tetapan akan mengubah lalai modul, dan
    # perubahan itu muncul semula pada setiap bacaan config selepas itu.
    cfg = {k: (dict(v) if isinstance(v, dict) else v)
           for k, v in _CONFIG_LALAI.items()}
    try:
        with open(FAIL_CONFIG, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            cfg.update({k: v for k, v in data.items() if k in _CONFIG_LALAI})
    except (OSError, ValueError):
        # Fail rosak atau tiada — guna lalai. Tetapan bukan data guru,
        # jadi ia tidak patut menghalang app daripada dibuka.
        pass
    return cfg


def simpan_config(cfg):
    os.makedirs(DIR_DATA, exist_ok=True)
    # Tulis ke fail sementara dahulu, kemudian ganti. Tanpa ini, app yang
    # mati semasa menulis meninggalkan config.json yang separuh siap.
    tmp = FAIL_CONFIG + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.replace(tmp, FAIL_CONFIG)


# ------------------------------------------------------------------ pelajar

def semua_pelajar(hanya_aktif=True):
    sql = "SELECT * FROM pelajar"
    if hanya_aktif:
        sql += " WHERE aktif = 1"
    sql += " ORDER BY nama COLLATE NOCASE"
    return db().execute(sql).fetchall()


def dapat_pelajar(pid):
    return db().execute("SELECT * FROM pelajar WHERE id = ?", (pid,)).fetchone()


def cari_pelajar_nama(nama):
    return db().execute(
        "SELECT * FROM pelajar WHERE nama = ? COLLATE NOCASE", (nama,)
    ).fetchone()


def nama_pelajar(pid):
    p = dapat_pelajar(pid)
    if not p:
        return "(murid dipadam)"
    return p["nama"] + (f" ({p['kelas']})" if p["kelas"] else "")


def tambah_pelajar(nama, kelas=None):
    conn = db()
    cur = conn.execute(
        "INSERT INTO pelajar (nama, kelas, aktif, dicipta) VALUES (?, ?, 1, ?)",
        (nama, kelas or None, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    return dapat_pelajar(cur.lastrowid)


def tambah_pelajar_banyak(senarai):
    """Tambah ramai pelajar sekali gus, dalam SATU transaksi.

    Satu transaksi bukan sekadar kemas — ia menjawab soalan yang guru
    akan tanya kalau sesuatu gagal: "berapa yang sudah masuk?" Jawapannya
    mestilah "semua, atau tiada", bukan "entah, separuh jalan".

    `senarai` ialah jujukan pasangan (nama, kelas). Pulangkan bilangannya.

    Membaling sqlite3.IntegrityError kalau ada nama yang sudah wujud —
    pemanggil sepatutnya menapis dahulu, jadi ini hanya berlaku kalau
    senarai berubah antara semakan dan simpan.
    """
    if not senarai:
        return 0
    conn = db()
    masa = datetime.now().isoformat(timespec="seconds")
    try:
        conn.executemany(
            "INSERT INTO pelajar (nama, kelas, aktif, dicipta) VALUES (?, ?, 1, ?)",
            [(nama, kelas or None, masa) for nama, kelas in senarai],
        )
    except sqlite3.IntegrityError:
        conn.rollback()
        raise
    conn.commit()
    return len(senarai)


def kemas_kini_pelajar(pid, nama, kelas):
    conn = db()
    conn.execute(
        "UPDATE pelajar SET nama = ?, kelas = ? WHERE id = ?",
        (nama, kelas or None, pid),
    )
    conn.commit()


def padam_pelajar(pid):
    conn = db()
    conn.execute("DELETE FROM pelajar WHERE id = ?", (pid,))
    conn.commit()


def bilangan_rekod_pelajar(pid):
    return db().execute(
        "SELECT COUNT(*) FROM rekod WHERE pelajar_id = ?", (pid,)
    ).fetchone()[0]


def jumlah_pelajar():
    return db().execute(
        "SELECT COUNT(*) FROM pelajar WHERE aktif = 1"
    ).fetchone()[0]


def senarai_kelas():
    """[(nama_kelas, bilangan_murid), ...] — disusun mengikut abjad.

    `kelas` ialah teks bebas yang ditaip pada setiap murid; tiada senarai
    kelas yang ditetapkan di mana-mana dalam app ini. Jadi menu kelas
    dibina daripada apa yang benar-benar ada dalam pangkalan data.

    Murid tanpa kelas dikumpulkan di bawah kunci "" dan sentiasa di
    HUJUNG, supaya ia tidak muncul di tengah-tengah kelas sebenar.
    """
    hasil = []
    for b in db().execute(
        """
        SELECT kelas, COUNT(*) AS n FROM pelajar
        WHERE aktif = 1 AND kelas IS NOT NULL AND kelas <> ''
        GROUP BY kelas ORDER BY kelas COLLATE NOCASE
        """
    ):
        hasil.append((b["kelas"], b["n"]))
    kosong = db().execute(
        "SELECT COUNT(*) FROM pelajar WHERE aktif = 1 "
        "AND (kelas IS NULL OR kelas = '')"
    ).fetchone()[0]
    if kosong:
        hasil.append(("", kosong))
    return hasil


# ------------------------------------------------------------------ rekod

def tambah_rekod(pelajar_id, tarikh, jenis, surah_no, dari=None, hingga=None,
                 juzuk=None, nota=None, muka_surat=None):
    """Simpan satu rekod tasmi'.

    Dua bentuk rekod wujud, dan sekurang-kurangnya satu mesti lengkap:

      - **ikut julat ayat** — `dari` dan `hingga` diisi. Ini hafazan, dan
        juga tilawah yang direkod cara lama sebelum v3.
      - **ikut halaman** — `muka_surat` diisi dan julat ayat NULL. Ini
        tilawah sejak v3.0.0. Halaman bukan bilangan ayat, jadi tiada julat
        yang jujur boleh diisi; menyimpan julat palsu akan menggelembungkan
        jumlah ayat dalam laporan.

    Kedua-duanya dikehendaki supaya rekod lama kekal sah dan tidak perlu
    ditukar.
    """
    if muka_surat is None and (dari is None or hingga is None):
        raise ValueError("Rekod mesti ada julat ayat atau muka surat.")
    conn = db()
    cur = conn.execute(
        """
        INSERT INTO rekod
            (pelajar_id, tarikh, jenis, surah_no, ayat_dari, ayat_hingga,
             juzuk, muka_surat, nota, dicipta)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            pelajar_id, tarikh, jenis, surah_no, dari, hingga,
            juzuk, muka_surat, nota or None,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    return cur.lastrowid


def padam_rekod(rid):
    conn = db()
    conn.execute("DELETE FROM rekod WHERE id = ?", (rid,))
    conn.commit()


def cari_rekod(where="", params=(), had=None):
    """Senarai rekod berserta nama pelajar, terbaharu dahulu."""
    sql = """
        SELECT r.*, p.nama AS nama_pelajar, p.kelas
        FROM rekod r JOIN pelajar p ON p.id = r.pelajar_id
    """
    if where:
        sql += " WHERE " + where
    sql += " ORDER BY r.tarikh DESC, r.id DESC"
    if had:
        sql += " LIMIT ?"
        params = tuple(params) + (had,)
    return db().execute(sql, params).fetchall()


def rekod_untuk_eksport():
    # Senarai lajur EKSPLISIT. Lajur baharu tidak muncul di sini dengan
    # sendirinya — tidak seperti `cari_rekod()` yang guna `r.*`. Kalau
    # `r.muka_surat` dilupakan, CSV akan senyap-senyap kehilangan halaman
    # dan tiada apa pun yang gagal.
    return db().execute(
        """
        SELECT p.nama AS nama_pelajar, p.kelas, r.tarikh, r.jenis,
               r.surah_no, r.ayat_dari, r.ayat_hingga, r.juzuk,
               r.muka_surat, r.nota
        FROM rekod r JOIN pelajar p ON p.id = r.pelajar_id
        ORDER BY p.nama COLLATE NOCASE, r.tarikh, r.id
        """
    ).fetchall()


def bilangan_rekod_hari_ini():
    return db().execute(
        "SELECT COUNT(*) FROM rekod WHERE tarikh = ?", (date.today().isoformat(),)
    ).fetchone()[0]


def bilangan_hari_ada_tasmi(sejak_iso):
    return db().execute(
        "SELECT COUNT(DISTINCT tarikh) FROM rekod WHERE tarikh >= ?", (sejak_iso,)
    ).fetchone()[0]


# ------------------------------------------------------------------ ringkasan

def ringkasan_pelajar(pid):
    """Kira statistik seorang pelajar untuk skrin laporan."""
    conn = db()
    hasil = {
        "sesi_tilawah": 0, "ayat_tilawah": 0,
        "sesi_hafazan": 0, "ayat_hafazan": 0,
        "juzuk": set(), "surah_hafazan": set(), "halaman": set(),
        "akhir": None, "akhir_hafazan": None,
    }

    for baris in conn.execute(
        """
        SELECT jenis, COUNT(*) AS sesi,
               SUM(COALESCE(ayat_hingga - ayat_dari + 1, 0)) AS ayat
        FROM rekod WHERE pelajar_id = ? GROUP BY jenis
        """,
        (pid,),
    ):
        if baris["jenis"] == TILAWAH:
            hasil["sesi_tilawah"] = baris["sesi"]
            hasil["ayat_tilawah"] = baris["ayat"] or 0
        else:
            hasil["sesi_hafazan"] = baris["sesi"]
            hasil["ayat_hafazan"] = baris["ayat"] or 0

    for baris in conn.execute(
        """SELECT DISTINCT juzuk FROM rekod
           WHERE pelajar_id = ? AND juzuk IS NOT NULL AND juzuk <> ''""",
        (pid,),
    ):
        hasil["juzuk"] |= surah.hurai_juzuk(baris["juzuk"])

    # Halaman dikira berasingan daripada ayat. Rekod tilawah ikut halaman
    # tiada julat ayat langsung, jadi tanpa kiraan ini laporan akan berkata
    # "0 ayat" bagi murid yang jelas membaca — betul secara teknikal, tetapi
    # mengelirukan sesiapa yang membacanya.
    for baris in conn.execute(
        """SELECT DISTINCT muka_surat FROM rekod
           WHERE pelajar_id = ? AND muka_surat IS NOT NULL""",
        (pid,),
    ):
        hasil["halaman"].add(baris["muka_surat"])

    for baris in conn.execute(
        "SELECT DISTINCT surah_no FROM rekod WHERE pelajar_id = ? AND jenis = ?",
        (pid, HAFAZAN),
    ):
        hasil["surah_hafazan"].add(baris["surah_no"])

    hasil["akhir"] = conn.execute(
        "SELECT * FROM rekod WHERE pelajar_id = ? ORDER BY tarikh DESC, id DESC LIMIT 1",
        (pid,),
    ).fetchone()

    # Hafazan "sampai mana" diukur ikut surah tertinggi, bukan ikut tarikh —
    # kerana murajaah surah lama biasanya direkod kemudian.
    hasil["akhir_hafazan"] = conn.execute(
        """SELECT * FROM rekod WHERE pelajar_id = ? AND jenis = ?
           ORDER BY surah_no DESC, ayat_hingga DESC LIMIT 1""",
        (pid, HAFAZAN),
    ).fetchone()

    return hasil
