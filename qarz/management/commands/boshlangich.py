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
    # (nom, birlik, narx, qoldiq)
    ("Sement 50 kg", Birlik.QOP, 55000, 120),
    ("Gips 30 kg", Birlik.QOP, 42000, 60),
    ("G'isht", Birlik.DONA, 1200, 5000),
    ("Bo'yoq oq 5 l", Birlik.LITR, 38000, 40),
    ("Kabel 2x2.5", Birlik.METR, 9500, 300),
    ("Mix 100 mm", Birlik.KG, 18000, 75),
    ("Plitka kley 25 kg", Birlik.QOP, 47000, 35),
    ("Lampochka LED 12W", Birlik.DONA, 15000, 200),
    ("Rozetka", Birlik.DONA, 12000, 150),
    ("Truba PVX 50", Birlik.METR, 22000, 90),
    ("Silikon germetik", Birlik.DONA, 25000, 48),
    ("Qo'lqop", Birlik.DONA, 8000, 0),
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
        for nom, birlik, narx, qoldiq in TOVARLAR:
            mahsulot, yaratildi = Mahsulot.objects.get_or_create(
                nom=nom,
                defaults={"birlik": birlik, "narx": Decimal(narx), "qoldiq": Decimal(qoldiq)},
            )
            if yaratildi:
                yangi += 1
                if mahsulot.qoldiq:
                    OmborHarakati.objects.create(
                        mahsulot=mahsulot, tur=HarakatTuri.KIRIM,
                        miqdor=mahsulot.qoldiq, izoh="Boshlang'ich qoldiq",
                    )
        self.stdout.write(self.style.SUCCESS(f"Tovarlar: {yangi} ta qo'shildi."))
