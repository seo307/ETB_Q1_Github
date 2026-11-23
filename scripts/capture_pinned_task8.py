#!/usr/bin/env python3
"""Native τ² Task 8 state projection, original in-memory engine; no agent/model/API writes.

The capture program trusts native tau2 data; it cannot establish independent root.
DO NOT edit upstream checkout or native evaluator. Only fresh result directory is written.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from etb_q1e.core import (PIN,USER,FLIGHT,DATE,CERTIFICATE,AMOUNT,SCHEMA,TASK,
                        canonical,file_sha,passenger_digest,verify_bundle,CERT,CLAIMS)

EXPECTED_NAMES=['get_user_details','get_reservation_details','search_direct_flight','book_reservation']
# Archived Q1B source-scoped native hashes, not independently certified ground truth.
Q1B_BASELINE_HASH='124e39a664b56402bcd09cb8a6a9cece6acb8462337c969799d5658e3250f263'
Q1B_TARGET_HASH='00766aa3e0341b497a623f93983c8d951b8d48ad541a15123a1e2b902e644a82'
EXPECTED_BOOK={
 'user_id':USER,'origin':'ORD','destination':'PHL','flight_type':'one_way','cabin':'economy',
 'flights':[{'flight_number':FLIGHT,'date':DATE}],
 'passengers':[
    {'first_name':'Sophia','last_name':'Silva','dob':'1957-10-05'},
    {'first_name':'Kevin','last_name':'Smith','dob':'2001-04-12'},
 ],
 'payment_methods':[{'payment_id':CERTIFICATE,'amount':AMOUNT}],
 'total_baggages':0,'nonfree_baggages':0,'insurance':'no'
}

def stop_if(condition,code):
    if not condition:raise RuntimeError(code)

def project(e,pre_db,phase,bind):
    db=e.tools.db
    user=db.users[USER]
    f=db.flights[FLIGHT].dates[DATE]
    # No customer address, profile email, full payment records, passenger plaintext or DOB.
    pay={}
    if CERTIFICATE in user.payment_methods:
        p=user.payment_methods[CERTIFICATE]
        pay[CERTIFICATE]={'source':p.source,'amount':p.amount}
    previous=set(pre_db.reservations)
    curr=set(db.reservations)
    added=curr-previous
    if phase=='pre':stop_if(not added,'PRE_ALREADY_MODIFIED')
    if phase=='post':stop_if(len(added)==1,'UNSUPPORTED_POST_RESERVATION_CARDINALITY')
    reservation=None
    if phase=='post':
        x=db.reservations[next(iter(added))]
        reservation={
            'reservation_id':x.reservation_id,'user_id':x.user_id,'origin':x.origin,
            'destination':x.destination,'flight_type':x.flight_type,'cabin':x.cabin,
            'flights':[{'flight_number':y.flight_number,'date':y.date} for y in x.flights],
            'passenger_count':len(x.passengers),
            'passenger_digests':sorted(passenger_digest(z.first_name,z.last_name,z.dob) for z in x.passengers),
            'payment_history':[{'payment_id':y.payment_id,'amount':y.amount} for y in x.payment_history],
            'total_baggages':x.total_baggages,'nonfree_baggages':x.nonfree_baggages,
            'insurance':x.insurance,
        }
    return {'schema':SCHEMA,'source_pin':PIN,'task_id':TASK,
            'capture_origin':'PINNED_NATIVE_RUNTIME','phase':phase,
            'observation_index':0 if phase=='pre' else 1,
            'nonce':bind,'run_binding':bind,
            'state':{'reservation_ids':sorted(curr),
                     'user_reservation_ids':list(user.reservations),
                     'flight':{'flight_number':FLIGHT,'date':DATE,'cabin':'economy',
                               'seats':f.available_seats['economy'],'unit_price':f.prices['economy']},
                     'payment_methods':pay,'new_reservation':reservation}}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--checkout',required=True)
    ap.add_argument('--out-dir',required=True)
    ap.add_argument('--run-binding',required=True)
    args=ap.parse_args()
    out=Path(args.out_dir)
    if out.exists():raise SystemExit('REFUSE_OVERWRITE:'+str(out))
    if not args.run_binding.startswith('Q1E_NATIVE_') or len(args.run_binding)>140:
        raise SystemExit('INVALID_RUN_BINDING')
    repo=Path(args.checkout).resolve()
    head=subprocess.run(['git','-C',str(repo),'rev-parse','HEAD'],capture_output=True,text=True,check=True,timeout=20).stdout.strip()
    stop_if(head==PIN,'UPSTREAM_COMMIT_PIN_MISMATCH')
    stop_if((repo/'src/tau2/__init__.py').is_file(),'UPSTREAM_SOURCE_LAYOUT')
    sys.path.insert(0,str(repo/'src'))
    from tau2.domains.airline.environment import get_environment,get_tasks
    from tau2.data_model.message import ToolCall
    import tau2
    stop_if(Path(tau2.__file__).resolve().is_relative_to(repo/'src/tau2'),'IMPORTED_WRONG_TAU2')
    task=next((x for x in get_tasks('base') if str(x.id)==TASK),None)
    stop_if(task is not None,'TASK8_NOT_FOUND')
    acts=task.evaluation_criteria.actions or []
    stop_if([x.name for x in acts]==EXPECTED_NAMES,'REFERENCE_ACTION_LIST_DRIFT')
    stop_if(acts[0].arguments=={'user_id':USER},'TASK8_USER_DRIFT')
    stop_if(acts[1].arguments=={'reservation_id':'WUNA5K'},'TASK8_PRIOR_RESERVATION_DRIFT')
    stop_if(acts[2].arguments=={'origin':'ORD','destination':'PHL','date':DATE},'TASK8_FLIGHT_SEARCH_DRIFT')
    stop_if(acts[3].arguments==EXPECTED_BOOK,'TASK8_BOOK_ARGUMENT_DRIFT')
    stop_if([x.value if hasattr(x,'value') else str(x) for x in task.evaluation_criteria.reward_basis]==['DB','COMMUNICATE'], 'REWARD_SCOPE_DRIFT')
    def baseline():
        e=get_environment();initial=task.initial_state
        e.set_state(initialization_data=initial.initialization_data if initial else None,
                    initialization_actions=initial.initialization_actions if initial else None,
                    message_history=list(initial.message_history or []) if initial else [],strict=True)
        return e
    before=baseline();after=baseline()
    baseline_hash=before.get_db_hash()
    stop_if(baseline_hash==Q1B_BASELINE_HASH,'Q1B_ARCHIVED_BASELINE_DB_DRIFT')
    prev=copy.deepcopy(before.tools.db)
    pre=project(before,prev,'pre',args.run_binding)
    for i,a in enumerate(acts):
        call=ToolCall(id=f'q1e-source-task8-{i}',name=a.name,arguments=copy.deepcopy(a.arguments),requestor=a.requestor)
        response=after.get_response(call)
        stop_if(response.error is False,'REFERENCE_ACTION_NATIVE_ERROR:'+a.name)
    post=project(after,prev,'post',args.run_binding)
    post_hash=after.get_db_hash()
    stop_if(post_hash==Q1B_TARGET_HASH,'Q1B_ARCHIVED_TARGET_DB_DRIFT')
    bundle=out/'bundle';bundle.mkdir(parents=True)
    (bundle/'pre.json').write_bytes(canonical(pre))
    (bundle/'post.json').write_bytes(canonical(post))
    (bundle/'MANIFEST.sha256.json').write_bytes(canonical({'pre.json':file_sha(bundle/'pre.json'),'post.json':file_sha(bundle/'post.json')}))
    assessment=verify_bundle(bundle)
    stop_if(not assessment['issues'],'NATIVE_PAIR_MALFORMED')
    stop_if(all(assessment['assessment']['claims'][c]['status']==CERT for c in CLAIMS[:3]),'NATIVE_WITNESS_OBLIGATION_NOT_MET')
    native={'schema':'ETB_Q1E_NATIVE_RECEIPT_v094','source_pin':PIN,'task_id':TASK,
            'source_git_head':head,
            'archived_native_baseline_hash_correlated':baseline_hash,
            'archived_native_target_hash_correlated':post_hash,
            'same_root_native_hash_comparison':True,
            'github_run_id':os.environ.get('GITHUB_RUN_ID','LOCAL'),
            'github_sha_self_reported':os.environ.get('GITHUB_SHA','LOCAL'),
            'pre_sha256':file_sha(bundle/'pre.json'),'post_sha256':file_sha(bundle/'post.json'),
            'bundle_verifier':assessment['status'],
            'capture_authoritative_independence':'NONE_SHARED_TAU2_DB_ROOT',
            'task_reward_basis_scope':'DB_COMPONENT_ONLY','full_task_communicate_evaluated':False,
            'model_calls':0,'q1_status':'Q1_BLOCKED','q2_confirmatory_eligible':False}
    (out/'native_receipt.json').write_bytes(canonical(native))
    print(json.dumps({'status':'NATIVE_TASK8_WITNESS_CAPTURE_SOURCE_SCOPED_ONLY',
                     'claim_statuses':{k:v['status'] for k,v in assessment['assessment']['claims'].items()},
                     'q1_status':'Q1_BLOCKED','issues':[]},indent=2))
    return 0
if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (RuntimeError,ValueError,KeyError,TypeError,OSError,subprocess.CalledProcessError) as exc:
        error={'schema':'ETB_Q1E_NATIVE_FAILURE_v094','status':'NATIVE_CAPTURE_BLOCKED',
               'error_type':type(exc).__name__,'reason':str(exc)[:200],
               'q1_status':'Q1_BLOCKED','q2_confirmatory_eligible':False}
        if '--out-dir' in sys.argv:
            try:
                p=Path(sys.argv[sys.argv.index('--out-dir')+1])
                p.mkdir(parents=True,exist_ok=True)
                if not (p/'FAILURE.json').exists():
                    (p/'FAILURE.json').write_bytes(canonical(error))
            except (OSError,IndexError):pass
        print(json.dumps(error,indent=2))
        raise SystemExit(2)

