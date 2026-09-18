# -*- coding: utf-8 -*-
"""Har bir sahifaga qo'shiladigan umumiy qiymatlar.

Hozircha bittasi — dastur versiyasi (`versiya.txt`). U yon menyu pastida
ko'rinib turadi: mijoz «qaysi versiya ishlayapti?» deganda aytishi oson bo'ladi.
"""
from django.conf import settings


def versiya(request):
    return {"versiya": getattr(settings, "VERSIYA", "")}
