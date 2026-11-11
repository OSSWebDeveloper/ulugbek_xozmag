import json
from pathlib import Path
import tempfile
import uuid
from unittest.mock import patch
from django.test import Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from config.sinov import KirganTest
from ombor.models import Mahsulot
from . import etiketka_print as printing


class NativeLabelTests(KirganTest):
    def setUp(self):
        super().setUp()
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        override = override_settings(MALUMOT_DIR=Path(directory.name))
        override.enable(); self.addCleanup(override.disable)
        self.product = Mahsulot.objects.create(nom='Mix', kod='0001', birlik='kg', narx=32000,
                                               kelish_narxi=2, kelish_valyutasi='dollar', qoldiq=100)
        self.url = reverse('etiketka_chop', args=[self.product.pk])
        self.id = str(uuid.uuid4())
        self.data = {'id':self.id, 'printer':'Xprinter XP-80', 'soni':1, 'olcham':'56x40'}
        self.printers = patch.object(printing, 'printers', return_value=[{'nom':'Xprinter XP-80','port':'USB001','drayver':'Xprinter XP-80'}])
        self.printers.start(); self.addCleanup(self.printers.stop)
        self.thread_patch = patch.object(printing.threading, 'Thread')
        self.thread = self.thread_patch.start(); self.addCleanup(self.thread_patch.stop)

    def post(self, **kw):
        return self.client.post(self.url, json.dumps(self.data), content_type='application/json', **kw)

    def test_native_label_uses_sale_price_unit_code_and_requested_size(self):
        self.assertEqual(self.post().status_code, 202)
        data = json.loads((printing.folder() / (self.id + '.data.json')).read_text())
        self.assertEqual(data['narx'], "32 000 so'm")
        self.assertEqual(data['birlik'], 'kg')
        self.assertEqual((data['width_mm'],data['height_mm']), (56,40))
        self.assertEqual(data['kod'], '0001')
        self.assertEqual(data['printer'], 'Xprinter XP-80')
        self.product.refresh_from_db(); self.assertEqual(self.product.qoldiq, 100)

    def test_duplicate_request_id_does_not_reprint(self):
        self.post(); self.post()
        self.thread.assert_called_once()
        response = self.client.get(reverse('etiketka_chop_holat', args=[self.id]))
        self.assertEqual(response.json()['holat'], 'yuborilmoqda')

    def test_other_device_without_helper_never_uses_server_printer(self):
        # Har bir kompyuter o'z printeridan chiqaradi: yordamchisiz qurilma server
        # printerini ko'rmaydi ham, unga yubora olmaydi ham — o'z brauzeridan chiqaradi.
        for extra in (dict(REMOTE_ADDR='192.168.100.88'), dict(REMOTE_ADDR='8.8.8.8'),
                      dict(REMOTE_ADDR='127.0.0.1', HTTP_HOST='abc.ngrok-free.app')):
            response = self.client.get(reverse('etiketka_printerlar'), **extra)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'printerlar': [], 'brauzer': True})
            self.assertEqual(self.post(**extra).status_code, 503)
        self.thread.assert_not_called()

    def test_server_computer_uses_its_own_printers_even_if_helper_is_online_elsewhere(self):
        from sotuv.models import KassaTerminal, ChekVazifa
        from django.utils import timezone
        user = get_user_model().objects.get(username=self.LOGIN)
        KassaTerminal.objects.create(kassir=user, nom='KASSA2', etiketka_tayyor=True,
            printerlar=[{'nom':'USB label','port':'USB003','drayver':'label'}], oxirgi_aloqa=timezone.now())
        response = self.client.get(reverse('etiketka_printerlar'))
        self.assertEqual(response.json(), {'printerlar': [{'nom':'Xprinter XP-80','port':'USB001','drayver':'Xprinter XP-80'}]})
        self.assertEqual(self.post().status_code, 202)
        self.thread.assert_called_once()
        self.assertFalse(ChekVazifa.objects.exists())

    def test_remote_helper_lists_and_queues_its_own_label_once(self):
        from sotuv.models import KassaTerminal,ChekVazifa
        from django.utils import timezone
        user=get_user_model().objects.get(username=self.LOGIN)
        terminal=KassaTerminal.objects.create(kassir=user,etiketka_tayyor=True,
            printerlar=[{'nom':'USB label','port':'USB003','drayver':'label'}],oxirgi_aloqa=timezone.now())
        self.data['printer']='USB label'
        for _ in range(2):
            self.assertEqual(self.post(REMOTE_ADDR='192.168.100.88').status_code,202)
        job=ChekVazifa.objects.get(request_key=self.id)
        self.assertEqual(job.terminal,terminal)
        self.assertEqual(job.malumot['kind'],'etiketka')
        self.assertIsNone(job.sotuv_id)
        self.thread.assert_not_called()
        self.data['id']=str(uuid.uuid4());self.data['printer']='Server only'
        self.assertEqual(self.post(REMOTE_ADDR='192.168.100.88').status_code,400)

    def test_unknown_printer_or_bad_size_does_not_start(self):
        self.data['printer'] = 'Fake'
        self.assertEqual(self.post().status_code, 400)
        self.data['printer'] = 'Xprinter XP-80'; self.data['soni'] = 501
        self.assertEqual(self.post().status_code, 400)
        self.data['soni'] = 1; self.data['olcham'] = 'A4'
        self.assertEqual(self.post().status_code, 400)
        self.thread.assert_not_called()

    def test_other_account_cannot_read_or_reuse_print_job(self):
        self.post()
        user = get_user_model().objects.create_user(username='other')
        self.client.force_login(user)
        self.assertEqual(self.post().status_code, 403)
        self.assertEqual(self.client.get(reverse('etiketka_chop_holat', args=[self.id])).status_code, 403)

    def test_csrf_is_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(get_user_model().objects.get(username=self.LOGIN))
        self.assertEqual(client.post(self.url, json.dumps(self.data), content_type='application/json').status_code, 403)
