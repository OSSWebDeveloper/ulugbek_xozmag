"""Qarz va ombor mantiqining asosiy sinovlari."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from config.sinov import KirganTest
from django.urls import reverse

from ombor.models import Birlik, HarakatTuri, Mahsulot, OmborHarakati

from .models import Hudud, Qarz, QarzQator, Qarzdor, Tolov


class QarzOqimiTest(KirganTest):
    def setUp(self):
        super().setUp()
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

    def test_qidirish_royxatda_qarzdor_korinadi(self):
        javob = self.client.get(reverse("qarz:qidirish"), {"korinish": "royxat"})
        self.assertContains(javob, "Aliyev")


class OmborTest(KirganTest):
    def setUp(self):
        super().setUp()
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


class TolovChegarasiTest(KirganTest):
    """Qarzdan ortiq to'lov balansni manfiyga olib ketmasligi kerak."""

    def setUp(self):
        super().setUp()
        self.hudud = Hudud.objects.create(nom="Hudud 1", tartib=1)
        self.qarzdor = Qarzdor.objects.create(ism="Vali", familiya="Aliyev", hudud=self.hudud)
        self.mahsulot = Mahsulot.objects.create(
            nom="Sement 50 kg", birlik=Birlik.QOP, narx=Decimal("55000"), qoldiq=Decimal("100"),
        )
        qarz = Qarz.objects.create(qarzdor=self.qarzdor, yakunlangan=True)
        QarzQator.objects.create(qarz=qarz, mahsulot=self.mahsulot, miqdor=Decimal("2"),
                                 narx=Decimal("55000"))
        self.manzil = reverse("qarz:tolov_qoshish", args=[self.qarzdor.pk])

    def test_qarzdan_ortiq_tolov_qabul_qilinmaydi(self):
        javob = self.client.post(self.manzil, {"summa": "200000", "izoh": ""}, follow=True)
        self.assertEqual(Tolov.objects.count(), 0)
        self.assertEqual(self.qarzdor.balans, Decimal("110000.00"))
        self.assertContains(javob, "Bundan ortiq to&#x27;lov yozib bo&#x27;lmaydi")

    def test_qarzi_yoq_mijozdan_tolov_olinmaydi(self):
        bosh = Qarzdor.objects.create(ism="Olim", familiya="Karimov", hudud=self.hudud)
        javob = self.client.post(reverse("qarz:tolov_qoshish", args=[bosh.pk]),
                                 {"summa": "5000", "izoh": ""}, follow=True)
        self.assertEqual(Tolov.objects.filter(qarzdor=bosh).count(), 0)
        self.assertContains(javob, "qarzi yo&#x27;q")

    def test_nol_tolov_qabul_qilinmaydi(self):
        self.client.post(self.manzil, {"summa": "0", "izoh": ""})
        self.assertEqual(Tolov.objects.count(), 0)

    def test_qarzga_teng_tolov_qarzni_yopadi(self):
        javob = self.client.post(self.manzil, {"summa": "110000", "izoh": ""}, follow=True)
        self.assertEqual(Tolov.objects.count(), 1)
        self.assertEqual(self.qarzdor.balans, Decimal("0.00"))
        self.assertContains(javob, "Qarz to&#x27;liq yopildi")

    def test_qisman_tolov_qoldiqni_korsatadi(self):
        javob = self.client.post(self.manzil, {"summa": "10000", "izoh": ""}, follow=True)
        self.assertEqual(self.qarzdor.balans, Decimal("100000.00"))
        self.assertContains(javob, "Qolgan qarzi 100 000 so&#x27;m")


