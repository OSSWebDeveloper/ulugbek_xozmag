"""Kassalar tarmog'i: server manzili routerda band qilinadi (DHCP reservation).

Dastur Windows'ning IP sozlamalariga tegmaydi. Router server kompyuteriga
har doim bir xil manzil beradi; bu sahifa routerga yoziladigan ma'lumotni
(MAC, joriy IP) ko'rsatadi va band qilingan manzil amalda kelganini tekshiradi.
"""
import ipaddress
import json
from pathlib import Path
from django import forms
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from sotuv.chek import mahalliymi
from config.tarmoq import ip_manzillar, doimiy_manzil, karta


def path():
    return Path(settings.MALUMOT_DIR)/'qurilmalar_data/kassalar.json'


def config():
    try:
        data = json.loads(path().read_text(encoding='utf-8'))
        return {'server_ip': str(data.get('server_ip', ''))}
    except (OSError, ValueError, AttributeError):
        return {'server_ip': ''}


class KassaForm(forms.Form):
    server_ip = forms.GenericIPAddressField(label='Routerda band qilingan server IP', protocol='IPv4')

    def clean_server_ip(self):
        ip = ipaddress.ip_address(self.cleaned_data['server_ip'])
        if not ip.is_private or ip.is_loopback or ip.is_link_local:
            raise forms.ValidationError('Mahalliy tarmoq IPv4 manzilini kiriting.')
        if ip.packed[-1] in (0, 255):
            raise forms.ValidationError('.0 va .255 bilan tugaydigan manzil ishlatilmaydi.')
        return str(ip)


def holat(saved, live, info):
    """Reservation holati: (kod, xabar). Kod — yoq / qolda / belgilanmagan / farq / tayyor."""
    if not live:
        return 'yoq', 'Kompyuter tarmoqqa ulanmagan.'
    if info and not info['dhcp']:
        return 'qolda', ('Bu kompyuterda IP qo‘lda yozilgan. Windows tarmoq sozlamasida '
                         'IP olishni avtomatik (DHCP) qiling — aks holda routerdagi band qilish ishlamaydi.')
    if not saved:
        return 'belgilanmagan', 'Routerda manzilni band qiling, so‘ng uni shu yerga yozib saqlang.'
    if saved not in live:
        return 'farq', (f'Router {live[0]} berdi, band qilingan manzil esa {saved}. '
                        'Routerda band qilish saqlanmagan yoki kompyuter tarmoqqa qayta ulanmagan.')
    return 'tayyor', f'Tayyor: router shu kompyuterga band qilingan {saved} manzilini berdi.'


def sahifa(request):
    if not mahalliymi(request):
        return HttpResponseForbidden('Kassalar sozlamasi faqat server kompyuterida ochiladi.')
    saved = config()['server_ip']
    live = ip_manzillar()
    form = KassaForm(request.POST or None, initial={'server_ip': saved or (live[0] if live else '')})
    if request.method == 'POST' and form.is_valid():
        try:
            # Faqat yozib qo'yiladi: Windows IP sozlamasi o'zgartirilmaydi,
            # server qayta ishga tushirilmaydi.
            target = path()
            target.parent.mkdir(parents=True, exist_ok=True)
            temp = target.with_suffix('.tmp')
            temp.write_text(json.dumps(form.cleaned_data), encoding='utf-8')
            temp.replace(target)
            messages.success(request, 'Band qilingan manzil saqlandi.')
            return redirect('kassalar')
        except OSError as exc:
            form.add_error(None, 'Sozlamalarni saqlab bo‘lmadi: ' + str(exc))
    for field in form.fields.values():
        field.widget.attrs['class'] = 'kirish'
    asosiy = saved if saved in live else (live[0] if live else '')
    info = karta(asosiy) if asosiy else {}
    kod, xabar = holat(saved, live, info)
    return render(request, 'kassalar.html', {
        'form': form, 'live_ip': asosiy, 'karta': info, 'holat': kod, 'holat_xabar': xabar,
        'server_url': doimiy_manzil(request.get_port(), request.scheme)})
