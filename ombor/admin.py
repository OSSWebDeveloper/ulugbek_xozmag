from django.contrib import admin

from .models import Mahsulot, OmborHarakati


@admin.register(Mahsulot)
class MahsulotAdmin(admin.ModelAdmin):
    list_display = ("nom", "birlik", "narx", "qoldiq", "faol")
    list_filter = ("birlik", "faol")
    search_fields = ("nom",)


@admin.register(OmborHarakati)
class OmborHarakatiAdmin(admin.ModelAdmin):
    list_display = ("sana", "mahsulot", "tur", "miqdor", "izoh")
    list_filter = ("tur",)
    search_fields = ("mahsulot__nom", "izoh")
