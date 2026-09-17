"""Qarz daftari modellari."""
from decimal import Decimal

from django.db import models
from django.db.models import Sum

from ombor.models import Mahsulot


class Hudud(models.Model):
    """Tuman ichidagi hudud (mahalla/qishloq)."""

    nom = models.CharField("Hudud nomi", max_length=80, unique=True)
    tartib = models.PositiveSmallIntegerField("Tartib", default=0)

    class Meta:
        verbose_name = "Hudud"
        verbose_name_plural = "Hududlar"
        ordering = ["tartib", "nom"]

    def __str__(self):
        return self.nom


class Qarzdor(models.Model):
    """Qarz oluvchi mijoz."""

    ism = models.CharField("Ism", max_length=60)
    familiya = models.CharField("Familiya", max_length=60)
    telefon = models.CharField("Telefon", max_length=25, blank=True)
    hudud = models.ForeignKey(Hudud, on_delete=models.PROTECT, related_name="qarzdorlar",
                              verbose_name="Hudud")
    izoh = models.CharField("Izoh", max_length=200, blank=True)
    yaratilgan = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Qarzdor"
        verbose_name_plural = "Qarzdorlar"
        ordering = ["familiya", "ism"]

    def __str__(self):
        return f"{self.familiya} {self.ism}"

    @property
    def toliq_ism(self):
        return f"{self.familiya} {self.ism}"

    @property
    def jami_qarz(self):
        """Barcha qarz hujjatlari summasi."""
        jami = QarzQator.objects.filter(qarz__qarzdor=self).aggregate(s=Sum("summa"))["s"]
        return jami or Decimal("0")

    @property
    def jami_tolov(self):
        jami = self.tolovlar.aggregate(s=Sum("summa"))["s"]
        return jami or Decimal("0")

    @property
    def balans(self):
        """Qolgan qarz. Musbat bo'lsa - qarzi bor."""
        return self.jami_qarz - self.jami_tolov


class Qarz(models.Model):
    """Bitta qarz hujjati (bir marta olingan tovarlar ro'yxati)."""

    qarzdor = models.ForeignKey(Qarzdor, on_delete=models.CASCADE, related_name="qarzlar")
    sana = models.DateTimeField("Sana", auto_now_add=True)
    izoh = models.CharField("Izoh", max_length=200, blank=True)
    yakunlangan = models.BooleanField("Yakunlangan", default=False)

    class Meta:
        verbose_name = "Qarz"
        verbose_name_plural = "Qarzlar"
        ordering = ["-sana"]

    def __str__(self):
        return f"#{self.pk} - {self.qarzdor}"

    @property
    def jami(self):
        s = self.qatorlar.aggregate(s=Sum("summa"))["s"]
        return s or Decimal("0")

    @property
    def qatorlar_soni(self):
        return self.qatorlar.count()


class QarzQator(models.Model):
    """Qarz hujjatidagi bitta tovar qatori."""

    qarz = models.ForeignKey(Qarz, on_delete=models.CASCADE, related_name="qatorlar")
    mahsulot = models.ForeignKey(Mahsulot, on_delete=models.PROTECT, related_name="qarz_qatorlari")
    mahsulot_nomi = models.CharField("Tovar nomi", max_length=120)
    birlik = models.CharField("Birlik", max_length=10, blank=True)
    miqdor = models.DecimalField("Miqdor", max_digits=12, decimal_places=3)
    narx = models.DecimalField("Narxi", max_digits=12, decimal_places=2)
    summa = models.DecimalField("Summa", max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = "Qarz qatori"
        verbose_name_plural = "Qarz qatorlari"
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


class Tolov(models.Model):
    """Qarzdorning to'lovi."""

    qarzdor = models.ForeignKey(Qarzdor, on_delete=models.CASCADE, related_name="tolovlar")
    summa = models.DecimalField("Summa", max_digits=14, decimal_places=2)
    sana = models.DateTimeField("Sana", auto_now_add=True)
    izoh = models.CharField("Izoh", max_length=200, blank=True)

    class Meta:
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"
        ordering = ["-sana"]

    def __str__(self):
        return f"{self.qarzdor} - {self.summa}"