class QarzdorlarKorinishiTest(KirganTest):
    """Qarzdorlar bo'limi: tanlov -> hududlar -> ro'yxat."""

    def setUp(self):
        super().setUp()
        self.h1 = Hudud.objects.create(nom="Hudud 1", tartib=1)
        self.h2 = Hudud.objects.create(nom="Hudud 2", tartib=2)
        Qarzdor.objects.create(ism="Vali", familiya="Aliyev", hudud=self.h1)
        Qarzdor.objects.create(ism="Olim", familiya="Karimov", hudud=self.h1)

    def test_boshida_ikkita_tugma(self):
        javob = self.client.get(reverse("qarz:qarzdorlar"))
        self.assertContains(javob, "Qarzdorlar ro'yxati")
        self.assertContains(javob, "Hududlar")
        self.assertNotContains(javob, "Familiya Ism")   # jadval hali yo'q

    def test_hududlar_tugmalari_sonini_korsatadi(self):
        javob = self.client.get(reverse("qarz:qarzdorlar"), {"korinish": "hududlar"})
        self.assertContains(javob, "2 ta qarzdor")      # Hudud 1
        self.assertContains(javob, "qarzdor yo'q")  # Hudud 2
        self.assertEqual(javob.content.decode().count("hudud-tugma"), 2)

    def test_hudud_tanlansa_faqat_oshaning_qarzdorlari(self):
        javob = self.client.get(reverse("qarz:qarzdorlar"), {"hudud": self.h1.pk})
        self.assertContains(javob, "Aliyev Vali")
        self.assertContains(javob, "Karimov Olim")
        javob2 = self.client.get(reverse("qarz:qarzdorlar"), {"hudud": self.h2.pk})
        self.assertNotContains(javob2, "Aliyev Vali")
        self.assertContains(javob2, "Bu hududda qarzdor yo'q")

    def test_toliq_royxat(self):
        javob = self.client.get(reverse("qarz:qarzdorlar"), {"korinish": "royxat"})
        self.assertContains(javob, "Aliyev Vali")
        self.assertContains(javob, "Karimov Olim")

    def test_qidirish_ham_shu_ketma_ketlikda(self):
        javob = self.client.get(reverse("qarz:qidirish"))
        self.assertContains(javob, "Barcha qarzdorlar")
        self.assertContains(javob, "Hududlar")

        javob = self.client.get(reverse("qarz:qidirish"), {"korinish": "hududlar"})
        self.assertEqual(javob.content.decode().count("hudud-tugma"), 2)

        javob = self.client.get(reverse("qarz:qidirish"), {"hudud": self.h1.pk})
        self.assertContains(javob, "Aliyev Vali")

    def test_qidirishda_matn_maydoni_yoq(self):
        """Ism yozib qidirish olib tashlandi — faqat ro'yxat va hududlar."""
        javob = self.client.get(reverse("qarz:qidirish"))
        self.assertNotContains(javob, 'name="q"')
        javob = self.client.get(reverse("qarz:qidirish"), {"korinish": "royxat"})
        self.assertContains(javob, "Aliyev Vali")
        self.assertContains(javob, "Karimov Olim")

class KirishTest(TestCase):
    """Saytga faqat login bilan kiriladi."""

    def setUp(self):
        super().setUp()
        self.parol = "sinov-parol"
        get_user_model().objects.create_user(username="reception", password=self.parol)

    def test_kirmasdan_sahifa_ochilmaydi(self):
        javob = self.client.get(reverse("qarz:boshlash"))
        self.assertEqual(javob.status_code, 302)
        self.assertIn(reverse("kirish"), javob["Location"])

    def test_kirish_sahifasi_ochiq(self):
        javob = self.client.get(reverse("kirish"))
        self.assertEqual(javob.status_code, 200)
        self.assertContains(javob, "Parol")

    def test_notogri_parol_kiritmaydi(self):
        javob = self.client.post(reverse("kirish"),
                                 {"username": "reception", "password": "xato"})
        self.assertEqual(javob.status_code, 200)
        self.assertContains(javob, "Login yoki parol xato")

    def test_togri_parol_bilan_kiradi(self):
        javob = self.client.post(reverse("kirish"),
                                 {"username": "reception", "password": self.parol})
        self.assertRedirects(javob, "/")
        self.assertEqual(self.client.get(reverse("ombor:royxat")).status_code, 200)

    def test_chiqqandan_keyin_yana_sorolinadi(self):
        self.client.login(username="reception", password=self.parol)
        self.client.post(reverse("chiqish"))
        javob = self.client.get(reverse("ombor:royxat"))
        self.assertEqual(javob.status_code, 302)

    def test_xodim_buyrugi_hisob_yaratadi(self):
        from django.core.management import call_command
        from io import StringIO

        call_command("xodim", "boshliq", "--parol", "maxfiy", stdout=StringIO())
        self.assertTrue(self.client.login(username="boshliq", password="maxfiy"))

    def test_xodim_buyrugi_parolsiz_loginni_beradi(self):
        from django.core.management import call_command
        from io import StringIO

        call_command("xodim", "ishchi", stdout=StringIO())
        self.assertTrue(self.client.login(username="ishchi", password="ishchi"))

