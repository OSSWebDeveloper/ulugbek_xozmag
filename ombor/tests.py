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
    """«Birlik o'zgaradi» richagi va uning atrofidagi maydonlar."""

    MANZIL = "ombor:mahsulot_yangi"

    def yubor(self, **qoshimcha):
        malumot = {
            "nom": "Polietilen lenta", "birlik": Birlik.METR, "narx": "3500",
            "qoldiq": "", "olish_birligi": "", "olish_miqdori": "",
            "narx_birligi": "sotuv", "faol": "on",
        }
        malumot.update(qoshimcha)
        return self.client.post(reverse(self.MANZIL), malumot)

    # ---------- Richag o'chiq: oddiy tovar ----------

    def test_richag_ochiq_bolsa_oddiy_tovar_yaratiladi(self):
        self.yubor(nom="Rozetka", birlik=Birlik.DONA, qoldiq="150")
        tovar = Mahsulot.objects.get(nom="Rozetka")
        self.assertFalse(tovar.ikki_birlikmi)
        self.assertEqual(tovar.qoldiq, Decimal("150.000"))
        self.assertEqual(tovar.olish_miqdori, Decimal("1.000"))

    def test_richag_ochiq_bolsa_olish_birligi_tashlab_yuboriladi(self):
        """Richag o'chiq turib birlik yuborilsa ham e'tiborga olinmaydi."""
        self.yubor(nom="Rozetka", birlik=Birlik.DONA, qoldiq="150",
                   olish_birligi=Birlik.QUTI, olish_miqdori="25")
        tovar = Mahsulot.objects.get(nom="Rozetka")
        self.assertFalse(tovar.ikki_birlikmi)
        self.assertEqual(tovar.olish_miqdori, Decimal("1.000"))

    # ---------- Richag yoqiq: qadoq bo'yicha ----------

    def test_qadoq_sonidan_qoldiq_hisoblanadi(self):
        self.yubor(birlik_ozgaradi="on", olish_birligi=Birlik.RULON,
                   olish_miqdori="100", qadoq_soni="3")
        tovar = Mahsulot.objects.get(nom="Polietilen lenta")
        self.assertTrue(tovar.ikki_birlikmi)
        self.assertEqual(tovar.qoldiq, Decimal("300.000"))
        self.assertEqual(tovar.olish_qoldigi, Decimal("3.000"))

    def test_kasrli_qadoq_ham_hisoblanadi(self):
        self.yubor(birlik_ozgaradi="on", olish_birligi=Birlik.RULON,
                   olish_miqdori="100", qadoq_soni="2,5")
        self.assertEqual(Mahsulot.objects.get(nom="Polietilen lenta").qoldiq,
                         Decimal("250.000"))

    def test_qadoq_soni_bosh_bolsa_qoldiq_nol(self):
        self.yubor(birlik_ozgaradi="on", olish_birligi=Birlik.RULON,
                   olish_miqdori="100", qadoq_soni="")
        tovar = Mahsulot.objects.get(nom="Polietilen lenta")
        self.assertEqual(tovar.qoldiq, Decimal("0.000"))
        self.assertTrue(tovar.ikki_birlikmi)

    def test_qadoq_narxi_bittasiga_bolinadi(self):
        self.yubor(birlik_ozgaradi="on", olish_birligi=Birlik.RULON,
                   olish_miqdori="100", qadoq_soni="1",
                   narx="350000", narx_birligi="olish")
        tovar = Mahsulot.objects.get(nom="Polietilen lenta")
        self.assertEqual(tovar.narx, Decimal("3500.00"))
        self.assertEqual(tovar.olish_narxi, Decimal("350000.00"))

    def test_sotuv_narxi_ozgarmaydi(self):
        self.yubor(birlik_ozgaradi="on", olish_birligi=Birlik.RULON,
                   olish_miqdori="100", qadoq_soni="1",
                   narx="3500", narx_birligi="sotuv")
        self.assertEqual(Mahsulot.objects.get(nom="Polietilen lenta").narx,
                         Decimal("3500.00"))

    def test_boshlangich_qoldiq_tarixda_ikkala_birlikda(self):
        self.yubor(birlik_ozgaradi="on", olish_birligi=Birlik.RULON,
                   olish_miqdori="100", qadoq_soni="3")
        harakat = OmborHarakati.objects.get(mahsulot__nom="Polietilen lenta")
        self.assertEqual(harakat.tur, HarakatTuri.KIRIM)
        self.assertEqual(harakat.korinish, "3 rulon = 300 metr")

    # ---------- Xatolar ----------

    def test_kelgan_birligi_tanlanmasa_xato(self):
        javob = self.yubor(birlik_ozgaradi="on", olish_miqdori="100", qadoq_soni="3")
        self.assertEqual(javob.status_code, 200)
        self.assertFalse(Mahsulot.objects.filter(nom="Polietilen lenta").exists())
        self.assertContains(javob, "qaysi birlikda kelishini tanlang")

    def test_ikkala_birlik_bir_xil_bolsa_xato(self):
        javob = self.yubor(birlik_ozgaradi="on", olish_birligi=Birlik.METR,
                           olish_miqdori="100", qadoq_soni="3")
        self.assertEqual(javob.status_code, 200)
        self.assertFalse(Mahsulot.objects.filter(nom="Polietilen lenta").exists())
        self.assertContains(javob, "richagni o&#x27;chiring")

    def test_qadoqdagi_soni_nol_bolsa_xato(self):
        javob = self.yubor(birlik_ozgaradi="on", olish_birligi=Birlik.RULON,
                           olish_miqdori="0", qadoq_soni="3")
        self.assertEqual(javob.status_code, 200)
        self.assertFalse(Mahsulot.objects.filter(nom="Polietilen lenta").exists())
        self.assertContains(javob, "nechta metr borligini yozing")

    # ---------- Tahrirlash ----------

    def test_tahrirlashda_qadoq_soni_sorolmaydi(self):
        tovar = Mahsulot.objects.create(
            nom="Polietilen lenta 10 sm", birlik=Birlik.METR,
            olish_birligi=Birlik.RULON, olish_miqdori=Decimal("100"),
            narx=Decimal("3500"), qoldiq=Decimal("300"),
        )
        javob = self.client.get(reverse("ombor:mahsulot_tahrir", args=[tovar.pk]))
        self.assertNotContains(javob, 'id="qadoq-soni"')
        self.assertContains(javob, 'id="birlik-ozgaradi"')

    def test_tahrirlashda_qoldiq_togridan_yoziladi(self):
        tovar = Mahsulot.objects.create(
            nom="Polietilen lenta 10 sm", birlik=Birlik.METR,
            olish_birligi=Birlik.RULON, olish_miqdori=Decimal("100"),
            narx=Decimal("3500"), qoldiq=Decimal("300"),
        )
        self.client.post(reverse("ombor:mahsulot_tahrir", args=[tovar.pk]), {
            "nom": tovar.nom, "birlik": Birlik.METR, "narx": "3500",
            "qoldiq": "450", "birlik_ozgaradi": "on", "olish_birligi": Birlik.RULON,
            "olish_miqdori": "100", "narx_birligi": "sotuv", "faol": "on",
        })
        tovar.refresh_from_db()
        self.assertEqual(tovar.qoldiq, Decimal("450.000"))
        self.assertEqual(tovar.olish_qoldigi, Decimal("4.500"))


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
