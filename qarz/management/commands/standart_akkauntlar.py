"""Ilk o'rnatishda server va kassa foydalanuvchilarini bir marta yaratadi.

Markirovka auth.Group orqali ma'lumotlar bazasida saqlanadi: login/parol
o'zgargach yoki server qayta ishga tushgach standart hisob qayta yaratilmaydi.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

SERVER_GURUH = "BizaroPOS-boshlangich-server"
KASSA_GURUH = "BizaroPOS-boshlangich-kassa"


class Command(BaseCommand):
    help = "Birinchi ishga tushishda server/server va kassa/kassa akkauntlarini yaratadi"

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        for login, belgi in (("server", SERVER_GURUH), ("kassa", KASSA_GURUH)):
            group, new_group = Group.objects.get_or_create(name=belgi)
            if not new_group:
                self.stdout.write(f"{login}: avval sozlangan, login va parolga tegilmadi.")
                continue

            user, created = User.objects.get_or_create(
                username=login, defaults={"is_active": True},
            )
            if created:
                user.set_password(login)
                user.save(update_fields=["password"])
            group.user_set.add(user)
            self.stdout.write(self.style.SUCCESS(
                f"{login}: " + ("yaratildi" if created else "mavjud hisob saqlandi")
                + ". Ilk kirishda parolni almashtiring."
            ))
