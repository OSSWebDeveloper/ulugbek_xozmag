"""Ombor (sklad) modellari."""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


def tekis_son(son):
    """Decimal dan ortiqcha nollarni olib tashlab matn qaytaradi."""
    son = son or Decimal("0")
    if son == son.to_integral_value():
        return f"{son.to_integral_value():f}"
    return f"{son.normalize():f}"


class Birlik(models.TextChoices):
    DONA = "dona", "dona"
    KG = "kg", "kg"
    METR = "metr", "metr"
    LITR = "litr", "litr"
    QOP = "qop", "qop"
    QUTI = "quti", "quti"
    RULON = "rulon", "rulon"
    BUXTA = "buxta", "buxta"
    PACHKA = "pachka", "pachka"
    LIST = "list", "list"
    TONNA = "tonna", "tonna"


class Mahsulot(models.Model):
    """Skladdagi tovar.

    Qoldiq har doim **sotuv birligida** yuritiladi. Ba'zi tovarlar boshqa
    birlikda olinadi — polietilen lenta rulonda olinib metrda sotiladi.
    Shunday tovarga `olish_birligi` va `olish_miqdori` to'ldiriladi, kirim
    o'sha joyda sotuv birligiga o'tkaziladi. Sotuv, qarz va qoldiq hisobi
    bundan keyin ham bitta birlik bilan ishlaydi.
    """

    nom = models.CharField("Nomi", max_length=120, unique=True)
    birlik = models.CharField("Sotuv birligi", max_length=10, choices=Birlik,
                              default=Birlik.DONA)
    olish_birligi = models.CharField(
        "Olish birligi", max_length=10, choices=Birlik, blank=True, default="",
        help_text="Tovar boshqa birlikda olinsa tanlang. Bo'sh bo'lsa — sotuv birligining o'zi.",
    )
    olish_miqdori = models.DecimalField(
        "Bittasida", max_digits=12, decimal_places=3, default=1,
        help_text="1 olish birligida nechta sotuv birligi bor. Masalan 1 rulon = 100 metr.",
    )
    narx = models.DecimalField("Narxi", max_digits=12, decimal_places=2, default=0)
    qoldiq = models.DecimalField("Qoldiq", max_digits=12, decimal_places=3, default=0)
    faol = models.BooleanField("Faol", default=True)
    yaratilgan = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} ({self.birlik})"

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
    def olish_narxi(self):
        """Bitta olish birligining narxi: 100 metr x 9500 = 950 000 so'm."""
        if not self.ikki_birlikmi:
            return self.narx
        return (self.narx * self.olish_miqdori).quantize(Decimal("0.01"))

    @property
    def birlik_qoidasi(self):
        """'1 rulon = 100 metr'. Oddiy tovarda bo'sh matn."""
        if not self.ikki_birlikmi:
            return ""
        return f"1 {self.olish_birligi} = {self.olish_miqdori_son} {self.birlik}"

    @property
    def qoldiq_toliq(self):
        """'250 metr (2.5 rulon)' — ikkala birlikda ko'rsatish uchun."""
        asos = f"{self.qoldiq_son} {self.birlik}"
        if not self.ikki_birlikmi:
            return asos
        return f"{asos} ({self.olish_qoldigi_son} {self.olish_birligi})"

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
    def narx_son(self):
        """Narx matn ko'rinishida: 55000.00 -> '55000' (JS uchun toza son)"""
        return tekis_son(self.narx)

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
        super().save(*args, **kwargs)


class HarakatTuri(models.TextChoices):
    KIRIM = "kirim", "Kirim"
    CHIQIM = "chiqim", "Chiqim"
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
        asos = f"{tekis_son(self.miqdor)} {self.mahsulot.birlik}"
        if (self.kiritilgan_birlik and self.kiritilgan_miqdor is not None
                and self.kiritilgan_birlik != self.mahsulot.birlik):
            return f"{tekis_son(self.kiritilgan_miqdor)} {self.kiritilgan_birlik} = {asos}"
        return asos
