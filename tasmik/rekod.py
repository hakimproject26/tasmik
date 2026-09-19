"""Skrin rekod tasmi' — tambah, senarai, tapis, padam."""

from datetime import date, timedelta

from . import pelajar, store, surah, ui


def _tanda(jenis):
    return "T" if jenis == store.TILAWAH else "H"


def baris_ringkas(r):
    """Dua atau tiga baris bagi satu rekod: bacaan, butiran, nota."""
    bacaan = surah.label_surah(r["surah_no"], r["ayat_dari"], r["ayat_hingga"])
    ayat = r["ayat_hingga"] - r["ayat_dari"] + 1
    baris = [f"{ui.tarikh_pendek(r['tarikh'])} [{_tanda(r['jenis'])}]  {bacaan}"]

    butiran = f"{r['nama_pelajar']}  ·  {ayat} ayat"
    if r["juzuk"]:
        butiran += f"  ·  J{r['juzuk']}"
    baris.append("   " + butiran)

    if r["nota"]:
        baris.append("   ↳ " + r["nota"])
    return baris


def tambah_skrin():
    """Aliran menambah satu rekod tasmi'."""
    ui.tajuk("Tambah rekod tasmi'")

    p = pelajar.pilih_pelajar("Pilih pelajar")
    if not p:
        return

    jenis = ui.pilih_dari_senarai(
        f"Jenis tasmi' untuk {p['nama']}",
        [("Tilawah  (bacaan)", store.TILAWAH),
         ("Hafazan  (menghafal)", store.HAFAZAN)],
    )
    if not jenis:
        return

    tarikh = ui.tanya_tarikh("Tarikh tasmi'")
    s = surah.pilih_surah()
    if not s:
        return
    no, nama_s, jumlah_ayat, _j1, _j2 = s

    print()
    print(ui.kotak([
        f"  {nama_s} mempunyai {jumlah_ayat} ayat.",
        "  ENTER sahaja untuk rekod seluruh surah.",
    ]))
    dari = ui.tanya_int(f"Ayat dari (1-{jumlah_ayat})", 1, jumlah_ayat, 1)
    hingga = ui.tanya_int(f"Ayat hingga ({dari}-{jumlah_ayat})",
                          dari, jumlah_ayat, jumlah_ayat)

    # Hafazan sengaja TIDAK bertanya juzuk. Guru menghafaz ikut surah dan
    # ayat, bukan ikut juzuk — dan satu soalan yang tidak perlu setiap kali
    # menambah rekod lama-lama menjadi kerja yang melecehkan.
    if jenis == store.TILAWAH:
        print()
        juzuk = ui.tanya("Juzuk (cth: 1 atau 1-3)", surah.julat_juzuk(no))
    else:
        juzuk = surah.julat_juzuk(no)

    print()
    nota = ui.tanya("Nota / catatan (boleh kosong)", boleh_kosong=True)

    store.tambah_rekod(p["id"], tarikh.isoformat(), jenis, no, dari, hingga,
                       juzuk, nota)

    bil_ayat = hingga - dari + 1
    ui.tajuk("Rekod disimpan")
    print(ui.kotak([
        ui.baris_kv("Pelajar ", p["nama"]),
        ui.baris_kv("Jenis   ", store.JENIS_NAMA[jenis]),
        ui.baris_kv("Tarikh  ", ui.tarikh_my(tarikh.isoformat(), dengan_hari=True)),
        ui.baris_kv("Bacaan  ", surah.label_surah(no, dari, hingga)),
        ui.baris_kv("Bilangan", f"{bil_ayat} ayat"),
        ui.baris_kv("Juzuk   ", juzuk or "-"),
    ] + ([ui.baris_kv("Nota    ", nota)] if nota else [])))
    ui.jeda()


# ------------------------------------------------------------------ tapisan

def _tapis():
    """Kumpul tapisan daripada guru. Pulangkan (where, params, keterangan)."""
    pilihan = ui.pilih_dari_senarai("Tapis rekod", [
        ("Semua rekod", "semua"),
        ("Ikut pelajar", "pelajar"),
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

    jumlah_ayat = sum(r["ayat_hingga"] - r["ayat_dari"] + 1 for r in baris)
    print(ui.garis())
    ui.maklum(f"{len(baris)} rekod  ·  {jumlah_ayat} ayat")

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
    ui.amaran("Padam rekod: "
              f"{r['nama_pelajar']} — "
              f"{surah.label_surah(r['surah_no'], r['ayat_dari'], r['ayat_hingga'])} "
              f"({ui.tarikh_my(r['tarikh'])})?")
    if (ui.tanya("Taip 'padam' untuk sahkan", boleh_kosong=True) or "").lower() != "padam":
        ui.sebut("Dibatalkan.")
        ui.jeda()
        return
    store.padam_rekod(r["id"])
    ui.jaya("Rekod telah dipadam.")
    ui.jeda()
