"""Enjin kemas kini — semak versi, muat turun, dan pasang sendiri.

App hubungi pelayan, bandingkan versi, dan kalau ada yang lebih baharu ia
muat turun arkib dan timpa fail kod yang lama. Semuanya dari dalam app;
guru tidak perlu buka terminal dan taip apa-apa.

    ┌──────────────────────────────────────────────────────────────┐
    │  ARKIB MESTI DITANDATANGANI.                                 │
    │                                                              │
    │  Tandatangan diperiksa terhadap kunci awam yang tersemat      │
    │  dalam `tasmik/tandatangan.py` — sebelum satu bait pun        │
    │  diekstrak. Arkib yang tidak ditandatangani, tandatangan      │
    │  yang rosak, atau tandatangan yang tidak sepadan kesemuanya   │
    │  DITOLAK. Tiada suis untuk mematikan pemeriksaan ini.         │
    │                                                              │
    │  Yang MASIH tidak dilindungi: pemasangan PERTAMA. Masa itu,   │
    │  `pasang.sh` dan arkib datang dari pelayan yang sama, jadi    │
    │  penyerang yang menguasai pelayan boleh menukar kedua-duanya  │
    │  sekali gus. Ambil `pasang.sh` dari GitHub untuk menutup      │
    │  jurang itu — lihat README, bahagian "Nota keselamatan".      │
    │  Selepas pemasangan pertama, pelayan tidak lagi berkuasa.     │
    └──────────────────────────────────────────────────────────────┘

Yang lain yang ada di sini, dan sebabnya:

  * Had saiz muat turun. Muat turun berlaku SEBELUM apa-apa diperiksa,
    jadi pelayan yang rosak boleh menghantar strim tanpa penghujung dan
    menghabiskan memori telefon.
  * Semakan laluan dalam arkib. Arkib yang mengandungi `..` atau laluan
    mutlak boleh menulis ke luar folder app.
  * Nombor versi dalam arkib mesti sama dengan yang dijanjikan. Tanpa ini,
    arkib lama yang tulen boleh dikitar semula untuk menurunkan versi.
  * Salinan kod lama ke `.backup/` sebelum menimpa. Bukan rollback
    automatik — cuma jaring keselamatan.

Fail `data/` tidak pernah disentuh: arkib yang dibina memang mengecualikan
`data`, dan data guru sebenarnya tinggal di `~/.tasmik/`, di luar folder
app sepenuhnya.
"""

import json
import os
import re
import socket
import tarfile
import tempfile
import urllib.error
import urllib.request

from . import tandatangan, versi

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_SALINAN = os.path.join(AKAR, ".backup")

NAMA_VERSI = "versi.json"
NAMA_ARKIB = "tasmik.tar.gz"
NAMA_SIG = NAMA_ARKIB + ".sig"

MASA_TAMAT = 3         # saat — semakan versi (fail kecil)
MASA_TAMAT_MUAT = 60   # saat — muat turun arkib penuh
MASA_TAMAT_TANDA = 10  # saat — fail tandatangan (129 bait)

# Arkib sebenar ~50 KB. Had ini wujud kerana muat turun berlaku SEBELUM
# apa-apa diperiksa.
SAIZ_MAKS = 20 * 1024 * 1024

# Tandatangan ialah 128 aksara hex + newline. Had ini jauh lebih besar
# daripada itu, tetapi jauh lebih kecil daripada SAIZ_MAKS: pelayan yang
# diceroboh tidak sepatutnya boleh membuat telefon memperuntukkan 20 MB
# untuk fail yang sepatutnya 129 bait.
SAIZ_MAKS_SIG = 4096

# Nombor versi yang sah. `_nombor()` sengaja pemaaf — ia mengira bahagian
# bukan angka sebagai 0 — jadi versi cacat mesti ditolak di sini.
_RE_VERSI = re.compile(r"^\d+(\.\d+){0,2}$")

# Aksara kawalan terminal. Medan `nota` dicetak ke skrin pada setiap kali
# app dibuka, sebelum apa-apa pengesahan berjalan. Pelayan yang rosak boleh
# menyelitkan "\x1b[2J\x1b[H" di situ dan melukis semula terminal.
_RE_KAWAL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


# ------------------------------------------------------------------ bantu

def betulkan(sumber):
    """Kemas alamat yang ditaip guru.

    Terima '192.168.1.10:8001' sepatah — tambah 'http://' sendiri.
    """
    s = (sumber or "").strip().rstrip("/")
    if s and "://" not in s:
        s = "http://" + s
    return s


