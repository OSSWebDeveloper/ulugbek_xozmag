"""Ombor sinovlari — asosan bir birlikda olinib boshqasida sotiladigan tovarlar."""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Birlik, HarakatTuri, Mahsulot, OmborHarakati


class IkkiBirlikModelTest(TestCase):
    """Rulonda olinib metrda sotiladigan tovarning hisoblari."""

    def setUp(self):
        self.lenta = Mahsulot.objects.create(
            nom="Polietilen lenta 10 sm", birlik=Birlik.METR,
            olish_birligi=Birlik.RULON, olish_miqdori=Decimal("100"),
            narx=Decimal("3500"), qoldiq=Decimal("300"),
        )
        self.gisht = Mahsulot.objects.create(
            nom="G'isht", birlik=Birlik.DONA, narx=Decimal("1200"), qoldiq=Decimal("5000"),
        )

    def test_ikki_birlikli_tovar_aniqlanadi(self):
        self.assertTrue(self.lenta.ikki_birlikmi)
        self.assertFalse(self.gisht.ikki_birlikmi)

    def test_qoldiq_olish_birligida_ham_korinadi(self):
        self.assertEqual(self.lenta.olish_qoldigi, Decimal("3.000"))
        self.assertEqual(self.lenta.qoldiq_toliq, "300 metr (3 rulon)")
        self.assertEqual(self.gisht.qoldiq_toliq, "5000 dona")

    def test_birlik_qoidasi_va_olish_narxi(self):
        self.assertEqual(self.lenta.birlik_qoidasi, "1 rulon = 100 metr")
        self.assertEqual(self.lenta.olish_narxi, Decimal("350000.00"))
        self.assertEqual(self.gisht.birlik_qoidasi, "")

    def test_olish_birligidan_sotuv_birligiga_otkaziladi(self):
        self.assertEqual(self.lenta.sotuvga_aylantir("2", Birlik.RULON), Decimal("200.000"))
        self.assertEqual(self.lenta.sotuvga_aylantir("2.5", Birlik.RULON), Decimal("250.000"))
        # Sotuv birligida kiritilsa o'zgarmaydi
        self.assertEqual(self.lenta.sotuvga_aylantir("40", Birlik.METR), Decimal("40"))
        # Oddiy tovarda hech qanday ko'paytirish yo'q
        self.assertEqual(self.gisht.sotuvga_aylantir("10", Birlik.DONA), Decimal("10"))

    def test_olish_birligi_sotuv_birligi_bilan_bir_xil_bolsa_tozalanadi(self):
        tovar = Mahsulot.objects.create(
            nom="Rozetka", birlik=Birlik.DONA, olish_birligi=Birlik.DONA,
            olish_miqdori=Decimal("5"), narx=Decimal("12000"),
        )
        tovar.refresh_from_db()
        self.assertEqual(tovar.olish_birligi, "")
        self.assertEqual(tovar.olish_miqdori, Decimal("1.000"))
        self.assertFalse(tovar.ikki_birlikmi)


