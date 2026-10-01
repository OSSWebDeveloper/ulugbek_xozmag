"""Rang (kolerovka) ko'rinishlari.

Ish tartibi:
1. Mijoz rang mashinasi oldidagi katalog varag'idan rang tanlaydi.
2. Sotuvchi rang ostidagi shtrixni skanerlaydi (Soruda'da ham — shtrix
   Soruda kodining o'zi), bankadagi etiketkani skanerlab baza bo'yoqni
   tanlaydi, kolerovka narxini yozadi.
3. «Chek chiqarish» — maxsus chek chop etiladi, mijoz kassaga boradi.
4. Kassir chekni skanerlaydi: baza bo'yoq chekka tushadi (`rang/kassa.py`).
"""
from datetime import datetime, time, timedelta

from django.contrib import messages
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from config.tarmoq import manzillar
from ombor.kod import topish
from ombor.models import Mahsulot, tekis_matn, tekis_son
from ombor.shtrix import chiziqlar as raqam_chiziqlari
from ombor.shtrix import svg as raqam_svg
from ombor.xizmat import oyna_tovarlari, pulga, songa
from qarz.templatetags.xozmag import narxi

from .forms import RangForm
from .models import Buyurtma, Holat, Rang, kalit_yasa
from .namuna import RAL, TOPLAM
from .yuklash import yukla

USTUNLAR = (2, 3, 4, 5)   # katalog varag'ida bir qatordagi ranglar (2 — katta namunalar)
ESKI_KUNLAR = 30       # shuncha kun ichidagi to'lanmagan cheklar stansiyada ko'rinib turadi


def _raqam(qiymat):
    """Formadan kelgan id: raqam bo'lmasa None (filter ValueError bermasin)."""
    qiymat = (qiymat or "").strip()
    return int(qiymat) if qiymat.isdigit() else None


# ---------- Stansiya ----------

def buyurtmani_oqi(post):
    """Stansiya formasini o'qib chek yaratadi.

    (buyurtma, xato, tanlov) qaytaradi. `tanlov` — xato bo'lsa ekranda
    tanlangan rang va baza o'chib ketmasin, sotuvchi qaytadan skanerlamasin.
    """
    rang = Rang.objects.filter(pk=_raqam(post.get("rang"))).first()
    baza = Mahsulot.objects.filter(pk=_raqam(post.get("baza")), faol=True).first()
    tanlov = {"rang": rang, "baza": baza, "miqdor": post.get("miqdor", ""),
              "narx": post.get("rang_narxi", "")}

    if rang is None:
        return None, "Rangni skanerlang yoki kodini yozing.", tanlov
    if baza is None:
        return None, "Baza bo'yoqni tanlang — bankadagi etiketkani skanerlang.", tanlov
    miqdor, xato = songa(post.get("miqdor"), "Miqdor")
    if xato:
        return None, xato, tanlov
    narx, xato = pulga(post.get("rang_narxi"), "Kolerovka narxi")
    if xato:
        return None, xato, tanlov
    # Kassa baribir ayira olmaydi — mijoz kassada qolib ketmasin, shu yerda aytiladi
    if miqdor > baza.qoldiq:
        return None, (f"Omborda yetarli emas. {baza.nom}: {tekis_matn(baza.qoldiq)} "
                      f"{baza.birlik} qoldi."), tanlov

    buyurtma = Buyurtma.objects.create(
        rang=rang, rang_kodi=rang.kod, rang_nomi=rang.nom, rang_hex=rang.hex,
        baza=baza, baza_nomi=baza.nom, baza_birligi=baza.birlik, miqdor=miqdor,
        baza_narxi=baza.narx, baza_valyuta=baza.valyuta, rang_narxi=narx,
    )
    return buyurtma, None, tanlov


