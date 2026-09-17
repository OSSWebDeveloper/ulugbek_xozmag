"""Ombor (sklad) modellari."""
from decimal import Decimal

from django.db import models


class Birlik(models.TextChoices):
    DONA = "dona", "dona"
    KG = "kg", "kg"
    METR = "metr", "metr"
    LITR = "litr", "litr"
    QOP = "qop", "qop"
    QUTI = "quti", "quti"


class Mahsulot(models.Model):
    """Skladdagi tovar."""

    nom = models.CharField("Nomi", max_length=120, unique=True)
    birlik = models.CharField("Birlik", max_length=10, choices=Birlik, default=Birlik.DONA)
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

    @property
    def qoldiq_son(self):
        """Qoldiqni chiroyli ko'rsatish uchun: 5.000 -> 5"""
        q = self.qoldiq.normalize() if self.qoldiq else Decimal("0")
        return q


class HarakatTuri(models.TextChoices):
    KIRIM = "kirim", "Kirim"
    CHIQIM = "chiqim", "Chiqim"
    TUZATISH = "tuzatish", "Tuzatish"


class OmborHarakati(models.Model):
    """Ombordagi har bir kirim/chiqim tarixi."""

    mahsulot = models.ForeignKey(Mahsulot, on_delete=models.CASCADE, related_name="harakatlar")
    tur = models.CharField("Turi", max_length=10, choices=HarakatTuri)
    miqdor = models.DecimalField("Miqdor", max_digits=12, decimal_places=3)
    izoh = models.CharField("Izoh", max_length=200, blank=True)
    sana = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ombor harakati"
        verbose_name_plural = "Ombor harakatlari"
        ordering = ["-sana"]

    def __str__(self):
        return f"{self.get_tur_display()}: {self.mahsulot.nom} {self.miqdor}"
