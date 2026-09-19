"""Pengesahan tandatangan Ed25519 — sahkan sahaja, tiada kod menandatangani.

App ini mengemas kini dirinya sendiri dengan memuat turun arkib kod dan
menimpanya. Tanpa pengesahan, sesiapa yang mengawal pelayan — atau
sesiapa yang boleh memintas trafik dalam rangkaian yang sama — boleh
menghantar apa-apa kod, dan telefon akan menjalankannya.

Modul ini menutup lubang itu. Arkib mesti ditandatangani dengan kunci
rahsia tuan; modul ini memegang kunci AWAM, jadi ia boleh mengesahkan
tetapi tidak boleh mencipta tandatangan. Kod menandatangani ada dalam
`alat/tanda.py`, dan folder itu SENGAJA tidak dimasukkan ke dalam arkib.

Kenapa kunci ada di sini dan bukan dalam `data/config.json`: fail itu
boleh ditulis pengguna, dan alamat pelayan pun boleh disunting di
Tetapan. Sauh kepercayaan mesti berada dalam kod yang SUDAH DIPASANG di
telefon — kod itu hanya boleh ditukar oleh kemas kini yang ditandatangani
oleh kunci itu sendiri.

Kenapa ini ditulis dengan tangan: app ini hanya guna pustaka standard
Python, dan pustaka standard tiada kripto kunci awam. Kod ini dijalankan
terhadap vektor ujian rasmi RFC 8032 (`ujian/test_tandatangan.py`) dan
disilang-periksa dengan openssl pada SETIAP binaan (lihat
`alat/tanda.py sahkan`, dipanggil oleh `bina.sh`). Ia tidak dibiarkan
tidak diuji.

`KUNCI` ialah SENARAI, bukan satu kunci. Sebabnya bukan keselesaan:
kalau frasa laluan kunci hilang, kunci baharu mesti sampai ke telefon,
dan ia hanya boleh sampai melalui kemas kini yang ditandatangani oleh
kunci LAMA. Itu lingkaran mati. Senarai membenarkan putaran — tambah
kunci baharu, terbitkan, kemudian buang yang lama.
"""

import hashlib

# ------------------------------------------------------------------ tetapan

# Kunci awam yang diterima. Setiap satu 32 bait. Lulus jika MANA-MANA satu
# mengesahkan. Kunci rahsia yang sepadan disimpan di luar repo, disulitkan
# dengan frasa laluan — lihat alat/tanda.py.
#
# KOSONG BERMAKNA GAGAL TERTUTUP: `sahkan()` menolak segala-galanya apabila
# senarai ini kosong. Ia tidak sekali-kali "terbuka" secara senyap.
#
# Untuk mengisinya: jalankan `python3 alat/tanda.py jana`, kemudian tampal
# baris `bytes.fromhex("…"),` yang dicetaknya di bawah ini.
KUNCI = [
    # Belum dijana. Lihat arahan di atas.
]

# Mesej kegagalan. Dipulangkan sebagai SEBAB, bukan sekadar False, supaya
# tiga kegagalan yang berbeza tidak kelihatan sama pada skrin.
TIADA = "Tandatangan tidak disertakan oleh pelayan — kemas kini dibatalkan."
ROSAK = "Fail tandatangan rosak — kemas kini dibatalkan."
TAK_PADAN = ("Tandatangan tidak sah — arkib ini bukan daripada tuan. "
             "Kemas kini dibatalkan.")


# ------------------------------------------------------------------ lengkung

