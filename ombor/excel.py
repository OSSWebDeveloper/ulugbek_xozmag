"""Omborni Excel orqali yangilash va yuklab olish (v3.0.0).

Yo'l: fayl yuklanadi -> **qoralama** (nima o'zgarishi ko'rsatiladi, qatorlarni
tuzatish/chiqarib tashlash mumkin) -> **qo'llash** -> kerak bo'lsa **bekor qilish**.

O'qish ikki xil faylni tushunadi:
  * saytning o'z shabloni (Kod | Tovar nomi | Birlik | Qoldiq | Narxi | Valyuta);
  * do'kon dasturining «Products …xlsx» eksporti (Товар | Остаток |
    Sotish narxi = «180726 UZS» …) — kodsiz, valyuta narx ichida yozilgan.
Ustunlar sarlavhasi bo'yicha topiladi, tartibi muhim emas. Faylda yo'q ustun
tovarda o'zgarmaydi (masalan faqat «Kod + Qoldiq» fayli faqat qoldiqni yangilaydi).

Tovar avval **kod** bo'yicha (kod — turgan joyi), kod bo'lmasa **nomi** bo'yicha
topiladi. Topilmasa — yangi tovar, kodi bo'sh bo'lsa navbatdagi bo'sh kod.
Qoldiq o'zgarsa ombor tarixiga (`OmborHarakati`) «Tuzatish» bo'lib yoziladi —
qoldiq boshqa hamma joydagidek izsiz o'zgarmaydi.
"""
import io
import re
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Case, IntegerField, OuterRef, ProtectedError, Q, Subquery, Value, When
from django.utils import timezone
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from .models import (HOLAT_MAYDONLARI, KOD_MAX, Birlik, HarakatTuri, Mahsulot, OmborHarakati,
                     OmborYangilanish, Valyuta, YangilanishQatori, holatni_qoy, kod_yasa,
                     holat_mosmi, mahsulot_holati, tekis_son)

Qator = YangilanishQatori


class ExcelXatosi(Exception):
    """Foydalanuvchiga ko'rsatiladigan xato (bir nechta sabab bo'lishi mumkin)."""

    def __init__(self, sabablar):
        self.sabablar = sabablar if isinstance(sabablar, list) else [sabablar]
        super().__init__("; ".join(self.sabablar))


# ---------- Ustunlar ----------

USTUNLAR = ["kod", "nom", "birlik", "qoldiq", "narx", "valyuta", "kelish_narxi",
            "kelish_valyutasi"]
USTUN_NOMI = {"kod": "Kod", "nom": "Tovar nomi", "birlik": "Birlik", "qoldiq": "Qoldiq",
              "narx": "Narxi", "valyuta": "Valyuta", "kelish_narxi": "Kelish narxi",
              "kelish_valyutasi": "Kelish valyutasi"}
USTUN_ENI = {"kod": 9, "nom": 60, "birlik": 10, "qoldiq": 12, "narx": 14, "valyuta": 10,
             "kelish_narxi": 14, "kelish_valyutasi": 16}
# Faqat shu ustunlar (+ kod/nom) bor fayl — «xarid narxlari fayli»: yashirilgan
# tovarni ochmaydi, chunki u ombordagi tovarlar ro'yxati emas.
KELISH_USTUNLARI = {"kelish_narxi", "kelish_valyutasi"}


def _norm(matn):
    matn = str(matn or "").lower().strip()
    matn = re.sub(r"[ʻʼ'`’‘]", "", matn)
    return re.sub(r"\s+", " ", matn)


SARLAVHALAR = {
    "kod": ["kod", "код", "tovar kodi", "joy kodi"],
    "nom": ["tovar nomi", "tovar", "nomi", "товар", "наименование", "название"],
    "birlik": ["birlik", "birligi", "olchov", "ед", "ед.", "единица", "ед. изм."],
    "qoldiq": ["qoldiq", "остаток", "soni", "miqdori", "количество"],
    "narx": ["narxi", "narx", "sotish narxi", "цена", "цена продажи"],
    "valyuta": ["valyuta", "валюта"],
    "kelish_narxi": ["kelish narxi", "kelish narx", "xarid narxi", "xarid narx",
                     "olish narxi", "закупочная цена", "цена закупки", "себестоимость"],
    "kelish_valyutasi": ["kelish valyutasi", "kelish valyuta", "xarid valyutasi",
                         "валюта закупки"],
}
_SARLAVHA = {_norm(s): m for m, ss in SARLAVHALAR.items() for s in ss}

VALYUTA_SOZLARI = {
    Valyuta.SOM: {"uzs", "som", "sum", "сум", "сўм", "so‘m"},
    Valyuta.DOLLAR: {"usd", "$", "dollar", "доллар", "долл"},
}
BIRLIK_SOZLARI = {b.value: {_norm(b.value), _norm(b.label)} for b in Birlik}
BIRLIK_SOZLARI[Birlik.DONA] |= {"шт", "шт.", "dona", "ta"}
BIRLIK_SOZLARI[Birlik.KG] |= {"кг"}
BIRLIK_SOZLARI[Birlik.METR] |= {"м", "m", "метр"}
BIRLIK_SOZLARI[Birlik.LITR] |= {"л", "l", "литр"}


