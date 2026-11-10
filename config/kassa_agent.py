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
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from sotuv.models import KassaTerminal, ChekVazifa


ESKIRGAN = 'O‘z vaqtida chiqmadi: printer ulanmagan edi. Kerak bo‘lsa qayta chiqaring.'


def digest(token):
    return hashlib.sha256(token.encode('ascii')).hexdigest()


def key_path(user_id):
    return Path(settings.MALUMOT_DIR)/'qurilmalar_data/kassa_keys'/f'{user_id}.json'


@require_POST
def paket(request):
    """Logged-in cashier downloads only their own terminal credentials."""
    cashier=request.user
    if request.POST.get('kassa2') == '1':
        from sotuv.chek import mahalliymi
        if not mahalliymi(request):
            return HttpResponseForbidden('Faqat server kompyuterida.')
        from django.contrib.auth import get_user_model
        from qarz.management.commands.standart_akkauntlar import KASSA_GURUH
        cashier=get_object_or_404(get_user_model(),groups__name=KASSA_GURUH,is_active=True)
    root = Path(settings.BASE_DIR)
    runtime = root / 'qurilma_drivers/kassa/python.zip'
    if not runtime.exists():
        return HttpResponse('Kassa yordamchisi runtime fayli serverda topilmadi.', status=503)
    from . import qurilmalar
    token = secrets.token_hex(32)
    with transaction.atomic():
        terminal, _ = KassaTerminal.objects.get_or_create(kassir=cashier)
        keyfile=key_path(cashier.pk)
        try:
            existing=json.loads(keyfile.read_text(encoding='utf-8'))['token']
        except (OSError,ValueError,KeyError):
            existing=''
        if existing and hmac.compare_digest(digest(existing),terminal.kalit_hash):
            token=existing
        else:
            terminal.kalit_hash = digest(token)
            terminal.oxirgi_aloqa = None
            terminal.save(update_fields=['kalit_hash', 'oxirgi_aloqa'])
            keyfile.parent.mkdir(parents=True,exist_ok=True)
            temp=keyfile.with_suffix('.tmp')
            temp.write_text(json.dumps({'token':token}),encoding='utf-8')
            temp.replace(keyfile)
    from .tarmoq import doimiy_manzil
    data = {'url': doimiy_manzil(request.get_port(), request.scheme), 'token': token,
            'kassir': cashier.username, 'printer': ''}
    from .kassalar import config
    from qarz.management.commands.standart_akkauntlar import KASSA_GURUH
    data['client_ip']=config()['client_ip'] if cashier.groups.filter(name=KASSA_GURUH).exists() else ''
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('kassa.json', json.dumps(data, ensure_ascii=True))
        archive.write(runtime, 'python.zip')
        for file in ('agent.py', 'tray.py', 'updater.py', 'ORNATISH.ps1', 'ORNATISH.bat', 'FOYDALANISH.txt'):
            archive.write(root / 'kassa_yordamchi' / file, file)
        archive.write(root / 'sotuv/chek_print.ps1', 'chek_print.ps1')
        archive.write(root / 'config/kassa_ip.ps1', 'kassa_ip.ps1')
        archive.write(root / 'config/etiketka_print.ps1', 'etiketka_print.ps1')
        archive.write(root / 'static/img/bizaropos.ico', 'bizaropos.ico')
        archive.write(root / 'versiya.txt', 'versiya.txt')
        for dep in (root/'qurilma_drivers/kassa/tray_deps').rglob('*'):
            if dep.is_file() and '__pycache__' not in dep.parts:
                archive.write(dep,'tray_deps/'+dep.relative_to(root/'qurilma_drivers/kassa/tray_deps').as_posix())
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
        if isinstance(data.get('printerlar'), list):
            terminal.printerlar = [p for p in data['printerlar'][:50] if isinstance(p, dict) and isinstance(p.get('nom'), str)]
            terminal.etiketka_tayyor = data.get('etiketka') is True
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
        # Printer yo'q paytda yig'ilib qolgan vazifalar printer ulanishi bilan
        # ketma-ket chiqib ketmasin: eskirgani o'zi chop etilmaydi.
        from datetime import timedelta
        chegara = timezone.now() - timedelta(seconds=settings.CHEK_NAVBAT_MUDDATI)
        terminal.cheklar.filter(holat='kutilmoqda', yaratilgan__lt=chegara).update(
            holat='xato', xato=ESKIRGAN)
        result = {'ok': True, 'vazifa': None}
        if data.get('tayyor') is True and (terminal.printer or terminal.etiketka_tayyor):
            jobs = terminal.cheklar.filter(holat='kutilmoqda')
            if data.get('etiketka') is not True:
                from django.db.models import Q
                jobs = jobs.filter(Q(malumot__kind__isnull=True) | ~Q(malumot__kind='etiketka'))
            if not terminal.printer:
                jobs = jobs.filter(malumot__kind='etiketka')
            job = jobs.order_by('pk').first()
            if job:
                job.holat = 'yuborildi'
                job.claim = secrets.token_hex(16)
                job.save(update_fields=['holat', 'claim'])
                result['vazifa'] = {'id': job.pk, 'claim': job.claim, 'data': job.malumot}
        return JsonResponse(result)

@csrf_exempt
@login_not_required
@require_POST
def yangila(request):
    """Code-only update; existing terminal token and configuration are preserved."""
    auth=request.headers.get('Authorization','')
    try:
        terminal=KassaTerminal.objects.filter(kalit_hash=digest(auth[7:]),kassir__is_active=True).first() if auth.startswith('Bearer ') and len(auth)==71 else None
    except UnicodeError:
        terminal=None
    if not terminal:return JsonResponse({'xato':'Yordamchi kaliti noto‘g‘ri.'},status=401)
    import hashlib
    from . import qurilmalar
    root=Path(settings.BASE_DIR)
    files={}
    for name in ('agent.py','tray.py','updater.py'):
        files[name]=(root/'kassa_yordamchi'/name).read_bytes()
    for name,source in [('chek_print.ps1','sotuv/chek_print.ps1'),('etiketka_print.ps1','config/etiketka_print.ps1'),('bizaropos.ico','static/img/bizaropos.ico'),('versiya.txt','versiya.txt')]:
        files[name]=(root/source).read_bytes()
    code='import os, re, json, base64, subprocess\n_SCRIPT = '+repr(qurilmalar._SCRIPT)+'\n'
    code+=inspect.getsource(qurilmalar.sarala)+'\n'+inspect.getsource(qurilmalar.aniqlash)
    files['local_devices.py']=code.encode('utf-8')
    deps=root/'qurilma_drivers/kassa/tray_deps'
    for dep in deps.rglob('*'):
        if dep.is_file() and '__pycache__' not in dep.parts:files['tray_deps/'+dep.relative_to(deps).as_posix()]=dep.read_bytes()
    manifest={'files':{name:hashlib.sha256(data).hexdigest() for name,data in files.items()}}
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in files.items():archive.writestr(name,data)
        archive.writestr('manifest.json',json.dumps(manifest))
    response=HttpResponse(output.getvalue(),content_type='application/zip')
    response['Cache-Control']='no-store'
    return response
