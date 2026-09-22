"""Ombor (sklad) ko'rinishlari."""
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import KirimForm, MahsulotForm
from .kod import topish, tozala
from .models import (HarakatTuri, Mahsulot, OmborHarakati, tekis_matn, tekis_son)


def royxat(request):
    """Skladdagi barcha tovarlar.

    Qidiruv maydoni nom bilan ham, kod bilan ham ishlaydi: yorliqdagi
    raqam yozilsa (yoki skaner o'qib bersa) o'sha tovar chiqadi.
    """
    matn = request.GET.get("q", "").strip()
    mahsulotlar = Mahsulot.objects.all()
    if matn:
        izlov = Q(nom__icontains=matn)
        raqam = matn.replace(" ", "")
        if raqam.isdigit():
            izlov |= Q(kod__endswith=raqam)
        mahsulotlar = mahsulotlar.filter(izlov)
    return render(request, "ombor/royxat.html", {
        "mahsulotlar": mahsulotlar,
        "matn": matn,
        "tugagan": Mahsulot.objects.filter(faol=True, qoldiq__lte=0).count(),
    })


def kod_qidir(request):
    """Kod, shtrix yoki tarozi etiketkasi bo'yicha tovar — JSON javob.

    Kassa, qarz ekrani va ombor ro'yxati shu manzilga so'raydi. Qidirish
    qoidalari `ombor/kod.py` da — JS ularni takrorlamaydi.
    """
    kiritilgan = request.GET.get("k", "")
    natija = topish(kiritilgan)
    if natija.mahsulot is None:
        # `qanday` sahifaga kerak: notanish **shtrix** bo'lsa ombor «yangi tovar»
        # taklif qiladi, notanish qisqa kod esa shunchaki xato.
        return JsonResponse({"topildi": False, "xato": natija.xato,
                             "qanday": natija.qanday, "kod": tozala(kiritilgan)})

    m = natija.mahsulot
    return JsonResponse({
        "topildi": True,
        "id": m.pk,
        "nom": m.nom,
        "kod": m.kod,
        "qisqa": m.qisqa_kod,
        "birlik": m.birlik,
        "qoldiq": tekis_son(m.qoldiq),
        "qadoq": m.qadoq_matni,
        "valyuta": m.valyuta_belgisi,
        "faol": m.faol,
        "bormi": m.qoldiq > 0,
        # Miqdor faqat kodning o'zi aytganda to'ladi (tarozi yoki quti shtrixi).
        # `miqdor` maydonga yoziladi, `miqdor_matni` ekranda ko'rinadi — do'konda
        # kasr vergul bilan o'qiladi (1,25), maydonda esa nuqta qoladi.
        "miqdor": tekis_son(natija.miqdor) if natija.miqdor is not None else "",
        "miqdor_matni": tekis_matn(natija.miqdor) if natija.miqdor is not None else "",
        "qanday": natija.qanday,
        "kirim": reverse("ombor:kirim", args=[m.pk]) + "?oyna=1",
    })


def mahsulot_yangi(request):
    """Skladga yangi tovar turi qo'shish.

    «Birlik o'zgaradi» richagi yoqilgan bo'lsa boshlang'ich qoldiq qadoq
    sonidan hisoblanadi (3 rulon -> 300 metr), tarixga esa ikkala son ham
    yoziladi.
    """
    if request.method == "POST":
        form = MahsulotForm(request.POST, yangi=True)
        if form.is_valid():
            mahsulot = form.save()
            if mahsulot.qoldiq:
                qadoq = form.cleaned_data.get("qadoq_soni")
                ikki = mahsulot.ikki_birlikmi and qadoq
                OmborHarakati.objects.create(
                    mahsulot=mahsulot, tur=HarakatTuri.KIRIM,
                    miqdor=mahsulot.qoldiq,
                    kiritilgan_miqdor=qadoq if ikki else None,
                    kiritilgan_birlik=mahsulot.olish_birligi if ikki else "",
                    izoh="Boshlang'ich qoldiq",
                )
            xabar = f"{mahsulot.nom} skladga qo'shildi"
            if mahsulot.qoldiq:
                xabar += f" — {mahsulot.qoldiq_toliq}"
            messages.success(request, xabar + ".")
            return redirect("ombor:royxat")
    else:
        # Omborda notanish shtrix skanerlansa shu sahifa kod bilan ochiladi —
        # yangi mol tushirilayotganda tovar va kodi bir yo'la kiritiladi.
        form = MahsulotForm(yangi=True,
                            initial={"shtrix": request.GET.get("shtrix", "").strip()})
    return render(request, "ombor/mahsulot_form.html", {"form": form, "yangi": True})


