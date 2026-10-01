"""Ranglar ro'yxatini matndan yuklash.

Soruda'dan, Excel'dan yoki bloknotdan nusxa olingan ro'yxat sahifadagi
maydonga qo'yiladi. Har qatorda bitta rang, kod — birinchi ustunda:

    RAL 3020;Yo'l qizil;#CC0605

Ajratuvchi — nuqtali vergul, tabulyatsiya (Excel'dan nusxa) yoki vergul.
Rang (#RRGGBB) ixtiyoriy va istalgan ustunda turishi mumkin; qolgan
ustunlar nomga qo'shiladi. Sarlavha qatori («Kod;Nomi;Rang») o'tkazib
yuboriladi.

Bor rang qayta yuklansa yangilanadi — ro'yxatni bir necha marta yuklash
xavfsiz, takror yozuv paydo bo'lmaydi.
"""
import re
from collections import namedtuple

from django.db import transaction

from .models import Rang, hex_tozala, kalit_yasa
from .shtrix import yaroqlimi

HEX = re.compile(r"^#?[0-9A-Fa-f]{6}$")
SARLAVHALAR = {"KOD", "CODE", "КОД", "RANGKODI"}
KOD_ENG_UZUN = Rang._meta.get_field("kod").max_length
NOM_ENG_UZUN = Rang._meta.get_field("nom").max_length

Natija = namedtuple("Natija", "yangi yangilandi xatolar")


def _bol(qator):
    for ajratuvchi in ("\t", ";", ","):
        if ajratuvchi in qator:
            return [b.strip().strip('"').strip() for b in qator.split(ajratuvchi)]
    return [qator.strip()]


def oqi(matn):
    """Matnni o'qiydi: ([(kod, nom, hex), ...], [xato, ...]).

    Xato qator butun yuklashni to'xtatmaydi — o'tkazib yuboriladi va nega
    o'tkazilgani aytiladi.
    """
    ranglar, xatolar, korilgan = [], [], set()
    for raqam, qator in enumerate((matn or "").splitlines(), 1):
        if not qator.strip():
            continue
        bolaklar = _bol(qator)
        kod = bolaklar[0]
        if kalit_yasa(kod) in SARLAVHALAR:
            continue
        if not kod:
            xatolar.append(f"{raqam}-qator: kod yo'q.")
            continue
        if not yaroqlimi(kod):
            xatolar.append(f"{raqam}-qator: «{kod}» — kodda kirill harfi yoki maxsus belgi bor.")
            continue
        if len(kod) > KOD_ENG_UZUN:
            xatolar.append(f"{raqam}-qator: «{kod}» — kod juda uzun.")
            continue

        rang, nomlar = "", []
        for bolak in bolaklar[1:]:
            if not rang and HEX.match(bolak):
                rang = hex_tozala(bolak)
            elif bolak:
                nomlar.append(bolak)

        kalit = kalit_yasa(kod)
        if kalit in korilgan:
            xatolar.append(f"{raqam}-qator: «{kod}» ro'yxatda ikkinchi marta keldi.")
            continue
        korilgan.add(kalit)
        ranglar.append((kod, " ".join(nomlar)[:NOM_ENG_UZUN], rang))
    return ranglar, xatolar


@transaction.atomic
def yukla(matn, toplam=""):
    """Ro'yxatni bazaga yozadi. Tartib — ro'yxatdagi o'rni (varaqda ham shunday)."""
    ranglar, xatolar = oqi(matn)
    toplam = (toplam or "").strip()
    bor = {r.kalit: r for r in Rang.objects.filter(
        kalit__in=[kalit_yasa(kod) for kod, _, _ in ranglar])}

    yangilar, yangilandi = [], 0
    for tartib, (kod, nom, rang) in enumerate(ranglar, 1):
        eski = bor.get(kalit_yasa(kod))
        if eski is None:
            yangilar.append(Rang(kod=kod, kalit=kalit_yasa(kod), nom=nom, hex=rang,
                                 toplam=toplam, tartib=tartib))
            continue
        # Kod aynan ro'yxatdagidek bo'lsin — shtrix Soruda'ga shu yozuvni tushiradi
        eski.kod = kod
        eski.nom = nom or eski.nom
        eski.hex = rang or eski.hex
        eski.toplam = toplam or eski.toplam
        eski.tartib = tartib
        eski.save()
        yangilandi += 1

    Rang.objects.bulk_create(yangilar)
    return Natija(len(yangilar), yangilandi, xatolar)
