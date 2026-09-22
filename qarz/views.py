"""Qarz daftari ko'rinishlari."""
from decimal import Decimal

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ombor.models import Mahsulot
from ombor.models import HarakatTuri, Valyuta
from ombor.xizmat import (OmborXatosi, ayir, oxirgi_kurs, pulga, qaytar,
                          qaytarishni_oqi, songa, summalarni_oqi)

from .forms import QarzdorForm, TolovForm
from .models import Hudud, Qarz, QarzQator, Qarzdor, Tolov



def pul_matn(son):
    """550000 -> '550 000'. Xabarlarda o'qishga qulay bo'lsin."""
    return f"{son:,.0f}".replace(",", " ")


def boshlash(request):
    """Bosh sahifa: eski qarzdormi yoki yangi qarzdormi?"""
    return render(request, "qarz/boshlash.html")


def hudud_kartalari():
    """Har bir hudud uchun qarzdorlar soni va umumiy qarz.

    Qarzdorlar sahifasida ham, «Oldin qarz olgan» qidiruvida ham
    bir xil tugmalar chiqadi.
    """
    bosh = (0, Decimal("0"), Decimal("0"))
    yigindi = {}
    for q in Qarzdor.objects.all():
        son, balans, dollar = yigindi.get(q.hudud_id, bosh)
        yigindi[q.hudud_id] = (son + 1, balans + q.balans, dollar + q.balans_dollar)
    return [
        {"hudud": h, "soni": yigindi.get(h.pk, bosh)[0],
         "balans": yigindi.get(h.pk, bosh)[1], "balans_dollar": yigindi.get(h.pk, bosh)[2]}
        for h in Hudud.objects.all()
    ]

