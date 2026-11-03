"""Mahsulot formasining qayta ishlangan ko'rinishi va narx qoidalari."""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from ombor.forms import MahsulotForm
from ombor.models import Mahsulot, Valyuta, Birlik


class MahsulotFormaTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="forma_user", password="FormTest987!Safe")
        self.client.force_login(self.user)

    def test_purchase_currency_placeholder_is_uzbek(self):
        form = MahsulotForm(yangi=True)
        self.assertEqual(form.fields["kelish_valyutasi"].choices[0],
                         ("", "Sotuv valyutasi bilan bir xil"))

    def test_new_product_form_renders_expected_sections(self):
        response = self.client.get(reverse("ombor:mahsulot_yangi"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Asosiy ma")
        self.assertContains(response, "Narx va valyuta")
        self.assertContains(response, "Ombor va o")
        self.assertContains(response, "mahsulot-farq")

    def test_purchase_price_inherits_sales_currency(self):
        form = MahsulotForm(data={
            "nom": "Sinov tovar dollar",
            "birlik": Birlik.DONA,
            "valyuta": Valyuta.DOLLAR,
            "narx": "12",
            "kelish_narxi": "9",
            "kelish_valyutasi": "",
            "qoldiq": "5",
            "faol": "on",
        }, yangi=True)
        self.assertTrue(form.is_valid(), form.errors.as_text())
        product = form.save()
        self.assertEqual(product.kelish_valyutasi, Valyuta.DOLLAR)

    def test_packed_units_keep_conversion(self):
        form = MahsulotForm(data={
            "nom": "Sinov 3 rulon",
            "birlik": Birlik.METR,
            "valyuta": Valyuta.SOM,
            "narx": "1000",
            "qoldiq": "",
            "faol": "on",
            "birlik_ozgaradi": "on",
            "olish_birligi": Birlik.RULON,
            "olish_miqdori": "100",
            "qadoq_soni": "3",
        }, yangi=True)
        self.assertTrue(form.is_valid(), form.errors.as_text())
        product = form.save()
        self.assertEqual(product.qoldiq, 300)
