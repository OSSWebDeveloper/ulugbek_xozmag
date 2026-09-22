"""Ombor sinovlari — asosan bir birlikda olinib boshqasida sotiladigan tovarlar."""
import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from config.sinov import KirganTest
from django.urls import reverse

from .forms import MahsulotForm
from .kod import ichki_shtrix, nazorat_raqami, topish
from .markaziy_bank import bankdan_sora, bugungi_kurs
from .models import (Birlik, DollarKursi, HarakatTuri, Mahsulot, OmborHarakati,
                     ShtrixKod)
from .xizmat import oxirgi_kurs


class IkkiBirlikModelTest(KirganTest):
    """Rulonda olinib metrda sotiladigan tovarning hisoblari."""

    def setUp(self):
        super().setUp()
        self.lenta = Mahsulot.objects.create(
            nom="Polietilen lenta 0,1 metr", birlik=Birlik.METR,
            olish_birligi=Birlik.RULON, olish_miqdori=Decimal("100"),
            qoldiq=Decimal("300"),
        )
        self.gisht = Mahsulot.objects.create(
            nom="G'isht", birlik=Birlik.DONA, qoldiq=Decimal("5000"),
        )

    def test_ikki_birlikli_tovar_aniqlanadi(self):
        self.assertTrue(self.lenta.ikki_birlikmi)
        self.assertFalse(self.gisht.ikki_birlikmi)

    def test_qoldiq_olish_birligida_ham_korinadi(self):
        self.assertEqual(self.lenta.olish_qoldigi, Decimal("3.000"))
        self.assertEqual(self.lenta.qoldiq_toliq, "300 metr = 3 rulon")
        self.assertEqual(self.gisht.qoldiq_toliq, "5000 dona")

    def test_qoldiq_butun_qadoq_va_ortiq_bilan_aytiladi(self):
        mix = Mahsulot.objects.create(
            nom="Mix 100 mm", birlik=Birlik.DONA,
            olish_birligi=Birlik.PACHKA, olish_miqdori=Decimal("1000"),
            qoldiq=Decimal("5020"),
        )
        self.assertEqual(mix.qadoq_soni, Decimal("5"))
        self.assertEqual(mix.qadoqdan_ortiq, Decimal("20.000"))
        self.assertEqual(mix.qadoq_matni, "5 pachka 20 dona")
        self.assertEqual(mix.qoldiq_toliq, "5020 dona = 5 pachka 20 dona")

    def test_butun_qadoq_bolsa_ortiq_aytilmaydi(self):
        self.assertEqual(self.lenta.qadoq_matni, "3 rulon")

    def test_bitta_qadoqqa_yetmasa_faqat_ortiq_aytiladi(self):
        self.lenta.qoldiq = Decimal("40")
        self.lenta.save()
        self.assertEqual(self.lenta.qadoq_matni, "40 metr")

    def test_qoldiq_nol_bolsa(self):
        self.lenta.qoldiq = Decimal("0")
        self.lenta.save()
        self.assertEqual(self.lenta.qadoq_matni, "0 metr")

    def test_kasrli_ortiq(self):
        self.lenta.qoldiq = Decimal("737.5")
        self.lenta.save()
        self.assertEqual(self.lenta.qadoq_matni, "7 rulon 37,5 metr")

    def test_birlik_qoidasi(self):
        self.assertEqual(self.lenta.birlik_qoidasi, "1 rulon = 100 metr")
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
            olish_miqdori=Decimal("5"),
        )
        tovar.refresh_from_db()
        self.assertEqual(tovar.olish_birligi, "")
        self.assertEqual(tovar.olish_miqdori, Decimal("1.000"))
        self.assertFalse(tovar.ikki_birlikmi)


