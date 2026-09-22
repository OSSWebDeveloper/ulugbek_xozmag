"""Narx qarz qatorlaridan olib tashlandi — qarz summasi qo'lda yoziladi.

Eski hujjatlarning summasi yo'qolmasin deb qator summalari `jami` ga ko'chiriladi.
"""
from decimal import Decimal

from django.db import migrations, models


def jamini_kochir(apps, schema_editor):
    Qarz = apps.get_model("qarz", "Qarz")
    for qarz in Qarz.objects.prefetch_related("qatorlar"):
        jami = sum((q.summa for q in qarz.qatorlar.all()), Decimal("0"))
        if jami:
            qarz.jami = jami
            qarz.save(update_fields=["jami"])


class Migration(migrations.Migration):

    dependencies = [("qarz", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="qarz",
            name="jami",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14,
                                      verbose_name="Jami"),
        ),
        migrations.RunPython(jamini_kochir, migrations.RunPython.noop),
        migrations.RemoveField(model_name="qarzqator", name="narx"),
        migrations.RemoveField(model_name="qarzqator", name="summa"),
    ]
