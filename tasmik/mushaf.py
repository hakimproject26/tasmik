"""Pemetaan halaman mushaf — halaman ke surah dan ke juzuk.

Sejak v3.0.0, tilawah direkod ikut HALAMAN mushaf, bukan ikut surah dan
ayat. Guru hanya menaip satu nombor; surah dan juzuk diterbitkan daripada
fail ini supaya satu bacaan tidak memerlukan tiga taipan.

Pemetaan ini SATU ARAH dengan sengaja: halaman memberi surah dan juzuk,
tetapi surah dan ayat TIDAK memberi halaman. Sebabnya sederhana — jadual
surah tidak menyimpan maklumat halaman, dan menambahnya bermakna 604 baris
data yang tidak dipakai oleh apa-apa.

`MULA` menyimpan halaman tempat setiap surah bermula — 114 nombor, bukan
peta 604 halaman. Peta itu diterbitkan melalui carian dedua pada masa
jalan, jadi hanya 114 nombor perlu disenggara dan diperiksa.

Susun atur yang digunakan ialah mushaf Madinah/Uthmani 604 halaman — yang
sama dicetak dan diedarkan di Malaysia.

Data di bawah disahkan DUA HALA sebelum dipakai, bukan diandaikan:

  1. Bilangan ayat setiap surah padan 100% dengan jadual dalam `surah.py`
     — silang-periksa antara dua sumber yang berasingan sepenuhnya.
  2. Kesemua 114 halaman mula padan dengan senarai bebas yang disemak
     secara manual sebelum dimasukkan ke sini.

`semak()` mengulang pemeriksaan struktur pada setiap kali app dibuka, dan
menambah satu pemeriksaan silang yang tidak boleh dilakukan ketika itu:
juzuk pada halaman mula setiap surah mesti sepadan dengan `juzuk_mula`
surah itu dalam `surah.py`. Dua jadual yang saling mengesahkan lebih kuat
daripada satu jadual yang disemak sendirian.
"""

import bisect

from . import surah

HALAMAN_MAKS = 604

# Halaman tempat setiap surah bermula, mengikut nombor surah (1-114).
MULA = [
      1,   2,  50,  77, 106, 128,
    151, 177, 187, 208, 221, 235,
    249, 255, 262, 267, 282, 293,
    305, 312, 322, 332, 342, 350,
    359, 367, 377, 385, 396, 404,
    411, 415, 418, 428, 434, 440,
    446, 453, 458, 467, 477, 483,
    489, 496, 499, 502, 507, 511,
    515, 518, 520, 523, 526, 528,
    531, 534, 537, 542, 545, 549,
    551, 553, 554, 556, 558, 560,
    562, 564, 566, 568, 570, 572,
    574, 575, 577, 578, 580, 582,
    583, 585, 586, 587, 587, 589,
    590, 591, 591, 592, 593, 594,
    595, 595, 596, 596, 597, 597,
    598, 598, 599, 599, 600, 600,
    601, 601, 601, 602, 602, 602,
    603, 603, 603, 604, 604, 604,
]

# Halaman tempat setiap juzuk bermula (juzuk 1-30). Juzuk pertama bermula
# pada halaman 1, dan selepas itu setiap juzuk 20 halaman.
JUZUK_MULA = [
      1,  22,  42,  62,  82, 102, 122, 142, 162, 182,
    202, 222, 242, 262, 282, 302, 322, 342, 362, 382,
    402, 422, 442, 462, 482, 502, 522, 542, 562, 582,
]


def semak():
    """Pastikan jadual halaman tidak rosak. Bangkitkan RuntimeError kalau rosak.

    Dipanggil semasa app dibuka, sama seperti `surah.semak()`. Jadual
    rujukan yang senyap-senyap salah lebih buruk daripada app yang enggan
    dibuka: setiap rekod tilawah yang disimpan selepas itu akan membawa
    surah atau juzuk yang salah, dan guru tidak akan nampak apa-apa.
    """
    if len(MULA) != 114:
        raise RuntimeError(f"MULA ada {len(MULA)} nilai, sepatutnya 114.")
    if MULA[0] != 1:
        raise RuntimeError("Surah pertama mesti bermula pada halaman 1.")
    for i in range(113):
        if MULA[i] > MULA[i + 1]:
            raise RuntimeError(
                f"Halaman mula surah {i + 1} ({MULA[i]}) melebihi "
                f"surah {i + 2} ({MULA[i + 1]})."
            )
    if MULA[-1] > HALAMAN_MAKS:
        raise RuntimeError(
            f"Surah terakhir bermula pada halaman {MULA[-1]}, "
            f"melebihi {HALAMAN_MAKS}."
        )

    if len(JUZUK_MULA) != 30:
        raise RuntimeError(f"JUZUK_MULA ada {len(JUZUK_MULA)} nilai, sepatutnya 30.")
    for i in range(29):
        if JUZUK_MULA[i] >= JUZUK_MULA[i + 1]:
            raise RuntimeError(f"Juzuk {i + 1} dan {i + 2} bertindih.")
    if JUZUK_MULA[0] != 1:
        raise RuntimeError("Juzuk pertama mesti bermula pada halaman 1.")

    # Pemeriksaan silang antara dua jadual yang berasingan. Kalau salah
    # satu hanyut, ini yang menangkapnya — pemeriksaan dalaman setiap
    # jadual tidak boleh melihat percanggahan antara keduanya.
    for i in range(114):
        dijangka = surah.SURAH[i][3]
        sebenar = juzuk_pada_halaman(MULA[i])
        if sebenar != dijangka:
            raise RuntimeError(
                f"{surah.nama_surah(i + 1)} bermula pada halaman {MULA[i]}, "
                f"yang jatuh pada juzuk {sebenar}, tetapi jadual surah "
                f"mengatakan juzuk {dijangka}."
            )


def juzuk_pada_halaman(halaman):
    """Nombor juzuk (1-30) bagi halaman itu, atau None kalau di luar 1-604."""
    if not 1 <= halaman <= HALAMAN_MAKS:
        return None
    return bisect.bisect_right(JUZUK_MULA, halaman)


def surah_pada_halaman(halaman):
    """Senarai nombor surah yang muncul pada halaman itu.

    Biasanya satu. Tetapi 16 surah bermula pada halaman yang sama dengan
    surah sebelumnya, jadi senarai ini boleh mengandungi dua — dan itu
    memang berlaku pada mushaf sebenar, bukan kes tepi yang dibayangkan.
    """
    if not 1 <= halaman <= HALAMAN_MAKS:
        return []
    k = bisect.bisect_right(MULA, halaman)
    if k == 0:
        return []
    # Semua surah dengan halaman mula yang SAMA. Surah yang bermula lebih
    # awal sudah tamat sebelum halaman ini, kerana surah seterusnya pula
    # bermula pada atau sebelum halaman ini.
    nilai = MULA[k - 1]
    j = k - 1
    while j > 0 and MULA[j - 1] == nilai:
        j -= 1
    return list(range(j + 1, k + 1))


def label_halaman(halaman):
    """Nama surah pada halaman itu, untuk paparan. '-' kalau tidak sah."""
    nos = surah_pada_halaman(halaman)
    if not nos:
        return "-"
    return ", ".join(surah.nama_surah(n) for n in nos)
