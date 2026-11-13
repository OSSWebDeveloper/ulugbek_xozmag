"""Ombor (sklad) modellari."""
from decimal import ROUND_DOWN, Decimal

from django.core.exceptions import ValidationError
from django.db import models


KOD_UZUNLIK = 4       # tovar kodi — turgan joyi: 0001 … 9999
KOD_MAX = 9999
QISQA_UZUNLIK = KOD_UZUNLIK   # kassada butun kod uriladi, boshidagi nollarsiz ham bo'ladi
ETIKETKA_KOPI = 500   # bir yo'la chop etiladigan etiketkalar chegarasi


def kod_yasa(raqam):
    """Raqamdan kod yasaydi: 7 -> '0007'."""
    return f"{int(raqam):0{KOD_UZUNLIK}d}"


def keyingi_kod(band=None):
    """Navbatdagi bo'sh kod: eng kattasidan keyingisi, 9999 to'lsa — bo'shliqlardan.

    `band` — qo'shimcha band kodlar (masalan hali saqlanmagan qoralama qatorlari).
    Bo'sh kod qolmagan bo'lsa None.
    """
    band = set(band or ()) | set(Mahsulot.objects.values_list("kod", flat=True))
    raqamlar = {int(k) for k in band if k and k.isdigit()}
    eng_katta = max(raqamlar, default=0)
    if eng_katta < KOD_MAX:
        return kod_yasa(eng_katta + 1)
    bosh = next((r for r in range(1, KOD_MAX + 1) if r not in raqamlar), None)
    return kod_yasa(bosh) if bosh else None


def tekis_son(son):
    """Decimal dan ortiqcha nollarni olib tashlab matn qaytaradi.

    Kasr nuqta bilan — bu qiymat JS o'qiydigan `data-` atributlariga tushadi.
    Ko'rinishga mo'ljallangan matn uchun `tekis_matn()` ishlatiladi.
    """
    son = son or Decimal("0")
    if son == son.to_integral_value():
        return f"{son.to_integral_value():f}"
    return f"{son.normalize():f}"


def tekis_matn(son):
    """Odamga ko'rsatiladigan son: kasr vergul bilan (2.5 -> '2,5')."""
    return tekis_son(son).replace(".", ",")


class Valyuta(models.TextChoices):
    """Tovar qaysi pulda keladi.

    Do'konga mol ikki xil keladi: bir qismi so'mda, bir qismi dollarda.
    Klientning asosiy sharti — ikkalasi hech qayerda qo'shilib ketmasligi:
    hisob-kitob ham, ko'rsatiladigan summa ham alohida yuritiladi.
    """

    SOM = "som", "so'm"
    DOLLAR = "dollar", "dollar"


class Birlik(models.TextChoices):
    DONA = "dona", "dona"
    KG = "kg", "kg"
    METR = "metr", "metr"
    LITR = "litr", "litr"
    QOP = "qop", "qop"
    QUTI = "quti", "quti"
    RULON = "rulon", "rulon"
    ORAM = "o'ram", "o'ram"
    PACHKA = "pachka", "pachka"
    LIST = "list", "list"
    TONNA = "tonna", "tonna"
    KVM = "kvm", "m²"
    BLOK = "blok", "blok"


