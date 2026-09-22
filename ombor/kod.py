"""Kod bo'yicha tovar topish — kassa, tarozi va ombor uchun yagona joy.

Do'konda tovar uch yo'l bilan topiladi, uchalasi ham shu faylga keladi:

1. **Qisqa kod** — kassir raqamlar klaviaturasida tovar kodining oxirgi
   4 raqamini uradi. Og'ir tovarni (50 kg li bolg'a, sement qop) kassagacha
   ko'tarib kelish shart emas: yorliqdagi raqam uriladi.
2. **Zavod shtrixi** — skaner o'qiydi, `ShtrixKod` jadvalidan topiladi.
3. **Tarozi etiketkasi** — tarozi bosgan shtrix ichida ham tovar kodi, ham
   og'irlik turadi; miqdor kassada qo'lda yozilmaydi.

Qoidalar JS tomonida takrorlanmaydi — `static/js/skaner.js` kiritilganini
shu yerga (`/ombor/kod/`) yuboradi va tayyor javob oladi. Ya'ni kod bo'yicha
qidirish bitta joyda turadi, xuddi qoldiq `ombor/xizmat.py` da turgani kabi.

Ichki shtrixning tuzilishi (13 raqam, EAN-13):

    2 | 000027 | 01250 | 4
    ^     ^        ^     ^
    |     |        |     nazorat raqami
    |     |        og'irlik grammda (01250 = 1,25 kg); 00000 — og'irliksiz
    |     tovar kodining oxirgi 6 raqami (tarozidagi PLU)
    do'kon ichki prefiksi

Prefiks `2` — GS1 da do'kon o'zi bosadigan kodlar uchun ajratilgan
(20–29), shuning uchun hech qanday zavod kodi bilan to'qnashmaydi.
"""
from collections import namedtuple
from decimal import Decimal

from .models import KOD_UZUNLIK, QISQA_UZUNLIK, Mahsulot, ShtrixKod

PREFIKS = "2"          # do'konning o'z kodlari uchun ajratilgan boshlanish
PLU_UZUNLIK = 6        # shtrix ichidagi tovar raqami
OGIRLIK_UZUNLIK = 5    # og'irlik grammda: 99999 g = 99,999 kg
SHTRIX_UZUNLIK = 13


Natija = namedtuple("Natija", "mahsulot miqdor qanday xato")


def tozala(kiritilgan):
    """Kiritilgan kodni tozalaydi: bo'shliq, chiziqcha va yangi qator ketadi."""
    matn = "" if kiritilgan is None else str(kiritilgan)
    for bosh in (" ", " ", " ", "\t", "\n", "\r", "-"):
        matn = matn.replace(bosh, "")
    return matn.strip()


# ---------- EAN-13 ----------

def nazorat_raqami(o_n_ikki):
    """EAN-13 ning oxirgi raqami. Kiruvchi — 12 ta raqamdan iborat matn."""
    yigindi = sum(int(raqam) * (3 if joy % 2 else 1)
                  for joy, raqam in enumerate(o_n_ikki))
    return (10 - yigindi % 10) % 10


def ichki_shtrix(kod, ogirlik=None):
    """Tovar kodidan 13 raqamli shtrix yasaydi — etiketkaga bosish uchun.

    `ogirlik` berilsa (kg) u ham shtrix ichiga joylanadi — tarozi ham xuddi
    shu formatda bosadi, ya'ni kassa ikkalasini bir xil o'qiydi.
    """
    plu = str(kod)[-PLU_UZUNLIK:].rjust(PLU_UZUNLIK, "0")
    gramm = 0
    if ogirlik:
        gramm = int((Decimal(str(ogirlik)) * 1000).to_integral_value())
        if gramm >= 10 ** OGIRLIK_UZUNLIK:
            raise ValueError("Og'irlik shtrixga sig'maydi (ko'pi bilan 99,999 kg).")
    asos = PREFIKS + plu + f"{gramm:0{OGIRLIK_UZUNLIK}d}"
    return asos + str(nazorat_raqami(asos))


def shtrixni_ochish(matn):
    """Ichki yoki tarozi shtrixini ochadi.

    `(plu, miqdor)` qaytaradi; boshqa formatdagi kod bo'lsa `(None, None)` —
    demak bu zavod shtrixi yoki oddiy tovar kodi.
    """
    if len(matn) != SHTRIX_UZUNLIK or not matn.isdigit():
        return None, None
    if not matn.startswith(PREFIKS):
        return None, None
    # Nazorat raqami to'g'ri kelmasa bu bizning kod emas — zavodniki bo'lishi
    # mumkin, shuning uchun xato qaytarilmaydi, qidiruv davom etadi.
    if str(nazorat_raqami(matn[:12])) != matn[12]:
        return None, None

    plu = matn[1:1 + PLU_UZUNLIK]
    gramm = int(matn[1 + PLU_UZUNLIK:12])
    miqdor = (Decimal(gramm) / 1000).quantize(Decimal("0.001")) if gramm else None
    return plu, miqdor


# ---------- Qidirish ----------

def _kod_bilan(qism):
    """Kodning oxirgi raqamlari bo'yicha tovar topadi."""
    if not qism:
        return None, "Kod yozilmadi."
    topilgan = list(Mahsulot.objects.filter(kod__endswith=qism)[:2])
    if not topilgan:
        return None, f"{qism} kodli tovar topilmadi."
    if len(topilgan) > 1:
        # 10 000 dan ortiq tovar bo'lganda oxirgi 4 raqam takrorlanishi mumkin.
        return None, f"{qism} bilan tugaydigan bir nechta tovar bor — kodni to'liqroq yozing."
    return topilgan[0], None


def topish(kiritilgan):
    """Kassa, tarozi va omborning yagona qidiruvi.

    `Natija(mahsulot, miqdor, qanday, xato)` qaytaradi. `miqdor` faqat kod
    o'zi miqdorni aytganda to'ladi (tarozi etiketkasi yoki quti shtrixi);
    qolgan hollarda None — miqdorni kassir yozadi.
    """
    matn = tozala(kiritilgan)
    if not matn:
        return Natija(None, None, "", "Kod yozilmadi.")

    # 1. Tarozi etiketkasi yoki o'zimiz bosgan shtrix
    plu, miqdor = shtrixni_ochish(matn)
    if plu:
        mahsulot, xato = _kod_bilan(plu)
        return Natija(mahsulot, miqdor, "tarozi", xato)

    # 2. Zavod shtrixi — bazaga biriktirilgan bo'lsa
    shtrix = (ShtrixKod.objects.select_related("mahsulot").filter(kod=matn).first())
    if shtrix:
        return Natija(shtrix.mahsulot, shtrix.miqdor, "shtrix", None)

    # 3. Tovar kodi: kassir oxirgi raqamlarini uradi (odatda 4 ta)
    if matn.isdigit() and len(matn) <= KOD_UZUNLIK:
        qism = matn.rjust(QISQA_UZUNLIK, "0")
        mahsulot, xato = _kod_bilan(qism)
        qanday = "qisqa" if len(qism) <= QISQA_UZUNLIK else "toliq"
        return Natija(mahsulot, None, qanday, xato)

    # 4. Uzun kod, lekin bazada yo'q — skanerlangan yangi tovar
    return Natija(None, None, "shtrix",
                  f"{matn} — bu shtrix hali biror tovarga biriktirilmagan.")
