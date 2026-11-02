from django.test import TestCase
from .forms import MahsulotForm
from .models import Mahsulot
from .kod import topish
from .excel import tovarlar


class ShtrixTests(TestCase):
    def form(self, value, name='Mahsulot'):
        return MahsulotForm({'nom':name,'shtrix_kod':value,'birlik':'dona','valyuta':'som','faol':'on'})

    def test_saved_factory_code_is_scannable_and_searchable(self):
        form = self.form('4780012345678')
        self.assertTrue(form.is_valid(), form.errors)
        product = form.save()
        self.assertEqual(topish('4780012345678').mahsulot, product)
        self.assertEqual(list(tovarlar(q='4780012345678')), [product])
        duplicate = self.form('4780012345678', 'Boshqa')
        self.assertFalse(duplicate.is_valid())

    def test_multiple_empty_codes_are_allowed(self):
        for name in ['Birinchi', 'Ikkinchi']:
            form = self.form('', name)
            self.assertTrue(form.is_valid(), form.errors)
            self.assertIsNone(form.save().shtrix_kod)

    def test_receipt_and_scale_prefixes_cannot_be_factory_codes(self):
        for code in ['880000000248','770000000123','2000098004452','abcd','1234']:
            self.assertFalse(self.form(code).is_valid(), code)

from config.sinov import KirganTest
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model


class InlineShtrixTests(KirganTest):
    def setUp(self):
        super().setUp()
        self.product = Mahsulot.objects.create(nom='Sinov tovar', qoldiq=42)
        self.url = reverse('ombor:shtrix_saqlash', args=[self.product.pk])

    def test_save_clear_and_conflict_do_not_change_stock_or_internal_code(self):
        code = self.product.kod
        self.assertEqual(self.client.post(self.url, {'shtrix_kod':'4780012345678'}).status_code,200)
        self.assertEqual(self.client.post(self.url, {'shtrix_kod':'4780012345679'}).status_code,409)
        self.product.refresh_from_db()
        self.assertEqual(self.product.shtrix_kod,'4780012345678')
        self.assertEqual(self.product.qoldiq,42)
        self.assertEqual(self.product.kod,code)
        self.assertEqual(self.client.post(self.url, {'shtrix_kod':'','eski':'4780012345678'}).status_code,200)
        self.product.refresh_from_db()
        self.assertIsNone(self.product.shtrix_kod)

    def test_invalid_or_duplicate_code_is_not_saved(self):
        Mahsulot.objects.create(nom='Boshqa',shtrix_kod='4780012345678')
        for code in ['123','4780012345678','2000098004452']:
            self.assertEqual(self.client.post(self.url, {'shtrix_kod':code}).status_code,400)
        self.product.refresh_from_db()
        self.assertIsNone(self.product.shtrix_kod)

    def test_auth_post_and_csrf_required(self):
        self.assertEqual(self.client.get(self.url).status_code,405)
        self.assertEqual(Client().post(self.url).status_code,302)
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(get_user_model().objects.get(username=self.LOGIN))
        self.assertEqual(csrf.post(self.url, {'shtrix_kod':'4780012345678'}).status_code,403)
