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
def tekis(qiymat):
    """Miqdorni o'qishga qulay qiladi: 120.000 -> '120', 5000 -> '5 000', 2.500 -> '2.5'."""
    son = _decimalga(qiymat)
    if son is None:
        return qiymat
    if son == son.to_integral_value():
        return f"{son.to_integral_value():,f}".replace(",", " ")
    butun, _, kasr = f"{son.normalize():f}".partition(".")
    butun = f"{int(butun):,}".replace(",", " ")
    return f"{butun}.{kasr}" if kasr else butun
