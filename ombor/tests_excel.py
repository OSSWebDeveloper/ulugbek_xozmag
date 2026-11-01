"""Omborni Excel orqali yangilash: o'qish, qoralama, qo'llash, bekor qilish (v3.0.0)."""
import io
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from openpyxl import Workbook, load_workbook

from config.sinov import KirganTest

from . import excel
from .models import (HarakatTuri, Mahsulot, OmborHarakati, OmborYangilanish, Valyuta,
                     YangilanishQatori as Qator)


def xlsx(satrlar, nom="ombor.xlsx"):
    wb = Workbook()
    ws = wb.active
    for s in satrlar:
        ws.append(s)
    buf = io.BytesIO()
    wb.save(buf)
    return SimpleUploadedFile(nom, buf.getvalue())


DOKON = ["Товар", "Остаток", "Sotish narxi", "Ko'cha fermachilar", "Diller narx",
         "internet zakaz", "Дата создания"]
SHABLON = ["Kod", "Tovar nomi", "Birlik", "Qoldiq", "Narxi", "Valyuta"]


class ExcelTest(KirganTest):
    def yukla(self, satrlar, **kw):
        return excel.fayldan_qoralama(xlsx(satrlar), **kw)

    def m(self, kod):
        return Mahsulot.objects.get(kod=kod)

    def test_dokon_fayli_kod_beriladi_valyuta_ajratiladi(self):
        y = self.yukla([DOKON,
                        ["Master tog'ora 25L", 68, "2.06 USD", "2.2 USD", "2.06 USD", None, "2026"],
                        ["Aaftamat 40A", None, "180726 UZS", "164296 UZS", None, None, "2024"],
                        ["Truba 50lik", 3, "3.5432 USD", "4 UZS", None, None, ""]])
        self.assertEqual(Mahsulot.objects.count(), 0)          # qoralama omborga tegmaydi
        self.assertEqual(y.sanoq()["yangi"], 3)
        excel.qollash(y)
        tog = self.m("0001")
        self.assertEqual((tog.nom, tog.qoldiq, tog.narx, tog.valyuta),
                         ("Master tog'ora 25L", Decimal("68"), Decimal("2.06"), Valyuta.DOLLAR))
        self.assertEqual((self.m("0002").valyuta, self.m("0002").qoldiq), (Valyuta.SOM, 0))
        self.assertEqual(self.m("0003").narx, Decimal("3.5432"))    # 4 xonali kasr saqlanadi
        # Boshlang'ich qoldiq tarixga kirim bo'lib yozildi
        self.assertEqual(OmborHarakati.objects.filter(tur=HarakatTuri.KIRIM).count(), 2)

    def test_qayta_yuklash_nom_boyicha_qoldiq_tuzatish_tarixda(self):
        excel.qollash(self.yukla([DOKON, ["A", 5, "10 USD"], ["B", 1, "100 UZS"]]))
        y = self.yukla([DOKON, ["A", 3, "10 USD"], ["B", 1, "100 UZS"], ["C", 2, "7 USD"]])
        s = y.sanoq()
        self.assertEqual((s["yangi"], s["ozgardi"], y.ozgarmagan), (1, 1, 1))
        excel.qollash(y)
        a = self.m("0001")
        self.assertEqual(a.qoldiq, 3)
        tuzatish = OmborHarakati.objects.get(mahsulot=a, tur=HarakatTuri.TUZATISH)
        self.assertEqual(tuzatish.miqdor, -2)
        self.assertEqual(self.m("0003").nom, "C")

    def test_faqat_kod_va_qoldiq_boshqasiga_tegmaydi(self):
        excel.qollash(self.yukla([SHABLON, ["0007", "Kran", "dona", 4, 15, "USD"]]))
        excel.qollash(self.yukla([["Kod", "Qoldiq"], [7, 9]]))
        k = self.m("0007")
        self.assertEqual((k.nom, k.qoldiq, k.narx, k.valyuta),
                         ("Kran", 9, 15, Valyuta.DOLLAR))

    def test_bekor_qilish_hammasini_qaytaradi(self):
        excel.qollash(self.yukla([SHABLON, ["0001", "A", "dona", 5, 10, "USD"],
                                  ["0002", "B", "kg", 1, 3, "UZS"]]))
        oldin = {m.kod: (m.nom, m.qoldiq, m.narx, m.valyuta, m.faol)
                 for m in Mahsulot.objects.all()}
        y = self.yukla([SHABLON, ["0001", "A2", "dona", 6, 11, "UZS"],
                        ["0009", "Yangi", "dona", 1, 1, "UZS"]], yoqlarini_yashir=True)
        self.assertEqual(y.sanoq()["yashirildi"], 1)               # B faylda yo'q
        excel.qollash(y)
        self.assertFalse(self.m("0002").faol)                     # o'chmaydi — yashiriladi
        excel.bekor_qil(y)
        self.assertEqual({m.kod: (m.nom, m.qoldiq, m.narx, m.valyuta, m.faol)
                          for m in Mahsulot.objects.all()}, oldin)
        y.refresh_from_db()
        self.assertEqual(y.holat, OmborYangilanish.BEKOR)

    def test_keyin_ozgargan_bolsa_bekor_qilinmaydi(self):
        y1 = self.yukla([SHABLON, ["0001", "A", "dona", 5, 10, "USD"]])
        excel.qollash(y1)
        y2 = self.yukla([SHABLON, ["0001", "A", "dona", 4, 10, "USD"]])
        excel.qollash(y2)
        self.assertEqual(excel.bekor_toqnashuvlari(y1)[0][2], y2)
        with self.assertRaises(excel.ExcelXatosi):
            excel.bekor_qil(y1)
        excel.bekor_qil(y2)                                        # avval keyingisi
        excel.bekor_qil(y1)
        self.assertEqual(Mahsulot.objects.count(), 0)

    def test_qoralamadan_keyingi_sotuv_yoqolmaydi(self):
        """Qoralama tuzilgach sotilgan bo'lsa, qo'llash faqat fayldagi o'zgarishni yozadi."""
        excel.qollash(self.yukla([SHABLON, ["0001", "A", "dona", 10, 5, "UZS"]]))
        y = self.yukla([["Kod", "Narxi"], ["0001", 6]])
        a = self.m("0001")
        a.qoldiq = 7                                               # oradagi sotuv
        a.save()
        excel.qollash(y)
        a.refresh_from_db()
        self.assertEqual((a.qoldiq, a.narx), (7, 6))

    def test_kod_almashinuvi_va_kochirish(self):
        excel.qollash(self.yukla([SHABLON, ["0001", "A", "dona", 1, 1, "UZS"],
                                  ["0002", "B", "dona", 1, 1, "UZS"]]))
        # Kod — joy: shu joydagi tovar nomlari almashadi
        excel.qollash(self.yukla([SHABLON, ["0001", "B", "dona", 1, 1, "UZS"],
                                  ["0002", "A", "dona", 1, 1, "UZS"]]))
        self.assertEqual(self.m("0001").nom, "B")
        # Nomi bo'yicha bo'sh kodga ko'chirish va qaytarish
        y = self.yukla([SHABLON, ["0050", "B", "dona", 1, 1, "UZS"]])
        excel.qollash(y)
        self.assertEqual(Mahsulot.objects.get(nom="B").kod, "0050")
        excel.bekor_qil(y)
        self.assertEqual(Mahsulot.objects.get(nom="B").kod, "0001")

    def test_xatolar_va_qatorni_tuzatish(self):
        y = self.yukla([SHABLON, ["123456", "Katta kod", "dona", 1, 1, "UZS"],
                        ["0003", "", "dona", 1, 1, "UZS"],
                        ["0004", "Narx", "dona", 1, "abc", "UZS"],
                        ["0005", "Valyuta", "dona", 1, 1, "EUR"],
                        ["0006", "Yaxshi", "dona", 1, 1, "USD"],
                        ["0006", "Takror", "dona", 1, 1, "USD"]])
        s = y.sanoq()
        self.assertEqual((s["yangi"], s["xato"]), (1, 5))
        q = y.qatorlar.get(excel_qator=2)
        holat, xato, ogoh = excel.qatorni_tekshir(
            {"kod": "12", "nom": "Katta kod", "birlik": "dona", "qoldiq": "1", "narx": "1",
             "valyuta": "UZS"})
        self.assertEqual(xato, "")
        self.assertIsNone(excel.qatorni_yangila(q, holat, ogoh))
        q.refresh_from_db()
        self.assertEqual((q.amal, q.kod), (Qator.YANGI, "0012"))
        holat["kod"] = "0006"                                     # band kod
        self.assertIn("0006", excel.qatorni_yangila(q, holat))
        excel.qollash(y)                                           # xatolar qo'llanmaydi
        self.assertEqual(set(Mahsulot.objects.values_list("kod", flat=True)), {"0006", "0012"})

    def test_eksport_kam_qolganlar_birinchi_va_qayta_import(self):
        excel.qollash(self.yukla([SHABLON, ["0001", "A", "metr", 2.5, 3.5432, "USD"],
                                  ["0002", "B", "dona", 0, 180726, "UZS"],
                                  ["0003", "C", "dona", 10, 5, "UZS"]]))
        baytlar = excel.excel_yoz(excel.tovarlar(kam_birinchi=True))
        ws = load_workbook(io.BytesIO(baytlar)).active
        self.assertEqual([r[0] for r in ws.iter_rows(min_row=2, max_row=4, values_only=True)],
                         ["0002", "0001", "0003"])               # kam qolgani birinchi
        y = excel.fayldan_qoralama(SimpleUploadedFile("q.xlsx", baytlar))
        s = y.sanoq()
        self.assertEqual((s["ozgardi"], s["yangi"], y.ozgarmagan), (0, 0, 3))

    def test_sahifalar(self):
        javob = self.client.post(reverse("ombor:excel_yuklash"),
                                 {"fayl": xlsx([SHABLON, ["0001", "A", "dona", 1, 2, "USD"]])})
        y = OmborYangilanish.objects.get()
        self.assertRedirects(javob, reverse("ombor:yangilanish", args=[y.pk]))
        for nom in ("ombor:royxat", "ombor:yangilanishlar", "ombor:excel_yuklash"):
            self.assertEqual(self.client.get(reverse(nom)).status_code, 200)
        self.assertContains(self.client.get(reverse("ombor:yangilanish", args=[y.pk])), "Qo'llash")
        q = y.qatorlar.get()
        self.assertEqual(self.client.get(reverse("ombor:qator", args=[q.pk])).status_code, 200)
        self.client.post(reverse("ombor:yangilanish_amal", args=[y.pk]), {"amal": "qollash"})
        self.assertEqual(Mahsulot.objects.get().kod, "0001")
        javob = self.client.get(reverse("ombor:royxat"), {"kam": "1"})
        self.assertContains(javob, "Kam qolganlar birinchi")
        javob = self.client.get(reverse("ombor:eksport"), {"kam": "1"})
        self.assertTrue(javob.content.startswith(b"PK"))
        self.assertTrue(self.client.get(reverse("ombor:shablon")).content.startswith(b"PK"))
        self.client.post(reverse("ombor:yangilanish_amal", args=[y.pk]), {"amal": "bekor"})
        self.assertEqual(Mahsulot.objects.count(), 0)

    def test_sahifalash(self):
        Mahsulot.objects.bulk_create([Mahsulot(nom=f"T{i}", kod=f"{i:05d}") for i in range(1, 121)])
        javob = self.client.get(reverse("ombor:royxat"), {"page": "3"})
        self.assertContains(javob, "3 / 3")
        self.assertContains(javob, "0101")
        self.assertNotContains(javob, "0050")


