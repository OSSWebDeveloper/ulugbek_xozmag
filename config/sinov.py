"""Testlar uchun umumiy asos.

Sayt butunlay login talab qiladi (`LoginRequiredMiddleware`), shuning uchun
sahifaga kiradigan har bir test avval xodim nomidan kirib oladi.
Kirishning o'zini sinaydigan testlar oddiy `TestCase` dan foydalanadi.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase


class KirganTest(TestCase):
    """Kirgan xodim nomidan ishlaydigan test."""

    LOGIN = "sinov"
    PAROL = "sinov-parol-123"

    def setUp(self):
        super().setUp()
        get_user_model().objects.create_user(username=self.LOGIN, password=self.PAROL)
        self.client.login(username=self.LOGIN, password=self.PAROL)
