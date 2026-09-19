# TASMIK

Rekod tilawah dan hafazan al-Quran murid — app terminal untuk Termux.

Guru mencatat apa yang murid baca atau hafaz, dan app menyimpan semuanya
dalam satu pangkalan data di telefon. Tiada akaun, tiada internet, tiada
pelayan luar: data tinggal dalam telefon guru.

---

## Pasang di telefon

Buka Termux. Termux baharu selalunya belum ada `curl`, jadi pasang dahulu:

```
pkg install -y curl
```

Kemudian taip **satu baris** ini:

```
curl -fsSL http://<alamat-pelayan>:8001/pasang.sh | bash -s http://<alamat-pelayan>:8001
```

Gantikan `<alamat-pelayan>` dengan alamat komputer yang menyimpan fail
pemasangan. Contoh:

```
curl -fsSL http://192.168.1.10:8001/pasang.sh | bash -s http://192.168.1.10:8001
```

Selepas siap, buka app dengan:

```
tasmik
```

> `curl` perlu ada **sebelum** baris itu boleh jalan — ia yang memuat turun
> `pasang.sh`. Sebab itu ia dipasang berasingan dahulu. Selepas ini, kemas
> kini tidak perlukan `curl` lagi; app mengambil alih sepenuhnya.

Skrip itu juga akan memasang `openssl` (kalau belum ada), kerana ia
diperlukan untuk memeriksa tandatangan arkib. **Kalau openssl tiada dan
tidak dapat dipasang, pemasangan dibatalkan** — memasang kod yang tidak
diperiksa adalah lebih teruk daripada tidak memasang.

> Baris di atas mengambil `pasang.sh` dari pelayan LAN. Untuk pemasangan
> pertama itu bermakna pelayan boleh menukar skrip itu dan arkibnya sekali
> gus. Lihat **Nota keselamatan** di bawah untuk cara menutup jurang itu
> dengan mengambil `pasang.sh` dari GitHub.

---

## Menyediakan pelayan pemasangan (di komputer)

Folder `~/serve-tasmik/` mengandungi fail yang perlu dihidangkan. Ia
**bukan** repo git — ia hanya tempat letak barang siap, sama seperti
folder `dist` dalam projek lain. Skrip yang menghasilkannya tinggal
dalam repo app, di `~/tasmik/alat/`.

**1. Bina fail pemasangan** — setiap kali kod berubah:

```bash
bash ~/tasmik/alat/bina.sh
```

Ia menghasilkan empat fail dalam `~/serve-tasmik/`:

| Fail | Isi |
|------|-----|
| `tasmik.tar.gz` | kod app — dikecualikan: `alat/`, `.git`, `__pycache__`, `data`, `.backup` |
| `tasmik.tar.gz.sig` | tandatangan Ed25519 bagi arkib itu |
| `versi.json` | nombor versi + nota |
| `pasang.sh` | disalin dari `alat/` — satu sumber sahaja |

`versi.json` ditulis **terakhir**, sebagai penanda bahawa terbitan itu
lengkap — app yang menyemak dan nampak versi lama tidak akan memuat turun
set fail yang belum siap. `pasang.sh` disalin sebelum itu, supaya tidak ada
saat pengguna menjalankan pemasang **lama** terhadap arkib **baharu**.

`bina.sh` juga, mengikut urutan: menjalankan ujian, memastikan kunci dalam
`pasang.sh` seiras dengan kunci dalam kod app, membina arkib,
menandatanganinya, dan **mengesahkan tandatangan itu sendiri** dengan
pengesah Python yang akan dihantar ke telefon. Langkah terakhir itu
menangkap percanggahan antara `openssl` dan kod app sebelum ia sampai ke
telefon, di mana ia bermakna kemas kini yang ditolak tanpa sebab.

**2. Hidupkan pelayan:**

```bash
python3 -m http.server 8001 --bind 0.0.0.0 --directory ~/serve-tasmik
```

Cari alamat IP komputer dengan `ip addr` (Linux) atau `ipconfig` (Windows).
Telefon dan komputer mesti berada dalam rangkaian Wi-Fi yang sama.

---

## Kemas kini

App semak sendiri apabila dibuka. Kalau ada versi baharu, menu utama
menunjukkan amaran — pilih `[7] Kemas kini`.

Skrin kemas kini menunjukkan versi yang dipasang, versi di pelayan, dan
apa yang baharu, kemudian meminta pengesahan sebelum memasang.

Kod lama disalin ke `.backup/` di dalam folder app sebelum ditimpa. Itu
jaring keselamatan, bukan rollback automatik — untuk kembali kepadanya,
ekstrak fail itu secara manual.

**Alamat pelayan ditetapkan sekali sahaja**, di
`Tetapan ▸ [1] Sumber kemas kini`. Ia sengaja tiada nilai lalai: alamat IP
LAN berubah bila router memberi alamat baharu, dan lebih baik guru nampak
alamat yang salah daripada ia senyap-senyap menunjuk ke tempat lain.

