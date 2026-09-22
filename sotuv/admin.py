from django.contrib import admin

from .models import Sotuv, SotuvQator


class SotuvQatorInline(admin.TabularInline):
    model = SotuvQator
    extra = 0


@admin.register(Sotuv)
class SotuvAdmin(admin.ModelAdmin):
    list_display = ("id", "sana", "jami", "yakunlangan")
    list_filter = ("yakunlangan",)
    inlines = [SotuvQatorInline]
