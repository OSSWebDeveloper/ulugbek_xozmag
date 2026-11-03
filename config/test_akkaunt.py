"""Birinchi o'rnatish va parolni almashtirish testlari."""
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse


class StandartHisobTest(TestCase):
    def test_idempotent_and_no_password_reset(self):
        call_command("standart_akkauntlar", verbosity=0)
        User = get_user_model()
        self.assertTrue(User.objects.get(username="server").check_password("server"))
        self.assertTrue(User.objects.get(username="kassa").check_password("kassa"))
        server = User.objects.get(username="server")
        server.set_password("AlreadyChangedSecure88!")
        server.save(update_fields=["password"])
        call_command("standart_akkauntlar", verbosity=0)
        self.assertTrue(User.objects.get(username="server").check_password("AlreadyChangedSecure88!"))

    def test_must_change_default_password_and_keep_session(self):
        call_command("standart_akkauntlar", verbosity=0)
        self.client.login(username="server", password="server")
        first = self.client.get(reverse("sotuv:boshlash"))
        self.assertRedirects(first, reverse("akkaunt_sozlamalar"), fetch_redirect_response=False)
        response = self.client.post(reverse("akkaunt_sozlamalar"), {
            "username": "server_new", "old_password": "server",
            "new_password1": "UniqueSecurePassword987!",
            "new_password2": "UniqueSecurePassword987!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.get(username="server_new").check_password("UniqueSecurePassword987!"))
        self.assertNotEqual(self.client.get(reverse("akkaunt_sozlamalar")).status_code, 302)
        # Server qayta ishga tushganda eski zaif login/parol qayta yaratilmasin.
        call_command("standart_akkauntlar", verbosity=0)
        self.assertFalse(get_user_model().objects.filter(username="server").exists())
        self.assertEqual(get_user_model().objects.filter(username="server_new").count(), 1)

    def test_cannot_reuse_default(self):
        call_command("standart_akkauntlar", verbosity=0)
        self.client.login(username="kassa", password="kassa")
        response = self.client.post(reverse("akkaunt_sozlamalar"), {
            "username": "kassa", "old_password": "kassa",
            "new_password1": "kassa", "new_password2": "kassa",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Standart login/paroldan foydalanmang.")
