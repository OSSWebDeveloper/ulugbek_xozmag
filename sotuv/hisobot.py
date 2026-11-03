"""Faqat server kompyuterida ko'rinadigan kassa savdolari hisoboti."""
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Count, F, Sum
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone

from sotuv.chek import mahalliymi
from sotuv.models import Sotuv

NOL = Decimal("0")


def _sana(matn, standart):
    try:
        return datetime.strptime(matn, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return standart


def sahifa(request):
    if not mahalliymi(request):
        return HttpResponseForbidden("Hisobot faqat server kompyuterida ochiladi.")

    bugun = timezone.localdate()
    boshlanish = _sana(request.GET.get("dan"), bugun)
    tugash = _sana(request.GET.get("gacha"), bugun)
    if tugash < boshlanish:
        boshlanish, tugash = tugash, boshlanish

    boshlanish_vaqti = timezone.make_aware(datetime.combine(boshlanish, time.min))
    tugash_vaqti = timezone.make_aware(datetime.combine(tugash + timedelta(days=1), time.min))
    sotuvlar = (Sotuv.objects.filter(
        yakunlangan=True, bekor_qilingan=False,
        sana__gte=boshlanish_vaqti, sana__lt=tugash_vaqti,
    ).select_related("kassir").order_by("-sana", "-pk"))

    kassir = request.GET.get("kassir", "").strip()
    if kassir.isdigit():
        sotuvlar = sotuvlar.filter(kassir_id=int(kassir))

    # Qarz undiruvi kassa sotuviga qo'shilmaydi. Qaytarilgan pul ayriladi.
    # So'm va dollar hech qachon birlashtirilmaydi.
    hisob = sotuvlar.aggregate(
        som=Sum(F("jami") - F("qaytarilgan_summa")),
        dollar=Sum(F("jami_dollar") - F("qaytarilgan_summa_dollar")),
    )
    kassalar = list(
        sotuvlar.values("kassir_id", "kassir__username")
        .annotate(
            soni=Count("pk"),
            som=Sum(F("jami") - F("qaytarilgan_summa")),
            dollar=Sum(F("jami_dollar") - F("qaytarilgan_summa_dollar")),
        )
        .order_by("kassir__username")
    )
    from django.contrib.auth import get_user_model
    kassirlar = get_user_model().objects.filter(
        pk__in=Sotuv.objects.filter(yakunlangan=True).values("kassir_id")
    ).order_by("username")

    return render(request, "sotuv/hisobot.html", {
        "dan": boshlanish, "gacha": tugash, "kassir": kassir,
        "kassirlar": kassirlar, "kassalar": kassalar,
        "sotuvlar": sotuvlar[:500], "soni": sotuvlar.count(),
        "jami_som": hisob["som"] or NOL,
        "jami_dollar": hisob["dollar"] or NOL,
    })
