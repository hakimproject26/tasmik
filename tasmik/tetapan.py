"""Skrin tetapan dan kemas kini."""

from . import kemas, store, tandatangan, ui, versi


def semak_awal(cfg):
    """Semak versi baharu SEKALI sahaja, semasa app dibuka.

    Tidak pernah menghalang app daripada dibuka: apa-apa kegagalan
    (pelayan mati, alamat kosong, talian perlahan) pulang None, dan menu
    utama terus dipaparkan. Hasilnya disimpan supaya menu boleh
    memberitahu guru tanpa membuat semakan kedua.
    """
    if not cfg.get("semak_kemas", True):
        return None
    sumber = cfg.get("sumber_kemas", "")
    if not sumber:
        return None
    hasil = kemas.semak(sumber)
    if hasil.get("ok") and hasil.get("ada"):
        return hasil
    return None


def _cap_jari():
    """Cap jari kunci yang dipercayai, atau ayat yang menjelaskan ketiadaannya.

    Dipaparkan supaya guru boleh membandingkannya dengan yang dicetak
    `bina.sh`. Kalau dua-dua berbeza, telefon ini memegang kunci yang
    berbeza daripada mesin pembinaan — dan setiap kemas kini akan ditolak.
    """
    cap = tandatangan.cap_jari()
    return cap if cap else "(belum dijana)"


def skrin_tetapan(cfg):
    while True:
        ui.tajuk("Tetapan")
        print(ui.kotak([
            ui.baris_kv("Versi           ", versi.penuh()),
            ui.baris_kv("Semak kemas kini",
                        "Ya" if cfg.get("semak_kemas", True) else "Tidak"),
            ui.baris_kv("Cap jari kunci  ", _cap_jari()),
            "",
            "  1.  Sumber kemas kini",
            "  2.  Semak semasa buka",
            "  3.  Kemas kini sekarang",
            "",
            "  0.  Kembali",
        ]))
        print()
        ui.maklum("Sumber: " + (cfg.get("sumber_kemas") or "(belum ditetapkan)"))
        pilihan = ui.tanya("Pilihan")
        if pilihan is None:
            continue

        if pilihan == "1":
            print()
            ui.maklum("Alamat folder yang ada versi.json dan tasmik.tar.gz.")
            ui.maklum("Contoh: http://192.168.1.10:8001")
            lama = cfg.get("sumber_kemas", "")
            baharu = ui.tanya("Sumber kemas kini ('-' untuk kosongkan)",
                              lama or "-")
            cfg["sumber_kemas"] = "" if baharu == "-" else baharu.strip()
            store.simpan_config(cfg)
            ui.jaya("Sumber disimpan.")
            ui.jeda()

        elif pilihan == "2":
            cfg["semak_kemas"] = not cfg.get("semak_kemas", True)
            store.simpan_config(cfg)
            ui.jaya("Semak semasa buka: "
                    + ("Ya" if cfg["semak_kemas"] else "Tidak"))
            if not cfg["semak_kemas"]:
                ui.maklum("Guna Tetapan ▸ [3] Kemas kini sekarang bila perlu.")
            ui.jeda()

        elif pilihan == "3":
            skrin_kemas(cfg)

        elif pilihan == "0":
            return
        else:
            ui.ralat("Pilihan tidak sah.")
            ui.jeda()


def skrin_kemas(cfg):
    ui.tajuk("Kemas kini")
    sumber = cfg.get("sumber_kemas", "")

    if not sumber:
        ui.amaran("Sumber kemas kini belum ditetapkan.")
        print()
        ui.maklum("Tetapkan di  Tetapan ▸ [1] Sumber kemas kini.")
        ui.jeda()
        return

    print()
    ui.sebut("Menghubungi pelayan …")
    hasil = kemas.semak(sumber)

    ui.tajuk("Kemas kini")
    if not hasil.get("ok"):
        print(ui.kotak([
            ui.baris_kv("Dipasang", versi.penuh()),
            ui.baris_kv("Sumber  ", kemas.betulkan(sumber)),
        ]))
        print()
        ui.ralat(hasil.get("ralat", "Tidak dapat menyemak."))
        ui.jeda()
        return

    baris = [
        ui.baris_kv("Dipasang", versi.penuh()),
        ui.baris_kv("Sumber  ", kemas.betulkan(sumber)),
        "",
        ui.baris_kv("Terkini ", f"v{hasil['versi']} ({hasil['tarikh']})"),
        ui.baris_kv("Kunci   ", _cap_jari()),
    ]
    print(ui.kotak(baris))

    if not hasil["ada"]:
        print()
        ui.jaya("App ini sudah versi terkini.")
        ui.jeda()
        return

    if hasil["nota"]:
        print()
        print(ui.kotak(hasil["nota"], tajuk="Apa yang baharu"))

    print()
    ui.amaran("Kemas kini akan menimpa kod app. Rekod anda tidak disentuh.")
    if (ui.tanya("Taip 'pasang' untuk teruskan", boleh_kosong=True) or "").lower() != "pasang":
        ui.sebut("Dibatalkan.")
        ui.jeda()
        return

    print()
    # `lapor` mencetak setiap langkah semasa ia berlaku. Pengesahan dan
    # muat turun mengambil beberapa saat di telefon — skrin yang membeku
    # tanpa petunjuk kelihatan seperti app hang.
    def lapor(mesej):
        ui.sebut(mesej)

    ok, mesej, berubah = kemas.pasang(sumber, hasil["versi"], lapor)

    print()
    if ok:
        ui.jaya(f"Versi {hasil['versi']} telah dipasang.")
        print()
        print(ui.kotak([
            "Tutup app ini dan buka semula untuk",
            "menggunakan versi baharu.",
        ]))
    else:
        ui.ralat(f"Kemas kini gagal: {mesej}")
        if not berubah:
            print()
            ui.maklum("Tiada apa-apa diubah — versi lama masih utuh.")
        else:
            print()
            ui.maklum("Salinan kod lama ada dalam .backup/ dalam folder app.")
    ui.jeda()
