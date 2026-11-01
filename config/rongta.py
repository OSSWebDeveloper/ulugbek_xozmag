"""Rongta RLS1100C: katalogni yuborish va qayta o'qib tekshirish.

SDK: Rongta RLS_setup_V2.0.19.37 ichidagi rtslabelscale.dll (x86).
Kalibrlash, firmware yangilash va barcha PLU'larni o'chirish chaqirilmaydi.
"""
import json
import os
import subprocess
import threading
import time
import unicodedata
import uuid
from collections import Counter
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.cache import never_cache

from ombor.models import Mahsulot, KOD_MAX


def folders():
    data = Path(settings.MALUMOT_DIR) / 'qurilmalar_data'
    data.mkdir(exist_ok=True)
    driver = Path(settings.MALUMOT_DIR) / 'qurilma_drivers' / 'rongta'
    return data, driver


def save(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding='ascii')
    for attempt in range(7):
        try:
            temp.replace(path)
            return
        except PermissionError:
            time.sleep(.05 * (attempt + 1))
    # Windows drayveri/antivirus vaqtincha rename'ni band qilsa progressni yozish.
    path.write_text(temp.read_text(encoding='ascii'), encoding='ascii')
    temp.unlink(missing_ok=True)


def short_name(name):
    # Mahalliy tarozidagi shriftni almashtirmaymiz: lotincha nomlar ASCII.
    text = unicodedata.normalize('NFKD', name.replace('‘', "'").replace('’', "'")).encode('ascii', 'replace').decode()
    return text if len(text) <= 32 else text[:24] + '~' + text[-7:]


def prepare():
    rows, skipped = [], []
    for m in Mahsulot.objects.filter(faol=True, birlik='kg').order_by('kod'):
        reason = None
        if m.valyuta != 'som':
            reason = 'Narx so‘mda emas'
        elif m.narx <= 0:
            reason = 'Sotish narxi yo‘q'
        elif m.narx > Decimal('999999.99'):
            reason = 'Narx tarozi chegarasidan katta (999 999,99)'
        elif not m.kod.isdigit() or not 1 <= int(m.kod) <= KOD_MAX:
            reason = 'Kod noto‘g‘ri'
        elif '?' in short_name(m.nom):
            reason = 'Nomi tarozi lotin shriftiga mos emas'
        if reason:
            skipped.append({'kod': m.kod, 'nom': m.nom, 'sabab': reason})
            continue
        if not m.tarozi_kodi:
            with transaction.atomic():
                locked = Mahsulot.objects.select_for_update().get(pk=m.pk)
                if not locked.tarozi_kodi:
                    last = Mahsulot.objects.exclude(tarozi_kodi__isnull=True).order_by('-tarozi_kodi').values_list('tarozi_kodi', flat=True).first()
                    next_id = int(last or 0) + 1
                    if next_id > 999999:
                        raise RuntimeError('Tarozi shtrix identifikatorlari tugadi.')
                    locked.tarozi_kodi = f'{next_id:06d}'
                    locked.save(update_fields=['tarozi_kodi'])
                m.tarozi_kodi = locked.tarozi_kodi
        rows.append({
            'PluName': short_name(m.nom), 'LFCode': int(m.kod), 'Code': str(int(m.tarozi_kodi)),
            'UnitPrice': int((m.narx * 100).quantize(Decimal('1'))),
            'AftertaxUP': float(m.narx),
            'WeightUnit': 4,
            'BarCode': 27, 'Deptment': 2, 'HotKey': 0, 'LabelId': 0,
            'ShlefTime': 365, 'ShelfDays': 365, 'PackageType': 0,
            'isDelete': 0,
        })
    return rows, skipped


def bridge(mode='probe', **paths):
    _, driver = folders()
    if os.name != 'nt' or not (driver / 'rtslabelscale.dll').is_file():
        raise RuntimeError('Rongta drayveri o‘rnatilmagan.')
    executable = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'SysWOW64/WindowsPowerShell/v1.0/powershell.exe'
    command = [str(executable), '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
               '-File', str(Path(__file__).with_name('rongta_bridge.ps1')),
               '-DriverDir', str(driver), '-Address', settings.RONGTA_IP, '-Mode', mode]
    for key, value in paths.items():
        command.extend(['-' + key, str(value)])
    result = subprocess.run(command, capture_output=True, encoding='utf-8', errors='replace',
                            creationflags=subprocess.CREATE_NO_WINDOW, timeout=900 if mode == 'sync' else 15)
    if result.returncode:
        raise RuntimeError(result.stderr.strip()[-1000:] or 'Tarozi javob bermadi.')
    return json.loads(result.stdout.lstrip('\ufeff'))


