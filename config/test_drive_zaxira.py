import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import TestCase
from openpyxl import load_workbook

from config import drive_zaxira as dz
from ombor.models import Mahsulot


class DriveZaxiraTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        t = Path(self.temp.name)
        self.drive = t / 'drive' / 'Xozmag zaxira'
        self.patches = [patch.object(dz, 'PAPKA', t / 'z'), patch.object(dz, 'NAVBAT', t / 'z' / 'navbat'),
                        patch.object(dz, 'OXIRGI', t / 'z' / 'oxirgi_sana.txt')]
        for p in self.patches:
            p.start()
        (t / 'drive').mkdir()
        Mahsulot.objects.create(nom='Bolg‘a', qoldiq=7, narx=45000)

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.temp.cleanup()

    def test_before_time_nothing_happens(self):
        with patch.object(dz, 'drive_papka', return_value=self.drive):
            dz.bir_qadam(datetime.datetime(2026, 11, 26, 19, 59))
        self.assertFalse(dz.NAVBAT.exists())
        self.assertFalse(self.drive.exists())

    def test_once_a_day_and_retry_when_drive_missing(self):
        with patch.object(dz, 'drive_papka', return_value=None):
            with self.assertRaises(RuntimeError):
                dz.bir_qadam(datetime.datetime(2026, 11, 26, 20, 0))
        nom = 'Xozmag ombor 2026-11-26.xlsx'
        self.assertTrue((dz.NAVBAT / nom).exists())
        with patch.object(dz, 'drive_papka', return_value=self.drive):
            dz.bir_qadam(datetime.datetime(2026, 11, 26, 20, 10))
            dz.bir_qadam(datetime.datetime(2026, 11, 26, 23, 0))
        self.assertEqual([f.name for f in self.drive.iterdir()], [nom])
        ws = load_workbook(self.drive / nom)['Ombor']
        self.assertEqual(ws['B2'].value, 'Bolg‘a')
        self.assertEqual(ws['D2'].value, 7)
        self.assertTrue((dz.PAPKA / nom).exists())
        self.assertFalse((dz.NAVBAT / nom).exists())

    def test_finds_real_drive_folder(self):
        # Shu kompyuterda Drive o'rnatilmagan bo'lsa None — xato bermasligi kerak
        papka = dz.drive_papka()
        self.assertTrue(papka is None or papka.name == 'Xozmag zaxira')
