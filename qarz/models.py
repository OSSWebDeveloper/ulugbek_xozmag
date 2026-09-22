"""Qarz daftari modellari."""
from decimal import Decimal

from django.db import models
from django.db.models import F, Sum

from ombor.models import Mahsulot, Valyuta


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

    # So'm va dollar hech qayerda qo'shilmaydi — har biri o'z hisobida yuradi.

    @property
    def jami_qarz(self):
        """Barcha qarz hujjatlarining so'mlik summasi.

        Qaytarib berilgan tovar puli ayriladi — mijoz olmagan mol uchun
        qarzdor bo'lib qolmasin.
        """
        jami = self.qarzlar.aggregate(s=Sum(F("jami") - F("qaytarilgan_summa")))["s"]
        return jami or Decimal("0")

    @property
    def jami_qarz_dollar(self):
        jami = self.qarzlar.aggregate(
            s=Sum(F("jami_dollar") - F("qaytarilgan_summa_dollar")))["s"]
        return jami or Decimal("0")

    @property
    def jami_tolov(self):
        jami = self.tolovlar.filter(valyuta=Valyuta.SOM).aggregate(s=Sum("summa"))["s"]
        return jami or Decimal("0")

    @property
    def jami_tolov_dollar(self):
        jami = self.tolovlar.filter(valyuta=Valyuta.DOLLAR).aggregate(s=Sum("summa"))["s"]
        return jami or Decimal("0")

    @property
    def balans(self):
        """Qolgan so'm qarzi. Musbat bo'lsa - qarzi bor."""
        return self.jami_qarz - self.jami_tolov

    @property
    def balans_dollar(self):
        """Qolgan dollar qarzi."""
        return self.jami_qarz_dollar - self.jami_tolov_dollar

    @property
    def qarzi_bormi(self):
        return self.balans > 0 or self.balans_dollar > 0


class Qarz(models.Model):
    """Bitta qarz hujjati (bir marta olingan tovarlar ro'yxati).

    Narx qatorlarda yozilmaydi — pul kalkulyatorda hisoblanadi, qarz summasi
    yakunlashda qo'lda kiritiladi.

    So'm va dollar qarzi **alohida** yuritiladi, qo'shilmaydi. `kurs` o'sha
    kundagi dollar kursi — keyin to'lov paytida kerak bo'ladi.

    Hujjat ikki yo'l bilan tug'iladi: qarz ekranida tovar yozib (qatorlari
    bo'ladi) yoki naqd sotuvda pul yetmay qolganda (`sotuv` to'ldiriladi,
    qatorlari bo'lmaydi — tovarlar chekda turadi).
    """

    qarzdor = models.ForeignKey(Qarzdor, on_delete=models.CASCADE, related_name="qarzlar")
    sotuv = models.OneToOneField(
        "sotuv.Sotuv", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="qarz", verbose_name="Qaysi chekdan",
        help_text="Naqd sotuvda pul yetmay qolgan qismi shu yerga yoziladi.",
    )
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

    class Meta:
        verbose_name = "Qarz"
        verbose_name_plural = "Qarzlar"
        ordering = ["-sana"]

    def __str__(self):
        return f"#{self.pk} - {self.qarzdor}"

    @property
    def qatorlar_soni(self):
        return self.qatorlar.count()

    @property
    def chekdanmi(self):
        """Naqd sotuvda pul yetmay qolgan qismimi."""
        return self.sotuv_id is not None

    # ---------- Oldindan to'lov ----------
    # Qarz yozilayotganda mijoz bir qismini darrov to'lashi mumkin. U alohida
    # maydonda saqlanmaydi — oddiy `Tolov` bo'lib yoziladi va shu hujjatga
    # bog'lanadi, shunda balans hisobi bitta joyda qoladi.

    @property
    def oldindan(self):
        jami = self.tolovlar.filter(valyuta=Valyuta.SOM).aggregate(s=Sum("summa"))["s"]
        return jami or Decimal("0")

    @property
    def oldindan_dollar(self):
        jami = self.tolovlar.filter(valyuta=Valyuta.DOLLAR).aggregate(s=Sum("summa"))["s"]
        return jami or Decimal("0")

    @property
    def oldindan_tolanganmi(self):
        return self.oldindan > 0 or self.oldindan_dollar > 0

    # ---------- Qaytarib berish ----------

    @property
    def sof_jami(self):
        """Qaytarilgani ayrilgan qarz summasi — balansga shu tushadi."""
        return self.jami - self.qaytarilgan_summa

    @property
    def sof_jami_dollar(self):
        return self.jami_dollar - self.qaytarilgan_summa_dollar

    @property
    def qaytarilganmi(self):
        return (self.qaytarilgan_summa > 0 or self.qaytarilgan_summa_dollar > 0
                or any(q.qaytarilgan for q in self.qatorlar.all()))


class QarzQator(models.Model):
    """Qarz hujjatidagi bitta tovar qatori."""

    qarz = models.ForeignKey(Qarz, on_delete=models.CASCADE, related_name="qatorlar")
    mahsulot = models.ForeignKey(Mahsulot, on_delete=models.PROTECT, related_name="qarz_qatorlari")
    mahsulot_nomi = models.CharField("Tovar nomi", max_length=120)
    birlik = models.CharField("Birlik", max_length=10, blank=True)
    miqdor = models.DecimalField("Miqdor", max_digits=12, decimal_places=3)
    qaytarilgan = models.DecimalField("Qaytarilgan miqdor", max_digits=12, decimal_places=3,
                                      default=0)

    class Meta:
        verbose_name = "Qarz qatori"
        verbose_name_plural = "Qarz qatorlari"
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


class Tolov(models.Model):
    """Qarzdorning to'lovi.

    To'lov ham valyutasi bilan yoziladi: so'm qarzi so'm bilan, dollar qarzi
    dollar bilan yopiladi. Aks holda ikki hisob aralashib ketadi.

    `qarz` to'ldirilgan bo'lsa bu **oldindan to'lov** — qarz yozilayotgan
    payt mijoz bir qismini darrov bergani. Balans uchun farqi yo'q, faqat
    kartochkada qaysi hujjatga tushgani ko'rinadi.
    """

    qarzdor = models.ForeignKey(Qarzdor, on_delete=models.CASCADE, related_name="tolovlar")
    qarz = models.ForeignKey(
        Qarz, on_delete=models.SET_NULL, null=True, blank=True, related_name="tolovlar",
        verbose_name="Qaysi hujjatga",
        help_text="Qarz yozilayotganda darrov to'langan bo'lsa shu hujjat.",
    )
    summa = models.DecimalField("Summa", max_digits=14, decimal_places=2)
    valyuta = models.CharField("Valyuta", max_length=10, choices=Valyuta, default=Valyuta.SOM)
    sana = models.DateTimeField("Sana", auto_now_add=True)
    izoh = models.CharField("Izoh", max_length=200, blank=True)

    class Meta:
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"
        ordering = ["-sana"]

    def __str__(self):
        return f"{self.qarzdor} - {self.summa} {self.get_valyuta_display()}"

    @property
    def dollarmi(self):
        return self.valyuta == Valyuta.DOLLAR
