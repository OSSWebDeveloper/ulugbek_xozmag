"""Ombor qoldig'ini o'zgartiruvchi umumiy amallar.

Qarz ham, naqd sotuv ham shu funksiyalardan foydalanadi — qoldiq bir joyda
o'zgaradi va har bir o'zgarish tarixga yoziladi.
"""
from collections import namedtuple
from decimal import Decimal, InvalidOperation

from django.db import transaction

from .models import HarakatTuri, Mahsulot, OmborHarakati


class OmborXatosi(Exception):
    """Ombordagi qoldiq yetmaganda ko'tariladi."""


def tozala(qiymat):
    """Kiritilgan matnni songa tayyorlaydi.

    Maydonlarda son chiroyli ko'rinadi — «12 800», «250 000» — shuning uchun
    ajratuvchi bo'shliqlar (oddiy va uzilmas) olib tashlanadi, vergul esa
    nuqtaga aylantiriladi: do'konda kasr vergul bilan yoziladi.
    """
    matn = "" if qiymat is None else str(qiymat)
    for bosh in (" ", " ", " ", "	"):
        matn = matn.replace(bosh, "")
    return matn.replace(",", ".").strip()


def songa(qiymat, nom):
    """Matnni Decimal ga aylantiradi. (son, xato_matni) qaytaradi."""
    try:
        son = Decimal(tozala(qiymat))
    except (InvalidOperation, AttributeError, TypeError):
        return None, f"{nom} xato kiritildi."
    if son <= 0:
        return None, f"{nom} noldan katta bo'lishi kerak."
    return son, None


def pulga(qiymat, nom):
    """Pul maydonini o'qiydi. Bo'sh bo'lsa 0, manfiy bo'lsa xato.

    `songa()` dan farqi: bu yerda bo'sh qoldirish mumkin — chekda faqat so'm
    yoki faqat dollar bo'lishi mumkin, ikkinchisi bo'sh turadi.
    """
    matn = tozala(qiymat)
    if not matn:
        return Decimal("0"), None
    try:
        son = Decimal(matn)
    except (InvalidOperation, AttributeError, TypeError):
        return None, f"{nom} xato kiritildi."
    if son < 0:
        return None, f"{nom} manfiy bo'lmaydi."
    return son, None


Kurs = namedtuple("Kurs", "qiymat manba")


def qolda_yozilgan_kurs():
    """Oxirgi marta hujjatga qo'lda yozilgan kurs.

    Modellar shu yerda import qilinadi — ombor ilovasi qarz va sotuvga
    bog'lanib qolmasin.
    """
    from qarz.models import Qarz
    from sotuv.models import Sotuv

    oxirgilar = []
    for model in (Qarz, Sotuv):
        hujjat = model.objects.filter(kurs__gt=0).order_by("-sana").first()
        if hujjat:
            oxirgilar.append((hujjat.sana, hujjat.kurs))
    return max(oxirgilar)[1] if oxirgilar else None


def oxirgi_kurs():
    """Kassada tayyor turadigan dollar kursi.

    Avval Markaziy bank kursi olinadi — klient shuni so'radi. Internet
    bo'lmasa oxirgi marta qo'lda yozilgan kurs qoladi. Ikkalasi ham bo'lmasa
    maydon bo'sh turadi, kassir o'zi yozadi.

    `Kurs(qiymat, manba)` yoki None qaytaradi — manba ekranda ko'rsatiladi.
    """
    from .markaziy_bank import bugungi_kurs

    bank = bugungi_kurs()
    if bank:
        return Kurs(bank, "Markaziy bank kursi")

    qolda = qolda_yozilgan_kurs()
    if qolda:
        return Kurs(qolda, "oxirgi yozilgan kurs")
    return None


def qaytarishni_oqi(post, qator):
    """Qaytarib berish formasini o'qiydi.

    Qaytarish to'liq bo'lmasligi mumkin: 20 qop sementning 5 tasi qaytishi
    ham normal. Shuning uchun miqdor sotilganidan oshmasligi tekshiriladi.
    Pul so'm va dollarda alohida yoziladi — boshqa joydagidek qo'lda.

    (miqdor, summa, summa_dollar, xato) qaytaradi.
    """
    from .models import tekis_matn

    miqdor, xato = songa(post.get("miqdor"), "Qaytarilgan miqdor")
    if xato:
        return None, None, None, xato
    if miqdor > qator.qolgan_miqdor:
        return None, None, None, (
            f"Bunchasi sotilmagan: ko'pi bilan {tekis_matn(qator.qolgan_miqdor)} "
            f"{qator.birlik} qaytarish mumkin."
        )

    summa, xato = pulga(post.get("summa"), "Qaytarilgan pul (so'm)")
    if xato:
        return None, None, None, xato

    summa_dollar, xato = pulga(post.get("summa_dollar"), "Qaytarilgan pul (dollar)")
    if xato:
        return None, None, None, xato

    return miqdor, summa, summa_dollar, None


