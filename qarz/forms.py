"""Qarz daftari formalari."""
from django import forms

from ombor.models import Valyuta

from .models import Qarzdor, Tolov


class QarzdorForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["hudud"].empty_label = "— Hududni tanlang —"

    class Meta:
        model = Qarzdor
        fields = ["ism", "familiya", "telefon", "hudud"]
        widgets = {
            "ism": forms.TextInput(attrs={"class": "kirish", "autocomplete": "off",
                                          "placeholder": "Ism"}),
            "familiya": forms.TextInput(attrs={"class": "kirish", "autocomplete": "off",
                                               "placeholder": "Familiya"}),
            "telefon": forms.TextInput(attrs={"class": "kirish raqam-maydon chap-tekis",
                                              "autocomplete": "off",
                                              "placeholder": "+998 __ ___ __ __",
                                              "inputmode": "tel"}),
            "hudud": forms.Select(attrs={"class": "kirish"}),
        }


class TolovForm(forms.ModelForm):
    """To'lov summasi va valyutasi.

    Valyuta so'raladi, chunki so'm qarzi va dollar qarzi alohida yuradi —
    to'lov qaysi hisobga tushishini tizim o'zi topolmaydi.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tanlanmasa so'm: do'kondagi to'lovlarning ko'pi so'mda bo'ladi
        self.fields["valyuta"].required = False

    def clean_valyuta(self):
        return self.cleaned_data.get("valyuta") or Valyuta.SOM

    class Meta:
        model = Tolov
        fields = ["summa", "valyuta", "izoh"]
        widgets = {
            "summa": forms.NumberInput(attrs={"class": "kirish raqam-maydon", "step": "0.01",
                                              "inputmode": "decimal", "placeholder": "0"}),
            "valyuta": forms.Select(attrs={"class": "kirish"}),
            "izoh": forms.TextInput(attrs={"class": "kirish", "placeholder": "Izoh (ixtiyoriy)"}),
        }
