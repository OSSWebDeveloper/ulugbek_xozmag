from decimal import Decimal
from unittest.mock import patch

from config.sinov import KirganTest
from config import rongta
from ombor.models import Mahsulot


class RongtaTests(KirganTest):
    def test_only_kg_sale_unit_and_sale_price_are_sent(self):
        Mahsulot.objects.create(nom='Dona', birlik='dona', narx=100)
        Mahsulot.objects.create(nom='Metr', birlik='metr', olish_birligi='kg', narx=100)
        m = Mahsulot.objects.create(nom="Mix 20 kg", birlik='kg', olish_birligi='pachka',
                                    olish_miqdori=20, narx=Decimal('32000'), kelish_narxi=2,
                                    kelish_valyutasi='dollar')
        rows, skipped = rongta.prepare()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['LFCode'], int(m.kod))
        self.assertEqual(rows[0]['UnitPrice'], 3200000)
        self.assertEqual(rows[0]['WeightUnit'], 4)
        self.assertEqual(rows[0]['BarCode'], 27)
        self.assertEqual(rows[0]['Deptment'], 2)
        self.assertEqual(skipped, [])

    def test_unpriced_expensive_and_inactive_are_not_sent(self):
        Mahsulot.objects.create(nom='Narxsiz', birlik='kg', narx=0)
        Mahsulot.objects.create(nom='Qimmat', birlik='kg', narx=1000000)
        Mahsulot.objects.create(nom='Yashirilgan', birlik='kg', narx=1, faol=False)
        rows, skipped = rongta.prepare()
        self.assertEqual(rows, [])
        self.assertEqual(len(skipped), 2)

    def test_sync_requires_post_and_authentication(self):
        self.assertEqual(self.client.get('/qurilmalar/tarozi/yukla/').status_code, 405)
        self.client.logout()
        self.assertEqual(self.client.post('/qurilmalar/tarozi/yukla/').status_code, 302)

    @patch.object(rongta, 'start_sync', return_value='job')
    def test_sync_starts_background_job(self, start):
        response = self.client.post('/qurilmalar/tarozi/yukla/')
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()['id'], 'job')
        start.assert_called_once()