def stansiya(request):
    """Rang mashinasi yonidagi ekran: rang + baza + narx -> maxsus chek."""
    tanlov = {}
    if request.method == "POST":
        buyurtma, xato, tanlov = buyurtmani_oqi(request.POST)
        if buyurtma:
            # Chek sahifasi o'zi chop etadi va stansiyaga qaytadi
            return redirect(reverse("rang:chek", args=[buyurtma.pk]) + "?chop=1")
        messages.error(request, xato)

    boshi = timezone.make_aware(datetime.combine(timezone.localtime().date(), time.min))
    cheklar = Buyurtma.objects.select_related("sotuv", "qarz")
    return render(request, "rang/stansiya.html", {
        "bugungi": cheklar.filter(sana__gte=boshi),
        # Kechagi (va undan oldingi) to'lanmagan bo'yoq ko'zdan qochmasin
        "eskilar": cheklar.filter(sana__lt=boshi, sana__gte=boshi - timedelta(days=ESKI_KUNLAR),
                                  bekor_qilingan=False, sotuv__isnull=True, qarz__isnull=True),
        "mahsulotlar": oyna_tovarlari(),
        "ranglar_soni": Rang.objects.count(),
        "tanlov": tanlov,
        # Rang mashinasi kompyuteri Wi-Fi orqali shu manzil bilan ulanadi
        "tarmoq": manzillar(request.get_port())[:1],
    })


def rang_json(rang):
    return {"topildi": True, "tur": "rang", "id": rang.pk, "kod": rang.kod, "nom": rang.nom,
            "hex": rang.hex, "yozuv": rang.yozuv_rangi, "toplam": rang.toplam}


def baza_json(mahsulot):
    if not mahsulot.faol:
        return {"topildi": False, "xato": f"{mahsulot.nom} ombordan yashirilgan — avval faollashtiring."}
    return {
        "topildi": True, "tur": "baza", "id": mahsulot.pk, "nom": mahsulot.nom,
        "kod": mahsulot.kod, "qisqa": mahsulot.qisqa_kod, "birlik": mahsulot.birlik,
        "qoldiq": tekis_son(mahsulot.qoldiq), "qoldiq_matni": tekis_matn(mahsulot.qoldiq),
        "narx": tekis_son(mahsulot.narx), "narx_matni": narxi(mahsulot),
        "valyuta": mahsulot.valyuta_belgisi,
    }


def kod_qidir(request):
    """Stansiyada skanerlangan yoki yozilgan kod — rangmi, bazami yoki chekmi.

    Tartib: katalogdagi rang (aynan) -> etiketkadagi to'liq tovar kodi ->
    rang cheki -> rang kodining oxiri («3020» -> «RAL 3020») -> tovarning
    qisqa kodi. Rang katalogi tovar kodidan oldin turadi: «1015» kabi raqamli
    rang kodi tovarning oxirgi 4 raqami bilan adashmasin.
    """
    kiritilgan = request.GET.get("k", "").strip()
    kalit = kalit_yasa(kiritilgan)
    if not kalit:
        return JsonResponse({"topildi": False, "xato": "Kod yozilmadi."})

    rang = Rang.objects.filter(kalit=kalit).first()
    if rang:
        return JsonResponse(rang_json(rang))

    natija = topish(kiritilgan)
    if natija.rang_cheki is not None:
        return JsonResponse({"topildi": True, "tur": "chek",
                             "manzil": reverse("rang:chek", args=[natija.rang_cheki.pk])})
    if natija.mahsulot and natija.qanday == "toliq":
        return JsonResponse(baza_json(natija.mahsulot))

    # Qo'lda yozilgan rang kodining oxiri — tovardagi «oxirgi 4 raqam» kabi
    if len(kalit) >= 3:
        mos = list(Rang.objects.filter(kalit__endswith=kalit)[:2])
        if len(mos) == 1:
            return JsonResponse(rang_json(mos[0]))
    if natija.mahsulot:
        return JsonResponse(baza_json(natija.mahsulot))
    return JsonResponse({"topildi": False,
                         "xato": f"«{kiritilgan}» — bunday rang katalogda ham, omborda ham yo'q."})


# ---------- Chek ----------

