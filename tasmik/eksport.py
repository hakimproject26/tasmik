"""Export ke CSV dan sandaran pangkalan data."""

import csv
import os
import sqlite3
from datetime import date, datetime

from . import store, surah, ui


def csv_skrin():
    ui.tajuk("Export ke CSV")
    if not store.semua_pelajar(hanya_aktif=False):
        ui.sebut("Tiada data untuk diexport.")
        ui.jeda()
        return

    os.makedirs(store.DIR_EXPORT, exist_ok=True)
    laluan = os.path.join(store.DIR_EXPORT, f"tasmik-{date.today().isoformat()}.csv")

    baris = store.rekod_untuk_eksport()
    # utf-8-sig supaya Excel membaca huruf beraksen dengan betul. Tanpa
    # tanda itu, nama seperti "Nur Aisyah" kelihatan elok tetapi apa-apa
    # aksara bukan ASCII akan jadi simbol pelik.
    with open(laluan, "w", newline="", encoding="utf-8-sig") as f:
        penulis = csv.writer(f)
        penulis.writerow([
            "Murid", "Kelas", "Tarikh", "Jenis", "Muka Surat", "Surah",
            "No. Surah", "Ayat Dari", "Ayat Hingga", "Bilangan Ayat",
            "Juzuk", "Nota",
        ])
        for r in baris:
            # Rekod tilawah ikut halaman tiada julat ayat. Sel itu dibiarkan
            # KOSONG, bukan diisi sifar: kosong bermakna "tiada julat", dan
            # sifar bermakna "ayat sifar". Dalam Excel, `=SUM()` mengabaikan
            # sel kosong dan mengira sifar — jadi memilih sifar akan
            # merosakkan jumlah ayat guru tanpa sebarang amaran.
            ayat = ("" if r["ayat_dari"] is None
                    else r["ayat_hingga"] - r["ayat_dari"] + 1)
            penulis.writerow([
                r["nama_pelajar"], r["kelas"] or "", r["tarikh"],
                store.JENIS_NAMA.get(r["jenis"], r["jenis"]),
                r["muka_surat"] if r["muka_surat"] else "",
                surah.nama_surah(r["surah_no"]), r["surah_no"],
                r["ayat_dari"] if r["ayat_dari"] is not None else "",
                r["ayat_hingga"] if r["ayat_hingga"] is not None else "",
                ayat,
                r["juzuk"] or "", r["nota"] or "",
            ])

    ui.jaya(f"{len(baris)} rekod diexport.")
    print()
    print(ui.kotak([
        "Fail disimpan di:",
        "  " + laluan,
    ]))
    print()
    ui.maklum("Untuk buka dalam Excel atau Google Sheets di telefon:")
    ui.maklum("  1. Jalankan  termux-setup-storage   (sekali sahaja)")
    ui.maklum("  2. Salin fail ke storan telefon:")
    ui.maklum(f"     cp {laluan} ~/storage/downloads/")
    ui.jeda()


def sandaran_skrin():
    ui.tajuk("Sandaran data")
    if not os.path.exists(store.FAIL_DB):
        ui.sebut("Belum ada pangkalan data untuk disandarkan.")
        ui.jeda()
        return

    os.makedirs(store.DIR_SANDARAN, exist_ok=True)
    cap = datetime.now().strftime("%Y%m%d-%H%M%S")
    laluan = os.path.join(store.DIR_SANDARAN, f"tasmik-{cap}.db")

    # Salinan guna API sqlite, bukan `cp`. Kalau app sedang menulis, menyalin
    # fail mentah boleh menghasilkan fail yang kelihatan elok tetapi rosak.
    # `backup()` menghasilkan pangkalan data yang konsisten walaupun begitu.
    tujuan = sqlite3.connect(laluan)
    try:
        store.db().backup(tujuan)
    finally:
        tujuan.close()

    saiz = os.path.getsize(laluan) / 1024
    ui.jaya("Sandaran berjaya dibuat.")
    print()
    print(ui.kotak([
        "Fail sandaran:",
        "  " + laluan,
        f"  {saiz:.1f} KB",
    ]))

    senarai = sorted(f for f in os.listdir(store.DIR_SANDARAN)
                     if f.startswith("tasmik-"))
    if len(senarai) > 5:
        print()
        ui.maklum(f"Ada {len(senarai)} fail sandaran. Yang lama boleh dibuang:")
        for f in senarai[:-5]:
            ui.maklum("  " + os.path.join(store.DIR_SANDARAN, f))
    ui.jeda()
