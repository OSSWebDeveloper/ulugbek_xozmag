from django.contrib import admin

from .models import Hudud, Qarz, QarzQator, Qarzdor, Tolov


@admin.register(Hudud)
class HududAdmin(admin.ModelAdmin):
    list_display = ("tartib", "nom")
    ordering = ("tartib",)


@admin.register(Qarzdor)
class QarzdorAdmin(admin.ModelAdmin):
    list_display = ("familiya", "ism", "telefon", "hudud")
    list_filter = ("hudud",)
    search_fields = ("ism", "familiya", "telefon")


class QarzQatorInline(admin.TabularInline):
    model = QarzQator
    extra = 0


@admin.register(Qarz)
class QarzAdmin(admin.ModelAdmin):
    list_display = ("id", "qarzdor", "sana", "yakunlangan")
    list_filter = ("yakunlangan",)
    inlines = [QarzQatorInline]


@admin.register(Tolov)
class TolovAdmin(admin.ModelAdmin):
    list_display = ("sana", "qarzdor", "summa", "izoh")
