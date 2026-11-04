"""BizaroPOS Windows tray supervisor and LAN WSGI server."""
import ctypes
import logging
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
import zipfile

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'qurilmalar_data' / 'server'
PORT = 5555
URL = f'http://127.0.0.55:{PORT}/'
REPO = 'https://github.com/OSSWebDeveloper/ulugbek_xozmag'
NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)


def version():
    return (ROOT / 'versiya.txt').read_text(encoding='utf-8').strip()


def worker():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    os.environ['XOZMAG_SERVER'] = '1'
    import django
    django.setup()
    from django.core.management import call_command
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from django.core.handlers.wsgi import WSGIHandler
    from waitress import create_server, wasyncore
    call_command('migrate', interactive=False, verbosity=0)
    call_command('standart_akkauntlar', verbosity=0)
    server = create_server(StaticFilesHandler(WSGIHandler()), host='0.0.0.0', port=PORT, threads=8)
    stop_file = DATA / f'stop-{os.getpid()}'
    stop_file.unlink(missing_ok=True)
    def drain():
        while not stop_file.exists():
            time.sleep(.2)
        server.close()
        server.task_dispatcher.shutdown(timeout=30)
        stop_file.unlink(missing_ok=True)
        wasyncore.close_all(map=server._map)
    threading.Thread(target=drain, daemon=True).start()
    server.run()


