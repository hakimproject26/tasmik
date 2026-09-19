"""Data 114 surah dan cariannya.

Setiap surah disimpan sebagai tuple:

    (nombor, nama, bilangan_ayat, juzuk_mula, juzuk_akhir)

Nombor surah ialah indeks + 1, jadi `SURAH[no - 1]` memberi surah bernombor
`no`. Ini dijaga oleh `semak()` di bawah, yang dipanggil semasa app dibuka
— data rujukan yang senyap-senyap salah lebih buruk daripada app yang
enggan dibuka.
"""

from . import ui

# (nombor, nama, bilangan ayat, juzuk mula, juzuk akhir)
SURAH = [
    (1, 'Al-Fatihah', 7, 1, 1),
    (2, 'Al-Baqarah', 286, 1, 3),
    (3, "Ali 'Imran", 200, 3, 4),
    (4, "An-Nisa'", 176, 4, 6),
    (5, "Al-Ma'idah", 120, 6, 7),
    (6, "Al-An'am", 165, 7, 8),
    (7, "Al-A'raf", 206, 8, 9),
    (8, 'Al-Anfal', 75, 9, 10),
    (9, 'At-Taubah', 129, 10, 11),
    (10, 'Yunus', 109, 11, 11),
    (11, 'Hud', 123, 11, 12),
    (12, 'Yusuf', 111, 12, 13),
    (13, "Ar-Ra'd", 43, 13, 13),
    (14, 'Ibrahim', 52, 13, 13),
    (15, 'Al-Hijr', 99, 14, 14),
    (16, 'An-Nahl', 128, 14, 14),
    (17, "Al-Isra'", 111, 15, 15),
    (18, 'Al-Kahf', 110, 15, 16),
    (19, 'Maryam', 98, 16, 16),
    (20, 'Ta-Ha', 135, 16, 16),
    (21, "Al-Anbiya'", 112, 17, 17),
    (22, 'Al-Hajj', 78, 17, 17),
    (23, "Al-Mu'minun", 118, 18, 18),
    (24, 'An-Nur', 64, 18, 18),
    (25, 'Al-Furqan', 77, 18, 19),
    (26, "Asy-Syu'ara'", 227, 19, 19),
    (27, 'An-Naml', 93, 19, 20),
    (28, 'Al-Qasas', 88, 20, 20),
    (29, "Al-'Ankabut", 69, 20, 21),
    (30, 'Ar-Rum', 60, 21, 21),
    (31, 'Luqman', 34, 21, 21),
    (32, 'As-Sajdah', 30, 21, 21),
    (33, 'Al-Ahzab', 73, 21, 22),
    (34, "Saba'", 54, 22, 22),
    (35, 'Fatir', 45, 22, 22),
    (36, 'Ya-Sin', 83, 22, 23),
    (37, 'As-Saffat', 182, 23, 23),
    (38, 'Sad', 88, 23, 23),
    (39, 'Az-Zumar', 75, 23, 24),
    (40, 'Ghafir', 85, 24, 24),
    (41, 'Fussilat', 54, 24, 25),
    (42, 'Asy-Syura', 53, 25, 25),
    (43, 'Az-Zukhruf', 89, 25, 25),
    (44, 'Ad-Dukhan', 59, 25, 25),
    (45, 'Al-Jasiyah', 37, 25, 25),
    (46, 'Al-Ahqaf', 35, 26, 26),
    (47, 'Muhammad', 38, 26, 26),
    (48, 'Al-Fath', 29, 26, 26),
    (49, 'Al-Hujurat', 18, 26, 26),
    (50, 'Qaf', 45, 26, 26),
    (51, 'Az-Zariyat', 60, 26, 27),
    (52, 'At-Tur', 49, 27, 27),
    (53, 'An-Najm', 62, 27, 27),
    (54, 'Al-Qamar', 55, 27, 27),
    (55, 'Ar-Rahman', 78, 27, 27),
    (56, "Al-Waqi'ah", 96, 27, 27),
    (57, 'Al-Hadid', 29, 27, 27),
    (58, 'Al-Mujadalah', 22, 28, 28),
    (59, 'Al-Hasyr', 24, 28, 28),
    (60, 'Al-Mumtahanah', 13, 28, 28),
    (61, 'As-Saff', 14, 28, 28),
    (62, "Al-Jumu'ah", 11, 28, 28),
    (63, 'Al-Munafiqun', 11, 28, 28),
    (64, 'At-Taghabun', 18, 28, 28),
    (65, 'At-Talaq', 12, 28, 28),
    (66, 'At-Tahrim', 12, 28, 28),
    (67, 'Al-Mulk', 30, 29, 29),
    (68, 'Al-Qalam', 52, 29, 29),
    (69, 'Al-Haqqah', 52, 29, 29),
    (70, "Al-Ma'arij", 44, 29, 29),
    (71, 'Nuh', 28, 29, 29),
    (72, 'Al-Jinn', 28, 29, 29),
    (73, 'Al-Muzzammil', 20, 29, 29),
    (74, 'Al-Muddassir', 56, 29, 29),
    (75, 'Al-Qiyamah', 40, 29, 29),
    (76, 'Al-Insan', 31, 29, 29),
    (77, 'Al-Mursalat', 50, 29, 29),
    (78, "An-Naba'", 40, 30, 30),
    (79, "An-Nazi'at", 46, 30, 30),
    (80, "'Abasa", 42, 30, 30),
    (81, 'At-Takwir', 29, 30, 30),
    (82, 'Al-Infitar', 19, 30, 30),
    (83, 'Al-Mutaffifin', 36, 30, 30),
    (84, 'Al-Insyiqaq', 25, 30, 30),
    (85, 'Al-Buruj', 22, 30, 30),
    (86, 'At-Tariq', 17, 30, 30),
    (87, "Al-A'la", 19, 30, 30),
    (88, 'Al-Gasyiyah', 26, 30, 30),
    (89, 'Al-Fajr', 30, 30, 30),
    (90, 'Al-Balad', 20, 30, 30),
    (91, 'Asy-Syams', 15, 30, 30),
    (92, 'Al-Lail', 21, 30, 30),
    (93, 'Ad-Duha', 11, 30, 30),
    (94, 'Asy-Syarh', 8, 30, 30),
    (95, 'At-Tin', 8, 30, 30),
    (96, "Al-'Alaq", 19, 30, 30),
    (97, 'Al-Qadr', 5, 30, 30),
    (98, 'Al-Bayyinah', 8, 30, 30),
    (99, 'Az-Zalzalah', 8, 30, 30),
    (100, "Al-'Adiyat", 11, 30, 30),
    (101, "Al-Qari'ah", 11, 30, 30),
    (102, 'At-Takasur', 8, 30, 30),
    (103, "Al-'Asr", 3, 30, 30),
    (104, 'Al-Humazah', 9, 30, 30),
    (105, 'Al-Fil', 5, 30, 30),
    (106, 'Quraisy', 4, 30, 30),
    (107, "Al-Ma'un", 7, 30, 30),
    (108, 'Al-Kausar', 3, 30, 30),
    (109, 'Al-Kafirun', 6, 30, 30),
    (110, 'An-Nasr', 3, 30, 30),
    (111, 'Al-Lahab', 5, 30, 30),
    (112, 'Al-Ikhlas', 4, 30, 30),
    (113, 'Al-Falaq', 5, 30, 30),
    (114, 'An-Nas', 6, 30, 30),
]

