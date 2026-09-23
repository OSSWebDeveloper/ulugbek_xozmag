"""Sotuv ko'rinishlari: kassa, yakunlash, qaytarish va kunlik ro'yxat."""
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import F, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from ombor.models import HarakatTuri, Mahsulot
from ombor.xizmat import (OmborXatosi, ayir, oxirgi_kurs, pulga, qaytar,
                          qaytarishni_oqi, songa, summalarni_oqi)

from qarz.forms import QarzdorForm
from qarz.models import Qarz, Qarzdor
from qarz.templatetags.xozmag import pul, tekis

from .models import Sotuv, SotuvQator

NOL = Decimal("0")


def qarz_matn(summa, summa_dollar):
    """«200 000 so'm» yoki «200 000 so'm va 15,5 $» — xabarda ko'rinadi."""
    bolaklar = []
    if summa > 0:
        bolaklar.append(f"{pul(summa)} so'm")
    if summa_dollar > 0:
        bolaklar.append(f"{tekis(summa_dollar)} $")
    return " va ".join(bolaklar)


def kun_manzili(sotuv):
    """Chek turgan kunning ro'yxati — yakunlangan chek shu yerda ko'rinadi."""
    kun = timezone.localtime(sotuv.sana).date()
    return reverse("sotuv:royxat") + f"?kun={kun:%Y-%m-%d}"


def yopiq_chek(request, sotuv):
    """Yakunlangan yoki bekor qilingan chekka tegilmaydi.

    Brauzerning «Orqaga» tugmasi yopilgan chekni yana ochib beradi, tugma
    ikki marta bosilishi ham mumkin. Tekshiruv bo'lmasa yopilgan chekka tovar
    tushib qolar yoki qarz ikki marta yozilardi. Chek ochiq bo'lsa None,
    yopiq bo'lsa o'sha kunning ro'yxatiga yo'naltirish qaytaradi.
    """
    if sotuv.ochiqmi:
        return None
    holat = "bekor qilingan" if sotuv.bekor_qilingan else "yakunlangan"
    messages.info(request, f"Chek #{sotuv.pk} {holat} — uni endi o'zgartirib bo'lmaydi.")
    return redirect(kun_manzili(sotuv))


def sotuv_boshlash(request):
    """Yangi (yoki tugallanmagan) sotuv chekini ochadi."""
    sotuv = Sotuv.objects.filter(yakunlangan=False, bekor_qilingan=False).first()
    if sotuv is None:
        sotuv = Sotuv.objects.create()
    return redirect("sotuv:tahrir", pk=sotuv.pk)


def tahrir(request, pk):
    """Sotuv ekrani (kassa ko'rinishi)."""
    sotuv = get_object_or_404(Sotuv, pk=pk)
    yopiq = yopiq_chek(request, sotuv)
    if yopiq:
        return yopiq
    return render(request, "sotuv/tahrir.html", {
        "sotuv": sotuv,
        "qatorlar": sotuv.qatorlar.select_related("mahsulot"),
        "mahsulotlar": Mahsulot.objects.filter(faol=True),
        "qator_manzili": reverse("sotuv:qator_qoshish", args=[sotuv.pk]),
        "yakun_manzili": reverse("sotuv:yakunlash", args=[sotuv.pk]),
        "oxirgi_kurs": oxirgi_kurs(),
        # Pul yetmay qolganda ochiladigan oynacha uchun — sahifa almashmasin
        "qarzdorlar": Qarzdor.objects.select_related("hudud"),
        "qarzdor_form": QarzdorForm(),
    })


def qator_qoshish(request, pk):
    """Sotuvga tovar qo'shadi va ombordan ayiradi."""
    sotuv = get_object_or_404(Sotuv, pk=pk)
    if request.method != "POST":
        return redirect("sotuv:tahrir", pk=sotuv.pk)
    yopiq = yopiq_chek(request, sotuv)
    if yopiq:
        return yopiq

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
    sotuv = qator.sotuv
    if request.method == "POST":
        yopiq = yopiq_chek(request, sotuv)
        if yopiq:
            return yopiq
        qaytar(qator.mahsulot_id, qator.miqdor, f"Sotuv #{sotuv.pk} dan qaytarildi")
        qator.delete()
        messages.success(request, "Qator o'chirildi, tovar omborga qaytdi.")
    return redirect("sotuv:tahrir", pk=sotuv.pk)


