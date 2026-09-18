from django.contrib import admin

from .models import Mahsulot, OmborHarakati


@admin.register(Mahsulot)
class MahsulotAdmin(admin.ModelAdmin):
    list_display = ("nom", "birlik", "olish_birligi", "olish_miqdori", "narx", "qoldiq", "faol")
    list_filter = ("birlik", "olish_birligi", "faol")
    search_fields = ("nom",)


@admin.register(OmborHarakati)
class OmborHarakatiAdmin(admin.ModelAdmin):
    list_display = ("sana", "mahsulot", "tur", "miqdor", "kiritilgan_miqdor",
                    "kiritilgan_birlik", "izoh")
    list_filter = ("tur",)
    search_fields = ("mahsulot__nom", "izoh")
