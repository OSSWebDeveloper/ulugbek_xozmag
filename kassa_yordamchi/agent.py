"""BizaroPOS USB print companion: outbound polling only, one terminal account."""
import ctypes
import json
import logging
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
PS = str(Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe')


def powershell(code):
    import base64
    result = subprocess.run([PS, '-NoProfile', '-NonInteractive', '-EncodedCommand',
        base64.b64encode(code.encode('utf-16-le')).decode('ascii')], capture_output=True,
        encoding='utf-8', errors='replace', timeout=20, creationflags=NO_WINDOW)
    if result.returncode:
        raise RuntimeError('Windows printer ro‘yxatini olib bo‘lmadi.')
    return result.stdout.strip().lstrip('\ufeff')


def printer_name(config):
    rows = json.loads(powershell("[Console]::OutputEncoding=[Text.Encoding]::UTF8; ConvertTo-Json -InputObject @(Get-CimInstance Win32_Printer | Select-Object Name,Default) -Compress"))
    available = [p['Name'] for p in rows if not any(s in p['Name'].lower() for s in ('pdf', 'xps', 'onenote', 'fax'))]
    preferred = config.get('printer', '')
    if preferred:
        return preferred if preferred in available else ''
    defaults = [p['Name'] for p in rows if p.get('Default') and p['Name'] in available]
    return defaults[0] if defaults else (available[0] if len(available) == 1 else '')


def exchange(config, data):
    request = urllib.request.Request(config['url'] + '/qurilmalar/kassa-agent/almashish/',
        json.dumps(data, ensure_ascii=True).encode('ascii'),
        {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + config['token']})
    # Do not let Windows proxy settings redirect local shop traffic.
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=20) as response:
        return json.load(response)


def atomic_json(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=True), encoding='ascii')
    temp.replace(path)


def main():
    logging.basicConfig(filename=ROOT / 'kassa.log', level=logging.INFO,
                        format='%(asctime)s %(message)s', encoding='utf-8')
    config = json.loads((ROOT / 'kassa.json').read_text(encoding='utf-8-sig'))
    kernel = ctypes.windll.kernel32
    kernel.CreateMutexW.restype = ctypes.c_void_p
    mutex = kernel.CreateMutexW(None, False, 'Local\\BizaroPOSUsbAgent')
    if kernel.GetLastError() == 183:
        webbrowser.open(config['url'])
        return
    webbrowser.open(config['url'])
    devices = []
    printer = ''
    next_scan = 0
    pending = ROOT / 'joriy_vazifa.json'
    while True:
        try:
            if time.monotonic() >= next_scan:
                next_scan = time.monotonic() + 30
                try:
                    from local_devices import aniqlash
                    devices = aniqlash()
                except Exception:
                    logging.exception('USB ro‘yxati yangilanmadi')
                printer = printer_name(config)
            ack = None
            if pending.exists():
                stored = json.loads(pending.read_text(encoding='ascii'))
                # A crash after the spooler accepted a job is ambiguous. Never print
                # the same job automatically a second time.
                ack = {'id': stored['id'], 'claim': stored['claim'], 'ok': stored.get('ok', False),
                       'xato': stored.get('xato', 'Oldingi chop holati noma’lum; chekni tekshirib qo‘lda qayta chiqaring.')}
            result = exchange(config, {'nom': socket.gethostname(), 'printer': printer,
                'qurilmalar': devices, 'tayyor': bool(printer) and not pending.exists(), 'ack': ack})
            if ack:
                pending.unlink(missing_ok=True)
            job = result.get('vazifa')
            if job:
                atomic_json(pending, {'id': job['id'], 'claim': job['claim']})
                data = job['data']
                data['printer'] = printer  # Never use a server printer name.
                path = ROOT / 'chek.json'
                atomic_json(path, data)
                process = subprocess.run([PS, '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                    '-File', str(ROOT / 'chek_print.ps1'), '-DataFile', str(path)], capture_output=True,
                    timeout=40, creationflags=NO_WINDOW)
                atomic_json(pending, {'id': job['id'], 'claim': job['claim'], 'ok': process.returncode == 0,
                    'xato': '' if process.returncode == 0 else 'USB printerga yuborilmadi.'})
        except Exception:
            logging.exception('Kassa qurilmalari bilan aloqa xatosi')
        time.sleep(2)


if __name__ == '__main__':
    main()