class Mahsulot(models.Model):
    """Skladdagi tovar.

    Tovarda narx turadi, lekin u **hisob-kitobga aralashmaydi**: do'konda
    savdolashiladi, shuning uchun chek/qarz summasi yakunlashda qo'lda
    yoziladi (`Sotuv.jami`, `Qarz.jami`). Narx ma'lumot uchun — sotuvchi
    ko'rib turadi, keyinchalik elektron tarozi shu narxdan foydalanadi.

    Har bir tovarga turgan joyiga qarab **4 xonali kod** beriladi (`0001` …
    `9999`; oldingi 5 va 10 xonali etiketkalar ham son bo‘yicha o‘qiladi). Bo'sh qoldirilsa
    navbatdagi bo'sh kod beriladi. Kassada va tarozida shu kod uriladi
    (boshidagi nollarsiz ham: `27` = `00027`) — og'ir tovarni kassagacha
    ko'tarib kelish shart emas. Etiketkadagi shtrix
    ham shu kodning o'zi — etiketka chop etilib tovarga yopishtiriladi va
    kassada skanerlanadi (`ombor/shtrix.py`). Zavod shtrixlari saqlanmaydi.

    Qoldiq har doim **sotuv birligida** yuritiladi. Ba'zi tovarlar boshqa
    birlikda olinadi — polietilen lenta rulonda olinib metrda sotiladi.
    Shunday tovarga `olish_birligi` va `olish_miqdori` to'ldiriladi, kirim
    o'sha joyda sotuv birligiga o'tkaziladi. Sotuv, qarz va qoldiq hisobi
    bundan keyin ham bitta birlik bilan ishlaydi.
    """

    nom = models.CharField("Nomi", max_length=120, unique=True,
                           error_messages={"unique": "Bunday nomli tovar allaqachon bor."})
    kod = models.CharField(
        "Kod", max_length=KOD_UZUNLIK, unique=True, blank=True, db_index=True,
        help_text="Tovar turgan joyi: 0001 … 9999. Bo'sh qoldirilsa navbatdagi bo'sh kod beriladi.",
    )
    shtrix_kod = models.CharField('Shtrix kod', max_length=14, null=True, blank=True, unique=True)
    tarozi_kodi = models.CharField('Tarozi shtrix identifikatori', max_length=6,
                                   null=True, blank=True, unique=True, editable=False)
    birlik = models.CharField("Sotuv birligi", max_length=10, choices=Birlik,
                              default=Birlik.DONA)
    valyuta = models.CharField(
        "Qaysi pulda keladi", max_length=10, choices=Valyuta, default=Valyuta.SOM,
        help_text="Tovar dollarda kelgan bo'lsa narxi ham dollarda hisoblanadi.",
    )
    olish_birligi = models.CharField(
        "Olish birligi", max_length=10, choices=Birlik, blank=True, default="",
        help_text="Tovar boshqa birlikda olinsa tanlang. Bo'sh bo'lsa — sotuv birligining o'zi.",
    )
    olish_miqdori = models.DecimalField(
        "Bittasida", max_digits=12, decimal_places=3, default=1,
        help_text="1 olish birligida nechta sotuv birligi bor. Masalan 1 rulon = 100 metr.",
    )
    narx = models.DecimalField(
        "Narxi", max_digits=16, decimal_places=4, default=0,
        help_text="1 sotuv birligi uchun, tovarning valyutasida. Kassada summa "
                  "baribir qo'lda yoziladi — bu narx ma'lumot uchun.",
    )
    kelish_narxi = models.DecimalField("Kelish narxi", max_digits=16, decimal_places=4,
                                      null=True, blank=True)
    kelish_valyutasi = models.CharField("Kelish narxi valyutasi", max_length=10,
                                       choices=Valyuta, blank=True, default="")
    manba = models.JSONField("Import manbasi", default=dict, blank=True)
    qoldiq = models.DecimalField("Qoldiq", max_digits=12, decimal_places=3, default=0)
    faol = models.BooleanField("Faol", default=True)
    yaratilgan = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} ({self.birlik})"

    # ---------- Kod ----------

    @property
    def qisqa_kod(self):
        """Kassada va tarozida uriladigan kod — 4 xonali kodning o'zi."""
        return self.kod or ""

    @property
    def etiketka_kodi(self):
        """Shtrix 6 raqam: rang kodidan ajraladi; odam ko'radigan kod 4 xonali."""
        return self.kod.rjust(6, "0") if self.kod else ""

    @property
    def etiketka_svg(self):
        """Etiketkadagi shtrixning SVG si (ombor/shtrix.py)."""
        from .shtrix import svg
        return svg(self.etiketka_kodi) if self.kod else ""

    def etiketka_soni(self, miqdor=None, birlik=None):
        """Nechta etiketka kerak: sanaladigan tovarning har biriga bittadan.

        20 ta rozetka keldi — 20 ta etiketka; 3 rulon keldi — 3 ta. Metr, kg,
        litr bilan o'lchanadigani (yoki juda ko'pi — 5000 g'isht) bitta.
        `miqdor`/`birlik` berilmasa — ombordagi qoldiq va sotuv birligi.
        """
        miqdor = self.qoldiq if miqdor is None else Decimal(str(miqdor))
        birlik = birlik or self.birlik
        sanaladi = birlik not in (Birlik.KG, Birlik.METR, Birlik.LITR, Birlik.TONNA)
        if sanaladi and miqdor == miqdor.to_integral_value() and 0 < miqdor <= ETIKETKA_KOPI:
            return int(miqdor)
        return 1

    # ---------- Valyuta ----------

    @property
    def dollarmi(self):
        return self.valyuta == Valyuta.DOLLAR

    @property
    def valyuta_belgisi(self):
        """Ro'yxatlarda tovar yonida turadigan qisqa belgi."""
        return "$" if self.dollarmi else "so'm"

    @property
    def narx_son(self):
        """Narx JS o'qiydigan `data-` atributi uchun."""
        return tekis_son(self.narx)

    # ---------- Ikki birlikli tovarlar ----------

    @property
    def ikki_birlikmi(self):
        """Tovar bir birlikda olinib boshqasida sotiladimi."""
        return bool(self.olish_birligi) and self.olish_birligi != self.birlik

    @property
    def olish_qoldigi(self):
        """Qoldiq olish birligida: 250 metr -> 2.5 rulon."""
        if not self.ikki_birlikmi or not self.olish_miqdori:
            return self.qoldiq
        return (self.qoldiq / self.olish_miqdori).quantize(Decimal("0.001"))

    @property
    def qadoq_soni(self):
        """Nechta to'liq qadoq bor: 5020 dona va 1 pachka = 1000 bo'lsa -> 5."""
        if not self.ikki_birlikmi or not self.olish_miqdori:
            return Decimal("0")
        return (self.qoldiq / self.olish_miqdori).to_integral_value(rounding=ROUND_DOWN)

    @property
    def qadoqdan_ortiq(self):
        """To'liq qadoqlardan ortib qolgani, sotuv birligida: 5020 -> 20."""
        if not self.ikki_birlikmi or not self.olish_miqdori:
            return self.qoldiq
        return self.qoldiq - self.qadoq_soni * self.olish_miqdori

    @property
    def qadoq_matni(self):
        """Qoldiqni qadoq bilan aytadi: '5 pachka 20 dona'.

        Kasr qadoq («5,02 pachka») do'konda tushunarsiz — necha butun qadoq
        va ustiga nechta dona qolgani aytiladi. Oddiy tovarda bo'sh matn.
        """
        if not self.ikki_birlikmi:
            return ""
        butun, ortiq = self.qadoq_soni, self.qadoqdan_ortiq
        bolaklar = []
        if butun:
            bolaklar.append(f"{tekis_matn(butun)} {self.olish_birligi}")
        if ortiq or not butun:
            bolaklar.append(f"{tekis_matn(ortiq)} {self.birlik}")
        return " ".join(bolaklar)

    @property
    def birlik_qoidasi(self):
        """'1 rulon = 100 metr'. Oddiy tovarda bo'sh matn."""
        if not self.ikki_birlikmi:
            return ""
        return f"1 {self.olish_birligi} = {tekis_matn(self.olish_miqdori)} {self.birlik}"

    @property
    def qoldiq_toliq(self):
        """'5020 dona = 5 pachka 20 dona' — ikkala birlikda ko'rsatish uchun."""
        asos = f"{tekis_matn(self.qoldiq)} {self.birlik}"
        if not self.ikki_birlikmi:
            return asos
        return f"{asos} = {self.qadoq_matni}"

    def sotuvga_aylantir(self, miqdor, birlik=None):
        """Kiritilgan miqdorni sotuv birligiga o'tkazadi.

        `birlik` olish birligi bo'lsa ko'paytiriladi, aks holda o'zgarmaydi.
        """
        miqdor = Decimal(str(miqdor))
        if birlik and self.ikki_birlikmi and birlik == self.olish_birligi:
            return (miqdor * self.olish_miqdori).quantize(Decimal("0.001"))
        return miqdor

    # ---------- Ko'rinish uchun ----------

    @property
    def qoldiq_son(self):
        """Qoldiq matn ko'rinishida: 120.000 -> '120', 2.500 -> '2.5'"""
        return tekis_son(self.qoldiq)

    @property
    def olish_qoldigi_son(self):
        return tekis_son(self.olish_qoldigi)

    @property
    def olish_miqdori_son(self):
        return tekis_son(self.olish_miqdori)

    # ---------- Tekshiruv ----------

    def clean(self):
        if self.olish_birligi and self.olish_birligi == self.birlik:
            self.olish_birligi = ""
        if self.olish_birligi and (self.olish_miqdori is None or self.olish_miqdori <= 0):
            raise ValidationError({
                "olish_miqdori": "Noldan katta bo'lishi kerak — 1 olish birligida "
                                 "nechta sotuv birligi borligini yozing.",
            })

    def save(self, *args, **kwargs):
        # Ma'lumot har qanday yo'l bilan kelsa ham izchil qoladi.
        if self.olish_birligi == self.birlik:
            self.olish_birligi = ""
        if not self.olish_birligi:
            self.olish_miqdori = Decimal("1")
        if not self.kod:
            self.kod = keyingi_kod()
        elif self.kod.isdigit() and 1 <= int(self.kod) <= KOD_MAX:
            self.kod = kod_yasa(self.kod)
        super().save(*args, **kwargs)


