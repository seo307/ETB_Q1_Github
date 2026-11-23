#!/usr/bin/env python3
"""Source-scoped native DB semantic qualification, with authored negative controls.
Runs only against the exact pinned τ² source. No agent/model calls.
All cases share one native implementation and are NOT independent semantic truth.
"""
from __future__ import annotations
import argparse,copy,json,platform,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'native_original'))
from etb_github.contract import freeze_check,git_checked,sha
from etb_github.q1b import PIN,check_reference,expected_observations,classify_native,read_json,json_bytes,audit_result
from native_airline_effect_probe import _native_import

def require(predicate,reason):
 if not predicate:raise RuntimeError(reason)

def baseline_env(get_environment,task):
 e=get_environment(); init=task.initial_state
 e.set_state(initialization_data=init.initialization_data if init else None,
             initialization_actions=init.initialization_actions if init else None,
             message_history=list(init.message_history or []) if init else [],strict=True)
 return e

def transition_checks(baseline,final,booking_action):
 """Supplemental native structural checks; same DB trust root as native evaluator."""
 from collections import Counter
 a=booking_action.arguments
 b=baseline.tools.db; f=final.tools.db
 before=set(b.reservations);after=set(f.reservations)
 created=sorted(after-before)
 require(len(created)==1,'CREATED_RESERVATION_COUNT_NOT_ONE')
 r=f.reservations[created[0]]
 uid=r.user_id
 expected_seats=Counter((leg['flight_number'],leg['date']) for leg in a['flights'])
 count=len(a['passengers']);cabin=a['cabin']
 seats=True
 for (flight,date),n in expected_seats.items():
  bef=b.flights[flight].dates[date].available_seats[cabin]
  aft=f.flights[flight].dates[date].available_seats[cabin]
  seats &= bef-aft == n*count
 return {
  'one_new_reservation':len(created)==1,
  'reservation_user_matches_book_argument':uid==a['user_id'],
  'user_reservation_link_created':created[0] in f.users[uid].reservations and created[0] not in b.users[uid].reservations,
  'flight_segments_match_request':[(x.flight_number,x.date) for x in r.flights]==[(x['flight_number'],x['date']) for x in a['flights']],
  'passenger_count_matches':len(r.passengers)==count,
  'requested_cabin_matches':r.cabin==cabin,
  'seat_inventory_decrement_matches':bool(seats),
  'no_preexisting_reservations_removed':before.issubset(after),
 }

