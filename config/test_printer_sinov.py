import json
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from config.sinov import KirganTest
from config.kassa_agent import digest
from sotuv.models import KassaTerminal, ChekVazifa, Sotuv
from ombor.models import OmborHarakati


class PrinterSinovTests(KirganTest):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.get(username=self.LOGIN)
        self.token = 'a' * 64
        self.terminal = KassaTerminal.objects.create(kassir=self.user,
            kalit_hash=digest(self.token), printer='USB2', oxirgi_aloqa=timezone.now())
        self.url = reverse('printer_sinov')

    def test_remote_test_and_ack_without_sale_or_stock_changes(self):
        response = self.client.post(self.url, REMOTE_ADDR='192.168.100.41')
        self.assertEqual(response.status_code, 202)
        job = ChekVazifa.objects.get()
        self.assertIsNone(job.sotuv_id)
        self.assertEqual(job.terminal, self.terminal)
        self.assertTrue(job.malumot['test'])
        self.assertEqual(job.malumot['barcode'], '')
        agent = Client()
        poll_url = reverse('kassa_agent_almashish')
        kwargs = dict(content_type='application/json', HTTP_AUTHORIZATION='Bearer ' + self.token)
        result = agent.post(poll_url, json.dumps({'printer':'USB2','tayyor':True}), **kwargs).json()
        claim = result['vazifa']['claim']
        agent.post(poll_url, json.dumps({'printer':'USB2', 'ack':{
            'id':job.pk,'claim':claim,'ok':True}}), **kwargs)
        self.assertEqual(self.client.get(response.json()['url']).json()['holat'], 'tayyor')
        self.assertFalse(Sotuv.objects.exists())
        self.assertFalse(OmborHarakati.objects.exists())

    def test_repeat_pending_test_is_not_duplicated(self):
        for _ in range(2):
            self.client.post(self.url, REMOTE_ADDR='192.168.100.41')
        self.assertEqual(ChekVazifa.objects.count(), 1)

    @patch('config.printer_sinov.chop_malumot')
    def test_remote_offline_never_prints_on_server(self, printer):
        self.terminal.oxirgi_aloqa = None
        self.terminal.save()
        # Yordamchisiz qurilma sinov chekini o'z brauzeridan chiqaradi.
        response = self.client.post(self.url, REMOTE_ADDR='192.168.100.41')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['bosma'], reverse('printer_sinov_bosma'))
        printer.assert_not_called()
        self.assertFalse(ChekVazifa.objects.exists())
        page = self.client.get(response.json()['bosma'], REMOTE_ADDR='192.168.100.41')
        self.assertContains(page, 'PRINTER SINOVI')
        self.assertContains(page, 'savdo_chek_bosma.js')
        self.assertNotContains(page, 'savdo-chek-shtrix')
        self.assertEqual(page['X-Frame-Options'], 'SAMEORIGIN')

    @patch('config.printer_sinov.chop_malumot')
    def test_local_without_helper_uses_main_printer(self, printer):
        self.terminal.oxirgi_aloqa = None
        self.terminal.save()
        self.assertEqual(self.client.post(self.url).status_code,200)
        printer.assert_called_once()
        self.assertTrue(printer.call_args.args[0]['test'])

    def test_status_is_account_scoped_and_hides_sale_jobs(self):
        job = ChekVazifa.objects.create(terminal=self.terminal)
        other = get_user_model().objects.create_user(username='another')
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse('printer_sinov_holat',args=[job.pk])).status_code,404)

    def test_auth_post_and_csrf_are_required(self):
        self.assertEqual(self.client.get(self.url).status_code,405)
        anonymous = Client()
        self.assertEqual(anonymous.post(self.url).status_code,302)
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(self.user)
        self.assertEqual(csrf.post(self.url).status_code,403)