Untuk naikkan versi: ubah `NOMBOR` dalam `tasmik/versi.py`, catat sebabnya
dalam `CHANGELOG.md`, kemudian jalankan `bina.sh` semula.

---

## Tambah pelajar secara pukal

Untuk mendaftarkan murid baharu, pergi ke `Pelajar ▸ [3] Tambah senarai (pukal)`.
Ada dua cara: **tampal senarai** terus ke dalam app, atau **baca dari fail**
`.txt` / `.csv`.

Formatnya longgar — senarai dari WhatsApp, Excel atau nota sendiri semuanya
boleh dibaca:

```
Ahmad Zaki, Tahun 4          nama, kelas
2. Nurul Huda, Tahun 5       nombor di hadapan dilangkau
- Siti Aminah; Tahun 6       bulet dan koma bertitik pun boleh
Muhammad Adam bin Abdullah   kelas tidak wajib
Nama Penuh,Kelas             baris kepala dari Excel dilangkau
```

Kalau bentuknya tidak pasti, pilih **`[3] Lihat contoh format`** dalam menu
yang sama — ia menunjukkan enam bentuk yang diterima, setiap satu dengan
contohnya. Contoh ringkas juga dipaparkan sebelum menampal dan sebelum
memilih fail, jadi formatnya tidak perlu diteka.

App menunjukkan ringkasan dahulu — berapa baharu, berapa sudah ada, berapa
tidak difahami — dan bertanya sebelum menyimpan. Nama yang sudah ada
dilangkau, jadi senarai yang sama boleh ditampal dua kali dengan selamat.

Untuk membaca fail di Termux, jalankan ini sekali dahulu supaya app boleh
mencapai folder Download:

```
termux-setup-storage
```

Kemudian laluannya seperti `~/storage/downloads/pelajar.csv`.

---

## Di mana data disimpan

```
~/.tasmik/
├── tasmik.db      pangkalan data (pelajar + rekod)
├── config.json    tetapan app
├── export/        fail CSV
└── sandaran/      salinan pangkalan data
```

Data ini berada **di luar** folder app. Kemas kini menimpa folder app
sahaja — rekod murid tidak pernah disentuh. Jadi pemasangan semula pun
tidak memadam data.

Untuk pindah ke telefon baharu, salin folder `~/.tasmik/` sepenuhnya.

---

## Struktur kod

```
~/tasmik/                  repo git — kod app
├── main.py                menu utama dan gelung utamanya
├── tasmik/
│   ├── versi.py           nombor versi — dibaca app DAN bina.sh
│   ├── ui.py              kotak, warna, input, tarikh
│   ├── store.py           semua SQL ada di sini, tiada di tempat lain
│   ├── surah.py           jadual 114 surah + carian nama
│   ├── pelajar.py         skrin pelajar
│   ├── rekod.py           skrin rekod tasmi'
│   ├── laporan.py         laporan kemajuan dan sejarah
│   ├── eksport.py         CSV dan sandaran
│   ├── kemas.py           enjin kemas kini
│   ├── tandatangan.py     pengesahan Ed25519 (pustaka asas sahaja)
│   └── tetapan.py         skrin tetapan
├── ujian/                 ujian — tidak sampai ke telefon
│   ├── test_tandatangan.py  vektor RFC 8032 + kes berniat jahat
│   └── test_kemas.py        gat tandatangan, hujung-ke-hujung
└── alat/                  perkakas pelayan — tidak sampai ke telefon
    ├── bina.sh            bina + tanda + sahkan ke ~/serve-tasmik/
    ├── tanda.py           jana kunci, tandatangan, sahkan, padan
    └── pasang.sh          pemasang satu baris untuk Termux

~/serve-tasmik/            bukan repo — barang siap
├── tasmik.tar.gz
├── tasmik.tar.gz.sig
├── versi.json
└── pasang.sh
```

Jalankan ujian dengan:

```
python3 -m unittest discover -s ~/tasmik/ujian -v
```

Hanya guna pustaka asas Python — tiada `pip install` diperlukan. Ia
berjalan pada Termux dengan hanya `pkg install python`.

### Git

Repo setempat sahaja, tiada remote, cawangan `main` — sama seperti
`taksiran`. `.gitignore` mengecualikan `data/`, `__pycache__/`, `.backup/`
dan fail yang dihasilkan `bina.sh`.

Data guru di `~/.tasmik/` berada di luar repo sepenuhnya, jadi ia tidak
boleh masuk git secara tidak sengaja.

Mesej commit mengikut bentuk `vX.Y.Z — ringkasan`, dengan badan yang
menerangkan **sebab** perubahan itu, bukan sekadar apa yang berubah.

---

## Nota keselamatan