def chek(request, pk):
    """Maxsus chek — chek printerida chop etiladi (brauzerning o'z oynasi).

    `?chop=1` — stansiyadan yangi chiqqan chek: sahifa o'zi chop etadi va
    chop etish tugagach stansiyaga qaytadi (`static/js/rang_chek.js`).
    """
    buyurtma = get_object_or_404(Buyurtma.objects.select_related("sotuv", "qarz"), pk=pk)
    kod = buyurtma.kod
    return render(request, "rang/chek.html", {
        "b": buyurtma,
        "shtrix": raqam_svg(kod),
        "modullar": raqam_chiziqlari(kod)[1],
        "chop": request.GET.get("chop") == "1",
    })


def bekor(request, pk):
    """Chekni bekor qiladi — mijoz fikridan qaytdi. To'langani bekor bo'lmaydi."""
    buyurtma = get_object_or_404(Buyurtma.objects.select_related("sotuv", "qarz"), pk=pk)
    if request.method == "POST":
        holat = buyurtma.holat
        if holat in (Holat.TOLANDI, Holat.QARZGA):
            messages.error(request, f"Rang cheki #{pk} to'langan — bekor qilib bo'lmaydi.")
        elif holat == Holat.KASSADA:
            messages.error(request, f"Rang cheki #{pk} kassada turibdi ({buyurtma.hujjat_matni}) "
                                    f"— avval o'sha yerdagi qatorni o'chiring.")
        elif holat == Holat.KUTILMOQDA:
            buyurtma.bekor_qilingan = True
            buyurtma.save(update_fields=["bekor_qilingan"])
            messages.info(request, f"Rang cheki #{pk} bekor qilindi.")
    return redirect("rang:stansiya")


# ---------- Ranglar katalogi ----------

def _toplamlar():
    return list(Rang.objects.order_by("toplam").values_list("toplam", flat=True).distinct())


def _toplam(request):
    """`?t=` — to'plam; yo'q yoki «*» bo'lsa hammasi (None). Bo'sh — to'plamsizlar."""
    toplam = request.GET.get("t")
    return None if toplam == "*" else toplam


def ranglar(request):
    """Katalogdagi ranglar: qidirish, to'plam bo'yicha ko'rish."""
    matn = request.GET.get("q", "").strip()
    toplam = _toplam(request)
    royxat = Rang.objects.all()
    if matn:
        royxat = royxat.filter(Q(kalit__contains=kalit_yasa(matn)) | Q(nom__icontains=matn))
    if toplam is not None:
        royxat = royxat.filter(toplam=toplam)
    return render(request, "rang/ranglar.html", {
        "ranglar": royxat,
        "matn": matn,
        "toplam": toplam,
        "toplamlar": _toplamlar(),
        "jami": Rang.objects.count(),
    })


def rang_yangi(request):
    form = RangForm(request.POST or None, initial={"toplam": request.GET.get("t", "")})
    if request.method == "POST" and form.is_valid():
        rang = form.save()
        messages.success(request, f"{rang.kod} katalogga qo'shildi.")
        return redirect(reverse("rang:ranglar") + f"?t={rang.toplam}")
    return render(request, "rang/rang_form.html", {"form": form, "toplamlar": _toplamlar()})


def rang_tahrir(request, pk):
    rang = get_object_or_404(Rang, pk=pk)
    form = RangForm(request.POST or None, instance=rang)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Saqlandi.")
        return redirect(reverse("rang:ranglar") + f"?t={rang.toplam}")
    return render(request, "rang/rang_form.html", {
        "form": form, "rang": rang, "toplamlar": _toplamlar(),
        "cheklar_soni": rang.buyurtmalar.count(),
    })


