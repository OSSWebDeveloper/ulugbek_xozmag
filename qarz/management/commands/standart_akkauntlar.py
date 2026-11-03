"""Birinchi o'rnatishda server va kassa hisoblarini yaratadi.

Mavjud akkauntning parolini yoki huquqini hech qachon o'zgartirmaydi.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Server va ikkinchi kassa uchun ilk akkauntlarni yaratadi (idempotent)"

    def handle(self, *args, **options):
        User = get_user_model()
        for login in ("server", "kassa"):
            user, created = User.objects.get_or_create(
                username=login,
                defaults={"is_active": True},
            )
            if created:
                user.set_password(login)
                user.save(update_fields=["password"])
                self.stdout.write(self.style.SUCCESS(
                    f"{login}: yangi hisob yaratildi. Kirishda parolni yangilang."
                ))
            else:
                self.stdout.write(f"{login}: mavjud hisob saqlandi, parol o'zgarmadi.")
