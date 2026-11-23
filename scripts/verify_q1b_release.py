#!/usr/bin/env python3
"""Strict public release + frozen prior run linkage. Does not execute tau2."""
from __future__ import annotations
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from etb_github.q1b import check_reference,read_json,sha,V080_ART_SHA
from scripts.verify_release import verify as verify_v080

def verify():
 issues=[]
 v080=verify_v080();issues+=v080['issues']
 issues+=check_reference(ROOT)
 try:
  frozen=read_json(ROOT/'protocol/freeze_q1b_v081.json')
  if frozen.get('schema')!='ETB_Q1B_FREEZE_v081':issues.append('Q1B_FREEZE_SCHEMA')
  if frozen.get('reference_run_id')!=45085918830 or frozen.get('reference_artifact_sha256')!=V080_ART_SHA:
   issues.append('Q1B_REFERENCE_LINKAGE')
  if frozen.get('source_commit')!='c06b07dd7c4d4ec61ba6ff9bcdf0b15dd7ef36d4' or frozen.get('task_id')!='8':issues.append('Q1B_NATIVE_PIN')
  if frozen.get('q1_independent_root_verified') is not False or frozen.get('confirmatory_eligible') is not False or frozen.get('model_calls')!=0:issues.append('Q1B_CLAIM_ESCALATION')
  work=(ROOT/'.github/workflows/etb-q1b-native-semantic.yml').read_text()
  for t in ['workflow_dispatch:', 'permissions:', 'contents: read','persist-credentials: false','uv sync --frozen',
            'q1b_native_probe.py','--upstream-lock vendor/tau2-bench/uv.lock','--pip-freeze "$RUNNER_TEMP/etb-q1b-pip-freeze.txt"',
            'validate_q1b_artifact.py',frozen['source_commit']]:
   if t not in work:issues.append('Q1B_WORKFLOW_MISSING:'+t)
  if not re.search(r'(?m)^on:\n  workflow_dispatch:\s*$',work):issues.append('WORKFLOW_NOT_DISPATCH_ONLY')
  if any(re.search(r'(?m)^\s*'+re.escape(t)+r'\s*:',work) for t in ('pull_request','push','schedule','workflow_run','pull_request_target')):
   issues.append('Q1B_UNAPPROVED_TRIGGER')
  if any(x in work for x in ('id-token: write','contents: write','attestations: write')):issues.append('Q1B_EXCESSIVE_GITHUB_PRIVILEGE')
  if 'credential' in work.lower() and 'persist-credentials' not in work:issues.append('Q1B_CREDENTIAL_SCOPE')
  if '/Users/' in (ROOT/'inputs/Q0_public_census.json').read_text():issues.append('Q0_PATH_DISCLOSURE')
  mf=read_json(ROOT/'MANIFEST.sha256.json')
  listed=set(mf)
  files={str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and p.name not in ('MANIFEST.sha256.json',) and '__pycache__' not in p.parts and not any(x in p.parts for x in ('.git','results'))}
  if listed!=files:issues.append('RELEASE_FILE_SET_DIFF:'+';'.join(sorted(listed.symmetric_difference(files))[:8]))
 except (OSError,ValueError,TypeError,KeyError) as e:issues.append('Q1B_RELEASE_ERROR:'+type(e).__name__+':'+str(e)[:110])
 return {'status':'ETB_Q1B_V081_RELEASE_PASS' if not issues else 'ETB_Q1B_V081_RELEASE_FAIL',
         'files_checked':v080['files_checked'],'reference_v080_run_id':45085918830,
         'reference_artifact_zip_sha256':V080_ART_SHA,
         'q1_status':'Q1_BLOCKED','independent_root_verified':False,'confirmatory_eligible':False,
         'native_agent_runs':0,'external_q1b_runs_executed_here':0,'issues':sorted(set(issues))}
if __name__=='__main__':
 x=verify();print(json.dumps(x,indent=2));raise SystemExit(0 if not x['issues'] else 2)
