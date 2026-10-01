"""Rang katalogidagi shtrix — Code 128, harfli kodlar uchun ham.

Do'kon etiketkasi faqat raqamdan iborat (`ombor/shtrix.py`, C to'plami).
Katalogdagi shtrix esa **Soruda dasturiga yoziladigan kodning o'zi**: skaner
uni Soruda'ning kod maydoniga xuddi odam yozgandek tushiradi. Bunday kod
harfli bo'lishi mumkin (`RAL 3020`, `S 1050-Y90R`), shuning uchun bu yerda B
to'plami (ASCII 32–127) ham ishlatiladi. Raqamlar ko'p bo'lgan joyda C ga
o'tiladi — shtrix qisqaroq chiqadi va kichik katakka sig'adi.

Chiziq naqshlari va jim zona `ombor/shtrix.py` dagi jadvaldan olinadi —
jadval bitta joyda.
"""
from django.utils.html import escape

from ombor.shtrix import JIM_ZONA, NAQSHLAR, TUGASH

BOSHLASH_B = 104
BOSHLASH_C = 105
B_GA = 100        # C to'plamida turib B ga o'tish
C_GA = 99         # B to'plamida turib C ga o'tish


def yaroqlimi(matn):
    """Shtrixga sig'adimi: bo'sh emas va faqat lotin harf, raqam, belgilar."""
    return bool(matn) and all(32 <= ord(b) <= 126 for b in matn)


def _raqamlar(matn, i):
    """`i` dan boshlab nechta raqam ketma-ket turibdi."""
    j = i
    while j < len(matn) and matn[j].isdigit():
        j += 1
    return j - i


def belgilar(matn):
    """Matnni Code 128 belgilariga aylantiradi (boshlash, nazorat, tugash bilan).

    C to'plami ikki raqamni bitta belgiga joylaydi. Unga o'tish ham bir belgi
    turadi, shuning uchun faqat foyda bo'lganda o'tiladi: matn butunlay juft
    sonli raqamdan iborat bo'lsa, boshida 4 tadan ko'p raqam bo'lsa, o'rtada
    6 tadan, oxirida 4 tadan ko'p raqam ketma-ket kelsa.
    """
    if not yaroqlimi(matn):
        raise ValueError("Shtrixga faqat lotin harflari, raqamlar va belgilar sig'adi.")

    n = len(matn)
    boshida = _raqamlar(matn, 0)
    if (boshida == n and n % 2 == 0) or boshida >= 4:
        toplam, qiymatlar = "C", [BOSHLASH_C]
    else:
        toplam, qiymatlar = "B", [BOSHLASH_B]

    i = 0
    while i < n:
        seriya = _raqamlar(matn, i)
        if toplam == "C":
            if seriya >= 2:
                qiymatlar.append(int(matn[i:i + 2]))
                i += 2
                continue
            qiymatlar.append(B_GA)
            toplam = "B"
            continue
        oxirida = i + seriya == n
        if seriya >= 6 or (oxirida and seriya >= 4):
            if seriya % 2:
                # Toq raqamning birinchisi B da qoladi, qolgani juft bo'lib C ga
                qiymatlar.append(ord(matn[i]) - 32)
                i += 1
            qiymatlar.append(C_GA)
            toplam = "C"
            continue
        qiymatlar.append(ord(matn[i]) - 32)
        i += 1

    nazorat = (qiymatlar[0] + sum(q * i for i, q in enumerate(qiymatlar[1:], 1))) % 103
    return qiymatlar + [nazorat, TUGASH]


def chiziqlar(matn):
    """Qora chiziqlar: [(boshlanishi, eni), ...] modulda; ikkinchisi — umumiy en."""
    natija, x = [], JIM_ZONA
    for belgi in belgilar(matn):
        for i, en in enumerate(NAQSHLAR[belgi]):
            en = int(en)
            if i % 2 == 0:
                natija.append((x, en))
            x += en
    return natija, x + JIM_ZONA


def svg(matn):
    """Shtrixning SVG si — o'lchami modulda, sahifada CSS uni mm ga cho'zadi."""
    qora, eni = chiziqlar(matn)
    rects = "".join(f'<rect x="{x}" width="{en}" height="1"/>' for x, en in qora)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {eni} 1" '
            f'preserveAspectRatio="none" shape-rendering="crispEdges" '
            f'data-modullar="{eni}" role="img" aria-label="Shtrix kod {escape(matn)}">'
            f'<rect width="{eni}" height="1" fill="#fff"/><g fill="#000">{rects}</g></svg>')
