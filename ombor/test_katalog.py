import json
import tempfile
from decimal import Decimal
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from .models import Mahsulot


class KatalogTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'katalog.json'
        self.row = dict(kod='0001', nom='Sinov', sotish_birligi='dona',
                        kelish_birligi='pachka', konvertatsiya='12',
                        sotish_narxi='11000', sotish_valyutasi='UZS',
                        kelish_narxi='9', kelish_valyutasi='USD', shtrix_kod=None)

    def load(self, rows, **options):
        self.path.write_text(json.dumps(rows), encoding='utf-8')
        call_command('katalog_yukla', str(self.path), verbosity=0, **options)

    def test_import_currencies_and_conversion(self):
        self.load([self.row])
        m = Mahsulot.objects.get()
        self.assertEqual(m.kod, '0001')
        self.assertEqual(m.narx, Decimal('11000'))
        self.assertEqual(m.valyuta, 'som')
        self.assertEqual(m.kelish_narxi, Decimal('9'))
        self.assertEqual(m.kelish_valyutasi, 'dollar')
        self.assertEqual(m.sotuvga_aylantir(2, 'pachka'), Decimal('24'))
        self.assertEqual(m.qoldiq, 0)
        self.assertEqual(m.manba, self.row)

    def test_existing_warehouse_is_untouched(self):
        self.load([self.row])
        with self.assertRaises(CommandError):
            self.load([self.row])
        self.assertEqual(Mahsulot.objects.count(), 1)

    def test_invalid_second_row_leaves_no_partial_import(self):
        with self.assertRaises(CommandError):
            self.load([self.row, dict(self.row, kod='0002')])
        self.assertEqual(Mahsulot.objects.count(), 0)

    def test_dry_run_and_missing_prices(self):
        row = dict(self.row, sotish_narxi=None, kelish_narxi=None, kelish_valyutasi=None)
        self.load([row], tekshir=True)
        self.assertEqual(Mahsulot.objects.count(), 0)
        self.load([row])
        self.assertIsNone(Mahsulot.objects.get().kelish_narxi)
        self.assertIsNone(Mahsulot.objects.get().manba['sotish_narxi'])
