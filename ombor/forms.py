"""Ombor formalari."""
from decimal import Decimal, InvalidOperation

from django import forms

from .models import Mahsulot, ShtrixKod, Valyuta, tekis_matn
from .xizmat import tozala


class VergulliDecimal(forms.DecimalField):
    """Sonni vergul bilan ham qabul qiladi: `2,5` -> `2.5`.

    Do'konda vergul bilan yozish odat; oddiy DecimalField uni rad etadi.
    Pul maydonlarida son guruhlangan keladi («45 000») — bo'shliqlar ham
    olib tashlanadi (`ombor.xizmat.tozala`).
    """

    def to_python(self, qiymat):
        if isinstance(qiymat, str):
            qiymat = tozala(qiymat)
        return super().to_python(qiymat)


class MahsulotForm(forms.ModelForm):
    """Tovar kartochkasi.

    «Birlik o'zgaradi» richagi yoqilsa forma qadoq bo'yicha savol beradi:
    necha qadoq keldi, qaysi birlikda keldi, qaysi birlikda sotiladi, bitta
    qadoqda nechta. Qoldiq shundan hisoblanadi — operator metrni o'zi
    ko'paytirib o'tirmaydi. Narx bu yerda so'ralmaydi — pul kalkulyatorda
    hisoblanadi; tovardan faqat qaysi pulda kelgani (so'm yoki dollar)
    so'raladi, kassada summa o'sha ustunga yoziladi.
    """

    birlik_ozgaradi = forms.BooleanField(
        label="Birlik o'zgaradi", required=False,
        widget=forms.CheckboxInput(attrs={"class": "richag-kirish", "id": "birlik-ozgaradi"}),
    )
    shtrix = forms.CharField(
        label="Zavod shtrixlari", required=False,
        help_text="Tovarni skanerlang — har bir kod alohida qatorga tushadi. "
                  "Quti kodi bo'lsa yoniga qutidagi sonini yozing: «4780001 1000». "
                  "Qatorni o'chirsangiz kod ham o'chadi.",
        widget=forms.Textarea(attrs={"class": "kirish shtrix-maydon", "rows": 2,
                                     "autocomplete": "off", "spellcheck": "false",
                                     "placeholder": "Skanerlang"}),
    )
    qadoq_soni = VergulliDecimal(
        label="Necha qadoq keldi", max_digits=12, decimal_places=3, min_value=0, required=False,
        widget=forms.TextInput(attrs={"class": "kirish raqam-maydon", "id": "qadoq-soni",
                                      "inputmode": "decimal", "autocomplete": "off",
                                      "placeholder": "0"}),
    )
    class Meta:
        model = Mahsulot
        fields = ["nom", "valyuta", "birlik", "olish_birligi", "olish_miqdori", "narx",
                  "qoldiq", "faol"]
        field_classes = {
            "qoldiq": VergulliDecimal,
            "olish_miqdori": VergulliDecimal,
            "narx": VergulliDecimal,
        }
        widgets = {
            "nom": forms.TextInput(attrs={"class": "kirish", "autocomplete": "off",
                                          "placeholder": "Tovar nomi"}),
            "valyuta": forms.Select(attrs={
                "class": "kirish",
                "title": "Dollarda kelgan tovar summasi kassada alohida yoziladi, "
                         "so'mga qo'shilmaydi",
            }),
            "birlik": forms.Select(attrs={"class": "kirish"}),
            "olish_birligi": forms.Select(attrs={"class": "kirish"}),
            "olish_miqdori": forms.TextInput(attrs={"class": "kirish raqam-maydon",
                                                    "inputmode": "decimal", "autocomplete": "off",
                                                    "placeholder": "masalan 100"}),
            "narx": forms.TextInput(attrs={"class": "kirish raqam-maydon pul-maydon", "id": "id_narx",
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
        # Tanlanmasa so'm: do'kondagi tovarlarning ko'pi so'mda keladi
        self.fields["valyuta"].required = False
        self.fields["olish_birligi"].choices = [("", "— tanlang —")] + [
            (q, n) for q, n in self.fields["olish_birligi"].choices if q
        ]
        if not self.is_bound:
            self.fields["birlik_ozgaradi"].initial = self.instance.ikki_birlikmi
            if self.instance.pk:
                self.initial["shtrix"] = self.shtrixlar_matni()
            sonli = ("qoldiq", "olish_miqdori", "narx")
            if self.instance.pk is None:
                # Yangi tovarda modeldagi standart qiymatlar (0 va 1) maydonda
                # yozuv bo'lib turmasin — placeholder ko'rinib tursin.
                for maydon in sonli:
                    self.initial[maydon] = None
            else:
                # Tahrirlashda ortiqcha nollar ko'rinmasin: 45.00 -> 45, 2.500 -> 2,5
                for maydon in sonli:
                    self.initial[maydon] = tekis_matn(getattr(self.instance, maydon))

    # ---------- Zavod shtrixlari ----------

    def shtrixlar_matni(self):
        """Biriktirilgan kodlarni maydon uchun matnga aylantiradi."""
        qatorlar = []
        for shtrix in self.instance.shtrixlar.all():
            if shtrix.miqdor == 1:
                qatorlar.append(shtrix.kod)
            else:
                qatorlar.append(f"{shtrix.kod} {tekis_matn(shtrix.miqdor)}")
        return "\n".join(qatorlar)

    def clean_shtrix(self):
        """Har bir qatorni «kod [miqdor]» deb o'qiydi.

        Kod boshqa tovarga biriktirilgan bo'lsa saqlanmaydi: bitta shtrix
        ikki tovarni bildirsa kassa qaysi birini olishni bilmaydi.
        """
        natija = {}
        for qator in (self.cleaned_data.get("shtrix") or "").splitlines():
            bolaklar = qator.replace(",", ".").split()
            if not bolaklar:
                continue
            kod, miqdor = bolaklar[0].strip(), Decimal("1")
            if len(bolaklar) > 1:
                try:
                    miqdor = Decimal(bolaklar[1])
                except InvalidOperation:
                    raise forms.ValidationError(
                        f"«{qator.strip()}» tushunarsiz — koddan keyin faqat son yoziladi "
                        f"(qutidagi soni).")
                if miqdor <= 0:
                    raise forms.ValidationError(
                        f"{kod} yonidagi son noldan katta bo'lishi kerak.")
            band = ShtrixKod.objects.filter(kod=kod)
            if self.instance.pk:
                band = band.exclude(mahsulot_id=self.instance.pk)
            band = band.select_related("mahsulot").first()
            if band:
                raise forms.ValidationError(
                    f"{kod} allaqachon «{band.mahsulot.nom}» ga biriktirilgan.")
            natija[kod] = miqdor
        return natija

    def shtrixlarni_saqla(self, mahsulot):
        """Maydonda nima yozilgan bo'lsa tovarning kodlari ham o'sha bo'ladi."""
        kerakli = self.cleaned_data.get("shtrix") or {}
        mahsulot.shtrixlar.exclude(kod__in=kerakli).delete()
        borlar = {s.kod: s for s in mahsulot.shtrixlar.all()}
        for kod, miqdor in kerakli.items():
            bor = borlar.get(kod)
            if bor is None:
                ShtrixKod.objects.create(mahsulot=mahsulot, kod=kod, miqdor=miqdor)
            elif bor.miqdor != miqdor:
                bor.miqdor = miqdor
                bor.save(update_fields=["miqdor"])

    def save(self, commit=True):
        mahsulot = super().save(commit=commit)
        if commit:
            self.shtrixlarni_saqla(mahsulot)
        return mahsulot

    # ---------- Tekshiruv ----------

    def clean_valyuta(self):
        return self.cleaned_data.get("valyuta") or Valyuta.SOM

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
