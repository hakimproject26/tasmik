"""Helper paparan terminal — kotak, warna, dan input.

Gaya visualnya sengaja sama dengan app taksiran: kotak bergaris, warna
sekadar penanda makna (hijau = berjaya, kuning = perlu perhatian, merah =
salah), dan teks yang terlalu panjang dibalut dan bukan menembus dinding
kotak.

Satu perbezaan penting daripada app taksiran: fail ini membaling
`InputTamat` apabila input tamat (Ctrl+D). Di sana, `tanya()` memulangkan
None — dan kerana kebanyakan gelung soal-jawab sengaja berulang sehingga
jawapan yang sah diterima, None bermakna gelung itu berpusing tanpa
henti. Membaling ralat membolehkan app keluar dengan bersih.
"""

import os
import re
import shutil
import sys
import textwrap
from datetime import date, datetime, timedelta


class InputTamat(Exception):
    """Input tamat (Ctrl+D, atau paip input habis)."""


# ------------------------------------------------------------------ warna

class W:
    RESET = "\033[0m"
    TEBAL = "\033[1m"
    MALAP = "\033[2m"
    MERAH = "\033[31m"
    HIJAU = "\033[32m"
    KUNING = "\033[33m"
    BIRU = "\033[36m"


def _warna_aktif():
    """Warna hanya bila output pergi ke terminal sebenar.

    Tanpa semakan ini, output yang disalurkan ke fail (atau dibaca oleh
    skrip ujian) penuh dengan kod ANSI dan sukar diperiksa. `NO_COLOR`
    dihormati kerana ia konvensyen yang meluas.
    """
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TASMIK_WARNA") == "1":
        return True
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def warna(teks, kod):
    if not _warna_aktif():
        return str(teks)
    return f"{kod}{teks}{W.RESET}"


# ------------------------------------------------------------------ lebar

LEBAR_MAKS = 52
LEBAR_MIN = 34


def lebar():
    """Lebar paparan, dihadkan supaya elok di skrin telefon.

    Termux dalam mod potret selalunya sekitar 40-46 aksara. Kita tidak
    pernah melebihi 52 (supaya ia tidak terlalu lebar di telefon) dan
    tidak pernah kurang daripada 34 (supaya kotak masih boleh dibaca).
    """
    try:
        kolum = shutil.get_terminal_size().columns - 2
    except Exception:
        return LEBAR_MAKS
    return max(LEBAR_MIN, min(LEBAR_MAKS, kolum))


def pad(teks, n):
    """Tambah ruang di kanan supaya panjangnya tepat n."""
    return teks + " " * max(0, n - len(teks))


def baris_kv(kiri, kanan, lebar_baris=None):
    """Kiri di hujung kiri, kanan di hujung kanan.

    Lebar lalai ialah lebar DALAM kotak (`lebar() - 4`), bukan lebar kotak.
    Ini penting: `kotak()` membalut baris yang lebih panjang daripada ruang
    dalamnya, jadi baris kunci-nilai selebar kotak akan terbelah dua —
    kunci di satu baris, nilai di baris berikutnya.

    Kotak memakan 4 aksara: '│ ' di kiri dan ' │' di kanan.
    """
    if lebar_baris is None:
        lebar_baris = lebar() - 4
    jarak = lebar_baris - len(kiri) - len(kanan)
    if jarak < 1:
        jarak = 1
    return kiri + " " * jarak + kanan


def kotak(baris, lebar_kotak=None, tajuk=None):
    """Lukis kotak sekeliling senarai baris teks biasa.

    Baris yang terlalu panjang dibalut, bukan dibiarkan menembus dinding
    kotak. Tanpa ini, satu nama pelajar yang panjang sudah cukup untuk
    merosakkan seluruh kotak.
    """
    lebar_kotak = lebar_kotak or lebar()
    dalam = lebar_kotak - 2
    if tajuk:
        atas = "╭─ " + tajuk + " " + "─" * max(0, dalam - len(tajuk) - 3) + "╮"
    else:
        atas = "╭" + "─" * dalam + "╮"
    bawah = "╰" + "─" * dalam + "╯"

    keluar = [atas]
    for b in baris:
        # Perkataan yang SENDIRI lebih panjang daripada kotak akan
        # dipotong — itu perlu, kerana nama tanpa ruang (alamat, rentetan
        # panjang) tidak boleh dibalut dengan cara lain.
        #
        # `subsequent_indent` menjorokkan baris sambungan dua ruang. Tanpa
        # ia, baris kedua sesuatu ayat bermula rapat di tepi kotak dan
        # nampak seperti baris yang berasingan, bukan sambungan.
        serpihan = textwrap.wrap(b, width=dalam - 2,
                                 break_on_hyphens=False,
                                 subsequent_indent="  ") or [""]
        for s in serpihan:
            keluar.append("│ " + pad(s, dalam - 2) + " │")
    keluar.append(bawah)
    return "\n".join(keluar)


