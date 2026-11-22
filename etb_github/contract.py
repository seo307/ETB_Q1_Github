"""Fail-closed source, input, output and external metadata checks."""
from __future__ import annotations
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PIN='c06b07dd7c4d4ec61ba6ff9bcdf0b15dd7ef36d4'
Q0_SHA='6706cfaef1665e685ebadc1f328528c5f2eca618e2d5eaa38cba5c82da476ee4'
WORKFLOW='.github/workflows/etb-q1-native-preflight.yml'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dupe_reject(pairs):
 o={}
 for k,v in pairs:
  if k in o:raise ValueError('DUPLICATE_JSON_KEY:'+k)
  o[k]=v
 return o

def readj(path):
 def reject_constant(v):raise ValueError('NONFINITE_JSON:'+v)
 return json.loads(Path(path).read_text(encoding='utf-8'),object_pairs_hook=dupe_reject,parse_constant=reject_constant)

def canonical(obj):return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',', ':'),allow_nan=False).encode()
def freeze_check():
 f=readj(ROOT/'protocol/freeze_v080.json');q0=readj(ROOT/'inputs/Q0_public_census.json')
 issues=[]
 if f.get('schema')!='ETB_Q1_GITHUB_NATIVE_FREEZE_v080':issues.append('FREEZE_SCHEMA')
 if f.get('source_commit')!=PIN or f.get('q0_sha256')!=Q0_SHA:issues.append('FREEZE_SOURCE_PIN')
 if sha(ROOT/'inputs/Q0_public_census.json')!=Q0_SHA:issues.append('Q0_BYTES_CHANGED')
 if q0.get('status')!='Q0_LOCAL_SOURCE_PIN_VERIFIED_Q1_STILL_REQUIRED' or q0.get('head')!=PIN or q0.get('pin_commit')!=PIN or q0.get('issues'):issues.append('Q0_STATUS_PIN')
 if f.get('task_id')!='8' or f.get('domain')!='airline' or '8' not in q0.get('airline_base_ids',[]):issues.append('FROZEN_TASK_MISSING')
 if f.get('q0_original_private_sha256')!='345f4f6673bf31fcec0d50bde87ff970b00d0171da504c383ea02b050a6c10cc':issues.append('ORIGINAL_Q0_LINK_MISSING')
 if f.get('q1_independent_root_verified') is not False or f.get('q2_confirmatory_eligible') is not False or f.get('native_agent_calls')!=0:issues.append('FREEZE_ASSURANCE_CEILING')
 if f.get('expected_runner_label')!='ubuntu-24.04' or f.get('allowed_workflow_event')!='workflow_dispatch':issues.append('FROZEN_RUNNER_SCOPE')
 return f,issues

def git_checked(repo):
 r=Path(repo)
 def run(*a):
  x=subprocess.run(['git','-C',str(r),*a],capture_output=True,text=True,timeout=20)
  if x.returncode:raise ValueError('GIT_'+a[0].upper()+'_ERROR')
  return x.stdout.strip()
 if run('rev-parse','HEAD')!=PIN:raise ValueError('SOURCE_PIN_MISMATCH')
 if run('status','--porcelain','--untracked-files=no'):raise ValueError('SOURCE_TRACKED_FILES_MODIFIED')
 if not (r/'src/tau2/__init__.py').is_file():raise ValueError('SOURCE_LAYOUT_MISSING')
 return True

def valid_sha(s):return isinstance(s,str) and bool(re.fullmatch('[0-9a-f]{40}',s))