class DollarKursi(models.Model):
    """Markaziy bankdan olingan kun kursi.

    Kuniga bitta yozuv. `kurs` nol bo'lsa — o'sha kuni bankdan olib
    bo'lmagan (internet yo'q edi); `urinish` qachon urinib ko'rilganini
    aytadi, shunga qarab qayta urinish vaqti belgilanadi.
    """

    sana = models.DateField("Sana", unique=True)
    kurs = models.DecimalField("Kurs", max_digits=12, decimal_places=2, default=0)
    urinish = models.DateTimeField("Oxirgi urinish", auto_now=True)

    class Meta:
        verbose_name = "Dollar kursi"
        verbose_name_plural = "Dollar kurslari"
        ordering = ["-sana"]

    def __str__(self):
        return f"{self.sana}: {self.kurs}"


class HarakatTuri(models.TextChoices):
    KIRIM = "kirim", "Kirim"
    CHIQIM = "chiqim", "Chiqim"
    QAYTARISH = "qaytarish", "Qaytarish"
    TUZATISH = "tuzatish", "Tuzatish"


class OmborHarakati(models.Model):
    """Ombordagi har bir kirim/chiqim tarixi.

    `miqdor` doim sotuv birligida. Kirim boshqa birlikda kiritilgan bo'lsa
    (2 rulon), aslida nima yozilgani `kiritilgan_*` maydonlarida saqlanadi —
    tarix o'qilganda "2 rulon = 200 metr" ko'rinishida chiqadi.
    """

    mahsulot = models.ForeignKey(Mahsulot, on_delete=models.CASCADE, related_name="harakatlar")
    tur = models.CharField("Turi", max_length=10, choices=HarakatTuri)
    miqdor = models.DecimalField("Miqdor", max_digits=12, decimal_places=3)
    kiritilgan_miqdor = models.DecimalField("Kiritilgan miqdor", max_digits=12, decimal_places=3,
                                            null=True, blank=True)
    kiritilgan_birlik = models.CharField("Kiritilgan birlik", max_length=10, blank=True)
    izoh = models.CharField("Izoh", max_length=200, blank=True)
    sana = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ombor harakati"
        verbose_name_plural = "Ombor harakatlari"
        ordering = ["-sana"]

    def __str__(self):
        return f"{self.get_tur_display()}: {self.mahsulot.nom} {self.miqdor}"

    @property
    def korinish(self):
        """'2 rulon = 200 metr' yoki oddiygina '200 metr'."""
        asos = f"{tekis_matn(self.miqdor)} {self.mahsulot.birlik}"
        if (self.kiritilgan_birlik and self.kiritilgan_miqdor is not None
                and self.kiritilgan_birlik != self.mahsulot.birlik):
            return f"{tekis_matn(self.kiritilgan_miqdor)} {self.kiritilgan_birlik} = {asos}"
        return asos