def summalarni_oqi(post, nomi="Jami", majburiy=True):
    """Kassadagi so'm / dollar / kurs maydonlarini o'qiydi.

    So'm va dollar **qo'shilmaydi** — ikkalasi alohida yoziladi. Bittasi
    to'ldirilsa yetadi; dollar yozilgan bo'lsa o'sha kungi kurs ham so'raladi,
    chunki keyin bu summa qaysi kursda olingani kerak bo'ladi.

    `majburiy=False` — ikkala maydon ham bo'sh qolishi mumkin. Naqd sotuvda
    pulning hammasi qarzga yozilsa shunday bo'ladi: kassaga hech narsa
    tushmaydi, summa qarz hujjatiga o'tadi.

    (jami, jami_dollar, kurs, xato) qaytaradi.
    """
    jami, xato = pulga(post.get("jami"), f"{nomi} (so'm)")
    if xato:
        return None, None, None, xato

    jami_dollar, xato = pulga(post.get("jami_dollar"), f"{nomi} (dollar)")
    if xato:
        return None, None, None, xato

    kurs, xato = pulga(post.get("kurs"), "Dollar kursi")
    if xato:
        return None, None, None, xato

    if majburiy and jami <= 0 and jami_dollar <= 0:
        return None, None, None, f"{nomi} summasini yozing — so'mda yoki dollarda."
    if jami_dollar > 0 and kurs <= 0:
        return None, None, None, "Dollar summasi yozildi — o'sha kungi kursni ham yozing."
    return jami, jami_dollar, kurs, None


@transaction.atomic
def ayir(mahsulot_id, miqdor, izoh):
    """Ombordan tovar ayiradi. Qoldiq yetmasa OmborXatosi ko'tariladi."""
    mahsulot = Mahsulot.objects.select_for_update().get(pk=mahsulot_id)
    if miqdor > mahsulot.qoldiq:
        raise OmborXatosi(
            f"Omborda yetarli emas. {mahsulot.nom}: "
            f"{mahsulot.qoldiq_son} {mahsulot.birlik} qoldi."
        )
    mahsulot.qoldiq -= miqdor
    mahsulot.save(update_fields=["qoldiq"])
    OmborHarakati.objects.create(
        mahsulot=mahsulot, tur=HarakatTuri.CHIQIM, miqdor=miqdor, izoh=izoh,
    )
    return mahsulot


@transaction.atomic
def hujjatga_qosh(qatorlar, mahsulot, miqdor, izoh):
    """Tovarni chek yoki qarz hujjatiga qo'shadi va ombordan ayiradi.

    Bir xil tovar ikkinchi qator bo'lib tushmaydi — mavjud qatorning miqdori
    oshadi: skaner bilan uchta rozetka o'qilsa chekda «Rozetka 3 dona» turadi.
    `qatorlar` — hujjatning qatorlar menejeri (`sotuv.qatorlar`,
    `qarz.qatorlar`). Qoldiq yetmasa OmborXatosi — hech narsa yozilmaydi.
    Qo'shilgan (yoki kattalashgan) qatorni qaytaradi.
    """
    ayir(mahsulot.pk, miqdor, izoh)
    qator = qatorlar.filter(mahsulot=mahsulot).first()
    if qator is None:
        return qatorlar.create(mahsulot=mahsulot, miqdor=miqdor)
    qator.miqdor += miqdor
    qator.save(update_fields=["miqdor"])
    return qator


@transaction.atomic
def qaytar(mahsulot_id, miqdor, izoh, tur=HarakatTuri.KIRIM):
    """Tovarni omborga qaytaradi.

    Ikki holatda ishlatiladi: qator o'chirilganda (oddiy kirim) va mijoz
    tovarni qaytarib berganda (`HarakatTuri.QAYTARISH`) — tarixda ikkisi
    ajralib tursin, do'kon nima qaytganini ko'rishi kerak.
    """
    mahsulot = Mahsulot.objects.select_for_update().get(pk=mahsulot_id)
    mahsulot.qoldiq += miqdor
    mahsulot.save(update_fields=["qoldiq"])
    OmborHarakati.objects.create(
        mahsulot=mahsulot, tur=tur, miqdor=miqdor, izoh=izoh,
    )
    return mahsulot


# ---------- Kassadagi tovar tanlash oynasi ----------

OYNA_SONI = 60       # oynada darrov ko'rinadigan kartalar (eng ko'p sotiladiganlari)
QIDIRUV_SONI = 30    # qidiruvda serverdan keladigan natijalar


def oyna_tovarlari():
    """Tovar tanlash oynasidagi kartalar — eng ko'p sotiladigan 60 tasi.

    Omborda 10 000 dan ortiq tovar bor (Excel'dan keladi): hammasini sahifaga
    chizsak kassa 10 soniyada ochilardi. Qolgani qidiruv orqali serverdan
    keladi (`/ombor/tovar-qidir/`), kod va skaner esa avvalgidek `/ombor/kod/`.
    """
    from django.db.models import Count
    return list(Mahsulot.objects.filter(faol=True)
                .annotate(sotilgan=Count("sotuv_qatorlari", distinct=True)
                          + Count("qarz_qatorlari", distinct=True))
                .order_by("-sotilgan", "nom")[:OYNA_SONI])


def karta_malumoti(m):
    """Oynadagi kartaning `data-*` qiymatlari — JS server javobidan ham shu kartani yasaydi."""
    from qarz.templatetags.xozmag import narxi, tekis
    return {
        "id": m.pk, "nom": m.nom, "kod": m.kod, "qisqa": m.qisqa_kod,
        "qoldiq": tekis(m.qoldiq), "birlik": m.birlik, "ikkinchi": m.qadoq_matni,
        "valyuta": m.valyuta_belgisi, "narx": narxi(m), "yoq": m.qoldiq <= 0,
    }