def backup():
    target = DATA / 'zaxira' / time.strftime('%Y%m%d-%H%M%S')
    target.mkdir(parents=True, exist_ok=False)
    with sqlite3.connect(ROOT / 'db.sqlite3') as source, sqlite3.connect(target / 'db.sqlite3') as dest:
        source.backup(dest)
        if dest.execute('pragma integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('Baza zaxirasi tekshiruvdan o‘tmadi')
    with zipfile.ZipFile(target / 'kod.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in ROOT.rglob('*'):
            rel = path.relative_to(ROOT)
            if any(part in {'.git', '__pycache__', '.venv', 'venv', 'qurilmalar_data', 'qurilma_drivers'} for part in rel.parts):
                continue
            if path.is_file() and path.name not in {'db.sqlite3', '.secret_key'}:
                archive.write(path, str(rel))
    return target


class Supervisor:
    def __init__(self):
        self.process = None
        self.busy = threading.Lock()
        self.closing = threading.Event()
        self.update_text = 'Dasturni yangilash'
        # Admin UAC launcher passes the Git executable explicitly because
        # elevated processes may not inherit the user's PATH.
        self.git_path = os.environ.get('BIZARO_GIT') or 'git'
        if '--git-path' in sys.argv:
            index = sys.argv.index('--git-path') + 1
            if index < len(sys.argv) and sys.argv[index]:
                self.git_path = sys.argv[index]

    def git(self, *args):
        # Windows o'rnatuvchisi Administrator orqali ishga tushirilsa, papkaning
        # egasi foydalanuvchidan farq qilishi mumkin. Faqat joriy ilova
        # papkasi uchun Git ishonchini vaqtincha taqdim etamiz.
        # Global safe.directory='*' ishlatilmaydi.
        result = subprocess.run([self.git_path, '-c', 'safe.directory=' + str(ROOT), *args],
                                cwd=ROOT, capture_output=True,
                                text=True, encoding='utf-8', errors='replace', timeout=90,
                                creationflags=NO_WINDOW, env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'})
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or 'Git buyrug‘i bajarilmadi')
        return result.stdout.strip()

    def start(self):
        with socket.socket() as probe:
            if probe.connect_ex(('127.0.0.1', PORT)) == 0:
                raise RuntimeError('5555 port band. Boshqa server nusxasini yoping.')
        log = open(DATA / 'server.log', 'a', encoding='utf-8')
        self.process = subprocess.Popen([sys.executable, str(Path(__file__)), '--worker'],
                                        cwd=ROOT, stdout=log, stderr=log, creationflags=NO_WINDOW)
        log.close()
        deadline = time.monotonic() + 35
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError('Server ochilmadi. qurilmalar_data/server/server.log ni tekshiring.')
            try:
                with urllib.request.urlopen(URL, timeout=1) as response:
                    if response.status == 200:
                        return
            except OSError:
                time.sleep(.2)
        self.stop_worker()
        raise RuntimeError('Serverni ishga tushirish vaqti tugadi.')

    def stop_worker(self):
        if self.process and self.process.poll() is None:
            (DATA / f'stop-{self.process.pid}').touch()
            self.process.wait(timeout=40)

    def notify(self, text):
        logging.info(text)
        self.icon.notify(text, 'BizaroPOS')

    def run_action(self, action):
        def run():
            if not self.busy.acquire(blocking=False):
                self.notify('Boshqa amal bajarilmoqda. Biroz kuting.')
                return
            try:
                action()
            except Exception as exc:
                logging.exception('Server amali bajarilmadi')
                self.notify(str(exc)[:240])
            finally:
                self.busy.release()
        threading.Thread(target=run, daemon=True).start()

    def restart(self):
        self.stop_worker()
        self.start()
        self.notify('Server qayta ishga tushdi.')

    def check_update(self):
        remote = self.git('remote', 'get-url', 'origin').rstrip('/').removesuffix('.git')
        if remote != REPO:
            raise RuntimeError('GitHub manzili kutilgan omborga mos emas.')
        self.git('fetch', 'origin', 'main')
        current = self.git('rev-parse', 'HEAD')
        latest = self.git('rev-parse', 'FETCH_HEAD')
        self.update_text = 'Dasturni yangilash' + (' — yangi versiya bor' if current != latest else '')
        self.icon.update_menu()
        return current, latest

    def update(self):
        current, latest = self.check_update()
        if current == latest:
            self.notify('GitHub’da yangi versiya yo‘q. Versiya: ' + version())
            return
        # Never discard local work or replace the live warehouse with GitHub's DB.
        # Dastur ishga tushganda hosil bo'ladigan untracked fayllar
        # (BizaroPOS.vbs, loglar, .secret_key va boshqalar) yangilashga
        # to'sqinlik qilmasin. Git merge mavjud faylni bosib yozishni
        # baribir tekshiradi; kuzatilayotgan kodga mahalliy o'zgarish
        # kiritilsa esa yangilash xavfsiz ravishda to'xtaydi.
        changed = self.git('status', '--porcelain', '--untracked-files=no',
                           '--', '.', ':(exclude)db.sqlite3')
        if changed:
            self.notify('Mahalliy kodda GitHub’ga saqlanmagan o‘zgarishlar bor. Yangilash ularni bosib yozmasligi uchun to‘xtatildi.')
            return
        self.git('merge-base', '--is-ancestor', current, latest)
        paths = self.git('diff', '--name-only', current, latest).splitlines()
        protected = {'db.sqlite3', '.secret_key', 'bizaropos_local.json'}
        if any(p in protected or p.startswith(('qurilmalar_data/', 'qurilma_drivers/')) for p in paths):
            raise RuntimeError('Yangilanish mahalliy baza yoki qurilma fayliga tegadi. Avtomatik yangilash to‘xtatildi.')
        self.stop_worker()
        try:
            saved = backup()
            self.git('merge', '--ff-only', latest)
            self.start()
        except Exception:
            if not self.process or self.process.poll() is not None:
                try:
                    self.start()
                except Exception:
                    logging.exception('Yangilashdan keyin server ochilmadi')
            raise
        self.icon.title = 'BizaroPOS ' + version()
        self.icon.update_menu()
        self.notify('Yangilandi. Versiya: ' + version() + '. Zaxira: ' + str(saved))

    def periodic(self):
        while not self.closing.is_set():
            try:
                if self.busy.acquire(blocking=False):
                    try:
                        self.check_update()
                    finally:
                        self.busy.release()
            except Exception:
                logging.exception('GitHub tekshiruvi bajarilmadi')
            self.closing.wait(3600)

    def quit(self):
        self.closing.set()
        self.stop_worker()
        self.icon.stop()

    def run(self):
        import pystray
        from pystray._util import win32
        from PIL import Image

        class LeftMenuIcon(pystray.Icon):
            def _on_notify(self, wparam, lparam):
                if lparam == win32.WM_LBUTTONUP:
                    lparam = win32.WM_RBUTTONUP
                return super()._on_notify(wparam, lparam)

        self.icon = LeftMenuIcon('BizaroPOS', Image.open(ROOT / 'static/img/bizaropos.ico'),
                                'BizaroPOS ' + version(), pystray.Menu(
            pystray.MenuItem('Serverni o‘chirish', lambda: self.run_action(self.quit)),
            pystray.MenuItem('Serverni qayta yuklash', lambda: self.run_action(self.restart)),
            pystray.MenuItem(lambda item: self.update_text, lambda: self.run_action(self.update)),
            pystray.MenuItem(lambda item: 'Dastur versiyasi: ' + version(), None, enabled=False)))
        self.start()
        webbrowser.open(URL)
        def ready(icon):
            icon.visible = True
            from config.tarmoq import doimiy_manzil
            self.notify('Server ishlayapti. Doimiy manzil: ' + doimiy_manzil(PORT))
            threading.Thread(target=self.periodic, daemon=True).start()
        try:
            self.icon.run(setup=ready)
        finally:
            self.closing.set()
            self.stop_worker()


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=DATA / 'boshqaruv.log', level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s', encoding='utf-8')
    if '--worker' in sys.argv:
        worker()
        return
    kernel = ctypes.windll.kernel32
    kernel.CreateMutexW.restype = ctypes.c_void_p
    mutex = kernel.CreateMutexW(None, False, 'Local\\BizaroPOSServer5555')
    if kernel.GetLastError() == 183:
        webbrowser.open(URL)
        return
    try:
        Supervisor().run()
    except Exception as exc:
        logging.exception('BizaroPOS ishga tushmadi')
        ctypes.windll.user32.MessageBoxW(None, str(exc), 'BizaroPOS', 16)
    finally:
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel.CloseHandle(mutex)


if __name__ == '__main__':
    main()