# ---------- Excel orqali yangilash (v3.0.0) ----------

# Yangilanish qatorida saqlanadigan tovar maydonlari — Excel ustunlari bilan bir xil
HOLAT_MAYDONLARI = ["kod", "nom", "birlik", "qoldiq", "narx", "valyuta", "faol",
                    "kelish_narxi", "kelish_valyutasi"]
SON_MAYDONLARI = {"qoldiq", "narx"}


def mahsulot_holati(m):
    """Tovarning qoralama/tarix uchun ko'rinishi — hammasi matn (faol — bool).

    Kelish narxi yo'q bo'lsa — bo'sh matn (0 emas: «narxi noma'lum» va «tekin» farqli).
    """
    return {
        "kod": m.kod or "", "nom": m.nom, "birlik": m.birlik,
        "qoldiq": tekis_son(m.qoldiq), "narx": tekis_son(m.narx),
        "valyuta": m.valyuta, "faol": bool(m.faol),
        "kelish_narxi": "" if m.kelish_narxi is None else tekis_son(m.kelish_narxi),
        "kelish_valyutasi": m.kelish_valyutasi or "",
    }


def holatni_qoy(m, holat):
    for maydon in HOLAT_MAYDONLARI:
        if maydon not in holat:
            continue
        qiymat = holat[maydon]
        if maydon in SON_MAYDONLARI:
            qiymat = Decimal(qiymat or "0")
        elif maydon == "kelish_narxi":
            qiymat = Decimal(qiymat) if qiymat not in (None, "") else None
        elif maydon == "kelish_valyutasi":
            qiymat = qiymat or ""
        setattr(m, maydon, qiymat)