def qarzni_oqi(post, jami, jami_dollar):
    """Chekning qarzga qoladigan qismini hisoblaydi.

    Mijozda pul yetmasa «Jami» ikkiga bo'linadi: mijoz bergan pul
    (`tolandi`) va qolgani — qarz. Oynachadan to'langan pul keladi, qarz
    shu yerda hisoblanadi: qarz = jami − tolandi. Shunday qilib kassir
    «Jami» ni keyin o'zgartirsa ham hisob o'z-o'zidan to'g'ri qoladi.

    (qarzdor, qarz_jami, qarz_jami_dollar, xato) qaytaradi. Qarzdor
    tanlanmagan bo'lsa qarz nol — oddiy naqd sotuv.
    """
    qarzdor_pk = (post.get("qarzdor") or "").strip()
    if not qarzdor_pk:
        return None, NOL, NOL, None
    if "tolandi" not in post:
        # Yangilanishdan oldin ochilgan sahifa qarzni boshqacha yuborardi
        return None, None, None, "Sahifa eskirgan — uni yangilab, qarzni qaytadan tanlang."

    qarzdor = Qarzdor.objects.filter(pk=qarzdor_pk).first()
    if qarzdor is None:
        return None, None, None, "Qarzdor topilmadi — qaytadan tanlang."

    tolandi, xato = pulga(post.get("tolandi"), "To'langan pul (so'm)")
    if xato:
        return None, None, None, xato
    tolandi_dollar, xato = pulga(post.get("tolandi_dollar"), "To'langan pul (dollar)")
    if xato:
        return None, None, None, xato

    if tolandi > jami:
        return None, None, None, (f"Mijoz bergan pul chek summasidan ko'p: "
                                  f"{pul(tolandi)} > {pul(jami)} so'm.")
    if tolandi_dollar > jami_dollar:
        return None, None, None, (f"Mijoz bergan dollar chek summasidan ko'p: "
                                  f"{tekis(tolandi_dollar)} > {tekis(jami_dollar)} $.")

    qarz_jami, qarz_jami_dollar = jami - tolandi, jami_dollar - tolandi_dollar
    if qarz_jami <= 0 and qarz_jami_dollar <= 0:
        return None, None, None, ("Chek to'liq to'langan — qarzga hech narsa qolmadi. "
                                  "«Qarzga» dagi tanlovni olib tashlang.")
    return qarzdor, qarz_jami, qarz_jami_dollar, None


def yakunlash(request, pk):
    """Sotuvni yopadi. Chek summasi qo'lda kiritiladi.

    Summa hisoblanmaydi: savdolashib narx o'zgaradi (183 000 -> 180 000),
    shuning uchun kassir kalkulyatordagi sonni o'zi yozadi. So'mlik va
    dollarlik qism alohida yoziladi, qo'shilmaydi.

    «Jami» — chekning **to'liq** summasi. Mijozda pul yetmasa u ikkiga
    bo'linadi: chekka **naqd olingan pul** yoziladi (kunlik tushum shundan
    chiqadi), qolgani esa qarz hujjatiga o'tadi. Tovarlar chekda qolgani
    uchun qarz hujjatining qatorlari bo'lmaydi — ombor ikki marta kamaymaydi.
    """
    sotuv = get_object_or_404(Sotuv, pk=pk)
    if request.method != "POST":
        return redirect("sotuv:tahrir", pk=sotuv.pk)
    yopiq = yopiq_chek(request, sotuv)
    if yopiq:
        return yopiq

    if sotuv.qatorlar_soni == 0:
        sotuv.delete()
        messages.info(request, "Bo'sh sotuv bekor qilindi.")
        return redirect("qarz:boshlash")

    jami, jami_dollar, kurs, xato = summalarni_oqi(request.POST)
    if xato:
        messages.error(request, xato)
        return redirect("sotuv:tahrir", pk=sotuv.pk)

    qarzdor, qarz_jami, qarz_jami_dollar, xato = qarzni_oqi(request.POST, jami, jami_dollar)
    if xato:
        messages.error(request, xato)
        return redirect("sotuv:tahrir", pk=sotuv.pk)

    naqd, naqd_dollar = jami - qarz_jami, jami_dollar - qarz_jami_dollar
    with transaction.atomic():
        # Faqat ochiq chek yopiladi: ikkinchi so'rov (tugma ikki bosilsa)
        # hech narsani o'zgartirmaydi va qarz ikkinchi marta yozilmaydi.
        yopildi = Sotuv.objects.filter(pk=sotuv.pk, yakunlangan=False,
                                       bekor_qilingan=False).update(
            jami=naqd, jami_dollar=naqd_dollar, kurs=kurs,
            yakunlangan=True, sana=timezone.now(),
        )
        if not yopildi:
            messages.info(request, f"Chek #{sotuv.pk} allaqachon yopilgan.")
            return redirect("sotuv:royxat")
        if qarzdor:
            Qarz.objects.create(
                qarzdor=qarzdor, sotuv=sotuv, jami=qarz_jami, jami_dollar=qarz_jami_dollar,
                kurs=kurs, izoh=f"Chek #{sotuv.pk} dan qolgan qarz", yakunlangan=True,
            )

    if qarzdor is None:
        messages.success(request, f"Chek #{sotuv.pk} yakunlandi — {qarz_matn(jami, jami_dollar)}.")
    else:
        tolangani = qarz_matn(naqd, naqd_dollar)
        messages.success(request, f"Chek #{sotuv.pk} yakunlandi. {qarz_matn(qarz_jami, qarz_jami_dollar)} "
                                  f"{qarzdor.toliq_ism} ning daftariga yozildi"
                                  + (f", naqd to'landi: {tolangani}." if tolangani else "."))
    return redirect("sotuv:royxat")