def _nombor(teks):
    """Tukar '1.2.3' jadi (1, 2, 3) supaya boleh dibandingkan."""
    bahagian = []
    for keping in str(teks).split("."):
        try:
            bahagian.append(int(keping))
        except ValueError:
            bahagian.append(0)
    while len(bahagian) < 3:
        bahagian.append(0)
    return tuple(bahagian[:3])


def _bersih(teks):
    """Buang aksara kawalan terminal. Lihat _RE_KAWAL."""
    return _RE_KAWAL.sub("", str(teks))


def _ambil(url, masa_tamat, maks=SAIZ_MAKS):
    """Muat turun, dengan had saiz."""
    with urllib.request.urlopen(url, timeout=masa_tamat) as jawapan:
        dijangka = jawapan.headers.get("Content-Length")
        if dijangka and dijangka.isdigit() and int(dijangka) > maks:
            raise ValueError(
                f"fail itu {int(dijangka) / 1048576:.1f} MB, sedangkan had "
                f"ialah {maks // 1048576} MB"
            )
        # Baca maks + 1 bait, bukan maks. Kalau tidak, fail yang tepat-tepat
        # melebihi had kelihatan sama panjang dengan fail yang cukup.
        data = jawapan.read(maks + 1)
        if len(data) > maks:
            raise ValueError(
                f"fail itu melebihi had {maks // 1048576} MB — pelayan "
                "menghantar lebih daripada yang diminta"
            )
        return data


def _mesej_ralat(e):
    """Tukar ralat teknikal jadi ayat yang boleh difahami guru."""
    if isinstance(e, urllib.error.HTTPError):
        if e.code == 404:
            return "Pelayan hidup, tetapi fail itu tiada (404)."
        return f"Pelayan jawab dengan ralat {e.code}."
    if isinstance(e, urllib.error.URLError):
        sebab = getattr(e, "reason", None)
        if isinstance(sebab, (socket.timeout, TimeoutError)):
            return f"Tiada jawapan dalam {MASA_TAMAT} saat."
        if isinstance(sebab, ConnectionRefusedError):
            return "Pelayan menolak sambungan — ia mungkin tidak hidup."
        return f"Tak dapat hubungi pelayan ({sebab})."
    if isinstance(e, (socket.timeout, TimeoutError)):
        return f"Tiada jawapan dalam {MASA_TAMAT} saat."
    return f"Ralat: {e}"


# ------------------------------------------------------------------ semak

