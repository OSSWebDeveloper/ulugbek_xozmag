"""Rang cheki kassada.

Mijoz rang mashinasi yonida chop etilgan chekni kassaga olib keladi. Kassir
skanerlaydi — chekdagi baza bo'yoq miqdori bilan hujjatga tushadi (sotuv yoki
qarz; ikkalasining kassa ekrani bir xil). Chek o'sha hujjatga bog'lanadi:

- ikkinchi marta skanerlansa qabul qilinmaydi (bo'yoq ombordan ikki marta
  ayrilmasin);
- hujjat yakunlansa chek «to'landi» / «qarzga yozildi» bo'ladi;
- qator o'chirilsa yoki sotuv bekor qilinsa chek yana bo'sh qoladi.

Kodni tanish `ombor/kod.py` da (format qoidalari bitta joyda), buyurtmani
topish esa shu yerda.
"""
from ombor.kod import Natija

from .models import Buyurtma


def chekni_top(raqam):
    """Rang cheki raqami bo'yicha kassa uchun `Natija`: baza va uning miqdori."""
    buyurtma = (Buyurtma.objects.select_related("baza", "sotuv", "qarz")
                .filter(pk=raqam).first())
    if buyurtma is None:
        return Natija(None, None, "rang", f"Rang cheki #{raqam} topilmadi.")
    xato = buyurtma.kassa_xatosi()
    if xato:
        return Natija(None, None, "rang", xato, buyurtma)
    return Natija(buyurtma.baza, buyurtma.miqdor, "rang", None, buyurtma)


def chekni_oqi(post, mahsulot):
    """Kassa formasi bilan kelgan rang chekini tekshiradi.

    (buyurtma, xato) qaytaradi. Formada rang cheki bo'lmasa (oddiy tovar)
    ikkalasi ham None. Chek boshqa tovarga tegishli bo'lsa ham None — kassir
    chekni skanerlab, keyin ro'yxatdan boshqa tovarni tanlagan bo'lishi mumkin.
    """
    raqam = (post.get("rang_chek") or "").strip()
    if not raqam.isdigit():
        return None, None
    buyurtma = (Buyurtma.objects.select_related("sotuv", "qarz")
                .filter(pk=raqam, baza=mahsulot).first())
    if buyurtma is None:
        return None, None
    xato = buyurtma.kassa_xatosi()
    return (None, xato) if xato else (buyurtma, None)


def boglash(buyurtma, sotuv=None, qarz=None):
    """Chekni kassa hujjatiga bog'laydi — endi u «kassada»."""
    buyurtma.sotuv, buyurtma.qarz = sotuv, qarz
    buyurtma.save(update_fields=["sotuv", "qarz"])


def ajratish(sotuv=None, qarz=None, mahsulot_id=None):
    """Hujjatdan chiqarilgan chekni bo'shatadi: qator o'chirildi yoki sotuv bekor.

    `mahsulot_id` berilsa faqat o'sha baza bo'yoqning cheklari.
    """
    if sotuv is not None:
        cheklar = Buyurtma.objects.filter(sotuv=sotuv)
    elif qarz is not None:
        cheklar = Buyurtma.objects.filter(qarz=qarz)
    else:
        return
    if mahsulot_id:
        cheklar = cheklar.filter(baza_id=mahsulot_id)
    cheklar.update(sotuv=None, qarz=None)


def kassa_xabari(buyurtma):
    """Kassirga: chekda qancha to'lanadi (summani «Jami» ga shu bo'yicha yozadi)."""
    from .templatetags.rang import tolov_matni
    return f"Rang cheki #{buyurtma.pk} — {buyurtma.rang_kodi}. To'lanadi: {tolov_matni(buyurtma)}."
