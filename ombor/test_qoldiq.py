from decimal import Decimal

from django.urls import reverse

from config.sinov import KirganTest
from .models import HarakatTuri, Mahsulot


class QoldiqTuzatishTests(KirganTest):
    def setUp(self):
        super().setUp()
        self.m = Mahsulot.objects.create(nom='Shisha', qoldiq=10)
        self.url = reverse('ombor:qoldiq_tuzatish', args=[self.m.pk])

    def test_breakage_reason_is_optional_and_history_retains_before_after(self):
        response = self.client.post(self.url, {'eski_qoldiq': '10', 'qoldiq': '8', 'sabab': ''})
        self.assertRedirects(response, reverse('ombor:royxat'))
        self.m.refresh_from_db()
        self.assertEqual(self.m.qoldiq, 8)
        h = self.m.harakatlar.get()
        self.assertEqual(h.tur, HarakatTuri.TUZATISH)
        self.assertEqual(h.miqdor, -2)
        self.assertIn('10 → 8', h.izoh)

    def test_reason_saved_and_zero_allowed(self):
        self.client.post(self.url, {'eski_qoldiq': '10', 'qoldiq': '0', 'sabab': 'Singan'})
        self.m.refresh_from_db()
        self.assertEqual(self.m.qoldiq, 0)
        self.assertIn('Singan', self.m.harakatlar.get().izoh)

    def test_negative_and_unchanged_rejected(self):
        for value in ['-1', '10']:
            response = self.client.post(self.url, {'eski_qoldiq': '10', 'qoldiq': value})
            self.assertEqual(response.status_code, 200)
        self.assertFalse(self.m.harakatlar.exists())
        self.m.refresh_from_db()
        self.assertEqual(self.m.qoldiq, 10)

    def test_stale_form_does_not_overwrite_sale(self):
        Mahsulot.objects.filter(pk=self.m.pk).update(qoldiq=9)
        response = self.client.post(self.url, {'eski_qoldiq': '10', 'qoldiq': '8'})
        self.assertContains(response, 'Qoldiq bu orada')
        self.m.refresh_from_db()
        self.assertEqual(self.m.qoldiq, 9)
        self.assertFalse(self.m.harakatlar.exists())

    def test_kg_decimal_and_read_only_form(self):
        self.m.birlik = 'kg'
        self.m.save()
        response = self.client.get(self.url)
        self.assertContains(response, 'Sabab (ixtiyoriy)')
        self.assertFalse(self.m.harakatlar.exists())
        self.client.post(self.url, {'eski_qoldiq': '10', 'qoldiq': '9,25'})
        self.m.refresh_from_db()
        self.assertEqual(self.m.qoldiq, Decimal('9.25'))
        self.assertEqual(self.m.harakatlar.get().miqdor, Decimal('-.75'))
