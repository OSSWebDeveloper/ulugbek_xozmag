"""Zavod shtrixlari jadvali olib tashlanadi.

Do'konda har bir tovarga o'zimiz kod beramiz, etiketkasini chop etib
tovarga yopishtiramiz — kassa shu etiketkani skanerlaydi. Zavod shtrixini
tovarga biriktirish kerak emas.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("ombor", "0010_tovar_kodi_va_shtrix")]

    operations = [
        migrations.DeleteModel(name="ShtrixKod"),
    ]
