"""Naqd sotuv ko'rinishlari."""
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.db.models import F, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from ombor.models import HarakatTuri, Mahsulot
from ombor.xizmat import (OmborXatosi, ayir, oxirgi_kurs, qaytar, qaytarishni_oqi,
                          songa, summalarni_oqi)

from .models import Sotuv, SotuvQator


def sotuv_boshlash(request):
    """Yangi (yoki tugallanmagan) sotuv chekini ochadi."""
    sotuv = Sotuv.objects.filter(yakunlangan=False, bekor_qilingan=False).first()
    if sotuv is None:
        sotuv = Sotuv.objects.create()
    return redirect("sotuv:tahrir", pk=sotuv.pk)


def tahrir(request, pk):
    """Sotuv ekrani (kassa ko'rinishi)."""
    sotuv = get_object_or_404(Sotuv, pk=pk)
    return render(request, "sotuv/tahrir.html", {
        "sotuv": sotuv,
        "qatorlar": sotuv.qatorlar.select_related("mahsulot"),
        "mahsulotlar": Mahsulot.objects.filter(faol=True),
        "qator_manzili": reverse("sotuv:qator_qoshish", args=[sotuv.pk]),
        "yakun_manzili": reverse("sotuv:yakunlash", args=[sotuv.pk]),
        "oxirgi_kurs": oxirgi_kurs(),
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

    try:
        ayir(mahsulot.pk, miqdor, f"Sotuv #{sotuv.pk}")
    except OmborXatosi as xato:
        messages.error(request, str(xato))
        return redirect("sotuv:tahrir", pk=sotuv.pk)

    SotuvQator.objects.create(sotuv=sotuv, mahsulot=mahsulot, miqdor=miqdor)
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
    """Sotuvni yopadi. Chek summasi qo'lda kiritiladi.

    Summa hisoblanmaydi: savdolashib narx o'zgaradi (183 000 -> 180 000),
    shuning uchun kassir kalkulyatordagi sonni o'zi yozadi. So'mlik va
    dollarlik qism alohida yoziladi, qo'shilmaydi.
    """
    sotuv = get_object_or_404(Sotuv, pk=pk)
    if request.method != "POST":
        return redirect("sotuv:tahrir", pk=sotuv.pk)

    if sotuv.qatorlar_soni == 0:
        sotuv.delete()
        messages.info(request, "Bo'sh sotuv bekor qilindi.")
        return redirect("qarz:boshlash")

    jami, jami_dollar, kurs, xato = summalarni_oqi(request.POST)
    if xato:
        messages.error(request, xato)
        return redirect("sotuv:tahrir", pk=sotuv.pk)

    sotuv.jami = jami
    sotuv.jami_dollar = jami_dollar
    sotuv.kurs = kurs
    sotuv.yakunlangan = True
    sotuv.save(update_fields=["jami", "jami_dollar", "kurs", "yakunlangan"])

    messages.success(request, "Sotuv yakunlandi.")
    return redirect("sotuv:royxat")


def bekor(request, pk):
    """Tugallanmagan sotuvni bekor qiladi, tovarlarni omborga qaytaradi.

    Chek o'chirilmaydi — bazada «bekor qilingan» bo'lib qoladi: keyin
    «o'sha kuni nima bo'lgan edi?» degan savolga javob beradigan yozuv kerak.
    Bo'sh chek (bironta tovar qo'shilmagani) esa yozuvga arzimaydi.
    """
    sotuv = get_object_or_404(Sotuv, pk=pk)
    if request.method == "POST":
        if sotuv.qatorlar_soni == 0:
            sotuv.delete()
            messages.info(request, "Bo'sh chek bekor qilindi.")
            return redirect("qarz:boshlash")

        for qator in sotuv.qatorlar.all():
            qaytar(qator.mahsulot_id, qator.qolgan_miqdor,
                   f"Sotuv #{sotuv.pk} bekor qilindi")
        sotuv.bekor_qilingan = True
        sotuv.save(update_fields=["bekor_qilingan"])
        messages.info(request, "Sotuv bekor qilindi, tovarlar omborga qaytdi.")
    return redirect("qarz:boshlash")


def qaytarish(request, pk):
    """Sotilgan tovarni qaytarib olish — qisman ham bo'ladi.

    20 qop sementning 15 tasi ishlatilib 5 tasi qaytsa: 5 qop omborga
    tushadi, qatorda «5 qaytarilgan» bo'lib qoladi, qaytarilgan pul esa
    chek summasidan ayriladi. Chekning o'zi bazada turaveradi.
    """
    qator = get_object_or_404(SotuvQator.objects.select_related("sotuv", "mahsulot"), pk=pk)
    sotuv = qator.sotuv
    orqaga = reverse("sotuv:royxat") + f"?kun={sotuv.sana.date():%Y-%m-%d}"

    if request.method != "POST":
        return render(request, "qaytarish.html", {
            "qator": qator,
            "hujjat": f"chek #{sotuv.pk}",
            "sana": sotuv.sana,
            "jami": sotuv.sof_jami,
            "jami_dollar": sotuv.sof_jami_dollar,
            "orqaga": orqaga,
        })

    miqdor, summa, summa_dollar, xato = qaytarishni_oqi(request.POST, qator)
    if xato:
        messages.error(request, xato)
        return redirect("sotuv:qaytarish", pk=qator.pk)

    if summa > sotuv.sof_jami or summa_dollar > sotuv.sof_jami_dollar:
        messages.error(request, "Qaytarilgan pul chek summasidan ko'p bo'lmasin.")
        return redirect("sotuv:qaytarish", pk=qator.pk)

    qaytar(qator.mahsulot_id, miqdor, f"Chek #{sotuv.pk} dan qaytarildi",
           HarakatTuri.QAYTARISH)
    qator.qaytarilgan += miqdor
    qator.save(update_fields=["qaytarilgan"])

    sotuv.qaytarilgan_summa += summa
    sotuv.qaytarilgan_summa_dollar += summa_dollar
    sotuv.save(update_fields=["qaytarilgan_summa", "qaytarilgan_summa_dollar"])

    messages.success(request, "Qaytarish yozildi, tovar omborga qaytdi.")
    return redirect(orqaga)


def royxat(request):
    """Sotuvlar ro'yxati va kunlik tushum."""
    bugun = timezone.localtime().date()
    kun = request.GET.get("kun", "")
    try:
        sana = timezone.datetime.strptime(kun, "%Y-%m-%d").date() if kun else bugun
    except ValueError:
        sana = bugun

    boshi = timezone.make_aware(timezone.datetime.combine(sana, timezone.datetime.min.time()))
    # Bekor qilingan cheklar ham ko'rinadi — ular bazada qoladi, lekin
    # tushumga qo'shilmaydi.
    sotuvlar = (Sotuv.objects
                .filter(sana__gte=boshi, sana__lt=boshi + timedelta(days=1))
                .filter(Q(yakunlangan=True) | Q(bekor_qilingan=True))
                .prefetch_related("qatorlar__mahsulot"))
    hisobda = sotuvlar.filter(bekor_qilingan=False)

    # Kunlik tushum ham ikki xil: so'm va dollar qo'shilmaydi.
    # Qaytarib berilgan pul tushumdan ayriladi.
    yigindi = hisobda.aggregate(
        s=Sum(F("jami") - F("qaytarilgan_summa")),
        d=Sum(F("jami_dollar") - F("qaytarilgan_summa_dollar")),
    )

    return render(request, "sotuv/royxat.html", {
        "sotuvlar": sotuvlar,
        "sana": sana,
        "bugunmi": sana == bugun,
        "jami": yigindi["s"] or Decimal("0"),
        "jami_dollar": yigindi["d"] or Decimal("0"),
        "soni": hisobda.count(),
    })
