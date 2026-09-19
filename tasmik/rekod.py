"""Skrin tasmi' — aliran Tasmik, senarai rekod, tapis, padam.

Aliran utama (sejak v3.0.0) mengikut susunan yang guru gunakan di dalam
kelas: pilih kumpulan murid, pilih jenis, kemudian isi borang. Ia
menggantikan "Tambah rekod tasmi'" yang lama, yang bermula dengan senarai
SEMUA murid — satu langkah yang tidak berguna apabila guru sedang mengajar
satu kelas.

Dua bentuk rekod wujud, dan paparan di sini mesti mengendalikan kedua-dua:

  - **hafazan** — julat ayat, seperti dahulu
  - **tilawah** — halaman mushaf sejak v3.0.0, dan julat ayat bagi rekod
    tilawah yang direkod sebelum itu

Rekod lama tidak pernah ditukar. Ia hanya dipaparkan mengikut bentuk yang
ia sebenarnya.
"""

from datetime import date, timedelta

from . import mushaf, pelajar, store, surah, ui


def _tanda(jenis):
    return "T" if jenis == store.TILAWAH else "H"


def label_rekod(r):
    """Satu baris yang menerangkan apa yang dibaca.

    Dikongsi oleh senarai dan skrin padam supaya kedua-duanya tidak boleh
    hanyut — rekod yang dipaparkan sebagai "Halaman 245" dalam senarai
    mesti dipaparkan sama apabila guru hendak memadamnya.
    """
    if r["muka_surat"]:
        return f"Halaman {r['muka_surat']} ({mushaf.label_halaman(r['muka_surat'])})"
    return surah.label_surah(r["surah_no"], r["ayat_dari"], r["ayat_hingga"])


def baris_ringkas(r):
    """Dua atau tiga baris bagi satu rekod: bacaan, butiran, nota."""
    baris = [f"{ui.tarikh_pendek(r['tarikh'])} [{_tanda(r['jenis'])}]  "
             f"{label_rekod(r)}"]

    if r["muka_surat"]:
        # Halaman bukan bilangan ayat, jadi butiran tidak boleh menyebut
        # bilangan. Ayat NULL di sini ialah keadaan yang sah, bukan data
        # yang hilang.
        butiran = f"{r['nama_pelajar']}  ·  halaman {r['muka_surat']}"
    else:
        ayat = r["ayat_hingga"] - r["ayat_dari"] + 1
        butiran = f"{r['nama_pelajar']}  ·  {ayat} ayat"
    if r["juzuk"]:
        butiran += f"  ·  J{r['juzuk']}"
    baris.append("   " + butiran)

    if r["nota"]:
        baris.append("   ↳ " + r["nota"])
    return baris


# ------------------------------------------------------------------ tasmik

def sesi_skrin(cfg):
    """Aliran Tasmik: kumpulan kelas → jenis → borang."""
    ui.tajuk("Tasmik")
    kelas = _pilih_kelas()
    if kelas is None:
        return
    jenis = _pilih_jenis(kelas)
    if jenis is None:
        return
    if jenis == store.TILAWAH:
        _borang_tilawah(kelas)
    else:
        _borang_hafazan(cfg, kelas)


def _pilih_kelas():
    """Pulangkan nama kelas, "" untuk tanpa kelas, atau None kalau batal."""
    senarai = store.senarai_kelas()
    if not senarai:
        ui.sebut("Belum ada murid didaftarkan.")
        ui.maklum("Tambah murid di menu Murid dahulu.")
        ui.jeda()
        return None
    # Label di dalam kotak disorong oleh "  1. " — lima aksara. Tanpa
    # menolaknya, setiap baris terbelah dua dan senarai jadi dua kali
    # panjang di skrin telefon.
    lebar_label = ui.lebar() - 9
    item = [
        (ui.baris_kv(nama or "Tanpa kelas", f"{bil} murid", lebar_label), nama)
        for nama, bil in senarai
    ]
    return ui.pilih_dari_senarai("Tasmik", item)


def _pilih_jenis(kelas):
    return ui.pilih_dari_senarai(
        f"{kelas or 'Tanpa kelas'} · jenis",
        [("Tilawah  — bacaan mushaf", store.TILAWAH),
         ("Hafazan  — hafalan surah", store.HAFAZAN)],
    )


