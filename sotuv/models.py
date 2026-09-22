"""Naqd sotuv modellari (qarzsiz savdo)."""
from django.db import models


from ombor.models import Mahsulot


class Sotuv(models.Model):
    """Bitta naqd savdo cheki.

    Narx qatorlarda saqlanmaydi — do'konda pul kalkulyatorda hisoblanadi.
    Tizim qaysi tovar qancha chiqqanini yozadi, chek summasi esa yakunlashda
    qo'lda kiritiladi.

    So'm va dollar **qo'shilmaydi**: ikkita alohida summa yoziladi. `kurs`
    o'sha kundagi dollar kursi — yozib qo'yiladi, lekin summalar birlashtirilmaydi.
    """

    sana = models.DateTimeField("Sana", auto_now_add=True)
    jami = models.DecimalField("Jami so'm", max_digits=14, decimal_places=2, default=0)
    jami_dollar = models.DecimalField("Jami dollar", max_digits=12, decimal_places=2, default=0)
    kurs = models.DecimalField("Dollar kursi", max_digits=12, decimal_places=2, default=0)
    qaytarilgan_summa = models.DecimalField("Qaytarilgan so'm", max_digits=14,
                                            decimal_places=2, default=0)
    qaytarilgan_summa_dollar = models.DecimalField("Qaytarilgan dollar", max_digits=12,
                                                   decimal_places=2, default=0)
    izoh = models.CharField("Izoh", max_length=200, blank=True)
    yakunlangan = models.BooleanField("Yakunlangan", default=False)
    bekor_qilingan = models.BooleanField("Bekor qilingan", default=False)

    class Meta:
        verbose_name = "Sotuv"
        verbose_name_plural = "Sotuvlar"
        ordering = ["-sana"]

    def __str__(self):
        return f"Sotuv #{self.pk}"

    @property
    def qatorlar_soni(self):
        return self.qatorlar.count()

    @property
    def dollarmi(self):
        """Chekda dollarlik qism bormi."""
        return self.jami_dollar > 0

    # ---------- Qaytarib berish ----------

    @property
    def sof_jami(self):
        """Qaytarilgani ayrilgan so'm summasi — kunlik tushumga shu tushadi."""
        return self.jami - self.qaytarilgan_summa

    @property
    def sof_jami_dollar(self):
        return self.jami_dollar - self.qaytarilgan_summa_dollar

    @property
    def qaytarilganmi(self):
        return (self.qaytarilgan_summa > 0 or self.qaytarilgan_summa_dollar > 0
                or any(q.qaytarilgan for q in self.qatorlar.all()))


class SotuvQator(models.Model):
    """Sotuvdagi bitta tovar qatori."""

    sotuv = models.ForeignKey(Sotuv, on_delete=models.CASCADE, related_name="qatorlar")
    mahsulot = models.ForeignKey(Mahsulot, on_delete=models.PROTECT, related_name="sotuv_qatorlari")
    mahsulot_nomi = models.CharField("Tovar nomi", max_length=120)
    birlik = models.CharField("Birlik", max_length=10, blank=True)
    miqdor = models.DecimalField("Miqdor", max_digits=12, decimal_places=3)
    qaytarilgan = models.DecimalField("Qaytarilgan miqdor", max_digits=12, decimal_places=3,
                                      default=0)

    class Meta:
        verbose_name = "Sotuv qatori"
        verbose_name_plural = "Sotuv qatorlari"
        ordering = ["id"]

    def __str__(self):
        return f"{self.mahsulot_nomi} x {self.miqdor}"

    @property
    def qolgan_miqdor(self):
        """Mijozda qolgan miqdor: 20 qop olib 5 tasini qaytarsa — 15."""
        return self.miqdor - self.qaytarilgan

    def save(self, *args, **kwargs):
        if not self.mahsulot_nomi:
            self.mahsulot_nomi = self.mahsulot.nom
        if not self.birlik:
            self.birlik = self.mahsulot.birlik
        super().save(*args, **kwargs)
