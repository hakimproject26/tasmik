#!/usr/bin/env bash
# Pemasang TASMIK untuk Termux.
#
# Guna:
#   curl -fsSL http://<alamat>:8001/pasang.sh | bash -s http://<alamat>:8001
#
# Alamat pelayan WAJIB diberi. Ia sengaja tiada lalai: alamat IP LAN rumah
# berubah bila router memberi alamat baharu, dan setiap arahan pemasangan
# yang sudah dicatat akan rosak setiap kali ia berubah. Lebih baik guru
# tahu alamatnya daripada ia senyap-senyap menunjuk ke tempat yang salah.
#
# ── APA YANG DIPERIKSA, DAN APA YANG TIDAK ────────────────────────────
#
# Arkib diperiksa tandatangannya terhadap kunci awam yang tertanam dalam
# fail ini. Arkib yang tandatangannya tidak sah DITOLAK — tiada apa-apa
# diekstrak. Kunci itu juga ada dalam `tasmik/tandatangan.py`, dan
# `bina.sh` memastikan kedua-duanya seiras pada setiap binaan.
#
# HAD YANG PENTING: pemeriksaan ini hanya bermakna kalau fail INI sendiri
# datang dari saluran yang anda percayai. Kalau anda mengambilnya dari
# pelayan yang sama dengan arkib, penyerang yang menguasai pelayan itu
# boleh menukar kedua-duanya sekali gus — kunci dalam skrip ini dan
# arkibnya — dan pemeriksaan itu menjadi sia-sia.
#
# Jadi untuk pemasangan PERTAMA, ambil skrip ini dari GitHub, dan ambil
# arkib dari pelayan LAN. GitHub tidak boleh diubah oleh pelayan LAN.
# Lihat README, bahagian "Nota keselamatan".
#
# Selepas pemasangan pertama, pelayan tidak lagi berkuasa: app memeriksa
# sendiri setiap kemas kini.

set -e

ASAS="${1:-}"
DEST="$HOME/tasmik"
ARKIB="$HOME/.tasmik-pasang.tar.gz"
SIG="$ARKIB.sig"
PEM="$HOME/.tasmik-pasang.pem"

# Perhatikan "$SIG.mentah", bukan "$ARKIB.mentah". Tandatangan mentah
# ditulis bersebelahan fail hex-nya, jadi namanya "$SIG" + ".mentah".
# Versi pertama skrip ini menulis "$ARKIB.mentah" — nama yang tidak
# pernah wujud — jadi fail itu tertinggal dalam folder rumah guru pada
# setiap pemasangan, sambil trap ini mendakwa ia sudah bersih.
bersih() { rm -f "$ARKIB" "$SIG" "$PEM" "$SIG.mentah"; }
trap bersih EXIT

echo
echo "  ── TASMIK — Rekod Tilawah & Hafazan ──"
echo

# --- 1. Alamat pelayan -------------------------------------------------
if [ -z "$ASAS" ]; then
    echo "  ✗ Alamat pelayan tidak diberi." >&2
    echo >&2
    echo "    Guna:" >&2
    echo "      curl -fsSL http://<alamat>:8001/pasang.sh | bash -s http://<alamat>:8001" >&2
    echo >&2
    exit 1
fi
ASAS="${ASAS%/}"

# --- 2. Python ---------------------------------------------------------
# Cari kedua-dua nama. Termux menyediakan 'python', tetapi banyak sistem
# lain hanya ada 'python3' — dan sesetengah sistem lama masih ada 'python'
# yang sebenarnya Python 2. Alias di penghujung skrip mesti menunjuk kepada
# jurubahasa yang benar-benar wujud, kalau tidak 'tasmik' gagal selepas
# pemasangan yang kelihatan berjaya.
PY=""
for c in python3 python; do
    if command -v "$c" >/dev/null 2>&1; then
        PY="$c"
        break
    fi
done

if [ -z "$PY" ]; then
    if command -v pkg >/dev/null 2>&1; then
        echo "  → memasang python..."
        pkg install -y python
    fi
    for c in python3 python; do
        if command -v "$c" >/dev/null 2>&1; then
            PY="$c"
            break
        fi
    done
fi

if [ -z "$PY" ]; then
    echo "  ✗ Python tiada, dan tiada cara memasangnya di sini." >&2
    echo "    Pasang Python 3 dahulu, kemudian jalankan semula." >&2
    exit 1
fi

