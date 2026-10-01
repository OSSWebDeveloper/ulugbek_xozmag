"""Kod bo'yicha tovar topish — kassa, tarozi va ombor uchun yagona joy.

Har bir tovarga yaratilganda kod beriladi va shu kod etiketkada chop etilib
tovarga yopishtiriladi. Zavod shtrixlari ishlatilmaydi — kassa faqat
do'konning o'z etiketkasini taniydi. Tovar ikki yo'l bilan topiladi,
ikkalasi ham shu faylga keladi:

1. **Tovar kodi** (5 xonali, tovar turgan joyi) — skaner etiketkadagi
   shtrixni o'qiydi (Code 128, `ombor/shtrix.py`) yoki kassir raqamlar
   klaviaturasida kodni uradi (`27` = `00027`). Og'ir tovarni (50 kg li
   bolg'a, sement qop) kassagacha ko'tarib kelish shart emas: yorliqdagi
   raqam uriladi.
2. **Tarozi etiketkasi** — tarozi bosgan shtrix ichida ham tovar kodi, ham
   og'irlik turadi; miqdor kassada qo'lda yozilmaydi.

Qoidalar JS tomonida takrorlanmaydi — `static/js/skaner.js` kiritilganini
shu yerga (`/ombor/kod/`) yuboradi va tayyor javob oladi. Ya'ni kod bo'yicha
qidirish bitta joyda turadi, xuddi qoldiq `ombor/xizmat.py` da turgani kabi.

Tarozi shtrixining tuzilishi (13 raqam, EAN-13):

    2 | 000027 | 01250 | 4
    ^     ^        ^     ^
    |     |        |     nazorat raqami
    |     |        og'irlik grammda (01250 = 1,25 kg); 00000 — og'irliksiz
    |     tovar kodining oxirgi 6 raqami (tarozidagi PLU)
    do'kon ichki prefiksi

Prefiks `2` — GS1 da do'kon o'zi bosadigan kodlar uchun ajratilgan
(20–29), shuning uchun hech qanday zavod kodi bilan to'qnashmaydi.

3. **Rang (kolerovka) cheki** — rang mashinasi yonida chop etiladi
   (`rang/`), mijoz uni kassaga olib keladi. Skanerlansa chekdagi baza
   bo'yoq miqdori bilan chekka tushadi. Tuzilishi (12 raqam, Code 128):

       77 | 000000012 | 3
       ^        ^      ^
       |        |      nazorat raqami (qo'lda xato urilsa qabul qilinmaydi)
       |        chek raqami
       rang cheki belgisi — tovar kodidan (10 raqam) va tarozidan (13) uzun-qisqaligi farq qiladi
"""
from collections import namedtuple
from decimal import Decimal

from .models import KOD_MAX, Mahsulot, kod_yasa

PREFIKS = "2"          # do'konning o'z kodlari uchun ajratilgan boshlanish
PLU_UZUNLIK = 6        # shtrix ichidagi tovar raqami
OGIRLIK_UZUNLIK = 5    # og'irlik grammda: 99999 g = 99,999 kg
SHTRIX_UZUNLIK = 13

RANG_PREFIKS = "77"    # rang (kolerovka) cheki
RANG_UZUNLIK = 12


# `rang_cheki` — kod rang cheki bo'lsa o'sha buyurtma (rang.Buyurtma), aks holda None
Natija = namedtuple("Natija", "mahsulot miqdor qanday xato rang_cheki", defaults=(None,))


def tozala(kiritilgan):
    """Kiritilgan kodni tozalaydi: bo'shliq, chiziqcha va yangi qator ketadi."""
    matn = "" if kiritilgan is None else str(kiritilgan)
    for bosh in (" ", " ", " ", "\t", "\n", "\r", "-"):
        matn = matn.replace(bosh, "")
    return matn.strip()


# ---------- EAN-13 ----------

def nazorat_raqami(o_n_ikki):
    """EAN-13 ning oxirgi raqami. Kiruvchi — 12 ta raqamdan iborat matn
    (rang chekida 11 ta — hisob usuli bir xil)."""
    yigindi = sum(int(raqam) * (3 if joy % 2 else 1)
                  for joy, raqam in enumerate(o_n_ikki))
    return (10 - yigindi % 10) % 10


