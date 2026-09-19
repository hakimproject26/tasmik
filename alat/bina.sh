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
# Menghasilkan TIGA fail dalam ~/serve-tasmik/:
#   tasmik.tar.gz    kod app
#   versi.json       nombor versi + nota, dibaca oleh app untuk semak
#   pasang.sh        disalin dari alat/ — satu sumber, tiada salinan
#                    yang boleh tak selaras dengan repo
#
# TIDAK seperti app taksiran, arkib ini TIDAK ditandatangani — pengesahan
# tandatangan belum dibawa ke sini. Sesiapa yang boleh menjawab pada alamat
# pelayan ini boleh menghantar kod yang akan dijalankan pada telefon.
# Lihat nota panjang dalam tasmik/kemas.py.
set -e

AKAR="$HOME"
SUMBER="$AKAR/tasmik"
TUJUAN="$AKAR/serve-tasmik"
ARKIB="$TUJUAN/tasmik.tar.gz"
ALAT="$(cd "$(dirname "$0")" && pwd)"

if [ ! -f "$SUMBER/main.py" ]; then
    echo "Ralat: tak jumpa $SUMBER/main.py" >&2
    exit 1
fi
if [ ! -f "$SUMBER/tasmik/versi.py" ]; then
    echo "Ralat: tak jumpa $SUMBER/tasmik/versi.py" >&2
    exit 1
fi
if [ ! -f "$ALAT/pasang.sh" ]; then
    echo "Ralat: tak jumpa $ALAT/pasang.sh" >&2
    exit 1
fi

mkdir -p "$TUJUAN"

# Bina ke nama .new dahulu, dan terbitkan hanya di penghujung. Kalau binaan
# mati di tengah jalan, pelayan masih memegang set fail LAMA yang lengkap.
rm -f "$ARKIB.new"
echo "Membina arkib …"

# .git dan __pycache__ tak perlu sampai ke telefon — ia hanya
# menggembungkan arkib.
# .backup/ mengandungi kod lama; menghantarnya bermakna setiap kemas kini
# membawa salinan kod yang semakin membesar.
# alat/ ialah perkakas pelayan (skrip binaan dan pemasangan) — guru tidak
# perlukan ia di telefon, dan ia tidak sepatutnya keluar dari mesin ini.
tar czf "$ARKIB.new" \
    --exclude='__pycache__' \
    --exclude='.backup' \
    --exclude='.git' \
    --exclude='.gitignore' \
    --exclude='data' \
    --exclude='alat' \
    -C "$AKAR" tasmik

# Pengecualian tar gagal secara SENYAP, jadi ia mesti diperiksa. Semakan
# ini menjaga kesilapan yang kesannya teruk.
for x in '__pycache__' '/alat'; do
    if tar tzf "$ARKIB.new" | grep -q "$x"; then
        echo "Ralat: $x masuk ke dalam arkib." >&2
        rm -f "$ARKIB.new"
        exit 1
    fi
done
for p in tasmik/main.py tasmik/tasmik/versi.py tasmik/tasmik/kemas.py; do
    if ! tar tzf "$ARKIB.new" | grep -qx "$p"; then
        echo "Ralat: $p tiada dalam arkib — telefon akan tersekat." >&2
        rm -f "$ARKIB.new"
        exit 1
    fi
done

mv "$ARKIB.new" "$ARKIB"

# pasang.sh diterbitkan dari repo, bukan disunting terus dalam serve-tasmik.
# Kalau ia disalin dengan tangan, dua salinan itu akan bercanggah suatu hari
# nanti — dan yang di pelayan ialah yang guru akan guna.
cp "$ALAT/pasang.sh" "$TUJUAN/pasang.sh"

# versi.json DITULIS TERAKHIR. Ia penanda bahawa terbitan ini lengkap: app
# yang menyemak dan nampak versi lama akan berkata "sudah terkini", jadi ia
# tidak akan memuat turun set fail yang belum siap.
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

ls -l "$ARKIB" "$TUJUAN/versi.json" "$TUJUAN/pasang.sh"
echo
echo "Sedia. Hidupkan pelayan dengan:"
echo "  python3 -m http.server 8001 --bind 0.0.0.0 --directory \"$TUJUAN\""
echo
echo "Kemudian di telefon:"
echo "  curl -fsSL http://<alamat>:8001/pasang.sh | bash -s http://<alamat>:8001"
