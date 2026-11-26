"""Har kuni 20:00 da ombor .xlsx faylini Google Drive'ga yuklaydi (zaxira).

Serverning ishchi jarayonida (bizaropos_server.py --worker) fon oqimi bo'lib ishlaydi.
Sozlash — koddagi konstantalar va bir martalik `python google_ulash.py`:
u Google akkauntiga kirib `qurilmalar_data/google_drive.json` ni yozadi.
Bu fayl git'ga tushmaydi (ombor ochiq) — unda Drive'ga kirish kaliti turadi.

Fayl avval `qurilmalar_data/server/drive_zaxira/navbat/` ga yoziladi, Drive'ga
yuklangach bir papka yuqoriga ko'chadi. Internet bo'lmasa har 10 daqiqada qayta urinadi;
server 20:00 dan keyin yoqilsa o'sha kunning zaxirasi darhol olinadi.
"""
import datetime
import json
import logging
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

ZAXIRA_SOATI = datetime.time(20, 0)
DRIVE_PAPKA = 'Xozmag zaxira'
FAYL_NOMI = 'Xozmag ombor {sana}.xlsx'
MAHALLIY_SAQLANADI = 30          # kompyuterda qoladigan oxirgi nusxalar
QAYTA_URINISH = 600              # soniya

ROOT = Path(__file__).resolve().parent.parent
SOZLAMA = ROOT / 'qurilmalar_data' / 'google_drive.json'
PAPKA = ROOT / 'qurilmalar_data' / 'server' / 'drive_zaxira'
NAVBAT = PAPKA / 'navbat'
OXIRGI = PAPKA / 'oxirgi_sana.txt'

log = logging.getLogger('drive_zaxira')
XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def sozlama():
    if not SOZLAMA.exists():
        return None
    s = json.loads(SOZLAMA.read_text(encoding='utf-8'))
    return s if all(s.get(k) for k in ('client_id', 'client_secret', 'refresh_token')) else None


def _sorov(url, data=None, headers=None, method=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'Google {e.code}: {e.read()[:300].decode("utf-8", "replace")}') from None


def _token(s):
    data = urllib.parse.urlencode({
        'client_id': s['client_id'], 'client_secret': s['client_secret'],
        'refresh_token': s['refresh_token'], 'grant_type': 'refresh_token',
    }).encode()
    return _sorov('https://oauth2.googleapis.com/token', data,
                  {'Content-Type': 'application/x-www-form-urlencoded'})['access_token']


def _papka_id(token, nom):
    sarlavha = {'Authorization': 'Bearer ' + token}
    q = (f"name = '{nom}' and mimeType = 'application/vnd.google-apps.folder' "
         "and trashed = false")
    topildi = _sorov('https://www.googleapis.com/drive/v3/files?' +
                     urllib.parse.urlencode({'q': q, 'fields': 'files(id)'}), headers=sarlavha)
    if topildi.get('files'):
        return topildi['files'][0]['id']
    meta = json.dumps({'name': nom, 'mimeType': 'application/vnd.google-apps.folder'}).encode()
    return _sorov('https://www.googleapis.com/drive/v3/files', meta,
                  {**sarlavha, 'Content-Type': 'application/json'})['id']


def yukla(fayl, s):
    token = _token(s)
    papka = _papka_id(token, s.get('papka') or DRIVE_PAPKA)
    chegara = uuid.uuid4().hex
    meta = json.dumps({'name': fayl.name, 'parents': [papka]}).encode()
    tana = (f'--{chegara}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n'.encode() + meta +
            f'\r\n--{chegara}\r\nContent-Type: {XLSX}\r\n\r\n'.encode() + fayl.read_bytes() +
            f'\r\n--{chegara}--\r\n'.encode())
    return _sorov('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id',
                  tana, {'Authorization': 'Bearer ' + token,
                         'Content-Type': f'multipart/related; boundary={chegara}'})['id']


def fayl_yasa(sana):
    from ombor.excel import excel_yoz, tovarlar
    NAVBAT.mkdir(parents=True, exist_ok=True)
    fayl = NAVBAT / FAYL_NOMI.format(sana=sana.isoformat())
    vaqtinchalik = fayl.with_suffix('.tmp')
    vaqtinchalik.write_bytes(excel_yoz(tovarlar()))
    vaqtinchalik.replace(fayl)
    return fayl


def _tozala():
    eski = sorted(PAPKA.glob('*.xlsx'))
    for f in eski[:-MAHALLIY_SAQLANADI]:
        f.unlink(missing_ok=True)


def navbatni_yukla(s):
    for fayl in sorted(NAVBAT.glob('*.xlsx')):
        yukla(fayl, s)
        fayl.replace(PAPKA / fayl.name)
        log.info('Drive zaxirasi yuklandi: %s', fayl.name)
    _tozala()


def bir_qadam(hozir=None):
    """Vaqti kelgan bo'lsa faylni yasaydi va navbatni yuklaydi. Yuklanmay qolsa xato chiqaradi."""
    hozir = hozir or datetime.datetime.now()
    s = sozlama()
    if not s:
        return
    PAPKA.mkdir(parents=True, exist_ok=True)
    oxirgi = OXIRGI.read_text().strip() if OXIRGI.exists() else ''
    if hozir.time() >= ZAXIRA_SOATI and oxirgi != hozir.date().isoformat():
        from django.db import connection
        try:
            fayl_yasa(hozir.date())
        finally:
            connection.close()
        OXIRGI.write_text(hozir.date().isoformat())
    if NAVBAT.exists() and any(NAVBAT.glob('*.xlsx')):
        navbatni_yukla(s)


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
    # Sozlama fayli keyin qo'yilsa ham server qayta yoqilmasdan ishlaydi
    threading.Thread(target=_sikl, name='drive_zaxira', daemon=True).start()