def valyutani_ani(matn):
    s = _norm(matn).replace(".", "")
    for val, sozlar in VALYUTA_SOZLARI.items():
        if s in sozlar:
            return val
    return None


def birlikni_ani(matn):
    s = _norm(matn)
    for b, sozlar in BIRLIK_SOZLARI.items():
        if s in sozlar:
            return b
    return None


def valyuta_yozuvi(valyuta):
    return "USD" if valyuta == Valyuta.DOLLAR else "UZS"


# ---------- Qatorni o'qish ----------

def _son(qiymat, kasr):
    """Katakdagi son -> (Decimal | None, valyuta | None).

    «180726 UZS», «2.65 USD», «1 200,5» kabi matnlarni ham tushunadi.
    """
    if qiymat is None or (isinstance(qiymat, str) and not qiymat.strip()):
        return None, None
    valyuta = None
    if isinstance(qiymat, (int, float, Decimal)) and not isinstance(qiymat, bool):
        d = Decimal(str(qiymat))
    else:
        s = str(qiymat).strip().replace("\xa0", " ")
        m = re.match(r"^(.*?)\s*([A-Za-zА-Яа-яЎўʻ‘'$.]+)$", s)
        if m and valyutani_ani(m.group(2)):
            s, valyuta = m.group(1), valyutani_ani(m.group(2))
        s = s.replace(" ", "")
        s = s.replace(",", ".") if s.count(",") == 1 and "." not in s else s.replace(",", "")
        try:
            d = Decimal(s)
        except InvalidOperation:
            raise ValueError(f"«{qiymat}» son emas")
    if not d.is_finite():
        raise ValueError(f"«{qiymat}» son emas")
    d = d.quantize(Decimal(1).scaleb(-kasr))
    if abs(d) >= Decimal(10) ** (9 if kasr == 3 else 12):
        raise ValueError(f"«{qiymat}» juda katta")
    return d, valyuta


def _kod(qiymat):
    if qiymat is None or str(qiymat).strip() == "":
        return ""
    if isinstance(qiymat, float) and qiymat.is_integer():
        qiymat = int(qiymat)
    s = str(qiymat).strip()
    if not s.isdigit() or not 1 <= int(s) <= KOD_MAX:
        raise ValueError(f"kod «{s}» noto'g'ri — 0001 dan 9999 gacha bo'lishi kerak")
    return kod_yasa(s)


def qatorni_tekshir(xom):
    """Bir qatorning xom qiymatlari (maydon -> katak) -> (holat, xato, ogohlantirish).

    Holatda faqat faylda bor ustunlar bo'ladi (+ `faol`: faylda bor tovar
    ko'rinadi). Qiymatlar `mahsulot_holati()` dagi ko'rinishda.
    """
    holat, xatolar, ogoh = {}, [], []
    if not (set(xom) & KELISH_USTUNLARI) or set(xom) - KELISH_USTUNLARI - {"kod", "nom"}:
        holat["faol"] = True
    if "kod" in xom:
        try:
            holat["kod"] = _kod(xom["kod"])
        except ValueError as e:
            xatolar.append(str(e))
            holat["kod"] = str(xom["kod"]).strip()[:10]

    if "nom" in xom:
        # Nom aynan fayldagidek: do'kon dasturida «SHlang sam 15» va
        # «shlang  sam 15» — ikki alohida tovar (faqat chetdagi bo'shliq olinadi)
        nom = str(xom["nom"] if xom["nom"] is not None else "").strip()
        if not nom:
            xatolar.append("tovar nomi bo'sh")
        elif len(nom) > 120:
            xatolar.append("tovar nomi 120 belgidan uzun")
        holat["nom"] = nom

    if "birlik" in xom and str(xom["birlik"] or "").strip():
        b = birlikni_ani(xom["birlik"])
        if not b:
            xatolar.append(f"birlik «{xom['birlik']}» noma'lum — "
                           f"{', '.join(x.value for x in Birlik)}")
        holat["birlik"] = b or str(xom["birlik"])

    narx_valyutasi = None
    for m, kasr in (("qoldiq", 3), ("narx", 4)):
        if m not in xom:
            continue
        try:
            d, val = _son(xom[m], kasr)
            if d is not None and d < 0 and m == "narx":
                raise ValueError(f"«{xom[m]}» manfiy")
        except ValueError as e:
            xatolar.append(f"{USTUN_NOMI[m]}: {e}")
            holat[m] = str(xom[m])
            continue
        holat[m] = tekis_son(d)          # bo'sh katak = 0
        if m == "narx" and val:
            narx_valyutasi = val

    if "valyuta" in xom and str(xom["valyuta"] or "").strip():
        val = valyutani_ani(xom["valyuta"])
        if not val:
            xatolar.append(f"valyuta «{xom['valyuta']}» noma'lum — UZS yoki USD yozing")
        holat["valyuta"] = val or str(xom["valyuta"])
        if val and narx_valyutasi and narx_valyutasi != val:
            ogoh.append("narx yonidagi valyuta «Valyuta» ustunidan farq qiladi — ustundagisi olindi")
    elif narx_valyutasi:
        holat["valyuta"] = narx_valyutasi

    kelish_valyutasi = None
    if "kelish_narxi" in xom:
        try:
            d, kelish_valyutasi = _son(xom["kelish_narxi"], 4)
            if d is not None and d < 0:
                raise ValueError(f"«{xom['kelish_narxi']}» manfiy")
            holat["kelish_narxi"] = "" if d is None else tekis_son(d)   # bo'sh = noma'lum
        except ValueError as e:
            xatolar.append(f"{USTUN_NOMI['kelish_narxi']}: {e}")
            holat["kelish_narxi"] = str(xom["kelish_narxi"])
    if "kelish_valyutasi" in xom and str(xom["kelish_valyutasi"] or "").strip():
        val = valyutani_ani(xom["kelish_valyutasi"])
        if not val:
            xatolar.append(f"kelish valyutasi «{xom['kelish_valyutasi']}» noma'lum — "
                           f"UZS yoki USD yozing")
        holat["kelish_valyutasi"] = val or str(xom["kelish_valyutasi"])
        if val and kelish_valyutasi and kelish_valyutasi != val:
            ogoh.append("kelish narxi yonidagi valyuta «Kelish valyutasi» ustunidan farq "
                        "qiladi — ustundagisi olindi")
    elif kelish_valyutasi:
        holat["kelish_valyutasi"] = kelish_valyutasi
    return holat, "; ".join(xatolar), "; ".join(ogoh)


