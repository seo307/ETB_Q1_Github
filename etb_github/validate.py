"""Independent artifact shape/integrity checks. Cannot infer independent root truth."""
from pathlib import Path
from .contract import PIN,Q0_SHA,readj,sha,freeze_check

def check_artifact(out):
 out=Path(out);errors=[]
 f,issues=freeze_check();errors.extend(issues)
 try:
  mf=readj(out/'SHA256_MANIFEST.json')
  allowed=({'native_result.json','context.json'},{'native_result.json','context.json','python_packages.txt'},{'native_result.json','context.json','python_packages.txt','upstream_uv.lock'})
  if not isinstance(mf,dict) or set(mf) not in allowed:
   errors.append('UNEXPECTED_ARTIFACT_FILE_SET')
  else:
   for name,expected in mf.items():
    if sha(out/name)!=expected:errors.append('ARTIFACT_HASH_MISMATCH:'+name)
   if set(x.name for x in out.iterdir() if x.is_file())!=set(mf)|{'SHA256_MANIFEST.json'}:errors.append('EXTRA_ARTIFACT_FILES')
  n=readj(out/'native_result.json');c=readj(out/'context.json')
  if c.get('schema')!='ETB_GITHUB_NATIVE_CONTEXT_v080':errors.append('CONTEXT_SCHEMA')
  if n.get('status')!='NATIVE_EFFECT_DEVELOPMENT_PREFLIGHT_PASS_ROOT_UNVERIFIED':errors.append('NATIVE_STATUS')
  if n.get('git_commit')!=PIN or c.get('source_commit')!=PIN or n.get('source_q0_sha256')!=Q0_SHA or c.get('q0_sha256')!=Q0_SHA:errors.append('SOURCE_PIN')
  if c.get('freeze_sha256')!=sha(Path(__file__).resolve().parents[1]/'protocol/freeze_v080.json'):errors.append('FREEZE_HASH')
  if c.get('native_report_sha256')!=sha(out/'native_result.json'):errors.append('NATIVE_HASH')
  if c.get('run_mode')=='GITHUB_CONTEXT_SELF_REPORTED':
   if not c.get('upstream_uv_lock_sha256') or not c.get('pip_freeze_sha256') or c.get('dependency_strategy')!='UPSTREAM_UV_FROZEN' or c.get('uv_version_pinned')!='0.13.9':errors.append('GITHUB_LOCK_EVIDENCE_MISSING')
  if 'upstream_uv_lock_sha256' in c and c['upstream_uv_lock_sha256']!=sha(out/'upstream_uv.lock'):errors.append('UPSTREAM_LOCK_HASH')
  if 'pip_freeze_sha256' in c and c['pip_freeze_sha256']!=sha(out/'python_packages.txt'):errors.append('PIP_HASH')
  if n.get('task_id')!=f['task_id']:errors.append('TASK_SCOPE')
  if c.get('native_agent_calls')!=0 or c.get('independent_root_verified') is not False or c.get('q1_status')!='Q1_BLOCKED' or c.get('confirmatory_eligible') is not False:errors.append('CLAIM_ESCALATION')
  if n.get('native_sut_executed') is not False or n.get('independent_root_verified') is not False or n.get('confirmatory_eligible') is not False:errors.append('NATIVE_CLAIM_ESCALATION')
  for tag in ('known_no_write','known_write'):
   if n.get('controls',{}).get(tag,{}).get('pass') is not True:errors.append('CONTROL_'+tag)
  if n.get('controls',{}).get('known_write',{}).get('state_effect_detectable') is not True:errors.append('NATIVE_EFFECT_NOT_DETECTABLE')
  if c.get('native_validation_status')!='PASS' or c.get('issues'):errors.append('NATIVE_CONTEXT_BLOCKED')
 except (FileNotFoundError,ValueError,TypeError,KeyError,IsADirectoryError) as e:
  errors.append('INVALID_ARTIFACT:'+type(e).__name__+':'+str(e)[:100])
 return sorted(set(errors))
