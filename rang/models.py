"""Rang (kolerovka) modellari: ranglar katalogi va rang mashinasining cheki."""
import re

from django.core.exceptions import ValidationError
from django.db import models

from ombor.models import Mahsulot, Valyuta

from .shtrix import chiziqlar, svg, yaroqlimi

HEX_NAQSH = re.compile(r"^#[0-9A-F]{6}$")


def kalit_yasa(kod):
    """Qidirish kaliti: katta harf, bo'shliq va chiziqchasiz.

    Skaner katalogdagi kodni aynan o'zicha o'qiydi, sotuvchi esa qo'lda
    «ral3020» yoki «RAL-3020» deb yozishi mumkin — hammasi bitta rang.
    """
    matn = "" if kod is None else str(kod)
    for bosh in (" ", " ", "-", "_", "\t"):
        matn = matn.replace(bosh, "")
    return matn.upper()


def hex_tozala(qiymat):
    """«cc0605», «#cc0605 » -> «#CC0605»; bo'sh bo'lsa bo'sh qoladi."""
    matn = (qiymat or "").strip().upper()
    if matn and not matn.startswith("#"):
        matn = "#" + matn
    return matn


def yozuv_rangi(hex_rang):
    """Rang ustidagi yozuv qora yoki oq bo'lsin — fon qanchalik yorug'ligiga qarab."""
    if not HEX_NAQSH.match(hex_rang or ""):
        return "#000000"
    r, g, b = (int(hex_rang[i:i + 2], 16) for i in (1, 3, 5))
    return "#000000" if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else "#FFFFFF"


class Rang(models.Model):
    """Katalogdagi bitta rang.

    `kod` — Soruda dasturiga qanday yozilsa aynan shunday. Katalog varag'idagi
    shtrix ham shu kodning o'zi: skaner uni Soruda'ning kod maydoniga xuddi
    odam yozgandek tushiradi, do'kon sahifasida esa rangni topadi.

    `hex` — varaqda chop etiladigan namuna. Printer rangi haqiqiy bo'yoqdan
    farq qiladi, bu faqat tanlashga yordam.
    """

    kod = models.CharField(
        "Kod", max_length=40, unique=True,
        help_text="Soruda dasturiga qanday yozilsa, aynan shunday. Katalogdagi shtrix shu kod.",
        error_messages={"unique": "Bunday kodli rang allaqachon bor."},
    )
    kalit = models.CharField(max_length=40, unique=True, editable=False)
    nom = models.CharField("Nomi", max_length=80, blank=True)
    hex = models.CharField(
        "Rangi", max_length=7, blank=True,
        help_text="Varaqda chop etiladigan namuna: #RRGGBB. Bo'sh bo'lsa varaqda bo'sh "
                  "katak qoladi — unga rang kartasidan namuna yopishtiriladi.",
    )
    toplam = models.CharField(
        "To'plam", max_length=40, blank=True,
        help_text="Masalan «RAL». Katalog varag'ida har bir to'plam alohida chop etiladi.",
    )
    tartib = models.PositiveIntegerField("Tartib", default=0,
                                         help_text="Varaqdagi o'rni — yuklangan tartibda.")
    faol = models.BooleanField("Katalogda ko'rinadi", default=True)
    yaratilgan = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Rang"
        verbose_name_plural = "Ranglar"
        ordering = ["toplam", "tartib", "kod"]

    def __str__(self):
        return f"{self.kod} {self.nom}".strip()

    # ---------- Ko'rinish ----------

    @property
    def yozuv_rangi(self):
        """Namuna ustidagi yozuv qora yoki oq — fon qanchalik yorug'ligiga qarab."""
        return yozuv_rangi(self.hex)

    @property
    def shtrix_svg(self):
        return svg(self.kod)

    @property
    def modullar(self):
        """Shtrixning eni modulda — CSS uni mm ga aylantiradi."""
        return chiziqlar(self.kod)[1]

    # ---------- Tekshiruv ----------

    def clean(self):
        self.kod = (self.kod or "").strip()
        xatolar = {}
        if not yaroqlimi(self.kod):
            xatolar["kod"] = ("Kodda faqat lotin harflari, raqamlar va belgilar bo'lsin — "
                              "kirill harfni skaner Soruda dasturiga to'g'ri yozolmaydi.")
        else:
            boshqa = Rang.objects.filter(kalit=kalit_yasa(self.kod)).exclude(pk=self.pk).first()
            if boshqa:
                xatolar["kod"] = f"Bu kod allaqachon bor: {boshqa.kod}."
        self.hex = hex_tozala(self.hex)
        if self.hex and not HEX_NAQSH.match(self.hex):
            xatolar["hex"] = "Rang #RRGGBB ko'rinishida bo'lsin, masalan #CC0605."
        if xatolar:
            raise ValidationError(xatolar)

    def save(self, *args, **kwargs):
        self.kod = (self.kod or "").strip()
        self.kalit = kalit_yasa(self.kod)
        self.hex = hex_tozala(self.hex)
        if not self.pk and not self.tartib:
            # Qo'lda qo'shilgan rang o'z to'plamining oxiriga tushadi
            oxirgi = (Rang.objects.filter(toplam=self.toplam)
                      .aggregate(m=models.Max("tartib"))["m"])
            self.tartib = (oxirgi or 0) + 1
        super().save(*args, **kwargs)


class Holat(models.TextChoices):
    KUTILMOQDA = "kutilmoqda", "To'lanmagan"
    KASSADA = "kassada", "Kassada"
    TOLANDI = "tolandi", "To'landi"
    QARZGA = "qarzga", "Qarzga yozildi"
    BEKOR = "bekor", "Bekor qilingan"


