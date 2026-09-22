"""Har bir tovarga kod beriladi va shtrix kodlar jadvali qo'shiladi.

Kod id dan chiqadi (`0000000001`), shuning uchun mavjud tovarlarga ham
o'sha zahoti beriladi — do'kon yangilangach hamma tovarning yorliq raqami
tayyor turadi.
"""
import django.db.models.deletion
from django.db import migrations, models


def kodlarni_ber(apps, schema_editor):
    """Bazadagi tovarlarga id bo'yicha kod yozadi."""
    Mahsulot = apps.get_model("ombor", "Mahsulot")
    for pk in Mahsulot.objects.filter(kod="").values_list("pk", flat=True):
        Mahsulot.objects.filter(pk=pk).update(kod=f"{pk:010d}")


def orqaga(apps, schema_editor):
    """Kodlar o'chiriladi — maydonning o'zi keyingi qadamda olib tashlanadi."""
    apps.get_model("ombor", "Mahsulot").objects.update(kod="")


class Migration(migrations.Migration):

    dependencies = [("ombor", "0009_markaziy_bank_kursi")]

    operations = [
        # Avval oddiy maydon: mavjud qatorlarda bo'sh bo'lgani uchun unique
        # bo'lolmaydi. Kodlar yozilgach unique qilinadi.
        migrations.AddField(
            model_name="mahsulot",
            name="kod",
            field=models.CharField(
                blank=True, db_index=True, default="", max_length=10,
                help_text="Tovar yaratilganda o'zi beriladi va hech qachon o'zgarmaydi.",
                verbose_name="Kod",
            ),
        ),
        migrations.RunPython(kodlarni_ber, orqaga),
        migrations.AlterField(
            model_name="mahsulot",
            name="kod",
            field=models.CharField(
                blank=True, db_index=True, max_length=10, unique=True,
                help_text="Tovar yaratilganda o'zi beriladi va hech qachon o'zgarmaydi.",
                verbose_name="Kod",
            ),
        ),
        migrations.CreateModel(
            name="ShtrixKod",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("kod", models.CharField(
                    db_index=True, max_length=32, unique=True,
                    error_messages={"unique": "Bu shtrix kod boshqa tovarga biriktirilgan."},
                    verbose_name="Shtrix kod")),
                ("miqdor", models.DecimalField(
                    decimal_places=3, default=1, max_digits=12,
                    help_text="Bir marta skanerlanganda nechta sotuv birligi. Quti kodi "
                              "bo'lsa qutidagi soni (masalan 1000).",
                    verbose_name="Bitta skan")),
                ("izoh", models.CharField(
                    blank=True, max_length=60,
                    help_text="Masalan «quti» yoki «eski partiya».", verbose_name="Izoh")),
                ("yaratilgan", models.DateTimeField(auto_now_add=True)),
                ("mahsulot", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="shtrixlar", to="ombor.mahsulot", verbose_name="Tovar")),
            ],
            options={
                "verbose_name": "Shtrix kod",
                "verbose_name_plural": "Shtrix kodlar",
                "ordering": ["mahsulot__nom", "kod"],
            },
        ),
    ]
