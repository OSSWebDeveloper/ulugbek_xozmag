"""Qarz daftari formalari."""
from django import forms

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
    class Meta:
        model = Tolov
        fields = ["summa", "izoh"]
        widgets = {
            "summa": forms.NumberInput(attrs={"class": "kirish raqam-maydon", "step": "0.01",
                                              "inputmode": "decimal"}),
            "izoh": forms.TextInput(attrs={"class": "kirish", "placeholder": "Izoh (ixtiyoriy)"}),
        }
