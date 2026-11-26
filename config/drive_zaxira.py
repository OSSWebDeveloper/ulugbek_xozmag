"""Har kuni 20:00 da ombor .xlsx faylini Google Drive papkasiga yozadi (zaxira).

Serverning ishchi jarayonida (bizaropos_server.py --worker) fon oqimi bo'lib ishlaydi.
Server kompyuterida «Google Drive for Desktop» o'rnatilgan va akkauntga kirilgan bo'lishi
kerak: fayl `G:\\Мой диск\\Xozmag zaxira\\` ga yoziladi, Drive ilovasi uni o'zi yuklaydi.
Sozlamalar — shu fayl boshidagi konstantalar, ko'rinish (UI) yo'q.

Fayl avval `qurilmalar_data/server/drive_zaxira/navbat/` da yaratiladi, Drive papkasiga
ko'chirilgach bir papka yuqoriga o'tadi. Drive topilmasa har 10 daqiqada qayta urinadi;
server 20:00 dan keyin yoqilsa o'sha kunning zaxirasi darhol olinadi.
"""
import ctypes
import datetime
import logging
import shutil
import string
import threading
import time
from pathlib import Path

ZAXIRA_SOATI = datetime.time(20, 0)
DRIVE_PAPKA_YOLI = ''            # bo'sh — Google Drive diski o'zi topiladi
DRIVE_ICHKI_PAPKA = 'Xozmag zaxira'
MENING_DISKIM = ('Мой диск', 'My Drive', 'Mening diskim')
FAYL_NOMI = 'Xozmag ombor {sana}.xlsx'
MAHALLIY_SAQLANADI = 30          # kompyuterda qoladigan oxirgi nusxalar
QAYTA_URINISH = 600              # soniya

ROOT = Path(__file__).resolve().parent.parent
PAPKA = ROOT / 'qurilmalar_data' / 'server' / 'drive_zaxira'
NAVBAT = PAPKA / 'navbat'
OXIRGI = PAPKA / 'oxirgi_sana.txt'

log = logging.getLogger('drive_zaxira')


def _ildizlar():
    """Disk harflari, keyin tomlar (Volume{...} yo'li): administrator bo'lib ishlagan
    server Drive ilovasining G: harfini ko'rmasligi mumkin, tom yo'li esa hammaga ko'rinadi."""
    for harf in string.ascii_uppercase:
        yield f'{harf}:\\'
    k = ctypes.windll.kernel32
    k.FindFirstVolumeW.restype = ctypes.c_void_p
    k.FindNextVolumeW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint]
    k.FindVolumeClose.argtypes = [ctypes.c_void_p]
    b = ctypes.create_unicode_buffer(300)
    h = k.FindFirstVolumeW(b, 300)
    if h in (None, ctypes.c_void_p(-1).value):
        return
    try:
        while True:
            yield b.value
            if not k.FindNextVolumeW(h, b, 300):
                break
    finally:
        k.FindVolumeClose(h)


def drive_papka():
    if DRIVE_PAPKA_YOLI:
        return Path(DRIVE_PAPKA_YOLI)
    for ildiz in _ildizlar():
        try:
            if not Path(ildiz, '.shortcut-targets-by-id').is_dir():
                continue
            for nom in MENING_DISKIM:
                if Path(ildiz, nom).is_dir():
                    return Path(ildiz, nom, DRIVE_ICHKI_PAPKA)
        except OSError:
            continue
    return None


def fayl_yasa(sana):
    from ombor.excel import excel_yoz, tovarlar
    NAVBAT.mkdir(parents=True, exist_ok=True)
    fayl = NAVBAT / FAYL_NOMI.format(sana=sana.isoformat())
    vaqtinchalik = fayl.with_suffix('.tmp')
    vaqtinchalik.write_bytes(excel_yoz(tovarlar()))
    vaqtinchalik.replace(fayl)
    return fayl


def _tozala():
    for f in sorted(PAPKA.glob('*.xlsx'))[:-MAHALLIY_SAQLANADI]:
        f.unlink(missing_ok=True)


def navbatni_yubor():
    fayllar = sorted(NAVBAT.glob('*.xlsx')) if NAVBAT.exists() else []
    if not fayllar:
        return
    manzil = drive_papka()
    if manzil is None:
        raise RuntimeError('Google Drive diski topilmadi (Drive ilovasi o‘chiq yoki akkauntga kirilmagan)')
    manzil.mkdir(exist_ok=True)
    for fayl in fayllar:
        shutil.copyfile(fayl, manzil / fayl.name)
        fayl.replace(PAPKA / fayl.name)
        log.info('Drive zaxirasi yozildi: %s', manzil / fayl.name)
    _tozala()


def bir_qadam(hozir=None):
    """Vaqti kelgan bo'lsa faylni yasaydi va navbatni Drive papkasiga ko'chiradi."""
    hozir = hozir or datetime.datetime.now()
    PAPKA.mkdir(parents=True, exist_ok=True)
    oxirgi = OXIRGI.read_text().strip() if OXIRGI.exists() else ''
    if hozir.time() >= ZAXIRA_SOATI and oxirgi != hozir.date().isoformat():
        from django.db import connection
        try:
            fayl_yasa(hozir.date())
        finally:
            connection.close()
        OXIRGI.write_text(hozir.date().isoformat())
    navbatni_yubor()


def _sikl():
    keyingi_urinish = 0.0
    while True:
        if time.monotonic() >= keyingi_urinish:
            try:
                bir_qadam()
            except Exception:
                log.exception('Drive zaxirasi bajarilmadi, %d soniyadan keyin qayta urinadi', QAYTA_URINISH)
                keyingi_urinish = time.monotonic() + QAYTA_URINISH
        time.sleep(60)


def boshla():
    threading.Thread(target=_sikl, name='drive_zaxira', daemon=True).start()
