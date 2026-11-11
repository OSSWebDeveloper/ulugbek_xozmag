# -*- coding: utf-8 -*-
"""Har bir sahifaga qo'shiladigan umumiy qiymatlar.

Hozircha bittasi — dastur versiyasi. U yon menyu pastida ko'rinib turadi:
mijoz «qaysi versiya ishlayapti?» deganda aytishi oson bo'ladi.

Fayl har safar o'qiladi (o'zgargan bo'lsagina), chunki `versiya.py` bilan
yangilangandan keyin sayt qayta ishga tushirilmasa ham to'g'ri raqam
ko'rinishi kerak.
"""
from django.conf import settings

_xotira = {"vaqt": None, "qiymat": None}


def _oqi():
    yol = getattr(settings, "VERSIYA_FAYL", None)
    if yol is None or not yol.exists():
        return getattr(settings, "VERSIYA", "")
    vaqt = yol.stat().st_mtime
    if _xotira["vaqt"] != vaqt:
        _xotira["vaqt"] = vaqt
        _xotira["qiymat"] = yol.read_text(encoding="utf-8").strip()
    return _xotira["qiymat"]


def versiya(request):
    from django.utils.functional import SimpleLazyObject
    from sotuv.chek import mahalliymi
    # Brauzerdan chiqariladigan chek: faqat base.html so'raganda va bir marta
    # olinadi — sahifa yangilansa chek ikkinchi marta chiqmaydi.
    chek = SimpleLazyObject(lambda: request.session.pop("brauzer_chek", None)
                            if hasattr(request, "session") else None)
    return {"versiya": _oqi(), "server_kompyuteri": mahalliymi(request), "brauzer_chek": chek}
