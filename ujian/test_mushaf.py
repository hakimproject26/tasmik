"""Ujian untuk jadual rujukan halaman mushaf.

Jadual dalam `tasmik/mushaf.py` ialah data, bukan kod — dan data yang salah
tidak menghasilkan ralat. Ia menghasilkan rekod tilawah yang membawa surah
atau juzuk yang salah, senyap-senyap, selama-lamanya.

Sebab itu ujian di sini memeriksa DUA perkara yang berbeza:

  1. Jadual itu konsisten dengan dirinya sendiri (menaik, lengkap, sempadan
     betul).
  2. Jadual itu konsisten dengan `surah.py` — silang-periksa antara dua
     sumber yang disenggara berasingan.

Yang kedua itu lebih bernilai. Jadual yang salah tetapi konsisten dengan
dirinya sendiri akan lulus kumpulan ujian pertama dengan jayanya.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasmik import mushaf, surah  # noqa: E402


class UjianJadual(unittest.TestCase):
    def test_semak_lulus(self):
        mushaf.semak()

    def test_114_surah(self):
        self.assertEqual(len(mushaf.MULA), 114)

    def test_30_juzuk(self):
        self.assertEqual(len(mushaf.JUZUK_MULA), 30)

    def test_halaman_mula_tidak_menurun(self):
        for i in range(113):
            self.assertLessEqual(mushaf.MULA[i], mushaf.MULA[i + 1])

    def test_sempadan_mushaf(self):
        self.assertEqual(mushaf.MULA[0], 1)
        self.assertEqual(mushaf.MULA[-1], mushaf.HALAMAN_MAKS)

    def test_setiap_surah_bermula_dalam_juzuk_yang_dijangka(self):
        """Silang-periksa dengan jadual surah — pemeriksaan paling bernilai di sini."""
        for i in range(114):
            dijangka = surah.SURAH[i][3]
            sebenar = mushaf.juzuk_pada_halaman(mushaf.MULA[i])
            self.assertEqual(
                sebenar, dijangka,
                f"{surah.nama_surah(i + 1)} @ halaman {mushaf.MULA[i]}",
            )


class UjianCarian(unittest.TestCase):
    def test_halaman_pertama(self):
        self.assertEqual(mushaf.surah_pada_halaman(1), [1])
        self.assertEqual(mushaf.juzuk_pada_halaman(1), 1)

    def test_halaman_terakhir(self):
        self.assertEqual(mushaf.surah_pada_halaman(604), [112, 113, 114])
        self.assertEqual(mushaf.juzuk_pada_halaman(604), 30)

    def test_halaman_berkongsi(self):
        """16 surah bermula pada halaman yang sama dengan surah sebelumnya."""
        self.assertEqual(mushaf.surah_pada_halaman(587), [82, 83])
        self.assertEqual(mushaf.label_halaman(587), "Al-Infitar, Al-Mutaffifin")

    def test_bilangan_halaman_berkongsi(self):
        kongsi = sum(1 for i in range(1, 114) if mushaf.MULA[i] == mushaf.MULA[i - 1])
        self.assertEqual(kongsi, 16)

    def test_setiap_halaman_dalam_julat_mempunyai_surah(self):
        """Tiada lubang: setiap halaman 1-604 mesti memetakan ke sekurang-kurangnya satu surah."""
        for p in range(1, mushaf.HALAMAN_MAKS + 1):
            self.assertTrue(mushaf.surah_pada_halaman(p), f"halaman {p} kosong")
            self.assertIsNotNone(mushaf.juzuk_pada_halaman(p), f"halaman {p}")

    def test_setiap_surah_boleh_dicapai(self):
        """Halaman mula setiap surah mesti memetakan kembali kepada surah itu."""
        for i in range(114):
            self.assertIn(i + 1, mushaf.surah_pada_halaman(mushaf.MULA[i]))

    def test_juzuk_bermula_pada_halamannya(self):
        for n, p in enumerate(mushaf.JUZUK_MULA, 1):
            self.assertEqual(mushaf.juzuk_pada_halaman(p), n)

    def test_luar_julat(self):
        for p in (0, -1, 605, 9999):
            self.assertEqual(mushaf.surah_pada_halaman(p), [])
            self.assertIsNone(mushaf.juzuk_pada_halaman(p))
            self.assertEqual(mushaf.label_halaman(p), "-")


if __name__ == "__main__":
    unittest.main()
