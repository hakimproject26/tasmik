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
# ⚠ TIDAK ADA PENGESAHAN TANDATANGAN dalam versi ini. Skrip ini memuat
#   turun arkib dan terus memasangnya. Ia hanya selamat setakat saluran
#   yang membawanya boleh dipercayai — kalau ia datang dari pelayan yang
#   sama dengan arkib, sesiapa yang menguasai pelayan itu boleh menghantar
#   apa-apa kod. Lihat nota dalam tasmik/kemas.py untuk cara menambahnya.

set -e

ASAS="${1:-}"
DEST="$HOME/tasmik"
ARKIB="$HOME/.tasmik-pasang.tar.gz"

bersih() { rm -f "$ARKIB"; }
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

# --- 3. curl -----------------------------------------------------------
if ! command -v curl >/dev/null 2>&1; then
    echo "  → memasang curl..."
    pkg install -y curl
fi

# --- 4. Muat turun -----------------------------------------------------
echo "  → memuat turun dari $ASAS ..."
cd "$HOME"
curl -fsSL "$ASAS/tasmik.tar.gz" -o "$ARKIB"

# --- 5. Periksa laluan dalam arkib -------------------------------------
# Ini BUKAN pengesahan identiti — ia hanya menghalang arkib yang rosak atau
# berniat jahat daripada menulis ke luar folder app. Ia tidak boleh
# menggantikan tandatangan: arkib yang ditulis penyerang tetap akan lulus
# semakan ini.
if tar tzf "$ARKIB" | grep -qE '^(/|.*\.\.)'; then
    echo "  ✗ Arkib mengandungi laluan tak selamat — dibatalkan." >&2
    exit 1
fi
if ! tar tzf "$ARKIB" | grep -qx 'tasmik/main.py'; then
    echo "  ✗ Arkib itu bukan TASMIK — main.py tiada di dalamnya." >&2
    exit 1
fi

# --- 6. Ekstrak --------------------------------------------------------
# Sengaja TIDAK buang $DEST — supaya salinan lama kekal kalau ini
# pemasangan semula, dan supaya fail yang tidak ada dalam arkib (cth.
# .backup/) tidak hilang.
mkdir -p "$DEST"
tar xzf "$ARKIB" -C "$HOME"
echo "  ✓ dipasang ke $DEST"
echo "  ✓ data guru di ~/.tasmik/ tidak disentuh"

# --- 7. Alias ----------------------------------------------------------
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
echo "  Untuk kemas kini kemudian, guna menu [7] Kemas kini di dalam app."
echo "  Tetapkan sumber dahulu di  Tetapan ▸ [1]  →  $ASAS"
echo
