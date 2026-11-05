"""Ombor (sklad) ko'rinishlari."""
from urllib.parse import urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from . import excel
from .excel_views import filtrlar
from .forms import KirimForm, MahsulotForm, QoldiqTuzatishForm
from .kod import topish
from .xizmat import QIDIRUV_SONI, karta_malumoti
from .models import (ETIKETKA_KOPI, HarakatTuri, Mahsulot, OmborHarakati, OmborYangilanish,
                     tekis_matn, tekis_son)
from .shtrix import chiziqlar


def royxat(request):
    """Skladdagi tovarlar — 50 tadan sahifalab (Excel'dan 10 000 tagacha tovar keladi).

    Qidiruv maydoni nom bilan ham, kod bilan ham ishlaydi: yorliqdagi
    raqam yozilsa (yoki skaner o'qib bersa) o'sha tovar chiqadi.
    «Kam qolganlar birinchi» belgilansa — omborda qolgan hajmiga teskari tartib.
    Yuklab olinadigan Excel ham aynan shu filtr va tartibda bo'ladi.
    """
    f = filtrlar(request)
    mahsulotlar = excel.tovarlar(**f)
    sahifa = Paginator(mahsulotlar, 50).get_page(request.GET.get("page"))
    soralgan = {k: v for k, v in request.GET.items() if k != "page" and v}
    return render(request, "ombor/royxat.html", {
        "mahsulotlar": sahifa,
        "matn": f["q"],
        "f": f,
        "topildi": sahifa.paginator.count,
        "qidiruv_satri": urlencode(soralgan),
        "tugagan": Mahsulot.objects.filter(faol=True, qoldiq__lte=0).count(),
        "qoralamalar": OmborYangilanish.objects.filter(holat=OmborYangilanish.QORALAMA).count(),
    })


def kod_qidir(request):
    """Kod, shtrix yoki tarozi etiketkasi bo'yicha tovar — JSON javob.

    Kassa, qarz ekrani va ombor ro'yxati shu manzilga so'raydi. Qidirish
    qoidalari `ombor/kod.py` da — JS ularni takrorlamaydi.
    """
    kiritilgan = request.GET.get("k", "")
    from sotuv.chek import och as chekni_och
    from sotuv.models import Sotuv
    chek_id = chekni_och(kiritilgan)
    if chek_id is not None:
        if Sotuv.objects.filter(pk=chek_id, yakunlangan=True, bekor_qilingan=False).exists():
            return JsonResponse({'topildi': False, 'qaytarish_manzili': reverse('sotuv:chek_qaytarish', args=[chek_id])})
        return JsonResponse({'topildi': False, 'xato': 'Savdo cheki topilmadi yoki bekor qilingan.'})
    natija = topish(kiritilgan)
    if natija.mahsulot is None:
        return JsonResponse({"topildi": False, "xato": natija.xato})

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
        # Miqdor faqat kodning o'zi aytganda to'ladi (tarozi etiketkasidagi og'irlik).
        # `miqdor` maydonga yoziladi, `miqdor_matni` ekranda ko'rinadi — do'konda
        # kasr vergul bilan o'qiladi (1,25), maydonda esa nuqta qoladi.
        "miqdor": tekis_son(natija.miqdor) if natija.miqdor is not None else "",
        "miqdor_matni": tekis_matn(natija.miqdor) if natija.miqdor is not None else "",
        "qanday": natija.qanday,
        "kirim": reverse("ombor:kirim", args=[m.pk]) + "?oyna=1",
        # Rang cheki bo'lsa — kassa uni hujjatga bog'laydi (rang/kassa.py):
        # bitta chek ikki marta ishlatilmaydi
    })


