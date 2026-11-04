from unittest.mock import patch
from django.test import RequestFactory
from config.sinov import KirganTest
from config.kassalar import KassaForm
from django.urls import reverse

class KassaSettingsTests(KirganTest):
    def test_remote_cannot_change_network_or_download_other_cashier(self):
        self.assertEqual(self.client.get(reverse('kassalar'), REMOTE_ADDR='192.168.153.26').status_code,403)
        self.assertEqual(self.client.post(reverse('kassa_agent_yukla'), {'kassa2':'1'}, REMOTE_ADDR='192.168.153.26').status_code,403)
    def test_local_page_and_validation(self):
        self.assertContains(self.client.get(reverse('kassalar')), '2-kassa dasturi')
        self.assertTrue(KassaForm({'server_ip':'192.168.153.25','client_ip':'192.168.153.26','interface':13}).is_valid())
        for ip in ['192.168.153.257','192.168.153.25','192.168.1.26','192.168.153.255']:
            self.assertFalse(KassaForm({'server_ip':'192.168.153.25','client_ip':ip,'interface':13}).is_valid())

    def test_save_does_not_run_powershell_or_start_server(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from config import kassalar
        with TemporaryDirectory() as temp, patch.object(kassalar, 'path', return_value=Path(temp) / 'kassalar.json'), patch('subprocess.run', side_effect=AssertionError('PowerShell must not run')):
            response = self.client.post(reverse('kassalar'), {
                'server_ip': '192.168.153.25',
                'client_ip': '192.168.153.26',
                'interface': '13',
            })
            self.assertEqual(response.status_code, 302)
            self.assertTrue((Path(temp) / 'kassalar.json').exists())

    def test_display_actual_network_address(self):
        from config import kassalar
        with patch.object(kassalar, 'ip_manzillar', return_value=['192.168.1.21']), patch.object(kassalar, 'doimiy_manzil', return_value='http://192.168.1.21:5555'):
            self.assertContains(self.client.get(reverse('kassalar')), 'http://192.168.1.21:5555')