def kelishni_tekisla(holat):
    """Kelish narxi bor-u valyutasi aytilmagan bo'lsa — tovarning o'z valyutasi
    (tovar formasidagi qoida bilan bir xil); narxi yo'q bo'lsa valyutasi ham yo'q."""
    if holat.get("kelish_narxi", "") == "":
        holat["kelish_valyutasi"] = ""
    elif not holat.get("kelish_valyutasi"):
        holat["kelish_valyutasi"] = holat.get("valyuta") or Valyuta.SOM
    return holat


def fayldan_oqi(fayl):
    """Excel faylini o'qiydi. (ustunlar, [(excel_qatori, xom), ...]) qaytaradi."""
    try:
        wb = load_workbook(fayl, read_only=True, data_only=True)
    except Exception:
        raise ExcelXatosi("Faylni o'qib bo'lmadi — u .xlsx Excel fayli bo'lishi kerak.")
    try:
        satrlar = wb.worksheets[0].iter_rows(values_only=True)
        ustunlar, sarlavha_qatori = None, 0
        for i, satr in enumerate(satrlar, start=1):
            topilgan = {}
            for j, katak in enumerate(satr or ()):
                m = _SARLAVHA.get(_norm(katak))
                if m and m not in topilgan:
                    topilgan[m] = j
            if "nom" in topilgan or ("kod" in topilgan and len(topilgan) > 1):
                ustunlar, sarlavha_qatori = topilgan, i
                break
            if i >= 15:
                break
        if not ustunlar:
            raise ExcelXatosi("Sarlavha qatori topilmadi: «Tovar nomi» (yoki «Товар») "
                              "yoki «Kod» ustuni bo'lishi kerak. Shablonni yuklab oling.")
        qatorlar = []
        for i, satr in enumerate(satrlar, start=sarlavha_qatori + 1):
            satr = satr or ()
            xom = {m: (satr[j] if j < len(satr) else None) for m, j in ustunlar.items()}
            if all(v is None or str(v).strip() == "" for v in xom.values()):
                continue
            qatorlar.append((i, xom))
        return set(ustunlar), qatorlar
    finally:
        wb.close()


# ---------- Tahlil: qoralama tuzish ----------

def _bosh_holat():
    return {"kod": "", "nom": "", "birlik": Birlik.DONA, "qoldiq": "0", "narx": "0",
            "valyuta": Valyuta.SOM, "faol": True, "kelish_narxi": "", "kelish_valyutasi": ""}


class _KodBeruvchi:
    """Kodsiz yangi tovarga navbatdagi bo'sh kodni beradi."""

    def __init__(self, band):
        self.band = {int(k) for k in band if k and str(k).isdigit()}
        self.keyingi = max(self.band, default=0) + 1

    def ber(self):
        while self.keyingi <= KOD_MAX and self.keyingi in self.band:
            self.keyingi += 1
        if self.keyingi > KOD_MAX:                 # oxiriga yetdi — bo'shliqlardan
            self.keyingi = next((k for k in range(1, KOD_MAX + 1) if k not in self.band), None)
            if self.keyingi is None:
                return None
        self.band.add(self.keyingi)
        return kod_yasa(self.keyingi)


