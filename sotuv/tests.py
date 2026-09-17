"""Naqd sotuv mantiqining sinovlari."""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from ombor.models import Birlik, HarakatTuri, Mahsulot, OmborHarakati

from .models import Sotuv, SotuvQator


class SotuvTest(TestCase):
    def setUp(self):
        self.mahsulot = Mahsulot.objects.create(
            nom="Sement 50 kg", birlik=Birlik.QOP, narx=Decimal("55000"), qoldiq=Decimal("100"),
        )
        self.sotuv = Sotuv.objects.create()

    def test_sotuv_qatori_ombordan_ayiradi(self):
        self.client.post(reverse("sotuv:qator_qoshish", args=[self.sotuv.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "3", "narx": "55000",
        })
        self.mahsulot.refresh_from_db()
        self.assertEqual(self.mahsulot.qoldiq, Decimal("97.000"))
        self.assertEqual(self.sotuv.jami, Decimal("165000.00"))
        harakat = OmborHarakati.objects.filter(tur=HarakatTuri.CHIQIM).first()
        self.assertIn(f"Sotuv #{self.sotuv.pk}", harakat.izoh)

    def test_omborda_yetmasa_qoshilmaydi(self):
        javob = self.client.post(reverse("sotuv:qator_qoshish", args=[self.sotuv.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "500", "narx": "55000",
        }, follow=True)
        self.mahsulot.refresh_from_db()
        self.assertEqual(self.mahsulot.qoldiq, Decimal("100.000"))
        self.assertEqual(self.sotuv.qatorlar.count(), 0)
        self.assertContains(javob, "Omborda yetarli emas")

    def test_qator_ochirilsa_tovar_qaytadi(self):
        self.client.post(reverse("sotuv:qator_qoshish", args=[self.sotuv.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "3", "narx": "55000",
        })
        qator = SotuvQator.objects.get(sotuv=self.sotuv)
        self.client.post(reverse("sotuv:qator_ochirish", args=[qator.pk]))
        self.mahsulot.refresh_from_db()
        self.assertEqual(self.mahsulot.qoldiq, Decimal("100.000"))

    def test_qaytim_hisoblanadi(self):
        SotuvQator.objects.create(
            sotuv=self.sotuv, mahsulot=self.mahsulot, miqdor=Decimal("2"), narx=Decimal("55000"),
        )
        self.client.post(reverse("sotuv:yakunlash", args=[self.sotuv.pk]), {"tolandi": "150000"})
        self.sotuv.refresh_from_db()
        self.assertTrue(self.sotuv.yakunlangan)
        self.assertEqual(self.sotuv.qaytim, Decimal("40000.00"))

    def test_tolov_kiritilmasa_tayyor_summa_hisoblanadi(self):
        SotuvQator.objects.create(
            sotuv=self.sotuv, mahsulot=self.mahsulot, miqdor=Decimal("1"), narx=Decimal("55000"),
        )
        self.client.post(reverse("sotuv:yakunlash", args=[self.sotuv.pk]), {"tolandi": ""})
        self.sotuv.refresh_from_db()
        self.assertEqual(self.sotuv.tolandi, Decimal("55000.00"))
        self.assertEqual(self.sotuv.qaytim, Decimal("0"))

    def test_bosh_sotuv_yakunlanganda_ochiriladi(self):
        self.client.post(reverse("sotuv:yakunlash", args=[self.sotuv.pk]))
        self.assertFalse(Sotuv.objects.filter(pk=self.sotuv.pk).exists())

    def test_bekor_qilinsa_tovarlar_omborga_qaytadi(self):
        self.client.post(reverse("sotuv:qator_qoshish", args=[self.sotuv.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "5", "narx": "55000",
        })
        self.client.post(reverse("sotuv:bekor", args=[self.sotuv.pk]))
        self.mahsulot.refresh_from_db()
        self.assertEqual(self.mahsulot.qoldiq, Decimal("100.000"))
        self.assertFalse(Sotuv.objects.filter(pk=self.sotuv.pk).exists())

    def test_tugallanmagan_sotuv_qayta_ochiladi(self):
        javob = self.client.get(reverse("sotuv:boshlash"))
        self.assertRedirects(javob, reverse("sotuv:tahrir", args=[self.sotuv.pk]))
        self.assertEqual(Sotuv.objects.count(), 1)

    def test_kunlik_tushum_korsatiladi(self):
        SotuvQator.objects.create(
            sotuv=self.sotuv, mahsulot=self.mahsulot, miqdor=Decimal("2"), narx=Decimal("55000"),
        )
        self.client.post(reverse("sotuv:yakunlash", args=[self.sotuv.pk]), {"tolandi": "110000"})
        javob = self.client.get(reverse("sotuv:royxat"))
        self.assertContains(javob, "110 000")

    def test_sotuv_qarzdorga_tegmaydi(self):
        """Naqd sotuv hech kimning qarziga yozilmaydi."""
        from qarz.models import QarzQator

        self.client.post(reverse("sotuv:qator_qoshish", args=[self.sotuv.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "2", "narx": "55000",
        })
        self.assertEqual(QarzQator.objects.count(), 0)
