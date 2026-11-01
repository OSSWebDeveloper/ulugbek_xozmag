from decimal import Decimal
from django.urls import reverse
from config.sinov import KirganTest
from ombor.models import Mahsulot
from ombor.xizmat import hujjatga_qosh
from qarz.models import Qarz, Qarzdor, Hudud
from sotuv.models import Sotuv


class QatorMiqdorTests(KirganTest):
    def setUp(self):
        super().setUp()
        self.m = Mahsulot.objects.create(nom='Lampochka', birlik='dona', qoldiq=100)
        self.sale = Sotuv.objects.create()
        self.row = hujjatga_qosh(self.sale.qatorlar, self.m, Decimal('1'), 'Sinov')
        self.url = reverse('sotuv:qator_miqdor', args=[self.row.pk])

    def test_one_scan_to_twenty_leaves_stock_until_finalization(self):
        self.client.post(self.url, {'miqdor': '20', 'eski_miqdor': '1'})
        self.row.refresh_from_db(); self.m.refresh_from_db()
        self.assertEqual(self.row.miqdor, 20)
        self.assertEqual(self.m.qoldiq, 100)
        self.assertEqual(self.sale.qatorlar.count(), 1)
        self.assertFalse(self.m.harakatlar.exists())

    def test_lower_cart_quantity_leaves_stock_unchanged(self):
        self.client.post(self.url, {'miqdor': '20', 'eski_miqdor': '1'})
        self.client.post(self.url, {'miqdor': '2', 'eski_miqdor': '20'})
        self.m.refresh_from_db()
        self.assertEqual(self.m.qoldiq, 100)

    def test_multiply_cart_quantity_leaves_stock_unchanged(self):
        self.client.post(self.url, {'miqdor': '3', 'eski_miqdor': '1'})
        self.client.post(self.url, {'amal': 'kopaytirish', 'miqdor': '4', 'eski_miqdor': '3'})
        self.row.refresh_from_db(); self.m.refresh_from_db()
        self.assertEqual(self.row.miqdor, 12)
        self.assertEqual(self.m.qoldiq, 100)
        self.assertFalse(self.m.harakatlar.exists())

    def test_multiply_scale_weight_and_replace_are_distinct(self):
        self.client.post(self.url, {'miqdor': '0,445', 'eski_miqdor': '1'})
        self.client.post(self.url, {'amal': 'kopaytirish', 'miqdor': '2', 'eski_miqdor': '0.445'})
        self.row.refresh_from_db(); self.m.refresh_from_db()
        self.assertEqual(self.row.miqdor, Decimal('.890'))
        self.assertEqual(self.m.qoldiq, Decimal('100'))
        self.client.post(self.url, {'amal': 'almashtirish', 'miqdor': '2', 'eski_miqdor': '0.890'})
        self.row.refresh_from_db()
        self.assertEqual(self.row.miqdor, 2)

    def test_invalid_multiplication_and_stale_request_do_not_change_stock(self):
        self.client.post(self.url, {'miqdor': '.445', 'eski_miqdor': '1'})
        for factor, old in [('0.333', '.445'), ('999999999.999', '.445'), ('2', '1'), ('0', '.445')]:
            self.client.post(self.url, {'amal': 'kopaytirish', 'miqdor': factor, 'eski_miqdor': old})
            self.row.refresh_from_db(); self.m.refresh_from_db()
            self.assertEqual(self.row.miqdor, Decimal('.445'))
            self.assertEqual(self.m.qoldiq, Decimal('100'))

    def test_debt_multiplication(self):
        person = Qarzdor.objects.create(ism='Sinov', hudud=Hudud.objects.create(nom='Sinov'))
        debt = Qarz.objects.create(qarzdor=person)
        row = hujjatga_qosh(debt.qatorlar, self.m, Decimal('2'), 'Sinov')
        self.client.post(reverse('qarz:qator_miqdor', args=[row.pk]), {
            'amal': 'kopaytirish', 'miqdor': '3', 'eski_miqdor': '2'})
        row.refresh_from_db()
        self.assertEqual(row.miqdor, 6)

    def test_shortage_invalid_and_stale_do_not_change_anything(self):
        for value, old in [('101','1'), ('0','1'), ('-1','1'), ('NaN','1'), ('1.0001','1'), ('20','2')]:
            self.client.post(self.url, {'miqdor': value, 'eski_miqdor': old})
            self.row.refresh_from_db(); self.m.refresh_from_db()
            self.assertEqual(self.row.miqdor, 1)
            self.assertEqual(self.m.qoldiq, 100)
        self.assertEqual(self.m.harakatlar.count(), 0)

    def test_closed_sale_and_get_cannot_change_stock(self):
        self.client.get(self.url, {'miqdor': '20', 'eski_miqdor': '1'})
        self.sale.yakunlangan = True
        self.sale.save()
        self.client.post(self.url, {'miqdor': '20', 'eski_miqdor': '1'})
        self.row.refresh_from_db(); self.m.refresh_from_db()
        self.assertEqual(self.row.miqdor, 1)
        self.assertEqual(self.m.qoldiq, 100)

    def test_kg_decimal_and_debt_screen(self):
        person = Qarzdor.objects.create(ism='Sinov', hudud=Hudud.objects.create(nom='Sinov'))
        debt = Qarz.objects.create(qarzdor=person)
        row = hujjatga_qosh(debt.qatorlar, self.m, Decimal('1'), 'Sinov')
        url = reverse('qarz:qator_miqdor', args=[row.pk])
        self.client.post(url, {'miqdor': '3,115', 'eski_miqdor': '1'})
        row.refresh_from_db(); self.m.refresh_from_db()
        self.assertEqual(row.miqdor, Decimal('3.115'))
        self.assertEqual(self.m.qoldiq, Decimal('100'))

    def test_sale_template_has_star_and_dialog(self):
        from unittest.mock import patch
        with patch('sotuv.views.oxirgi_kurs', return_value=None):
            response = self.client.get(reverse('sotuv:tahrir', args=[self.sale.pk]))
        self.assertContains(response, 'data-miqdor-och')
        self.assertContains(response, 'id="miqdor-dialog"')
        self.assertContains(response, 'kassa_miqdor.js')
        self.assertContains(response, 'name="amal" value="kopaytirish"')
        self.assertContains(response, 'Miqdorni ko‘paytirish')
        self.assertNotContains(response, 'Miqdorni almashtirish')
