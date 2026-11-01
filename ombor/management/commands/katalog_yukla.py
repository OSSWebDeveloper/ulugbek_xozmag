"""Tayyor katalog JSON'ini faqat bo'sh omborga yuklaydi."""
import json
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ombor.models import Birlik, Mahsulot, KOD_MAX, kod_yasa


class Command(BaseCommand):
    help = "Tayyor mahsulotlar katalogini bo'sh omborga yuklash"

    def add_arguments(self, parser):
        parser.add_argument('fayl', type=Path)
        parser.add_argument('--tekshir', action='store_true', help="Bazaga yozmasdan tekshirish")

    def handle(self, *args, **options):
        try:
            rows = json.loads(options['fayl'].read_text(encoding='utf-8'))
        except (OSError, ValueError) as exc:
            raise CommandError(f'Katalog o‘qilmadi: {exc}') from exc
        products, codes, names = [], set(), set()
        try:
            for i, row in enumerate(rows, 1):
                code, name = row['kod'], row['nom']
                assert code.isdigit() and int(code) == i and i <= KOD_MAX, 'Tartib kodi mos emas'
                code = kod_yasa(i)
                assert code not in codes and name not in names, 'Takroriy mahsulot'
                assert name and len(name) <= 120, 'Mahsulot nomi noto‘g‘ri'
                assert row['sotish_valyutasi'] == 'UZS', 'Sotish narxi UZS bo‘lishi kerak'
                assert row['sotish_birligi'] in Birlik.values, 'Sotish birligi noto‘g‘ri'
                assert row['kelish_birligi'] in Birlik.values, 'Kelish birligi noto‘g‘ri'
                factor = Decimal(row['konvertatsiya'])
                assert factor > 0, 'Konvertatsiya musbat bo‘lishi kerak'
                codes.add(code)
                names.add(name)
                product = Mahsulot(
                    kod=code, nom=name, birlik=row['sotish_birligi'],
                    olish_birligi=row['kelish_birligi'] if row['kelish_birligi'] != row['sotish_birligi'] else '',
                    olish_miqdori=factor, narx=Decimal(row['sotish_narxi'] or '0'),
                    valyuta='som', qoldiq=0, faol=True,
                    kelish_narxi=Decimal(row['kelish_narxi']) if row['kelish_narxi'] is not None else None,
                    kelish_valyutasi={'USD': 'dollar', 'UZS': 'som', None: ''}[row['kelish_valyutasi']],
                    manba=row,
                )
                product.full_clean(validate_unique=False, validate_constraints=False)
                products.append(product)
        except Exception as exc:
            raise CommandError(f'{i}-mahsulot tekshiruvi: {exc}') from exc
        if not products:
            raise CommandError('Katalog bo‘sh')
        if options['tekshir']:
            self.stdout.write(f'{len(products)} mahsulot tekshirildi. Bazaga yozilmadi.')
            return
        with transaction.atomic():
            if Mahsulot.objects.exists():
                raise CommandError('Ombor bo‘sh emas. Mavjud mahsulotlar o‘zgartirilmadi.')
            Mahsulot.objects.bulk_create(products, batch_size=300)
        self.stdout.write(self.style.SUCCESS(f'{len(products)} mahsulot omborga kiritildi.'))
