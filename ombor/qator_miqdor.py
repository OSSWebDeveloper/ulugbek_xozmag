"""Sotuv va qarz qatoridagi katta raqamli klaviatura uchun umumiy amal."""
from decimal import Decimal
from django import forms
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from .forms import VergulliDecimal
from .xizmat import OmborXatosi, qator_miqdorini_qoy


class MiqdorForm(forms.Form):
    amal = forms.ChoiceField(choices=[('almashtirish', 'Almashtirish'), ('kopaytirish', 'Ko‘paytirish')], required=False)
    miqdor = VergulliDecimal(max_digits=12, decimal_places=3, min_value=Decimal('.001'))
    eski_miqdor = VergulliDecimal(max_digits=12, decimal_places=3, min_value=Decimal('.001'))

    def clean(self):
        data = super().clean()
        if 'miqdor' in data and 'eski_miqdor' in data:
            yangi = data['miqdor']
            if data.get('amal') == 'kopaytirish':
                yangi *= data['eski_miqdor']
            if yangi < Decimal('.001') or yangi > Decimal('999999999.999') or yangi != yangi.quantize(Decimal('.001')):
                raise forms.ValidationError('Natija musbat bo‘lsin va ko‘pi bilan 3 kasr xonasi bo‘lsin.')
            data['yangi_miqdor'] = yangi
        return data


@transaction.atomic
def yangila(request, pk, model, hujjat_turi, sahifa, yopiqni_tekshir):
    qator = get_object_or_404(model, pk=pk)
    document_model = model._meta.get_field(hujjat_turi).related_model
    from config.kassa import hujjat as kassa_hujjati
    hujjat = kassa_hujjati(request, document_model, getattr(qator, hujjat_turi + '_id'))
    if request.method != 'POST':
        return redirect(sahifa, pk=hujjat.pk)
    closed = yopiqni_tekshir(request, hujjat)
    if closed:
        return closed
    form = MiqdorForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Miqdor va natija musbat son bo‘lsin (ko‘pi bilan 3 kasr xonasi).')
        return redirect(sahifa, pk=hujjat.pk)
    try:
        qator_miqdorini_qoy(qator, form.cleaned_data['yangi_miqdor'], form.cleaned_data['eski_miqdor'],
                            f'{hujjat_turi.capitalize()} #{hujjat.pk}: qator miqdori o‘zgartirildi')
        request.session[hujjat_turi + '_yangi_qator'] = qator.pk
    except OmborXatosi as exc:
        messages.error(request, str(exc))
    return redirect(sahifa, pk=hujjat.pk)
