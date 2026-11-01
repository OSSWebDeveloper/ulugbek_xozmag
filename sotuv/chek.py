"""Savdo cheki va uning qaytarish uchun ajratilgan Code 128 kodi."""
import json
import os
import subprocess
import uuid
from pathlib import Path

from django.conf import settings
from django.utils import timezone
from ombor.kod import nazorat_raqami, tozala
from ombor.shtrix import chiziqlar, svg
from qarz.templatetags.xozmag import pul, tekis

PREFIX = '88'


def kod(raqam):
    if not 1 <= int(raqam) <= 999999999:
        raise ValueError('Chek raqami shtrixga sig‘madi.')
    asos = PREFIX + f'{int(raqam):09d}'
    return asos + str(nazorat_raqami(asos))


def och(matn):
    text = tozala(matn)
    if len(text) != 12 or not text.isdigit() or not text.startswith(PREFIX):
        return None
    if text[-1] != str(nazorat_raqami(text[:-1])):
        return None
    return int(text[2:11]) or None


def malumot(s):
    debt = s.qarz_hujjati
    total = s.jami + (debt.jami if debt else 0)
    dollars = s.jami_dollar + (debt.jami_dollar if debt else 0)
    lines = [f'Chek #{s.pk}', timezone.localtime(s.sana).strftime('%d.%m.%Y %H:%M'), '']
    for row in s.qatorlar.all():
        lines.extend([row.mahsulot_nomi, f'{tekis(row.miqdor)} {row.birlik}'])
    lines += ['', 'JAMI: ' + pul(total) + " so'm"]
    if dollars:
        lines.append('JAMI ($): ' + tekis(dollars))
    lines.append('Naqd: ' + pul(s.jami) + " so'm")
    if s.jami_dollar:
        lines.append('Naqd ($): ' + tekis(s.jami_dollar))
    if debt:
        lines.append('Qarz: ' + pul(debt.jami) + " so'm")
        if debt.jami_dollar:
            lines.append('Qarz ($): ' + tekis(debt.jami_dollar))
    if s.qaytarilganmi:
        lines.append('Qaytarishlar mavjud; tarix bazada saqlanadi.')
    barcode = kod(s.pk)
    bars, width = chiziqlar(barcode)
    return {'nom': "ULUG'BEK XOZMAG", 'lines': lines, 'barcode': barcode,
            'bars': bars, 'width': width, 'printer': settings.CHEK_PRINTER}


def chop_et(s):
    if not s.yakunlangan or s.bekor_qilingan:
        raise ValueError('Faqat yakunlangan savdo cheki chiqariladi.')
    if os.name != 'nt':
        raise RuntimeError('Avtomatik chop etish Windows serverida ishlaydi.')
    folder = Path(settings.MALUMOT_DIR) / 'qurilmalar_data' / 'cheklar'
    folder.mkdir(parents=True, exist_ok=True)
    datafile = folder / f'{s.pk}_{uuid.uuid4().hex}.json'
    datafile.write_text(json.dumps(malumot(s), ensure_ascii=True), encoding='ascii')
    exe = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    result = subprocess.run([str(exe), '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                             '-File', str(Path(__file__).with_name('chek_print.ps1')),
                             '-DataFile', str(datafile)], capture_output=True,
                            encoding='utf-8', errors='replace', timeout=30,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise RuntimeError('Printerga yuborilmadi. Printer ulanishini tekshirib qayta chiqaring.')


def avtomatik(request, s):
    from django.contrib import messages
    if not settings.CHEK_AUTO_PRINT:
        return
    try:
        yubor(request, s)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        messages.warning(request, f'Savdo saqlandi, lekin chek #{s.pk} printerga yuborilmadi. Sotuvlar ro‘yxatidagi «Chek» orqali qayta chiqaring.')


def mahalliymi(request):
    from config.tarmoq import ip_manzillar
    return request.META.get('REMOTE_ADDR', '') in {'127.0.0.1', '127.0.0.55', '::1', *ip_manzillar()}


def yubor(request, s, qayta=False):
    """USB chekni aynan so'rov yuborgan kassaning printeriga yo'naltiradi."""
    from django.contrib import messages
    from django.db import transaction
    from .models import KassaTerminal, ChekVazifa
    terminal = KassaTerminal.objects.filter(kassir=request.user).first()
    online = bool(terminal and terminal.printer and terminal.oxirgi_aloqa
                  and (timezone.now() - terminal.oxirgi_aloqa).total_seconds() < 60)
    if mahalliymi(request) and not online:
        # Downloading an unused helper package must not disable the main USB
        # printer. Claim an existing queued receipt before direct printing so a
        # helper reconnecting later cannot print it again.
        with transaction.atomic():
            job = ChekVazifa.objects.select_for_update().filter(sotuv=s).first()
            if job and job.holat == 'yuborildi' and not (qayta and request.POST.get('chop_tasdiq') == 'ha'):
                messages.warning(request, 'Chek yuborilgan, lekin yakuniy holati noma’lum. Qog‘ozni tekshiring.')
                return
            if job and job.holat == 'tayyor' and not qayta:
                return
            if job:
                job.holat = 'yuborildi'
                job.claim = uuid.uuid4().hex
                job.save(update_fields=['holat', 'claim'])
        try:
            chop_et(s)
        except Exception:
            if job:
                ChekVazifa.objects.filter(pk=job.pk).update(holat='xato', xato='Asosiy printerga yuborilmadi.')
            raise
        if job:
            ChekVazifa.objects.filter(pk=job.pk).update(holat='tayyor', xato='')
        messages.success(request, f'Chek #{s.pk} asosiy kassa printeriga yuborildi.')
        return
    if terminal is None:
        terminal = KassaTerminal.objects.create(kassir=request.user)
    with transaction.atomic():
        job, created = ChekVazifa.objects.get_or_create(sotuv=s, defaults={
            'terminal': terminal, 'malumot': malumot(s)})
        if qayta and not created:
            # Explicit retry only. Never duplicate a job still being sent.
            if job.holat == 'kutilmoqda':
                messages.warning(request, 'Chek hali navbatda. USB yordamchisini oching.')
                return
            if job.holat == 'yuborildi' and request.POST.get('chop_tasdiq') != 'ha':
                messages.warning(request, 'Chop holati noma’lum. Qog‘ozni tekshiring va qayta chiqarishni alohida tasdiqlang.')
                return
            job.terminal = terminal
            job.malumot = malumot(s)
            job.holat = 'kutilmoqda'
            job.claim = ''
            job.xato = ''
            job.save()
    if terminal.oxirgi_aloqa and (timezone.now() - terminal.oxirgi_aloqa).total_seconds() < 60:
        messages.success(request, f'Chek #{s.pk} shu kassa printerining navbatiga qo‘yildi.')
    else:
        messages.warning(request, f'Savdo saqlandi. Chek #{s.pk} navbatda; Qurilmalar bo‘limidan shu kassada USB yordamchisini o‘rnating yoki oching.')


def svg_kod(s):
    return svg(kod(s.pk))
