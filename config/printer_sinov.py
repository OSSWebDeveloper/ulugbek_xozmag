"""Non-financial receipt tests, routed only to this cashier's printer."""
import subprocess
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.cache import never_cache
from sotuv.models import KassaTerminal, ChekVazifa
from sotuv.chek import mahalliymi, sinov_malumot, chop_malumot
from django.conf import settings


@require_GET
@never_cache
@xframe_options_sameorigin
def bosma(request):
    """Sinov chekining qog'ozi — brauzer chop oynasi uchun (yordamchisiz qurilma)."""
    return render(request, 'sotuv/chek_bosma.html', {
        'sarlavha': 'Printer sinovi',
        'data': sinov_malumot(request.user, 'shu kompyuterning standart printeri')})


@require_POST
def chop(request):
    terminal = KassaTerminal.objects.filter(kassir=request.user).first()
    online = bool(terminal and terminal.printer and terminal.oxirgi_aloqa
                  and (timezone.now() - terminal.oxirgi_aloqa).total_seconds() < 60)
    if mahalliymi(request) and not online:
        try:
            chop_malumot(sinov_malumot(request.user, settings.CHEK_PRINTER))
        except (OSError, RuntimeError, subprocess.SubprocessError):
            return JsonResponse({'xato': 'Sinov cheki yuborilmadi. Printer ulanishini tekshiring.'}, status=503)
        return JsonResponse({'xabar': 'Sinov Windows printer navbatiga yuborildi. Qog‘oz chiqqanini tekshiring.'})
    if not online:
        # Yordamchisiz qurilma: sinov cheki shu brauzerning chop oynasiga chiqadi.
        return JsonResponse({'xabar': 'Sinov cheki shu kompyuterning printeriga chiqarilmoqda. Chop oynasida printerni tasdiqlang.',
                             'bosma': reverse('printer_sinov_bosma')})
    with transaction.atomic():
        terminal = KassaTerminal.objects.select_for_update().get(pk=terminal.pk)
        # Repeated clicks cannot enqueue another still-pending test.
        job = terminal.cheklar.filter(sotuv__isnull=True,
            holat__in=['kutilmoqda', 'yuborildi']).order_by('-pk').first()
        if not job:
            job = ChekVazifa.objects.create(terminal=terminal,
                malumot=sinov_malumot(request.user, terminal.printer))
    return JsonResponse({'xabar': 'Sinov shu kassa printerining navbatiga qo‘yildi.',
        'url': reverse('printer_sinov_holat', args=[job.pk])}, status=202)


@require_GET
@never_cache
def holat(request, pk):
    job = get_object_or_404(ChekVazifa, pk=pk, sotuv__isnull=True,
                           terminal__kassir=request.user)
    messages = {'kutilmoqda': 'Sinov printer navbatida…',
        'yuborildi': 'Yordamchi sinov chekini printerga yuboryapti…',
        'tayyor': 'Sinov Windows printer navbatiga yuborildi. Qog‘oz chiqqanini tekshiring.',
        'xato': job.xato or 'Printerga yuborilmadi. USB ulanishini tekshiring.'}
    return JsonResponse({'holat': job.holat, 'xabar': messages.get(job.holat, job.holat)})
