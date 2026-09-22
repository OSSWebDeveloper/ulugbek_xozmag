from django.contrib import admin

from .models import DollarKursi, Mahsulot, OmborHarakati, ShtrixKod


class ShtrixKodInline(admin.TabularInline):
    """Tovarning zavod shtrixlari — kartochkaning o'zida qo'shiladi."""

    model = ShtrixKod
    extra = 1


@admin.register(Mahsulot)
class MahsulotAdmin(admin.ModelAdmin):
    list_display = ("kod", "nom", "birlik", "olish_birligi", "olish_miqdori",
                    "qoldiq", "faol")
    list_filter = ("birlik", "olish_birligi", "faol")
    search_fields = ("nom", "kod", "shtrixlar__kod")
    readonly_fields = ("kod",)     # id dan chiqadi, qo'lda o'zgartirilmaydi
    inlines = [ShtrixKodInline]


@admin.register(ShtrixKod)
class ShtrixKodAdmin(admin.ModelAdmin):
    list_display = ("kod", "mahsulot", "miqdor", "izoh")
    search_fields = ("kod", "mahsulot__nom")


@admin.register(OmborHarakati)
class OmborHarakatiAdmin(admin.ModelAdmin):
    list_display = ("sana", "mahsulot", "tur", "miqdor", "kiritilgan_miqdor",
                    "kiritilgan_birlik", "izoh")
    list_filter = ("tur",)
    search_fields = ("mahsulot__nom", "izoh")


@admin.register(DollarKursi)
class DollarKursiAdmin(admin.ModelAdmin):
    """Markaziy bankdan olingan kun kurslari — kerak bo'lsa qo'lda tuzatiladi."""

    list_display = ("sana", "kurs", "urinish")
