"""Ombor qoldig'ini o'zgartiruvchi umumiy amallar.

Qarz ham, naqd sotuv ham shu funksiyalardan foydalanadi — qoldiq bir joyda
o'zgaradi va har bir o'zgarish tarixga yoziladi.
"""
from decimal import Decimal, InvalidOperation

from django.db import transaction

from .models import HarakatTuri, Mahsulot, OmborHarakati


class OmborXatosi(Exception):
    """Ombordagi qoldiq yetmaganda ko'tariladi."""


def songa(qiymat, nom):
    """Matnni Decimal ga aylantiradi. (son, xato_matni) qaytaradi."""
    try:
        son = Decimal(str(qiymat).replace(",", ".").strip())
    except (InvalidOperation, AttributeError, TypeError):
        return None, f"{nom} xato kiritildi."
    if son <= 0:
        return None, f"{nom} noldan katta bo'lishi kerak."
    return son, None


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
def qaytar(mahsulot_id, miqdor, izoh):
    """Tovarni omborga qaytaradi (qator o'chirilganda)."""
    mahsulot = Mahsulot.objects.select_for_update().get(pk=mahsulot_id)
    mahsulot.qoldiq += miqdor
    mahsulot.save(update_fields=["qoldiq"])
    OmborHarakati.objects.create(
        mahsulot=mahsulot, tur=HarakatTuri.KIRIM, miqdor=miqdor, izoh=izoh,
    )
    return mahsulot
