"""Native shelf-label printing on the main cashier's Windows printers."""
import ipaddress
import json
import os
from pathlib import Path
import subprocess
import threading
import uuid
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.cache import never_cache
from ombor.models import Mahsulot
from ombor.shtrix import chiziqlar
from qarz.templatetags.xozmag import narxi
from sotuv.chek import TUNNEL_DOMENLARI, mahalliymi

SIZES = {'40x30': (40,30), '56x40': (56,40), '58x40': (58,40), '50x30': (50,30), '30x20': (30,20)}


def folder():
    path = Path(settings.MALUMOT_DIR) / 'qurilmalar_data/etiketkalar'
    path.mkdir(parents=True, exist_ok=True)
    return path


def powershell():
    return str(Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe')


def printers():
    result = subprocess.run([powershell(), '-NoProfile', '-NonInteractive', '-Command',
        '[Console]::OutputEncoding=[Text.Encoding]::UTF8; ConvertTo-Json -InputObject @(Get-Printer | Where-Object {$_.PrinterStatus -notmatch "Paused|Error|Offline"} | Select-Object Name,DriverName,PortName) -Compress'],
        capture_output=True, encoding='utf-8', errors='replace', timeout=15,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), check=True)
    return [dict(nom=p['Name'], drayver=p['DriverName'], port=p['PortName'])
            for p in json.loads(result.stdout.lstrip('\ufeff'))
            if not any(n in p['Name'].lower() for n in ('pdf', 'xps', 'onenote', 'fax'))]


def payload(product, printer, size, copies):
    bars, width = chiziqlar(product.etiketka_kodi)
    return {'printer': printer, 'nom': product.nom, 'kod': product.kod,
            'narx': narxi(product) if product.narx > 0 else 'Narx belgilanmagan',
            'birlik': product.birlik, 'barcode': product.etiketka_kodi,
            'bars': bars, 'modules': width, 'width_mm': SIZES[size][0],
            'height_mm': SIZES[size][1], 'copies': copies}


def render(datafile, preview=None):
    command = [powershell(), '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
        '-File', str(Path(__file__).with_name('etiketka_print.ps1')), '-DataFile', str(datafile)]
    if preview:
        command += ['-PreviewFile', str(preview)]
    result = subprocess.run(command, capture_output=True, encoding='utf-8', errors='replace',
        timeout=60, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode:
        raise RuntimeError('Yorliq printerga yuborilmadi. Printer va qog‘ozni tekshiring.')


def save(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=True), encoding='ascii')
    temp.replace(path)


def work(path, data):
    try:
        render(path.with_suffix('.data.json'))
        data.update(holat='yuborildi', xabar='Yorliq printer navbatiga yuborildi. Qog‘oz chiqqanini tekshiring.')
    except Exception as exc:
        data.update(holat='xato', xabar=str(exc))
    save(path, data)


def ichki_tarmoq(request):
    """Do'kon Wi-Fi'idagi qurilma: tunnel yoki proksi orqali emas, xususiy IP dan."""
    host = request.META.get('HTTP_HOST', '').split(':')[0].lower()
    if host.endswith(TUNNEL_DOMENLARI) or request.META.get('HTTP_X_FORWARDED_FOR'):
        return False
    try:
        return ipaddress.ip_address(request.META.get('REMOTE_ADDR', '')).is_private
    except ValueError:
        return False


def printer_source(request):
    """(printerlar, terminal). terminal None — yorliq server kompyuterining printeridan chiqadi."""
    if mahalliymi(request):
        return printers(), None
    from sotuv.models import KassaTerminal
    from django.utils import timezone
    terminal=KassaTerminal.objects.filter(kassir=request.user).first()
    fresh = bool(terminal and terminal.oxirgi_aloqa and (timezone.now()-terminal.oxirgi_aloqa).total_seconds()<=60)
    if fresh and terminal.etiketka_tayyor:
        return terminal.printerlar, terminal
    # Yordamchisiz do'kon kompyuteri yoki telefoni server printeriga yuboradi.
    if ichki_tarmoq(request):
        return printers(), None
    if not fresh:
        raise RuntimeError('«Brauzerdan chop etish» ni bosing — yorliq shu kompyuterning printeriga chiqadi.')
    raise RuntimeError('USB yordamchisini yangilang: yangi paketni yuklab olib shu kassada qayta o‘rnating.')


