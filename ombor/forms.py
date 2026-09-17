"""Ombor formalari."""
from django import forms

from .models import Mahsulot


class MahsulotForm(forms.ModelForm):
    class Meta:
        model = Mahsulot
        fields = ["nom", "birlik", "narx", "qoldiq", "faol"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "kirish", "autocomplete": "off",
                                          "placeholder": "Tovar nomi"}),
            "birlik": forms.Select(attrs={"class": "kirish"}),
            "narx": forms.NumberInput(attrs={"class": "kirish raqam-maydon", "step": "0.01",
                                             "inputmode": "decimal"}),
            "qoldiq": forms.NumberInput(attrs={"class": "kirish raqam-maydon", "step": "0.001",
                                               "inputmode": "decimal"}),
        }


class KirimForm(forms.Form):
    """Omborga tovar kirimi."""

    miqdor = forms.DecimalField(
        label="Kirim miqdori", max_digits=12, decimal_places=3, min_value=0,
        widget=forms.NumberInput(attrs={"class": "kirish raqam-maydon", "step": "0.001",
                                        "inputmode": "decimal"}),
    )
    izoh = forms.CharField(
        label="Izoh", max_length=200, required=False,
        widget=forms.TextInput(attrs={"class": "kirish", "placeholder": "Kimdan / izoh"}),
    )