# Ejaan lain yang biasa digunakan, untuk memudahkan carian.
ALIAS = {
    2: 'baqarah baqoroh',
    3: 'imran',
    4: 'nisa',
    6: 'anam',
    7: 'araf',
    9: 'taubat taubah',
    12: 'yusuf',
    17: 'isra',
    18: 'kahfi',
    19: 'maryam mariam',
    20: 'taha toha',
    21: 'anbiya',
    23: 'mukminun',
    24: 'nur',
    25: 'furqan',
    27: 'naml',
    29: 'ankabut',
    31: 'luqman',
    32: 'sajdah sajadah',
    33: 'ahzab',
    36: 'yasin yaseen yaasin',
    37: 'saffat',
    39: 'zumar',
    40: 'ghafir mukmin',
    41: 'fussilat ha mim',
    46: 'ahqaf',
    48: 'fath',
    49: 'hujurat',
    50: 'qaf',
    51: 'zariyat',
    53: 'najm',
    54: 'qamar',
    55: 'rahman',
    56: "waqiah waqi'ah",
    57: 'hadid',
    58: 'mujadalah',
    59: 'hasyr',
    62: 'jumuah jumaat',
    63: 'munafiqun',
    64: 'taghabun',
    65: 'talaq',
    66: 'tahrim',
    67: 'mulk',
    68: 'qalam',
    69: 'haqqah',
    70: 'maarij',
    72: 'jinn jin',
    73: 'muzzammil',
    74: 'muddassir mudatsir',
    75: 'qiyamah',
    76: 'insan',
    77: 'mursalat',
    78: "naba naba'",
    79: 'naziat',
    80: 'abasa',
    81: 'takwir',
    82: 'infitar',
    83: 'mutaffifin',
    84: 'insyiqaq',
    85: 'buruj',
    86: 'tariq',
    87: "a'la ala",
    88: 'gasyiyah',
    89: 'fajr',
    90: 'balad',
    91: 'syams',
    92: 'lail',
    93: 'duha dhuha',
    94: 'syarh insyirah',
    95: 'tin',
    96: 'alaq',
    97: 'qadr',
    98: 'bayyinah',
    99: 'zalzalah',
    100: 'adiyat',
    101: 'qariah',
    102: 'takasur',
    103: 'asr',
    104: 'humazah',
    105: 'fil',
    106: 'quraisy',
    107: 'maun',
    108: 'kausar kausar',
    109: 'kafirun',
    110: 'nasr',
    111: 'lahab',
    112: 'ikhlas',
    113: 'falaq',
    114: 'nas',
}


