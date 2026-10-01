"""Rang katalogi formalari."""
from django import forms

from .models import Rang


class RangForm(forms.ModelForm):
    class Meta:
        model = Rang
        fields = ["kod", "nom", "hex", "toplam", "faol"]
        widgets = {
            "kod": forms.TextInput(attrs={
                "class": "kirish", "autocomplete": "off", "spellcheck": "false",
                "placeholder": "Masalan: RAL 3020",
            }),
            "nom": forms.TextInput(attrs={"class": "kirish", "autocomplete": "off",
                                          "placeholder": "Masalan: Yo'l qizil"}),
            "hex": forms.TextInput(attrs={"class": "kirish", "autocomplete": "off",
                                          "spellcheck": "false", "placeholder": "#CC0605",
                                          "maxlength": 7}),
            "toplam": forms.TextInput(attrs={"class": "kirish", "autocomplete": "off",
                                             "list": "toplamlar", "placeholder": "Masalan: RAL"}),
        }
