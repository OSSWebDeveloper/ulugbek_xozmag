"""Ombor formalari."""
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
    class Meta:
        model = Mahsulot
        fields = ["nom", "birlik", "narx", "qoldiq", "olish_birligi", "olish_miqdori", "faol"]
        field_classes = {
            "narx": VergulliDecimal,
            "qoldiq": VergulliDecimal,
            "olish_miqdori": VergulliDecimal,
        }
        widgets = {
            "nom": forms.TextInput(attrs={"class": "kirish", "autocomplete": "off",
                                          "placeholder": "Tovar nomi"}),
            "birlik": forms.Select(attrs={"class": "kirish"}),
            "narx": forms.NumberInput(attrs={"class": "kirish raqam-maydon", "step": "0.01",
                                             "inputmode": "decimal"}),
            "qoldiq": forms.NumberInput(attrs={"class": "kirish raqam-maydon", "step": "0.001",
                                               "inputmode": "decimal"}),
            "olish_birligi": forms.Select(attrs={"class": "kirish"}),
            "olish_miqdori": forms.NumberInput(attrs={"class": "kirish raqam-maydon",
                                                      "step": "0.001", "inputmode": "decimal"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["olish_birligi"].choices = [("", "— boshqa birlikda olinmaydi —")] + [
            (q, n) for q, n in self.fields["olish_birligi"].choices if q
        ]

    def clean(self):
        tozalangan = super().clean()
        birlik = tozalangan.get("birlik")
        olish_birligi = tozalangan.get("olish_birligi")
        olish_miqdori = tozalangan.get("olish_miqdori")

        if olish_birligi and olish_birligi == birlik:
            # Ikkalasi bir xil bo'lsa — bu oddiy tovar, ortiqcha maydon tozalanadi.
            tozalangan["olish_birligi"] = ""
            olish_birligi = ""

        if olish_birligi and (olish_miqdori is None or olish_miqdori <= 0):
            self.add_error("olish_miqdori",
                           f"1 {olish_birligi} da nechta {birlik} borligini yozing "
                           f"(noldan katta son).")

        if not olish_birligi:
            tozalangan["olish_miqdori"] = 1
        return tozalangan


class KirimForm(forms.Form):
    """Omborga tovar kirimi.

    Tovar ikki birlikli bo'lsa (rulonda olinib metrda sotilsa) qaysi birlikda
    kiritilayotgani so'raladi; sotuv birligiga o'tkazish `sotuv_miqdori()` da.
    """

    # Maydon kassadagidek matn maydoni: yonidagi raqamlar klaviaturasi unga
    # yozadi, `data-numpadsiz` esa qalqib chiquvchi numpad ochilmasligi uchun.
    miqdor = VergulliDecimal(
        label="Kirim miqdori", max_digits=12, decimal_places=3, min_value=0,
        widget=forms.TextInput(attrs={"class": "kirish raqam-maydon", "id": "kirim-miqdor",
                                      "inputmode": "decimal", "autocomplete": "off",
                                      "data-numpadsiz": True, "placeholder": "0"}),
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
