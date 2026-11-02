"""Ombor manzillari."""
from django.urls import path

from . import excel_views, views

app_name = "ombor"

urlpatterns = [
    path("<int:pk>/shtrix/", views.shtrix_saqlash, name="shtrix_saqlash"),
    path("", views.royxat, name="royxat"),
    path("kod/", views.kod_qidir, name="kod_qidir"),
    path("tovar-qidir/", views.tovar_qidir, name="tovar_qidir"),
    path("yangi/", views.mahsulot_yangi, name="mahsulot_yangi"),
    path("<int:pk>/tahrir/", views.mahsulot_tahrir, name="mahsulot_tahrir"),
    path("<int:pk>/kirim/", views.kirim, name="kirim"),
    path("<int:pk>/qoldiq/", views.qoldiq_tuzatish, name="qoldiq_tuzatish"),
    path("<int:pk>/etiketka/", views.etiketka, name="etiketka"),
    path("<int:pk>/harakatlar/", views.harakatlar, name="harakatlar"),

    # Excel orqali yangilash (v3.0.0)
    path("excel/yuklab-olish/", excel_views.eksport, name="eksport"),
    path("excel/shablon/", excel_views.shablon, name="shablon"),
    path("excel/yuklash/", excel_views.yuklash, name="excel_yuklash"),
    path("yangilanishlar/", excel_views.yangilanishlar, name="yangilanishlar"),
    path("yangilanish/<int:pk>/", excel_views.yangilanish, name="yangilanish"),
    path("yangilanish/<int:pk>/amal/", excel_views.yangilanish_amal, name="yangilanish_amal"),
    path("qator/<int:pk>/", excel_views.qator_tahrir, name="qator"),
    path("qator/<int:pk>/chiqar/", excel_views.qator_chiqar, name="qator_chiqar"),
]