def tahlil_qil(yangilanish, xom_qatorlar):
    """Fayl qatorlarini hozirgi ombor bilan solishtirib, qoralama qatorlarini yozadi."""
    mahsulotlar = list(Mahsulot.objects.all())
    kod_boyicha = {m.kod: m for m in mahsulotlar}
    nom_boyicha = {m.nom: m for m in mahsulotlar}          # nom unique

    tekshirilgan, fayl_kodlari, fayl_nomlari = [], {}, {}
    for excel_qator, xom in xom_qatorlar:
        holat, xato, ogoh = qatorni_tekshir(xom)
        kod, nom = holat.get("kod", ""), holat.get("nom")
        if not xato and kod:
            if kod in fayl_kodlari:
                xato = f"kod {kod} faylda takrorlangan ({fayl_kodlari[kod]}-qatorda ham bor)"
            else:
                fayl_kodlari[kod] = excel_qator
        if not xato and nom:
            if nom in fayl_nomlari:
                xato = f"bu nom faylda takrorlangan ({fayl_nomlari[nom]}-qatorda ham bor)"
            else:
                fayl_nomlari[nom] = excel_qator
        if not xato and not kod and not nom:
            xato = "kod ham, nom ham yo'q"
        tekshirilgan.append((excel_qator, holat, xato, ogoh))

    kodlar = _KodBeruvchi(set(kod_boyicha) | set(fayl_kodlari))
    ishlatilgan = set()          # faylga mos kelgan tovarlar (id)
    natija, ozgarmagan = {}, 0

    # 1-o'tish: kodi omborda bor qatorlar (kod — tovarning joyi, asosiy kalit).
    # 2-o'tish: qolganlari — nomi bo'yicha yoki yangi tovar.
    for otish in (1, 2):
        for idx, (excel_qator, holat, xato, ogoh) in enumerate(tekshirilgan):
            if idx in natija:
                continue
            kod = holat.get("kod", "")
            if xato:
                if otish == 2:
                    natija[idx] = Qator(amal=Qator.XATO, excel_qator=excel_qator, kod=kod[:4],
                                        yangi=holat, xato=xato[:300], ogohlantirish=ogoh[:300])
                continue
            if otish == 1:
                if kod not in kod_boyicha:
                    continue
                mahsulot = kod_boyicha[kod]
            else:
                mahsulot = nom_boyicha.get(holat.get("nom"))
                if mahsulot is not None and mahsulot.pk in ishlatilgan:
                    mahsulot = None
            if mahsulot is not None:
                ishlatilgan.add(mahsulot.pk)
                eski = mahsulot_holati(mahsulot)
                yangi = kelishni_tekisla(eski | holat)
                if not kod:
                    yangi["kod"] = eski["kod"]
                if yangi == eski:
                    ozgarmagan += 1
                    natija[idx] = None
                else:
                    natija[idx] = Qator(amal=Qator.OZGARDI, excel_qator=excel_qator,
                                        mahsulot=mahsulot, kod=yangi["kod"], eski=eski,
                                        yangi=yangi, ogohlantirish=ogoh[:300])
            elif not holat.get("nom"):
                natija[idx] = Qator(amal=Qator.XATO, excel_qator=excel_qator, kod=kod,
                                    yangi=holat, xato=f"{kod} kodli tovar omborda yo'q, "
                                                      f"yangi tovar uchun nomi kerak")
            else:
                yangi = kelishni_tekisla(_bosh_holat() | holat)
                if not kod:
                    yangi["kod"] = kodlar.ber()
                    if not yangi["kod"]:
                        natija[idx] = Qator(amal=Qator.XATO, excel_qator=excel_qator, yangi=holat,
                                            xato="bo'sh kod qolmadi (9999 to'lgan)")
                        continue
                natija[idx] = Qator(amal=Qator.YANGI, excel_qator=excel_qator,
                                    kod=yangi["kod"], yangi=yangi, ogohlantirish=ogoh[:300])

    qatorlar = [natija[i] for i in sorted(natija) if natija[i] is not None]
    if yangilanish.yoqlarini_yashir:
        for m in mahsulotlar:
            if m.pk not in ishlatilgan and m.faol:
                eski = mahsulot_holati(m)
                qatorlar.append(Qator(amal=Qator.YASHIRILDI, mahsulot=m, kod=m.kod, eski=eski,
                                      yangi=eski | {"faol": False}))
    for q in qatorlar:
        q.yangilanish = yangilanish
    Qator.objects.bulk_create(qatorlar, batch_size=500)
    yangilanish.jami_qator = len(xom_qatorlar)
    yangilanish.ozgarmagan = ozgarmagan
    yangilanish.save(update_fields=["jami_qator", "ozgarmagan"])
    return yangilanish


def fayldan_qoralama(fayl, yoqlarini_yashir=False, izoh=""):
    _ustunlar, xom = fayldan_oqi(fayl)
    if not xom:
        raise ExcelXatosi("Faylda birorta ham tovar qatori yo'q.")
    with transaction.atomic():
        y = OmborYangilanish.objects.create(
            fayl_nomi=(getattr(fayl, "name", "") or "")[:255],
            yoqlarini_yashir=yoqlarini_yashir, izoh=izoh[:200])
        return tahlil_qil(y, xom)


