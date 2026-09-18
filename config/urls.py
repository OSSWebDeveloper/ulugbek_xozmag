"""Ulug'bek Xozmag - asosiy manzillar."""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("kirish/", auth_views.LoginView.as_view(
        template_name="kirish.html", redirect_authenticated_user=True), name="kirish"),
    path("chiqish/", auth_views.LogoutView.as_view(), name="chiqish"),
    path("admin/", admin.site.urls),
    path("ombor/", include("ombor.urls")),
    path("sotuv/", include("sotuv.urls")),
    path("", include("qarz.urls")),
]