def native_qualify(checkout):
 root=ROOT
 _,fi=freeze_check();require(not fi,'V080_FREEZE_INVALID:'+','.join(fi))
 require(not check_reference(root),'V080_REFERENCE_INVALID')
 require((3,12)<=sys.version_info[:2]<(3,14),'PYTHON_REQUIRES_3_12_TO_3_13')
 git_checked(checkout)
 get_environment,get_tasks,import_path=_native_import(checkout)
 from tau2.data_model.message import ToolCall,AssistantMessage
 from tau2.evaluator.evaluator_env import EnvironmentEvaluator
 task=next((t for t in get_tasks('base') if str(t.id)=='8'),None)
 require(task is not None,'NATIVE_TASK_8_MISSING')
 ec=task.evaluation_criteria;require(ec is not None,'NO_NATIVE_EVALUATION_CRITERIA')
 reward_basis=[x.value if hasattr(x,'value') else str(x) for x in ec.reward_basis]
 require(reward_basis==['DB','COMMUNICATE'],'NATIVE_REWARD_BASIS_DRIFT')
 acts=ec.actions or []
 require(len(acts)==4,'REFERENCE_COUNT_DRIFT')
 require([a.name for a in acts]==['get_user_details','get_reservation_details','search_direct_flight','book_reservation'],'REFERENCE_SEQUENCE_DRIFT')
 require(all(a.requestor=='assistant' for a in acts),'UNSUPPORTED_USER_GOLD_ACTION')
 blank=baseline_env(get_environment,task)
 expected=baseline_env(get_environment,task)
 history=list(task.initial_state.message_history or []) if task.initial_state else []
 # Generate a real native response and corresponding tool-call pair, not fabricated output.
 for idx,act in enumerate(acts):
  tc=ToolCall(id=f'q1b-native-task8-{idx}',name=act.name,arguments=copy.deepcopy(act.arguments),requestor=act.requestor)
  response=expected.get_response(tc)
  require(response.error is False,'GOLD_ACTION_NATIVE_TOOL_ERROR:'+act.name)
  history.append(AssistantMessage.text('',tool_calls=[tc]))
  history.append(response)
 target=expected.get_db_hash();baseline=blank.get_db_hash()
 ref=read_json(root/'evidence/v080_run45085918830/native_result.json')
 require(baseline==ref['controls']['known_no_write']['initial_hash'],'BASELINE_PINNED_HASH_DRIFT')
 require(target==ref['controls']['known_write']['gold_db_hash'],'GOLD_PINNED_HASH_DRIFT')
 require(baseline!=target,'GOLD_EFFECT_NOT_DETECTABLE')
 def evaluate(trajectory,strict=True):
  ri=EnvironmentEvaluator.calculate_reward(environment_constructor=get_environment,task=task,
              full_trajectory=trajectory,solo_mode=False,strict_replay=strict)
  ch=ri.db_check
  require(ch is not None,'NATIVE_DB_CHECK_MISSING')
  return {'db_match':bool(ch.db_match),'db_reward':float(ch.db_reward),
          'env_reward':float(ri.reward),'reward_basis':reward_basis}
 cases={}
 cases['no_write']=evaluate(list(task.initial_state.message_history or []) if task.initial_state else [])
 cases['gold_path']=evaluate(copy.deepcopy(history))
 cases['omitted_write']=evaluate(copy.deepcopy(history[:-2]))
 rejected=copy.deepcopy(history);rejected[-1].error=True;rejected[-1].execution_status='rejected'
 rejected[-1].content='Rejected by policy before execution'
 cases['rejected_write']=evaluate(rejected)
 tampered=copy.deepcopy(history);tampered[-1].content='{"forged":true,"false_result":"success"}'
 # strict=True must fail rather than silently accept altered tool receipt.
 strict_tamper='NOT_REJECTED'
 try:evaluate(tampered,strict=True)
 except ValueError as exc:
  message=str(exc)
  if all(token in message for token in ('Tool call:', 'Returned:', 'Expected:')):
   strict_tamper='REJECTED_STRICT_REPLAY'
  else:
   raise RuntimeError('UNRELATED_STRICT_EVALUATOR_ERROR') from exc
 cases['tampered_tool_output_lenient']=evaluate(tampered,strict=False)
 structured=transition_checks(blank,expected,acts[-1])
 result={'schema':'ETB_Q1B_NATIVE_SEMANTIC_v081','task_id':'8','source_commit':PIN,
         'upstream_import_sha256':sha(import_path),'task_reward_basis_scope':'DB_COMPONENT_ONLY',
         'reward_basis':reward_basis,'reference_actions_count':len(acts),
         'baseline_db_hash':baseline,'target_db_hash':target,
         'cases':cases,'structured_transition':structured,'strict_tamper':strict_tamper,
         'model_calls':0,'independent_root_verified':False,'q1_status':'Q1_BLOCKED',
         'confirmatory_eligible':False,'process_assurance':'NOT_CERTIFIED',
         'full_task_success':'NOT_EVALUATED_COMMUNICATE_NOT_EXECUTED',
         'semantic_oracle_independence':'NONE_NATIVE_IMPLEMENTATION_COUPLED',
         'development_case_scope':'AUTHOR_CONTROLLED_TASK8_NO_MODEL',
         'overall':'SOURCE_SCOPED_Q1B_DEVELOPMENT_PASS'}
 issues=audit_result(result,root)
 require(not issues,'Q1B_ORACLE_CONTRACT_FAIL:'+','.join(issues))
 return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--checkout',required=True);ap.add_argument('--out-dir',required=True)
 ap.add_argument('--pip-freeze',required=True);ap.add_argument('--upstream-lock',required=True)
 a=ap.parse_args();out=Path(a.out_dir)
 if out.exists():print('Q1B_REFUSE_OVERWRITE');return 2
 out.mkdir(parents=True)
 try:
  result=native_qualify(Path(a.checkout).resolve())
  (out/'native_semantic.json').write_bytes(json_bytes(result))
  # json_bytes and sha are module-scoped imports above. Never shadow them here.
  lock=Path(a.upstream_lock);freeze=Path(a.pip_freeze)
  require(lock.name=='uv.lock' and lock.is_file(),'FROZEN_LOCK_MISSING')
  require(freeze.is_file(),'PIP_FREEZE_MISSING')
  (out/'upstream_uv.lock').write_bytes(lock.read_bytes())
  (out/'python_packages.txt').write_bytes(freeze.read_bytes())
  from etb_github.q1b import V080_SHA,V080_ART_SHA
  import os
  github={k:os.environ.get(k) for k in ('GITHUB_ACTIONS','GITHUB_REPOSITORY','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT','GITHUB_SHA','GITHUB_EVENT_NAME','RUNNER_OS','RUNNER_ARCH')}
  context={'schema':'ETB_Q1B_GITHUB_CONTEXT_v081','source_commit':PIN,
           'github':github,'run_mode':'GITHUB_CONTEXT_SELF_REPORTED' if github['GITHUB_ACTIONS']=='true' else 'LOCAL_DEVELOPMENT',
           'native_result_sha256':sha(out/'native_semantic.json'),'upstream_uv_lock_sha256':sha(out/'upstream_uv.lock'),
           'python_packages_sha256':sha(out/'python_packages.txt'),
           'reference_v080_run_id':'45085918830','reference_v080_commit':V080_SHA,
           'reference_v080_artifact_sha256':V080_ART_SHA,
           'platform':platform.system(),'python_version':platform.python_version(),
           'independent_root_verified':False,'q1_status':'Q1_BLOCKED','confirmatory_eligible':False}
  (out/'context.json').write_bytes(json_bytes(context))
  files={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}
  (out/'SHA256_MANIFEST.json').write_bytes(json_bytes(files))
  print(json.dumps({'status':result['overall'],'native_controls':list(result['cases']),
                    'issues':[],'q1_status':'Q1_BLOCKED'},indent=2))
  return 0
 except Exception as exc:
  error={'status':'Q1B_NATIVE_BLOCKED','exception_type':type(exc).__name__,'reason':str(exc)[:220],
         'q1_status':'Q1_BLOCKED','confirmatory_eligible':False}
  (out/'FAILURE.json').write_bytes(json_bytes(error))
  print(json.dumps(error,indent=2));return 2
if __name__=='__main__':raise SystemExit(main())
