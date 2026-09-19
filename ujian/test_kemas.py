"""Ujian integrasi untuk gat tandatangan dalam tasmik/kemas.py.

Ujian unit dalam `test_tandatangan.py` membuktikan pengesah Ed25519 betul.
Fail ini membuktikan perkara yang berbeza, dan yang lebih mudah rosak:
bahawa `_periksa_arkib()` benar-benar MEMANGGILnya, pada data yang betul,
dan menolak arkib yang tidak sepatutnya diterima.

Perbezaan itu penting. Pengesah yang sempurna, dipanggil dengan hujah yang
salah atau selepas pengekstrakan, tidak melindungi apa-apa.

Langkau automatik kalau openssl tiada, supaya ujian ini tidak pernah
menjadi alasan untuk tidak menjalankan selebihnya.
"""

import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasmik import kemas, tandatangan as T  # noqa: E402

_ADA_OPENSSL = shutil.which("openssl") is not None


def _bina_arkib(versi="9.9.9"):
    """Arkib kecil yang berbentuk seperti terbitan TASMIK sebenar."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for nama, isi in (
            ("tasmik/main.py", b"# main\n"),
            ("tasmik/tasmik/versi.py",
             f'NOMBOR = "{versi}"\n'.encode()),
        ):
            data = isi
            info = tarfile.TarInfo(nama)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


@unittest.skipUnless(_ADA_OPENSSL, "openssl tiada")
class UjianGatTandatangan(unittest.TestCase):
    """Hujung-ke-hujung: tandatangan openssl, pengesahan kod app."""

    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp(prefix="tasmik-ujian-")
        cls.kunci = os.path.join(cls.dir, "kunci.pem")
        # Tanpa frasa laluan: ini kunci ujian, dan ia dibuang selepas ini.
        subprocess.run(
            ["openssl", "genpkey", "-algorithm", "ED25519", "-out", cls.kunci],
            check=True, capture_output=True,
        )
        der = subprocess.run(
            ["openssl", "pkey", "-in", cls.kunci, "-pubout", "-outform", "DER"],
            check=True, capture_output=True,
        ).stdout
        cls.awam = der[-32:]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir, ignore_errors=True)

    def setUp(self):
        self.asal = T.KUNCI
        T.KUNCI = [self.awam]
        self.data = _bina_arkib()
        self.laluan = os.path.join(self.dir, "arkib.tar.gz")
        with open(self.laluan, "wb") as f:
            f.write(self.data)
        self.mentah = os.path.join(self.dir, "sig.mentah")
        subprocess.run(
            ["openssl", "pkeyutl", "-sign", "-rawin", "-inkey", self.kunci,
             "-in", self.laluan, "-out", self.mentah],
            check=True, capture_output=True,
        )
        with open(self.mentah, "rb") as f:
            self.sig = f.read().hex() + "\n"

    def tearDown(self):
        T.KUNCI = self.asal

    def _periksa(self, sig=None, data=None, laluan=None):
        return kemas._periksa_arkib(
            laluan or self.laluan, "9.9.9",
            self.sig if sig is None else sig,
            self.data if data is None else data,
        )

    # ------------------------------------------------ yang sepatutnya lulus

    def test_arkib_sah_diterima(self):
        ok, mesej = self._periksa()
        self.assertTrue(ok, f"arkib sah ditolak: {mesej}")
        self.assertEqual(mesej, "")

    # ------------------------------------------------ yang sepatutnya ditolak

    def test_satu_bait_ditukar_ditolak(self):
        """Inilah serangan sebenar: pelayan menghantar arkib yang diubah."""
        rosak = bytearray(self.data)
        # Bait di TENGAH, bukan di penghujung — memastikan ia mengubah
        # kandungan yang bermakna dan bukan sekadar padding gzip.
        rosak[len(rosak) // 2] ^= 0x01
        with open(self.laluan, "wb") as f:
            f.write(bytes(rosak))
        ok, mesej = self._periksa(data=bytes(rosak))
        self.assertFalse(ok, "arkib yang diubah DITERIMA")
        self.assertEqual(mesej, T.TAK_PADAN)

    def test_tandatangan_arkib_lain_ditolak(self):
        """Tandatangan SAH, tetapi untuk arkib yang berbeza."""
        lain = os.path.join(self.dir, "lain.tar.gz")
        with open(lain, "wb") as f:
            f.write(_bina_arkib("1.1.1"))
        mentah = os.path.join(self.dir, "lain.mentah")
        subprocess.run(
            ["openssl", "pkeyutl", "-sign", "-rawin", "-inkey", self.kunci,
             "-in", lain, "-out", mentah],
            check=True, capture_output=True,
        )
        with open(mentah, "rb") as f:
            sig_lain = f.read().hex() + "\n"
        ok, mesej = self._periksa(sig=sig_lain)
        self.assertFalse(ok, "tandatangan arkib lain DITERIMA")
        self.assertEqual(mesej, T.TAK_PADAN)

    def test_tiada_tandatangan_ditolak(self):
        ok, mesej = self._periksa(sig="")
        self.assertFalse(ok)
        self.assertEqual(mesej, T.TIADA)

    def test_tandatangan_rosak_ditolak(self):
        ok, mesej = self._periksa(sig="bukan hex langsung")
        self.assertFalse(ok)
        self.assertEqual(mesej, T.ROSAK)

    def test_KUNCI_kosong_menolak_arkib_sah(self):
        """Kunci belum dijana bermakna TOLAK — bukan terima semua."""
        T.KUNCI = []
        ok, mesej = self._periksa()
        self.assertFalse(ok, "KUNCI kosong sepatutnya gagal TERTUTUP")
        self.assertEqual(mesej, T.TAK_PADAN)

    def test_arkib_berubah_di_cakera_ditolak(self):
        """Tandatangan sah, tetapi fail di cakera bukan fail yang ditandatangani.

        Ini menutup jurang antara "apa yang disahkan" dan "apa yang
        diekstrak" — dua benda berbeza kalau fail boleh berubah di antara
        keduanya.
        """
        with open(self.laluan, "wb") as f:
            f.write(self.data + b"sisa yang ditambah kemudian")
        ok, mesej = self._periksa()
        self.assertFalse(ok, "arkib yang berubah selepas muat turun DITERIMA")
        self.assertIn("berubah", mesej)

    # ------------------------------------------------ struktur, selepas sah

    def test_laluan_tak_selamat_ditolak(self):
        """Tandatangan sah tidak bermakna struktur selamat — dua-dua perlu."""
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tf:
            for nama in ("tasmik/main.py", "tasmik/tasmik/versi.py",
                         "tasmik/../../jahat.sh"):
                data = b'# x\n'
                info = tarfile.TarInfo(nama)
                info.size = len(data)
                tf.addfile(info, io.BytesIO(data))
        jahat = buf.getvalue()
        laluan = os.path.join(self.dir, "jahat.tar.gz")
        with open(laluan, "wb") as f:
            f.write(jahat)
        mentah = os.path.join(self.dir, "jahat.mentah")
        subprocess.run(
            ["openssl", "pkeyutl", "-sign", "-rawin", "-inkey", self.kunci,
             "-in", laluan, "-out", mentah],
            check=True, capture_output=True,
        )
        with open(mentah, "rb") as f:
            sig = f.read().hex() + "\n"
        ok, mesej = self._periksa(sig=sig, data=jahat, laluan=laluan)
        self.assertFalse(ok, "laluan tak selamat DITERIMA")
        self.assertIn("Laluan tak selamat", mesej)

    def test_versi_tak_sepadan_ditolak(self):
        ok, mesej = kemas._periksa_arkib(self.laluan, "1.0.0", self.sig, self.data)
        self.assertFalse(ok)
        self.assertIn("1.0.0", mesej)


if __name__ == "__main__":
    unittest.main()
