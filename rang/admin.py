from django.contrib import admin

from .models import Buyurtma, Rang


@admin.register(Rang)
class RangAdmin(admin.ModelAdmin):
    list_display = ("kod", "nom", "hex", "toplam", "tartib", "faol")
    list_filter = ("toplam", "faol")
    search_fields = ("kod", "nom")


@admin.register(Buyurtma)
class BuyurtmaAdmin(admin.ModelAdmin):
    list_display = ("id", "sana", "rang_kodi", "baza_nomi", "miqdor", "rang_narxi",
                    "sotuv", "qarz", "bekor_qilingan")
    list_filter = ("bekor_qilingan",)
    search_fields = ("rang_kodi", "baza_nomi")
    raw_id_fields = ("rang", "baza", "sotuv", "qarz")
