"""Boshlang'ich ma'lumotlarni yuklaydi: 13 ta hudud va sinov tovarlari.

Ishlatish:  python manage.py boshlangich
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from ombor.models import Birlik, HarakatTuri, Mahsulot, OmborHarakati
from qarz.models import Hudud

# Haqiqiy nomlar ma'lum bo'lgach shu ro'yxat almashtiriladi.
HUDUDLAR = [f"Hudud {i}" for i in range(1, 14)]

TOVARLAR = [
    # (nom, sotuv birligi, narx, qoldiq, olish birligi, 1 olish birligida nechta)
    # Olish birligi bo'sh bo'lsa — tovar qanday olinsa shunday sotiladi.
    ("Sement 50 kg", Birlik.QOP, 55000, 120, Birlik.TONNA, 20),
    ("Gips 30 kg", Birlik.QOP, 42000, 60, "", 1),
    ("G'isht", Birlik.DONA, 1200, 5000, "", 1),
    ("Bo'yoq oq 5 l", Birlik.LITR, 38000, 40, "", 1),
    ("Kabel 2x2.5", Birlik.METR, 9500, 300, Birlik.ORAM, 100),
    ("Polietilen lenta 0,1 metr", Birlik.METR, 3500, 300, Birlik.RULON, 100),
    ("Mix 100 mm", Birlik.DONA, 150, 5020, Birlik.PACHKA, 1000),
    ("Plitka kley 25 kg", Birlik.QOP, 47000, 35, "", 1),
    ("Lampochka LED 12W", Birlik.DONA, 15000, 200, Birlik.QUTI, 20),
    ("Rozetka", Birlik.DONA, 12000, 150, "", 1),
    ("Truba PVX 50", Birlik.METR, 22000, 90, "", 1),
    ("Silikon germetik", Birlik.DONA, 25000, 48, Birlik.QUTI, 24),
    ("Qo'lqop", Birlik.DONA, 8000, 0, Birlik.PACHKA, 12),
]


class Command(BaseCommand):
    help = "13 ta hudud va sinov tovarlarini yuklaydi"

    def add_arguments(self, parser):
        parser.add_argument("--tovarsiz", action="store_true",
                            help="Faqat hududlarni yuklaydi")

    def handle(self, *args, **sozlama):
        yangi = 0
        for tartib, nom in enumerate(HUDUDLAR, start=1):
            _, yaratildi = Hudud.objects.get_or_create(nom=nom, defaults={"tartib": tartib})
            yangi += int(yaratildi)
        self.stdout.write(self.style.SUCCESS(f"Hududlar: {yangi} ta qo'shildi."))

        if sozlama["tovarsiz"]:
            return

        yangi = 0
        toldirilgan = 0
        for nom, birlik, narx, qoldiq, olish_birligi, olish_miqdori in TOVARLAR:
            mahsulot, yaratildi = Mahsulot.objects.get_or_create(
                nom=nom,
                defaults={
                    "birlik": birlik,
                    "narx": Decimal(narx),
                    "qoldiq": Decimal(qoldiq),
                    "olish_birligi": olish_birligi,
                    "olish_miqdori": Decimal(olish_miqdori),
                },
            )
            if yaratildi:
                yangi += 1
                if mahsulot.qoldiq:
                    OmborHarakati.objects.create(
                        mahsulot=mahsulot, tur=HarakatTuri.KIRIM,
                        miqdor=mahsulot.qoldiq, izoh="Boshlang'ich qoldiq",
                    )
            elif olish_birligi and not mahsulot.olish_birligi and mahsulot.birlik == birlik:
                # Eski sinov bazasiga olish birligini to'ldiradi.
                # Foydalanuvchi o'zi qo'ygan birlik hech qachon ustidan yozilmaydi.
                mahsulot.olish_birligi = olish_birligi
                mahsulot.olish_miqdori = Decimal(olish_miqdori)
                mahsulot.save(update_fields=["olish_birligi", "olish_miqdori"])
                toldirilgan += 1
        self.stdout.write(self.style.SUCCESS(f"Tovarlar: {yangi} ta qo'shildi."))
        if toldirilgan:
            self.stdout.write(self.style.SUCCESS(
                f"Olish birligi to'ldirildi: {toldirilgan} ta tovar."))
