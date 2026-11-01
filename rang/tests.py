"""Rang (kolerovka): katalog, shtrix, stansiya, chek, kassa va Wi-Fi manzili."""
import json
from decimal import Decimal
from unittest.mock import patch

from django.test import SimpleTestCase
from django.urls import reverse

from config.sinov import KirganTest
from config.tarmoq import _ichkimi, manzillar
from ombor.kod import rang_cheki_kodi, rang_chekini_ochish, topish
from ombor.models import Birlik, Mahsulot, Valyuta
from ombor.shtrix import JIM_ZONA, NAQSHLAR
from qarz.models import Hudud, Qarz, Qarzdor
from sotuv.models import Sotuv

from .models import Buyurtma, Holat, Rang, kalit_yasa
from .namuna import RAL
from .shtrix import belgilar, chiziqlar
from .yuklash import oqi, yukla


def ochir(matn):
    """Chizilgan shtrixni qaytadan o'qiydi: chiziqlar -> belgilar -> matn.

    Code 128 ning B va C to'plamlari, o'tish belgilari va nazorat belgisi
    tekshiriladi — chizish buzilsa test shu yerda ushlaydi.
    """
    qora, eni = chiziqlar(matn)
    modullar = [0] * eni
    for x, en in qora:
        for i in range(x, x + en):
            modullar[i] = 1
    kengliklar, joriy, soni = [], modullar[JIM_ZONA], 0
    for m in modullar[JIM_ZONA:eni - JIM_ZONA]:
        if m == joriy:
            soni += 1
        else:
            kengliklar.append(soni)
            joriy, soni = m, 1
    kengliklar.append(soni)
    qiymatlar = [NAQSHLAR.index("".join(map(str, kengliklar[i:i + 6])))
                 for i in range(0, len(kengliklar) - 7, 6)]
    assert "".join(map(str, kengliklar[-7:])) == NAQSHLAR[106], "tugash belgisi yo'q"
    *asosiy, nazorat = qiymatlar
    assert nazorat == (asosiy[0] + sum(q * i for i, q in enumerate(asosiy[1:], 1))) % 103

    toplam = {104: "B", 105: "C"}[asosiy[0]]
    natija = ""
    for q in asosiy[1:]:
        if toplam == "C":
            if q == 100:
                toplam = "B"
            else:
                natija += f"{q:02d}"
        else:
            if q == 99:
                toplam = "C"
            else:
                natija += chr(q + 32)
    return natija


class ShtrixTest(KirganTest):
    """Katalog shtrixi — Soruda kodining o'zi, harfli bo'lsa ham."""

    def test_qaytadan_oqiladi(self):
        for matn in ("RAL 3020", "1015", "12345", "S 1050-Y90R", "A1", "0000", "7",
                     "ABC123456", "12AB", "X-9 ", "123456789012", "a1234567b", "1234ABC"):
            self.assertEqual(ochir(matn), matn, matn)

    def test_juft_raqam_c_toplamida(self):
        """Raqamli kod C to'plamida — shtrix kalta chiqadi."""
        self.assertEqual(belgilar("1015")[0], 105)
        self.assertEqual(len(belgilar("1015")), 5)          # boshlash, 10, 15, nazorat, tugash

    def test_harfli_kod_b_toplamida_raqamlari_c_da(self):
        qiymatlar = belgilar("RAL 3020")
        self.assertEqual(qiymatlar[0], 104)
        self.assertIn(99, qiymatlar)                          # oxiridagi 4 raqam uchun C ga o'tadi
        self.assertEqual(len(qiymatlar), 1 + 4 + 1 + 2 + 2)

    def test_kirill_harf_rad_etiladi(self):
        with self.assertRaises(ValueError):
            belgilar("РАЛ 3020")
        with self.assertRaises(ValueError):
            belgilar("")


