# Sejarah Perubahan — TASMIK

Format nombor versi: `MAJOR.MINOR.PATCH`

| Naik | Bila |
|------|------|
| MAJOR | Sesuatu yang lama **tak berfungsi lagi** — guru terpaksa ubah cara guna |
| MINOR | Ada **tambahan** baharu, yang lama masih jalan seperti biasa |
| PATCH | **Baiki** yang rosak sahaja |

Setiap kali nombor dalam `tasmik/versi.py` naik, catat sebabnya di sini.

---

## v1.2.0 — 19/09/2026

**Contoh format ditunjukkan dalam app** — `Pelajar ▸ [3] ▸ Lihat contoh format`

Enam bentuk senarai yang diterima, setiap satu dengan contoh dan sebabnya:
koma, bernombor, berbulet, tanpa kelas, salinan dari Excel, dan pemisah lain.
Contoh ringkas juga dipaparkan sebelum guru mula menampal, dan sebelum
memilih fail — supaya formatnya tidak perlu diteka.

Setiap contoh diuji terhadap penghurai sebenar, jadi apa yang ditunjukkan
itu benar-benar boleh dibaca.

**Pembetulan paparan**

- Baris yang terlalu panjang untuk kotak kini menjorok dua ruang apabila
  dibalut. Sebelum ini sambungannya bermula rapat di tepi kotak dan nampak
  seperti baris yang berasingan — berlaku pada semua kotak, termasuk nama
  pelajar yang panjang.
- Baris ringkasan laporan kemajuan dibahagi dua supaya tidak meninggalkan
  satu perkataan keseorangan di telefon.

---

## v1.1.0 — 19/09/2026

**Tambah pelajar secara pukal** — `Pelajar ▸ [3] Tambah senarai (pukal)`

Dua cara masuk:

- **Tampal / taip** — tampal senarai terus ke dalam app, satu pelajar satu
  baris. Baris kosong menamatkannya.
- **Baca dari fail** — `.txt` atau `.csv`. Fail eksport Excel terus boleh
  dibaca (BOM UTF-8 dan baris kepala dikendalikan).

Formatnya sengaja longgar, kerana senarai guru datang dari mana-mana:

```
Ahmad Zaki, Tahun 4          koma
2. Nurul Huda, Tahun 5       bernombor
- Siti Aminah; Tahun 6       bulet, koma bertitik
Muhammad Adam bin Abdullah   kelas boleh tiada
Nama Penuh,Kelas             baris kepala — dilangkau
```

Sebelum apa-apa disimpan, app menunjukkan ringkasan: berapa baharu, berapa
sudah ada, berapa tidak difahami. Nama yang sudah wujud dilangkau, bukan
ditambah dua kali. Semuanya disimpan dalam satu transaksi — semua masuk,
atau tiada langsung.

---

## v1.0.0 — 19/09/2026

Versi pertama.

**Rekod**

- Tilawah: tarikh, surah, ayat dari–hingga, juzuk, nota
- Hafazan: tarikh, surah, ayat dari–hingga, nota
- Juzuk tidak ditanya untuk hafazan — ia diisi sendiri daripada jadual surah

**Pelajar**

- Tambah, senarai, tukar nama/kelas, padam

**Laporan**

- Kemajuan ikut pelajar: bilangan rekod, ayat, surah yang telah dibaca
- Sejarah penuh seorang pelajar

**Data**

- Semua data dalam SQLite di `~/.tasmik/tasmik.db` — di **luar** folder app,
  jadi kemas kini kod tidak pernah menyentuhnya
- Export CSV (UTF-8 dengan BOM, terus dibuka dalam Excel/Sheets)
- Sandaran pangkalan data (salinan konsisten melalui `sqlite3.backup()`)

**Pemasangan & kemas kini**

- Pasang dengan satu baris `curl`
- Semak versi dan kemas kini dari dalam app (menu `[7] Kemas kini`)
- Kod lama disalin ke `.backup/` sebelum ditimpa
- Arkib diperiksa sebelum diekstrak: had saiz, laluan tak selamat, dan
  nombor versi dalam arkib mesti sama dengan yang dijanjikan pelayan

**Belum ada**

- Pengesahan tandatangan arkib. Sesiapa yang boleh menjawab pada alamat
  pelayan kemas kini boleh menghantar kod yang akan dijalankan pada telefon.
  Lihat nota dalam `tasmik/kemas.py` — tempat untuk menambahnya ialah
  `_periksa_arkib()`.