_q = 2 ** 255 - 19
_l = 2 ** 252 + 27742317777372353535851937790883648493
_d = -121665 * pow(121666, _q - 2, _q) % _q
_I = pow(2, (_q - 1) // 4, _q)
_IDENTITI = (0, 1)


def _inv(x):
    return pow(x % _q, _q - 2, _q)


def _tambah(P, Q):
    x1, y1 = P
    x2, y2 = Q
    k = _d * x1 * x2 * y1 * y2
    x3 = (x1 * y2 + x2 * y1) * _inv(1 + k)
    y3 = (y1 * y2 + x1 * x2) * _inv(1 - k)
    return (x3 % _q, y3 % _q)


def _darab(P, e):
    """[e]P — berganda-dan-tambah, secara gelung supaya tiada had rekursi."""
    hasil = _IDENTITI
    while e > 0:
        if e & 1:
            hasil = _tambah(hasil, P)
        P = _tambah(P, P)
        e >>= 1
    return hasil


def _pulih_x(y):
    """Pulihkan x daripada y. None kalau titik ini tiada pada lengkung.

    Sentiasa memulangkan punca yang GENAP. Lengkung ini ada dua punca bagi
    setiap y, dan bit tanda dalam pengekodan memilih antara keduanya — jadi
    pilihan di sini mesti tetap, kalau tidak titik asas menjadi -B dan
    semua pengesahan gagal. Pemanggil yang memerlukan punca ganjil
    menukarnya sendiri.
    """
    xx = (y * y - 1) * _inv(_d * y * y + 1) % _q
    x = pow(xx, (_q + 3) // 8, _q)
    if (x * x - xx) % _q != 0:
        x = (x * _I) % _q
    if (x * x - xx) % _q != 0:
        return None
    return _q - x if x & 1 else x


def _baca_titik(s):
    """Titik daripada 32 bait. None kalau pengekodan tidak kanonik.

    Dua pengekodan tidak kanonik ditolak di sini, dan kedua-duanya penting:
    y >= q, dan x == 0 dengan bit tanda 1. Tanpa semakan ini, satu titik
    boleh diwakili oleh lebih daripada satu rentetan bait, jadi tandatangan
    yang sama boleh dikitar semula dalam bentuk yang berbeza.
    """
    if len(s) != 32:
        return None
    y = int.from_bytes(s, "little") & ((1 << 255) - 1)
    if y >= _q:
        return None
    x = _pulih_x(y)
    if x is None:
        return None
    if x & 1 != (s[31] >> 7):
        x = _q - x
    if x == 0 and (s[31] >> 7):
        return None
    return (x, y)


def _kecil_order(P):
    """Titik tertib-kecil (torsion). Kunci awam seperti ini ditolak.

    Lapan titik ini membentuk subkumpulan kecil, jadi [8]P menjadi identiti.
    openssl menolaknya, dan kita mesti bersetuju dengan openssl — kalau
    tidak, ada tandatangan yang kita terima dan ia tolak.
    """
    return _darab(P, 8) == _IDENTITI


# ------------------------------------------------------------------ awam

def cap_jari(kunci=None, penuh=False):
    """Cap jari boleh dibaca manusia, cth. 'a1b2 c3d4 e5f6 7890'.

    Pendek (8 bait) untuk skrin; `penuh=True` untuk README, di mana ia
    dicetak supaya orang boleh mengesahkannya sendiri.
    """
    k = kunci if kunci is not None else (KUNCI[0] if KUNCI else b"")
    h = k.hex() if penuh else k[:8].hex()
    return " ".join(h[i:i + 4] for i in range(0, len(h), 4))


def sahkan(teks_sig, data):
    """Sahkan tandatangan terhadap kunci awam yang tersemat.

    Memulangkan (ok, sebab). sebab ialah rentetan Bahasa Melayu sedia untuk
    dipaparkan, dan kosong apabila ok.

    Fungsi ini TIDAK PERNAH membaling. Setiap input rosak — hex panjang
    ganjil, huruf besar, halaman HTML daripada captive portal, fail kosong —
    memulangkan (False, sebab). Sebabnya: pemanggil mesti gagal tertutup,
    dan `except` yang menangkap pengecualian daripada fungsi ini tidak boleh
    sekali-kali berakhir dengan kod yang dipasang.
    """
    # None bermakna "pelayan tidak menghantar tandatangan" — itu TIADA, bukan
    # fail yang rosak, dan guru patut melihat ayat yang berbeza. Ia dikendalikan
    # dahulu kerana ia satu-satunya jenis bukan-teks yang ada makna.
    if teks_sig is None:
        return False, TIADA
    # Jenis lain (int, senarai, kamus) pula ialah fail rosak. Tanpa semakan ini,
    # `teks_sig.strip()` di bawah membaling AttributeError — dan docstring di
    # atas berjanji fungsi ini tidak pernah membaling. Janji itulah yang
    # membolehkan pemanggil gagal tertutup tanpa `except` yang berisiko
    # menelan kegagalan sebenar.
    if not isinstance(teks_sig, (str, bytes, bytearray)):
        return False, ROSAK
    if isinstance(teks_sig, (bytes, bytearray)):
        teks_sig = teks_sig.decode("ascii", "replace")
    teks_sig = teks_sig.strip()

    if not teks_sig:
        return False, TIADA

    # 64 bait = 128 aksara hex. Panjang diperiksa SEBELUM fromhex, sebab
    # fromhex melangkau ruang di mana-mana sahaja — "aa bb" menjadi 2 bait
    # tanpa aduan.
    if len(teks_sig) != 128:
        return False, ROSAK
    try:
        sig = bytes.fromhex(teks_sig)
    except ValueError:
        return False, ROSAK

    if not KUNCI:
        # Kunci belum dijana. Gagal TERTUTUP, bukan terbuka.
        return False, TAK_PADAN

    # S mesti kurang daripada l. Tanpa semakan ini, S + l juga lulus —
    # pepijat klasik kripto tulisan tangan, dan openssl menolaknya.
    S = int.from_bytes(sig[32:], "little")
    if S >= _l:
        return False, TAK_PADAN

    for kunci in KUNCI:
        if len(kunci) != 32:
            continue
        R = _baca_titik(sig[:32])
        A = _baca_titik(kunci)
        if R is None or A is None or _kecil_order(A):
            continue
        # h TIDAK dikurangkan modulo l. Ia selamat untuk berbuat demikian
        # hanya kalau A berada dalam subkumpulan tertib prima, dan semakan
        # kecil_order di atas tidak menjamin itu — A boleh jadi tertib 2l,
        # 4l atau 8l. Pengurangan akan memecahkan kes itu, jadi jangan.
        h = int.from_bytes(
            hashlib.sha512(sig[:32] + kunci + data).digest(), "little"
        )
        if _darab(_B, S) == _tambah(R, _darab(A, h)):
            return True, ""

    return False, TAK_PADAN


# Titik asas. Dikira di sini, di bawah sekali, supaya pembaca bertemu
# `sahkan()` dahulu.
_By = 4 * _inv(5) % _q
_B = (_pulih_x(_By), _By)