def bekor(request, pk):
    """Tugallanmagan sotuvni bekor qiladi, tovarlarni omborga qaytaradi.

    Chek o'chirilmaydi — bazada «bekor qilingan» bo'lib qoladi: keyin
    «o'sha kuni nima bo'lgan edi?» degan savolga javob beradigan yozuv kerak.
    Bo'sh chek (bironta tovar qo'shilmagani) esa yozuvga arzimaydi.
    """
    sotuv = get_object_or_404(Sotuv, pk=pk)
    if request.method == "POST":
        yopiq = yopiq_chek(request, sotuv)
        if yopiq:
            return yopiq
        if sotuv.qatorlar_soni == 0:
            sotuv.delete()
            messages.info(request, "Bo'sh chek bekor qilindi.")
            return redirect("qarz:boshlash")

        with transaction.atomic():
            for qator in sotuv.qatorlar.all():
                qaytar(qator.mahsulot_id, qator.qolgan_miqdor,
                       f"Sotuv #{sotuv.pk} bekor qilindi")
            sotuv.bekor_qilingan = True
            sotuv.sana = timezone.now()
            sotuv.save(update_fields=["bekor_qilingan", "sana"])
        messages.info(request, f"Chek #{sotuv.pk} bekor qilindi, tovarlar omborga qaytdi.")
    return redirect("qarz:boshlash")


def qaytarishni_taqsimla(sotuv, summa, summa_dollar):
    """Qaytarilgan pulni chekning qarz va naqd qismiga bo'ladi.

    Chekning bir qismi qarzga yozilgan bo'lsa pul **avval o'sha qarzdan**
    ayriladi: mijoz to'lamagan mol uchun unga pul qaytarilmaydi. Qarzdan
    ko'pi bilan qarzdorning hozirgi qarzicha ayriladi — u qarzini allaqachon
    to'lagan bo'lsa balansi manfiyga ketmasin. Qolgani qo'lga qaytariladi va
    chekning naqd summasidan (kunlik tushumdan) ayriladi.

    (qarzdan, qarzdan_dollar, naqddan, naqddan_dollar, xato) qaytaradi.
    """
    qarz = sotuv.qarz_hujjati
    chegara, chegara_dollar = NOL, NOL
    if qarz:
        chegara = max(min(qarz.sof_jami, qarz.qarzdor.balans), NOL)
        chegara_dollar = max(min(qarz.sof_jami_dollar, qarz.qarzdor.balans_dollar), NOL)

    qarzdan, qarzdan_dollar = min(summa, chegara), min(summa_dollar, chegara_dollar)
    naqddan, naqddan_dollar = summa - qarzdan, summa_dollar - qarzdan_dollar
    if naqddan > sotuv.sof_jami or naqddan_dollar > sotuv.sof_jami_dollar:
        return None, None, None, None, "Qaytarilgan pul chek summasidan ko'p bo'lmasin."
    return qarzdan, qarzdan_dollar, naqddan, naqddan_dollar, None


