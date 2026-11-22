import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from etb_github.github_api import assess
from etb_github.validate import check_artifact
from etb_github.contract import WORKFLOW,PIN,readj
from scripts.run_pinned_native import run
from tests.test_contract import fake_native

SHA='0'*39+'1'
REPO='someone/etb-research'
RID=1112341

class GithubTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.d=Path(self.temp.name)/'native'
  environ={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':REPO,'GITHUB_RUN_ID':str(RID),
   'GITHUB_RUN_ATTEMPT':'1','GITHUB_SHA':SHA,'GITHUB_EVENT_NAME':'workflow_dispatch',
   'GITHUB_WORKFLOW_REF':REPO+'/'+WORKFLOW+'@refs/heads/main',
   'RUNNER_OS':'Linux','RUNNER_ARCH':'X64','GITHUB_SERVER_URL':'https://github.com'}
  lock=Path(self.temp.name)/'uv.lock';lock.write_text('version = 1\n')
  packages=Path(self.temp.name)/'freeze.txt';packages.write_text('tau2==2.0.0\n')
  with patch.dict('os.environ',environ,clear=True),patch('scripts.run_pinned_native.git_checked'),patch('scripts.run_pinned_native.generate',return_value=fake_native()):
   run(self.temp.name,self.d,pip_freeze=packages,upstream_lock=lock)
  self.api={'id':RID,'run_attempt':1,'head_sha':SHA,'event':'workflow_dispatch','status':'completed','conclusion':'success',
   'path':WORKFLOW+'@refs/heads/main','repository':{'full_name':REPO}}
  self.jobs={'total_count':1,'jobs':[{'id':16,'run_id':RID,'name':'native-preflight','status':'completed','conclusion':'success',
   'labels':['ubuntu-24.04'],'runner_name':'GitHub Actions 1234'}]}
 def assessed(self,run=None,jobs=None):return assess(run or self.api,jobs or self.jobs,self.d)
 def assert_fails(self,code):self.assertIn(code,self.assessed()['issues'])
 def test_corroborated_still_blocked(self):
  a=self.assessed();self.assertEqual(a['status'],'GITHUB_HOSTED_NATIVE_PREFLIGHT_CORROBORATED')
  self.assertEqual(a['q1_status'],'Q1_BLOCKED');self.assertFalse(a['independent_administrative_root_verified'])
 def test_run_id_change(self):self.api['id']+=1;self.assert_fails('RUN_ID_MISMATCH')
 def test_repo_change(self):self.api['repository']['full_name']='other/repo';self.assert_fails('REPOSITORY_SCOPE_MISMATCH')
 def test_sha_change(self):self.api['head_sha']='2'*40;self.assert_fails('WORKFLOW_SHA_MISMATCH')
 def test_event_change(self):self.api['event']='pull_request';self.assert_fails('API_EVENT_NOT_DISPATCH')
 def test_attempt_change(self):self.api['run_attempt']=2;self.assert_fails('RUN_ATTEMPT_MISMATCH')
 def test_run_failure(self):self.api['conclusion']='failure';self.assert_fails('RUN_NOT_SUCCESSFUL')
 def test_path_change(self):self.api['path']='.github/workflows/untrusted.yml';self.assert_fails('WORKFLOW_PATH_MISMATCH')
 def test_missing_job(self):self.jobs['jobs']=[];self.assert_fails('EXPECTED_JOB_NOT_UNIQUE')
 def test_two_jobs(self):self.jobs['jobs'].append(copy.deepcopy(self.jobs['jobs'][0]));self.jobs['total_count']=2;self.assert_fails('EXPECTED_JOB_NOT_UNIQUE')
 def test_self_hosted_denied(self):self.jobs['jobs'][0]['labels']=['self-hosted','ubuntu-24.04'];self.assert_fails('HOSTED_RUNNER_LABEL_NOT_VERIFIED')
 def test_wrong_runner_label(self):self.jobs['jobs'][0]['labels']=['ubuntu-latest'];self.assert_fails('HOSTED_RUNNER_LABEL_NOT_VERIFIED')
 def test_job_failed(self):self.jobs['jobs'][0]['conclusion']='failure';self.assert_fails('NATIVE_JOB_NOT_SUCCESSFUL')
 def test_job_not_associated(self):self.jobs['jobs'][0]['run_id']=999;self.assert_fails('JOB_RUN_ID_MISMATCH')
 def test_pagination_fail(self):self.jobs['total_count']=2;self.assert_fails('JOB_API_PAGINATION_INCOMPLETE')
 def test_tampered_context_fails(self):
  import json,hashlib
  c=readj(self.d/'context.json');c['github']['GITHUB_RUN_ID']='fake'
  (self.d/'context.json').write_text(json.dumps(c))
  self.assertIn('ARTIFACT_HASH_MISMATCH:context.json',self.assessed()['issues'])
 def test_unauthentic_root_never_certified(self):
  a=self.assessed();self.assertFalse(a['independent_effect_oracle_verified'])
  self.assertFalse(a['latest_checkpoint_external_root_verified'])
