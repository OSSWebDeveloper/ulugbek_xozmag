"""Windows serveriga hozir ulangan tashqi qurilmalar (faqat o'qish)."""
import base64
import json
import logging
import os
import re
import subprocess
import threading
import time

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)
_lock = threading.Lock()
_cached = None
_expires = 0

# PresentOnly eski, uzib qo'yilgan qurilmalarni ro'yxatga qo'shmaydi.
# https://learn.microsoft.com/powershell/module/pnpdevice/get-pnpdevice
_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$devices = @(Get-PnpDevice -PresentOnly | Select-Object Class,FriendlyName,InstanceId,Status)
$usb = @($devices | Where-Object { $_.InstanceId -like 'USB\*' })
$descriptions = @{}
if ($usb.Count -gt 0) {
    Get-PnpDeviceProperty -InstanceId $usb.InstanceId -KeyName 'DEVPKEY_Device_BusReportedDeviceDesc' -ErrorAction SilentlyContinue | ForEach-Object {
        $descriptions[$_.InstanceId] = [string]$_.Data
    }
}
foreach ($device in $devices) {
    $device | Add-Member -NotePropertyName BusDescription -NotePropertyValue $descriptions[$device.InstanceId]
}
ConvertTo-Json -InputObject $devices -Depth 3 -Compress
"""


def sarala(rows):
    """Klaviatura/sichqoncha va ichki tizim qismlarini chiqarib tashlaydi.

    Nomi aniq skaner/tarozi bo'lsa Keyboard sinfida ham ko'rsatiladi.
    Oddiy HID nomidan qurilma vazifasi taxmin qilinmaydi.
    """
    result = {}
    for row in rows:
        ident = str(row.get('InstanceId') or '')
        name = str(row.get('BusDescription') or row.get('FriendlyName') or 'Noma’lum qurilma')
        cls = str(row.get('Class') or '')
        text = name.casefold()
        scanner = bool(re.search(r'barcode|bar.?code|scanner|сканер|skaner|honeywell|datalogic|symbol', text))
        scale = bool(re.search(r'\bscale\b|weigh|tarozi|весы|масса-к', text))
        if not ident:
            continue
        if not (scanner or scale):
            if cls.casefold() in {'keyboard', 'mouse'}:
                continue
            if re.search(r'keyboard|mouse|touchpad|klaviatura|sichqon|клавиатур|мыш', text):
                continue
            # HID klaviatura/sichqonchaning qo'shimcha interfeyslari ham yashiriladi.
            if cls.casefold() == 'hidclass':
                continue
            if re.search(r'root hub|usb hub|host controller|composite device|usb input device|корневой usb|usb-концентратор|составное usb|usb-устройство ввода', text):
                continue
            if cls.casefold() == 'printqueue' and (ident.upper().endswith('PRINTQUEUES') or re.search(r'\bpdf\b|xps', text)):
                continue
            external = ident.upper().startswith(('USB\\', 'USBSTOR\\', 'BTHENUM\\', 'BTHLEDEVICE\\'))
            peripheral = cls.casefold() in {'ports', 'printer', 'printqueue', 'image', 'camera', 'wpd', 'smartcardreader'}
            if not external and not peripheral:
                continue
            if cls.casefold() in {'system', 'processor', 'softwaredevice', 'volume', 'computer'}:
                continue
        kind = ('Shtrix kod skaneri' if scanner else 'Elektron tarozi' if scale else
                'COM / LPT port' if cls.casefold() == 'ports' else
                'Printer' if cls.casefold() in {'printer', 'printqueue'} else
                'Kamera / tasvir qurilmasi' if cls.casefold() in {'camera', 'image'} else
                'Boshqa tashqi qurilma')
        port = re.search(r'\b(?:COM|LPT)\d+\b', name, re.I)
        status = str(row.get('Status') or 'Unknown')
        result[ident] = dict(id=ident, nom=name, tur=kind, sinf=cls or 'Noma’lum',
                             port=port.group(0).upper() if port else '',
                             holat='Windows aniqlagan' if status.upper() == 'OK' else 'Windows: tekshirish kerak',
                             tayyor=status.upper() == 'OK')
    return sorted(result.values(), key=lambda d: (d['tur'], d['nom'], d['id']))


def aniqlash():
    if os.name != 'nt':
        raise RuntimeError('Qurilmalarni aniqlash Windows kompyuterida ishlaydi.')
    encoded = base64.b64encode(_SCRIPT.encode('utf-16-le')).decode('ascii')
    system = os.environ.get('SystemRoot', r'C:\Windows')
    executable = os.path.join(system, 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
    proc = subprocess.run(
        [executable, '-NoLogo', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded],
        capture_output=True, encoding='utf-8', errors='replace', timeout=15,
        creationflags=subprocess.CREATE_NO_WINDOW, check=True,
    )
    rows = json.loads(proc.stdout.lstrip('\ufeff').strip())
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError('Windows javobi ro‘yxat emas.')
    return sarala(rows)


@login_required
@require_GET
def sahifa(request):
    from sotuv.models import KassaTerminal
    return render(request, 'qurilmalar.html', {'terminal': KassaTerminal.objects.filter(kassir=request.user).first()})


@login_required
@require_GET
@never_cache
def royxat(request):
    global _cached, _expires
    from sotuv.models import KassaTerminal
    from sotuv.chek import mahalliymi
    terminal = KassaTerminal.objects.filter(kassir=request.user).first()
    if terminal:
        if not terminal.oxirgi_aloqa or (timezone.now() - terminal.oxirgi_aloqa).total_seconds() > 60:
            return JsonResponse({'xato': 'Shu kassaning USB yordamchisi ulanmagan. Quyidagi paketni shu kompyuterda o‘rnating yoki BizaroPOS Kassa yarligini oching.'}, status=503)
        return JsonResponse({'qurilmalar': terminal.qurilmalar, 'vaqt': terminal.oxirgi_aloqa.isoformat()})
    if not mahalliymi(request):
        return JsonResponse({'xato': 'USB qurilmalarni ko‘rish uchun shu kassada yordamchini o‘rnating.'}, status=503)
    try:
        # Bir nechta ochiq brauzer PowerShell'ni bir vaqtda ishga tushirmasin.
        with _lock:
            if _cached is None or time.monotonic() >= _expires:
                _cached = {'qurilmalar': aniqlash(), 'vaqt': timezone.now().isoformat()}
                _expires = time.monotonic() + 5
            return JsonResponse(_cached)
    except RuntimeError as exc:
        return JsonResponse({'xato': str(exc)}, status=503)
    except (OSError, subprocess.SubprocessError, ValueError):
        logger.exception('Qurilmalarni aniqlab bo‘lmadi')
        return JsonResponse({'xato': 'Windows qurilmalar ro‘yxatini olib bo‘lmadi. Qayta yangilang.'}, status=503)