def garis(tajuk=None, lebar_kotak=None):
    lebar_kotak = lebar_kotak or lebar()
    if tajuk:
        return "── " + tajuk + " " + "─" * max(0, lebar_kotak - len(tajuk) - 4)
    return "─" * lebar_kotak


def bersih():
    os.system("cls" if os.name == "nt" else "clear")


def tajuk(teks):
    """Skrin penuh: bersihkan, kemudian kotak tajuk."""
    bersih()
    lebar_kotak = lebar()
    print("╭" + "─" * (lebar_kotak - 2) + "╮")
    print("│ " + pad(teks.upper(), lebar_kotak - 4) + " │")
    print("╰" + "─" * (lebar_kotak - 2) + "╯")


def tajuk_kotak(teks):
    return kotak([""], tajuk=teks)


def sebut(teks=""):
    """Cetak dengan indentasi standard supaya selari dengan kotak."""
    print("  " + teks if teks else "")


def jaya(teks):
    print()
    print(warna("  ✓ " + teks, W.HIJAU))


def ralat(teks):
    print()
    print(warna("  ✗ " + teks, W.MERAH))


def amaran(teks):
    print()
    print(warna("  ! " + teks, W.KUNING))


def maklum(teks):
    print(warna("  " + teks, W.MALAP))


# ------------------------------------------------------------------ input

def jeda(mesej="[ENTER] teruskan"):
    try:
        input("\n  " + mesej + " ")
    except EOFError:
        print()
        raise InputTamat
    except KeyboardInterrupt:
        print()
        raise


def tanya(label, lalai=None, boleh_kosong=False):
    """Baca satu baris.

    Pulangan:
        teks    — jawapan, atau `lalai` kalau kosong dan ada lalai
        ""      — kalau kosong, tiada lalai, dan `boleh_kosong` True
        None    — kalau kosong, tiada lalai, dan `boleh_kosong` False
    """
    if lalai not in (None, ""):
        petunjuk = f" [{lalai}]"
    else:
        petunjuk = ""
    while True:
        try:
            jawab = input(f"  {label}{petunjuk}: ").strip()
        except EOFError:
            print()
            raise InputTamat
        except KeyboardInterrupt:
            print()
            raise
        if jawab:
            return jawab
        if boleh_kosong:
            return ""
        if lalai not in (None, ""):
            return str(lalai)
        return None


def tanya_wajib(label, lalai=None):
    """Tanya sehingga jawapan tidak kosong."""
    while True:
        jawab = tanya(label, lalai)
        if jawab:
            return jawab
        ralat("Ruangan ini tidak boleh dibiarkan kosong.")


def tanya_int(label, minimum=None, maksimum=None, lalai=None):
    while True:
        jawab = tanya(label, lalai)
        if jawab is None:
            ralat("Sila masukkan nombor.")
            continue
        try:
            angka = int(str(jawab).strip())
        except ValueError:
            ralat("Sila masukkan nombor sahaja.")
            continue
        if minimum is not None and angka < minimum:
            ralat(f"Nilai paling kecil ialah {minimum}.")
            continue
        if maksimum is not None and angka > maksimum:
            ralat(f"Nilai paling besar ialah {maksimum}.")
            continue
        return angka


def tanya_ya(label, lalai=True):
    """Soalan ya/tidak. Pulangkan True atau False. ENTER bermakna `lalai`.

    Ditulis berasingan daripada `tanya()` kerana jawapan yang tidak
    difahami mesti ditanya semula. `tanya()` memulangkan teks bebas, jadi
    "yakin" akan diterima sebagai jawapan ya.
    """
    petunjuk = " [Y/n]" if lalai else " [y/N]"
    while True:
        try:
            jawab = input(f"  {label}{petunjuk}: ").strip().lower()
        except EOFError:
            print()
            raise InputTamat
        except KeyboardInterrupt:
            print()
            raise
        if not jawab:
            return lalai
        if jawab in ("y", "ya", "t", "true"):
            return True
        if jawab in ("n", "no", "tidak", "f", "false"):
            return False
        ralat("Sila jawab 'y' atau 'n'.")


