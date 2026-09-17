"""Naqd sotuv ko'rinishlari."""
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from ombor.models import Mahsulot
from ombor.xizmat import OmborXatosi, ayir, qaytar, songa

from .models import Sotuv, SotuvQator


def sotuv_boshlash(request):
    """Yangi (yoki tugallanmagan) sotuv chekini ochadi."""
    sotuv = Sotuv.objects.filter(yakunlangan=False).first()
    if sotuv is None:
        sotuv = Sotuv.objects.create()
    return redirect("sotuv:tahrir", pk=sotuv.pk)


def tahrir(request, pk):
    """Sotuv ekrani (kassa ko'rinishi)."""
    sotuv = get_object_or_404(Sotuv, pk=pk)
    return render(request, "sotuv/tahrir.html", {
        "sotuv": sotuv,
        "qatorlar": sotuv.qatorlar.all(),
        "mahsulotlar": Mahsulot.objects.filter(faol=True),
        "qator_manzili": reverse("sotuv:qator_qoshish", args=[sotuv.pk]),
    })


def qator_qoshish(request, pk):
    """Sotuvga tovar qo'shadi va ombordan ayiradi."""
    sotuv = get_object_or_404(Sotuv, pk=pk)
    if request.method != "POST":
        return redirect("sotuv:tahrir", pk=sotuv.pk)

    mahsulot = get_object_or_404(Mahsulot, pk=request.POST.get("mahsulot"))
    miqdor, xato = songa(request.POST.get("miqdor"), "Miqdor")
    if xato:
        messages.error(request, xato)
        return redirect("sotuv:tahrir", pk=sotuv.pk)

    narx, xato = songa(request.POST.get("narx") or mahsulot.narx, "Narx")
    if xato:
        messages.error(request, xato)
        return redirect("sotuv:tahrir", pk=sotuv.pk)

    try:
        ayir(mahsulot.pk, miqdor, f"Sotuv #{sotuv.pk}")
    except OmborXatosi as xato:
        messages.error(request, str(xato))
        return redirect("sotuv:tahrir", pk=sotuv.pk)

    SotuvQator.objects.create(sotuv=sotuv, mahsulot=mahsulot, miqdor=miqdor, narx=narx)
    return redirect("sotuv:tahrir", pk=sotuv.pk)


def qator_ochirish(request, pk):
    """Qatorni o'chiradi va tovarni omborga qaytaradi."""
    qator = get_object_or_404(SotuvQator.objects.select_related("sotuv"), pk=pk)
    sotuv_pk = qator.sotuv_id
    if request.method == "POST":
        qaytar(qator.mahsulot_id, qator.miqdor, f"Sotuv #{sotuv_pk} dan qaytarildi")
        qator.delete()
        messages.success(request, "Qator o'chirildi, tovar omborga qaytdi.")
    return redirect("sotuv:tahrir", pk=sotuv_pk)


def yakunlash(request, pk):
    """Sotuvni yopadi."""
    sotuv = get_object_or_404(Sotuv, pk=pk)
    if request.method != "POST":
        return redirect("sotuv:tahrir", pk=sotuv.pk)

    if sotuv.qatorlar_soni == 0:
        sotuv.delete()
        messages.info(request, "Bo'sh sotuv bekor qilindi.")
        return redirect("qarz:boshlash")

    try:
        tolandi = Decimal(str(request.POST.get("tolandi", "0")).replace(",", ".").strip() or "0")
    except (InvalidOperation, AttributeError, TypeError):
        tolandi = Decimal("0")

    # To'langan pul kiritilmagan bo'lsa, tayyor summa to'langan deb hisoblanadi
    sotuv.tolandi = tolandi if tolandi > 0 else sotuv.jami
    sotuv.yakunlangan = True
    sotuv.save(update_fields=["tolandi", "yakunlangan"])

    if sotuv.qaytim > 0:
        messages.success(request, f"Sotuv yakunlandi. Qaytim: {sotuv.qaytim:,.0f} so'm."
                         .replace(",", " "))
    else:
        messages.success(request, "Sotuv yakunlandi.")
    return redirect("sotuv:royxat")


def bekor(request, pk):
    """Tugallanmagan sotuvni butunlay bekor qiladi, tovarlarni omborga qaytaradi."""
    sotuv = get_object_or_404(Sotuv, pk=pk)
    if request.method == "POST":
        for qator in sotuv.qatorlar.all():
            qaytar(qator.mahsulot_id, qator.miqdor, f"Sotuv #{sotuv.pk} bekor qilindi")
        sotuv.delete()
        messages.info(request, "Sotuv bekor qilindi, tovarlar omborga qaytdi.")
    return redirect("qarz:boshlash")


def royxat(request):
    """Sotuvlar ro'yxati va kunlik tushum."""
    bugun = timezone.localtime().date()
    kun = request.GET.get("kun", "")
    try:
        sana = timezone.datetime.strptime(kun, "%Y-%m-%d").date() if kun else bugun
    except ValueError:
        sana = bugun

    boshi = timezone.make_aware(timezone.datetime.combine(sana, timezone.datetime.min.time()))
    sotuvlar = (Sotuv.objects
                .filter(yakunlangan=True, sana__gte=boshi, sana__lt=boshi + timedelta(days=1))
                .prefetch_related("qatorlar"))

    jami = SotuvQator.objects.filter(sotuv__in=sotuvlar).aggregate(s=Sum("summa"))["s"] or Decimal("0")

    return render(request, "sotuv/royxat.html", {
        "sotuvlar": sotuvlar,
        "sana": sana,
        "bugunmi": sana == bugun,
        "jami": jami,
        "soni": sotuvlar.count(),
    })
