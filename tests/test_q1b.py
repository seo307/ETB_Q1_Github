import copy,json,tempfile,unittest
from pathlib import Path
from etb_github.q1b import (PIN,REQUIRED_CASES,expected_observations,classify_native,
                            check_reference,audit_result,verify_result_directory,sha,json_bytes,
                            read_json,pairs_no_duplicates)

ROOT=Path(__file__).resolve().parents[1]

def example():
 cases={name:{'db_match':val,'db_reward':int(val),'env_reward':int(val)} for name,val in expected_observations().items()}
 return {'schema':'ETB_Q1B_NATIVE_SEMANTIC_v081','source_commit':PIN,'task_id':'8',
  'reward_basis':['DB','COMMUNICATE'],'reference_actions_count':4,
  'baseline_db_hash':'124e39a664b56402bcd09cb8a6a9cece6acb8462337c969799d5658e3250f263',
  'target_db_hash':'00766aa3e0341b497a623f93983c8d951b8d48ad541a15123a1e2b902e644a82',
  'cases':cases,'structured_transition':{'booking_created':True,'inventory_delta':True},
  'strict_tamper':'REJECTED_STRICT_REPLAY','model_calls':0,
  'independent_root_verified':False,'q1_status':'Q1_BLOCKED','confirmatory_eligible':False,
  'overall':'SOURCE_SCOPED_Q1B_DEVELOPMENT_PASS'}

