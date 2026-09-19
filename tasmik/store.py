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

_CONFIG_LALAI = {
    "sumber_kemas": "",
    "semak_kemas": True,
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
            ayat_dari   INTEGER NOT NULL,
            ayat_hingga INTEGER NOT NULL,
            juzuk       TEXT,
            nota        TEXT,
            dicipta     TEXT    NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_rekod_pelajar ON rekod(pelajar_id, tarikh);
        CREATE INDEX IF NOT EXISTS idx_rekod_tarikh  ON rekod(tarikh);
        """
    )
    conn.commit()


# ------------------------------------------------------------------ tetapan

def baca_config():
    """Baca ~/.tasmik/config.json. Sentiasa pulangkan dict yang lengkap."""
    cfg = dict(_CONFIG_LALAI)
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
        return "(pelajar dipadam)"
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


# ------------------------------------------------------------------ rekod

def tambah_rekod(pelajar_id, tarikh, jenis, surah_no, dari, hingga,
                 juzuk=None, nota=None):
    conn = db()
    cur = conn.execute(
        """
        INSERT INTO rekod
            (pelajar_id, tarikh, jenis, surah_no, ayat_dari, ayat_hingga,
             juzuk, nota, dicipta)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            pelajar_id, tarikh, jenis, surah_no, dari, hingga,
            juzuk, nota or None, datetime.now().isoformat(timespec="seconds"),
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
    return db().execute(
        """
        SELECT p.nama AS nama_pelajar, p.kelas, r.tarikh, r.jenis,
               r.surah_no, r.ayat_dari, r.ayat_hingga, r.juzuk, r.nota
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
        "juzuk": set(), "surah_hafazan": set(),
        "akhir": None, "akhir_hafazan": None,
    }

    for baris in conn.execute(
        """
        SELECT jenis, COUNT(*) AS sesi, SUM(ayat_hingga - ayat_dari + 1) AS ayat
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
