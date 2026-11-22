import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from etb_github.contract import ROOT,PIN,Q0_SHA,readj,canonical,freeze_check,git_checked
from etb_github.validate import check_artifact
from scripts.run_pinned_native import assess_native,run


def fake_native():
 return {'status':'NATIVE_EFFECT_DEVELOPMENT_PREFLIGHT_PASS_ROOT_UNVERIFIED','git_commit':PIN,'source_q0_sha256':Q0_SHA,
 'task_id':'8','native_sut_executed':False,'independent_root_verified':False,'confirmatory_eligible':False,
 'controls':{'known_no_write':{'pass':True},'known_write':{'pass':True,'state_effect_detectable':True}},'reference_action_log':[{'ordinal':0,'name':'native_action','status':'NATIVE_REPLAY_CALLED'}]}

class ContractTests(unittest.TestCase):
 def test_freeze(self):self.assertEqual(freeze_check()[1],[])
 def test_q0_exact_sha(self):self.assertEqual(__import__('hashlib').sha256((ROOT/'inputs/Q0_public_census.json').read_bytes()).hexdigest(),Q0_SHA)
 def test_duplicate_json_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'x';p.write_text('{"a":1,"a":2}')
   with self.assertRaises(ValueError):readj(p)
 def test_nan_json_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'x';p.write_text('{"a":NaN}')
   with self.assertRaises(ValueError):readj(p)
 def test_native_ok(self):self.assertEqual(assess_native(fake_native(),freeze_check()[0]),[])
 def test_wrong_task(self):
  x=fake_native();x['task_id']='9'
  self.assertIn('TASK_ID_MISMATCH',assess_native(x,freeze_check()[0]))
 def test_native_fake_success_denied(self):
  x=fake_native();x['independent_root_verified']=True
  self.assertIn('NATIVE_ESCALATED_CLAIM',assess_native(x,freeze_check()[0]))
 def test_no_write_false(self):
  x=fake_native();x['controls']['known_no_write']['pass']=False
  self.assertIn('CONTROL_FAILED_known_no_write',assess_native(x,freeze_check()[0]))
 def test_missing_gold_change(self):
  x=fake_native();x['controls']['known_write']['state_effect_detectable']=False
  self.assertIn('EFFECT_NOT_DETECTABLE',assess_native(x,freeze_check()[0]))
 def test_git_not_repository(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(ValueError):git_checked(td)
 def test_mock_run_artifact_internal_only(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'native'
   with patch('scripts.run_pinned_native.git_checked'),patch('scripts.run_pinned_native.generate',return_value=fake_native()):
    x=run(td,out)
   self.assertEqual(x['q1_status'],'Q1_BLOCKED')
   self.assertEqual(x['run_mode'],'LOCAL_DEVELOPMENT')
   self.assertEqual(check_artifact(out),[])
   # Artifact receipt rejects tamper even though JSON might still be syntactically valid.
   (out/'native_result.json').write_text('{}')
   self.assertIn('ARTIFACT_HASH_MISMATCH:native_result.json',check_artifact(out))
 def test_overwrite_denied(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'native';p.mkdir()
   with patch('scripts.run_pinned_native.git_checked'):
    with self.assertRaises(ValueError):run(td,p)
 def test_mock_run_failure_stays_blocked(self):
  with tempfile.TemporaryDirectory() as td:
   x=fake_native();x['controls']['known_write']['pass']=False
   with patch('scripts.run_pinned_native.git_checked'),patch('scripts.run_pinned_native.generate',return_value=x):
    c=run(td,Path(td)/'native')
   self.assertEqual(c['native_validation_status'],'BLOCKED')
   self.assertIn('NATIVE_CONTEXT_BLOCKED',check_artifact(Path(td)/'native'))
 def test_mock_input_not_benchmark_claim(self):
  x=fake_native()
  self.assertFalse(x['native_sut_executed'])
  self.assertFalse(x['independent_root_verified'])
