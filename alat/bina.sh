#!/bin/bash
# Bina fail pemasangan untuk pelayan kemas kini.
#
# Guna:  bash ~/tasmik/alat/bina.sh
#
# Skrip ini tinggal DI DALAM repo app (~/tasmik/alat/) supaya ia
# dijejaki git bersama kod yang dibinanya. Fail yang dihasilkan pula
# pergi ke ~/serve-tasmik/, yang bukan repo — ia hanya tempat letak
# barang siap, sama seperti folder 'dist' dalam projek lain.
#
# Menghasilkan EMPAT fail dalam ~/serve-tasmik/:
#   tasmik.tar.gz       kod app
#   tasmik.tar.gz.sig   tandatangan Ed25519 bagi arkib itu
#   versi.json          nombor versi + nota, dibaca oleh app untuk semak
#   pasang.sh           disalin dari alat/ — satu sumber, tiada salinan
#                       yang boleh tak selaras dengan repo
#
# URUTAN LANGKAH DI SINI MENGIKAT. Setiap satu ada sebab, dan sebabnya
# ditulis di tempatnya. Jangan susun semula tanpa membacanya.
set -e

AKAR="$HOME"
SUMBER="$AKAR/tasmik"
TUJUAN="$AKAR/serve-tasmik"
ARKIB="$TUJUAN/tasmik.tar.gz"
ALAT="$(cd "$(dirname "$0")" && pwd)"

# --------------------------------------------------------------- 0. fail
# Diperiksa di AWAL, bukan separuh jalan. Binaan yang mati selepas arkib
# dibina meninggalkan pelayan dengan set fail yang tidak lengkap.
for f in \
    "$SUMBER/main.py" \
    "$SUMBER/tasmik/versi.py" \
    "$SUMBER/tasmik/tandatangan.py" \
    "$ALAT/pasang.sh" \
    "$ALAT/tanda.py"
do
    if [ ! -f "$f" ]; then
        echo "Ralat: tak jumpa $f" >&2
        exit 1
    fi
done

mkdir -p "$TUJUAN"

# --------------------------------------------------------------- 1. ujian
# Sebelum apa-apa dibina. Ujian mengambil masa beberapa saat, dan ia
# menangkap penyimpangan dalam pengesah Ed25519 — kod yang, kalau rosak,
# akan menolak setiap kemas kini yang sah di telefon guru.
echo "Menjalankan ujian tandatangan …"
if ! python3 -m unittest discover -s "$SUMBER/ujian" 2>&1 | tail -3; then
    echo "Ralat: ujian tandatangan gagal. Tiada apa-apa diterbitkan." >&2
    exit 1
fi

# --------------------------------------------------------------- 2. padan
# TANPA SYARAT. Kalau PEM dalam pasang.sh tidak seiras dengan KUNCI dalam
# kod app, arkib yang sah akan ditolak pada PEMASANGAN PERTAMA — iaitu
# kepada orang yang belum ada app untuk membetulkannya. Kegagalan itu
# tidak boleh dibaiki dari jauh, jadi ia disekat di sini.
echo "Memeriksa kunci …"
python3 "$ALAT/tanda.py" padan "$ALAT/pasang.sh"

# --------------------------------------------------------------- 3. arkib
# Dibina ke nama .new dahulu, dan diterbitkan hanya di penghujung. Kalau
# binaan mati di tengah jalan, pelayan masih memegang set fail LAMA yang
# lengkap.
rm -f "$ARKIB.new" "$ARKIB.new.sig"
echo "Membina arkib …"

# .git dan __pycache__ tak perlu sampai ke telefon — ia hanya
# menggembungkan arkib.
# .backup/ mengandungi kod lama; menghantarnya bermakna setiap kemas kini
# membawa salinan kod yang semakin membesar.
# alat/ ialah perkakas pelayan (skrip binaan, pemasangan, DAN kunci
# tandatangan) — guru tidak perlukan ia di telefon, dan ia tidak
# sepatutnya keluar dari mesin ini.
# ujian/ dijalankan di sini, pada setiap binaan. Telefon tiada gunanya
# untuknya, jadi ia tidak dihantar.
tar czf "$ARKIB.new" \
    --exclude='__pycache__' \
    --exclude='.backup' \
    --exclude='.git' \
    --exclude='.gitignore' \
    --exclude='data' \
    --exclude='alat' \
    --exclude='ujian' \
    -C "$AKAR" tasmik

# Pengecualian tar gagal secara SENYAP, jadi ia mesti diperiksa. Semakan
# ini menjaga kesilapan yang kesannya teruk.
for x in '__pycache__' '/alat' '/ujian'; do
    if tar tzf "$ARKIB.new" | grep -q "$x"; then
        echo "Ralat: $x masuk ke dalam arkib." >&2
        rm -f "$ARKIB.new"
        exit 1
    fi
