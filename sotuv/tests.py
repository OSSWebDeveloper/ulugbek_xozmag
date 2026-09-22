"""Naqd sotuv mantiqining sinovlari."""
from decimal import Decimal

from django.test import TestCase

from config.sinov import KirganTest
from django.urls import reverse

from ombor.models import Birlik, HarakatTuri, Mahsulot, OmborHarakati
from qarz.models import Hudud, Qarz, Qarzdor

from .models import Sotuv, SotuvQator


class SotuvTest(KirganTest):
    def setUp(self):
        super().setUp()
        self.mahsulot = Mahsulot.objects.create(
            nom="Sement 50 kg", birlik=Birlik.QOP, qoldiq=Decimal("100"),
        )
        self.sotuv = Sotuv.objects.create()

    def test_sotuv_qatori_ombordan_ayiradi(self):
        self.client.post(reverse("sotuv:qator_qoshish", args=[self.sotuv.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "3",
        })
        self.mahsulot.refresh_from_db()
        self.assertEqual(self.mahsulot.qoldiq, Decimal("97.000"))
        self.assertEqual(self.sotuv.qatorlar.count(), 1)
        harakat = OmborHarakati.objects.filter(tur=HarakatTuri.CHIQIM).first()
        self.assertIn(f"Sotuv #{self.sotuv.pk}", harakat.izoh)

    def test_omborda_yetmasa_qoshilmaydi(self):
        javob = self.client.post(reverse("sotuv:qator_qoshish", args=[self.sotuv.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "500",
        }, follow=True)
        self.mahsulot.refresh_from_db()
        self.assertEqual(self.mahsulot.qoldiq, Decimal("100.000"))
        self.assertEqual(self.sotuv.qatorlar.count(), 0)
        self.assertContains(javob, "Omborda yetarli emas")

    def test_qator_ochirilsa_tovar_qaytadi(self):
        self.client.post(reverse("sotuv:qator_qoshish", args=[self.sotuv.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "3",
        })
        qator = SotuvQator.objects.get(sotuv=self.sotuv)
        self.client.post(reverse("sotuv:qator_ochirish", args=[qator.pk]))
        self.mahsulot.refresh_from_db()
        self.assertEqual(self.mahsulot.qoldiq, Decimal("100.000"))

    def test_jami_qolda_yoziladi(self):
        """Savdolashilgan summa hisoblanmaydi — kassir o'zi yozadi."""
        SotuvQator.objects.create(
            sotuv=self.sotuv, mahsulot=self.mahsulot, miqdor=Decimal("2"),
        )
        self.client.post(reverse("sotuv:yakunlash", args=[self.sotuv.pk]), {"jami": "180000"})
        self.sotuv.refresh_from_db()
        self.assertTrue(self.sotuv.yakunlangan)
        self.assertEqual(self.sotuv.jami, Decimal("180000.00"))

    def test_dollarlik_sotuv_somga_qoshilmaydi(self):
        """Dollar summasi alohida maydonda qoladi, so'mga aralashmaydi."""
        SotuvQator.objects.create(
            sotuv=self.sotuv, mahsulot=self.mahsulot, miqdor=Decimal("2"),
        )
        self.client.post(reverse("sotuv:yakunlash", args=[self.sotuv.pk]),
                         {"jami": "", "jami_dollar": "40", "kurs": "12800"})
        self.sotuv.refresh_from_db()
        self.assertTrue(self.sotuv.yakunlangan)
        self.assertEqual(self.sotuv.jami, Decimal("0"))
        self.assertEqual(self.sotuv.jami_dollar, Decimal("40.00"))
        self.assertEqual(self.sotuv.kurs, Decimal("12800.00"))

    def test_dollar_yozilsa_kurs_soraladi(self):
        SotuvQator.objects.create(
            sotuv=self.sotuv, mahsulot=self.mahsulot, miqdor=Decimal("1"),
        )
        javob = self.client.post(reverse("sotuv:yakunlash", args=[self.sotuv.pk]),
                                 {"jami_dollar": "40", "kurs": ""}, follow=True)
        self.sotuv.refresh_from_db()
        self.assertFalse(self.sotuv.yakunlangan)
        self.assertContains(javob, "kursni ham yozing")

    def test_boshliq_bilan_yozilgan_son_qabul_qilinadi(self):
        """Maydonda son «250 000» ko'rinishida turadi — shunday ham o'qilishi kerak."""
        SotuvQator.objects.create(
            sotuv=self.sotuv, mahsulot=self.mahsulot, miqdor=Decimal("1"),
        )
        self.client.post(reverse("sotuv:yakunlash", args=[self.sotuv.pk]),
                         {"jami": "250 000", "jami_dollar": "40", "kurs": "12 800"})
        self.sotuv.refresh_from_db()
        self.assertEqual(self.sotuv.jami, Decimal("250000.00"))
        self.assertEqual(self.sotuv.kurs, Decimal("12800.00"))

    def test_jami_yozilmasa_sotuv_yakunlanmaydi(self):
        SotuvQator.objects.create(
            sotuv=self.sotuv, mahsulot=self.mahsulot, miqdor=Decimal("1"),
        )
        javob = self.client.post(reverse("sotuv:yakunlash", args=[self.sotuv.pk]),
                                 {"jami": ""}, follow=True)
        self.sotuv.refresh_from_db()
        self.assertFalse(self.sotuv.yakunlangan)
        self.assertContains(javob, "Jami summasini yozing")

    def test_bosh_sotuv_yakunlanganda_ochiriladi(self):
        self.client.post(reverse("sotuv:yakunlash", args=[self.sotuv.pk]))
        self.assertFalse(Sotuv.objects.filter(pk=self.sotuv.pk).exists())

    def test_bekor_qilinsa_tovarlar_omborga_qaytadi(self):
        """Chek o'chirilmaydi — bazada «bekor qilingan» bo'lib qoladi."""
        self.client.post(reverse("sotuv:qator_qoshish", args=[self.sotuv.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "5",
        })
        self.client.post(reverse("sotuv:bekor", args=[self.sotuv.pk]))
        self.mahsulot.refresh_from_db()
        self.sotuv.refresh_from_db()
        self.assertEqual(self.mahsulot.qoldiq, Decimal("100.000"))
        self.assertTrue(self.sotuv.bekor_qilingan)
        self.assertEqual(self.sotuv.qatorlar.count(), 1)

    def test_bosh_chek_bekor_qilinsa_ochiriladi(self):
        """Bironta tovar qo'shilmagan chek yozuvga arzimaydi."""
        self.client.post(reverse("sotuv:bekor", args=[self.sotuv.pk]))
        self.assertFalse(Sotuv.objects.filter(pk=self.sotuv.pk).exists())

    def test_bekor_qilingan_chek_tushumga_qoshilmaydi(self):
        self.client.post(reverse("sotuv:qator_qoshish", args=[self.sotuv.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "2",
        })
        self.client.post(reverse("sotuv:bekor", args=[self.sotuv.pk]))
        javob = self.client.get(reverse("sotuv:royxat"))
        self.assertContains(javob, "Bekor qilingan")
        self.assertEqual(javob.context["jami"], Decimal("0"))
        self.assertEqual(javob.context["soni"], 0)

    # ---------- Qaytarib berish ----------

    def test_qisman_qaytarish(self):
        """20 qopdan 5 tasi qaytsa: 5 qop omborga, 15 tasi mijozda qoladi."""
        qator = SotuvQator.objects.create(
            sotuv=self.sotuv, mahsulot=self.mahsulot, miqdor=Decimal("20"),
        )
        self.mahsulot.qoldiq = Decimal("80")
        self.mahsulot.save(update_fields=["qoldiq"])
        self.sotuv.jami = Decimal("1000000")
        self.sotuv.yakunlangan = True
        self.sotuv.save()

        self.client.post(reverse("sotuv:qaytarish", args=[qator.pk]),
                         {"miqdor": "5", "summa": "250000", "summa_dollar": ""})

        qator.refresh_from_db()
        self.mahsulot.refresh_from_db()
        self.sotuv.refresh_from_db()
        self.assertEqual(qator.qaytarilgan, Decimal("5.000"))
        self.assertEqual(qator.qolgan_miqdor, Decimal("15.000"))
        self.assertEqual(self.mahsulot.qoldiq, Decimal("85.000"))
        self.assertEqual(self.sotuv.sof_jami, Decimal("750000.00"))
        self.assertTrue(
            OmborHarakati.objects.filter(tur=HarakatTuri.QAYTARISH, miqdor=Decimal("5")).exists()
        )

    def test_sotilganidan_kop_qaytarib_bolmaydi(self):
        qator = SotuvQator.objects.create(
            sotuv=self.sotuv, mahsulot=self.mahsulot, miqdor=Decimal("20"),
        )
        javob = self.client.post(reverse("sotuv:qaytarish", args=[qator.pk]),
                                 {"miqdor": "25", "summa": ""}, follow=True)
        qator.refresh_from_db()
        self.assertEqual(qator.qaytarilgan, Decimal("0"))
        self.assertContains(javob, "Bunchasi sotilmagan")

    def test_ikki_marta_qaytarish_yigilib_boradi(self):
        qator = SotuvQator.objects.create(
            sotuv=self.sotuv, mahsulot=self.mahsulot, miqdor=Decimal("20"),
        )
        self.sotuv.jami = Decimal("1000000")
        self.sotuv.save(update_fields=["jami"])
        manzil = reverse("sotuv:qaytarish", args=[qator.pk])
        self.client.post(manzil, {"miqdor": "5", "summa": "250000"})
        self.client.post(manzil, {"miqdor": "3", "summa": "150000"})
        qator.refresh_from_db()
        self.sotuv.refresh_from_db()
        self.assertEqual(qator.qaytarilgan, Decimal("8.000"))
        self.assertEqual(self.sotuv.sof_jami, Decimal("600000.00"))

    def test_qaytarilgan_pul_chekdan_ortmaydi(self):
        qator = SotuvQator.objects.create(
            sotuv=self.sotuv, mahsulot=self.mahsulot, miqdor=Decimal("20"),
        )
        self.sotuv.jami = Decimal("100000")
        self.sotuv.save(update_fields=["jami"])
        javob = self.client.post(reverse("sotuv:qaytarish", args=[qator.pk]),
                                 {"miqdor": "5", "summa": "300000"}, follow=True)
        qator.refresh_from_db()
        self.assertEqual(qator.qaytarilgan, Decimal("0"))
        self.assertContains(javob, "chek summasidan ko&#x27;p bo&#x27;lmasin")

    def test_tugallanmagan_sotuv_qayta_ochiladi(self):
        javob = self.client.get(reverse("sotuv:boshlash"))
        self.assertRedirects(javob, reverse("sotuv:tahrir", args=[self.sotuv.pk]))
        self.assertEqual(Sotuv.objects.count(), 1)

    def test_kunlik_tushum_korsatiladi(self):
        SotuvQator.objects.create(
            sotuv=self.sotuv, mahsulot=self.mahsulot, miqdor=Decimal("2"),
        )
        self.client.post(reverse("sotuv:yakunlash", args=[self.sotuv.pk]), {"jami": "110000"})
        javob = self.client.get(reverse("sotuv:royxat"))
        self.assertContains(javob, "110 000")

    def test_sotuv_qarzdorga_tegmaydi(self):
        """Naqd sotuv hech kimning qarziga yozilmaydi."""
        from qarz.models import QarzQator

        self.client.post(reverse("sotuv:qator_qoshish", args=[self.sotuv.pk]), {
            "mahsulot": self.mahsulot.pk, "miqdor": "2",
        })
        self.assertEqual(QarzQator.objects.count(), 0)


class QismanQarzTest(KirganTest):
    """Naqd sotuvda pul yetmay qolsa bir qismi qarzga yoziladi.

    Tovarlar chekda qoladi, qarz hujjatida faqat pul bo'ladi — ombor ikki
    marta kamaymasligi kerak.
    """

    def setUp(self):
        super().setUp()
        self.hudud = Hudud.objects.create(nom="Hudud 1", tartib=1)
        self.qarzdor = Qarzdor.objects.create(ism="Vali", familiya="Aliyev",
                                              hudud=self.hudud)
        self.mahsulot = Mahsulot.objects.create(nom="Sement 50 kg", birlik=Birlik.QOP,
                                                qoldiq=Decimal("100"))
        self.sotuv = Sotuv.objects.create()
        SotuvQator.objects.create(sotuv=self.sotuv, mahsulot=self.mahsulot,
                                  miqdor=Decimal("10"))

    def yakunla(self, **qoshimcha):
        malumot = {"jami": "100000", "jami_dollar": "", "kurs": "12000"}
        malumot.update(qoshimcha)
        return self.client.post(reverse("sotuv:yakunlash", args=[self.sotuv.pk]),
                                malumot, follow=True)

    def test_qarz_hujjati_yaratiladi(self):
        self.yakunla(qarzdor=self.qarzdor.pk, qarz_jami="50000")
        qarz = Qarz.objects.get(sotuv=self.sotuv)
        self.assertEqual(qarz.qarzdor, self.qarzdor)
        self.assertEqual(qarz.jami, Decimal("50000"))
        self.assertTrue(qarz.yakunlangan)
        self.assertTrue(qarz.chekdanmi)
        self.assertIn(f"Chek #{self.sotuv.pk}", qarz.izoh)

    def test_tovarlar_qarz_hujjatiga_kochmaydi(self):
        """Tovar chekda turadi — aks holda ombordan ikki marta ayrilardi."""
        self.yakunla(qarzdor=self.qarzdor.pk, qarz_jami="50000")
        qarz = Qarz.objects.get(sotuv=self.sotuv)
        self.assertEqual(qarz.qatorlar_soni, 0)
        self.mahsulot.refresh_from_db()
        self.assertEqual(self.mahsulot.qoldiq, Decimal("100.000"))

    def test_chekka_faqat_naqd_pul_yoziladi(self):
        """Kunlik tushum kassadagi pulni ko'rsatishi kerak."""
        self.yakunla(qarzdor=self.qarzdor.pk, qarz_jami="50000")
        self.sotuv.refresh_from_db()
        self.assertEqual(self.sotuv.jami, Decimal("100000"))
        javob = self.client.get(reverse("sotuv:royxat"))
        self.assertEqual(javob.context["jami"], Decimal("100000"))

    def test_qarzdor_balansi_oshadi(self):
        self.yakunla(qarzdor=self.qarzdor.pk, qarz_jami="50000")
        self.assertEqual(self.qarzdor.balans, Decimal("50000"))

    def test_hammasi_qarzga_ketsa_jami_bosh_qolishi_mumkin(self):
        javob = self.yakunla(jami="", qarzdor=self.qarzdor.pk, qarz_jami="150000")
        self.sotuv.refresh_from_db()
        self.assertTrue(self.sotuv.yakunlangan)
        self.assertEqual(self.sotuv.jami, Decimal("0"))
        self.assertEqual(self.qarzdor.balans, Decimal("150000"))
        self.assertContains(javob, "daftariga yozildi")

    def test_qarzdorsiz_jami_baribir_majburiy(self):
        javob = self.yakunla(jami="", jami_dollar="")
        self.assertContains(javob, "summasini yozing")
        self.sotuv.refresh_from_db()
        self.assertFalse(self.sotuv.yakunlangan)

    def test_qarzdor_tanlanib_summa_yozilmasa_xato(self):
        javob = self.yakunla(qarzdor=self.qarzdor.pk, qarz_jami="", qarz_jami_dollar="")
        self.assertContains(javob, "Qarzga qancha qolishini yozing")
        self.assertEqual(Qarz.objects.count(), 0)

    def test_notanish_qarzdor_rad_etiladi(self):
        javob = self.yakunla(qarzdor="999999", qarz_jami="50000")
        self.assertContains(javob, "Qarzdor topilmadi")
        self.assertEqual(Qarz.objects.count(), 0)

    def test_dollar_qarzga_kurs_soraladi(self):
        javob = self.yakunla(kurs="", qarzdor=self.qarzdor.pk, qarz_jami_dollar="40")
        self.assertContains(javob, "kursni ham yozing")
        self.assertEqual(Qarz.objects.count(), 0)

    def test_dollar_qarz_som_hisobiga_aralashmaydi(self):
        self.yakunla(qarzdor=self.qarzdor.pk, qarz_jami="50000", qarz_jami_dollar="40")
        self.assertEqual(self.qarzdor.balans, Decimal("50000"))
        self.assertEqual(self.qarzdor.balans_dollar, Decimal("40"))

    def test_qarzdorsiz_oddiy_sotuv_ozgarmagan(self):
        javob = self.yakunla()
        self.sotuv.refresh_from_db()
        self.assertTrue(self.sotuv.yakunlangan)
        self.assertEqual(Qarz.objects.count(), 0)
        self.assertContains(javob, "Sotuv yakunlandi")

    def test_manfiy_qarz_summasi_rad_etiladi(self):
        javob = self.yakunla(qarzdor=self.qarzdor.pk, qarz_jami="-5000")
        self.assertContains(javob, "manfiy")
        self.assertEqual(Qarz.objects.count(), 0)

    def test_chek_royxatida_qarz_korinadi(self):
        self.yakunla(qarzdor=self.qarzdor.pk, qarz_jami="50000")
        javob = self.client.get(reverse("sotuv:royxat"))
        self.assertContains(javob, "Qarzga: Aliyev Vali")
