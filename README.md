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

Ia menghasilkan tiga fail dalam `~/serve-tasmik/`:

| Fail | Isi |
|------|-----|
| `tasmik.tar.gz` | kod app — dikecualikan: `alat/`, `.git`, `__pycache__`, `data`, `.backup` |
| `versi.json` | nombor versi + nota |
| `pasang.sh` | disalin dari `alat/` — satu sumber sahaja |

`versi.json` ditulis **terakhir**, sebagai penanda bahawa terbitan itu
lengkap — app yang menyemak dan nampak versi lama tidak akan memuat turun
set fail yang belum siap. `pasang.sh` disalin pada setiap binaan supaya
salinan di pelayan tidak boleh tertinggal daripada repo.

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
│   └── tetapan.py         skrin tetapan
└── alat/                  perkakas pelayan — tidak sampai ke telefon
    ├── bina.sh            bina arkib ke ~/serve-tasmik/
    └── pasang.sh          pemasang satu baris untuk Termux

~/serve-tasmik/            bukan repo — barang siap
├── tasmik.tar.gz
├── versi.json
└── pasang.sh
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

Arkib kemas kini **tidak** ditandatangani dan **tidak** disahkan
tandatangannya. Sesiapa yang boleh menjawab pada alamat pelayan itu boleh
menghantar kod yang akan dijalankan pada telefon.

Yang sudah ada hanyalah perlindungan terhadap arkib yang rosak atau
tersalah hantar: had saiz muat turun, semakan laluan tak selamat dalam
arkib, dan semakan bahawa nombor versi dalam arkib benar-benar sama dengan
yang dijanjikan pelayan.

Tempat untuk menambah pengesahan tandatangan sudah disediakan — satu gat
tunggal dalam `_periksa_arkib()` di `tasmik/kemas.py`, sebelum apa-apa
diekstrak. App rujukan (`taksiran`) sudah ada pengesahan Ed25519 yang
boleh dijadikan contoh.