# ---------- Qoralama qatorini tuzatish ----------

def _mos_mahsulot(holat):
    kod, nom = holat.get("kod") or "", holat.get("nom") or ""
    if kod:
        m = Mahsulot.objects.filter(kod=kod).first()
        if m:
            return m
    if nom:      # kodsiz — nomi bo'yicha; yangi kod bilan — tovar boshqa joyga ko'chmoqda
        return Mahsulot.objects.filter(nom=nom).first()
    return None


def qator_formasi_uchun(qator):
    """Tuzatish formasining boshlang'ich qiymatlari — tovarning to'liq holati."""
    asos = _bosh_holat()
    if qator.eski:
        asos = dict(qator.eski)
    elif qator.amal == Qator.XATO:
        m = _mos_mahsulot({k: v for k, v in (qator.yangi or {}).items() if k in ("kod", "nom")})
        if m:
            asos = mahsulot_holati(m)
    return asos | (qator.yangi or {})


def qatorni_yangila(qator, holat, ogoh=""):
    """Qoralamadagi qatorni yangi qiymatlar bilan qayta hisoblaydi.

    Xato bo'lsa matnini qaytaradi va hech narsa saqlanmaydi.
    """
    boshqalar = (qator.yangilanish.qatorlar.exclude(pk=qator.pk).exclude(amal=Qator.XATO)
                 .filter(chiqarilgan=False))
    mahsulot = _mos_mahsulot(holat)
    if mahsulot is not None:
        band = boshqalar.filter(mahsulot=mahsulot).exclude(amal=Qator.YASHIRILDI).first()
        if band:
            joy = f" ({band.excel_qator}-qator)" if band.excel_qator else ""
            return f"Bu tovar ({mahsulot.kod}) qoralamaning boshqa qatorida ham bor{joy}."
        eski = mahsulot_holati(mahsulot)
        yangi = kelishni_tekisla(eski | holat)
        if not holat.get("kod"):
            yangi["kod"] = eski["kod"]
        amal = Qator.OZGARDI
    else:
        eski, yangi, amal = None, kelishni_tekisla(_bosh_holat() | holat), Qator.YANGI
        if not yangi["kod"]:
            yangi["kod"] = _KodBeruvchi(set(Mahsulot.objects.values_list("kod", flat=True))
                                        | set(boshqalar.values_list("kod", flat=True))).ber()
    for maydon, nomi in (("kod", "Kod"), ("nom", "Nom")):
        qiymat = yangi[maydon]
        toqnash = [q for q in boshqalar.exclude(amal=Qator.YASHIRILDI)
                   if (q.yangi or {}).get(maydon) == qiymat]
        if toqnash:
            joy = f" ({toqnash[0].excel_qator}-qator)" if toqnash[0].excel_qator else ""
            return f"{nomi} «{qiymat}» qoralamaning boshqa qatorida ham bor{joy}."
        egasi = Mahsulot.objects.filter(**{maydon: qiymat}).exclude(
            pk=mahsulot.pk if mahsulot else None).first()
        if egasi and not boshqalar.filter(mahsulot=egasi, amal=Qator.OZGARDI).exists():
            return f"{nomi} «{qiymat}» omborda boshqa tovarda band: {egasi.kod} {egasi.nom}."
    with transaction.atomic():
        if mahsulot is not None:     # «yashirish»ga tushgan bo'lsa — qaytarib olinadi
            boshqalar.filter(mahsulot=mahsulot, amal=Qator.YASHIRILDI).delete()
        qator.mahsulot, qator.amal, qator.eski, qator.yangi = mahsulot, amal, eski, yangi
        qator.kod, qator.xato, qator.ogohlantirish = yangi["kod"], "", ogoh[:300]
        qator.chiqarilgan = False
        qator.save()
    return None


# ---------- Qo'llash ----------

def _yakuniy_toqnashuvlar(qatorlar):
    """Qo'llashdan keyin bir kod (yoki nom) ikki tovarga tushib qolmasinmi."""
    ozgaradigan = {q.mahsulot_id: q.yangi for q in qatorlar
                   if q.amal in (Qator.OZGARDI, Qator.YASHIRILDI) and q.mahsulot_id}
    sabablar = []
    for maydon, nomi in (("kod", "kod"), ("nom", "nom")):
        band = {}
        for pk, qiymat in Mahsulot.objects.values_list("pk", maydon):
            qiymat = ozgaradigan.get(pk, {}).get(maydon, qiymat)
            band.setdefault(qiymat, []).append(f"tovar #{pk}")
        for q in qatorlar:
            if q.amal == Qator.YANGI:
                band.setdefault(q.yangi[maydon], []).append(f"{q.excel_qator or '—'}-qator")
        sabablar += [f"{nomi} «{k}» ikki joyda: {', '.join(v)}"
                     for k, v in band.items() if len(v) > 1]
    return sabablar


