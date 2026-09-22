"""Qarz va ombor mantiqining asosiy sinovlari."""
import json
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
            nom="Sement 50 kg", birlik=Birlik.QOP, qoldiq=Decimal("100"),
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
            "mahsulot": self.mahsulot.pk, "miqdor": "10",
        })
        self.mahsulot.refresh_from_db()
        self.assertEqual(self.mahsulot.qoldiq, Decimal("90.000"))
        self.assertEqual(self.qarz.qatorlar.count(), 1)
        self.assertTrue(
            OmborHarakati.objects.filter(mahsulot=self.mahsulot, tur=HarakatTuri.CHIQIM).exists()
        )

    def test_omborda_yetmasa_qator_qoshilmaydi(self):
        javob = self.client.post(reverse("qarz:qator_qoshish", args=[self.qarz.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "500",
        }, follow=True)
        self.mahsulot.refresh_from_db()
        self.assertEqual(self.mahsulot.qoldiq, Decimal("100.000"))
        self.assertEqual(self.qarz.qatorlar.count(), 0)
        self.assertContains(javob, "Omborda yetarli emas")

    def test_manfiy_miqdor_qabul_qilinmaydi(self):
        self.client.post(reverse("qarz:qator_qoshish", args=[self.qarz.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "-5",
        })
        self.assertEqual(self.qarz.qatorlar.count(), 0)

    def test_qator_ochirilsa_tovar_omborga_qaytadi(self):
        self.client.post(reverse("qarz:qator_qoshish", args=[self.qarz.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "10",
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
        self.qarz.jami = Decimal("550000")
        self.qarz.save(update_fields=["jami"])
        Tolov.objects.create(qarzdor=self.qarzdor, summa=Decimal("200000"))
        self.assertEqual(self.qarzdor.balans, Decimal("350000.00"))

    def test_qarz_summasi_qolda_yoziladi(self):
        """Savdolashilgan summa hisoblanmaydi — sotuvchi o'zi yozadi."""
        self.client.post(reverse("qarz:qator_qoshish", args=[self.qarz.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "10",
        })
        self.client.post(reverse("qarz:qarz_yakunlash", args=[self.qarz.pk]), {"jami": "540000"})
        self.qarz.refresh_from_db()
        self.assertTrue(self.qarz.yakunlangan)
        self.assertEqual(self.qarz.jami, Decimal("540000.00"))
        self.assertEqual(self.qarzdor.balans, Decimal("540000.00"))

    def test_dollar_qarzi_alohida_yuradi(self):
        """So'm qarzi va dollar qarzi qo'shilmaydi, har biri o'z hisobida."""
        self.qarz.jami = Decimal("500000")
        self.qarz.jami_dollar = Decimal("50")
        self.qarz.kurs = Decimal("12800")
        self.qarz.save()
        self.assertEqual(self.qarzdor.balans, Decimal("500000"))
        self.assertEqual(self.qarzdor.balans_dollar, Decimal("50"))

        # So'm to'lovi faqat so'm qarzini kamaytiradi
        self.client.post(reverse("qarz:tolov_qoshish", args=[self.qarzdor.pk]),
                         {"summa": "200000", "valyuta": "som", "izoh": ""})
        self.assertEqual(self.qarzdor.balans, Decimal("300000"))
        self.assertEqual(self.qarzdor.balans_dollar, Decimal("50"))

        # Dollar to'lovi faqat dollar qarzini kamaytiradi
        self.client.post(reverse("qarz:tolov_qoshish", args=[self.qarzdor.pk]),
                         {"summa": "20", "valyuta": "dollar", "izoh": ""})
        self.assertEqual(self.qarzdor.balans, Decimal("300000"))
        self.assertEqual(self.qarzdor.balans_dollar, Decimal("30"))

    def test_dollar_qarzidan_ortiq_dollar_tolov_qabul_qilinmaydi(self):
        self.qarz.jami_dollar = Decimal("50")
        self.qarz.kurs = Decimal("12800")
        self.qarz.save()
        javob = self.client.post(reverse("qarz:tolov_qoshish", args=[self.qarzdor.pk]),
                                 {"summa": "80", "valyuta": "dollar", "izoh": ""}, follow=True)
        self.assertEqual(Tolov.objects.count(), 0)
        self.assertContains(javob, "Qolgan dollar qarzi")

    def test_som_qarzi_yoq_bolsa_som_tolov_olinmaydi(self):
        """Dollar qarzi bor, so'm qarzi yo'q — so'm to'lov yozilmaydi."""
        self.qarz.jami_dollar = Decimal("50")
        self.qarz.kurs = Decimal("12800")
        self.qarz.save()
        javob = self.client.post(reverse("qarz:tolov_qoshish", args=[self.qarzdor.pk]),
                                 {"summa": "10000", "valyuta": "som", "izoh": ""}, follow=True)
        self.assertEqual(Tolov.objects.count(), 0)
        self.assertContains(javob, "so&#x27;m qarzi yo&#x27;q")

    def test_qarzda_dollar_summasi_qolda_yoziladi(self):
        self.client.post(reverse("qarz:qator_qoshish", args=[self.qarz.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "10",
        })
        self.client.post(reverse("qarz:qarz_yakunlash", args=[self.qarz.pk]),
                         {"jami": "300000", "jami_dollar": "25", "kurs": "12800"})
        self.qarz.refresh_from_db()
        self.assertTrue(self.qarz.yakunlangan)
        self.assertEqual(self.qarz.jami, Decimal("300000.00"))
        self.assertEqual(self.qarz.jami_dollar, Decimal("25.00"))
        self.assertEqual(self.qarzdor.balans, Decimal("300000.00"))
        self.assertEqual(self.qarzdor.balans_dollar, Decimal("25.00"))

    def test_qaytarish_qarzni_kamaytiradi(self):
        """Olingan tovar qaytsa, mijoz o'sha pul uchun qarzdor bo'lib qolmaydi."""
        qator = QarzQator.objects.create(
            qarz=self.qarz, mahsulot=self.mahsulot, miqdor=Decimal("20"),
        )
        self.mahsulot.qoldiq = Decimal("80")
        self.mahsulot.save(update_fields=["qoldiq"])
        self.qarz.jami = Decimal("1000000")
        self.qarz.yakunlangan = True
        self.qarz.save()

        self.client.post(reverse("qarz:qator_qaytarish", args=[qator.pk]),
                         {"miqdor": "5", "summa": "250000", "summa_dollar": ""})

        qator.refresh_from_db()
        self.mahsulot.refresh_from_db()
        self.qarz.refresh_from_db()
        self.assertEqual(qator.qaytarilgan, Decimal("5.000"))
        self.assertEqual(self.mahsulot.qoldiq, Decimal("85.000"))
        self.assertEqual(self.qarz.sof_jami, Decimal("750000.00"))
        self.assertEqual(self.qarzdor.balans, Decimal("750000.00"))

    def test_dollarlik_qarz_qaytarilishi_faqat_dollarga_tegadi(self):
        qator = QarzQator.objects.create(
            qarz=self.qarz, mahsulot=self.mahsulot, miqdor=Decimal("10"),
        )
        self.qarz.jami = Decimal("500000")
        self.qarz.jami_dollar = Decimal("50")
        self.qarz.kurs = Decimal("12800")
        self.qarz.yakunlangan = True
        self.qarz.save()

        self.client.post(reverse("qarz:qator_qaytarish", args=[qator.pk]),
                         {"miqdor": "4", "summa": "", "summa_dollar": "20"})

        self.assertEqual(self.qarzdor.balans, Decimal("500000.00"))
        self.assertEqual(self.qarzdor.balans_dollar, Decimal("30.00"))

    def test_summasiz_qarz_yakunlanmaydi(self):
        self.client.post(reverse("qarz:qator_qoshish", args=[self.qarz.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "10",
        })
        javob = self.client.post(reverse("qarz:qarz_yakunlash", args=[self.qarz.pk]),
                                 {"jami": ""}, follow=True)
        self.qarz.refresh_from_db()
        self.assertFalse(self.qarz.yakunlangan)
        self.assertContains(javob, "Qarz summasini yozing")

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
            nom="G'isht", birlik=Birlik.DONA, qoldiq=Decimal("1000"),
        )

    def test_kirim_qoldiqni_oshiradi(self):
        self.client.post(reverse("ombor:kirim", args=[self.mahsulot.pk]),
                         {"miqdor": "500", "izoh": "Zavoddan"})
        self.mahsulot.refresh_from_db()
        self.assertEqual(self.mahsulot.qoldiq, Decimal("1500.000"))
        self.assertEqual(
            OmborHarakati.objects.filter(mahsulot=self.mahsulot, tur=HarakatTuri.KIRIM).count(), 1
        )

    def test_tovar_valyutasi_somdan_boshlanadi(self):
        """Tovar qo'shilganda standarti so'm, dollarga qo'lda o'tkaziladi."""
        self.assertFalse(self.mahsulot.dollarmi)
        self.assertEqual(self.mahsulot.valyuta_belgisi, "so'm")

        dollarli = Mahsulot.objects.create(
            nom="Plastik truba", birlik=Birlik.METR, qoldiq=Decimal("50"), valyuta="dollar",
        )
        self.assertTrue(dollarli.dollarmi)
        self.assertEqual(dollarli.valyuta_belgisi, "$")

    def test_qoldiq_matni_ortiqcha_nollarsiz(self):
        self.assertEqual(self.mahsulot.qoldiq_son, "1000")


class TolovChegarasiTest(KirganTest):
    """Qarzdan ortiq to'lov balansni manfiyga olib ketmasligi kerak."""

    def setUp(self):
        super().setUp()
        self.hudud = Hudud.objects.create(nom="Hudud 1", tartib=1)
        self.qarzdor = Qarzdor.objects.create(ism="Vali", familiya="Aliyev", hudud=self.hudud)
        self.mahsulot = Mahsulot.objects.create(
            nom="Sement 50 kg", birlik=Birlik.QOP, qoldiq=Decimal("100"),
        )
        qarz = Qarz.objects.create(qarzdor=self.qarzdor, yakunlangan=True,
                                  jami=Decimal("110000"))
        QarzQator.objects.create(qarz=qarz, mahsulot=self.mahsulot, miqdor=Decimal("2"))
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
        self.assertContains(javob, "So&#x27;m qarzi to&#x27;liq yopildi")

    def test_qisman_tolov_qoldiqni_korsatadi(self):
        javob = self.client.post(self.manzil, {"summa": "10000", "izoh": ""}, follow=True)
        self.assertEqual(self.qarzdor.balans, Decimal("100000.00"))
        self.assertContains(javob, "Qolgan so&#x27;m qarzi 100 000")


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



class OldindanTolovTest(KirganTest):
    """Qarz yozilayotganda mijoz bir qismini darrov to'laydi."""

    def setUp(self):
        super().setUp()
        self.hudud = Hudud.objects.create(nom="Hudud 1", tartib=1)
        self.qarzdor = Qarzdor.objects.create(ism="Vali", familiya="Aliyev",
                                              hudud=self.hudud)
        self.mahsulot = Mahsulot.objects.create(nom="Sement 50 kg", birlik=Birlik.QOP,
                                                qoldiq=Decimal("100"))
        self.qarz = Qarz.objects.create(qarzdor=self.qarzdor)
        QarzQator.objects.create(qarz=self.qarz, mahsulot=self.mahsulot,
                                 miqdor=Decimal("10"))

    def yakunla(self, **qoshimcha):
        malumot = {"jami": "500000", "jami_dollar": "", "kurs": "12000",
                   "oldindan": "", "oldindan_dollar": ""}
        malumot.update(qoshimcha)
        return self.client.post(reverse("qarz:qarz_yakunlash", args=[self.qarz.pk]),
                                malumot, follow=True)

    def test_oldindan_tolov_balansdan_ayriladi(self):
        self.yakunla(oldindan="200000")
        self.assertEqual(self.qarzdor.balans, Decimal("300000"))

    def test_oldindan_tolov_hujjatga_boglanadi(self):
        self.yakunla(oldindan="200000")
        tolov = Tolov.objects.get(qarzdor=self.qarzdor)
        self.assertEqual(tolov.qarz, self.qarz)
        self.assertEqual(self.qarz.oldindan, Decimal("200000"))
        self.assertTrue(self.qarz.oldindan_tolanganmi)

    def test_standart_holatda_tolov_yozilmaydi(self):
        """Maydon 0 turadi — hech kim to'lamagan bo'lsa yozuv ham chiqmasin."""
        self.yakunla()
        self.assertEqual(Tolov.objects.count(), 0)
        self.assertFalse(self.qarz.oldindan_tolanganmi)
        self.assertEqual(self.qarzdor.balans, Decimal("500000"))

    def test_qarzdan_ortiq_tolov_qabul_qilinmaydi(self):
        """Aks holda balans manfiyga ketib «qarzi −100 000» chiqardi."""
        javob = self.yakunla(oldindan="600000")
        self.assertContains(javob, "qarz summasidan ko&#x27;p")
        self.assertEqual(Tolov.objects.count(), 0)
        self.qarz.refresh_from_db()
        self.assertFalse(self.qarz.yakunlangan)

    def test_toliq_tolansa_qarz_yopiladi(self):
        self.yakunla(oldindan="500000")
        self.assertEqual(self.qarzdor.balans, Decimal("0"))
        self.assertFalse(self.qarzdor.qarzi_bormi)

    def test_dollar_oldindan_somga_aralashmaydi(self):
        self.yakunla(jami="500000", jami_dollar="100", oldindan_dollar="40")
        self.assertEqual(self.qarzdor.balans, Decimal("500000"))
        self.assertEqual(self.qarzdor.balans_dollar, Decimal("60"))

    def test_dollar_oldindan_ham_chegaralanadi(self):
        javob = self.yakunla(jami="500000", jami_dollar="100", oldindan_dollar="150")
        self.assertContains(javob, "dollarlik summadan ko&#x27;p")
        self.assertEqual(Tolov.objects.count(), 0)

    def test_kartochkada_oldindan_tolov_korinadi(self):
        self.yakunla(oldindan="200000")
        javob = self.client.get(reverse("qarz:qarzdor_karta", args=[self.qarzdor.pk]))
        self.assertContains(javob, "Oldindan to'langan")
        self.assertContains(javob, "200 000")

    def test_manfiy_tolov_qabul_qilinmaydi(self):
        javob = self.yakunla(oldindan="-100")
        self.assertContains(javob, "manfiy")
        self.assertEqual(Tolov.objects.count(), 0)


class QarzdorOynachaTest(KirganTest):
    """Naqd sotuv oynachasidan yangi qarzdor qo'shish (sahifa almashmaydi)."""

    def setUp(self):
        super().setUp()
        self.hudud = Hudud.objects.create(nom="Hudud 1", tartib=1)

    def test_yangi_qarzdor_yaratiladi(self):
        javob = self.client.post(reverse("qarz:qarzdor_json"), {
            "ism": "Olim", "familiya": "Karimov", "telefon": "+998901112233",
            "hudud": self.hudud.pk,
        })
        malumot = json.loads(javob.content)
        self.assertTrue(malumot["ok"])
        self.assertEqual(malumot["nom"], "Karimov Olim")
        self.assertEqual(malumot["hudud"], "Hudud 1")
        self.assertTrue(Qarzdor.objects.filter(pk=malumot["id"]).exists())

    def test_notogri_malumot_maydon_bilan_qaytadi(self):
        javob = self.client.post(reverse("qarz:qarzdor_json"), {
            "ism": "", "familiya": "Karimov", "hudud": self.hudud.pk,
        })
        malumot = json.loads(javob.content)
        self.assertFalse(malumot["ok"])
        self.assertIn("ism", malumot["xatolar"])
        self.assertEqual(Qarzdor.objects.count(), 0)

    def test_get_bilan_ochilmaydi(self):
        javob = self.client.get(reverse("qarz:qarzdor_json"))
        self.assertEqual(javob.status_code, 405)
