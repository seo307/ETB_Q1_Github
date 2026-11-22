import io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts.fetch_github_run import acquire
from scripts.verify_release import verify
from etb_github.contract import ROOT,PIN,readj

class DummyResponse:
 status=200
 def __init__(self,b):self.f=io.BytesIO(b)
 def read(self,n=-1):return self.f.read(n)
 def __enter__(self):return self
 def __exit__(self,*a):return False

class ArtifactTests(unittest.TestCase):
 def test_release(self):
  x=verify();self.assertFalse(x['issues'],x);self.assertEqual(x['q1_status'],'Q1_BLOCKED')
 def test_workflow_manual_only(self):
  s=(ROOT/'.github/workflows/etb-q1-native-preflight.yml').read_text()
  self.assertIn('workflow_dispatch:',s)
  self.assertNotIn('id-token: write',s)
  self.assertNotIn('pull_request_target:',s)
 def test_prior_pinned(self):
  self.assertEqual(verify()['prior_v072_sha256_pinned_private_not_bundled'],'8b1f1f13483fa6924535732e05ddc6a583ae3a3425502a1e726f2d6792780f82')
 def test_invalid_repo_rejected(self):
  with self.assertRaises(ValueError):acquire('../nonsense',12,'unused')
 def test_readonly_request(self):
  seen=[]
  def opener(req,timeout):
   seen.append((req.get_method(),req.full_url));return DummyResponse(b'{"a":1}')
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'remote'
   r=acquire('owner/repo',123,out,opener=opener)
   self.assertEqual(r['q1_status'],'Q1_BLOCKED')
   self.assertEqual(len(seen),2)
   self.assertTrue(all(x[0]=='GET' and x[1].startswith('https://api.github.com/') for x in seen))
   self.assertEqual(readj(out/'run.json'),{'a':1})
 def test_refuse_existing_dir(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(ValueError):acquire('owner/repo',42,td)
 def test_incomplete_api_no_directory(self):
  count=[0]
  def opener(req,timeout):
   count[0]+=1
   return DummyResponse(b'{"a":1}' if count[0]==1 else b'not-json')
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'remote'
   with self.assertRaises(ValueError):acquire('owner/repo',42,out,opener=opener)
   self.assertFalse(out.exists())