def _vaqtinchalik(i):
    """Almashuv paytidagi vaqtinchalik kod: «~0000» … «~zzzz» (raqam emas — hech bir
    haqiqiy kod bilan to'qnashmaydi)."""
    belgilar = "0123456789abcdefghijklmnopqrstuvwxyz"
    s = ""
    for _ in range(4):
        i, r = divmod(i, 36)
        s = belgilar[r] + s
    return "~" + s


def _holatlarni_yoz(juftlar, izoh):
    """[(mahsulot, holat), ...] ni bazaga yozadi, qoldiq farqini tarixga yozadi.

    Kod yoki nom almashsa (A<->B) unique cheklov xalaqit bermasin deb avval
    vaqtinchalik qiymat beriladi.
    """
    if not juftlar:
        return
    eski_qoldiq = {m.pk: m.qoldiq for m, _ in juftlar}
    almashadigan = [m for m, h in juftlar if m.kod != h["kod"] or m.nom != h["nom"]]
    for i, m in enumerate(almashadigan):
        m.kod, m.nom = _vaqtinchalik(i), f"~{m.pk}~"
    Mahsulot.objects.bulk_update(almashadigan, ["kod", "nom"], batch_size=500)

    harakatlar = []
    for m, h in juftlar:
        holatni_qoy(m, h)
        farq = m.qoldiq - eski_qoldiq[m.pk]
        if farq:
            harakatlar.append(OmborHarakati(mahsulot=m, tur=HarakatTuri.TUZATISH,
                                            miqdor=farq, izoh=izoh[:200]))
    Mahsulot.objects.bulk_update([m for m, _ in juftlar], HOLAT_MAYDONLARI, batch_size=500)
    OmborHarakati.objects.bulk_create(harakatlar, batch_size=500)


def qollash(yangilanish):
    if yangilanish.holat != OmborYangilanish.QORALAMA:
        raise ExcelXatosi("Faqat qoralamani qo'llash mumkin.")
    izoh = f"Excel #{yangilanish.pk}: {yangilanish.nomi}"
    with transaction.atomic():
        qatorlar = list(yangilanish.qatorlar.filter(chiqarilgan=False).exclude(amal=Qator.XATO)
                        .select_related("mahsulot"))
        yoqolgan = [q.kod for q in qatorlar if q.amal != Qator.YANGI and q.mahsulot_id is None]
        if yoqolgan:
            raise ExcelXatosi(f"Bu tovarlar qoralama tuzilgandan keyin o'chirilgan: "
                              f"{', '.join(yoqolgan[:20])}. Ularni chiqarib tashlang.")
        sabablar = _yakuniy_toqnashuvlar(qatorlar)
        if sabablar:
            raise ExcelXatosi(sabablar[:20])

        mavjud = [q for q in qatorlar if q.amal != Qator.YANGI]
        for q in mavjud:
            # Qoralamadan keyin sotuv/kirim bo'lgan bo'lishi mumkin: faqat fayl
            # o'zgartirgan maydonlar yoziladi, qolgani tovarning hozirgi holatidan
            farq = {k: v for k, v in q.yangi.items() if (q.eski or {}).get(k) != v}
            q.eski = mahsulot_holati(q.mahsulot)
            q.yangi = q.eski | farq
        _holatlarni_yoz([(q.mahsulot, q.yangi) for q in mavjud], izoh)

        yangilari = []
        for q in qatorlar:
            if q.amal == Qator.YANGI:
                m = Mahsulot()
                holatni_qoy(m, q.yangi)
                yangilari.append(m)
        Mahsulot.objects.bulk_create(yangilari, batch_size=500)
        if yangilari:
            yangilanish.qatorlar.filter(amal=Qator.YANGI, chiqarilgan=False).update(
                mahsulot=Subquery(Mahsulot.objects.filter(kod=OuterRef("kod")).values("pk")[:1]))
            pk_xarita = dict(Mahsulot.objects.filter(kod__in=[m.kod for m in yangilari])
                             .values_list("kod", "pk"))
            OmborHarakati.objects.bulk_create(
                [OmborHarakati(mahsulot_id=pk_xarita[m.kod], tur=HarakatTuri.KIRIM,
                               miqdor=m.qoldiq, izoh=f"Boshlang'ich qoldiq ({izoh})"[:200])
                 for m in yangilari if m.qoldiq], batch_size=500)

        Qator.objects.bulk_update(mavjud, ["eski", "yangi"], batch_size=500)
        yangilanish.holat = OmborYangilanish.QOLLANDI
        yangilanish.qollangan = timezone.now()
        yangilanish.save(update_fields=["holat", "qollangan"])
    return yangilanish


# ---------- Bekor qilish ----------