def holat_mosmi(holat, kutilgan):
    """`kutilgan` dagi har maydon `holat` da ham shunday. Eski versiyada yozilgan
    qatorlarda yangi maydonlar (kelish narxi) yo'q — ular solishtirilmaydi."""
    return all(holat.get(k) == v for k, v in kutilgan.items())


class OmborYangilanish(models.Model):
    """Omborga bir yo'la kiritilgan o'zgarishlar: Excel fayl yoki qo'lda.

    Fayl yuklanganda avval **qoralama** bo'ladi — nima o'zgarishi ko'rsatiladi,
    qatorlarni tuzatish yoki chiqarib tashlash mumkin. «Qo'llash»dan keyin
    ombor yangilanadi; har qatorda tovarning oldingi holati saqlangani uchun
    yangilanishni keyin **bekor qilish** mumkin.
    """

    QORALAMA, QOLLANDI, BEKOR = "qoralama", "qollandi", "bekor"
    HOLATLAR = [(QORALAMA, "Qoralama"), (QOLLANDI, "Qo'llangan"), (BEKOR, "Bekor qilingan")]

    holat = models.CharField("Holat", max_length=10, choices=HOLATLAR, default=QORALAMA,
                             db_index=True)
    fayl_nomi = models.CharField("Fayl nomi", max_length=255, blank=True)
    izoh = models.CharField("Izoh", max_length=200, blank=True)
    yoqlarini_yashir = models.BooleanField("Faylda yo'q tovarlarni yashirish", default=False)
    jami_qator = models.PositiveIntegerField("Fayldagi qatorlar", default=0)
    ozgarmagan = models.PositiveIntegerField("O'zgarmagan qatorlar", default=0)
    yaratilgan = models.DateTimeField("Yuklangan", auto_now_add=True)
    qollangan = models.DateTimeField("Qo'llangan", null=True, blank=True)
    bekor_qilingan = models.DateTimeField("Bekor qilingan", null=True, blank=True)

    class Meta:
        verbose_name = "Ombor yangilanishi"
        verbose_name_plural = "Ombor yangilanishlari"
        ordering = ["-yaratilgan"]

    def __str__(self):
        return f"#{self.pk} {self.nomi}"

    @property
    def nomi(self):
        return self.fayl_nomi or self.izoh or "Qo'lda"

    def sanoq(self):
        """Amal turi bo'yicha qatorlar soni; chiqarib tashlanganlar alohida."""
        natija = {k: 0 for k, _ in YangilanishQatori.AMALLAR}
        natija["chiqarilgan"] = 0
        for amal, chiqarilgan, soni in (self.qatorlar.values_list("amal", "chiqarilgan")
                                        .annotate(n=models.Count("id"))):
            natija["chiqarilgan" if chiqarilgan else amal] += soni
        return natija


