"""Qarz daftari manzillari."""
from django.urls import path

from . import views

app_name = "qarz"

urlpatterns = [
    path("", views.boshlash, name="boshlash"),
    path("qidirish/", views.qidirish, name="qidirish"),
    path("yangi/", views.yangi_qarzdor, name="yangi_qarzdor"),
    path("qarzdorlar/", views.qarzdorlar_royxati, name="qarzdorlar"),
    path("qarzdor/<int:pk>/", views.qarzdor_karta, name="qarzdor_karta"),
    path("qarzdor/<int:pk>/tahrir/", views.qarzdor_tahrir, name="qarzdor_tahrir"),
    path("qarzdor/<int:qarzdor_pk>/qarz/", views.qarz_boshlash, name="qarz_boshlash"),
    path("qarzdor/<int:qarzdor_pk>/tolov/", views.tolov_qoshish, name="tolov_qoshish"),
    path("tolov/<int:pk>/ochirish/", views.tolov_ochirish, name="tolov_ochirish"),
    path("qarz/<int:pk>/", views.qarz_tahrir, name="qarz_tahrir"),
    path("qarz/<int:pk>/qator/", views.qator_qoshish, name="qator_qoshish"),
    path("qarz/<int:pk>/yakun/", views.qarz_yakunlash, name="qarz_yakunlash"),
    path("qator/<int:pk>/ochirish/", views.qator_ochirish, name="qator_ochirish"),
]
