"""Ombor formalari."""
from decimal import Decimal

from django import forms

from .models import Mahsulot


class VergulliDecimal(forms.DecimalField):
    """Sonni vergul bilan ham qabul qiladi: `2,5` -> `2.5`.

    Do'konda vergul bilan yozish odat; oddiy DecimalField uni rad etadi.
    """

    def to_python(self, qiymat):
        if isinstance(qiymat, str):
            qiymat = qiymat.replace(",", ".").strip()
        return super().to_python(qiymat)


class MahsulotForm(forms.ModelForm):
    """Tovar kartochkasi.

    «Birlik o'zgaradi» richagi yoqilsa forma qadoq bo'yicha savol beradi:
    necha qadoq keldi, qaysi birlikda keldi, qaysi birlikda sotiladi, bitta
    qadoqda nechta. Qoldiq shundan hisoblanadi — operator metrni o'zi
    ko'paytirib o'tirmaydi. Narx har doim sotuv birligida kiritiladi.
    """

    birlik_ozgaradi = forms.BooleanField(
        label="Birlik o'zgaradi", required=False,
        widget=forms.CheckboxInput(attrs={"class": "richag-kirish", "id": "birlik-ozgaradi"}),
    )
    qadoq_soni = VergulliDecimal(
        label="Necha qadoq keldi", max_digits=12, decimal_places=3, min_value=0, required=False,
        widget=forms.TextInput(attrs={"class": "kirish raqam-maydon", "id": "qadoq-soni",
                                      "inputmode": "decimal", "autocomplete": "off",
                                      "placeholder": "0"}),
    )
    class Meta:
        model = Mahsulot
        fields = ["nom", "birlik", "olish_birligi", "olish_miqdori", "narx", "qoldiq", "faol"]
        field_classes = {
            "narx": VergulliDecimal,
            "qoldiq": VergulliDecimal,
            "olish_miqdori": VergulliDecimal,
        }
        widgets = {
            "nom": forms.TextInput(attrs={"class": "kirish", "autocomplete": "off",
                                          "placeholder": "Tovar nomi"}),
            "birlik": forms.Select(attrs={"class": "kirish"}),
            "olish_birligi": forms.Select(attrs={"class": "kirish"}),
            "olish_miqdori": forms.TextInput(attrs={"class": "kirish raqam-maydon",
                                                    "inputmode": "decimal", "autocomplete": "off",
                                                    "placeholder": "masalan 100"}),
            "narx": forms.TextInput(attrs={"class": "kirish raqam-maydon",
                                           "inputmode": "decimal", "autocomplete": "off",
                                           "placeholder": "0"}),
            "qoldiq": forms.TextInput(attrs={"class": "kirish raqam-maydon",
                                             "inputmode": "decimal", "autocomplete": "off",
                                             "placeholder": "0"}),
        }

    def __init__(self, *args, yangi=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.yangi = yangi
        if not yangi:
            # Mavjud tovarda "necha qadoq keldi" ma'nosiz — qoldiq allaqachon bor,
            # yangi partiya Kirim ekranidan kiritiladi.
            del self.fields["qadoq_soni"]
        self.fields["qoldiq"].required = False
        self.fields["olish_miqdori"].required = False
        self.fields["narx"].required = False
        self.fields["olish_birligi"].choices = [("", "— tanlang —")] + [
            (q, n) for q, n in self.fields["olish_birligi"].choices if q
        ]
        if not self.is_bound:
            self.fields["birlik_ozgaradi"].initial = self.instance.ikki_birlikmi
            if self.instance.pk is None:
                # Yangi tovarda modeldagi standart qiymatlar (0 va 1) maydonda
                # yozuv bo'lib turmasin — placeholder ko'rinib tursin.
                for maydon in ("narx", "qoldiq", "olish_miqdori"):
                    self.initial[maydon] = None

    def clean(self):
        t = super().clean()
        ozgaradi = t.get("birlik_ozgaradi")
        birlik = t.get("birlik")
        olish_birligi = t.get("olish_birligi") or ""
        olish_miqdori = t.get("olish_miqdori")

        if t.get("narx") is None:
            t["narx"] = Decimal("0")

        if not ozgaradi:
            # Oddiy tovar: qanday olinsa shunday sotiladi.
            t["olish_birligi"] = ""
            t["olish_miqdori"] = Decimal("1")
            if t.get("qoldiq") is None:
                t["qoldiq"] = Decimal("0")
            return t

        if not olish_birligi:
            self.add_error("olish_birligi", "Tovar qaysi birlikda kelishini tanlang.")
        elif olish_birligi == birlik:
            self.add_error("olish_birligi",
                           "Kelgan va sotiladigan birlik bir xil. Birlik o'zgarmasa "
                           "richagni o'chiring.")
        if olish_miqdori is None or olish_miqdori <= 0:
            self.add_error("olish_miqdori",
                           f"1 {olish_birligi or 'qadoq'} da nechta {birlik or 'birlik'} "
                           f"borligini yozing (noldan katta son).")
        if self.errors:
            return t

        # Yangi tovarda qoldiq qadoqdan hisoblanadi, qo'lda yozilmaydi.
        if self.yangi:
            qadoq = t.get("qadoq_soni") or Decimal("0")
            t["qoldiq"] = (qadoq * olish_miqdori).quantize(Decimal("0.001"))
        elif t.get("qoldiq") is None:
            t["qoldiq"] = Decimal("0")
        return t


class KirimForm(forms.Form):
    """Omborga tovar kirimi.

    Tovar ikki birlikli bo'lsa (rulonda olinib metrda sotilsa) qaysi birlikda
    kiritilayotgani so'raladi; sotuv birligiga o'tkazish `sotuv_miqdori()` da.
    """

    # Maydon kassadagidek matn maydoni — yonidagi raqamlar klaviaturasi unga yozadi.
    miqdor = VergulliDecimal(
        label="Kirim miqdori", max_digits=12, decimal_places=3, min_value=0,
        widget=forms.TextInput(attrs={"class": "kirish raqam-maydon", "id": "kirim-miqdor",
                                      "inputmode": "decimal", "autocomplete": "off",
                                      "placeholder": "0"}),
    )
    birlik = forms.ChoiceField(label="Qaysi birlikda", required=False,
                               widget=forms.RadioSelect(attrs={"class": "birlik-radio"}))
    izoh = forms.CharField(
        label="Izoh", max_length=200, required=False,
        widget=forms.TextInput(attrs={"class": "kirish", "placeholder": "Kimdan / izoh"}),
    )

    def __init__(self, *args, mahsulot=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.mahsulot = mahsulot
        if mahsulot is not None and mahsulot.ikki_birlikmi:
            self.fields["birlik"].choices = [
                (mahsulot.olish_birligi, mahsulot.olish_birligi),
                (mahsulot.birlik, mahsulot.birlik),
            ]
            self.fields["birlik"].initial = mahsulot.olish_birligi
            self.fields["birlik"].required = True
        else:
            del self.fields["birlik"]

    def clean_miqdor(self):
        """Nol kirim ma'nosiz — tarixga bo'sh yozuv qoldiradi."""
        miqdor = self.cleaned_data["miqdor"]
        if miqdor <= 0:
            raise forms.ValidationError("Miqdor noldan katta bo'lishi kerak.")
        return miqdor

    def kiritilgan_birlik(self):
        """Foydalanuvchi tanlagan birlik (yoki tovarning sotuv birligi)."""
        if not self.mahsulot:
            return ""
        return self.cleaned_data.get("birlik") or self.mahsulot.birlik

    def sotuv_miqdori(self):
        """Kiritilgan miqdor sotuv birligida."""
        return self.mahsulot.sotuvga_aylantir(
            self.cleaned_data["miqdor"], self.kiritilgan_birlik(),
        )
