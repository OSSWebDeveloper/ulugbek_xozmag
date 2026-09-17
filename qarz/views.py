"""Qarz daftari ko'rinishlari."""
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from ombor.models import HarakatTuri, Mahsulot, OmborHarakati

from .forms import QarzdorForm, TolovForm
from .models import Hudud, Qarz, QarzQator, Qarzdor, Tolov


def boshlash(request):
    """Bosh sahifa: eski qarzdormi yoki yangi qarzdormi?"""
    return render(request, "qarz/boshlash.html")


def qidirish(request):
    """Eski qarzdorni qidirish."""
    matn = request.GET.get("q", "").strip()
    hudud_id = request.GET.get("hudud", "")
    qarzdorlar = Qarzdor.objects.select_related("hudud")

    if matn:
        qarzdorlar = qarzdorlar.filter(
            Q(ism__icontains=matn) | Q(familiya__icontains=matn) | Q(telefon__icontains=matn)
        )
    if hudud_id:
        qarzdorlar = qarzdorlar.filter(hudud_id=hudud_id)

    return render(request, "qarz/qidirish.html", {
        "qarzdorlar": qarzdorlar[:100],
        "matn": matn,
        "hudud_id": hudud_id,
        "hududlar": Hudud.objects.all(),
        "jami_topildi": qarzdorlar.count(),
    })


def yangi_qarzdor(request):
    """Yangi qarzdor qo'shish formasi."""
    if request.method == "POST":
        form = QarzdorForm(request.POST)
        if form.is_valid():
            qarzdor = form.save()
            messages.success(request, f"{qarzdor.toliq_ism} qo'shildi.")
            # Yaratilgandan keyin darrov qarz qo'shish sahifasiga o'tadi
            return redirect("qarz:qarz_boshlash", qarzdor_pk=qarzdor.pk)
    else:
        form = QarzdorForm()
    return render(request, "qarz/yangi_qarzdor.html", {"form": form})


def qarzdor_karta(request, pk):
    """Qarzdorning kartochkasi: qarzlari, to'lovlari, balansi."""
    qarzdor = get_object_or_404(Qarzdor.objects.select_related("hudud"), pk=pk)
    return render(request, "qarz/qarzdor_karta.html", {
        "qarzdor": qarzdor,
        "qarzlar": qarzdor.qarzlar.prefetch_related("qatorlar"),
        "tolovlar": qarzdor.tolovlar.all()[:20],
        "tolov_form": TolovForm(),
    })


def qarzdor_tahrir(request, pk):
    """Qarzdor ma'lumotlarini tahrirlash."""
    qarzdor = get_object_or_404(Qarzdor, pk=pk)
    if request.method == "POST":
        form = QarzdorForm(request.POST, instance=qarzdor)
        if form.is_valid():
            form.save()
            messages.success(request, "Ma'lumot saqlandi.")
            return redirect("qarz:qarzdor_karta", pk=qarzdor.pk)
    else:
        form = QarzdorForm(instance=qarzdor)
    return render(request, "qarz/yangi_qarzdor.html",
                  {"form": form, "tahrir": True, "qarzdor": qarzdor})


def qarz_boshlash(request, qarzdor_pk):
    """Qarzdor uchun yangi (yoki tugallanmagan) qarz hujjatini ochadi."""
    qarzdor = get_object_or_404(Qarzdor, pk=qarzdor_pk)
    qarz = qarzdor.qarzlar.filter(yakunlangan=False).first()
    if qarz is None:
        qarz = Qarz.objects.create(qarzdor=qarzdor)
    return redirect("qarz:qarz_tahrir", pk=qarz.pk)


def qarz_tahrir(request, pk):
    """Qarz qo'shish sahifasi (kassa ko'rinishi)."""
    qarz = get_object_or_404(Qarz.objects.select_related("qarzdor__hudud"), pk=pk)
    mahsulotlar = Mahsulot.objects.filter(faol=True)
    return render(request, "qarz/qarz_tahrir.html", {
        "qarz": qarz,
        "qarzdor": qarz.qarzdor,
        "qatorlar": qarz.qatorlar.all(),
        "mahsulotlar": mahsulotlar,
    })


def _songa(qiymat, nom):
    """Matnni Decimal ga aylantiradi. (son, xato_matni) qaytaradi."""
    try:
        son = Decimal(str(qiymat).replace(",", ".").strip())
    except (InvalidOperation, AttributeError, TypeError):
        return None, f"{nom} xato kiritildi."
    if son <= 0:
        return None, f"{nom} noldan katta bo'lishi kerak."
    return son, None