def semak():
    """Pastikan jadual surah lengkap dan konsisten.

    Dipanggil sekali semasa app dibuka. Kalau data ini rosak, setiap
    rekod yang disimpan selepas itu akan membawa nombor surah yang salah
    — jadi lebih baik gagal serta-merta dengan ayat yang jelas.
    """
    if len(SURAH) != 114:
        raise RuntimeError(f"Jadual surah ada {len(SURAH)} baris, patut 114.")
    for i, s in enumerate(SURAH, 1):
        if s[0] != i:
            raise RuntimeError(f"Baris {i} dalam jadual surah bernombor {s[0]}.")
        if not (1 <= s[2] <= 300):
            raise RuntimeError(f"Surah {i} ada bilangan ayat yang pelik: {s[2]}.")
        if not (1 <= s[3] <= s[4] <= 30):
            raise RuntimeError(f"Surah {i} ada julat juzuk yang pelik.")


def nama_surah(no):
    if no and 1 <= no <= 114:
        return SURAH[no - 1][1]
    return "?"


def ayat_surah(no):
    if no and 1 <= no <= 114:
        return SURAH[no - 1][2]
    return 0


def label_surah(no, dari=None, hingga=None):
    """Contoh: 'Al-Baqarah 1–20', 'Al-Baqarah (penuh)', atau 'Al-Baqarah'."""
    nama = nama_surah(no)
    jumlah = ayat_surah(no)
    if dari is None or hingga is None:
        return nama
    if dari == 1 and hingga == jumlah:
        return f"{nama} (penuh)"
    if dari == hingga:
        return f"{nama} {dari}"
    return f"{nama} {dari}–{hingga}"


