"""Ulug'bek Xozmak - asosiy manzillar."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("ombor/", include("ombor.urls")),
    path("", include("qarz.urls")),
]
