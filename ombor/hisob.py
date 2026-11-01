"""Kassa summalari: qatorga yozilgan sotish narxi × miqdor, valyutalar alohida."""
from decimal import Decimal, ROUND_HALF_UP


def hisobla(qatorlar):
    totals = {'som': Decimal(0), 'dollar': Decimal(0)}
    missing = 0
    count = 0
    for row in qatorlar:
        count += 1
        if row.narx is None or row.valyuta not in totals:
            missing += 1
        else:
            totals[row.valyuta] += row.narx * row.miqdor
    totals['som'] = totals['som'].quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    totals['dollar'] = totals['dollar'].quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    # Narxsiz tovar bor bo'lsa qisman summani to'liq jami sifatida ko'rsatmaymiz.
    return {**totals, 'toliq': bool(count) and not missing, 'narxsiz': missing}
