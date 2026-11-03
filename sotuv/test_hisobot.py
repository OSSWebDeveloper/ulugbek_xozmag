"""Server kassa hisobotlari va mahsulot xarid narxi testlari."""
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ombor.forms import MahsulotForm
from sotuv.models import Sotuv


class HisobotTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.kassir1 = user_model.objects.create_user(username="kassa_one", password="test-password")
        self.kassir2 = user_model.objects.create_user(username="kassa_two", password="test-password")
        self.client.force_login(self.kassir1)

    @patch("sotuv.hisobot.mahalliymi", return_value=True)
    def test_only_finished_non_cancelled_sales_and_returns(self, _server):
        Sotuv.objects.create(
            kassir=self.kassir1, yakunlangan=True, jami=Decimal("100"),
            qaytarilgan_summa=Decimal("25"), jami_dollar=Decimal("10"),
        )
        Sotuv.objects.create(
            kassir=self.kassir2, yakunlangan=True, jami=Decimal("70"),
        )
        Sotuv.objects.create(
            kassir=self.kassir1, yakunlangan=False, jami=Decimal("500"),
        )
        Sotuv.objects.create(
            kassir=self.kassir1, yakunlangan=True,
            bekor_qilingan=True, jami=Decimal("600"),
        )
        url = reverse("sotuv:hisobot")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["soni"], 2)
        self.assertEqual(r.context["jami_som"], Decimal("145"))
        self.assertEqual(r.context["jami_dollar"], Decimal("10"))

        r = self.client.get(url, {"kassir": self.kassir1.pk})
        self.assertEqual(r.context["soni"], 1)
        self.assertEqual(r.context["jami_som"], Decimal("75"))

    @patch("sotuv.hisobot.mahalliymi", return_value=False)
    def test_report_is_forbidden_from_other_computers(self, _server):
        r = self.client.get(reverse("sotuv:hisobot"))
        self.assertEqual(r.status_code, 403)


class XaridNarxiTests(TestCase):
    def test_purchase_price_and_currency_saved(self):
        form = MahsulotForm({
            "nom": "Sinov mahsuloti",
            "birlik": "dona", "valyuta": "som",
            "narx": "15000", "kelish_narxi": "10500",
            "kelish_valyutasi": "som", "qoldiq": "5",
            "faol": "on",
        }, yangi=True)
        self.assertTrue(form.is_valid(), form.errors.as_text())
        m = form.save()
        self.assertEqual(m.kelish_narxi, Decimal("10500"))
        self.assertEqual(m.kelish_valyutasi, "som")

    def test_negative_purchase_price_rejected(self):
        form = MahsulotForm({
            "nom": "Boshqa mahsulot", "birlik": "dona",
            "kelish_narxi": "-5",
        }, yangi=True)
        self.assertFalse(form.is_valid())
        self.assertIn("kelish_narxi", form.errors)