class KirimTest(KirganTest):
    """Kirim ekrani: miqdor rulonda ham, metrda ham kiritilishi mumkin."""

    def setUp(self):
        super().setUp()
        self.lenta = Mahsulot.objects.create(
            nom="Polietilen lenta 0,1 metr", birlik=Birlik.METR,
            olish_birligi=Birlik.RULON, olish_miqdori=Decimal("100"),
            qoldiq=Decimal("300"),
        )
        self.gisht = Mahsulot.objects.create(
            nom="G'isht", birlik=Birlik.DONA, qoldiq=Decimal("5000"),
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

    def test_oyna_rejimida_faqat_forma_qaytadi(self):
        """Ombor ro'yxatidagi ichki oyna butun sahifani emas, formani so'raydi."""
        javob = self.client.get(reverse("ombor:kirim", args=[self.lenta.pk]), {"oyna": "1"})
        self.assertEqual(javob.status_code, 200)
        matn = javob.content.decode()
        self.assertNotIn("<!DOCTYPE html>", matn)
        self.assertIn('id="kirim-forma"', matn)
        self.assertIn('id="kirim-raqamlar"', matn)

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

    def test_nol_kirim_qabul_qilinmaydi(self):
        javob = self.client.post(reverse("ombor:kirim", args=[self.gisht.pk]), {
            "miqdor": "0", "izoh": "",
        })
        self.assertEqual(javob.status_code, 200)
        self.gisht.refresh_from_db()
        self.assertEqual(self.gisht.qoldiq, Decimal("5000.000"))
        self.assertFalse(OmborHarakati.objects.filter(mahsulot=self.gisht).exists())
        self.assertContains(javob, "noldan katta")

    def test_ikki_birlikli_tovarda_birlik_tanlovi_korinadi(self):

        javob = self.client.get(reverse("ombor:kirim", args=[self.lenta.pk]))
        self.assertContains(javob, 'name="birlik"')
        self.assertContains(javob, "1 rulon = 100 metr")


class MahsulotFormaTest(KirganTest):
    """«Birlik o'zgaradi» richagi va uning atrofidagi maydonlar."""

    MANZIL = "ombor:mahsulot_yangi"

    def yubor(self, **qoshimcha):
        malumot = {
            "nom": "Polietilen lenta", "birlik": Birlik.METR,
            "qoldiq": "", "olish_birligi": "", "olish_miqdori": "",
            "faol": "on",
        }
        malumot.update(qoshimcha)
        return self.client.post(reverse(self.MANZIL), malumot)

    # ---------- Narx ----------

    def test_narx_saqlanadi(self):
        """Narx tovarda turadi, lekin hech qayerda hisobga qo'shilmaydi."""
        self.yubor(nom="Lyustra", birlik=Birlik.DONA, qoldiq="20",
                   valyuta="dollar", narx="45")
        tovar = Mahsulot.objects.get(nom="Lyustra")
        self.assertEqual(tovar.narx, Decimal("45.00"))
        self.assertTrue(tovar.dollarmi)

    def test_narx_yozilmasa_nol(self):
        self.yubor(nom="Rozetka", birlik=Birlik.DONA, qoldiq="150")
        self.assertEqual(Mahsulot.objects.get(nom="Rozetka").narx, Decimal("0"))

    def test_narx_vergul_bilan_ham_yoziladi(self):
        self.yubor(nom="Lenta", birlik=Birlik.METR, qoldiq="10", narx="3,5")
        self.assertEqual(Mahsulot.objects.get(nom="Lenta").narx, Decimal("3.50"))

    def test_narx_royxatda_valyutasi_bilan_korinadi(self):
        self.yubor(nom="Lyustra", birlik=Birlik.DONA, qoldiq="20",
                   valyuta="dollar", narx="45")
        self.yubor(nom="Rozetka", birlik=Birlik.DONA, qoldiq="150", narx="12000")
        javob = self.client.get(reverse("ombor:royxat"))
        self.assertContains(javob, "45 $")
        self.assertContains(javob, "12 000 so&#x27;m")

    # ---------- Valyuta ----------

    def test_tovar_dollarda_kelgan_deb_belgilanadi(self):
        self.yubor(nom="Plastik truba", birlik=Birlik.METR, qoldiq="50", valyuta="dollar")
        tovar = Mahsulot.objects.get(nom="Plastik truba")
        self.assertTrue(tovar.dollarmi)

    def test_valyuta_tanlanmasa_som_boladi(self):
        self.yubor(nom="Rozetka", birlik=Birlik.DONA, qoldiq="150")
        self.assertFalse(Mahsulot.objects.get(nom="Rozetka").dollarmi)

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


    def test_takroriy_nom_tushunarli_xato_beradi(self):
        Mahsulot.objects.create(nom="Rozetka", birlik=Birlik.DONA)
        javob = self.yubor(nom="Rozetka", birlik=Birlik.DONA)
        self.assertEqual(javob.status_code, 200)
        self.assertContains(javob, "Bunday nomli tovar allaqachon bor")
        self.assertEqual(Mahsulot.objects.filter(nom="Rozetka").count(), 1)

    # ---------- Tahrirlash ----------

    def test_tahrirlashda_qadoq_soni_sorolmaydi(self):
        tovar = Mahsulot.objects.create(
            nom="Polietilen lenta 0,1 metr", birlik=Birlik.METR,
            olish_birligi=Birlik.RULON, olish_miqdori=Decimal("100"),
            qoldiq=Decimal("300"),
        )
        javob = self.client.get(reverse("ombor:mahsulot_tahrir", args=[tovar.pk]))
        self.assertNotContains(javob, 'id="qadoq-soni"')
        self.assertContains(javob, 'id="birlik-ozgaradi"')

    def test_tahrirlashda_qoldiq_togridan_yoziladi(self):
        tovar = Mahsulot.objects.create(
            nom="Polietilen lenta 0,1 metr", birlik=Birlik.METR,
            olish_birligi=Birlik.RULON, olish_miqdori=Decimal("100"),
            qoldiq=Decimal("300"),
        )
        self.client.post(reverse("ombor:mahsulot_tahrir", args=[tovar.pk]), {
            "nom": tovar.nom, "birlik": Birlik.METR,
            "qoldiq": "450", "birlik_ozgaradi": "on", "olish_birligi": Birlik.RULON,
            "olish_miqdori": "100", "faol": "on",
        })
        tovar.refresh_from_db()
        self.assertEqual(tovar.qoldiq, Decimal("450.000"))
        self.assertEqual(tovar.olish_qoldigi, Decimal("4.500"))


class SotuvBirligiTest(KirganTest):
    """Sotuv va qarz tomonida hech nima o'zgarmaydi — hammasi sotuv birligida."""

    def setUp(self):
        super().setUp()
        self.lenta = Mahsulot.objects.create(
            nom="Polietilen lenta 0,1 metr", birlik=Birlik.METR,
            olish_birligi=Birlik.RULON, olish_miqdori=Decimal("100"),
            qoldiq=Decimal("300"),
        )

    def test_sotuvdan_keyin_ikkala_korsatkich_tori_qoladi(self):
        from ombor.xizmat import ayir

        ayir(self.lenta.pk, Decimal("150"), "Sinov")
        self.lenta.refresh_from_db()
        self.assertEqual(self.lenta.qoldiq, Decimal("150.000"))
        self.assertEqual(self.lenta.olish_qoldigi, Decimal("1.500"))
        self.assertEqual(self.lenta.qoldiq_toliq, "150 metr = 1 rulon 50 metr")


class DollarKursiTest(KirganTest):
    """Kassadagi kurs standart qiymati Markaziy bankdan olinadi.

    Sinovlar tarmoqqa chiqmaydi: `bankdan_sora()` almashtiriladi.
    """

    def test_bank_kursi_bazaga_yoziladi(self):
        with patch("ombor.markaziy_bank.bankdan_sora", return_value=Decimal("12346")):
            self.assertEqual(bugungi_kurs(), Decimal("12346"))
        yozuv = DollarKursi.objects.get(sana=timezone.localdate())
        self.assertEqual(yozuv.kurs, Decimal("12346.00"))

    def test_bank_tiyini_butun_somga_yaxlitlanadi(self):
        """Bank 11809.82 deydi — do'konda 11 810 bo'lib turadi."""
        javob = json.dumps([{"Ccy": "USD", "Rate": "11809.82"}]).encode("utf-8")
        with patch("ombor.markaziy_bank.urlopen") as ochish:
            ochish.return_value.__enter__.return_value.read.return_value = javob
            self.assertEqual(bankdan_sora(), Decimal("11810"))

    def test_kun_davomida_bir_marta_soraladi(self):
        """Kurs bazada bo'lsa bankka qayta murojaat qilinmaydi."""
        DollarKursi.objects.create(sana=timezone.localdate(), kurs=Decimal("12800"))
        with patch("ombor.markaziy_bank.bankdan_sora",
                   side_effect=AssertionError("tarmoqqa chiqmasligi kerak")):
            self.assertEqual(bugungi_kurs(), Decimal("12800"))

    def test_internet_yoq_bolsa_oldingi_kun_kursi(self):
        DollarKursi.objects.create(sana=timezone.localdate() - timedelta(days=1),
                                   kurs=Decimal("12700"))
        with patch("ombor.markaziy_bank.bankdan_sora", return_value=None):
            self.assertEqual(bugungi_kurs(), Decimal("12700"))
        # Urinish yozib qo'yiladi — har safar tarmoqni kutib turmaslik uchun
        self.assertTrue(DollarKursi.objects.filter(sana=timezone.localdate()).exists())

    def test_bank_kursi_yoq_bolsa_qolda_yozilgani_qoladi(self):
        from sotuv.models import Sotuv

        Sotuv.objects.create(jami=Decimal("100000"), jami_dollar=Decimal("10"),
                             kurs=Decimal("12900"), yakunlangan=True)
        with patch("ombor.markaziy_bank.bankdan_sora", return_value=None):
            kurs = oxirgi_kurs()
        self.assertEqual(kurs.qiymat, Decimal("12900"))
        self.assertEqual(kurs.manba, "oxirgi yozilgan kurs")

    def test_hech_narsa_bolmasa_bosh_qoladi(self):
        with patch("ombor.markaziy_bank.bankdan_sora", return_value=None):
            self.assertIsNone(oxirgi_kurs())

    def test_kassada_bank_kursi_tayyor_turadi(self):
        with patch("ombor.markaziy_bank.bankdan_sora", return_value=Decimal("12346")):
            javob = self.client.get(reverse("sotuv:boshlash"), follow=True)
        self.assertContains(javob, "12 346")
        self.assertContains(javob, "Markaziy bank kursi")


class KodTest(KirganTest):
    """Tovar kodi: yaratilganda beriladi va hech qachon o'zgarmaydi."""

    def setUp(self):
        super().setUp()
        self.gisht = Mahsulot.objects.create(nom="G'isht", birlik=Birlik.DONA,
                                             qoldiq=Decimal("5000"))

    def test_kod_id_dan_chiqadi(self):
        self.assertEqual(self.gisht.kod, f"{self.gisht.pk:010d}")
        self.assertEqual(len(self.gisht.kod), 10)

    def test_qisqa_kod_oxirgi_tort_raqam(self):
        self.assertEqual(self.gisht.qisqa_kod, self.gisht.kod[-4:])
        self.assertEqual(len(self.gisht.qisqa_kod), 4)

    def test_kod_qayta_saqlashda_ozgarmaydi(self):
        """Kod o'zgarsa bosilgan yorliqlarning hammasi yaroqsiz bo'lib qoladi."""
        eski = self.gisht.kod
        self.gisht.nom = "G'isht qizil"
        self.gisht.save()
        self.gisht.refresh_from_db()
        self.assertEqual(self.gisht.kod, eski)

    def test_har_bir_tovarda_boshqa_kod(self):
        sement = Mahsulot.objects.create(nom="Sement", birlik=Birlik.QOP)
        self.assertNotEqual(self.gisht.kod, sement.kod)


class KodQidirishTest(KirganTest):
    """`ombor/kod.py` — kassa, tarozi va ombor shu qidiruvdan foydalanadi."""

    def setUp(self):
        super().setUp()
        self.gisht = Mahsulot.objects.create(nom="G'isht", birlik=Birlik.DONA,
                                             qoldiq=Decimal("5000"))
        self.mix = Mahsulot.objects.create(
            nom="Mix 100 mm", birlik=Birlik.DONA, olish_birligi=Birlik.PACHKA,
            olish_miqdori=Decimal("1000"), qoldiq=Decimal("5020"),
        )

    def test_qisqa_kod_bilan_topiladi(self):
        natija = topish(self.gisht.qisqa_kod)
        self.assertEqual(natija.mahsulot, self.gisht)
        self.assertEqual(natija.qanday, "qisqa")
        self.assertIsNone(natija.miqdor)

    def test_boshidagi_nollarsiz_ham_topiladi(self):
        """Kassir 0007 emas, shunchaki 7 deb ursa ham o'sha tovar chiqadi."""
        natija = topish(str(int(self.gisht.kod)))
        self.assertEqual(natija.mahsulot, self.gisht)

    def test_toliq_kod_bilan_topiladi(self):
        self.assertEqual(topish(self.gisht.kod).mahsulot, self.gisht)

    def test_bosh_joylar_tashlanadi(self):
        self.assertEqual(topish(" " + self.gisht.qisqa_kod + " ").mahsulot, self.gisht)

    def test_notanish_kod_xato_beradi(self):
        natija = topish("9999")
        self.assertIsNone(natija.mahsulot)
        self.assertIn("topilmadi", natija.xato)

    def test_bosh_kod_xato_beradi(self):
        self.assertIsNotNone(topish("").xato)

    # ---------- Zavod shtrixi ----------

    def test_zavod_shtrixi_topiladi(self):
        ShtrixKod.objects.create(mahsulot=self.gisht, kod="4780123456789")
        natija = topish("4780123456789")
        self.assertEqual(natija.mahsulot, self.gisht)
        self.assertEqual(natija.qanday, "shtrix")
        self.assertEqual(natija.miqdor, Decimal("1"))

    def test_quti_shtrixi_qutidagi_sonni_beradi(self):
        """Quti skanerlansa 1 dona emas, qutidagi 1000 dona tushadi."""
        ShtrixKod.objects.create(mahsulot=self.mix, kod="4780000000017",
                                 miqdor=Decimal("1000"), izoh="quti")
        natija = topish("4780000000017")
        self.assertEqual(natija.mahsulot, self.mix)
        self.assertEqual(natija.miqdor, Decimal("1000"))

    def test_notanish_shtrix_alohida_aytiladi(self):
        """Ombor shunga qarab «yangi tovar qo'shilsinmi?» deb so'raydi."""
        natija = topish("4780999999995")
        self.assertIsNone(natija.mahsulot)
        self.assertEqual(natija.qanday, "shtrix")

    # ---------- Etiketka va tarozi ----------

    def test_etiketka_kodi_on_uch_raqam(self):
        kod = self.gisht.etiketka_kodi
        self.assertEqual(len(kod), 13)
        self.assertTrue(kod.startswith("2"))
        self.assertEqual(str(nazorat_raqami(kod[:12])), kod[12])

    def test_etiketka_kodi_ogirliksiz(self):
        natija = topish(self.gisht.etiketka_kodi)
        self.assertEqual(natija.mahsulot, self.gisht)
        self.assertEqual(natija.qanday, "tarozi")
        self.assertIsNone(natija.miqdor)   # miqdorni kassir yozadi

    def test_tarozi_etiketkasi_ogirlikni_beradi(self):
        kod = ichki_shtrix(self.gisht.kod, Decimal("1.25"))
        natija = topish(kod)
        self.assertEqual(natija.mahsulot, self.gisht)
        self.assertEqual(natija.miqdor, Decimal("1.250"))

    def test_nazorat_raqami_notogri_shtrix_qabul_qilinmaydi(self):
        """Skaner yarim o'qisa noto'g'ri tovar sotilib ketmasin."""
        toliq = self.gisht.etiketka_kodi
        buzuq = toliq[:12] + ("1" if toliq[12] == "0" else "0")
        self.assertIsNone(topish(buzuq).mahsulot)

    def test_ogirlik_shtrixga_sigmasa_xato(self):
        with self.assertRaises(ValueError):
            ichki_shtrix(self.gisht.kod, Decimal("150"))


class KodManziliTest(KirganTest):
    """`/ombor/kod/` — kassa va ombor shu manzilga so'raydi."""

    def setUp(self):
        super().setUp()
        self.gisht = Mahsulot.objects.create(nom="G'isht", birlik=Birlik.DONA,
                                             qoldiq=Decimal("5000"))

    def javob(self, kod):
        return json.loads(self.client.get(reverse("ombor:kod_qidir"),
                                          {"k": kod}).content)

    def test_topilgan_tovar_qaytadi(self):
        javob = self.javob(self.gisht.qisqa_kod)
        self.assertTrue(javob["topildi"])
        self.assertEqual(javob["id"], self.gisht.pk)
        self.assertEqual(javob["nom"], "G'isht")
        self.assertEqual(javob["qoldiq"], "5000")
        self.assertEqual(javob["miqdor"], "")       # miqdorni kassir yozadi
        self.assertIn("kirim", javob)

    def test_tarozi_kodida_miqdor_ham_qaytadi(self):
        javob = self.javob(ichki_shtrix(self.gisht.kod, Decimal("2.5")))
        self.assertTrue(javob["topildi"])
        self.assertEqual(javob["miqdor"], "2.5")

    def test_topilmasa_sabab_aytiladi(self):
        javob = self.javob("9999")
        self.assertFalse(javob["topildi"])
        self.assertIn("topilmadi", javob["xato"])
        self.assertEqual(javob["kod"], "9999")


class ShtrixFormaTest(KirganTest):
    """Tovar kartochkasidagi «Zavod shtrixlari» maydoni."""

    def asos(self, **qoshimcha):
        malumot = {"nom": "Rozetka", "birlik": Birlik.DONA, "qoldiq": "50",
                   "faol": "on"}
        malumot.update(qoshimcha)
        return malumot

    def test_skanerlangan_kod_saqlanadi(self):
        forma = MahsulotForm(self.asos(shtrix="4780123456789"), yangi=True)
        self.assertTrue(forma.is_valid(), forma.errors)
        mahsulot = forma.save()
        self.assertEqual([s.kod for s in mahsulot.shtrixlar.all()], ["4780123456789"])

    def test_quti_kodi_miqdor_bilan_yoziladi(self):
        forma = MahsulotForm(self.asos(shtrix="4780123456789\n4780000000017 1000"),
                             yangi=True)
        self.assertTrue(forma.is_valid(), forma.errors)
        mahsulot = forma.save()
        quti = mahsulot.shtrixlar.get(kod="4780000000017")
        self.assertEqual(quti.miqdor, Decimal("1000"))

    def test_band_kod_boshqa_tovarga_berilmaydi(self):
        """Bitta shtrix ikki tovarni bildirsa kassa qaysi birini olishni bilmaydi."""
        gisht = Mahsulot.objects.create(nom="G'isht", birlik=Birlik.DONA)
        ShtrixKod.objects.create(mahsulot=gisht, kod="4780123456789")
        forma = MahsulotForm(self.asos(shtrix="4780123456789"), yangi=True)
        self.assertFalse(forma.is_valid())
        self.assertIn("G'isht", forma.errors["shtrix"][0])

    def test_qator_ochirilsa_kod_ham_ochadi(self):
        mahsulot = Mahsulot.objects.create(nom="Rozetka", birlik=Birlik.DONA)
        ShtrixKod.objects.create(mahsulot=mahsulot, kod="4780123456789")
        forma = MahsulotForm(self.asos(shtrix=""), instance=mahsulot, yangi=False)
        self.assertTrue(forma.is_valid(), forma.errors)
        forma.save()
        self.assertEqual(mahsulot.shtrixlar.count(), 0)

    def test_tahrirlashda_mavjud_kodlar_maydonda_turadi(self):
        mahsulot = Mahsulot.objects.create(nom="Rozetka", birlik=Birlik.DONA)
        ShtrixKod.objects.create(mahsulot=mahsulot, kod="4780123456789")
        forma = MahsulotForm(instance=mahsulot, yangi=False)
        self.assertEqual(forma.initial["shtrix"], "4780123456789")

    def test_ozining_kodi_band_deb_hisoblanmaydi(self):
        mahsulot = Mahsulot.objects.create(nom="Rozetka", birlik=Birlik.DONA)
        ShtrixKod.objects.create(mahsulot=mahsulot, kod="4780123456789")
        forma = MahsulotForm(self.asos(shtrix="4780123456789"), instance=mahsulot,
                             yangi=False)
        self.assertTrue(forma.is_valid(), forma.errors)

    def test_koddan_keyingi_matn_xato_beradi(self):
        forma = MahsulotForm(self.asos(shtrix="4780123456789 quti"), yangi=True)
        self.assertFalse(forma.is_valid())


class OmborKodBilanQidirishTest(KirganTest):
    """Ombor ro'yxati kod bo'yicha ham qidiradi — yorliqdagi raqam yoziladi."""

    def test_kod_bilan_topiladi(self):
        rozetka = Mahsulot.objects.create(nom="Rozetka", birlik=Birlik.DONA)
        Mahsulot.objects.create(nom="Sement", birlik=Birlik.QOP)
        javob = self.client.get(reverse("ombor:royxat"), {"q": rozetka.qisqa_kod})
        self.assertContains(javob, "Rozetka")
        self.assertNotContains(javob, "Sement")

    def test_nom_bilan_qidirish_ishlayveradi(self):
        Mahsulot.objects.create(nom="Rozetka", birlik=Birlik.DONA)
        Mahsulot.objects.create(nom="Sement", birlik=Birlik.QOP)
        javob = self.client.get(reverse("ombor:royxat"), {"q": "ozet"})
        self.assertContains(javob, "Rozetka")
        self.assertNotContains(javob, "Sement")