def ichki_shtrix(kod, ogirlik=None):
    """Tarozi etiketkasining 13 raqamli shtrixi (EAN-13, `2` bilan boshlanadi).

    `ogirlik` berilsa (kg) u ham shtrix ichiga joylanadi — tarozi aynan shu
    formatda bosadi. O'zimiz bosadigan etiketkada esa Code 128 ishlatiladi
    (`Mahsulot.etiketka_kodi`): EAN-13 ning oxirgi raqami nazorat raqami,
    yozuvdagi oxirgi 4 raqam tovar kodiga to'g'ri kelmasdi.
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
    demak bu oddiy tovar kodi (yoki umuman notanish kod).
    """
    if len(matn) != SHTRIX_UZUNLIK or not matn.isdigit():
        return None, None
    if not matn.startswith(PREFIKS):
        return None, None
    # Nazorat raqami to'g'ri kelmasa bu tarozi kodi emas (yoki skaner yarim
    # o'qigan) — tovar topilmaydi, noto'g'ri tovar sotilib ketmaydi.
    if str(nazorat_raqami(matn[:12])) != matn[12]:
        return None, None

    plu = matn[1:1 + PLU_UZUNLIK]
    gramm = int(matn[1 + PLU_UZUNLIK:12])
    miqdor = (Decimal(gramm) / 1000).quantize(Decimal("0.001")) if gramm else None
    return plu, miqdor


# ---------- Rang cheki ----------

def rang_cheki_kodi(raqam):
    """Rang chekidagi shtrix: `77` + 9 raqamli chek raqami + nazorat raqami."""
    asos = RANG_PREFIKS + f"{int(raqam):0{RANG_UZUNLIK - len(RANG_PREFIKS) - 1}d}"
    return asos + str(nazorat_raqami(asos))


def rang_chekini_ochish(matn):
    """Rang cheki kodidan chek raqamini oladi; boshqa kod bo'lsa None."""
    if len(matn) != RANG_UZUNLIK or not matn.isdigit() or not matn.startswith(RANG_PREFIKS):
        return None
    if str(nazorat_raqami(matn[:-1])) != matn[-1]:
        return None
    return int(matn[len(RANG_PREFIKS):-1])


# ---------- Qidirish ----------

def _kod_bilan(qism):
    """Tovarni kod bo'yicha topadi. Kod son sifatida o'qiladi: `27`, `00027`
    va eski 10 xonali etiketkadagi `0000000027` — hammasi `00027`."""
    if not qism:
        return None, "Kod yozilmadi."
    raqam = int(qism)
    if not 1 <= raqam <= KOD_MAX:
        return None, f"{qism} kodli tovar topilmadi."
    mahsulot = Mahsulot.objects.filter(kod=kod_yasa(raqam)).first()
    if mahsulot is None:
        return None, f"{kod_yasa(raqam)} kodli tovar topilmadi."
    return mahsulot, None


def topish(kiritilgan):
    """Kassa, tarozi va omborning yagona qidiruvi.

    `Natija(mahsulot, miqdor, qanday, xato)` qaytaradi. `miqdor` faqat kod
    o'zi miqdorni aytganda to'ladi (tarozi etiketkasidagi og'irlik);
    qolgan hollarda None — miqdorni kassir yozadi.
    """
    matn = tozala(kiritilgan)
    if not matn:
        return Natija(None, None, "", "Kod yozilmadi.")

    # 1. Tarozi etiketkasi (og'irlik bilan)
    plu, miqdor = shtrixni_ochish(matn)
    if plu:
        mahsulot, xato = _kod_bilan(plu)
        return Natija(mahsulot, miqdor, "tarozi", xato)

    # 2. Tovar kodi: kassir kodni uradi (boshidagi nollarsiz ham) yoki skaner
    #    etiketkadagi kodni o'qiydi (Code 128). 10 raqamgacha — eski
    #    etiketkalar (0000000027) ham o'qilsin.
    if matn.isdigit() and len(matn) <= 10:
        mahsulot, xato = _kod_bilan(matn)
        qanday = "qisqa" if len(matn) < 5 else "toliq"
        return Natija(mahsulot, None, qanday, xato)

    # 3. Rang (kolerovka) cheki: baza bo'yoq chekdagi miqdori bilan keladi.
    #    Buyurtma rang ilovasida — ombor unga faqat shu yerda murojaat qiladi.
    raqam = rang_chekini_ochish(matn)
    if raqam:
        from rang.kassa import chekni_top
        return chekni_top(raqam)

    # 4. Bizning formatga to'g'ri kelmaydi. Ko'pincha bu qadoqdagi zavod
    #    shtrixi — skaner etiketka o'rniga shuni o'qib qo'ygan.
    return Natija(None, None, "notanish",
                  f"{matn} — bunday kod yo'q. Tovarga yopishtirilgan etiketkani "
                  f"skanerlang.")
