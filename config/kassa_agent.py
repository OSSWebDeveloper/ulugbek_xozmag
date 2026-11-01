"""Account-bound USB printer queue; no device API is exposed to the LAN."""
import hashlib
import hmac
import inspect
import io
import json
from pathlib import Path
import secrets
import zipfile

from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from sotuv.models import KassaTerminal, ChekVazifa


def digest(token):
    return hashlib.sha256(token.encode('ascii')).hexdigest()


@require_POST
def paket(request):
    """Logged-in cashier downloads only their own terminal credentials."""
    root = Path(settings.BASE_DIR)
    runtime = root / 'qurilma_drivers/kassa/python.zip'
    if not runtime.exists():
        return HttpResponse('Kassa yordamchisi runtime fayli serverda topilmadi.', status=503)
    from . import qurilmalar
    token = secrets.token_hex(32)
    with transaction.atomic():
        terminal, _ = KassaTerminal.objects.get_or_create(kassir=request.user)
        terminal.kalit_hash = digest(token)
        terminal.oxirgi_aloqa = None
        terminal.save(update_fields=['kalit_hash', 'oxirgi_aloqa'])
    data = {'url': request.build_absolute_uri('/').rstrip('/'), 'token': token,
            'kassir': request.user.username, 'printer': ''}
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('kassa.json', json.dumps(data, ensure_ascii=True))
        archive.write(runtime, 'python.zip')
        for file in ('agent.py', 'ORNATISH.ps1', 'ORNATISH.bat', 'FOYDALANISH.txt'):
            archive.write(root / 'kassa_yordamchi' / file, file)
        archive.write(root / 'sotuv/chek_print.ps1', 'chek_print.ps1')
        archive.write(root / 'static/img/bizaropos.ico', 'bizaropos.ico')
        code = 'import os, re, json, base64, subprocess\n_SCRIPT = ' + repr(qurilmalar._SCRIPT) + '\n'
        code += inspect.getsource(qurilmalar.sarala) + '\n' + inspect.getsource(qurilmalar.aniqlash)
        archive.writestr('local_devices.py', code)
    response = HttpResponse(output.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="BizaroPOS-kassa.zip"'
    response['Cache-Control'] = 'no-store'
    return response


@csrf_exempt
@login_not_required
@require_POST
def almashish(request):
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer ') or len(auth) != 71:
        return JsonResponse({'xato': 'Kalit kerak.'}, status=401)
    try:
        value = digest(auth[7:])
    except UnicodeError:
        return JsonResponse({'xato': 'Kalit noto‘g‘ri.'}, status=401)
    terminal = KassaTerminal.objects.filter(kalit_hash=value, kassir__is_active=True).first()
    if not terminal or not hmac.compare_digest(terminal.kalit_hash, value):
        return JsonResponse({'xato': 'Kalit bekor qilingan. Paketni qayta yuklang.'}, status=401)
    if len(request.body) > 262144:
        return JsonResponse({'xato': 'Javob juda katta.'}, status=400)
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            raise ValueError
    except (ValueError, UnicodeError):
        return JsonResponse({'xato': 'JSON kerak.'}, status=400)
    with transaction.atomic():
        terminal = KassaTerminal.objects.select_for_update().get(pk=terminal.pk)
        # A package download may revoke a token during an outstanding request.
        if not hmac.compare_digest(terminal.kalit_hash, value):
            return JsonResponse({'xato': 'Kalit bekor qilingan.'}, status=401)
        terminal.oxirgi_aloqa = timezone.now()
        terminal.nom = str(data.get('nom', ''))[:100]
        terminal.printer = str(data.get('printer', ''))[:200]
        if isinstance(data.get('qurilmalar'), list):
            terminal.qurilmalar = data['qurilmalar'][:100]
        terminal.save()
        if data.get('ack'):
            ack = data['ack']
            if not isinstance(ack, dict):
                return JsonResponse({'xato': 'ACK noto‘g‘ri.'}, status=400)
            job = get_object_or_404(ChekVazifa, pk=ack.get('id'), terminal=terminal)
            if job.holat == 'yuborildi' and hmac.compare_digest(job.claim, str(ack.get('claim', ''))):
                job.holat = 'tayyor' if ack.get('ok') is True else 'xato'
                job.xato = str(ack.get('xato', ''))[:300]
                job.save(update_fields=['holat', 'xato'])
        result = {'ok': True, 'vazifa': None}
        if data.get('tayyor') is True and terminal.printer:
            job = terminal.cheklar.filter(holat='kutilmoqda').order_by('pk').first()
            if job:
                job.holat = 'yuborildi'
                job.claim = secrets.token_hex(16)
                job.save(update_fields=['holat', 'claim'])
                result['vazifa'] = {'id': job.pk, 'claim': job.claim, 'data': job.malumot}
        return JsonResponse(result)
