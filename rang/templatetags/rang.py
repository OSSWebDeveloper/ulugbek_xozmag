"""Rang cheki summalari: so'm va dollar alohida — hech qayerda qo'shilmaydi."""
from django import template

from qarz.templatetags.xozmag import pul, tekis

register = template.Library()


@register.filter
def tolov_matni(buyurtma):
    """«135 000 so'm» yoki dollarlik bazada «12 $ va 15 000 so'm»."""
    bolaklar = []
    if buyurtma.jami_dollar:
        bolaklar.append(f"{tekis(buyurtma.jami_dollar)} $")
    if buyurtma.jami_som or not bolaklar:
        bolaklar.append(f"{pul(buyurtma.jami_som)} so'm")
    return " va ".join(bolaklar)


@register.simple_tag
def qator_rang_cheklari(hujjat, qator):
    """Kassa qatoriga tushgan rang cheklari — qator shu chekning baza bo'yog'i bo'lsa."""
    return [b for b in hujjat.rang_buyurtmalari.all() if b.baza_id == qator.mahsulot_id]


@register.filter
def baza_summa_matni(buyurtma):
    """Baza bo'yoq summasi o'z valyutasida: «240 000 so'm» yoki «24 $»."""
    if buyurtma.dollarmi:
        return f"{tekis(buyurtma.baza_summa)} $"
    return f"{pul(buyurtma.baza_summa)} so'm"
