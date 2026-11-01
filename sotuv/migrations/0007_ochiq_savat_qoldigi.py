from decimal import Decimal
from django.conf import settings
from django.db import migrations
from django.db.models import F


def savatlarni_tikla(apps, schema_editor):
    Product = apps.get_model('ombor', 'Mahsulot')
    Move = apps.get_model('ombor', 'OmborHarakati')
    app, name = settings.AUTH_USER_MODEL.split('.')
    owner = apps.get_model(app, name).objects.order_by('pk').first()
    for label, name, filters in [('sotuv', 'Sotuv', {'yakunlangan': False, 'bekor_qilingan': False}),
                                  ('qarz', 'Qarz', {'yakunlangan': False})]:
        Document = apps.get_model(label, name)
        if owner:
            Document.objects.filter(kassir__isnull=True).update(kassir_id=owner.pk)
        for doc in Document.objects.filter(**filters):
            for row in doc.qatorlar.all():
                qty = row.miqdor - row.qaytarilgan
                if qty > Decimal(0):
                    Product.objects.filter(pk=row.mahsulot_id).update(qoldiq=F('qoldiq') + qty)
                    Move.objects.create(mahsulot_id=row.mahsulot_id, tur='kirim', miqdor=qty,
                        izoh=f'{name} #{doc.pk}: ochiq savat qoldig‘i tiklandi; endi faqat yakunlashda ayiriladi')


class Migration(migrations.Migration):
    dependencies = [('sotuv', '0006_sotuv_kassir'), ('qarz', '0007_qarz_kassir')]
    operations = [migrations.RunPython(savatlarni_tikla)]