def qidirish(request):
    """Eski qarzdorni topish.

    Ikki yo'l: butun ro'yxatni ochish yoki hududni tanlab o'sha hududning
    qarzdorlarini ko'rish — qarzdorlar bo'limidagi ketma-ketlikning o'zi.
    """
    hudud_id = request.GET.get("hudud", "")
    korinish = request.GET.get("korinish", "")

    if hudud_id:
        korinish = "royxat"
    elif korinish not in ("royxat", "hududlar"):
        korinish = "tanlov"

    hudud = None
    qarzdorlar = []
    kartalar = []

    if korinish == "royxat":
        tanlangan = Qarzdor.objects.select_related("hudud")
        if hudud_id:
            hudud = get_object_or_404(Hudud, pk=hudud_id)
            tanlangan = tanlangan.filter(hudud=hudud)
        qarzdorlar = sorted(tanlangan, key=lambda q: (q.balans, q.balans_dollar), reverse=True)
    elif korinish == "hududlar":
        kartalar = hudud_kartalari()

    return render(request, "qarz/qidirish.html", {
        "korinish": korinish,
        "qarzdorlar": qarzdorlar,
        "hudud": hudud,
        "hudud_kartalari": kartalar,
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


def qarzdor_json(request):
    """Yangi qarzdorni oynachadan qo'shadi — sahifa almashmaydi.

    Naqd sotuvda pul yetmay qolganda kassir chekni tashlab boshqa sahifaga
    o'tolmaydi: mijoz qarshisida turibdi. Shuning uchun qarzdor o'sha
    oynachaning o'zida yaratiladi va darrov tanlanadi.
    """
    if request.method != "POST":
        return JsonResponse({"ok": False, "xato": "Faqat POST."}, status=405)

    form = QarzdorForm(request.POST)
    if not form.is_valid():
        # Maydon nomi bilan birinchi xatosi — oynachada o'sha maydon tagida chiqadi
        xatolar = {maydon: xato[0] for maydon, xato in form.errors.items()}
        return JsonResponse({"ok": False, "xatolar": xatolar})

    qarzdor = form.save()
    return JsonResponse({
        "ok": True,
        "id": qarzdor.pk,
        "nom": qarzdor.toliq_ism,
        "hudud": qarzdor.hudud.nom,
        "telefon": qarzdor.telefon,
    })


def qarzdor_karta(request, pk):
    """Qarzdorning kartochkasi: qarzlari, to'lovlari, balansi."""
    qarzdor = get_object_or_404(Qarzdor.objects.select_related("hudud"), pk=pk)
    return render(request, "qarz/qarzdor_karta.html", {
        "qarzdor": qarzdor,
        "qarzlar": qarzdor.qarzlar.prefetch_related("qatorlar__mahsulot"),
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
        "qatorlar": qarz.qatorlar.select_related("mahsulot"),
        "mahsulotlar": mahsulotlar,
        "qator_manzili": reverse("qarz:qator_qoshish", args=[qarz.pk]),
        "yakun_manzili": reverse("qarz:qarz_yakunlash", args=[qarz.pk]),
        "oxirgi_kurs": oxirgi_kurs(),
        # Shu hujjatdan oldingi qarzi (hozir yozilayotgani hisobga olinmaydi)
        "oldingi_qarz": qarz.qarzdor.balans - qarz.jami,
        "oldingi_qarz_dollar": qarz.qarzdor.balans_dollar - qarz.jami_dollar,
    })


def qator_qoshish(request, pk):
    """Qarzga tovar qatorini qo'shadi va ombordan ayiradi."""
    qarz = get_object_or_404(Qarz, pk=pk)
    if request.method != "POST":
        return redirect("qarz:qarz_tahrir", pk=qarz.pk)

    mahsulot = get_object_or_404(Mahsulot, pk=request.POST.get("mahsulot"))
    miqdor, xato = songa(request.POST.get("miqdor"), "Miqdor")
    if xato:
        messages.error(request, xato)
        return redirect("qarz:qarz_tahrir", pk=qarz.pk)

    try:
        ayir(mahsulot.pk, miqdor, f"Qarz #{qarz.pk} - {qarz.qarzdor.toliq_ism}")
    except OmborXatosi as xato:
        messages.error(request, str(xato))
        return redirect("qarz:qarz_tahrir", pk=qarz.pk)

    QarzQator.objects.create(qarz=qarz, mahsulot=mahsulot, miqdor=miqdor)
    return redirect("qarz:qarz_tahrir", pk=qarz.pk)


def qator_ochirish(request, pk):
    """Qatorni o'chiradi va tovarni omborga qaytaradi."""
    qator = get_object_or_404(QarzQator.objects.select_related("qarz"), pk=pk)
    qarz_pk = qator.qarz.pk
    if request.method == "POST":
        qaytar(qator.mahsulot_id, qator.miqdor, f"Qarz #{qarz_pk} dan qaytarildi")
        qator.delete()
        messages.success(request, "Qator o'chirildi, tovar omborga qaytdi.")
    return redirect("qarz:qarz_tahrir", pk=qarz_pk)


def qator_qaytarish(request, pk):
    """Qarzga olingan tovarni qaytarib berish — qisman ham bo'ladi.

    Qaytarilgan pul qarz summasidan ayriladi: mijoz olmagan mol uchun
    qarzdor bo'lib qolmaydi.
    """
    qator = get_object_or_404(QarzQator.objects.select_related("qarz__qarzdor", "mahsulot"),
                              pk=pk)
    qarz = qator.qarz

    if request.method != "POST":
        return render(request, "qaytarish.html", {
            "qator": qator,
            "hujjat": f"hujjat #{qarz.pk} · {qarz.qarzdor.toliq_ism}",
            "sana": qarz.sana,
            "jami": qarz.sof_jami,
            "jami_dollar": qarz.sof_jami_dollar,
            "orqaga": reverse("qarz:qarzdor_karta", args=[qarz.qarzdor_id]),
        })

    miqdor, summa, summa_dollar, xato = qaytarishni_oqi(request.POST, qator)
    if xato:
        messages.error(request, xato)
        return redirect("qarz:qator_qaytarish", pk=qator.pk)

    if summa > qarz.sof_jami or summa_dollar > qarz.sof_jami_dollar:
        messages.error(request, "Qaytarilgan pul qarz summasidan ko'p bo'lmasin.")
        return redirect("qarz:qator_qaytarish", pk=qator.pk)

    qaytar(qator.mahsulot_id, miqdor,
           f"Qarz #{qarz.pk} dan qaytarildi — {qarz.qarzdor.toliq_ism}",
           HarakatTuri.QAYTARISH)
    qator.qaytarilgan += miqdor
    qator.save(update_fields=["qaytarilgan"])

    qarz.qaytarilgan_summa += summa
    qarz.qaytarilgan_summa_dollar += summa_dollar
    qarz.save(update_fields=["qaytarilgan_summa", "qaytarilgan_summa_dollar"])

    messages.success(request, "Qaytarish yozildi, tovar omborga qaytdi.")
    return redirect("qarz:qarzdor_karta", pk=qarz.qarzdor_id)


def oldindanni_oqi(post, jami, jami_dollar):
    """Qarz yakunlanayotganda darrov to'langan pulni o'qiydi.

    Hujjat summasidan ortiq to'lash mumkin emas — aks holda qarzdorning
    balansi manfiyga ketib, «qarzi −5 000 so'm» degan ma'nosiz son chiqadi.

    (oldindan, oldindan_dollar, xato) qaytaradi.
    """
    oldindan, xato = pulga(post.get("oldindan"), "Oldindan to'lov (so'm)")
    if xato:
        return None, None, xato

    oldindan_dollar, xato = pulga(post.get("oldindan_dollar"), "Oldindan to'lov (dollar)")
    if xato:
        return None, None, xato

    if oldindan > jami:
        return None, None, (f"Oldindan to'lov qarz summasidan ko'p: {pul_matn(oldindan)} > "
                            f"{pul_matn(jami)} so'm.")
    if oldindan_dollar > jami_dollar:
        return None, None, (f"Oldindan to'lov dollarlik summadan ko'p: "
                            f"{pul_matn(oldindan_dollar)} > {pul_matn(jami_dollar)} $.")
    return oldindan, oldindan_dollar, None


def oldindan_yoz(qarz, oldindan, oldindan_dollar):
    """Oldindan to'langan pulni oddiy `Tolov` bo'lib yozadi.

    Alohida maydon emas, chunki balans hisobi bitta joyda — to'lovlar
    yig'indisida — qolishi kerak. `qarz` to'ldirilgani uchun kartochkada
    qaysi hujjatga tushgani ko'rinadi.

    Ekranda ko'rsatish uchun qisqa matn qaytaradi.
    """
    yozilgan = []
    for summa, valyuta, belgi in ((oldindan, Valyuta.SOM, "so'm"),
                                  (oldindan_dollar, Valyuta.DOLLAR, "$")):
        if summa > 0:
            Tolov.objects.create(qarzdor=qarz.qarzdor, qarz=qarz, summa=summa,
                                 valyuta=valyuta, izoh=f"Hujjat #{qarz.pk} — oldindan")
            yozilgan.append(f"{pul_matn(summa)} {belgi}")
    return " va ".join(yozilgan)


def qarz_yakunlash(request, pk):
    """Qarz hujjatini yopadi. Qarz summasi qo'lda kiritiladi.

    Narx qatorlarda yozilmaydi — savdolashib kelishilgan summa
    kalkulyatorda hisoblanib, shu yerda yoziladi. So'mlik va dollarlik
    qism alohida: qarzdorning ikkita mustaqil hisobi bo'ladi.
    """
    qarz = get_object_or_404(Qarz, pk=pk)
    if request.method == "POST":
        if qarz.qatorlar_soni == 0:
            qarzdor_pk = qarz.qarzdor_id
            qarz.delete()
            messages.info(request, "Bo'sh qarz bekor qilindi.")
            return redirect("qarz:qarzdor_karta", pk=qarzdor_pk)

        jami, jami_dollar, kurs, xato = summalarni_oqi(request.POST, "Qarz")
        if xato:
            messages.error(request, xato)
            return redirect("qarz:qarz_tahrir", pk=qarz.pk)

        oldindan, oldindan_dollar, xato = oldindanni_oqi(request.POST, jami, jami_dollar)
        if xato:
            messages.error(request, xato)
            return redirect("qarz:qarz_tahrir", pk=qarz.pk)

        qarz.jami = jami
        qarz.jami_dollar = jami_dollar
        qarz.kurs = kurs
        qarz.izoh = request.POST.get("izoh", "")[:200]
        qarz.yakunlangan = True
        qarz.save(update_fields=["jami", "jami_dollar", "kurs", "izoh", "yakunlangan"])

        tolandi = oldindan_yoz(qarz, oldindan, oldindan_dollar)
        messages.success(request, "Qarz daftarga yozildi." +
                         (f" Oldindan to'langani: {tolandi}." if tolandi else ""))
    return redirect("qarz:qarzdor_karta", pk=qarz.qarzdor_id)


def tolov_qoshish(request, qarzdor_pk):
    """Qarzdor to'lov qildi.

    To'lov o'z valyutasidagi qarzni yopadi: so'm to'lov so'm qarzini, dollar
    to'lov dollar qarzini. Qarzdan ortiq to'lov qabul qilinmaydi — aks holda
    balans manfiyga ketib, «Qolgan qarzi −5 000 so'm» kabi ma'nosiz son chiqadi.
    """
    qarzdor = get_object_or_404(Qarzdor, pk=qarzdor_pk)
    if request.method == "POST":
        form = TolovForm(request.POST)
        if not form.is_valid():
            messages.error(request, "To'lov summasi xato.")
            return redirect("qarz:qarzdor_karta", pk=qarzdor.pk)

        summa = form.cleaned_data["summa"]
        dollarmi = form.cleaned_data["valyuta"] == Valyuta.DOLLAR
        pul = "dollar" if dollarmi else "so'm"
        qoldiq = qarzdor.balans_dollar if dollarmi else qarzdor.balans

        if summa <= 0:
            messages.error(request, "To'lov summasi noldan katta bo'lishi kerak.")
        elif qoldiq <= 0:
            messages.error(request, f"{qarzdor.toliq_ism} ning {pul} qarzi yo'q — "
                                    f"to'lov yozishning hojati yo'q.")
        elif summa > qoldiq:
            messages.error(request, f"Qolgan {pul} qarzi {pul_matn(qoldiq)}. "
                                    f"Bundan ortiq to'lov yozib bo'lmaydi.")
        else:
            tolov = form.save(commit=False)
            tolov.qarzdor = qarzdor
            tolov.save()
            qolgan = qarzdor.balans_dollar if dollarmi else qarzdor.balans
            if qolgan > 0:
                messages.success(request, f"To'lov qabul qilindi. "
                                          f"Qolgan {pul} qarzi {pul_matn(qolgan)}.")
            else:
                messages.success(request, f"To'lov qabul qilindi. {pul.capitalize()} "
                                          f"qarzi to'liq yopildi.")
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
    """Qarzdorlar bo'limi — uch ko'rinishda.

    Boshida ikkita katta tugma: butun ro'yxat yoki hududlar. «Hududlar»
    bosilsa har bir hudud alohida tugma bo'lib chiqadi, hudud bosilsa
    o'sha hududning qarzdorlari ko'rinadi. Do'konda qarzdorlar hudud
    bo'yicha eslanadi, shuning uchun shu yo'l qisqaroq.
    """
    hudud_id = request.GET.get("hudud", "")
    korinish = request.GET.get("korinish", "")

    if hudud_id:
        korinish = "royxat"
    elif korinish not in ("royxat", "hududlar"):
        korinish = "tanlov"

    hudud = None
    qarzdorlar = []
    jami_balans = Decimal("0")
    jami_balans_dollar = Decimal("0")
    kartalar = []

    if korinish == "royxat":
        tanlangan = Qarzdor.objects.select_related("hudud")
        if hudud_id:
            hudud = get_object_or_404(Hudud, pk=hudud_id)
            tanlangan = tanlangan.filter(hudud=hudud)
        qarzdorlar = sorted(tanlangan, key=lambda q: (q.balans, q.balans_dollar), reverse=True)
        jami_balans = sum((q.balans for q in qarzdorlar), Decimal("0"))
        jami_balans_dollar = sum((q.balans_dollar for q in qarzdorlar), Decimal("0"))

    elif korinish == "hududlar":
        kartalar = hudud_kartalari()

    return render(request, "qarz/qarzdorlar.html", {
        "korinish": korinish,
        "qarzdorlar": qarzdorlar,
        "hudud": hudud,
        "hudud_kartalari": kartalar,
        "jami_balans": jami_balans,
        "jami_balans_dollar": jami_balans_dollar,
    })