def bekor_toqnashuvlari(yangilanish):
    """Bekor qilishga xalaqit beradigan narsalar — keyin o'zgargan tovarlar.

    [(kod, sabab, keyingi_yangilanish | None), ...] qaytaradi.
    """
    qatorlar = list(yangilanish.qatorlar.filter(chiqarilgan=False).exclude(amal=Qator.XATO)
                    .select_related("mahsulot"))
    toqnash = []
    for q in qatorlar:
        if q.mahsulot is None:
            toqnash.append((q.kod, "tovar keyinroq o'chirilgan"))
        elif not holat_mosmi(mahsulot_holati(q.mahsulot), q.yangi):
            toqnash.append((q.mahsulot.kod, "tovar keyin yana o'zgargan (sotuv, kirim yoki tahrir)"))
    # Eski kod/nomga qaytishda uni boshqa tovar egallab olgan bo'lmasin
    qaytadigan = {q.mahsulot_id for q in qatorlar}
    for maydon in ("kod", "nom"):
        eskilari = {q.eski[maydon] for q in qatorlar
                    if q.amal == Qator.OZGARDI and q.eski[maydon] != q.yangi[maydon]}
        for m in Mahsulot.objects.filter(**{f"{maydon}__in": list(eskilari)}):
            if m.pk not in qaytadigan:
                toqnash.append((m.kod, f"eski {maydon}ni keyin boshqa tovar olgan"))

    natija = []
    for kod, sabab in toqnash:
        keyingi = (OmborYangilanish.objects
                   .filter(holat=OmborYangilanish.QOLLANDI, qollangan__gt=yangilanish.qollangan)
                   .filter(Q(qatorlar__kod=kod) | Q(qatorlar__eski__kod=kod))
                   .distinct().order_by("-qollangan").first())
        natija.append((kod, sabab, keyingi))
    return natija


def bekor_qil(yangilanish):
    if yangilanish.holat != OmborYangilanish.QOLLANDI:
        raise ExcelXatosi("Faqat qo'llangan yangilanishni bekor qilish mumkin.")
    izoh = f"Excel #{yangilanish.pk} bekor qilindi"
    with transaction.atomic():
        toqnash = bekor_toqnashuvlari(yangilanish)
        if toqnash:
            raise ExcelXatosi([f"{k}: {s}" for k, s, _ in toqnash[:20]])
        qatorlar = list(yangilanish.qatorlar.filter(chiqarilgan=False).exclude(amal=Qator.XATO)
                        .select_related("mahsulot"))
        yangilar = [q.mahsulot_id for q in qatorlar if q.amal == Qator.YANGI]
        try:
            Mahsulot.objects.filter(pk__in=yangilar).delete()
        except ProtectedError:
            raise ExcelXatosi("Yangi qo'shilgan tovarlarning ba'zisi allaqachon sotuv yoki "
                              "qarzga yozilgan — bekor qilib bo'lmaydi.")
        _holatlarni_yoz([(q.mahsulot, q.eski) for q in qatorlar if q.amal != Qator.YANGI], izoh)
        yangilanish.holat = OmborYangilanish.BEKOR
        yangilanish.bekor_qilingan = timezone.now()
        yangilanish.save(update_fields=["holat", "bekor_qilingan"])
    return yangilanish


# ---------- Ro'yxat va yuklab olish ----------

def tovarlar(q="", valyuta="", kam_birinchi=False, tugagan=False, yashirilgan=False,
             bor_birinchi=False):
    """Ombor ro'yxati va eksport uchun bir xil filtr.

    `bor_birinchi` — kassa qidiruvi uchun: natijalar soni cheklangan, tugagan tovarlar
    borlarini ro'yxatdan siqib chiqarmasin. Kod yoki shtrixga aniq moslik baribir
    birinchi turadi: kassir shu tovarni so'radi, tugagani ham ko'rinsin.
    """
    qs = Mahsulot.objects.all()
    if not yashirilgan:
        qs = qs.filter(faol=True)
    q = (q or "").strip()
    bor_tartibi = [When(qoldiq__gt=0, then=Value(1))]
    if q:
        raqam = q.replace(" ", "")
        izlov = Q()
        for soz in q.split():
            izlov &= Q(nom__icontains=soz)
        aniq = Q(shtrix_kod=raqam)
        if raqam.isdigit() and len(raqam) <= 10 and 1 <= int(raqam) <= KOD_MAX:
            aniq |= Q(kod=kod_yasa(raqam))
        bor_tartibi.insert(0, When(aniq, then=Value(0)))
        qs = qs.filter(izlov | aniq)
    if valyuta in (Valyuta.SOM, Valyuta.DOLLAR):
        qs = qs.filter(valyuta=valyuta)
    if tugagan:
        qs = qs.filter(qoldiq__lte=0)
    # «Kam qolganlar birinchi»: omborda qolgan hajmiga teskari tartib
    qs = qs.annotate(kg_tartibi=Case(
        When(birlik=Birlik.KG, then=Value(0)), default=Value(1), output_field=IntegerField(),
    ))
    if bor_birinchi:
        return qs.annotate(bor_tartibi=Case(
            *bor_tartibi, default=Value(2), output_field=IntegerField(),
        )).order_by("bor_tartibi", "kg_tartibi", "kod")
    return (qs.order_by("kg_tartibi", "qoldiq", "kod") if kam_birinchi
            else qs.order_by("kg_tartibi", "kod"))


