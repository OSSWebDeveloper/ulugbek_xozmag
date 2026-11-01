"""Ulug'bek Xozmag - asosiy manzillar."""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from . import qurilmalar
from . import rongta
from . import kassa_agent
from . import etiketka_print

urlpatterns = [
    path('qurilmalar/etiketka/printerlar/', etiketka_print.royxat, name='etiketka_printerlar'),
    path('ombor/<int:pk>/etiketka/chop/', etiketka_print.chop, name='etiketka_chop'),
    path('qurilmalar/etiketka/holat/<uuid:token>/', etiketka_print.holat, name='etiketka_chop_holat'),
    path('qurilmalar/kassa-agent/yukla/', kassa_agent.paket, name='kassa_agent_yukla'),
    path('qurilmalar/kassa-agent/almashish/', kassa_agent.almashish, name='kassa_agent_almashish'),
    path("qurilmalar/", qurilmalar.sahifa, name="qurilmalar"),
    path("qurilmalar/royxat/", qurilmalar.royxat, name="qurilmalar_royxat"),
    path("qurilmalar/tarozi/", rongta.status, name="tarozi_status"),
    path("qurilmalar/tarozi/yukla/", rongta.sync, name="tarozi_sync"),
    path("qurilmalar/tarozi/holat/<uuid:token>/", rongta.progress, name="tarozi_progress"),
    path("kirish/", auth_views.LoginView.as_view(
        template_name="kirish.html", redirect_authenticated_user=True), name="kirish"),
    path("chiqish/", auth_views.LogoutView.as_view(), name="chiqish"),
    path("admin/", admin.site.urls),
    path("ombor/", include("ombor.urls")),
    path("sotuv/", include("sotuv.urls")),
    path("rang/", include("rang.urls")),
    path("", include("qarz.urls")),
]
