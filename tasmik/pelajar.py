"""Skrin pengurusan pelajar."""

import os
import re

from . import store, ui

# Baris pertama yang berbunyi "Nama, Kelas" ialah kepala jadual, bukan
# pelajar. Ia muncul bila guru export senarai dari Excel atau Google
# Sheets — kes yang paling mungkin, jadi ia patut dilayan.
_KATA_KEPALA = {
    "nama", "nama penuh", "nama pelajar", "name", "full name",
    "pelajar", "murid", "no", "bil", "bilangan",
}

# Hiasan senarai yang biasa terlekat semasa tampal: "1. ", "- ", "• ".
# '+' disertakan kerana ia bulet Markdown yang sah — senarai yang disalin
# dari nota Markdown atau WhatsApp selalunya bermula dengannya.
_RE_HIASAN = re.compile(r"^(?:\d{1,3}\s*[.)]\s*|[-•*·+]\s+|\d{1,3}\s+)")

# Pemisah antara nama dan kelas. Koma yang paling biasa; koma bertitik dan
# tab datang dari export spreadsheet.
_RE_PEMISAH = re.compile(r"[;,\t|]")


def pilih_pelajar(prompt="Pilih pelajar"):
    """Pilih pelajar dari senarai, atau tambah baharu.

    Pulangkan baris pelajar, atau None kalau dibatalkan.
    """
    senarai = store.semua_pelajar()
    if not senarai:
        ui.sebut("Belum ada pelajar didaftarkan.")
        if (ui.tanya("Tambah pelajar sekarang? (y/t)", "y") or "").lower().startswith("y"):
            return tambah_skrin()
        return None

    item = [
        (p["nama"] + (f"  ·  {p['kelas']}" if p["kelas"] else ""), p["id"])
        for p in senarai
    ]
    item.append(("Tambah pelajar baharu", -1))

    hasil = ui.pilih_dari_senarai(prompt, item)
    if hasil is None:
        return None
    if hasil == -1:
        return tambah_skrin()
    return store.dapat_pelajar(hasil)


def tambah_skrin():
    """Tambah pelajar baharu. Pulangkan baris pelajar, atau None."""
    print()
    print(ui.kotak([], tajuk="Pelajar baharu"))
    nama = ui.tanya_wajib("Nama pelajar")
    sedia = store.cari_pelajar_nama(nama)
    if sedia:
        ui.amaran(f"'{nama}' sudah ada dalam senarai.")
        return sedia
    kelas = ui.tanya("Kelas (boleh kosong)", boleh_kosong=True)
    p = store.tambah_pelajar(nama, kelas)
    ui.jaya(f"Pelajar '{nama}' telah ditambah.")
    return p


# ------------------------------------------------------- tambah pukal

def hurai_senarai(teks):
    """Hurai senarai pelajar daripada teks bebas.

    Menerima senarai yang ditampal dari WhatsApp, disalin dari Excel,
    atau ditaip sendiri — tanpa memaksa satu format yang tepat. Yang
    penting hanya dua: satu pelajar satu baris, dan nama didahulukan.

        Ahmad Zaki, Tahun 4
        2. Nurul Huda - Tahun 5
        nama,kelas            <- baris kepala, dilangkau
        Muhammad Adam         <- kelas boleh tiada

    Pulangkan (senarai, gagal, berganda):
        senarai  — [(nama, kelas), ...] yang sudah bersih dan unik
        gagal    — [(no_baris, teks_asli)] yang tidak dapat difahami
        berganda — nama yang berulang DALAM senarai ini (yang pertama
                   diambil, yang kemudian dilangkau)
    """
    senarai, gagal, berganda = [], [], []
    sudah = {}          # nama.lower() -> nama seperti yang disimpan
    baris_pertama = True

    for no, mentah in enumerate(teks.splitlines(), 1):
        baris = mentah.strip()

        # Baris kosong dan komen dilangkau tanpa dikira sebagai ralat.
        if not baris or baris.startswith("#"):
            continue

        baris = _RE_HIASAN.sub("", baris).strip()
        if not baris:
            continue

        padan = _RE_PEMISAH.search(baris)
        if padan:
            nama = baris[:padan.start()].strip()
            kelas = baris[padan.end():].strip()
        else:
            nama, kelas = baris, ""

        # Hanya baris data PERTAMA boleh jadi kepala jadual; selepas itu
        # "nama" yang berdiri sendiri ialah pelajar yang bernama Nama.
        if baris_pertama and nama.lower() in _KATA_KEPALA:
            baris_pertama = False
            continue
        baris_pertama = False

        if not nama:
            gagal.append((no, mentah.strip()))
            continue

        kunci = nama.lower()
        if kunci in sudah:
            berganda.append(nama)
            continue
        sudah[kunci] = nama
        senarai.append((nama, kelas))

    return senarai, gagal, berganda


