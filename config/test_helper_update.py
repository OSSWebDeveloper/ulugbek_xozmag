import hashlib,io,json,tempfile,zipfile
from pathlib import Path
from unittest.mock import patch
from django.test import Client
from django.urls import reverse
from config.sinov import KirganTest
from config.kassa_agent import digest
from sotuv.models import KassaTerminal

class HelperUpdateTests(KirganTest):
 def test_authenticated_update_preserves_key_and_excludes_local_configuration(self):
  from django.contrib.auth import get_user_model
  user=get_user_model().objects.get(username=self.LOGIN)
  terminal=KassaTerminal.objects.create(kassir=user,kalit_hash=digest('a'*64))
  url=reverse('kassa_agent_yangila')
  self.assertEqual(Client().post(url).status_code,401)
  with patch('config.kassa_agent.Path.rglob',return_value=[]):
   response=Client().post(url,HTTP_AUTHORIZATION='Bearer '+'a'*64)
  self.assertEqual(response.status_code,200)
  with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
   self.assertNotIn('kassa.json',archive.namelist())
   self.assertNotIn('python.zip',archive.namelist())
   manifest=json.loads(archive.read('manifest.json'))
   for name,h in manifest['files'].items():self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(),h)
   self.assertIn('updater.py',manifest['files'])
  terminal.refresh_from_db();self.assertEqual(terminal.kalit_hash,digest('a'*64))

 def test_rang_routes_are_removed(self):
  self.assertEqual(self.client.get('/rang/').status_code,404)
  self.assertNotContains(self.client.get('/'),'> Rang')