# Python 2 akan gagal dengan ralat sintaks yang mengelirukan jauh di dalam
# app. Lebih baik berhenti di sini dengan ayat yang jelas.
if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)' 2>/dev/null; then
    echo "  ✗ $PY ialah $("$PY" --version 2>&1) — TASMIK perlu Python 3.7+." >&2
    exit 1
fi
echo "  ✓ $PY dah ada — $("$PY" --version 2>&1)"

# --- 3. openssl --------------------------------------------------------
# SEBELUM muat turun, bukan selepas. openssl CLI ada dalam pakej
# openssl-tool, bukan dalam asas Termux. Ketiadaannya ialah kegagalan,
# bukan amaran — kita gagal TERTUTUP. Memasang kod yang tidak diperiksa
# adalah lebih teruk daripada tidak memasang langsung.
if ! command -v openssl >/dev/null 2>&1; then
    if command -v pkg >/dev/null 2>&1; then
        echo "  → memasang openssl-tool..."
        # `|| true` perlu: tanpa itu, `set -e` membunuh skrip di sini dan
        # guru tidak akan nampak mesej yang menjelaskan sebabnya.
        pkg install -y openssl-tool || true
    fi
fi
if ! command -v openssl >/dev/null 2>&1; then
    echo "  ✗ openssl tiada, jadi tandatangan tak dapat diperiksa." >&2
    echo "    Pemasangan dibatalkan. Cuba:  pkg install openssl-tool" >&2
    exit 1
fi

# `pkeyutl -verify -rawin` hanya ada dalam OpenSSL 3.0+. Pada versi lama
# ia gagal sebagai "tandatangan tidak sah", yang salah diagnosis: guru
# akan menyangka arkib tulen telah diceroboh.
if ! openssl pkeyutl -help 2>&1 | grep -q -- '-rawin'; then
    echo "  ✗ openssl ini $(openssl version) tidak menyokong `-rawin`," >&2
    echo "    yang diperlukan untuk mengesahkan tandatangan Ed25519." >&2
    echo "    Ia perlu OpenSSL 3.0+. Kemas kini openssl-tool, kemudian cuba lagi." >&2
    exit 1
fi
echo "  ✓ openssl dah ada — $(openssl version)"

# --- 4. Muat turun -----------------------------------------------------
echo "  → memuat turun dari $ASAS ..."
cd "$HOME"
curl -fsSL "$ASAS/tasmik.tar.gz" -o "$ARKIB"

if ! curl -fsSL "$ASAS/tasmik.tar.gz.sig" -o "$SIG"; then
    echo "  ✗ Pelayan itu tiada fail tandatangan (tasmik.tar.gz.sig)." >&2
    echo "    Tanpanya arkib tak dapat diperiksa, jadi pemasangan" >&2
    echo "    dibatalkan. Pastikan pelayan menyediakan fail itu." >&2
    exit 1
fi

# --- 5. Sahkan tandatangan ---------------------------------------------
# Ini berlaku SEBELUM apa-apa dibuka atau diekstrak. Arkib yang tidak
# ditandatangani tidak pernah sampai ke peringkat penyahmampatan.
cat > "$PEM" <<'PEM'
-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAPFWoOYFD39b/ZNCIfjlkwOfSkil1Wj3EJp5rBfIuUwI=
-----END PUBLIC KEY-----
PEM

# Tandatangan disimpan sebagai hex supaya ia tahan melalui sebarang
# pengendalian teks. openssl mahu bait mentah, jadi ia ditukar di sini —
# sekali gus memeriksa panjangnya, supaya fail rosak gagal dengan ayat
# yang jelas dan bukan dengan "tandatangan tidak sah" yang mengelirukan.
if ! "$PY" - "$SIG" "$SIG.mentah" <<'PY'
import sys
teks = open(sys.argv[1], encoding="ascii", errors="replace").read().strip()
if len(teks) != 128:
    sys.exit(f"  ✗ Fail tandatangan {len(teks)} aksara, sepatutnya 128.")
try:
    sig = bytes.fromhex(teks)
except ValueError:
    sys.exit("  ✗ Fail tandatangan bukan hex yang sah.")
open(sys.argv[2], "wb").write(sig)
PY
then
    echo "    Fail tandatangan rosak — pemasangan dibatalkan." >&2
    exit 1
fi

if openssl pkeyutl -verify -pubin -inkey "$PEM" -rawin \
        -in "$ARKIB" -sigfile "$SIG.mentah" >/dev/null 2>&1; then
    echo "  ✓ tandatangan sah"
