from decimal import Decimal
from unittest.mock import patch
from django.test import override_settings
from django.urls import reverse
from config.sinov import KirganTest
from ombor.models import Mahsulot
from ombor.xizmat import hujjatga_qosh
from qarz.models import Hudud, Qarzdor, Qarz
from .models import Sotuv
from . import chek


class SavdoChekTests(KirganTest):
    def setUp(self):
        super().setUp()
        self.m = Mahsulot.objects.create(nom='Lampochka', qoldiq=100)
        self.s = Sotuv.objects.create()
        self.row = hujjatga_qosh(self.s.qatorlar, self.m, Decimal(20), 'Sinov')

    def finish(self):
        return self.client.post(reverse('sotuv:yakunlash', args=[self.s.pk]), {'jami':'200000'})

    def test_receipt_has_snapshot_prices_and_no_shop_brand(self):
        self.row.narx = Decimal('10000')
        self.row.save()
        self.m.narx = Decimal('90000')
        self.m.save()
        data = chek.malumot(self.s)
        self.assertEqual(data['nom'], 'SAVDO CHEKI')
        detail = next(b for b in data['blocks'] if b['kind'] == 'detail')
        self.assertEqual(detail['text'], '20 dona x 10 000')
        self.assertEqual(detail['right'], "200 000 so'm")
        self.assertNotIn('XOZMAG', str(data).upper())
        self.assertEqual(chek.och(data['barcode']), self.s.pk)

    def test_receipt_code_cannot_be_confused_with_product_weight_or_paint(self):
        value = chek.kod(self.s.pk)
        self.assertEqual(len(value), 12)
        self.assertTrue(value.startswith('88'))
        self.assertEqual(chek.och(value), self.s.pk)
        self.assertIsNone(chek.och(value[:-1] + str((int(value[-1])+1)%10)))
        for invalid in ['0001','2000098004452','770000000123']:
            self.assertIsNone(chek.och(invalid))

    @override_settings(CHEK_AUTO_PRINT=True)
    @patch('sotuv.chek.chop_et')
    def test_finalize_prints_once_even_on_repeated_post(self, printer):
        response = self.finish()
        self.assertRedirects(response, reverse('sotuv:boshlash'), fetch_redirect_response=False)
        self.finish()
        printer.assert_called_once()
        self.s.refresh_from_db()
        self.assertTrue(self.s.yakunlangan)

    @override_settings(CHEK_AUTO_PRINT=True)
    @patch('sotuv.chek.chop_et', side_effect=RuntimeError('offline'))
    def test_printer_failure_does_not_undo_sale(self, printer):
        self.finish()
        self.s.refresh_from_db(); self.m.refresh_from_db()
        self.assertTrue(self.s.yakunlangan)
        self.assertEqual(self.m.qoldiq, 80)

    def test_scan_opens_return_selection_without_changing_stock(self):
        self.finish()
        data = self.client.get(reverse('ombor:kod_qidir'), {'k':chek.kod(self.s.pk)}).json()
        expected = reverse('sotuv:chek_qaytarish', args=[self.s.pk])
        self.assertEqual(data['qaytarish_manzili'], expected)
        response = self.client.get(expected)
        self.assertContains(response, 'Lampochka')
        self.assertContains(response, reverse('sotuv:qaytarish', args=[self.row.pk]))
        self.m.refresh_from_db(); self.row.refresh_from_db()
        self.assertEqual(self.m.qoldiq, 80)
        self.assertEqual(self.row.qaytarilgan, 0)

    def test_open_and_cancelled_receipts_cannot_be_used(self):
        url = reverse('sotuv:chek_qaytarish', args=[self.s.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.s.yakunlangan=True; self.s.bekor_qilingan=True; self.s.save()
        self.assertEqual(self.client.get(url).status_code, 404)
        response = self.client.get(reverse('ombor:kod_qidir'), {'k':chek.kod(self.s.pk)})
        self.assertNotIn('qaytarish_manzili', response.json())

    def test_receipt_print_preview_and_manual_reprint_are_separate(self):
        self.finish()
        with patch('sotuv.chek.chop_et') as printer:
            response = self.client.get(reverse('sotuv:chek', args=[self.s.pk]))
            self.assertContains(response, chek.kod(self.s.pk))
            self.assertContains(response, '200 000')
            printer.assert_not_called()
            self.client.post(reverse('sotuv:chek_chop', args=[self.s.pk]))
            printer.assert_called_once()

    def test_partial_return_then_rescan_and_overreturn_rejected(self):
        self.finish()
        url = reverse('sotuv:qaytarish', args=[self.row.pk])
        self.client.post(url, {'miqdor':'5','summa':'50000'})
        self.row.refresh_from_db(); self.m.refresh_from_db()
        self.assertEqual(self.row.qaytarilgan,5)
        self.assertEqual(self.m.qoldiq,85)
        self.client.post(url, {'miqdor':'20','summa':'200000'})
        self.row.refresh_from_db(); self.m.refresh_from_db()
        self.assertEqual(self.row.qaytarilgan,5)
        self.assertEqual(self.m.qoldiq,85)

    @patch('sotuv.chek.chop_et')
    def test_history_reprint_button_does_not_change_stock_or_money(self, printer):
        self.finish()
        self.s.refresh_from_db(); self.m.refresh_from_db()
        stock, money = self.m.qoldiq, self.s.jami
        response = self.client.get(reverse('sotuv:royxat'))
        self.assertContains(response, 'Chekni qayta chiqarish')
        result = self.client.post(reverse('sotuv:chek_chop', args=[self.s.pk]), {'royxatga':'ha'})
        self.assertTrue(result.url.startswith(reverse('sotuv:royxat') + '?kun='))
        printer.assert_called_once()
        self.s.refresh_from_db(); self.m.refresh_from_db()
        self.assertEqual(self.m.qoldiq, stock)
        self.assertEqual(self.s.jami, money)