def semak(sumber):
    """Semak versi terkini di pelayan.

    Pulangkan dict. Dua bentuk:
        {"ok": True,  "ada": bool, "versi": str, "tarikh": str, "nota": [str]}
        {"ok": False, "ralat": str}

    Tidak pernah membaling ralat — semua kegagalan jadi "ok": False, supaya
    app boleh terus jalan walaupun pelayan mati.
    """
    sumber = betulkan(sumber)
    if not sumber:
        return {"ok": False, "ralat": "Sumber kemas kini belum ditetapkan."}

    try:
        mentah = _ambil(f"{sumber}/{NAMA_VERSI}", MASA_TAMAT)
    except Exception as e:  # noqa: BLE001 — apa-apa pun, jangan hembuskan
        return {"ok": False, "ralat": _mesej_ralat(e)}

    try:
        data = json.loads(mentah.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return {"ok": False, "ralat": f"{NAMA_VERSI} rosak atau bukan JSON."}

    jauh = _bersih(data.get("versi", "")).strip()
    if not jauh:
        return {"ok": False, "ralat": f"{NAMA_VERSI} tiada nombor versi."}
    if not _RE_VERSI.match(jauh):
        return {"ok": False,
                "ralat": f"{NAMA_VERSI} ada nombor versi yang tidak sah."}

    return {
        "ok": True,
        "ada": _nombor(jauh) > _nombor(versi.NOMBOR),
        "versi": jauh,
        "tarikh": _bersih(data.get("tarikh", "")),
        "nota": [_bersih(n) for n in data.get("nota", [])],
    }


# ----------------------------------------------------------------- pasang

def _periksa_arkib(laluan, dijangka, teks_sig, data):
    """Periksa arkib SEBELUM ia menyentuh apa-apa. Pulangkan (ok, mesej).

    INILAH gat tunggal untuk kemas kini — tandatangan DAN struktur, dalam
    satu fungsi yang sama. Ia sengaja tidak dipecahkan kepada dua, kerana
    fungsi berasingan mencipta jalan panggilan yang boleh memintas
    pengesahan. Satu gat, tiada jalan sekeliling.

    Urutannya mengikat, bukan gaya:

      1. Tandatangan di atas `data` — bait yang benar-benar tiba dari wayar.
      2. Baharu struktur arkib dibuka.

    `tarfile.getnames()` memaksa penyahmampatan gzip yang penuh untuk membaca
    senarai nama. Kalau struktur diperiksa dahulu, arkib bom meletup sebelum
    apa-apa disahkan. Jadi tandatangan mesti dahulu.

    `data` dihantar masuk, bukan dibaca semula dari `laluan`, supaya yang
    disahkan ialah tepat apa yang dimuat turun. Pembacaan kedua membuka
    peluang arkib berubah antara pengesahan dan pengekstrakan.
    """
    ok, sebab = tandatangan.sahkan(teks_sig, data)
    if not ok:
        return False, sebab

    # Tandatangan sah bermakna `data` tulen. Tetapi yang akan diekstrak ialah
    # `laluan`, bukan `data`. Kalau dua-dua tidak sama panjang, fail di atas
    # cakera bukan fail yang ditandatangani — dan itu mesti berhenti di sini.
    try:
        saiz_cakera = os.path.getsize(laluan)
    except OSError as e:
        return False, f"Fail arkib tidak boleh dibaca ({e})."
    if saiz_cakera != len(data):
        return False, "Fail arkib berubah selepas dimuat turun — dibatalkan."

    try:
        with tarfile.open(laluan, "r:gz") as tf:
            nama = tf.getnames()

            # Jangan benarkan arkib menulis ke luar folder app.
            for n in nama:
                if n.startswith("/") or ".." in n.split("/"):
                    return False, f"Laluan tak selamat dalam arkib: {n}"

            # Arkib mesti ada satu folder akar sahaja (cth. 'tasmik/').
            akar = {n.split("/")[0] for n in nama if "/" in n}
            if len(akar) != 1:
                return False, "Arkib mesti ada tepat satu folder akar."
            awalan = akar.pop() + "/"

            for p in ("main.py", "tasmik/versi.py"):
                if awalan + p not in nama:
                    return False, f"Arkib tak lengkap — {p} tiada."

            f = tf.extractfile(awalan + "tasmik/versi.py")
            teks = f.read().decode("utf-8", "replace") if f else ""
    except (tarfile.TarError, OSError) as e:
        return False, f"Fail rosak atau bukan arkib yang sah ({e})."

    padan = re.search(r'^NOMBOR\s*=\s*["\']([^"\']+)["\']', teks, re.M)
    if not padan:
        return False, "Tak dapat baca nombor versi dalam arkib."
    jumpa = padan.group(1)
    if dijangka and jumpa != dijangka:
        return False, f"Arkib ini versi {jumpa}, bukan {dijangka} seperti dijangka."
    return True, ""


def simpan_salinan():
    """Simpan kod versi semasa ke .backup/ sebelum ia ditimpa."""
    os.makedirs(DIR_SALINAN, exist_ok=True)
    laluan = os.path.join(DIR_SALINAN, f"tasmik-{versi.NOMBOR}.tar.gz")
    awalan = os.path.basename(AKAR) + "/"
    with tarfile.open(laluan, "w:gz") as tf:
        for item in ("main.py", "README.md", "CHANGELOG.md", "tasmik"):
            p = os.path.join(AKAR, item)
            if os.path.exists(p):
                tf.add(p, arcname=awalan + item)
    return laluan


def _ekstrak(laluan, ke):
    """Ekstrak isi arkib TERUS ke dalam folder app.

    Komponen pertama setiap nama (cth. 'tasmik/') dibuang dahulu. Tanpa
    ini, arkib masuk ke 'tasmik/tasmik/…' — satu folder terlalu dalam.
    Ia juga bermakna folder app boleh dinamakan apa sahaja.
    """
    with tarfile.open(laluan, "r:gz") as tf:
        ahli = []
        for m in tf.getmembers():
            bahagian = m.name.split("/")[1:]
            if not bahagian or not any(bahagian):
                continue  # entri akar arkib — tiada isi
            m.name = "/".join(bahagian)
            ahli.append(m)

        try:
            # Python 3.12+ — tolak laluan tak selamat, buang setuid.
            tf.extractall(path=ke, members=ahli, filter="data")
        except TypeError:
            # Python lebih lama tiada parameter `filter`. Laluan sudah
            # diperiksa dalam _periksa_arkib(), jadi ini selamat.
            tf.extractall(path=ke, members=ahli)


def pasang(sumber, versi_dijangka, lapor=None):
    """Muat turun dan pasang versi baharu.

    Pulangkan (ok, mesej_ralat, berubah).

    `berubah` menjawab soalan yang berasingan daripada kejayaan: adakah
    fail dalam folder app mungkin sudah tersentuh? Ia False untuk SEMUA
    kegagalan sebelum pengekstrakan, jadi skrin boleh mengaku "Tiada
    apa-apa diubah" dengan jujur. Ia True apabila pengekstrakan bermula,
    kerana pengekstrakan menulis terus dan boleh berhenti separuh jalan.
    """
    if lapor is None:
        lapor = lambda m: None  # noqa: E731

    sumber = betulkan(sumber)
    if not sumber:
        return False, "Sumber kemas kini belum ditetapkan.", False

    # Jaring keselamatan, bukan kawalan anti-replay: `semak()` hanya
    # menawarkan kemas kini apabila versi jauh LEBIH BESAR. Kekal `<` dan
    # bukan `<=` — `<` membenarkan pembaikan pada versi yang sama, dan itu
    # lebih berguna daripada menolaknya.
    if versi_dijangka and _nombor(versi_dijangka) < _nombor(versi.NOMBOR):
        return False, (f"Arkib itu versi {versi_dijangka}, lebih lama "
                       f"daripada {versi.NOMBOR} yang sudah dipasang."), False

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz")
    tmp.close()
    try:
        lapor(f"Memuat turun {NAMA_ARKIB} …")
        data = _ambil(f"{sumber}/{NAMA_ARKIB}", MASA_TAMAT_MUAT)
        with open(tmp.name, "wb") as f:
            f.write(data)
        lapor(f"  {len(data) / 1024:.0f} KB diterima")

        # Tandatangan dimuat turun BERASINGAN, dan ketiadaannya ialah
        # kegagalan yang tersendiri. Kalau 404 jatuh ke `_mesej_ralat()`,
        # guru akan membaca "Pelayan hidup, tetapi fail itu tiada (404)" —
        # betul secara teknikal, tetapi ia menyembunyikan sebab sebenar,
        # iaitu kemas kini dibatalkan kerana KESELAMATAN.
        lapor(f"Memuat turun {NAMA_SIG} …")
        try:
            mentah_sig = _ambil(f"{sumber}/{NAMA_SIG}", MASA_TAMAT_TANDA,
                                maks=SAIZ_MAKS_SIG)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False, (
                    f"Pelayan ini tidak menyediakan {NAMA_SIG}, jadi "
                    "tandatangan tak dapat diperiksa. Kemas kini dibatalkan — "
                    "tiada apa-apa diubah."
                ), False
            return False, _mesej_ralat(e), False
        except Exception as e:  # noqa: BLE001
            return False, _mesej_ralat(e), False

        lapor("Mengesahkan tandatangan …")
        ok, mesej = _periksa_arkib(
            tmp.name, versi_dijangka,
            mentah_sig.decode("ascii", "replace"), data)
        if not ok:
            # Gagal TERTUTUP. Setiap kegagalan di sini berlaku SEBELUM
            # pengekstrakan, jadi `berubah=False` sentiasa betul.
            return False, mesej, False
        lapor("  ✓ tandatangan sah, arkib utuh")

        lapor("Menyimpan salinan lama …")
        simpan_salinan()
        lapor(f"  ✓ {os.path.basename(DIR_SALINAN)}/")

        lapor("Memasang …")
        try:
            _ekstrak(tmp.name, AKAR)
        except Exception as e:  # noqa: BLE001
            return False, (f"Sebahagian fail sudah ditulis, kemudian gagal "
                           f"({e}). Salinan kod lama ada dalam "
                           f"{os.path.basename(DIR_SALINAN)}/ — pasang semula "
                           f"dari situ."), True
        lapor("  ✓ selesai")
        return True, "", True

    except Exception as e:  # noqa: BLE001
        return False, _mesej_ralat(e), False
    finally:
        # Arkib muat turun mesti dibuang dalam SEMUA jalan keluar.
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
