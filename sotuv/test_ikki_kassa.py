import io
import json
import zipfile
from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import Client, override_settings
from django.urls import reverse
from config.sinov import KirganTest
from config.kassa_agent import digest
from ombor.models import Mahsulot, OmborHarakati
from .models import Sotuv, SotuvQator, KassaTerminal, ChekVazifa


class IkkiKassaTests(KirganTest):
    def setUp(self):
        super().setUp()
        self.one = get_user_model().objects.get(username=self.LOGIN)
        self.two = get_user_model().objects.create_user(username='kassa2', password='test-password')
        self.other = Client()
        self.other.force_login(self.two)
        self.product = Mahsulot.objects.create(nom='Lampochka', kod='0001', qoldiq=10, narx=10000)

    def cart(self, client):
        response = client.get(reverse('sotuv:boshlash'))
        return Sotuv.objects.get(pk=response.url.strip('/').split('/')[-1])

    def add(self, client, sale, qty, product=None):
        return client.post(reverse('sotuv:qator_qoshish', args=[sale.pk]), {
            'mahsulot': (product or self.product).pk, 'miqdor': qty})

    def finish(self, client, sale):
        return client.post(reverse('sotuv:yakunlash', args=[sale.pk]), {'jami': 100000})

    def test_carts_and_edit_permissions_are_separate(self):
        first, second = self.cart(self.client), self.cart(self.other)
        self.assertNotEqual(first.pk, second.pk)
        self.assertEqual(self.cart(self.client).pk, first.pk)
        self.add(self.client, first, 2)
        row = first.qatorlar.get()
        for name, pk, post in [('qator_qoshish', first.pk, {'mahsulot': self.product.pk, 'miqdor': 1}),
                               ('qator_ochirish', row.pk, {}),
                               ('qator_miqdor', row.pk, {'miqdor': 5, 'eski_miqdor': 2}),
                               ('yakunlash', first.pk, {'jami': 20000}), ('bekor', first.pk, {})]:
            self.assertEqual(self.other.post(reverse('sotuv:' + name, args=[pk]), post).status_code, 404)
        self.assertEqual(self.other.get(reverse('sotuv:tahrir', args=[first.pk])).status_code, 404)
        self.assertFalse(second.qatorlar.exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.qoldiq, 10)

    @override_settings(CHEK_AUTO_PRINT=True)
    @patch('sotuv.chek.chop_et')
    def test_only_finalization_deducts_and_prints_once(self, printer):
        sale = self.cart(self.client)
        self.add(self.client, sale, 2)
        row = sale.qatorlar.get()
        self.client.post(reverse('sotuv:qator_miqdor', args=[row.pk]), {
            'amal': 'kopaytirish', 'miqdor': '3', 'eski_miqdor': '2'})
        self.product.refresh_from_db()
        self.assertEqual(self.product.qoldiq, 10)
        self.assertFalse(OmborHarakati.objects.exists())
        printer.assert_not_called()
        self.finish(self.client, sale)
        self.finish(self.client, sale)
        self.product.refresh_from_db()
        self.assertEqual(self.product.qoldiq, 4)
        self.assertEqual(OmborHarakati.objects.count(), 1)
        printer.assert_called_once()

    @override_settings(CHEK_AUTO_PRINT=True)
    @patch('sotuv.chek.chop_et')
    def test_last_item_cannot_be_sold_by_both_cashiers(self, printer):
        first, second = self.cart(self.client), self.cart(self.other)
        self.add(self.client, first, 10)
        self.add(self.other, second, 10)
        self.finish(self.client, first)
        self.finish(self.other, second)
        second.refresh_from_db(); self.product.refresh_from_db()
        self.assertFalse(second.yakunlangan)
        self.assertEqual(self.product.qoldiq, 0)
        self.assertEqual(second.qatorlar.get().miqdor, 10)
        self.assertEqual(OmborHarakati.objects.count(), 1)
        printer.assert_called_once()

    def test_one_short_product_rolls_back_all_stock_and_debt(self):
        first, second = self.cart(self.client), self.cart(self.other)
        other = Mahsulot.objects.create(nom='Boshqa', kod='0002', qoldiq=1)
        self.add(self.client, first, 5)
        self.add(self.client, first, 1, other)
        self.add(self.other, second, 1, other)
        self.finish(self.other, second)
        self.finish(self.client, first)
        first.refresh_from_db(); self.product.refresh_from_db(); other.refresh_from_db()
        self.assertFalse(first.yakunlangan)
        self.assertEqual(self.product.qoldiq, 10)
        self.assertEqual(other.qoldiq, 0)
        self.assertEqual(OmborHarakati.objects.count(), 1)

    def test_cancelling_or_removing_cart_does_not_add_stock(self):
        sale = self.cart(self.client)
        self.add(self.client, sale, 2)
        self.client.post(reverse('sotuv:qator_ochirish', args=[sale.qatorlar.get().pk]))
        self.add(self.client, sale, 3)
        self.client.post(reverse('sotuv:bekor', args=[sale.pk]))
        self.product.refresh_from_db()
        self.assertEqual(self.product.qoldiq, 10)
        self.assertFalse(OmborHarakati.objects.exists())

    def test_open_debt_cart_cannot_be_returned_into_stock(self):
        from qarz.models import Qarz, QarzQator, Qarzdor, Hudud
        customer = Qarzdor.objects.create(ism='Sinov', hudud=Hudud.objects.create(nom='Sinov'))
        debt = Qarz.objects.create(kassir=self.one, qarzdor=customer)
        row = QarzQator.objects.create(qarz=debt, mahsulot=self.product, miqdor=2)
        self.client.post(reverse('qarz:qator_qaytarish', args=[row.pk]), {'miqdor':1, 'summa':0})
        self.product.refresh_from_db(); row.refresh_from_db()
        self.assertEqual(self.product.qoldiq, 10)
        self.assertEqual(row.qaytarilgan, 0)
        self.assertFalse(OmborHarakati.objects.exists())

    def test_both_cashiers_read_same_scale_label(self):
        self.product.kod = '0098'; self.product.birlik = 'kg'; self.product.save()
        for client in (self.client, self.other):
            data = client.get(reverse('ombor:kod_qidir'), {'k': '2000098004452'}).json()
            self.assertTrue(data['topildi'])
            self.assertEqual(data['id'], self.product.pk)


