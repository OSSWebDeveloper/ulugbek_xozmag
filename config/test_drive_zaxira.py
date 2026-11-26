import datetime
import json
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
        (t / 'google_drive.json').write_text(json.dumps(
            {'client_id': 'a', 'client_secret': 'b', 'refresh_token': 'c'}))
        self.patches = [patch.object(dz, 'SOZLAMA', t / 'google_drive.json'),
                        patch.object(dz, 'PAPKA', t / 'z'), patch.object(dz, 'NAVBAT', t / 'z' / 'navbat'),
                        patch.object(dz, 'OXIRGI', t / 'z' / 'oxirgi_sana.txt')]
        for p in self.patches:
            p.start()
        Mahsulot.objects.create(nom='Bolg‘a', qoldiq=7, narx=45000)

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.temp.cleanup()

    def test_before_time_nothing_happens(self):
        with patch.object(dz, 'yukla') as yukla:
            dz.bir_qadam(datetime.datetime(2026, 11, 26, 19, 59))
        yukla.assert_not_called()
        self.assertFalse(dz.NAVBAT.exists())

    def test_once_a_day_and_retry_after_failure(self):
        with patch.object(dz, 'yukla', side_effect=RuntimeError('internet yo‘q')):
            with self.assertRaises(RuntimeError):
                dz.bir_qadam(datetime.datetime(2026, 11, 26, 20, 0))
        fayl = dz.NAVBAT / 'Xozmag ombor 2026-11-26.xlsx'
        self.assertTrue(fayl.exists())
        ws = load_workbook(fayl)['Ombor']
        self.assertEqual(ws['B2'].value, 'Bolg‘a')
        self.assertEqual(ws['D2'].value, 7)
        with patch.object(dz, 'yukla', return_value='id') as yukla:
            dz.bir_qadam(datetime.datetime(2026, 11, 26, 20, 10))
            dz.bir_qadam(datetime.datetime(2026, 11, 26, 23, 0))
        yukla.assert_called_once()
        self.assertTrue((dz.PAPKA / fayl.name).exists())
        self.assertFalse(fayl.exists())

    def test_without_settings_disabled(self):
        dz.SOZLAMA.unlink()
        with patch.object(dz, 'yukla') as yukla:
            dz.bir_qadam(datetime.datetime(2026, 11, 26, 21, 0))
        yukla.assert_not_called()
