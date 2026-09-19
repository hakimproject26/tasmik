# Sejarah Perubahan — TASMIK

Format nombor versi: `MAJOR.MINOR.PATCH`

| Naik | Bila |
|------|------|
| MAJOR | Sesuatu yang lama **tak berfungsi lagi** — guru terpaksa ubah cara guna |
| MINOR | Ada **tambahan** baharu, yang lama masih jalan seperti biasa |
| PATCH | **Baiki** yang rosak sahaja |

Setiap kali nombor dalam `tasmik/versi.py` naik, catat sebabnya di sini.

---

## v2.0.0 — 19/09/2026

**Arkib kemas kini ditandatangani** — app menolak apa-apa yang
tandatangannya tidak sah.

Ini perubahan MAJOR kerana sesuatu yang lama memang tak berfungsi lagi:
pelayan yang tiada `tasmik.tar.gz.sig` akan mula ditolak. Itu memang
tujuannya.

Sebelum ini, sesiapa yang boleh menjawab pada alamat pelayan kemas kini
boleh menghantar kod yang akan dijalankan pada telefon. Sekarang arkib
mesti ditandatangani dengan kunci rahsia tuan, dan app memegang kunci
**awam** — jadi ia boleh mengesahkan tetapi tidak boleh mencipta
tandatangan.

**Bagaimana ia berfungsi**

- Tandatangan Ed25519, diperiksa terhadap kunci yang tersemat dalam
  `tasmik/tandatangan.py`. Sesiapa yang boleh menulis `config.json` tidak
  boleh mengubah sauh kepercayaan itu.
- Diperiksa **sebelum** arkib dibuka — `tarfile.getnames()` menyahmampatkan
  seluruh gzip, jadi arkib bom mesti ditolak sebelum ia sempat meletup.
- Tiada suis untuk mematikan pemeriksaan. Kalau ada, ia menjadi sasaran
  pertama penyerang.
- Ditulis dengan pustaka asas Python sahaja — Termux tiada `pip`. Ia diuji
  terhadap vektor rasmi RFC 8032 dan satu set kes berniat jahat, dan
  disilang-periksa dengan `openssl` pada setiap binaan.

**Tiga kegagalan dibezakan**, supaya guru tahu apa yang berlaku:
tandatangan tiada, tandatangan rosak, dan tandatangan tidak sepadan. Ketiga-
tiganya berlaku sebelum pengextrakan, jadi skrin boleh mengaku dengan jujur
"Tiada apa-apa diubah".

**Yang masih tidak dilindungi:** pemasangan PERTAMA. Masa itu `pasang.sh`
dan arkib datang dari pelayan yang sama, jadi penyerang yang menguasai
pelayan boleh menukar kedua-duanya sekali gus. Ambil `pasang.sh` dari GitHub
untuk menutupnya — lihat README, "Nota keselamatan".

**Tambahan**

- `ujian/` — 32 ujian, dijalankan oleh `bina.sh` sebelum apa-apa dibina
- `alat/tanda.py` — jana kunci, tandatangan, sahkan, dan gat `padan`
- Skrin Tetapan dan skrin Kemas Kini memaparkan cap jari kunci
- `bina.sh` mengesahkan tandatangan yang baru dibuat dengan pengesah Python
  yang akan dihantar ke telefon — percanggahan antara `openssl` dan kod app
  ditangkap di mesin pembinaan, bukan di telefon guru
- Alamat Tailscale sebenar dalam contoh `tetapan.py` dan `kemas.py`
  digantikan dengan contoh generik, supaya ia tidak diterbitkan kalau repo
  ini ditolak ke GitHub

**Pembetulan**

- `sahkan()` dalam `tandatangan.py` membaling `AttributeError` apabila
  menerima input bukan teks (cth. integer), walaupun docstringnya berjanji
  ia tidak pernah membaling. Janji itu yang membolehkan pemanggil gagal
  tertutup tanpa `except` yang berisiko menelan kegagalan sebenar, jadi ia
  kini dipenuhi.

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

- Pengesahan tandatangan arkib. *(Ditambah dalam v2.0.0.)* Sesiapa yang
  boleh menjawab pada alamat pelayan kemas kini boleh menghantar kod yang
  akan dijalankan pada telefon.