def julat_juzuk(no):
    """Cadangan teks juzuk bagi sesuatu surah: '30' atau '1-3'."""
    if not no or not (1 <= no <= 114):
        return None
    _, _, _, j1, j2 = SURAH[no - 1]
    return str(j1) if j1 == j2 else f"{j1}-{j2}"


def hurai_juzuk(teks):
    """
    Tukar catatan juzuk yang bebas jadi set nombor juzuk.

        '30'   -> {30}
        '1-3'  -> {1, 2, 3}
        '5,7'  -> {5, 7}

    Nilai di luar 1-30 diabaikan. Guru menaip ini dengan tangan, jadi ia
    tidak boleh dianggap sentiasa kemas.
    """
    hasil = set()
    if not teks:
        return hasil
    for bahagian in str(teks).replace("–", "-").split(","):
        bahagian = bahagian.strip()
        padan = None
        if "-" in bahagian:
            kiri, _, kanan = bahagian.partition("-")
            if kiri.strip().isdigit() and kanan.strip().isdigit():
                padan = (int(kiri), int(kanan))
        if padan:
            a, b = padan
            if a > b:
                a, b = b, a
            hasil.update(j for j in range(a, b + 1) if 1 <= j <= 30)
        elif bahagian.isdigit() and 1 <= int(bahagian) <= 30:
            hasil.add(int(bahagian))
    return hasil


def ringkas_nombor(nombor):
    """[1, 2, 3, 22, 23] -> '1-3, 22-23'. Senarai kosong -> '-'."""
    nombor = sorted(set(nombor))
    if not nombor:
        return "-"
    julat, mula, akhir = [], nombor[0], nombor[0]
    for n in nombor[1:]:
        if n == akhir + 1:
            akhir = n
        else:
            julat.append((mula, akhir))
            mula = akhir = n
    julat.append((mula, akhir))
    return ", ".join(str(a) if a == b else f"{a}-{b}" for a, b in julat)


def cari_surah(kueri):
    """Cari surah ikut nombor atau sebahagian nama. Pulangkan senarai tuple."""
    q = ui.normal(kueri)
    if not q:
        return []

    if q.isdigit():
        no = int(q)
        if 1 <= no <= 114:
            return [SURAH[no - 1]]

    hasil = []
    for s in SURAH:
        no, nama = s[0], s[1]
        teks = ui.normal(nama) + " " + ALIAS.get(no, "")
        if q in teks:
            hasil.append(s)

    # Yang bermula dengan kueri didahulukan, kemudian ikut nombor surah.
    hasil.sort(key=lambda s: (0 if ui.normal(s[1]).startswith(q) else 1, s[0]))
    return hasil


def pilih_surah():
    """Pilih surah dengan carian. Pulangkan tuple surah, atau None."""
    print()
    ui.maklum("Taip nombor surah (1-114) atau sebahagian namanya.")
    ui.maklum("Contoh: 2  ·  baqarah  ·  yasin  ·  mulk")
    while True:
        kueri = ui.tanya("Surah")
        if not kueri:
            ui.ralat("Sila taip nombor atau nama surah.")
            continue

        hasil = cari_surah(kueri)
        if not hasil:
            ui.ralat(f"Tiada surah sepadan dengan '{kueri}'. Cuba lagi.")
            continue

        if len(hasil) == 1:
            s = hasil[0]
            print()
            ui.sebut(f"→ {s[0]}. {s[1]}  ({s[2]} ayat, juzuk {julat_juzuk(s[0])})")
            return s

        dipapar = hasil[:14]
        item = [
            (f"{s[0]:>3}. {s[1]}  ({s[2]} ayat)", s) for s in dipapar
        ]
        if len(hasil) > len(dipapar):
            print()
            ui.maklum(f"Ada {len(hasil)} padanan — hanya {len(dipapar)} dipaparkan.")
            ui.maklum("Taip lebih khusus untuk mengecilkan carian.")
        pilihan = ui.pilih_dari_senarai("Padanan dijumpai", item,
                                        label_batal="Taip semula")
        if pilihan:
            return pilihan
        print()
