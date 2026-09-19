"""Ujian untuk tasmik/tandatangan.py.

Jalankan dengan:

    python3 -m unittest discover -s ujian -v

Kenapa fail ini wujud: app rujukan (taksiran) mendakwa dalam docstringnya
bahawa kodnya "dijalankan terhadap vektor ujian rasmi RFC 8032", tetapi
repo itu tiada satu fail ujian pun. Dakwaan yang tidak disandarkan lebih
teruk daripada tiada dakwaan — ia membuat orang berhenti memeriksa.

Jadi di sini dakwaan itu disandarkan. Tiga kumpulan ujian:

  1. Vektor rasmi RFC 8032 §7.1 — tandatangan yang SAH mesti diterima.
  2. Kes tepi berniat jahat — mesti DITOLAK, tanpa pengecualian terlepas.
  3. Kawalan positif — selepas semua penolakan itu, yang sah masih lulus.

Kumpulan 3 bukan hiasan. Tanpa ia, `sahkan()` yang sentiasa memulangkan
False akan lulus kumpulan 2 dengan sempurna.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasmik import tandatangan as T  # noqa: E402

# --------------------------------------------------------------- vektor RFC

# RFC 8032 §7.1. Setiap satu: (kunci awam, mesej, tandatangan).
VEKTOR_RFC = [
    (
        "d75a980182b10ab7d54bfed3c964073a"
        "0ee172f3daa62325af021a68f707511a",
        b"",
        "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555"
        "fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b",
    ),
    (
        "3d4017c3e843895a92b70aa74d1b7ebc"
        "9c982ccf2ec4968cc0cd55f12af4660c",
        bytes.fromhex("72"),
        "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da"
        "085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00",
    ),
    (
        "fc51cd8e6218a1a38da47ed00230f058"
        "0816ed13ba3303ac5deb911548908025",
        bytes.fromhex("af82"),
        "6291d657deec24024827e69c3abe01a30ce548a284743a445e3680d7db5ac3ac"
        "18ff9b538d16f290ae67f760984dc6594a7c15e9716ed28dc027beceea1ec40a",
    ),
]


class AsasKunci(unittest.TestCase):
    """Ujian yang perlu memasang kunci ujian, bukan kunci sebenar tuan.

    Kunci sebenar TASMIK berada dalam `KUNCI` dan selalunya kosong semasa
    pembangunan. Ujian tidak boleh bergantung padanya — kalau tidak, ia
    lulus atau gagal mengikut keadaan mesin, bukan mengikut kod.
    """

    def setUp(self):
        self.asal = T.KUNCI
        T.KUNCI = [bytes.fromhex(VEKTOR_RFC[0][0])]

    def tearDown(self):
        T.KUNCI = self.asal


class UjianVektorRFC(AsasKunci):
    """Tandatangan yang sah mesti diterima."""

    def test_tiga_vektor_rasmi(self):
        for pub, mesej, sig in VEKTOR_RFC:
            with self.subTest(pub=pub[:16]):
                T.KUNCI = [bytes.fromhex(pub)]
                ok, sebab = T.sahkan(sig, mesej)
                self.assertTrue(ok, f"vektor RFC ditolak: {sebab}")
                self.assertEqual(sebab, "")

    def test_sig_huruf_besar_diterima(self):
        """Hex huruf besar ialah hex yang sah — pelayan boleh menghantarnya."""
        pub, mesej, sig = VEKTOR_RFC[0]
        T.KUNCI = [bytes.fromhex(pub)]
        ok, _ = T.sahkan(sig.upper(), mesej)
        self.assertTrue(ok)

    def test_sig_dengan_newline_diterima(self):
        """Fail .sig berakhir dengan newline — itu bentuk yang kita tulis."""
        pub, mesej, sig = VEKTOR_RFC[0]
        T.KUNCI = [bytes.fromhex(pub)]
        ok, _ = T.sahkan(sig + "\n", mesej)
        self.assertTrue(ok)


class UjianKesTepi(AsasKunci):
    """Setiap input rosak mesti DITOLAK — dan tidak sekali-kali membaling."""

    def _tolak(self, teks_sig, data=b"apa-apa"):
        """Sahkan penolakan, dan bahawa sebabnya boleh dipaparkan."""
        try:
            ok, sebab = T.sahkan(teks_sig, data)
        except Exception as e:  # noqa: BLE001
            self.fail(f"sahkan() membaling {type(e).__name__}: {e}")
        self.assertFalse(ok, f"sepatutnya ditolak tetapi diterima: {teks_sig!r}")
        self.assertTrue(sebab, "penolakan mesti ada sebab untuk dipaparkan")
        return sebab

    def test_kosong(self):
        self.assertEqual(self._tolak(""), T.TIADA)
        self.assertEqual(self._tolak(None), T.TIADA)
        self.assertEqual(self._tolak("   \n  "), T.TIADA)

    def test_terlalu_pendek_atau_panjang(self):
        self.assertEqual(self._tolak("ab"), T.ROSAK)
        self.assertEqual(self._tolak("a" * 127), T.ROSAK)
        self.assertEqual(self._tolak("a" * 129), T.ROSAK)

    def test_panjang_ganjil(self):
        self.assertEqual(self._tolak("a" * 126 + "b"), T.ROSAK)

    def test_bukan_hex(self):
        self.assertEqual(self._tolak("z" * 128), T.ROSAK)

    def test_hex_ada_ruang(self):
        """fromhex melangkau ruang — mesti ditolak SEBELUM ia dipanggil."""
        pub, mesej, sig = VEKTOR_RFC[0]
        T.KUNCI = [bytes.fromhex(pub)]
        bersela = " ".join(sig[i:i + 2] for i in range(0, len(sig), 2))
        self.assertEqual(self._tolak(bersela, mesej), T.ROSAK)

    def test_halaman_html_captive_portal(self):
        """Rangkaian hotel menghantar HTML, bukan fail. Jangan meledak."""
        self._tolak("<html><body>Login required</body></html>")

    def test_S_lebih_besar_daripada_l(self):
        """S + l juga lulus kalau semakan ini tiada — pepijat klasik."""
        pub, mesej, sig = VEKTOR_RFC[0]
        T.KUNCI = [bytes.fromhex(pub)]
        R = bytes.fromhex(sig[:64])
        S = int.from_bytes(bytes.fromhex(sig[64:]), "little")
        dipintas = (R + (S + T._l).to_bytes(32, "little")).hex()
        self.assertEqual(self._tolak(dipintas, mesej), T.TAK_PADAN)

    def test_semua_sifar(self):
        self.assertEqual(self._tolak("00" * 64), T.TAK_PADAN)

    def test_semua_ff(self):
        self.assertEqual(self._tolak("ff" * 64), T.TAK_PADAN)

    def test_data_berbeza(self):
        """Tandatangan sah, mesej lain — inilah serangan sebenar."""
        pub, mesej, sig = VEKTOR_RFC[0]
        T.KUNCI = [bytes.fromhex(pub)]
        self.assertEqual(self._tolak(sig, b"mesej yang lain"), T.TAK_PADAN)

    def test_kunci_salah(self):
        pub, mesej, sig = VEKTOR_RFC[0]
        T.KUNCI = [bytes.fromhex(VEKTOR_RFC[1][0])]
        self.assertEqual(self._tolak(sig, mesej), T.TAK_PADAN)

    def test_R_bukan_titik_sah(self):
        """Bait R yang tidak berada pada lengkung — jangan meledak."""
        pub, mesej, sig = VEKTOR_RFC[0]
        T.KUNCI = [bytes.fromhex(pub)]
        rosak = "ff" * 32 + sig[64:]
        self.assertEqual(self._tolak(rosak, mesej), T.TAK_PADAN)

    def test_KUNCI_kosong_gagal_tertutup(self):
        """Kunci belum dijana bermakna TOLAK, bukan terima."""
        pub, mesej, sig = VEKTOR_RFC[0]
        T.KUNCI = []
        self.assertEqual(self._tolak(sig, mesej), T.TAK_PADAN)

    def test_kunci_pendek_dilangkau(self):
        """Kunci cacat dalam senarai tidak boleh menyebabkan ledakan."""
        pub, mesej, sig = VEKTOR_RFC[0]
        T.KUNCI = [b"\x01\x02", bytes.fromhex(pub)]
        ok, _ = T.sahkan(sig, mesej)
        self.assertTrue(ok, "kunci cacat sepatutnya dilangkau, bukan merosakkan")

    def test_kunci_tertib_kecil_ditolak(self):
        """Titik tertib-kecil (torsion) mesti ditolak — openssl pun menolaknya.

        Bait semua-sifar ialah titik (x, 0), iaitu titik tertib-2 yang SAH di
        atas lengkung. Ia ditolak kerana `_kecil_order()`, bukan kerana ia
        titik yang tidak wujud — dan itu perbezaan yang penting: ujian ini
        mengunci semakan torsion, bukan semakan lengkung.
        """
        pub, mesej, sig = VEKTOR_RFC[0]
        T.KUNCI = [bytes(32)]
        self.assertEqual(self._tolak(sig, mesej), T.TAK_PADAN)

    def test_teks_sig_jenis_pelik(self):
        """Pelayan boleh menghantar apa-apa jenis — jangan meledak."""
        for pelik in (123, [], {}, b"", 0):
            with self.subTest(pelik=repr(pelik)):
                self._tolak(pelik)


class UjianKawalanPositif(AsasKunci):
    """Selepas semua penolakan di atas, yang SAH mesti masih lulus.

    Tanpa kelas ini, `sahkan()` yang sentiasa memulangkan False akan lulus
    seluruh UjianKesTepi.
    """

    def test_sah_masih_lulus_selepas_penolakan(self):
        pub, mesej, sig = VEKTOR_RFC[0]
        T.KUNCI = [bytes.fromhex(pub)]
        self._tolak_dulu = T.sahkan("00" * 64, mesej)
        self.assertFalse(self._tolak_dulu[0])
        ok, sebab = T.sahkan(sig, mesej)
        self.assertTrue(ok, f"kawalan positif gagal: {sebab}")

    def test_putaran_kunci(self):
        """Senarai berbilang kunci — mana-mana satu boleh mengesahkan."""
        pub1, mesej1, sig1 = VEKTOR_RFC[0]
        pub2, mesej2, sig2 = VEKTOR_RFC[1]
        T.KUNCI = [bytes.fromhex(pub2), bytes.fromhex(pub1)]
        self.assertTrue(T.sahkan(sig1, mesej1)[0], "kunci kedua perlu diterima")
        self.assertTrue(T.sahkan(sig2, mesej2)[0], "kunci pertama perlu diterima")


class UjianCapJari(unittest.TestCase):
    def test_cap_jari_pendek_dan_penuh(self):
        kunci = bytes.fromhex(VEKTOR_RFC[0][0])
        pendek = T.cap_jari(kunci)
        penuh = T.cap_jari(kunci, penuh=True)
        # Kedua-duanya ada ruang setiap empat aksara, jadi ruang mesti dibuang
        # SEBELUM dibandingkan — kalau tidak, perbandingan gagal pada ruang
        # pertama dan bukan pada isi kunci.
        pendek_rapat = pendek.replace(" ", "")
        penuh_rapat = penuh.replace(" ", "")
        self.assertEqual(len(pendek_rapat), 16)
        self.assertEqual(len(penuh_rapat), 64)
        self.assertTrue(penuh_rapat.startswith(pendek_rapat))

    def test_cap_jari_tiada_kunci_tidak_meledak(self):
        """Skrin Tetapan memanggil ini walaupun kunci belum dijana."""
        asal = T.KUNCI
        T.KUNCI = []
        try:
            self.assertEqual(T.cap_jari(), "")
        finally:
            T.KUNCI = asal


if __name__ == "__main__":
    unittest.main()
