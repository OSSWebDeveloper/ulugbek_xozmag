"""Ombor (sklad) modellari."""
from decimal import ROUND_DOWN, Decimal

from django.core.exceptions import ValidationError
from django.db import models


KOD_UZUNLIK = 10      # tovar kodi: 0000000001, 0000000002 ...
QISQA_UZUNLIK = 4     # kassada va tarozida uriladigan oxirgi raqamlar soni


def kod_yasa(raqam):
    """Tovar id sidan kod yasaydi: 7 -> '0000000007'."""
    return f"{int(raqam):0{KOD_UZUNLIK}d}"


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


class Mahsulot(models.Model):
    """Skladdagi tovar.

    Tovarda narx turadi, lekin u **hisob-kitobga aralashmaydi**: do'konda
    savdolashiladi, shuning uchun chek/qarz summasi yakunlashda qo'lda
    yoziladi (`Sotuv.jami`, `Qarz.jami`). Narx ma'lumot uchun — sotuvchi
    ko'rib turadi, keyinchalik elektron tarozi shu narxdan foydalanadi.

    Har bir tovarga yaratilganda **kod** beriladi (`0000000001` dan boshlab,
    id bo'yicha). Kassada va tarozida uning **oxirgi 4 raqami** uriladi —
    og'ir tovarni kassagacha ko'tarib kelish shart emas. Shu kod ichki
    shtrixning ham ichida turadi (`ombor/kod.py`).

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
        help_text="Tovar yaratilganda o'zi beriladi va hech qachon o'zgarmaydi.",
    )
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
        "Narxi", max_digits=12, decimal_places=2, default=0,
        help_text="1 sotuv birligi uchun, tovarning valyutasida. Kassada summa "
                  "baribir qo'lda yoziladi — bu narx ma'lumot uchun.",
    )
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
        """Kassada va tarozida uriladigan oxirgi 4 raqam: '0000000027' -> '0027'."""
        return self.kod[-QISQA_UZUNLIK:] if self.kod else ""

    @property
    def etiketka_kodi(self):
        """O'zimiz bosadigan etiketkadagi 13 raqamli shtrix.

        Bazada saqlanmaydi — kodning o'zidan hisoblanadi, shuning uchun
        ikki joyda turib bir-biriga zid bo'lib qolmaydi. Import ichkarida:
        `ombor.kod` shu modelni o'qiydi.
        """
        from .kod import ichki_shtrix
        return ichki_shtrix(self.kod) if self.kod else ""

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
        super().save(*args, **kwargs)
        # Kod id dan chiqadi, ya'ni yozuv bazaga tushgandan keyin ma'lum bo'ladi.
        # Bir marta beriladi va boshqa o'zgarmaydi — etiketkalar qayta bosilmasin.
        if not self.kod:
            self.kod = kod_yasa(self.pk)
            super().save(update_fields=["kod"])


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


class ShtrixKod(models.Model):
    """Tovarga biriktirilgan shtrix kod.

    Alohida jadval, chunki bitta tovarda bir nechta kod bo'ladi: dona kodi
    va quti kodi, yoki bir xil tovar ikki zavoddan kelgani. `miqdor` — bitta
    skan nechta sotuv birligini bildiradi: quti kodi skanerlansa 1000 dona
    tushadi.

    Bu yerda faqat **zavod** kodlari saqlanadi. O'zimiz bosadigan etiketka
    kodi hech qayerda saqlanmaydi — u tovarning `kod` idan hisoblanadi
    (`ombor/kod.py`), ya'ni bazada ikki joyda turib bir-biriga zid bo'lib
    qolmaydi.
    """

    mahsulot = models.ForeignKey(Mahsulot, on_delete=models.CASCADE,
                                 related_name="shtrixlar", verbose_name="Tovar")
    kod = models.CharField(
        "Shtrix kod", max_length=32, unique=True, db_index=True,
        error_messages={"unique": "Bu shtrix kod boshqa tovarga biriktirilgan."},
    )
    miqdor = models.DecimalField(
        "Bitta skan", max_digits=12, decimal_places=3, default=1,
        help_text="Bir marta skanerlanganda nechta sotuv birligi. Quti kodi "
                  "bo'lsa qutidagi soni (masalan 1000).",
    )
    izoh = models.CharField("Izoh", max_length=60, blank=True,
                            help_text="Masalan «quti» yoki «eski partiya».")
    yaratilgan = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Shtrix kod"
        verbose_name_plural = "Shtrix kodlar"
        ordering = ["mahsulot__nom", "kod"]

    def __str__(self):
        return f"{self.kod} — {self.mahsulot.nom}"
