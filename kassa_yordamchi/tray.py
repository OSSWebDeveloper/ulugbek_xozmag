"""BizaroPOS cashier tray menu; runs on the Windows main thread."""
import base64
import ipaddress
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
PS = str(Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe')
# Server bilan aloqa shuncha soniya uzilib tursa, manzil o'zi so'raladi.
ALOQA_KUTISH = 15

# Kichik WinForms oynasi: yangi manzil stdout'ga chiqadi, «Bekor qilish» — bo'sh.
_OYNA = r'''
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()
function M($s) { [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($s)) }
$f = New-Object System.Windows.Forms.Form
$f.Text = 'BizaroPOS Kassa - server manzili'
$f.FormBorderStyle = 'FixedDialog'; $f.MaximizeBox = $false; $f.MinimizeBox = $false
$f.StartPosition = 'CenterScreen'; $f.TopMost = $true; $f.ShowInTaskbar = $true
$f.Font = New-Object System.Drawing.Font('Segoe UI', 10)
$y = 14
$sabab = M '__SABAB__'
if ($sabab) {
  $s = New-Object System.Windows.Forms.Label
  $s.Text = $sabab; $s.Location = New-Object System.Drawing.Point(16, $y)
  $s.Size = New-Object System.Drawing.Size(428, 40); $s.Font = New-Object System.Drawing.Font('Segoe UI', 10, [System.Drawing.FontStyle]::Bold)
  $f.Controls.Add($s); $y += 44
}
$l = New-Object System.Windows.Forms.Label
$l.Text = M '__MATN__'; $l.Location = New-Object System.Drawing.Point(16, $y)
$l.Size = New-Object System.Drawing.Size(428, 40); $f.Controls.Add($l); $y += 44
$t = New-Object System.Windows.Forms.TextBox
$t.Text = M '__QIYMAT__'; $t.Location = New-Object System.Drawing.Point(16, $y)
$t.Size = New-Object System.Drawing.Size(428, 28); $t.Font = New-Object System.Drawing.Font('Consolas', 12)
$f.Controls.Add($t); $y += 38
$xato = M '__XATO__'
if ($xato) {
  $e = New-Object System.Windows.Forms.Label
  $e.Text = $xato; $e.ForeColor = [System.Drawing.Color]::FromArgb(200, 30, 30)
  $e.Location = New-Object System.Drawing.Point(16, $y); $e.Size = New-Object System.Drawing.Size(428, 40)
  $f.Controls.Add($e); $y += 44
}
$ok = New-Object System.Windows.Forms.Button
$ok.Text = 'Saqlash'; $ok.Size = New-Object System.Drawing.Size(130, 34)
$ok.Location = New-Object System.Drawing.Point(178, $y); $ok.DialogResult = 'OK'
$no = New-Object System.Windows.Forms.Button
$no.Text = 'Bekor qilish'; $no.Size = New-Object System.Drawing.Size(130, 34)
$no.Location = New-Object System.Drawing.Point(314, $y); $no.DialogResult = 'Cancel'
$f.Controls.AddRange(@($ok, $no)); $f.AcceptButton = $ok; $f.CancelButton = $no
$f.ClientSize = New-Object System.Drawing.Size(460, ($y + 50))
$f.Add_Shown({ $f.Activate(); $t.Focus(); $t.SelectAll() })
if ($f.ShowDialog() -eq 'OK') {
  [Console]::OutputEncoding = [Text.Encoding]::UTF8
  [Console]::Out.Write('=' + $t.Text)
}
'''


def _b64(text):
    return base64.b64encode(text.encode('utf-8')).decode('ascii')


def manzil_oynasi(qiymat, xato='', sabab=''):
    """Foydalanuvchidan manzil so'raydi; «Bekor qilish» bosilsa None."""
    code = _OYNA
    for kalit, matn in (('__SABAB__', sabab), ('__XATO__', xato), ('__QIYMAT__', qiymat), ('__MATN__',
            'Server kompyuterining IP manzilini kiriting, masalan 192.168.1.5 '
            '(port boshqa bo‘lsa: 192.168.1.5:5555).')):
        code = code.replace(kalit, _b64(matn))
    result = subprocess.run([PS, '-NoProfile', '-NonInteractive', '-Sta', '-EncodedCommand',
        base64.b64encode(code.encode('utf-16-le')).decode('ascii')], capture_output=True,
        encoding='utf-8', errors='replace', creationflags=NO_WINDOW)
    out = result.stdout.lstrip('\ufeff')
    return out[1:].strip() if out.startswith('=') else None


def joriy_manzil(url):
    """Oynada ko'rsatiladigan qism: 192.168.1.5:5555."""
    return urllib.parse.urlsplit(url).netloc


def yangi_url(matn, eski_url):
    """«192.168.1.5», «192.168.1.5:5555» yoki «http://…/» dan server manzilini yasaydi."""
    eski = urllib.parse.urlsplit(eski_url)
    matn = matn.strip().replace(' ', '')
    if not matn:
        raise ValueError('Server IP manzilini kiriting.')
    if '://' not in matn:
        matn = (eski.scheme or 'http') + '://' + matn
    qism = urllib.parse.urlsplit(matn)
    if qism.scheme not in ('http', 'https') or (qism.path not in ('', '/')) or qism.query or qism.username:
        raise ValueError('Faqat IP manzil va port yozing, masalan 192.168.1.5:5555.')
    try:
        ip = ipaddress.IPv4Address(qism.hostname or '')
        port = qism.port or eski.port or 5555
    except ValueError:
        raise ValueError('IP manzil noto‘g‘ri. To‘rtta son nuqta bilan: 192.168.1.5.') from None
    if ip.is_loopback or ip.is_unspecified or ip.is_multicast or ip.is_link_local or str(ip).endswith('.255'):
        raise ValueError('Bu manzil server bo‘la olmaydi. Server kompyuterining tarmoqdagi IP manzilini yozing.')
    return f'{qism.scheme}://{ip}:{port}'


def ulanib_kor(url, config, state):
    """Yangi manzilda shu kassaning kaliti bilan serverga bir marta murojaat qiladi."""
    body = json.dumps({'nom': socket.gethostname(), 'printer': state.get('printer', '')},
                      ensure_ascii=True).encode('ascii')
    request = urllib.request.Request(url + '/qurilmalar/kassa-agent/almashish/', body,
        {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + config['token']})
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=8) as response:
            if json.load(response).get('ok') is True:
                return ''
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            return ('Server topildi, lekin bu kassaning kaliti u yerda yo‘q. Shu serverdan '
                    'Qurilmalar bo‘limida kassa paketini qayta yuklab o‘rnating.')
        return f'Bu manzilda BizaroPOS serveri topilmadi (javob {exc.code}).'
    except (OSError, ValueError):
        return 'Serverga ulanib bo‘lmadi. Server kompyuteri yoqilganini, IP manzil va tarmoqni tekshiring.'
    return 'Bu manzilda BizaroPOS serveri topilmadi.'


