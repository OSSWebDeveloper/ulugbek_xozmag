"""Ombor manzillari."""
from django.urls import path

from . import views

app_name = "ombor"

urlpatterns = [
    path("", views.royxat, name="royxat"),
    path("yangi/", views.mahsulot_yangi, name="mahsulot_yangi"),
    path("<int:pk>/tahrir/", views.mahsulot_tahrir, name="mahsulot_tahrir"),
    path("<int:pk>/kirim/", views.kirim, name="kirim"),
    path("<int:pk>/harakatlar/", views.harakatlar, name="harakatlar"),
]
