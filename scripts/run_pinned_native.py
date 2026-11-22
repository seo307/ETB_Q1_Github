#!/usr/bin/env python3
"""Single frozen, source-scoped native Airline preflight. Never certify Q1.

Offline except the pre-installed pinned checkout, and never issues agent/model calls.
"""
from __future__ import annotations
import argparse,hashlib,json,os,platform,shutil,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from etb_github.contract import PIN,Q0_SHA,freeze_check,git_checked,readj,sha,canonical
sys.path.insert(0,str(ROOT/'native_original'))
from native_airline_effect_probe import generate

def snapshot_context():
 env=os.environ
 # No tokens or secrets. This is self-reported runner context, to be checked by the GitHub REST collector.
 return {'GITHUB_ACTIONS':env.get('GITHUB_ACTIONS'),
         'GITHUB_REPOSITORY':env.get('GITHUB_REPOSITORY'),
         'GITHUB_RUN_ID':env.get('GITHUB_RUN_ID'),
         'GITHUB_RUN_ATTEMPT':env.get('GITHUB_RUN_ATTEMPT'),
         'GITHUB_SHA':env.get('GITHUB_SHA'),
         'GITHUB_EVENT_NAME':env.get('GITHUB_EVENT_NAME'),
         'GITHUB_WORKFLOW_REF':env.get('GITHUB_WORKFLOW_REF'),
         'RUNNER_OS':env.get('RUNNER_OS'), 'RUNNER_ARCH':env.get('RUNNER_ARCH'),
         'GITHUB_SERVER_URL':env.get('GITHUB_SERVER_URL')}

def assess_native(native,freeze):
 reasons=[]
 if native.get('status')!='NATIVE_EFFECT_DEVELOPMENT_PREFLIGHT_PASS_ROOT_UNVERIFIED':reasons.append('NATIVE_PROBE_NOT_PASS')
 if native.get('git_commit')!=PIN or native.get('source_q0_sha256')!=Q0_SHA:reasons.append('NATIVE_PIN_MISMATCH')
 if native.get('task_id')!=freeze['task_id']:reasons.append('TASK_ID_MISMATCH')
 if native.get('native_sut_executed') is not False or native.get('independent_root_verified') is not False or native.get('confirmatory_eligible') is not False:reasons.append('NATIVE_ESCALATED_CLAIM')
 controls=native.get('controls',{})
 for name in ('known_no_write','known_write'):
  if controls.get(name,{}).get('pass') is not True:reasons.append('CONTROL_FAILED_'+name)
 if controls.get('known_write',{}).get('state_effect_detectable') is not True:reasons.append('EFFECT_NOT_DETECTABLE')
 if not isinstance(native.get('reference_action_log'),list):reasons.append('MISSING_NATIVE_ACTION_LOG')
 return reasons

def run(repo,out_dir,pip_freeze=None,upstream_lock=None):
 frozen,issues=freeze_check()
 if issues:raise ValueError('FROZEN_INPUTS_INVALID:'+','.join(issues))
 git_checked(repo)
 out=Path(out_dir)
 if out.exists():raise ValueError('REFUSE_OVERWRITE_OUTPUT_DIRECTORY')
 out.mkdir(parents=True)
 try:
  native=generate(Path(repo).resolve(),ROOT/'inputs/Q0_public_census.json',frozen['task_id'])
  reasons=assess_native(native,frozen)
  (out/'native_result.json').write_bytes(canonical(native)+b'\n')
  github=snapshot_context()
  context={'schema':'ETB_GITHUB_NATIVE_CONTEXT_v080','github':github,'source_commit':PIN,'q0_sha256':Q0_SHA,
           'freeze_sha256':sha(ROOT/'protocol/freeze_v080.json'),
           'native_report_sha256':sha(out/'native_result.json'),
           'python_version':platform.python_version(),
           'python_executable_basename':Path(sys.executable).name,
           'system':platform.system(),'machine':platform.machine(),
           'run_mode':'GITHUB_CONTEXT_SELF_REPORTED' if github['GITHUB_ACTIONS']=='true' else 'LOCAL_DEVELOPMENT',
           'native_agent_calls':0,'independent_root_verified':False,'q1_status':'Q1_BLOCKED',
           'confirmatory_eligible':False,'native_validation_status':'PASS' if not reasons else 'BLOCKED',
           'issues':reasons}
  if pip_freeze:
   p=Path(pip_freeze)
   if not p.is_file():raise ValueError('PIP_FREEZE_MISSING')
   shutil.copyfile(p,out/'python_packages.txt')
   context['pip_freeze_sha256']=sha(out/'python_packages.txt')
  if upstream_lock:
   p=Path(upstream_lock)
   if not p.is_file() or p.name!='uv.lock':raise ValueError('UPSTREAM_LOCK_MISSING_OR_WRONG_NAME')
   shutil.copyfile(p,out/'upstream_uv.lock')
   context['upstream_uv_lock_sha256']=sha(out/'upstream_uv.lock')
   context['dependency_strategy']='UPSTREAM_UV_FROZEN'
   context['uv_version_pinned']='0.13.9'
  (out/'context.json').write_bytes(canonical(context)+b'\n')
  manifest={x.name:sha(x) for x in sorted(out.iterdir()) if x.is_file()}
  (out/'SHA256_MANIFEST.json').write_bytes(canonical(manifest)+b'\n')
  return context
 except Exception:
  # Keep partial files as diagnostic records; never label this as success.
  raise

def main():
 p=argparse.ArgumentParser();p.add_argument('--checkout',required=True);p.add_argument('--out-dir',required=True);p.add_argument('--pip-freeze');p.add_argument('--upstream-lock')
 args=p.parse_args()
 try:context=run(args.checkout,args.out_dir,args.pip_freeze,args.upstream_lock)
 except Exception as e:
  print(json.dumps({'status':'NATIVE_PREFLIGHT_BLOCKED','reason':str(e)[:240],'q1_status':'Q1_BLOCKED'}));return 2
 print(json.dumps({'status':'NATIVE_PREFLIGHT_PASS_SOURCE_SCOPED_ONLY' if context['native_validation_status']=='PASS' else 'NATIVE_PREFLIGHT_BLOCKED',
  'q1_status':'Q1_BLOCKED','native_agent_calls':0,'issues':context['issues']},indent=2))
 return 0 if context['native_validation_status']=='PASS' else 2
if __name__=='__main__':raise SystemExit(main())