def saqla(root, config):
    path = root / 'kassa.json'
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(config, ensure_ascii=True), encoding='ascii')
    temp.replace(path)


def run_tray(root, config, stop, state):
    sys.path.insert(0,str(root/'tray_deps'))
    import pystray
    from pystray._util import win32
    from PIL import Image

    restart=[False]
    class LeftMenuIcon(pystray.Icon):
        def _on_notify(self,wparam,lparam):
            if lparam==win32.WM_LBUTTONUP:
                lparam=win32.WM_RBUTTONUP
            if lparam==win32.WM_RBUTTONUP:
                # Menyu bir marta yasaladi; server manzili va belgilar yangi ko'rinsin.
                self._update_menu()
            return super()._on_notify(wparam,lparam)

    def close(icon,item):
        stop.set();icon.stop()

    def reboot(icon,item):
        restart[0]=True;close(icon,item)

    updating=[False]
    def update(icon,item):
        if updating[0]:return
        updating[0]=True
        def work():
            try:
                from updater import stage_update
                icon.notify('Serverdan yangilanish olinmoqda…','BizaroPOS Kassa')
                stage=stage_update(root,config)
                if stage is None:
                    icon.notify('Dastur yangilangan. Yangi o‘zgarish yo‘q.','BizaroPOS Kassa')
                else:
                    restart[0]=str(stage)
                    close(icon,item)
            except Exception as exc:icon.notify(str(exc)[:200],'Yangilash bajarilmadi')
            finally:updating[0]=False
        threading.Thread(target=work,daemon=True).start()

    def select(name):
        def choose(icon,item):
            config['printer']=name
            saqla(root,config)
            state['refresh']=True
            icon.notify('Chek printeri: '+(name or 'Avtomatik'),'BizaroPOS Kassa')
        return choose

    def printer_items():
        yield pystray.MenuItem('Avtomatik',select(''),checked=lambda item:not config.get('printer'))
        for printer in state['printers']:
            name=printer['nom']
            yield pystray.MenuItem(name.replace('&','&&'),select(name),checked=lambda item,n=name:config.get('printer')==n)

    asking=threading.Lock()
    def ask_address(sabab=''):
        """Server manzilini so'raydi, yangi manzilda tekshiradi va kassa.json ga yozadi."""
        if not asking.acquire(blocking=False):
            return
        try:
            qiymat,xato=joriy_manzil(config['url']),''
            while not stop.is_set():
                javob=manzil_oynasi(qiymat,xato,sabab)
                if javob is None:
                    return
                qiymat=javob
                try:
                    url=yangi_url(javob,config['url'])
                except ValueError as exc:
                    xato=str(exc);continue
                xato=ulanib_kor(url,config,state)
                if xato:
                    continue
                eski=config['url']
                config['url']=url
                saqla(root,config)
                state['uzildi']=None;state['soraldi']=False;state['refresh']=True
                icon.notify('Server manzili saqlandi: '+joriy_manzil(url),'BizaroPOS Kassa')
                if url!=eski:
                    webbrowser.open(url)
                return
        except Exception as exc:
            icon.notify(str(exc)[:200],'Server manzili saqlanmadi')
        finally:
            asking.release()

    def change_address(icon,item):
        threading.Thread(target=ask_address,daemon=True).start()

    def watch():
        """Aloqa uzilsa (server IP o'zgargan bo'lishi mumkin) manzilni o'zi so'raydi."""
        while not stop.wait(2):
            since=state.get('uzildi')
            if since and not state.get('soraldi') and time.monotonic()-since>=ALOQA_KUTISH:
                state['soraldi']=True
                ask_address('Server bilan aloqa yo‘q ('+joriy_manzil(config['url'])+'). '
                            'Server IP manzili o‘zgargan bo‘lsa, yangisini kiriting.')

    def address_text(item):
        holat='aloqa yo‘q' if state.get('uzildi') else 'ulangan'
        return 'Server: '+joriy_manzil(config['url'])+' — '+holat

    version=(root/'versiya.txt').read_text(encoding='utf-8').strip()
    icon=LeftMenuIcon('BizaroPOSKassa',Image.open(root/'bizaropos.ico'),
        'BizaroPOS '+config.get('kassir','Kassa'),pystray.Menu(
        pystray.MenuItem('Kassani ochish',lambda icon,item:webbrowser.open(config['url'])),
        pystray.MenuItem('Chek printerini tanlash',pystray.Menu(printer_items)),
        pystray.MenuItem('Printerlarni yangilash',lambda icon,item:state.update(refresh=True)),
        pystray.MenuItem('Server IP manzilini o‘zgartirish',change_address),
        pystray.MenuItem(address_text,None,enabled=False),
        pystray.MenuItem('Dasturni yangilash',update),
        pystray.MenuItem('Yordamchini qayta ishga tushirish',reboot),
        pystray.MenuItem('Yordamchini yopish',close),
        pystray.MenuItem('Dastur versiyasi: '+version,None,enabled=False)))
    threading.Thread(target=watch,daemon=True).start()
    icon.run()
    return restart[0]
