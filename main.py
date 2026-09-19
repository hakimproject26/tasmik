#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TASMIK — Rekod Tilawah & Hafazan al-Quran
==========================================
Aplikasi terminal untuk merekod bacaan (tilawah) dan hafazan al-Quran murid.

Dibina untuk berjalan dalam Termux (Android) dan mana-mana terminal Linux.
Hanya guna pustaka asas Python — tiada `pip install` diperlukan.

Cara guna:
    python main.py

Data guru disimpan di:  ~/.tasmik/
Kod app di:             folder ini
"""

import sys
from datetime import date

from tasmik import (eksport, laporan, pelajar, rekod, store, surah,
                    tetapan, ui)

# Hasil semakan kemas kini semasa app dibuka. None = tiada versi baharu.
_KEMAS = None


def skrin_utama(cfg):
    ui.bersih()
    lebar_kotak = ui.lebar()

    print("╭" + "─" * (lebar_kotak - 2) + "╮")
    print("│ " + ui.pad("TASMIK", lebar_kotak - 4) + " │")
    print("│ " + ui.pad("Rekod Tilawah & Hafazan al-Quran", lebar_kotak - 4) + " │")
    print("╰" + "─" * (lebar_kotak - 2) + "╯")

    print()
    ui.maklum(ui.tarikh_my(date.today().isoformat(), dengan_hari=True))
    ui.maklum(f"{store.jumlah_pelajar()} pelajar  ·  "
              f"{store.bilangan_rekod_hari_ini()} rekod hari ini")
    print()

    item = [
        "  1.  Tambah rekod tasmi'",
        "  2.  Rekod terkini",
        "  3.  Pelajar",
        "  4.  Laporan kemajuan",
        "  5.  Export ke CSV",
        "  6.  Sandaran data",
        "  7.  Kemas kini",
        "  8.  Tetapan",
        "",
        "  0.  Keluar",
    ]
    print(ui.kotak(item, lebar_kotak))

    if _KEMAS:
        print()
        ui.amaran(f"Versi baharu {_KEMAS['versi']} tersedia — pilih [7].")
    print()


def main():
    global _KEMAS

    store.init_db()
    # Jadual surah diperiksa SEBELUM apa-apa lagi. Kalau ia rosak, setiap
    # rekod yang disimpan selepas ini akan membawa nombor surah yang salah
    # — lebih baik app enggan dibuka daripada menyimpan data yang cacat.
    surah.semak()

    cfg = store.baca_config()
    _KEMAS = tetapan.semak_awal(cfg)

    while True:
        skrin_utama(cfg)
        pilihan = ui.tanya("Pilihan")
        if pilihan is None:
            continue

        if pilihan == "1":
            rekod.tambah_skrin()
        elif pilihan == "2":
            rekod.senarai_skrin()
        elif pilihan == "3":
            pelajar.skrin()
        elif pilihan == "4":
            laporan.kemajuan_skrin()
        elif pilihan == "5":
            eksport.csv_skrin()
        elif pilihan == "6":
            eksport.sandaran_skrin()
        elif pilihan == "7":
            tetapan.skrin_kemas(cfg)
            _KEMAS = None      # selepas dipasang, penanda ini sudah lapuk
        elif pilihan == "8":
            tetapan.skrin_tetapan(cfg)
        elif pilihan in ("0", "q", "keluar"):
            ui.bersih()
            print()
            print("  Jumpa lagi.  بارك الله فيك")
            print()
            return
        else:
            ui.ralat("Pilihan tidak sah. Sila taip nombor 0-8.")
            ui.jeda()


if __name__ == "__main__":
    try:
        main()
    except ui.InputTamat:
        print("\n  Input tamat. Data anda selamat.\n")
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n  Dibatalkan. Data anda selamat.\n")
        sys.exit(0)
    finally:
        store.tutup()