def pilih_dari_senarai(judul, item, label_batal="Batal", lebar_kotak=None):
    """
    Papar senarai bernombor dalam kotak dan minta pengguna memilih.

    `item` ialah senarai pasangan (label, nilai). Pulangkan nilai, atau
    None kalau dibatalkan.
    """
    if not item:
        return None
    lebar_kotak = lebar_kotak or lebar()
    baris = []
    for i, (label, _) in enumerate(item, 1):
        baris.append(f"{i:>3}. {label}")
    baris.append("")
    baris.append(f"  0. {label_batal}")
    print()
    print(kotak(baris, lebar_kotak, tajuk=judul))
    print()
    while True:
        jawab = tanya("Pilih nombor")
        if jawab is None:
            ralat("Sila pilih satu nombor.")
            continue
        if jawab == "0":
            return None
        if jawab.isdigit() and 1 <= int(jawab) <= len(item):
            return item[int(jawab) - 1][1]
        ralat("Nombor tidak sah. Cuba lagi.")


# ------------------------------------------------------------------ tarikh

NAMA_HARI = ["Isnin", "Selasa", "Rabu", "Khamis", "Jumaat", "Sabtu", "Ahad"]
NAMA_BULAN = [
    "", "Jan", "Feb", "Mac", "Apr", "Mei", "Jun",
    "Jul", "Ogo", "Sep", "Okt", "Nov", "Dis",
]


def tarikh_my(iso, dengan_hari=False):
    """Tukar '2026-09-19' jadi '19 Sep 2026' (atau 'Sabtu, 19 Sep 2026')."""
    try:
        d = date.fromisoformat(iso)
    except (ValueError, TypeError):
        return str(iso) if iso else "-"
    teks = f"{d.day} {NAMA_BULAN[d.month]} {d.year}"
    if dengan_hari:
        teks = f"{NAMA_HARI[d.weekday()]}, {teks}"
    return teks


def tarikh_pendek(iso):
    """Tukar '2026-09-19' jadi '19/09'."""
    try:
        d = date.fromisoformat(iso)
    except (ValueError, TypeError):
        return str(iso) if iso else "-"
    return f"{d.day:02d}/{d.month:02d}"


def parse_tarikh(teks):
    """Terima pelbagai format tarikh. Pulangkan date, atau None."""
    if not teks:
        return None
    s = teks.strip().lower()
    hari_ini = date.today()

    if s in ("h", "hari ini", "harini", "today"):
        return hari_ini
    if s in ("s", "semalam", "yesterday"):
        return hari_ini - timedelta(days=1)

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass

    padan = re.fullmatch(r"(\d{1,2})[/-](\d{1,2})", s)
    if padan:
        try:
            return date(hari_ini.year, int(padan.group(2)), int(padan.group(1)))
        except ValueError:
            return None

    # Satu nombor sahaja = hari dalam bulan ini.
    if re.fullmatch(r"\d{1,2}", s):
        try:
            return date(hari_ini.year, hari_ini.month, int(s))
        except ValueError:
            return None

    return None


def tanya_tarikh(label="Tarikh"):
    """
    Tanya tarikh. Enter kosong bermakna hari ini.

    Input dibaca terus (bukan melalui `tanya`) supaya paparan cadangan
    yang cantik — '19 Sep 2026' — tidak tersalah anggap sebagai nilai
    yang perlu dihurai semula oleh `parse_tarikh`, yang tidak faham
    format itu.
    """
    hari_ini = date.today()
    print()
    maklum("Boleh taip: 19/09  ·  19-09-2026  ·  semalam  ·  atau ENTER untuk hari ini")
    while True:
        try:
            nilai = input(f"  {label} [{tarikh_my(hari_ini.isoformat())}]: ").strip()
        except EOFError:
            print()
            raise InputTamat
        except KeyboardInterrupt:
            print()
            raise
        if not nilai:
            return hari_ini
        d = parse_tarikh(nilai)
        if d:
            return d
        ralat("Tarikh tidak difahami. Cuba lagi (cth: 19/09).")


def normal(teks):
    """Buang tanda baca dan huruf besar untuk carian yang lebih longgar."""
    teks = (teks or "").lower()
    teks = re.sub(r"[^a-z0-9 ]+", "", teks)
    return " ".join(teks.split())