class RangModelTest(KirganTest):
    def test_kalit_bo_shliq_va_harfga_qaramaydi(self):
        self.assertEqual(kalit_yasa("ral 3020"), kalit_yasa("RAL-3020"))
        rang = Rang.objects.create(kod=" RAL 3020 ", hex="cc0605")
        self.assertEqual(rang.kod, "RAL 3020")
        self.assertEqual(rang.kalit, "RAL3020")
        self.assertEqual(rang.hex, "#CC0605")

    def test_yozuv_rangi(self):
        self.assertEqual(Rang(kod="a", hex="#FFFFFF").yozuv_rangi, "#000000")
        self.assertEqual(Rang(kod="b", hex="#0A0A0A").yozuv_rangi, "#FFFFFF")
        self.assertEqual(Rang(kod="c", hex="").yozuv_rangi, "#000000")

    def test_tartib_toplam_oxiriga(self):
        birinchi = Rang.objects.create(kod="A1", toplam="X")
        ikkinchi = Rang.objects.create(kod="A2", toplam="X")
        self.assertEqual(ikkinchi.tartib, birinchi.tartib + 1)


class RangFormaTest(KirganTest):
    def test_yangi_rang(self):
        javob = self.client.post(reverse("rang:rang_yangi"), {
            "kod": "RAL 5015", "nom": "Osmon ko'k", "hex": "2271b3", "toplam": "RAL", "faol": "on",
        })
        self.assertEqual(javob.status_code, 302)
        rang = Rang.objects.get(kod="RAL 5015")
        self.assertEqual(rang.hex, "#2271B3")

    def test_bir_xil_kalitli_kod_rad_etiladi(self):
        Rang.objects.create(kod="RAL 5015")
        javob = self.client.post(reverse("rang:rang_yangi"), {"kod": "ral5015", "faol": "on"})
        self.assertEqual(javob.status_code, 200)
        self.assertContains(javob, "allaqachon bor")

    def test_kirill_kod_rad_etiladi(self):
        javob = self.client.post(reverse("rang:rang_yangi"), {"kod": "Қизил", "faol": "on"})
        self.assertContains(javob, "kirill")
        self.assertFalse(Rang.objects.exists())

    def test_notogri_rang(self):
        javob = self.client.post(reverse("rang:rang_yangi"), {"kod": "X1", "hex": "#12", "faol": "on"})
        self.assertContains(javob, "#RRGGBB")

    def test_tahrir_sahifasida_shtrix(self):
        rang = Rang.objects.create(kod="RAL 1015", hex="#E6D690")
        javob = self.client.get(reverse("rang:rang_tahrir", args=[rang.pk]))
        self.assertContains(javob, "<svg")
        self.assertContains(javob, "RAL 1015")

    def test_chekli_rang_ochirilmaydi_yashiriladi(self):
        rang, baza = _rang_va_baza()
        Buyurtma.objects.create(rang=rang, rang_kodi=rang.kod, baza=baza, baza_nomi=baza.nom)
        self.client.post(reverse("rang:rang_ochirish", args=[rang.pk]))
        rang.refresh_from_db()
        self.assertFalse(rang.faol)

    def test_chek_chiqmagan_rang_ochiriladi(self):
        rang = Rang.objects.create(kod="X9")
        self.client.post(reverse("rang:rang_ochirish", args=[rang.pk]))
        self.assertFalse(Rang.objects.filter(pk=rang.pk).exists())


