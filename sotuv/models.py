"""Naqd sotuv modellari (qarzsiz savdo)."""
from decimal import Decimal

from django.db import models
from django.db.models import Sum

from ombor.models import Mahsulot


class Sotuv(models.Model):
    """Bitta naqd savdo cheki."""

    sana = models.DateTimeField("Sana", auto_now_add=True)
    tolandi = models.DecimalField("To'landi", max_digits=14, decimal_places=2, default=0)
    izoh = models.CharField("Izoh", max_length=200, blank=True)
    yakunlangan = models.BooleanField("Yakunlangan", default=False)

    class Meta:
        verbose_name = "Sotuv"
        verbose_name_plural = "Sotuvlar"
        ordering = ["-sana"]

    def __str__(self):
        return f"Sotuv #{self.pk}"

    @property
    def jami(self):
        s = self.qatorlar.aggregate(s=Sum("summa"))["s"]
        return s or Decimal("0")

    @property
    def qaytim(self):
        """Mijozga qaytariladigan pul."""
        farq = self.tolandi - self.jami
        return farq if farq > 0 else Decimal("0")

    @property
    def qatorlar_soni(self):
        return self.qatorlar.count()


class SotuvQator(models.Model):
    """Sotuvdagi bitta tovar qatori."""

    sotuv = models.ForeignKey(Sotuv, on_delete=models.CASCADE, related_name="qatorlar")
    mahsulot = models.ForeignKey(Mahsulot, on_delete=models.PROTECT, related_name="sotuv_qatorlari")
    mahsulot_nomi = models.CharField("Tovar nomi", max_length=120)
    birlik = models.CharField("Birlik", max_length=10, blank=True)
    miqdor = models.DecimalField("Miqdor", max_digits=12, decimal_places=3)
    narx = models.DecimalField("Narxi", max_digits=12, decimal_places=2)
    summa = models.DecimalField("Summa", max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = "Sotuv qatori"
        verbose_name_plural = "Sotuv qatorlari"
        ordering = ["id"]

    def __str__(self):
        return f"{self.mahsulot_nomi} x {self.miqdor}"

    def save(self, *args, **kwargs):
        if not self.mahsulot_nomi:
            self.mahsulot_nomi = self.mahsulot.nom
        if not self.birlik:
            self.birlik = self.mahsulot.birlik
        self.summa = (self.miqdor * self.narx).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)
