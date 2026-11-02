import json
import subprocess
from types import SimpleNamespace
from unittest.mock import patch

from django.test import RequestFactory, TestCase
from django.contrib.auth import get_user_model

from config import qurilmalar


class QurilmalarTests(TestCase):
    def setUp(self):
        qurilmalar._cached = None
        qurilmalar._expires = 0
        self.request = RequestFactory().get('/qurilmalar/royxat/')
        self.request.user = get_user_model().objects.create_user(username='device-test')

    def test_filter_and_classification(self):
        def row(cls, name, ident):
            return dict(Class=cls, FriendlyName=name, InstanceId=ident, Status='OK')
        rows = [row('Keyboard', 'HID Keyboard', 'HID\\1'),
                row('Mouse', 'USB Mouse', 'USB\\2'),
                row('HIDClass', 'HID-compliant consumer control device', 'HID\\3'),
                row('USB', 'USB Root Hub', 'USB\\4'),
                row('System', 'Chipset', 'PCI\\5'),
                row('Keyboard', 'Barcode Scanner', 'HID\\6'),
                row('Ports', 'Electronic Scale (COM3)', 'USB\\7'),
                row('Ports', 'USB Serial Port (COM4)', 'USB\\8'),
                row('Printer', 'Receipt Printer', 'USBPRINT\\9'),
                row('DiskDrive', 'USB Storage', 'USBSTOR\\10')]
        result = qurilmalar.sarala(rows + [rows[-1]])
        self.assertEqual(len(result), 5)
        by_id = {d['id']: d for d in result}
        self.assertEqual(by_id['HID\\6']['tur'], 'Shtrix kod skaneri')
        self.assertEqual(by_id['USB\\7']['tur'], 'Elektron tarozi')
        self.assertEqual(by_id['USB\\7']['port'], 'COM3')
        self.assertEqual(by_id['USB\\8']['tur'], 'COM / LPT port')

    def test_error_status_not_reported_ready(self):
        result = qurilmalar.sarala([dict(Class='Ports', FriendlyName='COM1',
                                         InstanceId='PORT\\1', Status='Error')])
        self.assertFalse(result[0]['tayyor'])

    def test_scanner_bus_description_and_virtual_printers(self):
        result = qurilmalar.sarala([
            dict(Class='HIDClass', FriendlyName='USB-устройство ввода',
                 BusDescription='2D Barcode Scanner', InstanceId='USB\\SCANNER', Status='OK'),
            dict(Class='PrintQueue', FriendlyName='Microsoft Print to PDF',
                 InstanceId='SWD\\PDF', Status='OK'),
            dict(Class='PrintQueue', FriendlyName='Root print queue',
                 InstanceId='SWD\\PRINTENUM\\PRINTQUEUES', Status='OK'),
        ])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['nom'], '2D Barcode Scanner')
        self.assertEqual(result[0]['tur'], 'Shtrix kod skaneri')

    def test_login_required_for_page_and_api(self):
        for url in ['/qurilmalar/', '/qurilmalar/royxat/']:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn('/kirish/', response.url)

    @patch.object(qurilmalar, 'aniqlash', return_value=[])
    def test_api_empty_success_and_cache(self, detect):
        for _ in range(2):
            response = qurilmalar.royxat(self.request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.content)['qurilmalar'], [])
            self.assertIn('no-store', response['Cache-Control'])
        detect.assert_called_once()

    @patch.object(qurilmalar, 'aniqlash', return_value=[])
    def test_unused_helper_does_not_hide_main_usb_devices(self, detect):
        from sotuv.models import KassaTerminal
        KassaTerminal.objects.create(kassir=self.request.user)
        self.assertEqual(qurilmalar.royxat(self.request).status_code, 200)
        detect.assert_called_once()

    @patch.object(qurilmalar, 'aniqlash', side_effect=subprocess.TimeoutExpired('powershell', 15))
    def test_timeout_not_a_successful_empty_list(self, detect):
        with self.assertLogs('config.qurilmalar', level='ERROR'):
            response = qurilmalar.royxat(self.request)
        self.assertEqual(response.status_code, 503)
        self.assertIn('xato', json.loads(response.content))
        self.assertIsNone(qurilmalar._cached)

    def test_template_and_navigation(self):
        response = qurilmalar.sahifa(self.request)
        self.assertContains(response, 'Yangi ulangan qurilmalar')
        self.assertContains(response, '/qurilmalar/royxat/')
        self.assertContains(response, 'js/qurilmalar.js')
