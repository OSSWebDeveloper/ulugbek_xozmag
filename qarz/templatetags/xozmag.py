"""Sonlarni odam o'qiydigan ko'rinishga keltiruvchi filtrlar."""
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django import template

register = template.Library()


def _decimalga(qiymat):
    try:
        return Decimal(str(qiymat).replace(" ", "").replace(",", "."))
    except (InvalidOperation, TypeError, ValueError):
        return None


@register.filter
def pul(qiymat):
    """550000 -> '550 000'. Butun songa yaxlitlanadi."""
    son = _decimalga(qiymat)
    if son is None:
        return qiymat
    return f"{son.quantize(Decimal('1'), rounding=ROUND_HALF_UP):,f}".replace(",", " ")


@register.filter
def narxi(mahsulot):
    """Tovar narxini o'z valyutasida yozadi: «45 000 so'm» yoki «12,5 $».

    Narx yozilmagan bo'lsa bo'sh matn — ro'yxatda chiziqcha ko'rinadi.
    """
    if not getattr(mahsulot, "narx", None):
        return ""
    if mahsulot.dollarmi:
        return f"{tekis(mahsulot.narx)} $"
    return f"{pul(mahsulot.narx)} so'm"


@register.filter
def tekis(qiymat):
    """Miqdorni o'qishga qulay qiladi: 120.000 -> '120', 5000 -> '5 000', 2.500 -> '2,5'.

    Kasr vergul bilan — saytning qolgan joyi (JS hisoblari) ham shunday
    ko'rsatadi, ikki xil belgi chalkashtirmasin.
    """
    son = _decimalga(qiymat)
    if son is None:
        return qiymat
    if son == son.to_integral_value():
        return f"{son.to_integral_value():,f}".replace(",", " ")
    butun, _, kasr = f"{son.normalize():f}".partition(".")
    manfiy = butun.startswith("-")
    butun = f"{abs(int(butun)):,}".replace(",", " ")
    if manfiy:
        butun = "-" + butun
    return f"{butun},{kasr}" if kasr else butun