def _borang_tilawah(kelas):
    """Tilawah direkod ikut HALAMAN. Surah dan juzuk diterbitkan."""
    p = pelajar.pilih_pelajar_kelas(kelas, "Pilih murid")
    if not p:
        return
    tarikh = ui.tanya_tarikh("Tarikh tasmi'")

    while True:
        halaman = ui.tanya_int(f"Muka surat mushaf (1-{mushaf.HALAMAN_MAKS})",
                               1, mushaf.HALAMAN_MAKS)
        juzuk = mushaf.juzuk_pada_halaman(halaman)
        print()
        print(ui.kotak([
            f"  Halaman {halaman}",
            f"  Juzuk {juzuk}   ·   {mushaf.label_halaman(halaman)}",
        ], tajuk="Halaman ini"))
        # Guru SAHKAN terbitan itu, bukan menerimanya bulat-bulat. Jadual
        # halaman ialah data yang disemak di mesin pembina, tetapi mushaf
        # guru mungkin berbeza — dan dia satu-satunya yang boleh nampak
        # perbezaan itu.
        if ui.tanya_ya("Betul"):
            break
        ui.sebut("Taip semula nombor halaman.")

    print()
    nota = ui.tanya("Nota / catatan (boleh kosong)", boleh_kosong=True)

    _sahkan_dan_simpan(
        p=p, tarikh=tarikh, jenis=store.TILAWAH,
        no=mushaf.surah_pada_halaman(halaman)[0],
        dari=None, hingga=None, juzuk=str(juzuk), nota=nota,
        muka_surat=halaman, kelas=kelas,
    )


def _borang_hafazan(cfg, kelas):
    p = pelajar.pilih_pelajar_kelas(kelas, "Pilih murid")
    if not p:
        return
    tarikh = ui.tanya_tarikh("Tarikh tasmi'")

    s = _pilih_surah_kelas(cfg, kelas)
    if not s:
        return
    no, nama_s, jumlah, _j1, _j2 = s

    print()
    print(ui.kotak([
        f"  {nama_s} mempunyai {jumlah} ayat.",
        "  ENTER sahaja untuk rekod seluruh surah.",
    ]))
    # Had atas ialah bilangan ayat SEBENAR surah itu. Dokumen asal menyebut
    # "auto 1-110 sebab al-Kahfi sampai 110", tetapi senarai rata begitu
    # membenarkan "al-Mulk ayat 50" disimpan tanpa sebarang amaran.
    dari = ui.tanya_int(f"Ayat dari (1-{jumlah})", 1, jumlah, 1)
    hingga = ui.tanya_int(f"Ayat hingga ({dari}-{jumlah})", dari, jumlah, jumlah)

    print()
    nota = ui.tanya("Nota / catatan (boleh kosong)", boleh_kosong=True)

    # Hafazan sengaja TIDAK bertanya juzuk. Guru menghafaz ikut surah dan
    # ayat, bukan ikut juzuk — dan satu soalan yang tidak perlu setiap kali
    # menambah rekod lama-lama menjadi kerja yang melecehkan.
    _sahkan_dan_simpan(
        p=p, tarikh=tarikh, jenis=store.HAFAZAN, no=no,
        dari=dari, hingga=hingga, juzuk=surah.julat_juzuk(no), nota=nota,
        muka_surat=None, kelas=kelas,
    )


def _pilih_surah_kelas(cfg, kelas):
    """Surah daripada sukatan kelas, atau carian penuh 114 surah."""
    sukatan = (cfg.get("sukatan") or {}).get(kelas or "", [])
    item = []
    for n in sukatan:
        if isinstance(n, int) and 1 <= n <= 114:
            item.append(
                (f"{surah.nama_surah(n)}  ({surah.ayat_surah(n)} ayat)",
                 surah.SURAH[n - 1])
            )
    if not item:
        ui.maklum("Sukatan kelas ini belum ditetapkan.")
    item.append(("Cari surah lain (114)", "cari"))

    pilihan = ui.pilih_dari_senarai(f"Hafazan · {kelas or 'Tanpa kelas'}", item)
    if pilihan is None:
        return None
    if pilihan == "cari":
        return surah.pilih_surah()
    return pilihan


def _sahkan_dan_simpan(p, tarikh, jenis, no, dari, hingga, juzuk, nota,
                       muka_surat, kelas):
    """Papar ringkasan, minta pengesahan, kemudian simpan.

    Satu tempat sahaja menyimpan rekod, supaya kedua-dua jenis tidak boleh
    hanyut dari segi apa yang dipaparkan sebelum menyimpan.
    """
    baris = [
        ui.baris_kv("Murid ", p["nama"]),
        ui.baris_kv("Kelas ", kelas or "—"),
        ui.baris_kv("Tarikh", ui.tarikh_my(tarikh.isoformat(), dengan_hari=True)),
    ]
    if muka_surat:
        baris += [
            ui.baris_kv("Bacaan", f"Halaman {muka_surat}"),
            ui.baris_kv("Surah ", mushaf.label_halaman(muka_surat)),
            ui.baris_kv("Juzuk ", str(juzuk)),
        ]
    else:
        baris += [
            ui.baris_kv("Bacaan", surah.label_surah(no, dari, hingga)),
            ui.baris_kv("Bilangan", f"{hingga - dari + 1} ayat"),
            ui.baris_kv("Juzuk ", juzuk or "-"),
        ]
    if nota:
        baris.append(ui.baris_kv("Nota  ", nota))

    print()
    print(ui.kotak(baris, tajuk="Simpan rekod?"))
    if not ui.tanya_ya("Simpan"):
        ui.sebut("Dibatalkan — tiada apa-apa disimpan.")
        ui.jeda()
        return

    store.tambah_rekod(p["id"], tarikh.isoformat(), jenis, no, dari, hingga,
                       juzuk, nota, muka_surat)
    ui.jaya("Rekod disimpan.")
    ui.jeda()


