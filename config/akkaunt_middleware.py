"""Standart zaif parol bilan dasturdan foydalanishga yo'l qo'ymaydi."""
from django.shortcuts import redirect
from django.urls import reverse
from .akkaunt import boshlangich_parol


class StandartParolMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and boshlangich_parol(request.user):
            allow = (reverse("akkaunt_sozlamalar"), reverse("chiqish"))
            if request.path not in allow and not request.path.startswith("/static/"):
                return redirect("akkaunt_sozlamalar")
        return self.get_response(request)
