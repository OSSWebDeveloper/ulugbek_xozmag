"""Qarz va ombor mantiqining asosiy sinovlari."""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from ombor.models import Birlik, HarakatTuri, Mahsulot, OmborHarakati

from .models import Hudud, Qarz, QarzQator, Qarzdor, Tolov


class QarzOqimiTest(TestCase):
    def setUp(self):
        self.hudud = Hudud.objects.create(nom="Hudud 1", tartib=1)
        self.qarzdor = Qarzdor.objects.create(
            ism="Vali", familiya="Aliyev", telefon="+998901234567", hudud=self.hudud,
        )
        self.mahsulot = Mahsulot.objects.create(
            nom="Sement 50 kg", birlik=Birlik.QOP, narx=Decimal("55000"), qoldiq=Decimal("100"),
        )
        self.qarz = Qarz.objects.create(qarzdor=self.qarzdor)

    def test_yangi_qarzdor_yaratilgach_qarz_sahifasiga_otadi(self):
        javob = self.client.post(reverse("qarz:yangi_qarzdor"), {
            "ism": "Olim", "familiya": "Karimov", "telefon": "+998901112233",
            "hudud": self.hudud.pk,
        })
        yangi = Qarzdor.objects.get(familiya="Karimov")
        self.assertRedirects(
            javob, reverse("qarz:qarz_boshlash", args=[yangi.pk]),
            target_status_code=302,
        )

    def test_qator_qoshilsa_ombordan_ayriladi(self):
        self.client.post(reverse("qarz:qator_qoshish", args=[self.qarz.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "10", "narx": "55000",
        })
        self.mahsulot.refresh_from_db()
        self.assertEqual(self.mahsulot.qoldiq, Decimal("90.000"))
        self.assertEqual(self.qarz.jami, Decimal("550000.00"))
        self.assertTrue(
            OmborHarakati.objects.filter(mahsulot=self.mahsulot, tur=HarakatTuri.CHIQIM).exists()
        )

    def test_omborda_yetmasa_qator_qoshilmaydi(self):
        javob = self.client.post(reverse("qarz:qator_qoshish", args=[self.qarz.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "500", "narx": "55000",
        }, follow=True)
        self.mahsulot.refresh_from_db()
        self.assertEqual(self.mahsulot.qoldiq, Decimal("100.000"))
        self.assertEqual(self.qarz.qatorlar.count(), 0)
        self.assertContains(javob, "Omborda yetarli emas")

    def test_manfiy_miqdor_qabul_qilinmaydi(self):
        self.client.post(reverse("qarz:qator_qoshish", args=[self.qarz.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "-5", "narx": "55000",
        })
        self.assertEqual(self.qarz.qatorlar.count(), 0)

    def test_qator_ochirilsa_tovar_omborga_qaytadi(self):
        self.client.post(reverse("qarz:qator_qoshish", args=[self.qarz.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "10", "narx": "55000",
        })
        qator = QarzQator.objects.get(qarz=self.qarz)
        self.client.post(reverse("qarz:qator_ochirish", args=[qator.pk]))
        self.mahsulot.refresh_from_db()
        self.assertEqual(self.mahsulot.qoldiq, Decimal("100.000"))
        self.assertEqual(self.qarz.qatorlar.count(), 0)

    def test_bosh_qarz_yakunlanganda_ochiriladi(self):
        self.client.post(reverse("qarz:qarz_yakunlash", args=[self.qarz.pk]))
        self.assertFalse(Qarz.objects.filter(pk=self.qarz.pk).exists())

    def test_balans_tolovni_hisobga_oladi(self):
        QarzQator.objects.create(
            qarz=self.qarz, mahsulot=self.mahsulot, miqdor=Decimal("10"), narx=Decimal("55000"),
        )
        Tolov.objects.create(qarzdor=self.qarzdor, summa=Decimal("200000"))
        self.assertEqual(self.qarzdor.balans, Decimal("350000.00"))

    def test_tugallanmagan_qarz_qayta_ochiladi(self):
        javob = self.client.get(reverse("qarz:qarz_boshlash", args=[self.qarzdor.pk]))
        self.assertRedirects(javob, reverse("qarz:qarz_tahrir", args=[self.qarz.pk]))
        self.assertEqual(self.qarzdor.qarzlar.count(), 1)

    def test_qidirish_telefon_boyicha_topadi(self):
        javob = self.client.get(reverse("qarz:qidirish"), {"q": "901234567"})
        self.assertContains(javob, "Aliyev")


class OmborTest(TestCase):
    def setUp(self):
        self.mahsulot = Mahsulot.objects.create(
            nom="G'isht", birlik=Birlik.DONA, narx=Decimal("1200"), qoldiq=Decimal("1000"),
        )

    def test_kirim_qoldiqni_oshiradi(self):
        self.client.post(reverse("ombor:kirim", args=[self.mahsulot.pk]),
                         {"miqdor": "500", "izoh": "Zavoddan"})
        self.mahsulot.refresh_from_db()
        self.assertEqual(self.mahsulot.qoldiq, Decimal("1500.000"))
        self.assertEqual(
            OmborHarakati.objects.filter(mahsulot=self.mahsulot, tur=HarakatTuri.KIRIM).count(), 1
        )

    def test_qoldiq_matni_ortiqcha_nollarsiz(self):
        self.assertEqual(self.mahsulot.qoldiq_son, "1000")
        self.assertEqual(self.mahsulot.narx_son, "1200")