class YuklashTest(KirganTest):
    def test_format_va_ajratuvchilar(self):
        ranglar, xatolar = oqi("Kod;Nomi;Rang\n"
                               "RAL 1015;Och fil suyagi;#E6D690\n"
                               "RAL 3020\tYo'l qizil\tcc0605\n"
                               "1001,#C2B078,Bej\n"
                               "\n"
                               "Қизил;xato\n"
                               "RAL 1015;takror\n")
        self.assertEqual(ranglar, [
            ("RAL 1015", "Och fil suyagi", "#E6D690"),
            ("RAL 3020", "Yo'l qizil", "#CC0605"),
            ("1001", "Bej", "#C2B078"),
        ])
        self.assertEqual(len(xatolar), 2)

    def test_qayta_yuklash_yangilaydi(self):
        birinchi = yukla("A1;Eski;#000000\nA2;;#111111", "T")
        self.assertEqual((birinchi.yangi, birinchi.yangilandi), (2, 0))
        ikkinchi = yukla("a 1;Yangi\nA3;;#333333", "T")
        self.assertEqual((ikkinchi.yangi, ikkinchi.yangilandi), (1, 1))
        a1 = Rang.objects.get(kalit="A1")
        self.assertEqual(a1.kod, "a 1")             # kod ro'yxatdagidek bo'ladi
        self.assertEqual(a1.nom, "Yangi")
        self.assertEqual(a1.hex, "#000000")         # rang berilmasa eskisi qoladi
        self.assertEqual(Rang.objects.count(), 3)

    def test_namuna_ral(self):
        ranglar, xatolar = oqi(RAL)
        self.assertEqual(len(ranglar), 213)
        self.assertEqual(xatolar, [])
        javob = self.client.post(reverse("rang:yuklash"), {"namuna": "ral"})
        self.assertEqual(javob.status_code, 302)
        self.assertEqual(Rang.objects.filter(toplam="RAL").count(), 213)
        self.assertEqual(Rang.objects.get(kod="RAL 3020").hex, "#CC0605")

    def test_sahifadan_yuklash(self):
        self.client.post(reverse("rang:yuklash"), {"matn": "S1;Bir;#FF0000", "toplam": "Soruda"})
        self.assertTrue(Rang.objects.filter(kod="S1", toplam="Soruda").exists())

    def test_bosh_royxat_xato(self):
        javob = self.client.post(reverse("rang:yuklash"), {"matn": "Қ;Қ", "toplam": ""}, follow=True)
        self.assertContains(javob, "Bironta rang o")
        self.assertFalse(Rang.objects.exists())

    def test_toplamni_ochirish(self):
        yukla(RAL, "RAL")
        rang, baza = _rang_va_baza(kod="RAL 3020")
        Buyurtma.objects.create(rang=rang, rang_kodi=rang.kod, baza=baza, baza_nomi=baza.nom)
        self.client.post(reverse("rang:toplam_ochirish"), {"toplam": "RAL"})
        self.assertEqual(list(Rang.objects.values_list("kod", "faol")), [("RAL 3020", False)])


class SahifalarTest(KirganTest):
    def setUp(self):
        super().setUp()
        yukla(RAL, "RAL")

    def test_ranglar_royxati(self):
        javob = self.client.get(reverse("rang:ranglar"), {"q": "3020"})
        self.assertContains(javob, "RAL 3020")
        self.assertNotContains(javob, "RAL 1015")

    def test_katalog_varagi(self):
        javob = self.client.get(reverse("rang:varaq"), {"ustun": "5"})
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.context["soni"], 213)
        self.assertEqual(javob.context["ustun"], 5)
        self.assertContains(javob, 'class="katak"', count=213)

    def test_varaq_toplam_va_bosh_katak(self):
        Rang.objects.create(kod="S1", toplam="Soruda")
        javob = self.client.get(reverse("rang:varaq"), {"t": "Soruda", "tur": "bosh", "ustun": "9"})
        self.assertEqual(javob.context["soni"], 1)
        self.assertEqual(javob.context["ustun"], 4)          # noto'g'ri qiymat — standart
        self.assertContains(javob, "katak-rang bosh")
        self.assertEqual(self.client.get(reverse("rang:varaq"), {"t": "*"}).context["soni"], 214)

    def test_qatorda_ikki_rang(self):
        """Oz rangli varaq (10 ta) uchun: katta namunalar, qatorda 2 ta."""
        javob = self.client.get(reverse("rang:varaq"), {"ustun": "2"})
        self.assertEqual(javob.context["ustun"], 2)
        self.assertContains(javob, 'data-ustun="2"')

    def test_yashirilgan_rang_varaqda_yoq(self):
        Rang.objects.filter(kod="RAL 3020").update(faol=False)
        self.assertEqual(self.client.get(reverse("rang:varaq")).context["soni"], 212)

    def test_menyuda_rang_bolimi(self):
        javob = self.client.get(reverse("qarz:boshlash"))
        self.assertContains(javob, reverse("rang:stansiya"))