class KirimTest(TestCase):
    """Kirim ekrani: miqdor rulonda ham, metrda ham kiritilishi mumkin."""

    def setUp(self):
        self.lenta = Mahsulot.objects.create(
            nom="Polietilen lenta 10 sm", birlik=Birlik.METR,
            olish_birligi=Birlik.RULON, olish_miqdori=Decimal("100"),
            narx=Decimal("3500"), qoldiq=Decimal("300"),
        )
        self.gisht = Mahsulot.objects.create(
            nom="G'isht", birlik=Birlik.DONA, narx=Decimal("1200"), qoldiq=Decimal("5000"),
        )

    def test_rulonda_kirim_qilinsa_metr_bolib_tushadi(self):
        self.client.post(reverse("ombor:kirim", args=[self.lenta.pk]), {
            "miqdor": "2", "birlik": Birlik.RULON, "izoh": "Bozordan",
        })
        self.lenta.refresh_from_db()
        self.assertEqual(self.lenta.qoldiq, Decimal("500.000"))
        self.assertEqual(self.lenta.olish_qoldigi, Decimal("5.000"))

    def test_kasrli_rulon_ham_hisoblanadi(self):
        self.client.post(reverse("ombor:kirim", args=[self.lenta.pk]), {
            "miqdor": "2,5", "birlik": Birlik.RULON, "izoh": "",
        })
        self.lenta.refresh_from_db()
        self.assertEqual(self.lenta.qoldiq, Decimal("550.000"))

    def test_metrda_kirim_qilinsa_ozgarmaydi(self):
        self.client.post(reverse("ombor:kirim", args=[self.lenta.pk]), {
            "miqdor": "40", "birlik": Birlik.METR, "izoh": "Qoldiq rulon",
        })
        self.lenta.refresh_from_db()
        self.assertEqual(self.lenta.qoldiq, Decimal("340.000"))

    def test_tarixda_ikkala_birlik_saqlanadi(self):
        self.client.post(reverse("ombor:kirim", args=[self.lenta.pk]), {
            "miqdor": "2", "birlik": Birlik.RULON, "izoh": "",
        })
        harakat = OmborHarakati.objects.get(mahsulot=self.lenta, tur=HarakatTuri.KIRIM)
        self.assertEqual(harakat.miqdor, Decimal("200.000"))
        self.assertEqual(harakat.kiritilgan_miqdor, Decimal("2.000"))
        self.assertEqual(harakat.kiritilgan_birlik, Birlik.RULON)
        self.assertEqual(harakat.korinish, "2 rulon = 200 metr")

    def test_oddiy_tovarda_birlik_tanlovi_sorolmaydi(self):
        javob = self.client.get(reverse("ombor:kirim", args=[self.gisht.pk]))
        self.assertNotContains(javob, 'name="birlik"')

        self.client.post(reverse("ombor:kirim", args=[self.gisht.pk]), {
            "miqdor": "100", "izoh": "",
        })
        self.gisht.refresh_from_db()
        self.assertEqual(self.gisht.qoldiq, Decimal("5100.000"))
        harakat = OmborHarakati.objects.get(mahsulot=self.gisht, tur=HarakatTuri.KIRIM)
        self.assertEqual(harakat.korinish, "100 dona")

    def test_ikki_birlikli_tovarda_birlik_tanlovi_korinadi(self):
        javob = self.client.get(reverse("ombor:kirim", args=[self.lenta.pk]))
        self.assertContains(javob, 'name="birlik"')
        self.assertContains(javob, "1 rulon = 100 metr")


class MahsulotFormaTest(TestCase):
    """Tovar kartochkasidagi olish birligi maydonlari."""

    def test_olish_birligi_tanlansa_miqdor_talab_qilinadi(self):
        javob = self.client.post(reverse("ombor:mahsulot_yangi"), {
            "nom": "Polietilen lenta", "birlik": Birlik.METR, "narx": "3500",
            "qoldiq": "0", "olish_birligi": Birlik.RULON, "olish_miqdori": "0",
            "faol": "on",
        })
        self.assertEqual(javob.status_code, 200)
        self.assertFalse(Mahsulot.objects.filter(nom="Polietilen lenta").exists())
        self.assertContains(javob, "nechta metr borligini yozing")

    def test_toliq_toldirilsa_saqlanadi(self):
        self.client.post(reverse("ombor:mahsulot_yangi"), {
            "nom": "Polietilen lenta", "birlik": Birlik.METR, "narx": "3500",
            "qoldiq": "300", "olish_birligi": Birlik.RULON, "olish_miqdori": "100",
            "faol": "on",
        })
        tovar = Mahsulot.objects.get(nom="Polietilen lenta")
        self.assertTrue(tovar.ikki_birlikmi)
        self.assertEqual(tovar.olish_qoldigi, Decimal("3.000"))

    def test_olish_birligi_tanlanmasa_miqdor_birga_qaytadi(self):
        self.client.post(reverse("ombor:mahsulot_yangi"), {
            "nom": "Rozetka", "birlik": Birlik.DONA, "narx": "12000",
            "qoldiq": "150", "olish_birligi": "", "olish_miqdori": "25",
            "faol": "on",
        })
        tovar = Mahsulot.objects.get(nom="Rozetka")
        self.assertFalse(tovar.ikki_birlikmi)
        self.assertEqual(tovar.olish_miqdori, Decimal("1.000"))


class SotuvBirligiTest(TestCase):
    """Sotuv va qarz tomonida hech nima o'zgarmaydi — hammasi sotuv birligida."""

    def setUp(self):
        self.lenta = Mahsulot.objects.create(
            nom="Polietilen lenta 10 sm", birlik=Birlik.METR,
            olish_birligi=Birlik.RULON, olish_miqdori=Decimal("100"),
            narx=Decimal("3500"), qoldiq=Decimal("300"),
        )

    def test_sotuvdan_keyin_ikkala_korsatkich_tori_qoladi(self):
        from ombor.xizmat import ayir

        ayir(self.lenta.pk, Decimal("150"), "Sinov")
        self.lenta.refresh_from_db()
        self.assertEqual(self.lenta.qoldiq, Decimal("150.000"))
        self.assertEqual(self.lenta.olish_qoldigi, Decimal("1.500"))
        self.assertEqual(self.lenta.qoldiq_toliq, "150 metr (1.5 rulon)")
