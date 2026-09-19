"""Skrin laporan kemajuan."""

from datetime import date, timedelta

from . import pelajar, rekod, store, surah, ui


def _blok_pelajar(p, ringkas=False):
    """Senarai baris kotak bagi seorang pelajar."""
    s = store.ringkasan_pelajar(p["id"])
    nama = p["nama"] + (f"   ·   {p['kelas']}" if p["kelas"] else "")

    if not s["akhir"]:
        return [nama, "", "Belum ada rekod tasmi'."]

    baris = [
        nama,
        "",
        ui.baris_kv("Tilawah ", f"{s['sesi_tilawah']} sesi  ·  {s['ayat_tilawah']} ayat"),
        ui.baris_kv("Hafazan ", f"{s['sesi_hafazan']} sesi  ·  {s['ayat_hafazan']} ayat"),
        ui.baris_kv("Juzuk   ", surah.ringkas_nombor(s["juzuk"])),
        ui.baris_kv("Surah dihafaz", f"{len(s['surah_hafazan'])} surah"),
    ]

    if s["akhir_hafazan"]:
        a = s["akhir_hafazan"]
        baris.append("")
        baris.append("Hafazan terjauh:")
        baris.append("  " + surah.label_surah(a["surah_no"], a["ayat_dari"],
                                               a["ayat_hingga"]))
        baris.append("  " + ui.tarikh_my(a["tarikh"]))

    if not ringkas:
        a = s["akhir"]
        baris.append("")
        baris.append("Tasmi' terakhir:")
        baris.append("  " + store.JENIS_NAMA[a["jenis"]] + " — "
                     + surah.label_surah(a["surah_no"], a["ayat_dari"],
                                         a["ayat_hingga"]))
        baris.append("  " + ui.tarikh_my(a["tarikh"]))

    return baris


def kemajuan_skrin():
    ui.tajuk("Laporan kemajuan")
    senarai = store.semua_pelajar()
    if not senarai:
        ui.sebut("Belum ada pelajar didaftarkan.")
        ui.jeda()
        return

    pilihan = ui.pilih_dari_senarai(
        "Papar laporan",
        [("Semua pelajar", "semua")] + [(p["nama"], p["id"]) for p in senarai],
    )
    if not pilihan:
        return

    ui.tajuk("Laporan kemajuan")

    if pilihan == "semua":
        mula = date.today() - timedelta(days=30)
        bil_hari = store.bilangan_hari_ada_tasmi(mula.isoformat())
        print(ui.kotak([
            "Semua pelajar",
            f"{bil_hari} hari ada tasmi'",
            "dalam 30 hari lepas",
        ]))
        print()
        for p in senarai:
            print(ui.kotak(_blok_pelajar(p, ringkas=True)))
            print()
    else:
        p = store.dapat_pelajar(pilihan)
        if not p:
            return
        print(ui.kotak(_blok_pelajar(p)))
        print()
        _sejarah(p["id"])
        print()

    ui.jeda()


def _sejarah(pid, had=10):
    """Senarai rekod terakhir seorang pelajar."""
    baris = store.cari_rekod("r.pelajar_id = ?", (pid,), had=had)
    if not baris:
        return
    ui.maklum(f"{len(baris)} rekod terakhir:")
    print()
    for r in baris:
        print("  " + rekod.baris_ringkas(r)[0])
