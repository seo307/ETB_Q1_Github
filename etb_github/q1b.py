"""Q1B boundary logic: pure, strict, auditable, without semantic-oracle claims."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

REQUIRED_CASES=("no_write", "gold_path", "omitted_write", "rejected_write", "tampered_tool_output_lenient")
PIN="c06b07dd7c4d4ec61ba6ff9bcdf0b15dd7ef36d4"
V080_RUN="45085918830"
V080_SHA="eaecb26bddd8a70df5668d2646160e00d7315b44"
V080_ART_SHA="a48f2ac62d2c5ac286fe77f533b33f840d1206be1afea2ef0b483f99b0006081"
V080_REFERENCE={"context.json":"cedee8575f124cb3a30940617505eb5034436531e088c437356670a27e9323ba",
                "native_result.json":"3cbf8168187499b73c40db953b8c34e83fb03dcbcafc5e7a1806c8d4f4fdec48",
                "python_packages.txt":"6391fbaeb4ddc5488136191e2e81f6643a7bde7524ffe126884baf51b7d78ab9",
                "upstream_uv.lock":"3254fbf8ac11d4a7a68fffb2d2f0b5fd6e35c7b92c9ddff2ad7f9af4ad10591d"}

def sha_bytes(b: bytes)->str: return hashlib.sha256(b).hexdigest()
def sha(p):return sha_bytes(Path(p).read_bytes())
def pairs_no_duplicates(pairs):
 o={}
 for k,v in pairs:
  if k in o:raise ValueError("DUPLICATE_JSON_KEY:"+k)
  o[k]=v
 return o

def read_json(p):
 def reject(c):raise ValueError("NONFINITE_JSON:"+c)
 return json.loads(Path(p).read_text(encoding="utf-8"),object_pairs_hook=pairs_no_duplicates,parse_constant=reject)

def json_bytes(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()

def check_reference(root):
 root=Path(root);d=root/'evidence/v080_run45085918830'; issues=[]
 try:
  mf=read_json(d/'SHA256_MANIFEST.json')
  if mf!=V080_REFERENCE:issues.append('V080_REFERENCE_MANIFEST_CHANGED')
  for k,v in V080_REFERENCE.items():
   if not (d/k).is_file() or sha(d/k)!=v:issues.append('V080_REFERENCE_FILE_MISMATCH:'+k)
  n=read_json(d/'native_result.json');c=read_json(d/'context.json')
  if n.get('git_commit')!=PIN or n.get('task_id')!='8':issues.append('V080_TASK_PIN')
  if c.get('github',{}).get('GITHUB_RUN_ID')!=V080_RUN or c.get('github',{}).get('GITHUB_SHA')!=V080_SHA:issues.append('V080_RUN_BINDING')
  if c.get('native_report_sha256')!=sha(d/'native_result.json'):issues.append('V080_NATIVE_BINDING')
  if n.get('status')!='NATIVE_EFFECT_DEVELOPMENT_PREFLIGHT_PASS_ROOT_UNVERIFIED':issues.append('V080_NATIVE_STATUS')
  if not n.get('controls',{}).get('known_no_write',{}).get('pass') or not n.get('controls',{}).get('known_write',{}).get('pass'):issues.append('V080_CONTROLS')
  if c.get('independent_root_verified') is not False or c.get('confirmatory_eligible') is not False:issues.append('V080_ESCALATION')
 except (OSError,ValueError,KeyError,TypeError) as e:issues.append('V080_REFERENCE_PARSE:'+type(e).__name__)
 return sorted(set(issues))

def expected_observations():
 return {"no_write":False,"gold_path":True,"omitted_write":False,
         "rejected_write":False,"tampered_tool_output_lenient":True}

def classify_native(cases,structured,strict_tamper):
 issues=[]; expected=expected_observations()
 if not isinstance(cases,dict):return ['CASES_INVALID']
 for k,v in expected.items():
  got=cases.get(k)
  if not isinstance(got,dict) or got.get('db_match') is not v:issues.append('CASE_MISMATCH:'+k)
  if isinstance(got,dict) and (got.get('db_reward') not in (0,1) or got.get('db_reward')!=int(v)):
   issues.append('DB_REWARD_MISMATCH:'+k)
 if strict_tamper!='REJECTED_STRICT_REPLAY':issues.append('STRICT_TAMPER_NOT_REJECTED')
 if not isinstance(structured,dict) or not structured or not all(v is True for v in structured.values()):
  issues.append('STRUCTURED_TRANSITION_NOT_VERIFIED')
 return issues

def audit_result(result,root):
 errors=check_reference(root)
 try:
  if result.get('schema')!='ETB_Q1B_NATIVE_SEMANTIC_v081':errors.append('RESULT_SCHEMA')
  if result.get('task_id')!='8' or result.get('source_commit')!=PIN:errors.append('RESULT_SOURCE_PIN')
  if result.get('baseline_db_hash')!='124e39a664b56402bcd09cb8a6a9cece6acb8462337c969799d5658e3250f263':errors.append('BASELINE_DRIFT')
  if result.get('target_db_hash')!='00766aa3e0341b497a623f93983c8d951b8d48ad541a15123a1e2b902e644a82':errors.append('TARGET_DRIFT')
  if result.get('reward_basis')!=['DB','COMMUNICATE']:errors.append('NATIVE_REWARD_BASIS_CHANGED')
  if result.get('reference_actions_count')!=4:errors.append('REFERENCE_ACTION_COUNT_CHANGED')
  errors+=classify_native(result.get('cases'),result.get('structured_transition'),result.get('strict_tamper'))
  if result.get('model_calls')!=0 or result.get('q1_status')!='Q1_BLOCKED' or result.get('independent_root_verified') is not False or result.get('confirmatory_eligible') is not False:errors.append('ASSURANCE_CLAIM_ESCALATED')
  if result.get('overall')!='SOURCE_SCOPED_Q1B_DEVELOPMENT_PASS':errors.append('RESULT_NOT_PASS')
 except (AttributeError,TypeError,ValueError,KeyError) as e:errors.append('RESULT_PARSE:'+type(e).__name__)
 return sorted(set(errors))

def verify_result_directory(directory,root):
 p=Path(directory);errs=[]
 try:
  mf=read_json(p/'SHA256_MANIFEST.json')
  if set(mf)!={'native_semantic.json','context.json','upstream_uv.lock','python_packages.txt'}:
   errs.append('RESULT_FILE_SET')
  if set(x.name for x in p.iterdir() if x.is_file())!=set(mf)|{'SHA256_MANIFEST.json'}:
   errs.append('RESULT_EXTRA_OR_MISSING_FILE')
  for k,v in mf.items():
   if not re.fullmatch('[a-f0-9]{64}',v) or '/' in k or not (p/k).is_file() or sha(p/k)!=v:errs.append('ARTIFACT_MISMATCH:'+k)
  result=read_json(p/'native_semantic.json'); ctx=read_json(p/'context.json')
  errs+=audit_result(result,root)
  if ctx.get('native_result_sha256')!=sha(p/'native_semantic.json'):errs.append('CONTEXT_NATIVE_HASH')
  if ctx.get('upstream_uv_lock_sha256')!=sha(p/'upstream_uv.lock'):errs.append('CONTEXT_LOCK_HASH')
  if sha(p/'upstream_uv.lock')!=V080_REFERENCE['upstream_uv.lock']:errs.append('FROZEN_UPSTREAM_LOCK_DRIFT')
  if ctx.get('python_packages_sha256')!=sha(p/'python_packages.txt'):errs.append('CONTEXT_DEPENDENCY_HASH')
  if ctx.get('source_commit')!=PIN or ctx.get('q1_status')!='Q1_BLOCKED' or ctx.get('independent_root_verified') is not False:errs.append('CONTEXT_CLAIMS')
  if ctx.get('run_mode')!='GITHUB_CONTEXT_SELF_REPORTED':errs.append('NOT_EXTERNAL_GITHUB_CONTEXT')
 except (OSError,ValueError,TypeError,AttributeError) as e:errs.append('RESULT_DIRECTORY_PARSE:'+type(e).__name__)
 return sorted(set(errs))
