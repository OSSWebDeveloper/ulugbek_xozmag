"""Naqd sotuv manzillari."""
from django.urls import path

from . import views, hisobot
from . import chek_views

app_name = "sotuv"

urlpatterns = [
    path("hisobot/", hisobot.sahifa, name="hisobot"),
    path("chek-qidir/", chek_views.qaytarish_cheki, name="chek_izla"),
    path("chek/<int:pk>/", chek_views.korish, name="chek"),
    path("chek/<int:pk>/chop/", chek_views.chiqarish, name="chek_chop"),
    path("chek/<int:pk>/bosma/", chek_views.bosma, name="chek_bosma"),
    path("chek/<int:pk>/qaytarish/", chek_views.qaytarish_cheki, name="chek_qaytarish"),
    path("", views.royxat, name="royxat"),
    path("yangi/", views.sotuv_boshlash, name="boshlash"),
    path("<int:pk>/", views.tahrir, name="tahrir"),
    path("<int:pk>/qator/", views.qator_qoshish, name="qator_qoshish"),
    path("<int:pk>/yakun/", views.yakunlash, name="yakunlash"),
    path("<int:pk>/bekor/", views.bekor, name="bekor"),
    path("qator/<int:pk>/ochirish/", views.qator_ochirish, name="qator_ochirish"),
    path("qator/<int:pk>/miqdor/", views.qator_miqdor, name="qator_miqdor"),
    path("qator/<int:pk>/qaytarish/", views.qaytarish, name="qaytarish"),
]