def tovar_qidir(request):
    """Tovar tanlash oynasining qidiruvi — nom yoki kod bo'yicha, ko'pi bilan 30 ta.

    Oynaga hamma tovar chizilmaydi (`xizmat.oyna_tovarlari`), shuning uchun
    qidiruv brauzerda emas, shu yerda bo'ladi.
    """
    matn = request.GET.get("q", "").strip()
    if not matn:
        return JsonResponse({"tovarlar": []})
    topilgan = list(excel.tovarlar(q=matn, bor_birinchi=True)[:QIDIRUV_SONI + 1])
    return JsonResponse({
        "tovarlar": [karta_malumoti(m) for m in topilgan[:QIDIRUV_SONI]],
        "yana": len(topilgan) > QIDIRUV_SONI,
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
            # Kod tayyor: endi etiketkasini chop etib tovarlarga yopishtirish qoladi.
            # Nusxalar soni — kelgan qadoqlar (3 rulon) yoki donalar (20 ta).
            qadoq = form.cleaned_data.get("qadoq_soni")
            soni = (mahsulot.etiketka_soni(qadoq, mahsulot.olish_birligi)
                    if mahsulot.ikki_birlikmi and qadoq else mahsulot.etiketka_soni())
            return redirect(reverse("ombor:etiketka", args=[mahsulot.pk]) + f"?soni={soni}")
    else:
        form = MahsulotForm(yangi=True)
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
            if request.POST.get("etiketka"):
                # «Qo'shish va etiketka» — kelgan mol soniga qarab nusxalar
                soni = mahsulot.etiketka_soni(kiritilgan, kiritilgan_birlik)
                return redirect(reverse("ombor:etiketka", args=[mahsulot.pk]) + f"?soni={soni}")
            return redirect("ombor:royxat")
    else:
        form = KirimForm(mahsulot=mahsulot)

    # `?oyna=1` — ombor ro'yxatidagi ichki oyna faqat forma qismini so'raydi.
    shablon = "ombor/kirim_forma.html" if request.GET.get("oyna") else "ombor/kirim.html"
    return render(request, shablon, {
        "form": form, "mahsulot": mahsulot, "oynada": bool(request.GET.get("oyna")),
    })


@transaction.atomic
def qoldiq_tuzatish(request, pk):
    """Sinish, yaroqsizlik yoki sanoq sababli qoldiqni tarix bilan tuzatish."""
    mahsulot = get_object_or_404(Mahsulot, pk=pk)
    form = QoldiqTuzatishForm(
        request.POST if request.method == 'POST' else None,
        initial={'eski_qoldiq': mahsulot.qoldiq, 'qoldiq': mahsulot.qoldiq_son},
    )
    if request.method == 'POST' and form.is_valid():
        old = form.cleaned_data['eski_qoldiq']
        new = form.cleaned_data['qoldiq']
        # Kirim/sotuv shu orada qoldiqni o'zgartirgan bo'lsa uni bosib ketmaymiz.
        updated = Mahsulot.objects.filter(pk=pk, qoldiq=old).update(qoldiq=new)
        if not updated:
            form.add_error(None, "Qoldiq bu orada o‘zgardi. Sahifani yangilab, qayta kiriting.")
        else:
            izoh = f"Qoldiq: {tekis_matn(old)} → {tekis_matn(new)} {mahsulot.birlik}"
            if form.cleaned_data['sabab']:
                izoh += '. ' + form.cleaned_data['sabab']
            OmborHarakati.objects.create(
                mahsulot=mahsulot, tur=HarakatTuri.TUZATISH,
                miqdor=new-old, kiritilgan_miqdor=new-old,
                kiritilgan_birlik=mahsulot.birlik, izoh=izoh,
            )
            messages.success(request, f"{mahsulot.nom}: qoldiq {tekis_matn(new)} {mahsulot.birlik} bo‘ldi.")
            return redirect('ombor:royxat')
    return render(request, 'ombor/qoldiq_tuzatish.html', {'mahsulot': mahsulot, 'form': form})


def etiketka(request, pk):
    """Tovar etiketkasi: nomi, shtrixi va kodi — etiketka printerida chop etiladi.

    Brauzerning o'z chop etish oynasi ishlatiladi: printer Windows'da
    o'rnatilgan bo'lsa bas, modeli muhim emas. Etiketka o'lchami sahifada
    tanlanadi va brauzerda eslab qolinadi (`static/js/etiketka.js`).
    `?soni=` — nechta nusxa: tovar qo'shilganda va kirimda o'zi qo'yiladi.
    """
    mahsulot = get_object_or_404(Mahsulot, pk=pk)
    try:
        soni = int(request.GET.get("soni", 1))
    except ValueError:
        soni = 1
    return render(request, "ombor/etiketka.html", {
        "mahsulot": mahsulot,
        "soni": min(max(soni, 1), ETIKETKA_KOPI),
        "eng_kop": ETIKETKA_KOPI,
        # Shtrix eni modulda — etiketkada mm ga aylanadi (o'lchamga qarab)
        "modullar": chiziqlar(mahsulot.etiketka_kodi)[1],
    })


def harakatlar(request, pk):
    """Bitta tovarning kirim-chiqim tarixi."""
    mahsulot = get_object_or_404(Mahsulot, pk=pk)
    return render(request, "ombor/harakatlar.html", {
        "mahsulot": mahsulot,
        "harakatlar": mahsulot.harakatlar.all()[:200],
    })

from django.views.decorators.http import require_POST
from django.db import IntegrityError
from .forms import ShtrixKodForm


@require_POST
def shtrix_saqlash(request, pk):
    try:
        with transaction.atomic():
            product = get_object_or_404(Mahsulot.objects.select_for_update(), pk=pk)
            if request.POST.get('eski', '') != (product.shtrix_kod or ''):
                return JsonResponse({'xato': 'Shtrix kod boshqa oynada o‘zgartirilgan. Sahifani yangilang.'}, status=409)
            form = ShtrixKodForm(request.POST, instance=product)
            if not form.is_valid():
                return JsonResponse({'xato': ' '.join(str(e) for errors in form.errors.values() for e in errors)}, status=400)
            product.shtrix_kod = form.cleaned_data['shtrix_kod']
            product.save(update_fields=['shtrix_kod'])
            return JsonResponse({'shtrix_kod': product.shtrix_kod or ''})
    except IntegrityError:
        return JsonResponse({'xato': 'Bu shtrix kod boshqa mahsulotga berilgan.'}, status=400)
