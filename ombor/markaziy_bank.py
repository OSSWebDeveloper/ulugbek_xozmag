"""Dollar kursini O'zbekiston Markaziy bankidan oladi.

Do'kon internetsiz ham ishlashi kerak, shuning uchun:

* kurs **kuniga bir marta** so'raladi va bazaga yoziladi (`DollarKursi`);
* so'rov qisqa kutish bilan ketadi — sayt bank javobini kutib turmaydi;
* olib bo'lmasa oxirgi ma'lum kurs ishlatiladi, hech qanday xatolik
  chiqmaydi: kassir kursni baribir qo'lda yozib qo'ya oladi.

Bank JSON i bitta ro'yxat qaytaradi:
`[{"Ccy": "USD", "Rate": "12345.67", "Date": "22.09.2026", ...}]`
"""
import json
import logging
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from urllib.error import URLError
from urllib.request import urlopen

from django.utils import timezone

from .models import DollarKursi

MANZIL = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/USD/"
KUTISH = 3                              # soniya — bankni uzoq kutmaymiz
QAYTA_URINISH = timedelta(minutes=60)   # olib bo'lmasa qancha vaqtdan keyin qayta urinish

logger = logging.getLogger(__name__)


def bankdan_sora():
    """Tarmoqqa chiqib kursni oladi. Kurs yoki None qaytaradi.

    Sinovlar shu funksiyani almashtiradi — tarmoqqa chiqmaydi.
    """
    try:
        with urlopen(MANZIL, timeout=KUTISH) as javob:
            malumot = json.loads(javob.read().decode("utf-8"))
        # Bank tiyinigacha aytadi (11809.82) — do'konda butun so'm ishlatiladi
        kurs = Decimal(str(malumot[0]["Rate"])).quantize(Decimal("1"),
                                                         rounding=ROUND_HALF_UP)
    except (URLError, TimeoutError, OSError, ValueError, TypeError,
            KeyError, IndexError, InvalidOperation) as xato:
        logger.warning("Markaziy bank kursi olinmadi: %s", xato)
        return None
    return kurs if kurs > 0 else None


def bugungi_kurs():
    """Markaziy bank kursi: bazadagisi, kerak bo'lsa yangisi so'raladi.

    Bugungisi bo'lmasa oldingi kunlarnikini qaytaradi — bir oy oldingi
    qo'lda yozilgan kursdan ko'ra kechagi bank kursi to'g'riroq.
    """
    bugun = timezone.localdate()
    yozuv = DollarKursi.objects.filter(sana=bugun).first()
    if yozuv and yozuv.kurs > 0:
        return yozuv.kurs

    # Yaqinda urinib ko'rilgan bo'lsa qayta urinmaymiz — sayt sekinlashmasin
    yaqinda = yozuv and timezone.now() - yozuv.urinish < QAYTA_URINISH
    if not yaqinda:
        kurs = bankdan_sora()
        if kurs:
            DollarKursi.objects.update_or_create(sana=bugun, defaults={"kurs": kurs})
            return kurs
        # Urinish sanasi yozilib qolsin (kurs 0 — "olib bo'lmadi" degani)
        DollarKursi.objects.update_or_create(sana=bugun, defaults={"kurs": Decimal("0")})

    oldingi = DollarKursi.objects.filter(kurs__gt=0).order_by("-sana").first()
    return oldingi.kurs if oldingi else None
