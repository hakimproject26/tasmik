"""Alat menandatangani — JANGAN dihantar ke telefon.

Folder `alat/` dikecualikan daripada arkib oleh `bina.sh`, dan `bina.sh`
memeriksa bahawa pengecualian itu benar-benar berlaku sebelum ia menerbitkan
apa-apa. Sebabnya: kod di sini memegang kunci RAHSIA. Kalau ia sampai ke
telefon, sesiapa yang membongkar app itu boleh menandatangani kod sendiri,
dan seluruh jaminan ini runtuh.

Kriptonya bukan tulisan tangan — semuanya openssl. Yang app perlukan ialah
PENGESAHAN, dan itu ada dalam `tasmik/tandatangan.py`. Pemisahan ini
disengajakan: kod menandatangani tidak pernah dihantar, dan pengesahan
tidak pernah bergantung pada binari luar.

Guna:

    python3 alat/tanda.py jana            jana kunci baharu (disulitkan)
    python3 alat/tanda.py tanda <fail>    tandatangan <fail> -> <fail>.sig
    python3 alat/tanda.py sahkan <fail>   sahkan guna kod app sendiri
    python3 alat/tanda.py cap             cetak cap jari + baris untuk KUNCI
    python3 alat/tanda.py pem             cetak PEM kunci awam (untuk pasang.sh)
    python3 alat/tanda.py padan <psg.sh>  pastikan kunci pasang.sh = kunci app

Kunci rahsia disimpan di `~/.tasmik-kunci/kunci.pem`, disulitkan dengan
frasa laluan. Kunci awam disimpan di sebelahnya dalam fail biasa — ia
memang maklumat awam, dan menyimpannya begini bermakna `cap` dan `pem`
tidak perlu menanya frasa laluan. Jadi `bina.sh` menanya SEKALI sahaja.

Frasa laluan ditanya oleh openssl terus di terminal. Ia tidak pernah melalui
argumen, jadi ia tidak pernah muncul dalam senarai proses. Kesan sampingannya:
alat ini TIDAK boleh dijalankan dari cron atau CI — tanpa terminal, openssl
gagal selepas tiga percubaan. Itu memang sepatutnya.
"""

import os
import subprocess
import sys

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_KUNCI = os.path.join(os.path.expanduser("~"), ".tasmik-kunci")
KUNCI_RAHSIA = os.path.join(DIR_KUNCI, "kunci.pem")
KUNCI_AWAM = os.path.join(DIR_KUNCI, "kunci.awam")

# 12 bait pengepala SPKI bagi Ed25519. Dikira semula oleh ujian terhadap
# openssl, supaya ia tidak pernah menjadi tekaan yang disalin.
_PENGEPALA_SPKI = bytes.fromhex("302a300506032b6570032100")


def _openssl(*args, **kw):
    """Jalankan openssl. Berhenti dengan mesej Melayu, bukan traceback.

    Frasa laluan ditanya oleh openssl sendiri di terminal, jadi ia tidak
    pernah melalui argumen dan tidak pernah muncul dalam senarai proses.
    """
    try:
        return subprocess.run(["openssl", *args], check=True, **kw)
    except FileNotFoundError:
        sys.exit("Ralat: openssl tiada. Pasang dahulu (pkg install openssl-tool).")
    except subprocess.CalledProcessError as e:
        if e.returncode in (1, 2):
            # Dua sebab yang berbeza menghasilkan kegagalan yang sama, dan
            # akibatnya berbeza sama sekali. Frasa laluan yang salah bermakna
            # kunci itu tidak boleh dipakai. Terminal yang tiada bermakna
            # kunci itu tidak pernah ditanya — dan itu berlaku setiap kali
            # skrip ini dijalankan dari cron, systemd, atau paip. Menyebut
            # hanya yang pertama menghantar guru memburu masalah yang tidak
            # wujud.
            sys.exit(
                "Ralat: openssl gagal membaca kunci.\n"
                "       Kemungkinan:\n"
                "         • Frasa laluan salah.\n"
                "         • Skrip ini tiada terminal. openssl menanya frasa\n"
                "           laluan terus di terminal, jadi ia TIDAK boleh\n"
                "           dijalankan dari cron, dari paip, atau dengan\n"
                "           stdin ditutup. Jalankan terus dalam Termux."
            )
        sys.exit(f"Ralat: openssl keluar dengan kod {e.returncode}.")


