from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_GET, require_POST
from .models import Sotuv
from . import chek


def yopilgan(pk):
    return get_object_or_404(Sotuv.objects.prefetch_related('qatorlar'), pk=pk,
                             yakunlangan=True, bekor_qilingan=False)


@require_GET
def korish(request, pk):
    sale = yopilgan(pk)
    data = chek.malumot(sale)
    return render(request, 'sotuv/chek.html', {'sotuv': sale, 'data': data,
                                             'barcode_svg': chek.svg_kod(sale),
                                             'vazifa': getattr(sale, 'chop_vazifa', None)})


@require_GET
@xframe_options_sameorigin
def bosma(request, pk):
    """Faqat chekning o'zi: yashirin ramkada ochiladi va brauzer chop oynasini chaqiradi."""
    sale = yopilgan(pk)
    return render(request, 'sotuv/chek_bosma.html', {
        'sarlavha': f'Savdo cheki #{sale.pk}', 'data': chek.malumot(sale),
        'barcode_svg': chek.svg_kod(sale)})


@require_POST
def chiqarish(request, pk):
    sale = yopilgan(pk)
    try:
        chek.yubor(request, sale, qayta=True)
    except Exception:
        messages.error(request, 'Printerga yuborilmadi. Ulanishini tekshiring yoki brauzerdan chop eting.')
    if request.POST.get('royxatga') == 'ha':
        from django.utils import timezone
        return redirect(reverse('sotuv:royxat') + '?kun=' + timezone.localtime(sale.sana).date().isoformat())
    return redirect('sotuv:chek', pk=pk)


@require_GET
def qaytarish_cheki(request, pk=None):
    if pk is None and request.GET.get('k'):
        pk = chek.och(request.GET['k'])
        if pk is None:
            messages.error(request, 'Savdo chekining shtrix kodi noto‘g‘ri.')
        else:
            return redirect('sotuv:chek_qaytarish', pk=pk)
    sale = yopilgan(pk) if pk is not None else None
    return render(request, 'sotuv/chek_qaytarish.html', {'sotuv': sale,
                                                       'qatorlar': sale.qatorlar.all() if sale else []})
