"""Cross-check an independently retrieved GitHub workflow-run record with the source-scoped native artifact.

This is an external execution corroboration, not independent administrative-root assurance.
"""
from __future__ import annotations
from pathlib import Path
from .contract import PIN,WORKFLOW,readj,valid_sha
from .validate import check_artifact

def assess(run,jobs,native_dir):
 problems=list(check_artifact(native_dir))
 try:
  context=readj(Path(native_dir)/'context.json'); g=context['github']
  if context.get('run_mode')!='GITHUB_CONTEXT_SELF_REPORTED' or g.get('GITHUB_ACTIONS')!='true':problems.append('CONTEXT_NOT_GITHUB')
  if g.get('GITHUB_EVENT_NAME')!='workflow_dispatch':problems.append('EVENT_CONTEXT_UNEXPECTED')
  if g.get('GITHUB_SERVER_URL')!='https://github.com':problems.append('SERVER_UNEXPECTED')
  if g.get('RUNNER_OS')!='Linux' or g.get('RUNNER_ARCH')!='X64':problems.append('RUNNER_CONTEXT_UNEXPECTED')
  if not isinstance(run,dict) or not isinstance(jobs,dict):raise ValueError('API_OBJECT_TYPE')
  repo=(run.get('repository') or {}).get('full_name')
  if not isinstance(repo,str) or repo!=g.get('GITHUB_REPOSITORY'):problems.append('REPOSITORY_SCOPE_MISMATCH')
  if not isinstance(run.get('id'),int) or str(run['id'])!=g.get('GITHUB_RUN_ID'):problems.append('RUN_ID_MISMATCH')
  if not isinstance(run.get('run_attempt'),int) or str(run['run_attempt'])!=g.get('GITHUB_RUN_ATTEMPT'):problems.append('RUN_ATTEMPT_MISMATCH')
  if not valid_sha(run.get('head_sha')) or run.get('head_sha')!=g.get('GITHUB_SHA'):problems.append('WORKFLOW_SHA_MISMATCH')
  if run.get('event')!='workflow_dispatch':problems.append('API_EVENT_NOT_DISPATCH')
  if run.get('status')!='completed' or run.get('conclusion')!='success':problems.append('RUN_NOT_SUCCESSFUL')
  # Path in workflow-run API may include @ref suffix.
  if not isinstance(run.get('path'),str) or run['path'].split('@')[0]!=WORKFLOW:problems.append('WORKFLOW_PATH_MISMATCH')
  if not isinstance(g.get('GITHUB_WORKFLOW_REF'),str) or not g['GITHUB_WORKFLOW_REF'].startswith(repo+'/'+WORKFLOW+'@'):problems.append('WORKFLOW_REF_MISMATCH')
  found=[]
  for job in jobs.get('jobs',[]):
   if not isinstance(job,dict):continue
   name=job.get('name')
   if name=='native-preflight':found.append(job)
  if len(found)!=1:problems.append('EXPECTED_JOB_NOT_UNIQUE')
  else:
   j=found[0]
   if j.get('status')!='completed' or j.get('conclusion')!='success':problems.append('NATIVE_JOB_NOT_SUCCESSFUL')
   if j.get('run_id')!=run.get('id'):problems.append('JOB_RUN_ID_MISMATCH')
   labels=j.get('labels')
   if not isinstance(labels,list) or 'ubuntu-24.04' not in labels or 'self-hosted' in labels:problems.append('HOSTED_RUNNER_LABEL_NOT_VERIFIED')
   if not j.get('runner_name'):problems.append('RUNNER_NAME_MISSING')
  if jobs.get('total_count')!=len(jobs.get('jobs',[])) or jobs.get('total_count',0)>100:problems.append('JOB_API_PAGINATION_INCOMPLETE')
 except (TypeError,ValueError,KeyError,AttributeError) as e:problems.append('INVALID_GITHUB_API:'+str(e)[:120])
 problems=sorted(set(problems))
 return {'schema':'ETB_GITHUB_RUN_AUDIT_v080',
  'status':'GITHUB_HOSTED_NATIVE_PREFLIGHT_CORROBORATED' if not problems else 'GITHUB_NATIVE_PREFLIGHT_BLOCKED',
  'external_runner_corroborated':not problems,
  'native_reference_replay_source_scoped':not problems,
  'independent_effect_oracle_verified':False,
  'independent_administrative_root_verified':False,
  'latest_checkpoint_external_root_verified':False,
  'native_llm_agent_runs':0,'q1_status':'Q1_BLOCKED','q2_confirmatory_eligible':False,
  'issues':problems}
