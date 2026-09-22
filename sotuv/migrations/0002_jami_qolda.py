"""Narx qatorlardan olib tashlandi — chek summasi qo'lda yoziladi.

Do'konda savdolashiladi: 183 000 so'mlik tovar 180 000 ga ketishi mumkin.
Shuning uchun summa hisoblanmaydi, kassir kalkulyatordagi sonni yozadi.
Eski cheklarning summasi yo'qolmasin deb qator summalari `jami` ga ko'chiriladi.
"""
from decimal import Decimal

from django.db import migrations, models


def jamini_kochir(apps, schema_editor):
    Sotuv = apps.get_model("sotuv", "Sotuv")
    for sotuv in Sotuv.objects.prefetch_related("qatorlar"):
        jami = sum((q.summa for q in sotuv.qatorlar.all()), Decimal("0"))
        if jami:
            sotuv.jami = jami
            sotuv.save(update_fields=["jami"])


class Migration(migrations.Migration):

    dependencies = [("sotuv", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="sotuv",
            name="jami",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14,
                                      verbose_name="Jami"),
        ),
        migrations.RunPython(jamini_kochir, migrations.RunPython.noop),
        migrations.RemoveField(model_name="sotuv", name="tolandi"),
        migrations.RemoveField(model_name="sotuvqator", name="narx"),
        migrations.RemoveField(model_name="sotuvqator", name="summa"),
    ]