@require_GET
@never_cache
def royxat(request):
    try:
        rows, terminal = printer_source(request)
        return JsonResponse({'printerlar': rows, 'serverda': terminal is None and not mahalliymi(request)})
    except RuntimeError as exc:
        return JsonResponse({'xato': str(exc)},status=503)
    except Exception:
        return JsonResponse({'xato': 'Windows printerlari ro‘yxatini olib bo‘lmadi.'}, status=503)


@require_POST
def chop(request, pk):
    product = get_object_or_404(Mahsulot, pk=pk)
    try:
        body = json.loads(request.body)
        token = str(uuid.UUID(body['id']))
        size = body['olcham']
        copies = int(body['soni'])
        printer = body['printer']
        if size not in SIZES or not 1 <= copies <= 500:
            raise ValueError
    except (ValueError, TypeError, KeyError):
        return JsonResponse({'xato': 'Nusxalar soni yoki o‘lcham noto‘g‘ri.'}, status=400)
    try:
        rows, terminal = printer_source(request)
    except RuntimeError as exc:
        return JsonResponse({'xato':str(exc)},status=503)
    except Exception:
        return JsonResponse({'xato': 'Windows printerlari ro‘yxatini olib bo‘lmadi.'}, status=503)
    if printer not in {p['nom'] for p in rows}:
        return JsonResponse({'xato': 'Tanlangan printer topilmadi.'}, status=400)
    if terminal:
        from sotuv.models import ChekVazifa
        data=payload(product,printer,size,copies);data['kind']='etiketka'
        job,created=ChekVazifa.objects.get_or_create(request_key=token,defaults={'terminal':terminal,'malumot':data})
        if job.terminal_id!=terminal.pk:
            return JsonResponse({'xato':'Boshqa kassa vazifasi.'},status=403)
        return JsonResponse({'id':token},status=202)
    path = folder() / (token + '.json')
    if path.exists():
        current = json.loads(path.read_text(encoding='ascii'))
        if current['user'] != request.user.pk:
            return JsonResponse({'xato': 'Boshqa kassa vazifasi.'}, status=403)
        return JsonResponse({'id': token}, status=202)
    try:
        initial ={'user': request.user.pk, 'mahsulot': product.pk, 'holat': 'yuborilmoqda',
                   'xabar': 'Yorliq printerga yuborilmoqda…'}
        # Same click/request ID can only launch one Windows print job.
        try:
            with path.open('x', encoding='ascii') as stream:
                json.dump(initial, stream, ensure_ascii=True)
        except FileExistsError:
            return JsonResponse({'id': token}, status=202)
        save(path.with_suffix('.data.json'), payload(product, printer, size, copies))
        threading.Thread(target=work, args=(path, initial), daemon=True).start()
        return JsonResponse({'id': token}, status=202)
    except Exception:
        return JsonResponse({'xato': 'Chop etish boshlanmadi. Avval vazifa holatini tekshiring.'}, status=503)


@require_GET
@never_cache
def holat(request, token):
    from sotuv.models import ChekVazifa
    job=ChekVazifa.objects.filter(request_key=token).first()
    if job:
        if job.terminal.kassir_id!=request.user.pk:
            return JsonResponse({'xato':'Boshqa kassa vazifasi.'},status=403)
        status={'tayyor':'yuborildi','xato':'xato'}.get(job.holat,'yuborilmoqda')
        message=job.xato if status=='xato' else ('Yorliq kassa printeri navbatiga yuborildi. Qog‘ozni tekshiring.' if status=='yuborildi' else 'Kassa yordamchisi yorliqni yubormoqda…')
        return JsonResponse({'holat':status,'xabar':message})
    path = folder() / (str(token) + '.json')
    if not path.exists():
        return JsonResponse({'xato': 'Chop vazifasi topilmadi.'}, status=404)
    data = json.loads(path.read_text(encoding='ascii'))
    if data['user'] != request.user.pk:
        return JsonResponse({'xato': 'Boshqa kassa vazifasi.'}, status=403)
    return JsonResponse({'holat': data['holat'], 'xabar': data['xabar']})