@transaction.atomic
def qator_qoshish(request, pk):
    """Qarzga tovar qatorini qo'shadi va ombordan ayiradi."""
    qarz = get_object_or_404(Qarz, pk=pk)
    if request.method != "POST":
        return redirect("qarz:qarz_tahrir", pk=qarz.pk)

    mahsulot = get_object_or_404(Mahsulot, pk=request.POST.get("mahsulot"))
    miqdor, xato = _songa(request.POST.get("miqdor"), "Miqdor")
    if xato:
        messages.error(request, xato)
        return redirect("qarz:qarz_tahrir", pk=qarz.pk)

    narx, xato = _songa(request.POST.get("narx") or mahsulot.narx, "Narx")
    if xato:
        messages.error(request, xato)
        return redirect("qarz:qarz_tahrir", pk=qarz.pk)

    mahsulot = Mahsulot.objects.select_for_update().get(pk=mahsulot.pk)
    if miqdor > mahsulot.qoldiq:
        messages.error(
            request,
            f"Omborda yetarli emas. {mahsulot.nom}: {mahsulot.qoldiq_son} {mahsulot.birlik} qoldi.",
        )
        return redirect("qarz:qarz_tahrir", pk=qarz.pk)

    QarzQator.objects.create(qarz=qarz, mahsulot=mahsulot, miqdor=miqdor, narx=narx)
    mahsulot.qoldiq -= miqdor
    mahsulot.save(update_fields=["qoldiq"])
    OmborHarakati.objects.create(
        mahsulot=mahsulot, tur=HarakatTuri.CHIQIM, miqdor=miqdor,
        izoh=f"Qarz #{qarz.pk} - {qarz.qarzdor.toliq_ism}",
    )
    return redirect("qarz:qarz_tahrir", pk=qarz.pk)


@transaction.atomic
def qator_ochirish(request, pk):
    """Qatorni o'chiradi va tovarni omborga qaytaradi."""
    qator = get_object_or_404(QarzQator.objects.select_related("qarz"), pk=pk)
    qarz_pk = qator.qarz.pk
    if request.method == "POST":
        mahsulot = Mahsulot.objects.select_for_update().get(pk=qator.mahsulot_id)
        mahsulot.qoldiq += qator.miqdor
        mahsulot.save(update_fields=["qoldiq"])
        OmborHarakati.objects.create(
            mahsulot=mahsulot, tur=HarakatTuri.KIRIM, miqdor=qator.miqdor,
            izoh=f"Qarz #{qarz_pk} dan qaytarildi",
        )
        qator.delete()
        messages.success(request, "Qator o'chirildi, tovar omborga qaytdi.")
    return redirect("qarz:qarz_tahrir", pk=qarz_pk)


def qarz_yakunlash(request, pk):
    """Qarz hujjatini yopadi."""
    qarz = get_object_or_404(Qarz, pk=pk)
    if request.method == "POST":
        if qarz.qatorlar_soni == 0:
            qarzdor_pk = qarz.qarzdor_id
            qarz.delete()
            messages.info(request, "Bo'sh qarz bekor qilindi.")
            return redirect("qarz:qarzdor_karta", pk=qarzdor_pk)
        qarz.izoh = request.POST.get("izoh", "")[:200]
        qarz.yakunlangan = True
        qarz.save(update_fields=["izoh", "yakunlangan"])
        messages.success(request, "Qarz daftarga yozildi.")
    return redirect("qarz:qarzdor_karta", pk=qarz.qarzdor_id)


def tolov_qoshish(request, qarzdor_pk):
    """Qarzdor to'lov qildi."""
    qarzdor = get_object_or_404(Qarzdor, pk=qarzdor_pk)
    if request.method == "POST":
        form = TolovForm(request.POST)
        if form.is_valid():
            tolov = form.save(commit=False)
            tolov.qarzdor = qarzdor
            tolov.save()
            messages.success(request, "To'lov qabul qilindi.")
        else:
            messages.error(request, "To'lov summasi xato.")
    return redirect("qarz:qarzdor_karta", pk=qarzdor.pk)


def tolov_ochirish(request, pk):
    """To'lovni bekor qiladi."""
    tolov = get_object_or_404(Tolov, pk=pk)
    qarzdor_pk = tolov.qarzdor_id
    if request.method == "POST":
        tolov.delete()
        messages.success(request, "To'lov o'chirildi.")
    return redirect("qarz:qarzdor_karta", pk=qarzdor_pk)


def qarzdorlar_royxati(request):
    """Barcha qarzdorlar va ularning balansi."""
    hudud_id = request.GET.get("hudud", "")
    qarzdorlar = Qarzdor.objects.select_related("hudud")
    if hudud_id:
        qarzdorlar = qarzdorlar.filter(hudud_id=hudud_id)

    royxat = sorted(qarzdorlar, key=lambda q: q.balans, reverse=True)
    jami_balans = sum((q.balans for q in royxat), Decimal("0"))

    return render(request, "qarz/qarzdorlar.html", {
        "qarzdorlar": royxat,
        "hududlar": Hudud.objects.all(),
        "hudud_id": hudud_id,
        "jami_balans": jami_balans,
    })