def _baca_tampal():
    """Baca senarai yang ditampal. Baris kosong menamatkannya.

    Baris kosong dipilih sebagai penamat kerana ia satu-satunya isyarat
    yang guru boleh teka sendiri tanpa diberitahu — dan ia kekal betul
    sama ada senarai itu ditampal atau ditaip.
    """
    print(ui.kotak([
        "  Ahmad Zaki, Tahun 4",
        "  2. Nurul Huda, Tahun 5",
        "  - Siti Aminah; Tahun 6",
        "  Muhammad Adam bin Abdullah",
        "",
        "  Satu pelajar satu baris.",
        "  Nama dahulu, kelas kemudian.",
        "  Kelas tidak wajib.",
    ], tajuk="Contoh bentuk yang diterima"))
    print()
    ui.maklum("Tampal atau taip senarai itu sekarang.")
    ui.maklum("Tekan ENTER pada baris kosong bila sudah habis.")
    print()

    baris = []
    while True:
        try:
            teks = input("  > ")
        except EOFError:
            # Ctrl+D, atau input habis kerana dipipe. Kedua-duanya bermakna
            # "sudah habis" di sini — bukan ralat seperti di skrin lain.
            print()
            break
        except KeyboardInterrupt:
            print()
            return None
        if not teks.strip():
            break
        baris.append(teks)
    return "\n".join(baris)


def _baca_fail(laluan):
    """Baca fail teks. Pulangkan (teks, ralat)."""
    p = os.path.expanduser(os.path.expandvars(laluan.strip().strip("'\"")))
    if not os.path.isfile(p):
        return None, f"Fail tidak dijumpai: {p}"

    # utf-8-sig dahulu: fail yang datang dari Excel bermula dengan BOM,
    # dan tanpanya nama pelajar pertama akan membawa aksara halimunan.
    # latin-1 tidak pernah gagal, jadi ia penamat yang selamat.
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with open(p, encoding=enc) as f:
                return f.read(), ""
        except UnicodeDecodeError:
            continue
    return None, "Fail itu bukan teks yang boleh dibaca."


def _papar_hurai(senarai, gagal, berganda, sedia_ada):
    """Tunjuk apa yang akan berlaku, sebelum apa-apa disimpan."""
    baharu = [(n, k) for n, k in senarai if n.lower() not in sedia_ada]

    print()
    print(ui.kotak([
        ui.baris_kv("Dibaca       ", f"{len(senarai) + len(gagal)} baris"),
        ui.baris_kv("Pelajar baharu", str(len(baharu))),
        ui.baris_kv("Sudah ada    ", str(len(senarai) - len(baharu))),
        ui.baris_kv("Tak difahami ", str(len(gagal))),
    ]))

    if baharu:
        print()
        had = 15
        papar = [f"{n}  ·  {k}" if k else n for n, k in baharu[:had]]
        if len(baharu) > had:
            papar.append(f"… dan {len(baharu) - had} lagi")
        print(ui.kotak(papar, tajuk="Akan ditambah"))
    else:
        print()
        ui.maklum("Tiada pelajar baharu untuk ditambah.")

    if gagal:
        print()
        ui.amaran(f"{len(gagal)} baris tidak difahami dan akan dilangkau:")
        for no, teks in gagal[:5]:
            ui.maklum(f"  baris {no}: {teks[:40]}")
        if len(gagal) > 5:
            ui.maklum(f"  … dan {len(gagal) - 5} lagi")

    if berganda:
        print()
        ui.amaran("Nama berulang dalam senarai (yang pertama diambil):")
        for n in berganda[:5]:
            ui.maklum(f"  {n}")
        if len(berganda) > 5:
            ui.maklum(f"  … dan {len(berganda) - 5} lagi")

    return baharu