class Buyurtma(models.Model):
    """Rang mashinasida tayyorlangan bo'yoq — uning maxsus cheki.

    Chek mashina yonida chop etiladi, mijoz uni kassaga olib boradi. Kassir
    skanerlaydi: baza bo'yoq (ombordagi tovar) chekka miqdori bilan o'zi
    tushadi va ombordan **o'sha yerda** ayriladi. Summa boshqa joydagidek
    qo'lda yoziladi — chekdagi «To'lanadi» kassir uchun.

    Kassa chekni hujjatga bog'lab qo'yadi (`sotuv` yoki `qarz`): bitta chek
    ikki marta ishlatilmaydi, to'lanmay qolgan bo'yoq esa ro'yxatda ko'rinadi.

    Rang, baza va narxlar yozilgan paytdagicha saqlanadi — katalogda rang
    yoki ombordagi narx keyin o'zgarsa ham chek o'zgarmaydi.
    """

    rang = models.ForeignKey(Rang, on_delete=models.PROTECT, related_name="buyurtmalar")
    rang_kodi = models.CharField("Rang kodi", max_length=40)
    rang_nomi = models.CharField("Rang nomi", max_length=80, blank=True)
    rang_hex = models.CharField("Rangi", max_length=7, blank=True)

    baza = models.ForeignKey(Mahsulot, on_delete=models.PROTECT,
                             related_name="rang_buyurtmalari", verbose_name="Baza bo'yoq")
    baza_nomi = models.CharField("Baza nomi", max_length=120)
    baza_birligi = models.CharField("Birlik", max_length=10, blank=True)
    miqdor = models.DecimalField("Miqdor", max_digits=12, decimal_places=3, default=1)
    baza_narxi = models.DecimalField(
        "Baza narxi", max_digits=12, decimal_places=2, default=0,
        help_text="1 birlik uchun, tovarning o'z valyutasida (ombordagi narx).",
    )
    baza_valyuta = models.CharField("Baza valyutasi", max_length=10, choices=Valyuta,
                                    default=Valyuta.SOM)
    rang_narxi = models.DecimalField("Kolerovka narxi", max_digits=12, decimal_places=2,
                                     default=0, help_text="Rang berish xizmati, so'mda.")

    sana = models.DateTimeField("Sana", auto_now_add=True)
    sotuv = models.ForeignKey("sotuv.Sotuv", on_delete=models.SET_NULL, null=True, blank=True,
                              related_name="rang_buyurtmalari")
    qarz = models.ForeignKey("qarz.Qarz", on_delete=models.SET_NULL, null=True, blank=True,
                             related_name="rang_buyurtmalari")
    bekor_qilingan = models.BooleanField("Bekor qilingan", default=False)

    class Meta:
        verbose_name = "Rang cheki"
        verbose_name_plural = "Rang cheklari"
        ordering = ["-sana"]

    def __str__(self):
        return f"Rang cheki #{self.pk} — {self.rang_kodi}"

    @property
    def kod(self):
        """Chekdagi shtrix (12 raqam) — kassa uni `ombor/kod.py` orqali taniydi."""
        from ombor.kod import rang_cheki_kodi
        return rang_cheki_kodi(self.pk)

    @property
    def yozuv_rangi(self):
        return yozuv_rangi(self.rang_hex)

    # ---------- Pul ----------

    @property
    def dollarmi(self):
        return self.baza_valyuta == Valyuta.DOLLAR

    @property
    def baza_summa(self):
        return self.baza_narxi * self.miqdor

    @property
    def jami_som(self):
        """So'mda to'lanadigani. Dollarlik baza so'mga qo'shilmaydi."""
        return self.rang_narxi + (0 if self.dollarmi else self.baza_summa)

    @property
    def jami_dollar(self):
        return self.baza_summa if self.dollarmi else 0

    # ---------- Holat ----------

    def _hujjat(self):
        """(hujjat, turi) — chek bog'langan kassa hujjati.

        Bekor qilingan sotuv hisobga olinmaydi: undagi bo'yoq sotilmagan.
        """
        if self.sotuv_id and not self.sotuv.bekor_qilingan:
            return self.sotuv, "chek"
        if self.qarz_id:
            return self.qarz, "qarz"
        return None, ""

    @property
    def holat(self):
        if self.bekor_qilingan:
            return Holat.BEKOR
        hujjat, turi = self._hujjat()
        if hujjat is None:
            return Holat.KUTILMOQDA
        if not hujjat.yakunlangan:
            return Holat.KASSADA
        return Holat.TOLANDI if turi == "chek" else Holat.QARZGA

    @property
    def holat_matni(self):
        return Holat(self.holat).label

    @property
    def hujjat_matni(self):
        """«chek #12» yoki «qarz #5» — qaysi hujjatga tushgani."""
        hujjat, turi = self._hujjat()
        return f"{turi} #{hujjat.pk}" if hujjat else ""

    def kassa_xatosi(self):
        """Kassada qabul qilib bo'lmasa sababi; bo'lsa None.

        Bitta chek ikki marta ishlatilmasin: ikkinchi marta skanerlansa baza
        bo'yoq ombordan yana ayrilib qolardi.
        """
        if self.bekor_qilingan:
            return f"Rang cheki #{self.pk} bekor qilingan."
        hujjat, _ = self._hujjat()
        if hujjat is None:
            return None
        if hujjat.yakunlangan:
            return f"Rang cheki #{self.pk} allaqachon to'langan ({self.hujjat_matni})."
        return f"Rang cheki #{self.pk} allaqachon {self.hujjat_matni} ga qo'shilgan."
