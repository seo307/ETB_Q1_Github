#!/usr/bin/env python3
"""Local, source-native Airline *development preflight*, NOT an independent observer.

Uses tau2's original Environment/Task methods in the user's pinned checkout.
No LLM SUT, no tool output scoring, and no independent-root attestation.
Writes only a JSON report; reference tool calls mutate a newly created in-memory env.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys,traceback
from pathlib import Path

COMMIT='c06b07dd7c4d4ec61ba6ff9bcdf0b15dd7ef36d4'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def git_head(repo):
    r=subprocess.run(['git','-C',str(repo),'rev-parse','HEAD'],capture_output=True,text=True,timeout=15)
    if r.returncode:raise RuntimeError('git rev-parse HEAD failed')
    return r.stdout.strip()

def _ensure_pinned_import(repo:Path):
    """Prepend the verified checkout's src tree; never silently load ambient tau2.

    This solves src-layout module discovery, not dependency installation, native
    environment validity, or ETB observer-root independence.
    """
    src=(repo/'src').resolve()
    if not (src/'tau2'/'__init__.py').is_file():
        raise RuntimeError('PINNED_TAU2_SOURCE_LAYOUT_MISSING')
    if str(src) in sys.path:
        sys.path.remove(str(src))
    sys.path.insert(0,str(src))
    return src


def _native_import(repo:Path):
    import importlib
    src=_ensure_pinned_import(repo)
    importlib.invalidate_caches()
    import tau2
    pkg=Path(getattr(tau2,'__file__','') or '/nonexistent').resolve()
    if not pkg.is_relative_to(src/'tau2'):
        raise RuntimeError('TAU2_MODULE_NOT_FROM_PINNED_CHECKOUT:'+str(pkg))
    from tau2.domains.airline.environment import get_environment,get_tasks
    return get_environment,get_tasks,str(pkg)

def generate(repo:Path,q0:Path,task_id:str='8'):
    result={'status':'NATIVE_EFFECT_PROBE_BLOCKED','task_id':task_id,'git_commit':None,'source_q0_sha256':sha(q0),
        'native_sut_executed':False,'independent_root_verified':False,'confirmatory_eligible':False,
        'controls':{},'reference_action_log':[],
        'qualification_limit':'Gold action replay and native hash are from same tau2 in-memory implementation. This is not independent ETB ground truth.'}
    census=json.loads(q0.read_text(encoding='utf8'))
    if census.get('status')!='Q0_LOCAL_SOURCE_PIN_VERIFIED_Q1_STILL_REQUIRED' or census.get('issues') or census.get('head')!=COMMIT:
        result['error']='Q0_NOT_VERIFIED';return result
    head=git_head(repo);result['git_commit']=head
    if head!=COMMIT:result['error']='PIN_MISMATCH';return result
    if task_id not in census.get('airline_base_ids',[]):result['error']='TASK_NOT_IN_Q0';return result
    result['python_executable']=sys.executable
    result['python_version']='.'.join(map(str,sys.version_info[:3]))
    if not ((3,12)<=sys.version_info[:2]<(3,14)):
        result['error']='UNSUPPORTED_PYTHON_VERSION_REQUIRES_3_12_TO_3_13';return result
    try:
        get_environment,get_tasks,import_location=_native_import(repo)
        result['imported_tau2_location']=import_location
    except Exception as e:
        result['error']='NATIVE_IMPORT_FAILED:'+type(e).__name__+':'+str(e)[:180];return result
    tasks={str(t.id):t for t in get_tasks('base')}
    task=tasks.get(task_id)
    if task is None:result['error']='NATIVE_TASK_NOT_FOUND';return result
    try:
        init=task.initial_state
        initdata=init.initialization_data if init else None
        initactions=init.initialization_actions if init else None
        initmessages=init.message_history if init and init.message_history else []
        def env0():
            e=get_environment()
            e.set_state(initialization_data=initdata,initialization_actions=initactions,
                        message_history=list(initmessages),strict=True)
            return e
        initial=env0();initial_hash=initial.get_db_hash();initial_user_hash=initial.get_user_db_hash()
        control=env0();control_hash=control.get_db_hash();control_user_hash=control.get_user_db_hash()
        stable=(initial_hash is not None and initial_hash==control_hash and initial_user_hash==control_user_hash)
        result['controls']['known_no_write']={'test':'repeatable_initial_state','pass':bool(stable),
            'initial_hash':initial_hash,'repeat_hash':control_hash,'user_hash_equal':initial_user_hash==control_user_hash}
        expected=env0(); gold_actions=task.evaluation_criteria.actions or []
        for i,a in enumerate(gold_actions):
            try:
                expected.make_tool_call(tool_name=a.name,requestor=a.requestor,**a.arguments)
                result['reference_action_log'].append({'ordinal':i,'name':a.name,'status':'NATIVE_REPLAY_CALLED'})
            except Exception as exc:
                result['reference_action_log'].append({'ordinal':i,'name':a.name,'status':'NATIVE_REPLAY_EXCEPTION','exception_type':type(exc).__name__})
                result['error']='REFERENCE_REPLAY_EXCEPTION';result['controls']['known_write']={'pass':False,'tested':False};return result
        target=expected.get_db_hash(); target_user=expected.get_user_db_hash()
        changed=(target!=initial_hash or target_user!=initial_user_hash)
        result['controls']['known_write']={'test':'reference_replay_changes_native_db_state',
            'pass':bool(changed and stable),'tested':True,
            'baseline_db_hash':initial_hash,'gold_db_hash':target,
            'baseline_user_hash':initial_user_hash,'gold_user_hash':target_user,
            'reference_actions_count':len(gold_actions),
            'state_effect_detectable':bool(changed)}
        result['status']='NATIVE_EFFECT_DEVELOPMENT_PREFLIGHT_PASS_ROOT_UNVERIFIED' if changed and stable else 'NATIVE_EFFECT_INDETERMINATE_ROOT_UNVERIFIED'
    except Exception as e:
        result['error']='NATIVE_RUNTIME_FAILURE:'+type(e).__name__+':'+str(e)[:160]
        result['status']='NATIVE_EFFECT_PROBE_BLOCKED'
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--checkout',type=Path,required=True)
    ap.add_argument('--q0',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--task-id',default='8');a=ap.parse_args()
    d=generate(a.checkout.resolve(),a.q0.resolve(),a.task_id)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print(json.dumps({k:d.get(k) for k in ('status','task_id','error','independent_root_verified','confirmatory_eligible')},indent=2))
    return 0 if d['status']=='NATIVE_EFFECT_DEVELOPMENT_PREFLIGHT_PASS_ROOT_UNVERIFIED' else 2
if __name__=='__main__':raise SystemExit(main())
