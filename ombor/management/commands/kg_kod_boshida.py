"""One-time explicit renumbering, preserving stock, prices and scale barcodes."""
import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Case, IntegerField, Value, When
from ombor.models import Mahsulot, kod_yasa, KOD_MAX


class Command(BaseCommand):
    help = 'KG mahsulotlarni boshidan ketma-ket raqamlaydi; standart holatda faqat reja.'

    def add_arguments(self, parser):
        parser.add_argument('--qolla', action='store_true')
        parser.add_argument('--hisobot', required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        rows = list(Mahsulot.objects.select_for_update().annotate(
            kg_order=Case(When(birlik='kg', then=Value(0)), default=Value(1), output_field=IntegerField())
        ).order_by('kg_order', 'kod', 'pk'))
        if len(rows) > KOD_MAX:
            raise CommandError('4 xonali kodga sig‘maydi.')
        if any(not m.tarozi_kodi for m in rows):
            raise CommandError('Avval tarozi identifikatorlari migratsiyasini bajaring.')
        plan = [(m, m.kod, kod_yasa(i)) for i, m in enumerate(rows, 1)]
        report = Path(options['hisobot'])
        report.parent.mkdir(parents=True, exist_ok=True)
        with report.open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(['ID', 'Eski kod', 'Yangi kod', 'Tovar', 'Sotish birligi', 'Tarozi shtrix ID'])
            writer.writerows((m.pk, old, new, m.nom, m.birlik, m.tarozi_kodi) for m, old, new in plan)
        changed = [(m, old, new) for m, old, new in plan if old != new]
        kg = sum(m.birlik == 'kg' for m in rows)
        if options['qolla']:
            # Unique codes are exchanged through a disjoint temporary namespace.
            for m, old, new in changed:
                m.kod = f'~{m.pk}'
            Mahsulot.objects.bulk_update([m for m, _, _ in changed], ['kod'], batch_size=300)
            for m, old, new in changed:
                m.kod = new
            Mahsulot.objects.bulk_update([m for m, _, _ in changed], ['kod'], batch_size=300)
        self.stdout.write(f'{len(rows)} mahsulot; kg: {kg}; kod almashadi: {len(changed)}; '
                          + ('QO‘LLANDI' if options['qolla'] else 'Faqat reja, baza o‘zgarmadi'))