else
    echo "  ✗ Tandatangan tidak sah — arkib ini bukan daripada tuan." >&2
    echo "    Pemasangan dibatalkan. Tiada apa-apa telah diubah." >&2
    exit 1
fi

# --- 6. Periksa laluan dalam arkib -------------------------------------
# Tandatangan sudah membuktikan arkib ini tulen, jadi ini bukan lagi
# pertahanan terhadap penyerang — ia pertahanan terhadap arkib TULEN yang
# rosak atau tersalah bina. Murah, jadi ia kekal.
if tar tzf "$ARKIB" | grep -qE '^(/|.*\.\.)'; then
    echo "  ✗ Arkib mengandungi laluan tak selamat — dibatalkan." >&2
    exit 1
fi
if ! tar tzf "$ARKIB" | grep -qx 'tasmik/main.py'; then
    echo "  ✗ Arkib itu bukan TASMIK — main.py tiada di dalamnya." >&2
    exit 1
fi

# --- 7. Ekstrak --------------------------------------------------------
# Sengaja TIDAK buang $DEST — supaya salinan lama kekal kalau ini
# pemasangan semula, dan supaya fail yang tidak ada dalam arkib (cth.
# .backup/) tidak hilang.
mkdir -p "$DEST"
tar xzf "$ARKIB" -C "$HOME"
echo "  ✓ dipasang ke $DEST"
echo "  ✓ rekod murid di ~/.tasmik/ tidak disentuh"

# --- 8. Sumber kemas kini ----------------------------------------------
# Ditulis ke dalam config supaya guru tidak perlu menaip URL yang panjang
# pada papan kekunci telefon. URL itu senang tersalah taip, dan yang paling
# menderita ialah guru yang belum kenal app ini.
#
# Yang ditulis hanyalah SATU tetapan. Rekod murid tidak pernah disentuh —
# ia fail yang berbeza sama sekali.
#
# Kalau sumber SUDAH ditetapkan, ia DIKEKALKAN. Guru yang menaip sesuatu
# di Tetapan membuat tindakan yang disengajakan, dan menimpanya secara
# senyap lebih memudaratkan daripada satu langkah tambahan.
#
# Kegagalan di sini TIDAK membatalkan pemasangan: app sudah dipasang dan
# berfungsi, dan guru boleh menetapkan sumber sendiri di Tetapan ▸ [1].
if ! "$PY" - "$DEST" "$ASAS" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from tasmik import kemas, store

sumber = kemas.betulkan(sys.argv[2])
cfg = store.baca_config()
lama = (cfg.get("sumber_kemas") or "").strip()

if lama:
    print(f"  ! Sumber kemas kini sedia ada dikekalkan: {lama}")
    if lama != sumber:
        print(f"    Untuk tukar kepada {sumber}, guna Tetapan ▸ [1].")
else:
    cfg["sumber_kemas"] = sumber
    store.simpan_config(cfg)
    print(f"  ✓ sumber kemas kini ditetapkan: {sumber}")
PY
then
    echo "  ! Tak dapat menetapkan sumber kemas kini."
    echo "    App tetap berfungsi. Tetapkan sendiri di Tetapan ▸ [1]:"
    echo "      $ASAS"
fi

# --- 9. Alias ----------------------------------------------------------
if ! grep -qs "alias tasmik=" "$HOME/.bashrc"; then
    echo "alias tasmik='$PY $DEST/main.py'" >> "$HOME/.bashrc"
    echo "  ✓ alias 'tasmik' ditambah"
fi

echo
echo "  Siap."
echo
echo "  Jalan sekarang:   cd ~/tasmik && $PY main.py"
echo "  Lain kali:        buka Termux, taip — tasmik"
echo
echo "  Untuk kemas kini kemudian, guna menu Kemas kini di dalam app."
# Sengaja TIDAK menyebut sumber di sini. Langkah 8 di atas sudah
# melaporkan sama ada ia DITETAPKAN atau DIKEKALKAN, dan kedua-duanya
# boleh berlaku dengan $ASAS yang sama. Menyebut "$ASAS" di sini akan
# mendakwa sumber itu GitHub walaupun config masih menyimpan alamat LAN —
# dan guru yang mempercayai mesej itu tidak akan faham kenapa kemas kini
# masih mencari laptop.
echo "  Sumber kemas kini: lihat atau tukar di  Tetapan ▸ [1]"
echo