class UsbAgentTests(KirganTest):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.get(username=self.LOGIN)
        self.token = 'a' * 64
        self.terminal = KassaTerminal.objects.create(kassir=self.user, kalit_hash=digest(self.token))
        self.url = reverse('kassa_agent_almashish')
        self.unsigned = Client(enforce_csrf_checks=True)

    def poll(self, **data):
        return self.unsigned.post(self.url, json.dumps({'nom': 'KASSA2', 'printer': 'USB POS',
            'tayyor': True, **data}), content_type='application/json',
            HTTP_AUTHORIZATION='Bearer ' + self.token)

    @override_settings(CHEK_AUTO_PRINT=True)
    @patch('sotuv.chek.chop_et')
    def test_remote_sale_queues_only_its_own_printer_and_never_server_printer(self, printer):
        product = Mahsulot.objects.create(nom='Lampochka', qoldiq=10)
        sale = Sotuv.objects.create(kassir=self.user)
        self.client.post(reverse('sotuv:qator_qoshish', args=[sale.pk]), {'mahsulot':product.pk, 'miqdor':2})
        self.assertFalse(ChekVazifa.objects.exists())
        for _ in range(2):
            self.client.post(reverse('sotuv:yakunlash', args=[sale.pk]), {'jami':20000}, REMOTE_ADDR='192.168.100.41')
        self.assertEqual(ChekVazifa.objects.count(), 1)
        printer.assert_not_called()
        data = self.poll().json()['vazifa']
        self.assertEqual(data['data']['barcode'][:2], '88')
        self.assertIsNone(self.poll().json()['vazifa'])
        # Acknowledgement can be retried, but the physical job is not repeated.
        ack = {'id':data['id'], 'claim':data['claim'], 'ok':True}
        self.poll(ack=ack); self.poll(ack=ack)
        self.assertEqual(ChekVazifa.objects.get().holat, 'tayyor')

    def test_invalid_or_other_account_token_cannot_claim_jobs(self):
        self.assertEqual(self.unsigned.post(self.url, '{}', content_type='application/json').status_code, 401)
        self.assertEqual(self.unsigned.post(self.url, '{}', content_type='application/json',
            HTTP_AUTHORIZATION='Bearer ' + 'b'*64).status_code, 401)
        other = get_user_model().objects.create_user(username='other')
        second = KassaTerminal.objects.create(kassir=other, kalit_hash=digest('b'*64))
        sale = Sotuv.objects.create(kassir=other, yakunlangan=True)
        job = ChekVazifa.objects.create(sotuv=sale, terminal=second, holat='yuborildi', claim='secret')
        self.assertIsNone(self.poll().json()['vazifa'])
        self.assertEqual(self.poll(ack={'id':job.pk, 'claim':'secret', 'ok':True}).status_code, 404)
        job.refresh_from_db(); self.assertEqual(job.holat, 'yuborildi')

    def test_device_list_is_from_cashier_not_server(self):
        device = {'id':'usb1', 'nom':'USB scanner', 'tur':'Shtrix kod skaneri'}
        self.poll(qurilmalar=[device])
        response = self.client.get(reverse('qurilmalar_royxat'))
        self.assertEqual(response.json()['qurilmalar'], [device])

    @patch('sotuv.chek.chop_et')
    def test_unconfigured_helper_does_not_block_local_main_printer(self, printer):
        from sotuv.chek import yubor
        from django.test import RequestFactory
        from django.contrib.messages.storage.fallback import FallbackStorage
        sale = Sotuv.objects.create(kassir=self.user, yakunlangan=True)
        job = ChekVazifa.objects.create(sotuv=sale, terminal=self.terminal)
        request = RequestFactory().post('/print/')
        request.user = self.user; request.session = {}
        request._messages = FallbackStorage(request)
        yubor(request, sale)
        printer.assert_called_once_with(sale)
        job.refresh_from_db(); self.assertEqual(job.holat, 'tayyor')
        # The stale agent cannot claim a directly printed job later.
        self.assertIsNone(self.poll().json()['vazifa'])

    @patch('config.kassa_agent.Path.exists', return_value=True)
    @patch('config.kassa_agent.zipfile.ZipFile.write')
    def test_package_has_no_database_and_requires_authenticated_post(self, write, exists):
        # Zip writes are mocked to avoid reading the full runtime in every test.
        response = self.client.post(reverse('kassa_agent_yukla'))
        self.assertEqual(response.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(response.content)) as package:
            config = json.loads(package.read('kassa.json'))
            self.assertEqual(config['kassir'], self.LOGIN)
            self.assertNotIn('db.sqlite3', package.namelist())
            self.assertIn('local_devices.py', package.namelist())
        self.terminal.refresh_from_db()
        self.assertEqual(self.terminal.kalit_hash, digest(config['token']))
        self.assertEqual(self.poll().status_code, 401)
        self.assertEqual(self.client.get(reverse('kassa_agent_yukla')).status_code, 405)