def qaytarish(request, pk):
    """Sotilgan tovarni qaytarib olish — qisman ham bo'ladi.

    20 qop sementning 15 tasi ishlatilib 5 tasi qaytsa: 5 qop omborga
    tushadi, qatorda «5 qaytarilgan» bo'lib qoladi, qaytarilgan pul esa
    chek summasidan ayriladi — chekda qarz bo'lsa avval qarzdan
    (`qaytarishni_taqsimla`). Chekning o'zi bazada turaveradi.
    """
    qator = get_object_or_404(SotuvQator.objects.select_related("sotuv", "mahsulot"), pk=pk)
    sotuv = qator.sotuv
    qarz = sotuv.qarz_hujjati

    # Qarzdor kartasidan kelinsa o'sha yerga qaytiladi
    keyin = request.GET.get("keyin", "")
    if not url_has_allowed_host_and_scheme(keyin, allowed_hosts={request.get_host()}):
        keyin = ""
    orqaga = keyin or kun_manzili(sotuv)

    if not sotuv.yakunlangan or sotuv.bekor_qilingan:
        messages.error(request, "Faqat yakunlangan chekdan tovar qaytarish mumkin.")
        return redirect(orqaga)

    if request.method != "POST":
        return render(request, "qaytarish.html", {
            "qator": qator,
            "hujjat": f"chek #{sotuv.pk}",
            "sana": sotuv.sana,
            "jami": sotuv.umumiy_jami,
            "jami_dollar": sotuv.umumiy_jami_dollar,
            "qarz": qarz,
            "orqaga": orqaga,
        })

    miqdor, summa, summa_dollar, xato = qaytarishni_oqi(request.POST, qator)
    if xato:
        messages.error(request, xato)
        return redirect(request.get_full_path())

    qarzdan, qarzdan_dollar, naqddan, naqddan_dollar, xato = qaytarishni_taqsimla(
        sotuv, summa, summa_dollar)
    if xato:
        messages.error(request, xato)
        return redirect(request.get_full_path())

    with transaction.atomic():
        qaytar(qator.mahsulot_id, miqdor, f"Chek #{sotuv.pk} dan qaytarildi",
               HarakatTuri.QAYTARISH)
        qator.qaytarilgan += miqdor
        qator.save(update_fields=["qaytarilgan"])

        sotuv.qaytarilgan_summa += naqddan
        sotuv.qaytarilgan_summa_dollar += naqddan_dollar
        sotuv.save(update_fields=["qaytarilgan_summa", "qaytarilgan_summa_dollar"])

        if qarzdan > 0 or qarzdan_dollar > 0:
            qarz.qaytarilgan_summa += qarzdan
            qarz.qaytarilgan_summa_dollar += qarzdan_dollar
            qarz.save(update_fields=["qaytarilgan_summa", "qaytarilgan_summa_dollar"])

    xabar = "Qaytarish yozildi, tovar omborga qaytdi."
    if qarzdan > 0 or qarzdan_dollar > 0:
        xabar += (f" {qarz_matn(qarzdan, qarzdan_dollar)} {qarz.qarzdor.toliq_ism} ning "
                  f"qarzidan ayrildi.")
    if naqddan > 0 or naqddan_dollar > 0:
        xabar += f" Qo'lga qaytarildi: {qarz_matn(naqddan, naqddan_dollar)}."
    messages.success(request, xabar)
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
                .select_related("qarz__qarzdor")
                .prefetch_related("qatorlar__mahsulot"))
    hisobda = sotuvlar.filter(bekor_qilingan=False)

    # Kunlik tushum ham ikki xil: so'm va dollar qo'shilmaydi. Qaytarib
    # berilgan pul tushumdan ayriladi. Qarzga qolgani tushum emas — alohida.
    yigindi = hisobda.aggregate(
        s=Sum(F("jami") - F("qaytarilgan_summa")),
        d=Sum(F("jami_dollar") - F("qaytarilgan_summa_dollar")),
        qs=Sum(F("qarz__jami") - F("qarz__qaytarilgan_summa")),
        qd=Sum(F("qarz__jami_dollar") - F("qarz__qaytarilgan_summa_dollar")),
    )

    return render(request, "sotuv/royxat.html", {
        "sotuvlar": sotuvlar,
        "sana": sana,
        "bugunmi": sana == bugun,
        "jami": yigindi["s"] or NOL,
        "jami_dollar": yigindi["d"] or NOL,
        "qarzga": yigindi["qs"] or NOL,
        "qarzga_dollar": yigindi["qd"] or NOL,
        "soni": hisobda.count(),
    })