Arkib kemas kini **ditandatangani**, dan app **menolak** apa-apa yang
tandatangannya tidak sah. Tandatangan diperiksa terhadap kunci awam yang
tersemat dalam `tasmik/tandatangan.py` — sebelum satu bait pun diekstrak.
Tiada suis untuk mematikan pemeriksaan itu.

Kriptonya Ed25519, ditulis dengan pustaka asas Python sahaja (Termux tiada
`pip`). Ia diuji terhadap vektor rasmi RFC 8032 dan satu set kes berniat
jahat dalam `ujian/`, dan disilang-periksa dengan `openssl` pada setiap
binaan.

### Had yang penting: pemasangan PERTAMA

Pada pemasangan pertama, `pasang.sh` dan arkib datang dari pelayan yang
**sama**. Penyerang yang menguasai pelayan itu boleh menukar kedua-duanya
sekali gus — kunci dalam skrip itu dan arkibnya — jadi pemeriksaan
tandatangan tidak melindungi apa-apa pada pusingan itu.

Untuk menutupnya, ambil **`pasang.sh` dari GitHub** dan **arkib dari
pelayan LAN**:

```
curl -fsSL https://raw.githubusercontent.com/hakimproject26/tasmik/c63d542/alat/pasang.sh \
  | bash -s http://192.168.1.10:8001
```

GitHub tidak boleh diubah oleh pelayan LAN, jadi kunci yang tertanam dalam
skrip itu boleh dipercayai — dan pelayan hanya menyediakan arkib, yang
diperiksa tandatangannya.

Repo: <https://github.com/hakimproject26/tasmik>. Nombor dalam URL itu
ialah commit SHA — lihat nota 1 di bawah.

**Selepas pemasangan pertama, pelayan tidak lagi berkuasa.** App memeriksa
sendiri setiap kemas kini.

Tiga perkara yang perlu diambil berat kalau anda guna cara GitHub:

1. **Sematkan kepada commit atau tag, bukan `main`.** URL `…/main/…` boleh
   ditulis semula oleh sesiapa yang menguasai akaun GitHub itu. Commit SHA
   menjadikan pemasang itu tidak boleh berubah — dan arahan yang sudah
   dicatat tidak rosak bila anda push commit baharu.
2. **Kunci akaun GitHub menjadi sauh kepercayaan** untuk pemasangan
   pertama. Aktifkan 2FA.
3. **`curl | bash` bermakna tiada siapa membaca skrip itu.** Kalau anda
   mahu menyemaknya dahulu:
   `curl -fsSL <url> -o pasang.sh` — lihat fail itu, kemudian
   `bash pasang.sh <alamat>`.

### Yang tidak dilindungi

- **Kerahsiaan.** Arkib melalui HTTP biasa. Tandatangan melindungi
  integriti dan asal usul, bukan kerahsiaan.
- **Pakej sistem.** `pasang.sh` menjalankan `pkg install` untuk Python,
  curl dan openssl dari cermin Termux — muat turun yang di luar skop
  tandatangan ini.

---

## Kunci tandatangan

Kunci rahsia disimpan di `~/.tasmik-kunci/kunci.pem`, disulitkan dengan
frasa laluan. Ia **tidak pernah** masuk repo dan **tidak pernah** masuk
arkib — `alat/` dikecualikan, dan `bina.sh` memeriksa kedua-duanya.

**Jana kunci (sekali sahaja):**

```
python3 ~/tasmik/alat/tanda.py jana
```

openssl akan menanya frasa laluan **tiga kali**. Ia menanya terus di
terminal, jadi frasa itu tidak pernah muncul dalam senarai proses — dan
sebab itu juga `bina.sh` tidak boleh dijalankan dari cron atau CI.

Simpan frasa itu dalam pengurus kata laluan, dan sandarkan
`kunci.pem` ke tempat lain.

**Kalau frasa itu hilang**, anda tidak boleh menandatangani terbitan
baharu. Pemulihannya ialah memasang semula di telefon melalui `pasang.sh`
— bukan dengan mematikan pemeriksaan tandatangan.

Jana kunci akan mencetak cap jari dan memberitahu dua tempat untuk
menampalnya. Selepas itu, pastikan ketiga-tiganya seiras:

```
python3 ~/tasmik/alat/tanda.py padan ~/tasmik/alat/pasang.sh
```

`bina.sh` menjalankan pemeriksaan ini pada setiap binaan, tanpa syarat.

### Memutar kunci

`KUNCI` dalam `tasmik/tandatangan.py` ialah **senarai**, bukan satu kunci.
Sebabnya bukan keselesaan: kalau kunci perlu ditukar, kunci baharu hanya
boleh sampai ke telefon melalui kemas kini yang ditandatangani oleh kunci
**lama**. Itu lingkaran mati.

Caranya: tambah kunci baharu ke dalam senarai (jangan buang yang lama),
terbitkan kemas kini itu, dan tunggu semua telefon menerimanya. Barulah
buang kunci lama. Telefon yang belum dikemas kini akan terkunci selamanya
kalau kunci lama dibuang terlalu awal.
