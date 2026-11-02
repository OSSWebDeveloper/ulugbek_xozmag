"""Sotuv modellari: do'kondagi savdo cheki."""
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.conf import settings


from ombor.models import Mahsulot


class Sotuv(models.Model):
    """Bitta savdo cheki.

    Sotish narxi va valyuta qatorga tovar qo'shilganda saqlanadi. Kassa
    narx × miqdordan jami hisoblaydi; savdolashilgan yakuniy summa qo'lda
    o'zgartirilishi mumkin.

    So'm va dollar **qo'shilmaydi**: ikkita alohida summa yoziladi. `kurs`
    o'sha kundagi dollar kursi — yozib qo'yiladi, lekin summalar birlashtirilmaydi.

    `jami` — kassaga **naqd tushgan** pul (kunlik tushum shundan chiqadi).
    Mijozda pul yetmasa qolgani alohida `Qarz` hujjatiga yoziladi va
    `self.qarz` orqali bog'lanadi; chekning to'liq summasi — `umumiy_jami`.

    `sana` — chek yakunlangan (yoki bekor qilingan) payt: kechagi ochiq chek
    bugun yopilsa puli bugungi tushumga tushadi.
    """

    kassir = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                               on_delete=models.SET_NULL, related_name='sotuvlar')
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
    def ochiqmi(self):
        """Chekka hali tovar qo'shish, uni yakunlash yoki bekor qilish mumkinmi."""
        return not (self.yakunlangan or self.bekor_qilingan)

    @property
    def dollarmi(self):
        """Chekda dollarlik qism bormi."""
        return self.jami_dollar > 0

    # ---------- Qarzga qolgan qism ----------

    @property
    def qarz_hujjati(self):
        """Pul yetmay qolgan qism yozilgan qarz hujjati; bo'lmasa None."""
        try:
            return self.qarz
        except ObjectDoesNotExist:
            return None

    @property
    def umumiy_jami(self):
        """Chekning to'liq summasi: naqd tushgani + qarzga qolgani.

        Ikkalasidan ham qaytarilgan pul ayrilgan — ya'ni mijozda qolgan mol puli.
        """
        qarz = self.qarz_hujjati
        return self.sof_jami + (qarz.sof_jami if qarz else 0)

    @property
    def umumiy_jami_dollar(self):
        qarz = self.qarz_hujjati
        return self.sof_jami_dollar + (qarz.sof_jami_dollar if qarz else 0)

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
    narx = models.DecimalField("Sotish narxi", max_digits=16, decimal_places=4, null=True, blank=True)
    valyuta = models.CharField("Narx valyutasi", max_length=10, default='som')
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
        if self._state.adding and self.narx is None:
            self.narx = self.mahsulot.narx if self.mahsulot.narx > 0 else None
            self.valyuta = self.mahsulot.valyuta
        if not self.mahsulot_nomi:
            self.mahsulot_nomi = self.mahsulot.nom
        if not self.birlik:
            self.birlik = self.mahsulot.birlik
        super().save(*args, **kwargs)


class KassaTerminal(models.Model):
    kassir = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='kassa_terminal')
    kalit_hash = models.CharField(max_length=64, blank=True, default='')
    nom = models.CharField(max_length=100, blank=True)
    printer = models.CharField(max_length=200, blank=True)
    qurilmalar = models.JSONField(default=list)
    oxirgi_aloqa = models.DateTimeField(null=True, blank=True)
    printerlar = models.JSONField(default=list)
    etiketka_tayyor = models.BooleanField(default=False)


class ChekVazifa(models.Model):
    request_key = models.UUIDField(null=True, blank=True, unique=True)
    sotuv = models.OneToOneField(Sotuv, null=True, blank=True, on_delete=models.CASCADE, related_name='chop_vazifa')
    terminal = models.ForeignKey(KassaTerminal, on_delete=models.PROTECT, related_name='cheklar')
    holat = models.CharField(max_length=12, default='kutilmoqda')
    malumot = models.JSONField(default=dict)
    claim = models.CharField(max_length=64, blank=True)
    xato = models.CharField(max_length=300, blank=True)
    yaratilgan = models.DateTimeField(auto_now_add=True)
