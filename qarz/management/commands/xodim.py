"""Saytga kiradigan xodim hisobini yaratadi yoki parolini almashtiradi.

    python manage.py xodim reception                 parol login bilan bir xil
    python manage.py xodim reception --parol 1234    parolni o'zingiz berasiz
    python manage.py xodim boshliq --boshqaruvchi    admin panelga ham kiradi

Parol kodda yozilmagan — berilmasa login bilan bir xil qilib qo'yiladi.
Bu qulay, lekin kuchsiz: do'konga o'rnatilgach almashtirib qo'ying.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Saytga kiradigan xodim hisobini yaratadi yoki parolini almashtiradi"

    def add_arguments(self, parser):
        parser.add_argument("login", help="Kirish uchun nom, masalan reception")
        parser.add_argument("--parol", default=None,
                            help="Berilmasa login bilan bir xil bo'ladi")
        parser.add_argument("--boshqaruvchi", action="store_true",
                            help="Admin panelga ham kira olsin")

    def handle(self, *args, **sozlama):
        login = sozlama["login"].strip()
        if not login:
            raise CommandError("Login bo'sh bo'lmasin.")
        parol = sozlama["parol"] or login

        Foydalanuvchi = get_user_model()
        xodim, yaratildi = Foydalanuvchi.objects.get_or_create(username=login)
        xodim.set_password(parol)
        if sozlama["boshqaruvchi"]:
            xodim.is_staff = True
            xodim.is_superuser = True
        xodim.save()

        holat = "yaratildi" if yaratildi else "paroli almashtirildi"
        self.stdout.write(self.style.SUCCESS(f"«{login}» {holat}."))
        if parol == login:
            self.stdout.write(self.style.WARNING(
                "Parol login bilan bir xil — do'konga o'rnatilgach "
                f"`python manage.py xodim {login} --parol <yangi>` bilan almashtiring."
            ))
