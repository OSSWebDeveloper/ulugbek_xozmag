import csv
from decimal import Decimal
import tempfile
from pathlib import Path
from django.core.management import call_command
from django.test import TestCase
from ombor.models import Mahsulot
from ombor.kod import topish, ichki_shtrix
from config.rongta import prepare


class KgKodTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.report = str(Path(self.directory.name) / 'codes.csv')
        self.dona = Mahsulot.objects.create(nom='Lampochka', kod='0001', tarozi_kodi='000001', qoldiq=10, narx=5000)
        self.kg = Mahsulot.objects.create(nom='Mix', kod='0098', tarozi_kodi='000098', birlik='kg', qoldiq=Decimal('9995.105'), narx=32000)

    def apply(self):
        call_command('kg_kod_boshida', qolla=True, hisobot=self.report, verbosity=0)

    def test_dry_run_only_writes_mapping(self):
        call_command('kg_kod_boshida', hisobot=self.report, verbosity=0)
        self.kg.refresh_from_db(); self.dona.refresh_from_db()
        self.assertEqual(self.kg.kod, '0098')
        self.assertEqual(self.dona.kod, '0001')
        with open(self.report, encoding='utf-8-sig') as source:
            rows = list(csv.DictReader(source))
        self.assertEqual(rows[0]['Yangi kod'], '0001')

    def test_codes_kg_first_preserve_stock_price_and_old_weight_labels(self):
        old_label = ichki_shtrix(self.kg.kod, Decimal('.445'))
        self.apply()
        self.kg.refresh_from_db(); self.dona.refresh_from_db()
        self.assertEqual(self.kg.kod, '0001')
        self.assertEqual(self.dona.kod, '0002')
        self.assertEqual(self.kg.qoldiq, Decimal('9995.105'))
        self.assertEqual(self.kg.narx, 32000)
        self.assertEqual(topish('1').mahsulot, self.kg)
        result = topish(old_label)
        self.assertEqual(result.mahsulot, self.kg)
        self.assertEqual(result.miqdor, Decimal('.445'))
        self.assertEqual(topish(ichki_shtrix('0001', 1)).mahsulot, self.dona)

    def test_scale_has_new_keyboard_plu_and_stable_barcode_code(self):
        self.apply()
        rows, _ = prepare()
        self.assertEqual(rows[0]['LFCode'], 1)
        self.assertEqual(rows[0]['Code'], '98')

    def test_repeat_is_stable(self):
        self.apply(); self.apply()
        self.kg.refresh_from_db()
        self.assertEqual(self.kg.kod, '0001')
        self.assertEqual(self.kg.tarozi_kodi, '000098')

    def test_unknown_barcode_is_not_resolved_to_reused_manual_code(self):
        self.apply()
        self.assertIsNone(topish(ichki_shtrix('0002', 1)).mahsulot)

    def test_future_kg_gets_unused_stable_identity(self):
        self.apply()
        newer = Mahsulot.objects.create(nom='Yangi mix', kod='0003', birlik='kg', narx=500)
        prepare()
        newer.refresh_from_db()
        self.assertEqual(newer.tarozi_kodi, '000099')
        self.assertEqual(topish(ichki_shtrix(newer.tarozi_kodi, 1)).mahsulot, newer)
