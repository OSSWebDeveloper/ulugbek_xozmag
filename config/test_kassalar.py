import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from config.sinov import KirganTest
from config import kassalar
from config.kassalar import KassaForm, holat
from django.urls import reverse

DHCP = {'mac': '80-30-49-BD-17-47', 'dhcp': True, 'router': '192.168.1.1'}


class KassaSettingsTests(KirganTest):
    def ochish(self, saved, live, info=DHCP):
        with patch.object(kassalar, 'config', return_value={'server_ip': saved}), \
             patch.object(kassalar, 'ip_manzillar', return_value=live), \
             patch.object(kassalar, 'karta', return_value=info), \
             patch.object(kassalar, 'doimiy_manzil', return_value=f'http://{live[0]}:5555' if live else ''):
            return self.client.get(reverse('kassalar'))

    def test_remote_cannot_change_network_or_download_other_cashier(self):
        self.assertEqual(self.client.get(reverse('kassalar'), REMOTE_ADDR='192.168.153.26').status_code,403)
        self.assertEqual(self.client.post(reverse('kassa_agent_yukla'), {'kassa2':'1'}, REMOTE_ADDR='192.168.153.26').status_code,403)

    def test_tunnel_request_is_not_local(self):
        # ngrok so'rovi 127.0.0.1 dan keladi, lekin server kompyuteri hisoblanmaydi
        for sarlavha in ({'HTTP_X_FORWARDED_FOR': '203.0.113.5'}, {'HTTP_HOST': 'misol.ngrok-free.app'}, {'HTTP_HOST': 'misol.ngrok-free.app:443'}):
            self.assertEqual(self.client.get(reverse('kassalar'), **sarlavha).status_code, 403)
            self.assertEqual(self.client.post(reverse('kassa_agent_yukla'), {'kassa2':'1'}, **sarlavha).status_code, 403)

    def test_validation(self):
        self.assertTrue(KassaForm({'server_ip': '192.168.1.21'}).is_valid())
        for ip in ['192.168.1.257', '192.168.1.0', '192.168.1.255', '8.8.8.8', '127.0.0.1', '169.254.3.4']:
            self.assertFalse(KassaForm({'server_ip': ip}).is_valid(), ip)

    def test_save_only_writes_config(self):
        with TemporaryDirectory() as temp, patch.object(kassalar, 'path', return_value=Path(temp) / 'kassalar.json'), \
             patch('subprocess.run', side_effect=AssertionError('PowerShell must not run')):
            response = self.client.post(reverse('kassalar'), {'server_ip': '192.168.1.21'})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(json.loads((Path(temp) / 'kassalar.json').read_text()), {'server_ip': '192.168.1.21'})

    def test_old_static_config_is_read(self):
        # Eski fayldagi client_ip va interface e'tiborga olinmaydi.
        with TemporaryDirectory() as temp, patch.object(kassalar, 'path', return_value=Path(temp) / 'kassalar.json'):
            self.assertEqual(kassalar.config(), {'server_ip': ''})
            (Path(temp) / 'kassalar.json').write_text('{"server_ip":"192.168.153.25","client_ip":"192.168.153.26","interface":13}')
            self.assertEqual(kassalar.config(), {'server_ip': '192.168.153.25'})

    def test_reservation_states(self):
        self.assertEqual(holat('', [], {})[0], 'yoq')
        self.assertEqual(holat('192.168.1.21', ['192.168.1.21'], {**DHCP, 'dhcp': False})[0], 'qolda')
        self.assertEqual(holat('', ['192.168.1.21'], DHCP)[0], 'belgilanmagan')
        self.assertEqual(holat('192.168.1.21', ['192.168.1.37'], DHCP)[0], 'farq')
        self.assertEqual(holat('192.168.1.21', ['192.168.1.21'], DHCP)[0], 'tayyor')
        # Karta aniqlanmasa ham IP mosligi tekshiriladi.
        self.assertEqual(holat('192.168.1.21', ['192.168.1.21'], {})[0], 'tayyor')

    def test_page_shows_router_data(self):
        page = self.ochish('', ['192.168.1.21'])
        for matn in ('80-30-49-BD-17-47', 'http://192.168.1.1/', 'http://192.168.1.21:5555', 'data-holat="belgilanmagan"', 'value="192.168.1.21"'):
            self.assertContains(page, matn)
        self.assertContains(self.ochish('192.168.1.21', ['192.168.1.21']), 'data-holat="tayyor"')
        self.assertContains(self.ochish('192.168.1.21', ['192.168.1.37']), 'data-holat="farq"')
        self.assertContains(self.ochish('192.168.1.21', []), 'data-holat="yoq"')

    def test_package_has_no_static_ip_setup(self):
        import io, zipfile
        from django.contrib.auth.models import Group
        from django.contrib.auth import get_user_model
        from qarz.management.commands.standart_akkauntlar import KASSA_GURUH
        kassir = get_user_model().objects.create_user(username='kassa2', password='x')
        kassir.groups.add(Group.objects.get_or_create(name=KASSA_GURUH)[0])
        with TemporaryDirectory() as temp, self.settings(MALUMOT_DIR=temp), \
             patch('config.tarmoq.ip_manzillar', return_value=['192.168.1.21']):
            response = self.client.post(reverse('kassa_agent_yukla'), {'kassa2': '1'})
        if response.status_code == 503:
            self.skipTest('kassa runtime fayli yo‘q')
        archive = zipfile.ZipFile(io.BytesIO(response.content))
        self.assertNotIn('kassa_ip.ps1', archive.namelist())
        data = json.loads(archive.read('kassa.json'))
        self.assertNotIn('client_ip', data)
        self.assertEqual(data['url'], 'http://192.168.1.21:80')
