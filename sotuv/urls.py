"""Naqd sotuv manzillari."""
from django.urls import path

from . import views

app_name = "sotuv"

urlpatterns = [
    path("", views.royxat, name="royxat"),
    path("yangi/", views.sotuv_boshlash, name="boshlash"),
    path("<int:pk>/", views.tahrir, name="tahrir"),
    path("<int:pk>/qator/", views.qator_qoshish, name="qator_qoshish"),
    path("<int:pk>/yakun/", views.yakunlash, name="yakunlash"),
    path("<int:pk>/bekor/", views.bekor, name="bekor"),
    path("qator/<int:pk>/ochirish/", views.qator_ochirish, name="qator_ochirish"),
    path("qator/<int:pk>/qaytarish/", views.qaytarish, name="qaytarish"),
]
