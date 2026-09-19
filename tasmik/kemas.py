"""Enjin kemas kini — semak versi, muat turun, dan pasang sendiri.

App hubungi pelayan, bandingkan versi, dan kalau ada yang lebih baharu ia
muat turun arkib dan timpa fail kod yang lama. Semuanya dari dalam app;
guru tidak perlu buka terminal dan taip apa-apa.

    ┌──────────────────────────────────────────────────────────────┐
    │  BELUM ADA PENGESAHAN TANDATANGAN.                           │
    │                                                              │
    │  Arkib yang dimuat turun TIDAK diperiksa tandatangannya.     │
    │  Sesiapa yang boleh menjawab pada alamat pelayan itu boleh   │
    │  menghantar kod yang akan dijalankan pada telefon ini.       │
    │                                                              │
    │  App rujukan (taksiran) sudah ada pengesahan Ed25519. Ia     │
    │  belum dibawa ke sini. Untuk menambahnya kemudian, tempat   │
    │  yang betul ialah di dalam `_periksa()` di bawah — satu gat  │
    │  tunggal, sebelum apa-apa diekstrak.                         │
    └──────────────────────────────────────────────────────────────┘

Yang SUDAH ada di sini, dan sebabnya:

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

from . import versi

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_SALINAN = os.path.join(AKAR, ".backup")

NAMA_VERSI = "versi.json"
NAMA_ARKIB = "tasmik.tar.gz"

MASA_TAMAT = 3         # saat — semakan versi (fail kecil)
MASA_TAMAT_MUAT = 60   # saat — muat turun arkib penuh

# Arkib sebenar ~50 KB. Had ini wujud kerana muat turun berlaku SEBELUM
# apa-apa diperiksa.
SAIZ_MAKS = 20 * 1024 * 1024

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

    Terima '100.78.29.8:8001' sepatah — tambah 'http://' sendiri.
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

def _periksa_arkib(laluan, dijangka):
    """Periksa struktur arkib SEBELUM ia menyentuh apa-apa.

    Pulangkan (ok, mesej).

    INILAH gat tunggal untuk kemas kini. Kalau pengesahan tandatangan
    ditambah kemudian, ia masuk di sini — sebelum `tarfile.open()`, supaya
    arkib yang tidak dipercayai tidak pernah sampai ke peringkat
    penyahmampatan.
    """
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

        lapor("Memeriksa arkib …")
        ok, mesej = _periksa_arkib(tmp.name, versi_dijangka)
        if not ok:
            # Gagal TERTUTUP.
            return False, mesej, False
        lapor("  ✓ arkib utuh")

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
