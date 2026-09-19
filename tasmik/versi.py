"""Nombor versi app.

Format MAJOR.MINOR.PATCH — dipanggil semantic versioning.

    MAJOR  naik bila sesuatu yang lama TAK BERFUNGSI lagi.
           Pengguna terpaksa ubah cara guna.
    MINOR  naik bila ada TAMBAHAN baharu, tapi yang lama masih jalan.
    PATCH  naik bila BAIKI yang rosak sahaja.

Ukurannya bukan berapa banyak kerja, tapi berapa besar kesannya pada
pengguna.

Setiap kali nombor ini naik, catat sebabnya dalam CHANGELOG.md.

Fail ini dibaca oleh app DAN oleh skrip pembinaan (`bina.sh`) di sisi
pelayan. Sebab itu ia fail berasingan dan bukan sekadar pemalar dalam
main.py — supaya `versi.json` yang dihantar ke telefon tidak boleh tak
selaras dengan versi kod yang sebenarnya.
"""

NOMBOR = "2.0.0"
TARIKH = "19/09/2026"

# Apa yang berubah pada versi SEMASA. Dipaparkan pada skrin Kemas Kini,
# dan dihantar ke app melalui versi.json di pelayan.
# Sejarah penuh ada dalam CHANGELOG.md.
NOTA = [
    "Arkib kemas kini kini DITANDATANGANI, dan app menolak apa-apa",
    "yang tandatangannya tidak sah.",
    "Pelayan kemas kini mesti menyediakan tasmik.tar.gz.sig — kalau",
    "tidak, kemas kini akan ditolak. Jalankan bina.sh semula.",
    "Rekod murid tidak pernah disentuh, sama ada kemas kini berjaya",
    "atau ditolak.",
]


def penuh():
    """Contoh: 'v1.0.0 (19/09/2026)'."""
    return f"v{NOMBOR} ({TARIKH})"