def _rang_va_baza(kod="RAL 3020", qoldiq="10", narx="120000", valyuta=Valyuta.SOM):
    rang = Rang.objects.filter(kod=kod).first() or Rang.objects.create(
        kod=kod, nom="Yo'l qizil", hex="#CC0605", toplam="RAL")
    baza = Mahsulot.objects.create(nom=f"Emulsiya baza {Mahsulot.objects.count() + 1}",
                                   birlik=Birlik.DONA, qoldiq=Decimal(qoldiq),
                                   narx=Decimal(narx), valyuta=valyuta)
    return rang, baza


class StansiyaTest(KirganTest):
    def setUp(self):
        super().setUp()
        self.rang, self.baza = _rang_va_baza()

    def kod(self, kiritilgan):
        return json.loads(self.client.get(reverse("rang:kod_qidir"), {"k": kiritilgan}).content)

    def test_sahifa_ochiladi(self):
        javob = self.client.get(reverse("rang:stansiya"))
        self.assertEqual(javob.status_code, 200)
        self.assertContains(javob, "Chek chiqarish")

    def test_rang_skaneri(self):
        javob = self.kod("RAL 3020")
        self.assertEqual(javob["tur"], "rang")
        self.assertEqual(javob["id"], self.rang.pk)
        self.assertEqual(self.kod("ral3020")["tur"], "rang")       # qo'lda boshqacha yozilsa ham

    def test_rang_kodi_oxiri_bilan(self):
        self.assertEqual(self.kod("3020")["id"], self.rang.pk)

    def test_baza_etiketkasi(self):
        javob = self.kod(self.baza.kod)
        self.assertEqual(javob["tur"], "baza")
        self.assertEqual(javob["id"], self.baza.pk)
        self.assertEqual(javob["narx"], "120000")

    def test_raqamli_rang_kodi_tovardan_oldin(self):
        """«0001» rang kodi tovar kodi bilan adashmasin: qo'lda yozilsa — rang,
        etiketka skanerlansa (000001) — baza."""
        rang = Rang.objects.create(kod=self.baza.qisqa_kod)
        javob = self.kod(self.baza.qisqa_kod)
        self.assertEqual((javob["tur"], javob["id"]), ("rang", rang.pk))
        self.assertEqual(self.kod(self.baza.etiketka_kodi)["tur"], "baza")   # etiketka — baza

    def test_notanish_kod(self):
        javob = self.kod("NCS S 9999")
        self.assertFalse(javob["topildi"])
        self.assertIn("katalogda", javob["xato"])

    def test_chek_skanerlansa_ochiladi(self):
        chek = self.chek_chiqar()
        javob = self.kod(chek.kod)
        self.assertEqual(javob["tur"], "chek")
        self.assertEqual(javob["manzil"], reverse("rang:chek", args=[chek.pk]))

    def chek_chiqar(self, **qoshimcha):
        malumot = {"rang": self.rang.pk, "baza": self.baza.pk, "miqdor": "2", "rang_narxi": "15 000"}
        malumot.update(qoshimcha)
        javob = self.client.post(reverse("rang:stansiya"), malumot)
        chek = Buyurtma.objects.order_by("-pk").first()
        if chek:
            self.assertRedirects(javob, reverse("rang:chek", args=[chek.pk]) + "?chop=1",
                                 fetch_redirect_response=False)
        return chek

    def test_chek_chiqadi(self):
        chek = self.chek_chiqar()
        self.assertEqual(chek.rang_kodi, "RAL 3020")
        self.assertEqual(chek.baza_nomi, self.baza.nom)
        self.assertEqual(chek.miqdor, Decimal("2"))
        self.assertEqual(chek.rang_narxi, Decimal("15000"))
        self.assertEqual(chek.jami_som, Decimal("255000"))     # 2 × 120 000 + 15 000
        self.assertEqual(chek.holat, Holat.KUTILMOQDA)
        # Ombordan hali ayrilmaydi — kassada ayriladi
        self.baza.refresh_from_db()
        self.assertEqual(self.baza.qoldiq, Decimal("10"))

    def test_chek_sahifasi(self):
        chek = self.chek_chiqar()
        javob = self.client.get(reverse("rang:chek", args=[chek.pk]), {"chop": "1"})
        self.assertContains(javob, "RAL 3020")
        self.assertContains(javob, "255 000 so")
        self.assertContains(javob, "<svg")
        self.assertContains(javob, "data-chop")
        self.assertEqual(ochir_raqam(chek.kod), chek.kod)

    def test_rangsiz_bazasiz_chek_chiqmaydi(self):
        for malumot, xato in (({"rang": ""}, "Rangni skanerlang"),
                              ({"baza": ""}, "yoqni tanlang"),
                              ({"rang": "abc"}, "Rangni skanerlang"),
                              ({"miqdor": "0"}, "Miqdor"),
                              ({"rang_narxi": "-5"}, "manfiy")):
            with self.subTest(malumot=malumot):
                javob = self.client.post(reverse("rang:stansiya"), {
                    "rang": self.rang.pk, "baza": self.baza.pk, "miqdor": "1", "rang_narxi": "0",
                    **malumot})
                self.assertEqual(javob.status_code, 200)
                self.assertContains(javob, xato)
        self.assertFalse(Buyurtma.objects.exists())

    def test_xatoda_tanlov_saqlanadi(self):
        javob = self.client.post(reverse("rang:stansiya"), {
            "rang": self.rang.pk, "baza": self.baza.pk, "miqdor": "0", "rang_narxi": "5000"})
        self.assertContains(javob, f'data-id="{self.rang.pk}"')
        self.assertContains(javob, f'data-id="{self.baza.pk}"')

    def test_omborda_yetmasa_chek_chiqmaydi(self):
        javob = self.client.post(reverse("rang:stansiya"), {
            "rang": self.rang.pk, "baza": self.baza.pk, "miqdor": "11", "rang_narxi": "0"})
        self.assertContains(javob, "Omborda yetarli emas")
        self.assertFalse(Buyurtma.objects.exists())

    def test_dollarlik_baza_somga_qoshilmaydi(self):
        _, dollarlik = _rang_va_baza(narx="12.5", valyuta=Valyuta.DOLLAR)
        chek = self.chek_chiqar(baza=dollarlik.pk)
        self.assertEqual(chek.jami_som, Decimal("15000"))
        self.assertEqual(chek.jami_dollar, Decimal("25.0"))
        javob = self.client.get(reverse("rang:chek", args=[chek.pk]))
        self.assertContains(javob, "25 $ va 15 000 so")

    def test_bekor_qilish(self):
        chek = self.chek_chiqar()
        self.client.post(reverse("rang:bekor", args=[chek.pk]))
        chek.refresh_from_db()
        self.assertTrue(chek.bekor_qilingan)
        self.assertIsNotNone(topish(chek.kod).xato)          # kassada endi o'tmaydi

    def test_stansiyada_bugungi_cheklar(self):
        self.chek_chiqar()
        javob = self.client.get(reverse("rang:stansiya"))
        self.assertContains(javob, "lanmagan")        # «To'lanmagan» — apostrof sahifada ekranlanadi
        self.assertEqual(len(javob.context["bugungi"]), 1)


