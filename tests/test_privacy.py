import json,unittest
from pathlib import Path
from etb_github.contract import ROOT,sha,freeze_check

class PublicReleasePrivacyTests(unittest.TestCase):
 def test_public_q0_is_redacted(self):
  p=ROOT/'inputs/Q0_public_census.json'
  x=json.loads(p.read_text())
  self.assertEqual(x['repository'],'REDACTED_LOCAL_PATH')
  self.assertNotIn('/Users/',p.read_text())
 def test_original_provenance_digest_retained(self):
  r=json.loads((ROOT/'protocol/q0_redaction_v080.json').read_text())
  self.assertEqual(r['source_sha256'],'345f4f6673bf31fcec0d50bde87ff970b00d0171da504c383ea02b050a6c10cc')
  self.assertEqual(r['public_sha256'],sha(ROOT/'inputs/Q0_public_census.json'))
 def test_private_original_not_in_public_project(self):
  self.assertFalse((ROOT/'prior').exists())
  self.assertFalse((ROOT/'inputs/Q0_local_census.json').exists())
  self.assertFalse((ROOT/'ETB_Q1_GitHubNative_v0.8.0_PRIVATE_PROVENANCE.zip').exists())
 def test_q1_hard_block_preserved(self):
  f,e=freeze_check()
  self.assertEqual(e,[])
  self.assertIs(f['q1_independent_root_verified'],False)
  self.assertIs(f['q2_confirmatory_eligible'],False)