def mahsulot_tahrir(request, pk):
    """Tovar ma'lumotlarini tahrirlash."""
    mahsulot = get_object_or_404(Mahsulot, pk=pk)
    eski_qoldiq = mahsulot.qoldiq
    if request.method == "POST":
        form = MahsulotForm(request.POST, instance=mahsulot, yangi=False)
        if form.is_valid():
            mahsulot = form.save()
            farq = mahsulot.qoldiq - eski_qoldiq
            if farq:
                OmborHarakati.objects.create(
                    mahsulot=mahsulot, tur=HarakatTuri.TUZATISH,
                    miqdor=farq, izoh="Qo'lda tuzatildi",
                )
            messages.success(request, "Saqlandi.")
            return redirect("ombor:royxat")
    else:
        form = MahsulotForm(instance=mahsulot, yangi=False)
    return render(request, "ombor/mahsulot_form.html", {"form": form, "mahsulot": mahsulot})


@transaction.atomic
def kirim(request, pk):
    """Omborga tovar kirimi.

    Ikki birlikli tovarda miqdor olish birligida kiritilishi mumkin
    (2 rulon); omborga sotuv birligida qo'shiladi (200 metr).
    """
    mahsulot = get_object_or_404(Mahsulot, pk=pk)
    if request.method == "POST":
        form = KirimForm(request.POST, mahsulot=mahsulot)
        if form.is_valid():
            kiritilgan = form.cleaned_data["miqdor"]
            kiritilgan_birlik = form.kiritilgan_birlik()
            miqdor = form.sotuv_miqdori()

            mahsulot = Mahsulot.objects.select_for_update().get(pk=pk)
            mahsulot.qoldiq += miqdor
            mahsulot.save(update_fields=["qoldiq"])
            OmborHarakati.objects.create(
                mahsulot=mahsulot, tur=HarakatTuri.KIRIM, miqdor=miqdor,
                kiritilgan_miqdor=kiritilgan, kiritilgan_birlik=kiritilgan_birlik,
                izoh=form.cleaned_data["izoh"],
            )
            xabar = f"{mahsulot.nom}: +{tekis_matn(miqdor)} {mahsulot.birlik}"
            if kiritilgan_birlik != mahsulot.birlik:
                xabar += f" ({tekis_matn(kiritilgan)} {kiritilgan_birlik})"
            messages.success(request, xabar)
            return redirect("ombor:royxat")
    else:
        form = KirimForm(mahsulot=mahsulot)

    # `?oyna=1` — ombor ro'yxatidagi ichki oyna faqat forma qismini so'raydi.
    shablon = "ombor/kirim_forma.html" if request.GET.get("oyna") else "ombor/kirim.html"
    return render(request, shablon, {
        "form": form, "mahsulot": mahsulot, "oynada": bool(request.GET.get("oyna")),
    })


def harakatlar(request, pk):
    """Bitta tovarning kirim-chiqim tarixi."""
    mahsulot = get_object_or_404(Mahsulot, pk=pk)
    return render(request, "ombor/harakatlar.html", {
        "mahsulot": mahsulot,
        "harakatlar": mahsulot.harakatlar.all()[:200],
    })