def _openssl_moden_raw():
    """Pastikan openssl cukup baharu untuk `pkeyutl -rawin`.

    `-rawin` hanya ada dalam OpenSSL 3.0+. Pada versi lama, openssl tidak
    mengadu "pilihan tidak dikenali" dengan jelas — ia gagal sebagai
    pengesahan yang tidak sepadan. Itu salah diagnosis yang teruk: guru akan
    melihat "tandatangan tidak sah" untuk arkib yang sebenarnya tulen.

    Jadi keupayaan itu diperiksa SEKALI di sini, dengan ayat yang menyatakan
    sebab sebenar.
    """
    try:
        keluaran = subprocess.run(
            ["openssl", "version"], capture_output=True, text=True, check=True
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        sys.exit("Ralat: tak dapat baca versi openssl.")

    # "OpenSSL 3.0.13 30 Jan 2024" → (3, 0)
    try:
        nombor = keluaran.split()[1].split(".")
        utama, kecil = int(nombor[0]), int(nombor[1])
    except (IndexError, ValueError):
        sys.exit(f"Ralat: versi openssl tidak difahami — {keluaran.strip()}")

    if (utama, kecil) < (3, 0):
        sys.exit(
            f"Ralat: openssl ini {utama}.{kecil}, tetapi tandatangan Ed25519\n"
            f"       memerlukan 3.0 atau lebih baharu (`pkeyutl -rawin`).\n"
            f"       Kemas kini openssl dahulu, kemudian jalankan semula."
        )


def _kunci_awam_bait(laluan=None):
    der = subprocess.run(
        ["openssl", "pkey", "-in", laluan or KUNCI_RAHSIA,
         "-pubout", "-outform", "DER"],
        check=True, capture_output=True,
    ).stdout
    # DER bagi Ed25519 ialah 44 bait: 12 bait pengepala SPKI, kemudian 32
    # bait kunci mentah. Bentuk ini stabil merentas OpenSSL 1.1.1 dan 3.x.
    return der[-32:]


def jana():
    _openssl_moden_raw()
    if os.path.exists(KUNCI_RAHSIA):
        sys.exit(f"Ralat: {KUNCI_RAHSIA} sudah ada. "
                 "Sengaja tidak ditimpa — kunci yang hilang tidak boleh dipulihkan.")
    os.makedirs(DIR_KUNCI, mode=0o700, exist_ok=True)
    os.chmod(DIR_KUNCI, 0o700)
    print(f"Menjana kunci baharu di {KUNCI_RAHSIA}")
    print("openssl akan menanya frasa laluan. Ingat ia — kalau ia hilang,")
    print("kunci ini hilang, dan kunci baharu tidak boleh sampai ke telefon.")
    print()
    print("Tiga kali ia menanya, dan itu memang sepatutnya:")
    print("  1. Frasa laluan baharu")
    print("  2. Ulang frasa yang sama (pengesahan)")
    print("  3. Frasa itu sekali lagi — untuk membaca kunci awam")
    print()
    print("Simpan frasa itu dalam pengurus kata laluan. Sandarkan juga")
    print(f"{KUNCI_RAHSIA} ke tempat lain — kalau telefon perlu dipasang")
    print("semula, ini satu-satunya cara menandatangani terbitan baharu.")
    print()

    # Dijana ke nama sementara, dan dinamakan semula hanya selepas kunci
    # awam berjaya dibaca. Tanpa ini, openssl yang gagal di tengah jalan
    # (Ctrl-C pada gesaan, terminal tanpa input) meninggalkan kunci.pem
    # KOSONG — dan semakan "sudah ada" di atas kemudiannya menyekat SETIAP
    # percubaan seterusnya dengan mesej yang menyuruh tuan berhenti
    # mencuba. Kunci separuh tulis tidak boleh menjadi kunci.
    sementara = KUNCI_RAHSIA + ".baharu"
    try:
        _openssl("genpkey", "-algorithm", "ED25519", "-aes-256-cbc",
                 "-out", sementara)
        if os.path.getsize(sementara) == 0:
            sys.exit("Ralat: openssl tulis kunci kosong. Tiada apa-apa disimpan.")
        print()
        print("Membaca kunci awam (frasa laluan sekali lagi) …")
        awam = _kunci_awam_bait(sementara)
    except BaseException:
        # SystemExit daripada _openssl juga sampai ke sini.
        try:
            os.unlink(sementara)
        except OSError:
            pass
        raise

    os.replace(sementara, KUNCI_RAHSIA)
    os.chmod(KUNCI_RAHSIA, 0o600)

    with open(KUNCI_AWAM, "w", encoding="ascii") as f:
        f.write(awam.hex() + "\n")

    sys.path.insert(0, AKAR)
    from tasmik import tandatangan as T
    print()
    print(f"Cap jari: {T.cap_jari(awam, penuh=True)}")
    print()
    print("LANGKAH SETERUSNYA — tampal kunci ini ke DUA tempat:")
    print()
    print("1. Ke dalam KUNCI di tasmik/tandatangan.py:")
    print()
    print(f'    bytes.fromhex("{awam.hex()}"),')
    print()
    print("2. Ke dalam PEM di alat/pasang.sh — jalankan ini dan salin")
    print("   keluarannya:")
    print()
    print("       python3 alat/tanda.py pem")
    print()
    print("Kemudian pastikan ketiga-tiganya seiras:")
    print()
    print("       python3 alat/tanda.py padan alat/pasang.sh")
    print()


def tanda(arkib):
    _openssl_moden_raw()
    if not os.path.exists(KUNCI_RAHSIA):
        sys.exit(f"Ralat: {KUNCI_RAHSIA} tiada. Jalankan `jana` dahulu.")
    if not os.path.exists(arkib):
        sys.exit(f"Ralat: {arkib} tiada.")

    mentah = arkib + ".sig.mentah"
    print(f"Menandatangani {os.path.basename(arkib)} …")
    _openssl("pkeyutl", "-sign", "-rawin", "-inkey", KUNCI_RAHSIA,
             "-in", arkib, "-out", mentah)
    try:
        with open(mentah, "rb") as f:
            sig = f.read()
        if len(sig) != 64:
            sys.exit(f"Ralat: tandatangan {len(sig)} bait, sepatutnya 64.")
        # Hex, bukan bait mentah: ia tahan melalui sebarang pengendalian
        # teks, dan boleh dibaca mata semasa menyiasat masalah.
        with open(arkib + ".sig", "w", encoding="ascii") as f:
            f.write(sig.hex() + "\n")
    finally:
        os.unlink(mentah)
    print(f"  ✓ {os.path.basename(arkib)}.sig")


def sahkan(arkib):
    """Sahkan artifak yang baru dibina dengan kod yang AKAN dihantar.

    Inilah ujian yang paling bernilai dalam keseluruhan projek ini. Ia
    membandingkan openssl dengan tasmik/tandatangan.py pada setiap binaan,
    jadi penyimpangan antara keduanya ditangkap di sini — bukan di telefon
    guru, di mana ia bermakna kemas kini yang ditolak tanpa sebab.
    """
    sys.path.insert(0, AKAR)
    from tasmik import tandatangan as T

    laluan_sig = arkib + ".sig"
    if not os.path.exists(laluan_sig):
        sys.exit(f"Ralat: {laluan_sig} tiada — tandatangan dahulu.")
    with open(arkib, "rb") as f:
        data = f.read()
    with open(laluan_sig, encoding="ascii") as f:
        teks = f.read()

    ok, sebab = T.sahkan(teks, data)
    if not ok:
        sys.exit(f"Ralat: pengesah Python menolak arkib yang openssl tandatangani.\n"
                 f"       {sebab}\n"
                 f"       JANGAN terbitkan ini — dua pelaksanaan tidak bersetuju.")
    print(f"  ✓ pengesah Python bersetuju dengan openssl "
          f"({len(data) / 1024:.0f} KB, cap jari {T.cap_jari()})")


def cap():
    if not os.path.exists(KUNCI_AWAM):
        sys.exit("Ralat: kunci awam tiada. Jalankan `jana` dahulu.")
    sys.path.insert(0, AKAR)
    from tasmik import tandatangan as T
    awam = bytes.fromhex(open(KUNCI_AWAM, encoding="ascii").read().strip())
    print(T.cap_jari(awam, penuh=True))


def pem():
    """PEM kunci awam — untuk ditampal ke dalam pasang.sh.

    Dibina daripada kunci awam yang DIKAJI di `kunci.awam`, bukan dengan
    membuka kunci rahsia. Dua sebab, dan kedua-duanya penting:

    Ia tidak menanya frasa laluan. Lebih penting lagi, ia TIDAK BOLEH
    gagal pada masa yang salah: `openssl pkey` pada kunci bersulit tanpa
    terminal akan mencuba tiga kali, gagal, dan mencetak empat baris ralat
    OpenSSL. Menyalin PEM yang salah ke dalam `pasang.sh` bermakna arkib
    yang sah ditolak pada pemasangan pertama.

    `openssl pkey -pubout -outform DER` menghasilkan 44 bait: 12 bait
    pengepala SPKI yang tetap untuk Ed25519, kemudian 32 bait kunci mentah.
    Bentuk itu stabil merentas OpenSSL 1.1.1 dan 3.x, jadi pengepala itu
    boleh ditulis terus — dan ia disemak terhadap openssl dalam ujian.
    """
    import base64

    if not os.path.exists(KUNCI_AWAM):
        sys.exit("Ralat: kunci awam tiada. Jalankan `jana` dahulu.")
    awam = bytes.fromhex(open(KUNCI_AWAM, encoding="ascii").read().strip())
    if len(awam) != 32:
        sys.exit(f"Ralat: {KUNCI_AWAM} bukan 32 bait. Jalankan `jana` semula.")
    b64 = base64.b64encode(_PENGEPALA_SPKI + awam).decode("ascii")
    baris = [b64[i:i + 64] for i in range(0, len(b64), 64)]
    print("-----BEGIN PUBLIC KEY-----")
    for b in baris:
        print(b)
    print("-----END PUBLIC KEY-----")


def padan(pasang_sh):
    """Pastikan kunci dalam pasang.sh SAMA dengan kunci dalam kod app.

    Dua tempat memegang kunci awam: `tasmik/tandatangan.py` (untuk kemas
    kini dari dalam app) dan `pasang.sh` (untuk pemasangan pertama). Kalau
    kedua-duanya menyimpang, arkib yang sah akan DITOLAK pada pemasangan
    pertama — dan itu berlaku kepada orang yang belum ada app untuk
    membetulkannya. Jadi ia diperiksa setiap binaan, bukan diharap.
    """
    import base64
    import re

    sys.path.insert(0, AKAR)
    from tasmik import tandatangan as T

    teks = open(pasang_sh, encoding="utf-8").read()
    padan_pem = re.search(
        r"-----BEGIN PUBLIC KEY-----(.*?)-----END PUBLIC KEY-----", teks, re.S)

    # Kunci belum dijana. Itu keadaan yang sah semasa pembangunan, tetapi
    # ia mesti BERHENTI di sini — binaan yang menerbitkan arkib tanpa kunci
    # menghasilkan kemas kini yang setiap telefon akan tolak.
    #
    # Placeholder dalam pasang.sh diperiksa DAHULU. Tanpa semakan ini,
    # teks penanda itu gagal sebagai "PEM tidak boleh dibaca", yang
    # menunjuk guru kepada masalah yang salah.
    if padan_pem and "KUNCI_AWAM_TASMIK" in padan_pem.group(1):
        sys.exit(
            "Ralat: kunci awam belum ditampal ke alat/pasang.sh.\n"
            "       Jalankan `python3 alat/tanda.py jana` dahulu, kemudian\n"
            "       salin keluaran `python3 alat/tanda.py pem` ke dalam\n"
            "       blok PEM dalam alat/pasang.sh."
        )
    if not padan_pem:
        if not T.KUNCI:
            sys.exit(
                "Ralat: tiada kunci di mana-mana.\n"
                "       Jalankan `python3 alat/tanda.py jana` dahulu, kemudian\n"
                "       tampal kunci ke tasmik/tandatangan.py dan alat/pasang.sh."
            )
        sys.exit(f"Ralat: tiada PEM kunci awam dalam {pasang_sh}.\n"
                 f"       Cetak satu dengan: python3 alat/tanda.py pem")

    try:
        der = base64.b64decode("".join(padan_pem.group(1).split()))
    except ValueError:
        sys.exit(f"Ralat: PEM dalam {pasang_sh} tidak boleh dibaca.")
    if len(der) != 44:
        sys.exit(f"Ralat: DER dalam {pasang_sh} {len(der)} bait, sepatutnya 44.")
    awam_pasang = der[-32:]

    if awam_pasang not in T.KUNCI:
        sys.exit(
            f"Ralat: kunci dalam {pasang_sh} TIDAK sama dengan mana-mana kunci\n"
            f"       dalam tasmik/tandatangan.py.\n"
            f"       pasang.sh : {T.cap_jari(awam_pasang, penuh=True)}\n"
            f"       app       : {T.cap_jari(penuh=True)}\n"
            f"       Arkib yang sah akan ditolak pada pemasangan pertama.\n"
            f"       Betulkan dengan: python3 alat/tanda.py pem"
        )

    # Kalau kunci tempatan ada, ia juga mesti sama — kalau tidak, binaan ini
    # akan menandatangani dengan kunci yang telefon tidak percaya.
    if os.path.exists(KUNCI_AWAM):
        tempatan = bytes.fromhex(open(KUNCI_AWAM, encoding="ascii").read().strip())
        if tempatan != awam_pasang:
            sys.exit(
                f"Ralat: kunci tandatangan tempatan berbeza daripada {pasang_sh}.\n"
                f"       tempatan  : {T.cap_jari(tempatan, penuh=True)}\n"
                f"       pasang.sh : {T.cap_jari(awam_pasang, penuh=True)}\n"
                f"       Kemas kini akan ditolak oleh app, dan pemasangan\n"
                f"       pertama akan ditolak oleh pasang.sh.\n"
                f"       Betulkan dengan: python3 alat/tanda.py pem"
            )

    print(f"  ✓ kunci pasang.sh padan dengan app "
          f"({T.cap_jari(awam_pasang)})")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in (
            "jana", "tanda", "sahkan", "cap", "pem", "padan"):
        sys.exit(__doc__.strip().split("Guna:")[1].strip())
    arahan = sys.argv[1]
    if arahan in ("tanda", "sahkan", "padan"):
        if len(sys.argv) < 3:
            sys.exit(f"Ralat: `{arahan}` perlukan nama fail.")
        {"tanda": tanda, "sahkan": sahkan, "padan": padan}[arahan](sys.argv[2])
    else:
        {"jana": jana, "cap": cap, "pem": pem}[arahan]()


if __name__ == "__main__":
    main()