class TarmoqTest(SimpleTestCase):
    """Wi-Fi manzili: rang mashinasi kompyuteri serverga shu bilan ulanadi."""

    def test_faqat_ichki_tarmoq(self):
        for ip in ("192.168.1.5", "10.0.0.2", "172.20.1.1"):
            self.assertTrue(_ichkimi(ip), ip)
        for ip in ("127.0.0.1", "169.254.3.4", "8.8.8.8", "::1", "abc"):
            self.assertFalse(_ichkimi(ip), ip)

    def test_manzillar(self):
        with patch("config.tarmoq.ip_manzillar", return_value=["192.168.1.5"]), \
                patch("config.tarmoq.socket.gethostname", return_value="KASSA"):
            self.assertEqual(manzillar(8000), ["http://192.168.1.5:8000/", "http://KASSA:8000/"])

    def test_tarmoq_yoq(self):
        with patch("config.tarmoq.ip_manzillar", return_value=[]):
            self.assertEqual(manzillar(8000), [])


class StansiyaTarmoqTest(KirganTest):
    def test_stansiyada_wifi_manzili(self):
        with patch("rang.views.manzillar", return_value=["http://192.168.1.5:8000/"]):
            javob = self.client.get(reverse("rang:stansiya"))
        self.assertContains(javob, "Wi-Fi: http://192.168.1.5:8000/rang/")

    def test_tarmoqsiz_manzil_chiqmaydi(self):
        with patch("rang.views.manzillar", return_value=[]):
            javob = self.client.get(reverse("rang:stansiya"))
        self.assertNotContains(javob, "Wi-Fi:")


