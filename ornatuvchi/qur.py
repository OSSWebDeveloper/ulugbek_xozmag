"""O'rnatuvchini yig'adi.

Ishlatish (loyiha papkasidan):

    python ornatuvchi/qur.py

Natija:  dist/XozmagOrnatish.exe  — mijozga beriladigan yagona fayl.
Ichida:  Python, Django, sayt fayllari, ikonka va tayyor ma'lumotlar bazasi.

Kompyuterda `pyinstaller` va `pillow` bo'lishi kerak:

    python -m pip install pyinstaller pillow
"""
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ILDIZ = Path(__file__).resolve().parent.parent
QURISH = ILDIZ / "ornatuvchi"
IKON = QURISH / "xozmag.ico"
ARXIV = QURISH / "dastur.zip"
ISH = QURISH / "_ish"                 # PyInstaller ning oraliq fayllari


def buyruq(qatorlar: list) -> None:
    print(">", " ".join(str(q) for q in qatorlar))
    natija = subprocess.run(qatorlar, cwd=str(ILDIZ))
    if natija.returncode != 0:
        raise SystemExit(f"Xatolik: {qatorlar[0]} {natija.returncode} qaytardi")


# ------------------------------------------------------------------- ikonka
def ikonka_yasa() -> None:
    """Ko'k kvadrat ustida oq savat — dastur belgisi."""
    from PIL import Image, ImageDraw

    olcham = 512
    im = Image.new("RGBA", (olcham, olcham), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, olcham - 1, olcham - 1], radius=112,
                        fill=(37, 99, 235, 255))

    # savat tanasi — pastga torayadigan to'rtburchak
    tana = [(126, 196), (386, 196), (352, 420), (160, 420)]
    d.polygon(tana, fill=(255, 255, 255, 255))
    # savat dastasi — yarim aylana
    d.arc([186, 118, 326, 258], start=180, end=360, fill=(255, 255, 255, 255),
          width=26)
    # tanadagi ikki chiziq
    d.line([(196, 246), (196, 344)], fill=(37, 99, 235, 255), width=20)
    d.line([(316, 246), (316, 344)], fill=(37, 99, 235, 255), width=20)

    olchamlar = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128),
                 (256, 256)]
    im.save(IKON, format="ICO", sizes=olchamlar)
    print("ikonka:", IKON)


# -------------------------------------------------------------- dastur va exe
def dasturni_yig() -> Path:
    """Saytning o'zini Xozmag.exe qilib yig'adi."""
    keral = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
        "--name", "Xozmag",
        "--windowed",
        "--icon", str(IKON),
        "--distpath", str(ILDIZ / "dist"),
        "--workpath", str(ISH),
        "--specpath", str(ISH),
        "--add-data", f"{ILDIZ / 'templates'}{os.pathsep}templates",
        "--add-data", f"{ILDIZ / 'static'}{os.pathsep}static",
        "--add-data", f"{ILDIZ / 'versiya.txt'}{os.pathsep}.",
        "--add-data", f"{IKON}{os.pathsep}.",
        "--add-data", f"{ILDIZ / 'db.sqlite3'}{os.pathsep}boshlangich_baza",
        "--collect-all", "django",
        "--collect-submodules", "config",
        "--collect-submodules", "ombor",
        "--collect-submodules", "qarz",
        "--collect-submodules", "sotuv",
        "--hidden-import", "config.kontekst",
        str(ILDIZ / "ishga_tushir.py"),
    ]
    buyruq(keral)
    papka = ILDIZ / "dist" / "Xozmag"
    shutil.copy2(IKON, papka / "xozmag.ico")   # yorliq ikonkasi uchun
    shutil.copy2(QURISH / "OCHIRISH.bat", papka / "OCHIRISH.bat")
    return papka


def arxivla(papka: Path) -> None:
    if ARXIV.exists():
        ARXIV.unlink()
    with zipfile.ZipFile(ARXIV, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for fayl in papka.rglob("*"):
            if fayl.is_file():
                z.write(fayl, fayl.relative_to(papka))
    print("arxiv:", ARXIV, f"{ARXIV.stat().st_size / 1048576:.1f} MB")


def bat_ornatuvchi(papka: Path) -> Path:
    """.bat bilan o'rnatiladigan variant: papka + ORNATISH.bat + OCHIRISH.bat.

    Exe ishlamagan (antivirus to'sgan) joyda shu ishlaydi — ichida hech qanday
    yig'ilgan o'rnatgich yo'q, oddiy nusxa ko'chirish.
    """
    joy = ILDIZ / "dist" / "XozmagOrnatuvchi"
    shutil.rmtree(joy, ignore_errors=True)
    joy.mkdir(parents=True, exist_ok=True)
    shutil.copytree(papka, joy / "Xozmag")
    shutil.copy2(QURISH / "ORNATISH.bat", joy / "ORNATISH.bat")
    shutil.copy2(QURISH / "OCHIRISH.bat", joy / "OCHIRISH.bat")

    arxiv = ILDIZ / "dist" / "XozmagOrnatuvchi.zip"
    if arxiv.exists():
        arxiv.unlink()
    with zipfile.ZipFile(arxiv, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for fayl in joy.rglob("*"):
            if fayl.is_file():
                z.write(fayl, Path("XozmagOrnatuvchi") / fayl.relative_to(joy))
    print("bat o'rnatuvchi:", arxiv, f"{arxiv.stat().st_size / 1048576:.1f} MB")
    return arxiv


def ornatgichni_yig() -> Path:
    keral = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
        "--name", "XozmagOrnatish",
        "--onefile", "--windowed",
        "--icon", str(IKON),
        "--distpath", str(ILDIZ / "dist"),
        "--workpath", str(ISH),
        "--specpath", str(ISH),
        "--add-data", f"{ARXIV}{os.pathsep}.",
        "--add-data", f"{IKON}{os.pathsep}.",
        "--add-data", f"{ILDIZ / 'versiya.txt'}{os.pathsep}.",
        str(QURISH / "ornatuvchi.py"),
    ]
    buyruq(keral)
    return ILDIZ / "dist" / "XozmagOrnatish.exe"


def main() -> int:
    print("=" * 58)
    print("Ulug'bek Xozmag — o'rnatuvchini yig'ish")
    print("=" * 58)
    ikonka_yasa()
    papka = dasturni_yig()
    zip_fayl = bat_ornatuvchi(papka)
    arxivla(papka)
    exe = ornatgichni_yig()
    shutil.rmtree(ISH, ignore_errors=True)
    print()
    print("TAYYOR — ikkita variant:")
    print(f"  1) {exe}  ({exe.stat().st_size / 1048576:.1f} MB)")
    print("     bitta fayl, ikki marta bosiladi;")
    print(f"  2) {zip_fayl}  ({zip_fayl.stat().st_size / 1048576:.1f} MB)")
    print("     arxivni ochib ORNATISH.bat ni bosish kerak.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
