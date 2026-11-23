#!/usr/bin/env python3
"""Frozen native task-8 tool-sequence qualification; no LLM and no tool source edits.

This program is for prospective GitHub hosted upstream native execution only.
Never pass its results off as independent effect or process authorization.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,os,subprocess,sys,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
# In the GitHub patch, etb_q1e/core.py from v0.9.4 must already be present.
from etb_q1e.core import (PIN,USER,FLIGHT,DATE,CERTIFICATE,SCHEMA,TASK,
  canonical,file_sha,passenger_digest,verdict,CERT,REJECT)
PLAN=ROOT/'protocol/native_execution_plan_v095.json'
Q1B_BASELINE='124e39a664b56402bcd09cb8a6a9cece6acb8462337c969799d5658e3250f263'
FROZEN_PLAN_SHA256='5a3e8481425e5722a0e85ae0be39f9646a7c386d797682b4de21aa7eb9f5c87a'
EXPECTED_NAMES=['get_user_details','get_reservation_details','search_direct_flight','book_reservation']

class Blocked(Exception):pass

def require(x,msg):
    if not x:raise Blocked(msg)

def expected_case_status(label):
    S='SUPPORTED_SOURCE_SCOPED'; C='CONTRADICTED'
    mapping={'C1_C2_C3_SUPPORTED':[S,S,S],
             'C1_C2_C3_CONTRADICTED':[C,C,C],
             'C1_SUPPORTED_C2_C3_CONTRADICTED':[S,C,C]}
    return mapping[label]

def frozen_sequences(gold_actions):
    """All deviations from gold are constructed from frozen original gold arguments."""
    names=[a.name for a in gold_actions]
    require(names==EXPECTED_NAMES,'GOLD_ACTION_NAMES_CHANGED')
    g=[(a.name,copy.deepcopy(a.arguments),a.requestor) for a in gold_actions]
    read=g[:3]
    book_name,book_args,book_requestor=g[3]
    require(book_args['user_id']==USER and book_args['flights']==[{'flight_number':FLIGHT,'date':DATE}],'BOOKING_CONTEXT_CHANGED')
    require(book_args['payment_methods']==[{'payment_id':CERTIFICATE,'amount':348}],'BOOKING_GOLD_PAYMENT_CHANGED')
    def new_book(changes):
        b=copy.deepcopy(book_args)
        b.update(copy.deepcopy(changes))
        return book_name,b,book_requestor
    seqs={
      'gold':g,
      'no_write':read,
      'bad_payment':read+[new_book({'payment_methods':[{'payment_id':CERTIFICATE,'amount':1}]})],
      'single_passenger':read+[new_book({'passengers':book_args['passengers'][:1],
                                         'payment_methods':[{'payment_id':CERTIFICATE,'amount':174}]})],
      'insurance':read+[new_book({'insurance':'yes',
                                  'payment_methods':[{'payment_id':CERTIFICATE,'amount':408}]})],
      'baggage':read+[new_book({'total_baggages':1,'nonfree_baggages':1,
                                'payment_methods':[{'payment_id':CERTIFICATE,'amount':398}]})],
      'split_certificates':read+[new_book({'payment_methods':[
          {'payment_id':CERTIFICATE,'amount':198},
          {'payment_id':'certificate_3887113','amount':150}]})],
      'book_only':[g[3]],
      'reordered_reads':[g[1],g[0],g[2],g[3]],
      'gold_plus_failed_read':g+[('get_user_details',{'user_id':'etb_unknown_user'},g[0][2])],
    }
    return seqs

def project(env,original_db,phase,bind):
    db=env.tools.db
    f=db.flights[FLIGHT].dates[DATE]
    user=db.users[USER]
    pre=set(original_db.reservations)
    current=set(db.reservations)
    new=sorted(current-pre)
    # This is not the Q1E gold-only extractor: no-write is a legitimate negative.
    rec=None
    if phase=='post' and len(new)==1:
        x=db.reservations[new[0]]
        rec={'reservation_id':x.reservation_id,'user_id':x.user_id,'origin':x.origin,
             'destination':x.destination,'flight_type':x.flight_type,'cabin':x.cabin,
             'flights':[{'flight_number':y.flight_number,'date':y.date} for y in x.flights],
             'passenger_count':len(x.passengers),
             'passenger_digests':sorted(passenger_digest(y.first_name,y.last_name,y.dob) for y in x.passengers),
             'payment_history':[{'payment_id':y.payment_id,'amount':y.amount} for y in x.payment_history],
             'total_baggages':x.total_baggages,'nonfree_baggages':x.nonfree_baggages,
             'insurance':x.insurance}
    pay={}
    if CERTIFICATE in user.payment_methods:
        v=user.payment_methods[CERTIFICATE]
        pay[CERTIFICATE]={'source':v.source,'amount':v.amount}
    return {'schema':SCHEMA,'source_pin':PIN,'task_id':TASK,'capture_origin':'PINNED_NATIVE_RUNTIME',
            'phase':phase,'observation_index':0 if phase=='pre' else 1,
            'nonce':bind,'run_binding':bind,
            'state':{'reservation_ids':sorted(current),'user_reservation_ids':list(user.reservations),
                     'new_reservation':rec,
                     'flight':{'flight_number':FLIGHT,'date':DATE,'cabin':'economy',
                               'seats':f.available_seats['economy'],'unit_price':f.prices['economy']},
                     'payment_methods':pay}}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--checkout',required=True);ap.add_argument('--out-dir',required=True)
    ap.add_argument('--run-binding',required=True)
    a=ap.parse_args()
    out=Path(a.out_dir)
    require(not out.exists(),'OUTPUT_EXISTS_NO_OVERWRITE')
    require(a.run_binding.startswith('Q1E_COUNTEREXAMPLE_') and len(a.run_binding)<120,'RUN_BINDING_INVALID')
    require(file_sha(PLAN)==FROZEN_PLAN_SHA256,'FROZEN_PLAN_SHA256_MISMATCH')
    p=json.loads(PLAN.read_bytes())
    require(p['source_commit']==PIN and p['task_id']==TASK,'FROZEN_PLAN_DRIFT')
    require(len(p['cases'])==10 and len({x['mode'] for x in p['cases']})==10,'PLAN_NOT_FROZEN_10_CASES')
    repo=Path(a.checkout).resolve()
    git=subprocess.run(['git','-C',str(repo),'rev-parse','HEAD'],capture_output=True,text=True,check=True,timeout=20).stdout.strip()
    require(git==PIN,'UPSTREAM_PIN_DRIFT')
    require((repo/'src/tau2/__init__.py').exists(),'UPSTREAM_LAYOUT_BAD')
    sys.path.insert(0,str(repo/'src'))
    from tau2.domains.airline.environment import get_environment,get_tasks
    from tau2.data_model.message import ToolCall
    import tau2
    require(Path(tau2.__file__).resolve().is_relative_to(repo/'src/tau2'),'IMPORT_ROOT_DRIFT')
    task=next((t for t in get_tasks('base') if str(t.id)==TASK),None)
    require(task is not None,'TASK8_NOT_FOUND')
    gold=task.evaluation_criteria.actions
    require(gold is not None,'MISSING_GOLD')
    require([x.name for x in gold]==EXPECTED_NAMES,'GOLD_ACTIONS_DRIFT')
    require([getattr(x,'value',str(x)) for x in task.evaluation_criteria.reward_basis]==['DB','COMMUNICATE'],'REWARD_DRIFT')
    seqs=frozen_sequences(gold)
    from loguru import logger
    logger.remove()  # Suppress synthetic profile text in public CI logs.
    require(set(seqs)=={x['mode'] for x in p['cases']},'FROZEN_SEQUENCES_MISMATCH')
    out.mkdir(parents=True,exist_ok=False)
    def baseline():
        env=get_environment();initial=task.initial_state
        env.set_state(initialization_data=initial.initialization_data if initial else None,
                      initialization_actions=initial.initialization_actions if initial else None,
                      message_history=list(initial.message_history or []) if initial else [],strict=True)
        return env
    results=[];errors=[]
    for case in p['cases']:
        case_dir=out/case['id'];case_dir.mkdir()
        try:
            env=baseline()
            require(env.get_db_hash()==Q1B_BASELINE,'INITIAL_NATIVE_DB_HASH_DRIFT')
            before=copy.deepcopy(env.tools.db)
            bind=a.run_binding+'_'+case['id']
            pre=project(env,before,'pre',bind)
            tool_out=[]
            for k,(name,args,requestor) in enumerate(seqs[case['mode']]):
                call=ToolCall(id=f'q1e-qualification-{case["id"]}-{k}',name=name,arguments=copy.deepcopy(args),requestor=requestor)
                response=env.get_response(call)
                tool_out.append({'step':k,'tool':name,'error':bool(response.error)})
            post=project(env,before,'post',bind)
            outcome=verdict(pre,post)
            got=[outcome['claims'][key]['status'] for key in ('C1_RESERVATION','C2_BOOKING_FIELDS','C3_COMMIT_CONSISTENCY')]
            observed_new=len(set(post['state']['reservation_ids'])-set(pre['state']['reservation_ids']))
            observed_tool_errors=sum(x['error'] for x in tool_out)
            expect=expected_case_status(case['expected'])
            success=(got==expect and observed_new==case['expected_new_reservations']
                     and observed_tool_errors==case['expected_tool_errors']
                     and outcome['claims']['C4_PROCESS_AUTH_ROOT']['status']=='NOT_IDENTIFIED'
                     and outcome['issues']==[])
            (case_dir/'pre.json').write_bytes(canonical(pre))
            (case_dir/'post.json').write_bytes(canonical(post))
            (case_dir/'case_verdict.json').write_bytes(canonical(outcome))
            (case_dir/'MANIFEST.sha256.json').write_bytes(canonical({n:file_sha(case_dir/n) for n in ('pre.json','post.json','case_verdict.json')}))
            rec={'case_id':case['id'],'native_tool_sequence':[x[0] for x in seqs[case['mode']]],
                 'native_call_errors':tool_out,'native_final_db_hash':env.get_db_hash(),
                 'claim_statuses':got,'expected_statuses':expect,'expected_matched':success,
                 'new_reservations_observed':observed_new,'expected_new_reservations':case['expected_new_reservations'],
                 'tool_errors_observed':observed_tool_errors,'expected_tool_errors':case['expected_tool_errors'],
                 'source_scope_only':True,'q1_status':'Q1_BLOCKED'}
            (case_dir/'receipt.json').write_bytes(canonical(rec))
            results.append(rec)
            if not success:errors.append({'case_id':case['id'],'reason':'FROZEN_QUALIFICATION_MISMATCH',
                                         'observed':got,'expected':expect,'new':observed_new,
                                         'errors':observed_tool_errors})
        except Exception as e:
            msg=type(e).__name__+':'+str(e)[:200]
            errors.append({'case_id':case['id'],'reason':msg})
            (case_dir/'FAILURE.json').write_bytes(canonical({'case_id':case['id'],'error':msg,'q1_status':'Q1_BLOCKED'}))
            # Continue only to preserve case-level diagnostics; no adaptive reruns.
    gold_final_hash=next((x['native_final_db_hash'] for x in results if x['case_id']=='GOLD'),None)
    same_gold_hash=[r['case_id'] for r in results if gold_final_hash is not None and r['native_final_db_hash']==gold_final_hash]
    summary={'schema':'ETB_Q1E_NATIVE_COUNTEREXAMPLE_QUALIFICATION_v095',
             'status':'NATIVE_COUNTEREXAMPLE_QUALIFICATION_PASS_SOURCE_SCOPED_ONLY' if not errors else 'NATIVE_COUNTEREXAMPLE_QUALIFICATION_NOT_CONFIRMED',
             'source_commit':PIN,'task_id':TASK,'run_binding':a.run_binding,
             'frozen_plan_sha256':file_sha(PLAN),'cases_expected':len(p['cases']),
             'cases_completed':len(results),'cases_matching':sum(r['expected_matched'] for r in results),
             'native_same_gold_db_hash_cases':same_gold_hash,
             'errors':errors,'native_llm_agent_runs':0,'native_communicate_evaluated':False,
             'q1_status':'Q1_BLOCKED','q2_confirmatory_eligible':False,
             'external_independent_effect_oracle':False,
             'claim_guard':'Native tool executions but authored sequences, native source-only effect, not model tasks, policy authorization, independent root or confirmed generalization.'}
    (out/'SUMMARY.json').write_bytes(canonical(summary))
    print(json.dumps(summary,indent=2))
    return 0 if not errors else 2

if __name__=='__main__':
    try:raise SystemExit(main())
    except (Blocked,ValueError,RuntimeError,OSError,subprocess.CalledProcessError) as e:
        print(json.dumps({'status':'Q1E_NATIVE_QUALIFICATION_BLOCKED','reason':str(e)[:250],
                          'q1_status':'Q1_BLOCKED','q2_confirmatory_eligible':False}))
        raise SystemExit(2)