class TovarOynasiTest(KirganTest):
    """Kassadagi tovar oynasi: 60 ta karta, qolgani server qidiruvi orqali."""

    def setUp(self):
        super().setUp()
        Mahsulot.objects.bulk_create([Mahsulot(nom=f"Tovar {i:03d}", kod=f"{i:04d}",
                                               qoldiq=Decimal("5")) for i in range(1, 151)])

    def test_kassada_faqat_60_ta_karta(self):
        from .xizmat import OYNA_SONI
        javob = self.client.get(reverse("sotuv:boshlash"), follow=True)
        self.assertEqual(len(javob.context["mahsulotlar"]), OYNA_SONI)
        self.assertContains(javob, 'data-qidir-manzil="/ombor/tovar-qidir/"')

    def test_qidiruv_nom_va_kod(self):
        url = reverse("ombor:tovar_qidir")
        javob = self.client.get(url, {"q": "Tovar 14"}).json()     # so'zlar alohida izlanadi
        self.assertEqual(len(javob["tovarlar"]), 12)                 # 014, 114, 140-149
        self.assertEqual(javob["tovarlar"][0]["nom"], "Tovar 014")
        self.assertEqual(self.client.get(url, {"q": "137"}).json()["tovarlar"][0]["kod"], "0137")
        javob = self.client.get(url, {"q": "Tovar"}).json()
        self.assertEqual((len(javob["tovarlar"]), javob["yana"]), (30, True))
        self.assertEqual(self.client.get(url, {"q": ""}).json()["tovarlar"], [])
