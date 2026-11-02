"""Local-server cashier network setup; changes only extra IPv4 addresses."""
import ipaddress
import json
import os
from pathlib import Path
import subprocess
from django import forms
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from sotuv.chek import mahalliymi


def path():
    return Path(settings.MALUMOT_DIR)/'qurilmalar_data/kassalar.json'


def config():
    try:
        return json.loads(path().read_text(encoding='utf-8'))
    except FileNotFoundError:
        return {'server_ip':'192.168.153.25','client_ip':'192.168.153.26','interface':13}


class KassaForm(forms.Form):
    server_ip=forms.GenericIPAddressField(label='Server IP',protocol='IPv4')
    client_ip=forms.GenericIPAddressField(label='2-kassa IP',protocol='IPv4')
    interface=forms.IntegerField(label='Tarmoq kartasi indeksi',min_value=1)
    def clean(self):
        data=super().clean()
        a,b=data.get('server_ip'),data.get('client_ip')
        if a and b:
            network=ipaddress.ip_network(a+'/24',strict=False)
            if not network.is_private or any(ipaddress.ip_address(v).is_loopback or ipaddress.ip_address(v).is_link_local for v in (a,b)):
                raise forms.ValidationError('Mahalliy tarmoq IPv4 manzilini kiriting.')
            if a==b or ipaddress.ip_address(b) not in network or any(ipaddress.ip_address(v) in (network.network_address,network.broadcast_address) for v in (a,b)):
                raise forms.ValidationError('IP lar bir /24 tarmoqda, turlicha bo‘lsin; .0 va .255 ishlatilmaydi.')
        return data


def sahifa(request):
    if not mahalliymi(request):
        return HttpResponseForbidden('Kassalar sozlamasi faqat server kompyuterida ochiladi.')
    saved=config()
    form=KassaForm(request.POST or None,initial=saved)
    if request.method=='POST' and form.is_valid():
        try:
            exe=Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32/WindowsPowerShell/v1.0/powershell.exe'
            result=subprocess.run([str(exe),'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(Path(__file__).with_name('kassa_ip.ps1')),'-Address',form.cleaned_data['server_ip'],'-InterfaceIndex',str(form.cleaned_data['interface'])],capture_output=True,timeout=20,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if result.returncode:
                raise RuntimeError('IP qo‘llanmadi. Serverni administrator sifatida oching; tarmoq kartasi va IP band emasligini tekshiring.')
            target=path();target.parent.mkdir(parents=True,exist_ok=True)
            temp=target.with_suffix('.tmp');temp.write_text(json.dumps(form.cleaned_data),encoding='utf-8');temp.replace(target)
            messages.success(request,'Server IP saqlandi va tarmoq kartasiga qo‘llandi.')
            return redirect('kassalar')
        except (OSError,subprocess.SubprocessError,RuntimeError) as exc:
            form.add_error(None,str(exc))
    for field in form.fields.values():field.widget.attrs['class']='kirish'
    return render(request,'kassalar.html',{'form':form,'network':saved})
