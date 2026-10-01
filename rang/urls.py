"""Rang (kolerovka) manzillari."""
from django.urls import path

from . import views

app_name = "rang"

urlpatterns = [
    path("", views.stansiya, name="stansiya"),
    path("kod/", views.kod_qidir, name="kod_qidir"),
    path("chek/<int:pk>/", views.chek, name="chek"),
    path("chek/<int:pk>/bekor/", views.bekor, name="bekor"),
    path("ranglar/", views.ranglar, name="ranglar"),
    path("ranglar/yangi/", views.rang_yangi, name="rang_yangi"),
    path("ranglar/yuklash/", views.yuklash, name="yuklash"),
    path("ranglar/toplam-ochirish/", views.toplam_ochirish, name="toplam_ochirish"),
    path("ranglar/<int:pk>/", views.rang_tahrir, name="rang_tahrir"),
    path("ranglar/<int:pk>/ochirish/", views.rang_ochirish, name="rang_ochirish"),
    path("varaq/", views.varaq, name="varaq"),
]