def ochir_raqam(kod):
    """Chekdagi (C to'plami) shtrixni o'qiydi — ombor testidagi o'quvchi bilan."""
    from ombor.tests import ochir_code128
    return ochir_code128(kod)


class KassaTest(KirganTest):
    """Chek kassada: skanerlansa baza bo'yoq miqdori bilan tushadi, bir marta."""

    def setUp(self):
        super().setUp()
        self.rang, self.baza = _rang_va_baza()
        self.chek = Buyurtma.objects.create(
            rang=self.rang, rang_kodi=self.rang.kod, baza=self.baza, baza_nomi=self.baza.nom,
            miqdor=Decimal("2"), baza_narxi=self.baza.narx, rang_narxi=Decimal("15000"))
        self.sotuv = Sotuv.objects.create()

    def kassa_kodi(self, kod):
        return json.loads(self.client.get(reverse("ombor:kod_qidir"), {"k": kod}).content)

    def qosh(self, **qoshimcha):
        malumot = {"mahsulot": self.baza.pk, "miqdor": "2", "rang_chek": self.chek.pk}
        malumot.update(qoshimcha)
        return self.client.post(reverse("sotuv:qator_qoshish", args=[self.sotuv.pk]), malumot,
                                follow=True)

    def test_kod_formati(self):
        kod = rang_cheki_kodi(12)
        self.assertEqual(len(kod), 12)
        self.assertTrue(kod.startswith("77"))
        self.assertEqual(rang_chekini_ochish(kod), 12)
        buzuq = kod[:-1] + ("1" if kod[-1] == "0" else "0")
        self.assertIsNone(rang_chekini_ochish(buzuq))       # qo'lda xato urilsa
        self.assertIsNone(rang_chekini_ochish("0000000012"))

    def test_tovar_va_tarozi_kodlari_ozgarmadi(self):
        self.assertEqual(topish(self.baza.kod).mahsulot, self.baza)
        self.assertEqual(topish(self.baza.qisqa_kod).mahsulot, self.baza)

    def test_kassa_chekni_taniydi(self):
        javob = self.kassa_kodi(self.chek.kod)
        self.assertTrue(javob["topildi"])
        self.assertEqual(javob["id"], self.baza.pk)
        self.assertEqual(javob["miqdor"], "2")
        self.assertEqual(javob["qanday"], "rang")
        self.assertEqual(javob["rang_chek"], self.chek.pk)

    def test_oddiy_tovarda_rang_cheki_yoq(self):
        self.assertEqual(self.kassa_kodi(self.baza.kod)["rang_chek"], "")

    def test_notanish_chek(self):
        javob = self.kassa_kodi(rang_cheki_kodi(999))
        self.assertFalse(javob["topildi"])
        self.assertIn("#999", javob["xato"])

    def test_chek_qoshiladi_va_boglanadi(self):
        javob = self.qosh()
        self.assertContains(javob, f"Rang cheki #{self.chek.pk}")
        self.assertContains(javob, "lanadi: 255 000 so")    # kassirga — «Jami» ga shuni yozadi
        self.chek.refresh_from_db()
        self.assertEqual(self.chek.sotuv, self.sotuv)
        self.assertEqual(self.chek.holat, Holat.KASSADA)
        self.baza.refresh_from_db()
        self.assertEqual(self.baza.qoldiq, Decimal("10"))      # savatda ombor o'zgarmaydi

    def test_kassa_qatorida_rang_kodi(self):
        """Kassir chek qatorida bu bo'yoq rang mashinasidan kelganini ko'radi."""
        self.qosh()
        javob = self.client.get(reverse("sotuv:tahrir", args=[self.sotuv.pk]))
        self.assertContains(javob, f"Rang cheki #{self.chek.pk}")
        self.assertContains(javob, ">RAL 3020</span>")

    def test_ikkinchi_marta_otmaydi(self):
        self.qosh()
        self.assertFalse(self.kassa_kodi(self.chek.kod)["topildi"])
        javob = self.qosh()
        self.assertContains(javob, "allaqachon")
        self.baza.refresh_from_db()
        self.assertEqual(self.baza.qoldiq, Decimal("10"))      # yakunlashgacha ayrilmaydi

    def test_yakunlansa_tolandi(self):
        self.qosh()
        self.client.post(reverse("sotuv:yakunlash", args=[self.sotuv.pk]), {"jami": "255 000"})
        self.chek.refresh_from_db()
        self.assertEqual(self.chek.holat, Holat.TOLANDI)
        self.assertIn("to'langan", topish(self.chek.kod).xato)

    def test_qator_ochirilsa_chek_boshaydi(self):
        self.qosh()
        qator = self.sotuv.qatorlar.get()
        self.client.post(reverse("sotuv:qator_ochirish", args=[qator.pk]))
        self.chek.refresh_from_db()
        self.assertIsNone(self.chek.sotuv)
        self.assertEqual(self.chek.holat, Holat.KUTILMOQDA)

    def test_sotuv_bekor_bolsa_chek_boshaydi(self):
        self.qosh()
        self.client.post(reverse("sotuv:bekor", args=[self.sotuv.pk]))
        self.chek.refresh_from_db()
        self.assertIsNone(self.chek.sotuv)
        self.assertIsNone(topish(self.chek.kod).xato)

    def test_bosh_sotuv_ochirilsa_chek_boshaydi(self):
        self.chek.sotuv = self.sotuv
        self.chek.save()
        self.sotuv.delete()
        self.chek.refresh_from_db()
        self.assertEqual(self.chek.holat, Holat.KUTILMOQDA)

    def test_boshqa_tovar_tanlansa_chek_boglanmaydi(self):
        _, boshqa = _rang_va_baza()
        self.qosh(mahsulot=boshqa.pk, miqdor="1")
        self.chek.refresh_from_db()
        self.assertIsNone(self.chek.sotuv)

    def test_qarzga_ham_otadi(self):
        hudud = Hudud.objects.create(nom="Hudud 1")
        qarzdor = Qarzdor.objects.create(ism="Vali", familiya="Aliyev", hudud=hudud)
        qarz = Qarz.objects.create(qarzdor=qarzdor)
        self.client.post(reverse("qarz:qator_qoshish", args=[qarz.pk]),
                         {"mahsulot": self.baza.pk, "miqdor": "2", "rang_chek": self.chek.pk})
        self.chek.refresh_from_db()
        self.assertEqual(self.chek.qarz, qarz)
        self.client.post(reverse("qarz:qarz_yakunlash", args=[qarz.pk]), {"jami": "255000"})
        self.chek.refresh_from_db()
        self.assertEqual(self.chek.holat, Holat.QARZGA)

    def test_bekor_qilingan_chek_kassada_otmaydi(self):
        self.chek.bekor_qilingan = True
        self.chek.save()
        javob = self.qosh()
        self.assertContains(javob, "bekor qilingan")
        self.assertFalse(self.sotuv.qatorlar.exists())

    def test_tolangan_chek_stansiyada_bekor_bolmaydi(self):
        self.qosh()
        self.client.post(reverse("sotuv:yakunlash", args=[self.sotuv.pk]), {"jami": "255000"})
        self.client.post(reverse("rang:bekor", args=[self.chek.pk]))
        self.chek.refresh_from_db()
        self.assertFalse(self.chek.bekor_qilingan)