def _harf(i):
    return chr(ord("A") + i)


def excel_yoz(mahsulotlar):
    """Tovarlardan (yoki bo'sh ro'yxatdan — shablon) .xlsx baytlari."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Ombor"
    ws.append([USTUN_NOMI[m] for m in USTUNLAR])
    for i, m in enumerate(USTUNLAR):
        c = ws.cell(row=1, column=i + 1)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="2F7AE0")
        c.alignment = Alignment(horizontal="center", vertical="center")
        ws.column_dimensions[_harf(i)].width = USTUN_ENI[m]
    ws.row_dimensions[1].height = 24
    ws.freeze_panes = "C2"
    n = 1
    for m in mahsulotlar:
        ws.append([m.kod, m.nom, m.birlik, m.qoldiq, m.narx, valyuta_yozuvi(m.valyuta),
                   m.kelish_narxi,
                   valyuta_yozuvi(m.kelish_valyutasi) if m.kelish_narxi is not None else None])
        n += 1
    oxiri = max(n, 2) + 2000
    for (katak,) in ws.iter_rows(min_row=2, max_row=oxiri, max_col=1):
        katak.number_format = "@"             # 00001 boshidagi nollar yo'qolmasin
    for ustun, fmt in (("qoldiq", "#,##0.###"), ("narx", "#,##0.####"),
                       ("kelish_narxi", "#,##0.####")):
        j = USTUNLAR.index(ustun) + 1
        for (katak,) in ws.iter_rows(min_row=2, max_row=n, min_col=j, max_col=j):
            katak.number_format = fmt
    ws.auto_filter.ref = f"A1:{_harf(len(USTUNLAR) - 1)}{n}"
    for maydon, royxat in (("valyuta", '"UZS,USD"'), ("kelish_valyutasi", '"UZS,USD"'),
                           ("birlik", '"' + ",".join(b.value for b in Birlik) + '"')):
        dv = DataValidation(type="list", formula1=royxat, allow_blank=True)
        ws.add_data_validation(dv)
        h = _harf(USTUNLAR.index(maydon))
        dv.add(f"{h}2:{h}{oxiri}")
    _yoriqnoma(wb)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _yoriqnoma(wb):
    ws = wb.create_sheet("Yo'riqnoma")
    ws.column_dimensions["A"].width = 18
    ws.column_dimensions["B"].width = 95
    ws.append(["Ombor shabloni", ""])
    ws["A1"].font = Font(bold=True, size=14)
    for a, b in [
        ("Kod", "4 xonali: 0001 … 9999 — tovar turgan joyi. Bo'sh qolsa navbatdagi bo'sh "
                "kod beriladi. Tovar avval kod bo'yicha topiladi."),
        ("Tovar nomi", "Kod bo'lmasa tovar nomi bo'yicha topiladi (harfma-harf bir xil)."),
        ("Birlik", ", ".join(b.value for b in Birlik) + " — bo'sh bo'lsa dona."),
        ("Qoldiq", "Omborda qolgan miqdor (kasr bo'lishi mumkin: 12,5). O'zgarsa ombor "
                   "tarixiga «Tuzatish» bo'lib yoziladi."),
        ("Narxi", "Faqat son (180726 yoki 2,65)."),
        ("Valyuta", "UZS (so'm) yoki USD (dollar)."),
        ("Kelish narxi", "Xarid narxi, 1 sotuv birligi uchun (2,2 yoki «2.2 USD»). Bo'sh "
                         "katak — kelish narxi noma'lum."),
        ("Kelish valyutasi", "UZS yoki USD. Bo'sh bo'lsa tovarning valyutasi olinadi."),
        ("", ""),
        ("Qanday ishlaydi", "1) Fayl yuklanadi — ombor hali o'zgarmaydi."),
        ("", "2) Nima o'zgarishi ko'rsatiladi: yangi, o'zgargan, xato qatorlar."),
        ("", "3) Kerak bo'lsa qatorni tuzatasiz yoki chiqarib tashlaysiz, keyin «Qo'llash»."),
        ("", "4) Xato bo'lsa «Bekor qilish» — ombor avvalgi holatiga qaytadi."),
        ("", ""),
        ("Muhim", "Faylda yo'q ustun o'zgarmaydi: faqat «Kod» va «Qoldiq» ustunli fayl faqat "
                  "qoldiqni yangilaydi."),
        ("", "Faqat «Kod» (yoki «Tovar nomi») va «Kelish narxi» ustunli fayl faqat xarid "
             "narxini yangilaydi — yashirilgan tovarlar yashirinligicha qoladi."),
        ("", "Do'kon dasturining «Products …xlsx» faylini ham to'g'ridan-to'g'ri yuklash mumkin."),
    ]:
        ws.append([a, b])
    for row in ws.iter_rows(min_row=2):
        row[0].font = Font(bold=True)
        row[1].alignment = Alignment(wrap_text=True, vertical="top")
