"""Printer ulanmagan paytda yig'ilgan cheklar keyin o'zi chiqib ketmaydi."""
import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, SimpleTestCase
from django.urls import reverse
from django.utils import timezone

from config.kassa_agent import ESKIRGAN, digest
from config.sinov import KirganTest
from .models import ChekVazifa, KassaTerminal, Sotuv


class ChekNavbatMuddatiTests(KirganTest):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.get(username=self.LOGIN)
        self.token = 'b' * 64
        self.terminal = KassaTerminal.objects.create(
            kassir=self.user, kalit_hash=digest(self.token), printer='Xprinter XP-80',
            oxirgi_aloqa=timezone.now())
        self.sale = Sotuv.objects.create(kassir=self.user, yakunlangan=True, jami=10000)

    def poll(self):
        return Client().post(
            reverse('kassa_agent_almashish'),
            json.dumps({'printer': 'Xprinter XP-80', 'tayyor': True}),
            content_type='application/json',
            HTTP_AUTHORIZATION='Bearer ' + self.token).json()

    def job(self, yoshi_daqiqa):
        job = ChekVazifa.objects.create(terminal=self.terminal, sotuv=self.sale,
                                        malumot={'nom': 'SAVDO CHEKI'})
        ChekVazifa.objects.filter(pk=job.pk).update(
            yaratilgan=timezone.now() - timedelta(minutes=yoshi_daqiqa))
        return job

    def test_fresh_job_is_printed(self):
        job = self.job(1)
        self.assertEqual(self.poll()['vazifa']['id'], job.pk)

    def test_stale_job_is_not_printed_when_printer_appears(self):
        job = self.job(30)
        self.assertIsNone(self.poll()['vazifa'])
        job.refresh_from_db()
        self.assertEqual(job.holat, 'xato')
        self.assertEqual(job.xato, ESKIRGAN)

    def test_manual_reprint_of_stale_job_goes_out(self):
        job = self.job(30)
        self.poll()
        self.client.post(reverse('sotuv:chek_chop', args=[self.sale.pk]),
                         REMOTE_ADDR='192.168.100.41')
        job.refresh_from_db()
        self.assertEqual(job.holat, 'kutilmoqda')
        self.assertEqual(self.poll()['vazifa']['id'], job.pk)


class YordamchiPrinterTanloviTests(SimpleTestCase):
    def tanla(self, config, *nomlar, default=None):
        from kassa_yordamchi.agent import printer_name
        return printer_name(config, [dict(nom=n, default=n == default) for n in nomlar])

    def test_automatic_never_falls_back_to_label_or_default_printer(self):
        self.assertEqual(self.tanla({}, 'Xprinter XP-365B'), '')
        self.assertEqual(self.tanla({}, 'HP LaserJet', default='HP LaserJet'), '')

    def test_automatic_picks_receipt_printer(self):
        self.assertEqual(self.tanla({}, 'Xprinter XP-365B', 'Xprinter XP-80T'), 'Xprinter XP-80T')
        self.assertEqual(self.tanla({}, 'RONGTA 80mm Series Printer'), 'RONGTA 80mm Series Printer')

    def test_chosen_printer_is_used_only_while_connected(self):
        config = {'printer': 'HP LaserJet'}
        self.assertEqual(self.tanla(config, 'HP LaserJet', 'Xprinter XP-80'), 'HP LaserJet')
        self.assertEqual(self.tanla(config, 'Xprinter XP-80'), '')