class YangilanishQatori(models.Model):
    """Yangilanishdagi bitta tovar o'zgarishi: oldingi va keyingi holat."""

    YANGI, OZGARDI, YASHIRILDI, XATO = "yangi", "ozgardi", "yashirildi", "xato"
    AMALLAR = [(YANGI, "Yangi tovar"), (OZGARDI, "O'zgardi"),
               (YASHIRILDI, "Yashiriladi"), (XATO, "Xato")]

    yangilanish = models.ForeignKey(OmborYangilanish, on_delete=models.CASCADE,
                                    related_name="qatorlar")
    mahsulot = models.ForeignKey(Mahsulot, null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="yangilanish_qatorlari")
    excel_qator = models.PositiveIntegerField("Excel qatori", null=True, blank=True)
    amal = models.CharField("Amal", max_length=10, choices=AMALLAR, db_index=True)
    kod = models.CharField("Kod", max_length=KOD_UZUNLIK, blank=True, db_index=True)
    eski = models.JSONField("Oldingi holat", null=True, blank=True)
    yangi = models.JSONField("Yangi holat", null=True, blank=True)
    xato = models.CharField("Xato", max_length=300, blank=True)
    ogohlantirish = models.CharField("Ogohlantirish", max_length=300, blank=True)
    chiqarilgan = models.BooleanField("Qo'llanmaydi", default=False)

    class Meta:
        verbose_name = "Yangilanish qatori"
        verbose_name_plural = "Yangilanish qatorlari"
        ordering = ["id"]

    def ozgargan_maydonlar(self):
        if self.amal != self.OZGARDI or not self.eski or not self.yangi:
            return set()
        return {m for m in HOLAT_MAYDONLARI if self.eski.get(m) != self.yangi.get(m)}

    def katakchalar(self):
        """Shablon uchun: qoldiq, narx va kelish narxi ustunlari (valyuta narx yonida)."""
        ozg = self.ozgargan_maydonlar()
        eski = self.eski or {}
        yangi = eski if self.amal == self.YASHIRILDI else (self.yangi or {})
        return [
            {"maydon": "qoldiq", "eski": eski.get("qoldiq", ""), "yangi": yangi.get("qoldiq", ""),
             "ozgardi": "qoldiq" in ozg, "qoshimcha": yangi.get("birlik", ""),
             "eski_qoshimcha": eski.get("birlik", "")},
            {"maydon": "narx", "eski": eski.get("narx", ""), "yangi": yangi.get("narx", ""),
             "ozgardi": bool(ozg & {"narx", "valyuta"}),
             "qoshimcha": "$" if yangi.get("valyuta") == Valyuta.DOLLAR else "so'm",
             "eski_qoshimcha": "$" if eski.get("valyuta") == Valyuta.DOLLAR else "so'm"},
            {"maydon": "kelish_narxi", "eski": eski.get("kelish_narxi", ""),
             "yangi": yangi.get("kelish_narxi", ""),
             "ozgardi": bool(ozg & {"kelish_narxi", "kelish_valyutasi"}),
             "qoshimcha": _valyuta_belgisi(yangi.get("kelish_valyutasi")),
             "eski_qoshimcha": _valyuta_belgisi(eski.get("kelish_valyutasi"))},
        ]


def _valyuta_belgisi(valyuta):
    return {Valyuta.DOLLAR: "$", Valyuta.SOM: "so'm"}.get(valyuta, "")