def run_sync(token, rows, skipped):
    data, _ = folders()
    progress = data / (token + '.json')
    input_file = data / (token + '_input.json')
    after = data / (token + '_after.json')
    backup = data / (token + '_backup.json')
    try:
        save(input_file, rows)
        save(data / (token + '_otkazilgan.json'), skipped)
        result = bridge('sync', InputJson=input_file, OutputJson=after,
                        BackupFile=backup, ProgressJson=progress)
        actual = {int(r['LFCode']): r for r in json.loads(after.read_text(encoding='utf-8')) if not r.get('isDelete')}
        keys = ('Code', 'UnitPrice', 'WeightUnit', 'BarCode', 'Deptment', 'PluName')
        mismatch = [r['LFCode'] for r in rows if r['LFCode'] not in actual or
                    any(actual[r['LFCode']].get(k) != r[k] for k in keys)]
        if mismatch:
            raise RuntimeError(f'{len(mismatch)} mahsulot tarozidagi ma’lumotga mos kelmadi. Birinchi kodlar: {mismatch[:10]}')
        if set(actual) != {r['LFCode'] for r in rows}:
            raise RuntimeError('Tarozida yuborilgan kg katalogidan tashqari faol mahsulot qoldi.')
        status = {'holat': 'tayyor', 'yuborildi': len(rows), 'jami': len(rows),
                  'tekshirildi': len(rows), 'otkazildi': len(skipped), 'vaqt': timezone.now().isoformat(),
                  'backup': backup.name, 'protocol': result['protocol']}
        save(progress, status)
        save(data / 'rongta_last_sync.json', status)
    except Exception as exc:
        save(progress, {'holat': 'xato', 'xato': str(exc),
                        'izoh': 'Qisman yuborilgan bo‘lishi mumkin. Zaxira va hisobot saqlanadi.'})
    finally:
        (data / 'rongta_sync.lock').unlink(missing_ok=True)


def start_sync(background=True):
    data, _ = folders()
    rows, skipped = prepare()
    if not rows:
        raise RuntimeError('Taroziga yuboriladigan narxli mahsulot yo‘q.')
    try:
        fd = os.open(data / 'rongta_sync.lock', os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise RuntimeError('Yuklash davom etmoqda. Tugashini kuting.')
    token = str(uuid.uuid4())
    os.write(fd, token.encode('ascii'))
    os.close(fd)
    save(data / (token + '.json'), {'holat': 'boshlanmoqda', 'jami': len(rows), 'yuborildi': 0})
    if background:
        threading.Thread(target=run_sync, args=(token, rows, skipped), daemon=True).start()
    else:
        run_sync(token, rows, skipped)
    return token


@login_required
@require_GET
@never_cache
def status(request):
    data, _ = folders()
    rows, skipped = prepare()
    try:
        lock = data / 'rongta_sync.lock'
        if lock.exists():
            return JsonResponse({'ok': True, 'band': True, 'id': lock.read_text(encoding='ascii'),
                                 'address': settings.RONGTA_IP, 'tayyor': len(rows),
                                 'otkazildi': len(skipped)})
        result = bridge()
        result.update({'model': 'RLS1100C', 'tayyor': len(rows), 'otkazildi': len(skipped),
                       'sabablar': dict(Counter(r['sabab'] for r in skipped))})
        last = data / 'rongta_last_sync.json'
        if last.exists():
            result['oxirgi'] = json.loads(last.read_text(encoding='ascii'))
        return JsonResponse(result)
    except (RuntimeError, OSError, subprocess.SubprocessError, ValueError) as exc:
        return JsonResponse({'ok': False, 'xato': str(exc)}, status=503)


@login_required
@require_POST
def sync(request):
    try:
        token = start_sync()
        return JsonResponse({'id': token}, status=202)
    except RuntimeError as exc:
        return JsonResponse({'xato': str(exc)}, status=409)


@login_required
@require_GET
@never_cache
def progress(request, token):
    data, _ = folders()
    path = data / (str(token) + '.json')
    if not path.exists():
        return JsonResponse({'xato': 'Yuklash topilmadi'}, status=404)
    return JsonResponse(json.loads(path.read_text(encoding='ascii')))
