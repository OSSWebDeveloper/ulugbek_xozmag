"""Kunlik Drive zaxirasi uchun Google akkauntini bir marta ulash.

    python google_ulash.py client_secret_XXXX.json [chiqish.json]

client_secret_XXXX.json — Google Cloud Console'dagi «Desktop app» OAuth mijozi fayli.
Brauzer ochiladi, zaxira tushadigan Google akkauntiga kirib ruxsat berasiz.
Natija: qurilmalar_data/google_drive.json (sayt) yoki ko'rsatilgan fayl
(C++ Xozmag uchun: %LOCALAPPDATA%\\Xozmag\\google_drive.json). Faylni git'ga qo'shmang.

Ruxsat faqat `drive.file`: dastur Drive'da faqat o'zi yaratgan fayllarni ko'radi.
"""
import hashlib
import base64
import http.server
import json
import secrets
import sys
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

SCOPE = 'https://www.googleapis.com/auth/drive.file'


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    mijoz = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    mijoz = mijoz.get('installed') or mijoz.get('web') or mijoz
    chiqish = Path(sys.argv[2]) if len(sys.argv) > 2 else \
        Path(__file__).resolve().parent / 'qurilmalar_data' / 'google_drive.json'

    kod = {}

    class Javob(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            kod.update(urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query))
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write('Tayyor. Oynani yopishingiz mumkin.'.encode())

        def log_message(self, *a):
            pass

    server = http.server.HTTPServer(('127.0.0.1', 0), Javob)
    qaytish = f'http://127.0.0.1:{server.server_port}'
    tekshiruv = secrets.token_urlsafe(48)
    holat = secrets.token_urlsafe(16)
    url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode({
        'client_id': mijoz['client_id'], 'redirect_uri': qaytish, 'response_type': 'code',
        'scope': SCOPE, 'access_type': 'offline', 'prompt': 'consent', 'state': holat,
        'code_challenge_method': 'S256',
        'code_challenge': base64.urlsafe_b64encode(
            hashlib.sha256(tekshiruv.encode()).digest()).rstrip(b'=').decode(),
    })
    print('Brauzerda oching (o‘zi ochilmasa):\n' + url)
    webbrowser.open(url)
    while 'code' not in kod and 'error' not in kod:
        server.handle_request()
    if kod.get('state', [''])[0] != holat or 'error' in kod:
        sys.exit('Ruxsat berilmadi: ' + str(kod.get('error')))

    data = urllib.parse.urlencode({
        'code': kod['code'][0], 'client_id': mijoz['client_id'],
        'client_secret': mijoz['client_secret'], 'redirect_uri': qaytish,
        'grant_type': 'authorization_code', 'code_verifier': tekshiruv,
    }).encode()
    with urllib.request.urlopen('https://oauth2.googleapis.com/token', data, timeout=60) as r:
        token = json.loads(r.read())
    if 'refresh_token' not in token:
        sys.exit('Google refresh_token bermadi: ' + json.dumps(token))
    chiqish.parent.mkdir(parents=True, exist_ok=True)
    chiqish.write_text(json.dumps({
        'client_id': mijoz['client_id'], 'client_secret': mijoz['client_secret'],
        'refresh_token': token['refresh_token'],
    }, indent=2), encoding='utf-8')
    print('Saqlandi:', chiqish)


if __name__ == '__main__':
    main()
