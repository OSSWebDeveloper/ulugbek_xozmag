"""Ombor (sklad) ko'rinishlari."""
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import KirimForm, MahsulotForm
from .models import HarakatTuri, Mahsulot, OmborHarakati, tekis_son


def royxat(request):
    """Skladdagi barcha tovarlar."""
    matn = request.GET.get("q", "").strip()
    mahsulotlar = Mahsulot.objects.all()
    if matn:
        mahsulotlar = mahsulotlar.filter(Q(nom__icontains=matn))
    return render(request, "ombor/royxat.html", {
        "mahsulotlar": mahsulotlar,
        "matn": matn,
        "tugagan": Mahsulot.objects.filter(faol=True, qoldiq__lte=0).count(),
    })


def mahsulot_yangi(request):
    """Skladga yangi tovar turi qo'shish."""
    if request.method == "POST":
        form = MahsulotForm(request.POST)
        if form.is_valid():
            mahsulot = form.save()
            if mahsulot.qoldiq:
                OmborHarakati.objects.create(
                    mahsulot=mahsulot, tur=HarakatTuri.KIRIM,
                    miqdor=mahsulot.qoldiq, izoh="Boshlang'ich qoldiq",
                )
            messages.success(request, f"{mahsulot.nom} skladga qo'shildi.")
            return redirect("ombor:royxat")
    else:
        form = MahsulotForm()
    return render(request, "ombor/mahsulot_form.html", {"form": form})


def mahsulot_tahrir(request, pk):
    """Tovar ma'lumotlarini tahrirlash."""
    mahsulot = get_object_or_404(Mahsulot, pk=pk)
    eski_qoldiq = mahsulot.qoldiq
    if request.method == "POST":
        form = MahsulotForm(request.POST, instance=mahsulot)
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
        form = MahsulotForm(instance=mahsulot)
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
            xabar = f"{mahsulot.nom}: +{tekis_son(miqdor)} {mahsulot.birlik}"
            if kiritilgan_birlik != mahsulot.birlik:
                xabar += f" ({tekis_son(kiritilgan)} {kiritilgan_birlik})"
            messages.success(request, xabar)
            return redirect("ombor:royxat")
    else:
        form = KirimForm(mahsulot=mahsulot)
    return render(request, "ombor/kirim.html", {"form": form, "mahsulot": mahsulot})


def harakatlar(request, pk):
    """Bitta tovarning kirim-chiqim tarixi."""
    mahsulot = get_object_or_404(Mahsulot, pk=pk)
    return render(request, "ombor/harakatlar.html", {
        "mahsulot": mahsulot,
        "harakatlar": mahsulot.harakatlar.all()[:200],
    })
