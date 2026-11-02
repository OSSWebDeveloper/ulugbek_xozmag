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