# ------------------------------------------------------------------ tapisan

def _tapis():
    """Kumpul tapisan daripada guru. Pulangkan (where, params, keterangan)."""
    pilihan = ui.pilih_dari_senarai("Tapis rekod", [
        ("Semua rekod", "semua"),
        ("Ikut murid", "pelajar"),
        ("Ikut tarikh (julat)", "tarikh"),
        ("Hari ini sahaja", "hari_ini"),
        ("Minggu ini sahaja", "minggu"),
        ("Ikut jenis (tilawah / hafazan)", "jenis"),
    ])
    if not pilihan:
        return None

    where, params, ket = [], [], []

    if pilihan == "pelajar":
        p = pelajar.pilih_pelajar()
        if not p:
            return None
        where.append("r.pelajar_id = ?")
        params.append(p["id"])
        ket.append(p["nama"])

    elif pilihan == "tarikh":
        print()
        ui.maklum("ENTER pada 'hingga' bermaksud hari ini.")
        d1 = ui.tanya_tarikh("Dari tarikh")
        d2 = ui.tanya_tarikh("Hingga tarikh")
        where.append("r.tarikh BETWEEN ? AND ?")
        params += [d1.isoformat(), d2.isoformat()]
        ket.append(f"{ui.tarikh_my(d1.isoformat())} – {ui.tarikh_my(d2.isoformat())}")

    elif pilihan == "hari_ini":
        where.append("r.tarikh = ?")
        params.append(date.today().isoformat())
        ket.append("hari ini")

    elif pilihan == "minggu":
        # Isnin minggu ini. `weekday()` ialah 0 untuk Isnin.
        mula = date.today() - timedelta(days=date.today().weekday())
        where.append("r.tarikh >= ?")
        params.append(mula.isoformat())
        ket.append(f"minggu ini (dari {ui.tarikh_pendek(mula.isoformat())})")

    elif pilihan == "jenis":
        j = ui.pilih_dari_senarai("Pilih jenis", [
            ("Tilawah", store.TILAWAH), ("Hafazan", store.HAFAZAN)])
        if not j:
            return None
        where.append("r.jenis = ?")
        params.append(j)
        ket.append(store.JENIS_NAMA[j])

    return " AND ".join(where), tuple(params), " · ".join(ket) or "semua rekod"


def senarai_skrin():
    ui.tajuk("Rekod tasmi'")
    tapis = _tapis()
    if tapis is None:
        return
    where, params, keterangan = tapis

    baris = store.cari_rekod(where, params)
    if not baris:
        print()
        ui.sebut("Tiada rekod dijumpai.")
        ui.jeda()
        return

    ui.tajuk("Rekod tasmi'")
    print(ui.kotak([ui.baris_kv("Tapisan", f"{len(baris)} rekod")]))
    print()
    ui.maklum(keterangan)
    print()

    for i, r in enumerate(baris, 1):
        blok = baris_ringkas(r)
        print(f"{i:>3}. " + blok[0])
        for lanjutan in blok[1:]:
            print("     " + lanjutan.strip())
        print()

    # Rekod ikut halaman tiada julat ayat, jadi ia tidak boleh dicampur ke
    # dalam jumlah ayat tanpa menjadikannya palsu. Kedua-duanya dikira dan
    # dilaporkan berasingan.
    jumlah_ayat = sum(r["ayat_hingga"] - r["ayat_dari"] + 1
                      for r in baris if r["ayat_dari"] is not None)
    jumlah_hal = sum(1 for r in baris if r["muka_surat"])

    print(ui.garis())
    ringkas = f"{len(baris)} rekod"
    if jumlah_ayat:
        ringkas += f"  ·  {jumlah_ayat} ayat"
    if jumlah_hal:
        ringkas += f"  ·  {jumlah_hal} halaman"
    ui.maklum(ringkas)

    print()
    # Soalan ini sekali gus jadi jeda untuk membaca senarai — guru membaca
    # rekod, kemudian menekan ENTER. Menambah satu lagi "[ENTER] teruskan"
    # selepas ini bermakna dua tekanan untuk satu tindakan.
    pilihan = ui.tanya("Nombor rekod untuk padam, atau ENTER untuk kembali",
                       boleh_kosong=True)
    if pilihan and pilihan.isdigit() and 1 <= int(pilihan) <= len(baris):
        padam_skrin(baris[int(pilihan) - 1])


def padam_skrin(r):
    print()
    ui.amaran(f"Padam rekod: {r['nama_pelajar']} — {label_rekod(r)} "
              f"({ui.tarikh_my(r['tarikh'])})?")
    if (ui.tanya("Taip 'padam' untuk sahkan", boleh_kosong=True) or "").lower() != "padam":
        ui.sebut("Dibatalkan.")
        ui.jeda()
        return
    store.padam_rekod(r["id"])
    ui.jaya("Rekod telah dipadam.")
    ui.jeda()