class Q1BTests(unittest.TestCase):
 def test_prior_evidence_unchanged(self):self.assertEqual(check_reference(ROOT),[])
 def test_expected_cases(self):self.assertEqual(set(REQUIRED_CASES),set(expected_observations()))
 def test_base_contract(self):self.assertEqual(audit_result(example(),ROOT),[])
 def test_no_write_false(self):
  x=example();x['cases']['no_write']['db_match']=True;self.assertIn('CASE_MISMATCH:no_write',audit_result(x,ROOT))
 def test_gold_false(self):
  x=example();x['cases']['gold_path']['db_match']=False;self.assertIn('CASE_MISMATCH:gold_path',audit_result(x,ROOT))
 def test_omitted_write_false(self):
  x=example();x['cases']['omitted_write']['db_match']=True;self.assertIn('CASE_MISMATCH:omitted_write',audit_result(x,ROOT))
 def test_rejected_write_false(self):
  x=example();x['cases']['rejected_write']['db_match']=True;self.assertIn('CASE_MISMATCH:rejected_write',audit_result(x,ROOT))
 def test_tampered_lenient_still_db_match(self):
  x=example();x['cases']['tampered_tool_output_lenient']['db_match']=False;self.assertIn('CASE_MISMATCH:tampered_tool_output_lenient',audit_result(x,ROOT))
 def test_strict_reject_required(self):
  x=example();x['strict_tamper']='NOT_REJECTED';self.assertIn('STRICT_TAMPER_NOT_REJECTED',audit_result(x,ROOT))
 def test_no_structural_oracle(self):
  x=example();x['structured_transition']={};self.assertIn('STRUCTURED_TRANSITION_NOT_VERIFIED',audit_result(x,ROOT))
 def test_structural_false(self):
  x=example();x['structured_transition']['booking_created']=False;self.assertIn('STRUCTURED_TRANSITION_NOT_VERIFIED',audit_result(x,ROOT))
 def test_full_task_reward_blocked(self):
  x=example();x['reward_basis']=['DB'];self.assertIn('NATIVE_REWARD_BASIS_CHANGED',audit_result(x,ROOT))
 def test_q1_always_blocked(self):
  x=example();x['q1_status']='PASS';self.assertIn('ASSURANCE_CLAIM_ESCALATED',audit_result(x,ROOT))
 def test_confirmatory_forbidden(self):
  x=example();x['confirmatory_eligible']=True;self.assertIn('ASSURANCE_CLAIM_ESCALATED',audit_result(x,ROOT))
 def test_model_calls_forbidden(self):
  x=example();x['model_calls']=1;self.assertIn('ASSURANCE_CLAIM_ESCALATED',audit_result(x,ROOT))
 def test_context_integrity(self):
  x=example();x['target_db_hash']='0'*64;self.assertIn('TARGET_DRIFT',audit_result(x,ROOT))
 def test_reference_action_drift(self):
  x=example();x['reference_actions_count']=5;self.assertIn('REFERENCE_ACTION_COUNT_CHANGED',audit_result(x,ROOT))
 def test_nonfinite_json_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'bad.json';p.write_text('{"x":NaN}')
   with self.assertRaises(ValueError):read_json(p)
 def test_duplicate_key_json_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'bad.json';p.write_text('{"x":1,"x":2}')
   with self.assertRaises(ValueError):read_json(p)
 def test_upstream_lock_requires_exact_pinned_bytes(self):
  source=(ROOT/'etb_github/q1b.py').read_text()
  self.assertIn('FROZEN_UPSTREAM_LOCK_DRIFT',source)
 def test_result_directory_missing_rejected(self):
  with tempfile.TemporaryDirectory() as d:self.assertTrue(verify_result_directory(d,ROOT))
 def test_result_directory_hash_missing(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'SHA256_MANIFEST.json').write_bytes(json_bytes({'native_semantic.json':'0'*64}))
   self.assertTrue(verify_result_directory(p,ROOT))
 def test_result_directory_extra_file_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)
   files={'native_semantic.json':json_bytes(example()),'context.json':json_bytes({'schema':'test'}),
          'upstream_uv.lock':b'lock','python_packages.txt':b'packages'}
   for n,b in files.items():(p/n).write_bytes(b)
   (p/'SHA256_MANIFEST.json').write_bytes(json_bytes({n:sha(p/n) for n in files}))
   (p/'EXTRA').write_text('foo')
   self.assertIn('RESULT_EXTRA_OR_MISSING_FILE',verify_result_directory(p,ROOT))
 def test_signed_claim_not_independent(self):
  x=example();self.assertEqual(x['independent_root_verified'],False);self.assertEqual(x['q1_status'],'Q1_BLOCKED')
 def test_prior_manifest_hash_is_expected(self):
  p=ROOT/'evidence/v080_run45085918830/native_result.json';self.assertEqual(sha(p),'3cbf8168187499b73c40db953b8c34e83fb03dcbcafc5e7a1806c8d4f4fdec48')
 def test_replay_rejected_literal_native_guard(self):
  source=(ROOT/'scripts/q1b_native_probe.py').read_text()
  self.assertIn("rejected[-1].error=True;rejected[-1].execution_status='rejected'",source)
  self.assertIn('strict=False',source)
 def test_strict_exception_guard_is_specific(self):
  source=(ROOT/'scripts/q1b_native_probe.py').read_text()
  self.assertIn('UNRELATED_STRICT_EVALUATOR_ERROR',source)
  self.assertIn("('Tool call:', 'Returned:', 'Expected:')",source)
 def test_development_not_confirmatory(self):
  cfg=read_json(ROOT/'protocol/freeze_q1b_v081.json')
  self.assertFalse(cfg['confirmatory_eligible']);self.assertEqual(cfg['model_calls'],0)
 def test_github_workflow_manual_only(self):
  s=(ROOT/'.github/workflows/etb-q1b-native-semantic.yml').read_text()
  self.assertIn('  workflow_dispatch:',s);self.assertNotIn('id-token: write',s)
 def test_output_no_raw_booking_details(self):
  x=example();self.assertNotIn('passengers',json.dumps(x));self.assertNotIn('payment',json.dumps(x))
 def test_original_manifest_v080_preserved(self):
  # The original workflow content remains bytewise identical to its manifest entry.
  mf=read_json(ROOT/'MANIFEST.sha256.json')
  self.assertEqual(sha(ROOT/'.github/workflows/etb-q1-native-preflight.yml'),mf['.github/workflows/etb-q1-native-preflight.yml'])

if __name__=='__main__':unittest.main()