def rang_ochirish(request, pk):
    """Rangni katalogdan o'chiradi. U bilan chek chiqqan bo'lsa — faqat yashiriladi."""
    rang = get_object_or_404(Rang, pk=pk)
    if request.method == "POST":
        try:
            rang.delete()
            messages.info(request, f"{rang.kod} katalogdan o'chirildi.")
        except ProtectedError:
            rang.faol = False
            rang.save(update_fields=["faol"])
            messages.warning(request, f"{rang.kod} bilan chek chiqarilgan — o'chirilmadi, "
                                      f"faqat katalogdan yashirildi.")
    return redirect(reverse("rang:ranglar") + f"?t={rang.toplam}")


def yuklash(request):
    """Ro'yxatni matndan yuklash (Soruda, Excel) yoki namuna RAL palitrasi."""
    matn = toplam = ""
    if request.method == "POST":
        if request.POST.get("namuna") == "ral":
            matn, toplam = RAL, TOPLAM
        else:
            matn = request.POST.get("matn", "")
            toplam = request.POST.get("toplam", "").strip()
        natija = yukla(matn, toplam)
        if natija.yangi or natija.yangilandi:
            xabar = f"Yuklandi: {natija.yangi} ta yangi rang"
            if natija.yangilandi:
                xabar += f", {natija.yangilandi} tasi yangilandi"
            messages.success(request, xabar + ".")
            if natija.xatolar:
                messages.warning(request, f"{len(natija.xatolar)} ta qator o'tkazib yuborildi: "
                                          + " ".join(natija.xatolar[:3]))
            return redirect(reverse("rang:ranglar") + f"?t={toplam}")
        messages.error(request, "Bironta rang o'qilmadi. " + " ".join(natija.xatolar[:3]))
    return render(request, "rang/yuklash.html", {
        "matn": "" if request.POST.get("namuna") else matn,
        "toplam": toplam,
        "toplamlar": _toplamlar(),
    })


def toplam_ochirish(request):
    """Butun to'plamni o'chiradi — masalan namuna RAL haqiqiy palitra kelgach.

    Chek chiqarilgan ranglar o'chmaydi (cheklar ularni ko'rsatadi), yashiriladi.
    """
    if request.method != "POST":
        return redirect("rang:ranglar")
    toplam = request.POST.get("toplam", "")
    royxat = Rang.objects.filter(toplam=toplam)
    chekli = royxat.filter(buyurtmalar__isnull=False).distinct()
    yashirildi = chekli.update(faol=False)
    ochdi, _ = royxat.exclude(pk__in=chekli.values("pk")).delete()
    nomi = f"«{toplam}»" if toplam else "To'plamsiz ranglar"
    xabar = f"{nomi}: {ochdi} ta rang o'chirildi"
    if yashirildi:
        xabar += f", {yashirildi} tasi chekda bor — yashirildi"
    messages.info(request, xabar + ".")
    return redirect("rang:ranglar")


# ---------- Katalog varag'i ----------

def varaq(request):
    """Rang mashinasi oldiga qo'yiladigan varaq: rang, kodi va shtrixi.

    A4 da chop etiladi. Har bir to'plam yangi sahifadan boshlanadi.
    `tur=bosh` — rang o'rnida bo'sh katak: printer rangni aniq bermaydi,
    unga rang kartasidan haqiqiy namuna yopishtiriladi.
    """
    toplam = _toplam(request)
    try:
        ustun = int(request.GET.get("ustun", 4))
    except ValueError:
        ustun = 4
    if ustun not in USTUNLAR:
        ustun = 4
    tur = "bosh" if request.GET.get("tur") == "bosh" else "rang"

    royxat = Rang.objects.filter(faol=True)
    if toplam is not None:
        royxat = royxat.filter(toplam=toplam)
    guruhlar = []
    for rang in royxat:
        if not guruhlar or guruhlar[-1][0] != rang.toplam:
            guruhlar.append((rang.toplam, []))
        guruhlar[-1][1].append(rang)

    return render(request, "rang/varaq.html", {
        "guruhlar": guruhlar,
        "soni": sum(len(r) for _, r in guruhlar),
        "ustun": ustun,
        "ustunlar": USTUNLAR,
        "tur": tur,
        "toplam": toplam,
        "toplamlar": _toplamlar(),
    })
