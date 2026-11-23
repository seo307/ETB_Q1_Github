#!/usr/bin/env python3
"""Combine independently acquired GitHub run/jobs metadata with self-reported native case receipt."""
from pathlib import Path
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from etb_github.q1b import verify_result_directory,read_json,json_bytes

def evaluate(run,jobs,artifact_dir,root):
 issues=verify_result_directory(artifact_dir,root)
 try:
  c=read_json(Path(artifact_dir)/'context.json'); g=c['github']
  if g.get('GITHUB_ACTIONS')!='true' or g.get('GITHUB_EVENT_NAME')!='workflow_dispatch':issues.append('GITHUB_CONTEXT')
  if g.get('GITHUB_REPOSITORY')!='seo307/ETB_Q1_Github':issues.append('GITHUB_REPO_UNEXPECTED')
  if run.get('repository',{}).get('full_name')!=g.get('GITHUB_REPOSITORY'):issues.append('REPOSITORY_MISMATCH')
  if str(run.get('id'))!=g.get('GITHUB_RUN_ID') or str(run.get('run_attempt'))!=g.get('GITHUB_RUN_ATTEMPT'):issues.append('RUN_ID_ATTEMPT_MISMATCH')
  if run.get('head_sha')!=g.get('GITHUB_SHA'):issues.append('GITHUB_SHA_MISMATCH')
  if run.get('event')!='workflow_dispatch' or run.get('status')!='completed' or run.get('conclusion')!='success':issues.append('RUN_NOT_SUCCESSFUL')
  if run.get('path','').split('@')[0]!='.github/workflows/etb-q1b-native-semantic.yml':issues.append('RUN_WRONG_WORKFLOW')
  jb=[x for x in jobs.get('jobs',[]) if x.get('name')=='q1b-native-semantic']
  if len(jb)!=1:issues.append('EXPECTED_JOB_NOT_UNIQUE')
  else:
   j=jb[0]
   if j.get('run_id')!=run.get('id') or j.get('conclusion')!='success' or j.get('status')!='completed':issues.append('JOB_NOT_SUCCESS')
   if 'ubuntu-24.04' not in j.get('labels',[]) or 'self-hosted' in j.get('labels',[]):issues.append('RUNNER_LABEL')
  if jobs.get('total_count')!=len(jobs.get('jobs',[])) or jobs.get('total_count',0)>100:issues.append('JOB_LIST_TRUNCATED')
 except (AttributeError,KeyError,TypeError,ValueError,OSError) as e:issues.append('GITHUB_RESULT_MALFORMED:'+type(e).__name__)
 issues=sorted(set(issues))
 return {'status':'GITHUB_Q1B_NATIVE_SEMANTIC_CORROBORATED' if not issues else 'GITHUB_Q1B_NATIVE_SEMANTIC_BLOCKED',
         'issues':issues,'native_db_component_qualified':not issues,'native_full_task_reward_verified':False,
         'native_llm_agent_runs':0,'independent_semantic_oracle_verified':False,
         'independent_admin_root_verified':False,'q1_status':'Q1_BLOCKED','confirmatory_eligible':False}

def main():
 p=argparse.ArgumentParser();p.add_argument('--run-json',required=True);p.add_argument('--jobs-json',required=True)
 p.add_argument('--artifact-dir',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 out=Path(a.out)
 if out.exists():p.error('REFUSE_OVERWRITE')
 try:x=evaluate(read_json(a.run_json),read_json(a.jobs_json),a.artifact_dir,Path(__file__).resolve().parents[1])
 except (OSError,ValueError,TypeError) as e:x={'status':'GITHUB_Q1B_NATIVE_SEMANTIC_BLOCKED','issues':['LOAD_ERROR:'+type(e).__name__], 'q1_status':'Q1_BLOCKED'}
 out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(json_bytes(x));print(json.dumps(x,indent=2))
 return 0 if x['status']=='GITHUB_Q1B_NATIVE_SEMANTIC_CORROBORATED' else 2
if __name__=='__main__':raise SystemExit(main())