def contoh_format_skrin():
    """Rujukan bentuk senarai yang app boleh baca.

    Guru tidak sepatutnya perlu meneka format. Setiap bentuk di bawah
    pernah muncul dalam senarai sebenar — dari WhatsApp, dari Excel,
    dari nota sendiri — jadi setiap satunya ditunjukkan dengan contoh.
    """
    ui.tajuk("Contoh format senarai")

    print(ui.kotak([
        "  Ahmad Zaki, Tahun 4",
        "",
        "  Nama dahulu, kemudian kelas,",
        "  dipisahkan koma.",
    ], tajuk="1 · Yang paling biasa"))

    print(ui.kotak([
        "  2. Nurul Huda, Tahun 5",
        "  3) Siti Aminah, Tahun 6",
        "",
        "  Nombor 1. atau 2) di hadapan",
        "  dilangkau sendiri.",
    ], tajuk="2 · Senarai bernombor"))

    print(ui.kotak([
        "  - Yusuf Hakim, Tahun 4",
        "  • Fatimah Az-Zahra, Tahun 5",
        "  + Abdul Rahman, Tahun 6",
        "",
        "  Bulet - • * + juga dilangkau.",
    ], tajuk="3 · Senarai berbulet"))

    print(ui.kotak([
        "  Muhammad Adam bin Abdullah",
        "",
        "  Kelas tidak wajib. Nama sahaja",
        "  pun boleh.",
    ], tajuk="4 · Tanpa kelas"))

    print(ui.kotak([
        "  Nama Penuh,Kelas",
        "  Ahmad Zaki,Tahun 4",
        "",
        "  Baris kepala dari fail Excel",
        "  dilangkau, bukan jadi pelajar.",
    ], tajuk="5 · Salinan dari Excel"))

    print(ui.kotak([
        "  Ahmad Zaki,Tahun 4",
        "  Ahmad Zaki;Tahun 4",
        "",
        "  Koma, koma bertitik, atau jarak",
        "  tab — semuanya sama sahaja.",
    ], tajuk="6 · Pemisah lain"))

    print()
    ui.maklum("Baris kosong menamatkan senarai semasa menampal.")
    ui.maklum("Baris yang bermula dengan # diabaikan.")
    ui.maklum("Nama yang sudah ada dilangkau, bukan ditambah dua kali.")
    ui.jeda()


def tambah_pukal_skrin():
    """Tambah ramai pelajar sekali gus — tampal senarai, atau baca fail."""
    while True:
        ui.tajuk("Tambah senarai pelajar")

        pilihan = ui.pilih_dari_senarai("Dari mana senarai itu", [
            ("Tampal / taip di sini", "tampal"),
            ("Baca dari fail teks atau CSV", "fail"),
            ("Lihat contoh format", "contoh"),
        ])
        if not pilihan:
            return

        # Melihat contoh tidak sepatutnya menendang guru keluar dari skrin
        # ini — dia selalunya mahu terus menampal selepas faham formatnya.
        if pilihan == "contoh":
            contoh_format_skrin()
            continue
        break

    if pilihan == "tampal":
        teks = _baca_tampal()
        if teks is None:
            return
    else:
        print(ui.kotak([
            "  Ahmad Zaki, Tahun 4",
            "  2. Nurul Huda, Tahun 5",
            "  - Siti Aminah; Tahun 6",
            "",
            "  Isi fail mesti sama bentuknya —",
            "  satu pelajar satu baris.",
        ], tajuk="Contoh isi fail"))
        print()
        ui.maklum("Contoh laluan: ~/storage/downloads/pelajar.csv")
        ui.maklum("Di Termux, jalankan 'termux-setup-storage' sekali dahulu")
        ui.maklum("supaya fail dari folder Download boleh dibaca.")
        laluan = ui.tanya("Laluan fail", boleh_kosong=True)
        if not laluan:
            return
        teks, ralat = _baca_fail(laluan)
        if ralat:
            ui.ralat(ralat)
            ui.jeda()
            return

    if not teks.strip():
        ui.amaran("Tiada apa-apa dibaca.")
        ui.jeda()
        return

    senarai, gagal, berganda = hurai_senarai(teks)

    # Guru mungkin menampal senarai yang sama dua kali, atau senarai yang
    # bertindih dengan yang sudah ada. Kedua-duanya bukan ralat — cuma
    # perlu dinyatakan, supaya angka "sudah ada" tidak mengelirukan.
    sedia_ada = set()
    for nama, _ in senarai:
        if store.cari_pelajar_nama(nama):
            sedia_ada.add(nama.lower())

    baharu = _papar_hurai(senarai, gagal, berganda, sedia_ada)

    if not baharu:
        ui.jeda()
        return

    print()
    if (ui.tanya("Taip 'tambah' untuk simpan", boleh_kosong=True) or "").lower() != "tambah":
        ui.sebut("Dibatalkan.")
        ui.jeda()
        return

    try:
        store.tambah_pelajar_banyak(baharu)
    except Exception as e:  # noqa: BLE001 — jangan tinggalkan guru dengan separuh senarai
        ui.ralat(f"Gagal menyimpan: {e}")
        ui.maklum("Tiada pelajar disimpan — senarai lama masih utuh.")
        ui.jeda()
        return

    print()
    ui.jaya(f"{len(baharu)} pelajar telah ditambah.")
    ui.jeda()


