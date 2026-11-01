from decimal import Decimal
from django.urls import reverse
from config.sinov import KirganTest
from ombor.models import Mahsulot
from ombor.xizmat import hujjatga_qosh, qator_miqdorini_qoy
from ombor.hisob import hisobla
from sotuv.models import Sotuv


class KassaHisobTests(KirganTest):
    def setUp(self):
        super().setUp()
        self.s = Sotuv.objects.create()
        self.m = Mahsulot.objects.create(nom='Lampochka', narx=10000, qoldiq=100)

    def test_twenty_bulbs_and_kg_decimal_totals(self):
        hujjatga_qosh(self.s.qatorlar, self.m, Decimal(20), 'Sinov')
        kg = Mahsulot.objects.create(nom='Mix', narx=32000, birlik='kg', qoldiq=100)
        hujjatga_qosh(self.s.qatorlar, kg, Decimal('.445'), 'Sinov')
        total = hisobla(self.s.qatorlar.all())
        self.assertTrue(total['toliq'])
        self.assertEqual(total['som'], Decimal('214240'))

    def test_currency_stays_separate_and_price_snapshot_does_not_drift(self):
        row = hujjatga_qosh(self.s.qatorlar, self.m, Decimal(2), 'Sinov')
        dollar = Mahsulot.objects.create(nom='Dollar', narx=Decimal('2.35'), valyuta='dollar', qoldiq=100)
        hujjatga_qosh(self.s.qatorlar, dollar, Decimal(3), 'Sinov')
        self.m.narx=999; self.m.valyuta='dollar'; self.m.save()
        total = hisobla(self.s.qatorlar.all())
        self.assertEqual(total['som'], 20000)
        self.assertEqual(total['dollar'], Decimal('7.05'))
        qator_miqdorini_qoy(row, Decimal(20), Decimal(2), 'Sinov')
        self.assertEqual(hisobla(self.s.qatorlar.all())['som'], 200000)

    def test_missing_price_does_not_present_partial_total_as_complete(self):
        hujjatga_qosh(self.s.qatorlar, self.m, Decimal(2), 'Sinov')
        other = Mahsulot.objects.create(nom='Narxsiz', narx=0, qoldiq=100)
        hujjatga_qosh(self.s.qatorlar, other, Decimal(1), 'Sinov')
        total = hisobla(self.s.qatorlar.all())
        self.assertFalse(total['toliq'])
        self.assertEqual(total['narxsiz'], 1)
        page = self.client.get(reverse('sotuv:tahrir', args=[self.s.pk]))
        self.assertContains(page, 'sotish narxi yo‘q')

    def test_rendered_total_and_negotiated_override(self):
        hujjatga_qosh(self.s.qatorlar, self.m, Decimal(20), 'Sinov')
        page = self.client.get(reverse('sotuv:tahrir', args=[self.s.pk]))
        self.assertContains(page, 'value="200 000"')
        self.client.post(reverse('sotuv:yakunlash', args=[self.s.pk]), {'jami':'190000'})
        self.s.refresh_from_db()
        self.assertEqual(self.s.jami, 190000)