done
for p in tasmik/main.py tasmik/tasmik/versi.py tasmik/tasmik/kemas.py \
         tasmik/tasmik/tandatangan.py; do
    if ! tar tzf "$ARKIB.new" | grep -qx "$p"; then
        echo "Ralat: $p tiada dalam arkib — telefon akan tersekat." >&2
        rm -f "$ARKIB.new"
        exit 1
    fi
done

# Kunci rahsia memang tiada dalam repo, tetapi ini mengunci andaian itu.
# Kalau ia pernah sampai ke telefon, sesiapa yang membongkar app boleh
# menandatangani kod sendiri dan seluruh jaminan ini runtuh.
if tar xzOf "$ARKIB.new" 2>/dev/null | grep -q "PRIVATE KEY"; then
    echo "Ralat: kunci RAHSIA ditemui dalam arkib. Binaan dibatalkan." >&2
    rm -f "$ARKIB.new"
    exit 1
fi

# --------------------------------------------------------------- 4. tanda
# Arkib mesti SIAP dahulu. Yang ditandatangani ialah bait mentah arkib,
# jadi menandatangani sebelum ia siap menghasilkan tandatangan bagi bait
# yang berbeza.
echo "Menandatangani …"
python3 "$ALAT/tanda.py" tanda "$ARKIB.new"

# --------------------------------------------------------------- 5. sahkan
# Ujian paling bernilai dalam projek ini. Ia membandingkan openssl dengan
# pengesah Python yang AKAN DIHANTAR ke telefon, pada setiap binaan.
# Penyimpangan antara keduanya ditangkap di sini — bukan di telefon guru,
# di mana ia bermakna kemas kini yang ditolak tanpa sebab.
python3 "$ALAT/tanda.py" sahkan "$ARKIB.new"

# --------------------------------------------------------------- 6. terbit
# Kedua-dua mv tidak boleh dijadikan satu operasi. Turutan ini (sig
# dahulu) bermakna tetingkap antara keduanya menghasilkan "sig baharu +
# arkib lama"; turutan sebaliknya menghasilkan "arkib baharu + sig lama".
# App menolak kedua-duanya, jadi ini soal diagnosis, bukan keselamatan.
mv "$ARKIB.new.sig" "$ARKIB.sig"
mv "$ARKIB.new" "$ARKIB"

# --------------------------------------------------------------- 7. pasang
# Sebelum versi.json. pasang.sh membawa kunci awam, jadi kalau versi.json
# diterbitkan dahulu, ada saat pengguna boleh menjalankan pasang.sh LAMA
# terhadap arkib BAHARU — kunci tak padan, pemasangan pertama gagal.
cp "$ALAT/pasang.sh" "$TUJUAN/pasang.sh"

# --------------------------------------------------------------- 8. versi
# DITULIS TERAKHIR. Ia penanda bahawa terbitan ini lengkap: app yang
# menyemak dan nampak versi lama akan berkata "sudah terkini", jadi ia
# tidak akan memuat turun set fail yang belum siap.
#
# Sebab itu juga tiada arahan lambat di antara langkah 6 dan langkah ini:
# versi.json LAMA bersama arkib BAHARU menghasilkan "Arkib ini versi X,
# bukan Y seperti dijangka" — fail tertutup yang betul, tetapi mengelirukan.
echo "Menulis versi.json …"
python3 - "$SUMBER" "$TUJUAN/versi.json" <<'PY'
import json, sys
sys.path.insert(0, sys.argv[1])
from tasmik import versi
json.dump(
    {"versi": versi.NOMBOR, "tarikh": versi.TARIKH, "nota": versi.NOTA},
    open(sys.argv[2], "w", encoding="utf-8"),
    ensure_ascii=False,
    indent=2,
)
print(f"  versi {versi.NOMBOR} ({versi.TARIKH})")
PY

# --------------------------------------------------------------- 9. lapor
# Selepas semuanya siap, bukan di tengah jalan.
ls -l "$ARKIB" "$ARKIB.sig" "$TUJUAN/versi.json" "$TUJUAN/pasang.sh"
echo
echo -n "Cap jari kunci: "
python3 "$ALAT/tanda.py" cap
echo
echo "Sedia. Hidupkan pelayan dengan:"
echo "  python3 -m http.server 8001 --bind 0.0.0.0 --directory \"$TUJUAN\""
echo
echo "Kemudian di telefon:"
echo "  curl -fsSL http://<alamat>:8001/pasang.sh | bash -s http://<alamat>:8001"