def senarai_skrin():
    ui.tajuk("Senarai pelajar")
    senarai = store.semua_pelajar()
    if not senarai:
        ui.sebut("Belum ada pelajar didaftarkan.")
        ui.jeda()
        return

    baris = []
    for i, p in enumerate(senarai, 1):
        bil = store.bilangan_rekod_pelajar(p["id"])
        akhir = store.db().execute(
            "SELECT MAX(tarikh) FROM rekod WHERE pelajar_id = ?", (p["id"],)
        ).fetchone()[0]
        kiri = f"{i:>3}. {p['nama']}"
        kanan = f"{bil} rekod"
        baris.append(ui.baris_kv(kiri, kanan))
        keterangan = f"     {p['kelas'] or 'tiada kelas'}"
        if akhir:
            keterangan += f"  ·  terakhir {ui.tarikh_pendek(akhir)}"
        baris.append(keterangan)

    print(ui.kotak(baris, tajuk="Pelajar"))
    print()
    ui.maklum(f"Jumlah: {len(senarai)} pelajar")
    ui.jeda()


def tukar_skrin():
    ui.tajuk("Tukar maklumat pelajar")
    p = pilih_pelajar()
    if not p:
        return
    print()
    nama = ui.tanya("Nama baharu", p["nama"])
    # Lalai ialah kelas semasa, jadi ENTER sahaja mengekalkannya. '-' perlu
    # kerana `tanya()` memulangkan lalai apabila kosong — tanpa penanda ini
    # tiada cara untuk mengosongkan kelas.
    kelas = ui.tanya("Kelas ('-' untuk kosongkan)", p["kelas"] or "-")
    if kelas == "-":
        kelas = ""

    # Nama ialah UNIQUE dalam jadual. Kalau guru menukar nama kepada nama
    # pelajar lain, SQLite akan membaling IntegrityError — ditangkap di
    # sini supaya ia jadi ayat yang boleh difahami, bukan jejak ralat.
    if nama != p["nama"] and store.cari_pelajar_nama(nama):
        ui.ralat(f"Sudah ada pelajar bernama '{nama}'.")
        ui.jeda()
        return

    store.kemas_kini_pelajar(p["id"], nama, kelas)
    ui.jaya(f"Maklumat '{nama}' telah dikemas kini.")
    ui.jeda()


def padam_skrin():
    ui.tajuk("Padam pelajar")
    p = pilih_pelajar()
    if not p:
        return
    bil = store.bilangan_rekod_pelajar(p["id"])
    print()
    ui.amaran(f"Anda akan padam '{p['nama']}' bersama {bil} rekod tasmi'nya.")
    ui.maklum("Tindakan ini tidak boleh dibatalkan.")
    if (ui.tanya("Taip 'padam' untuk sahkan", boleh_kosong=True) or "").lower() != "padam":
        ui.sebut("Dibatalkan.")
        ui.jeda()
        return
    store.padam_pelajar(p["id"])
    ui.jaya(f"'{p['nama']}' telah dipadam.")
    ui.jeda()


def skrin():
    """Submenu pengurusan pelajar."""
    while True:
        ui.tajuk("Pelajar")
        print(ui.kotak([
            "  1.  Senarai pelajar",
            "  2.  Tambah pelajar",
            "  3.  Tambah senarai (pukal)",
            "  4.  Tukar nama / kelas",
            "  5.  Padam pelajar",
            "",
            "  0.  Kembali",
        ]))
        pilihan = ui.tanya("Pilihan")
        if pilihan is None:
            continue

        if pilihan == "1":
            senarai_skrin()
        elif pilihan == "2":
            tambah_skrin()
            ui.jeda()
        elif pilihan == "3":
            tambah_pukal_skrin()
        elif pilihan == "4":
            tukar_skrin()
        elif pilihan == "5":
            padam_skrin()
        elif pilihan == "0":
            return
        else:
            ui.ralat("Pilihan tidak sah.")
            ui.jeda()
