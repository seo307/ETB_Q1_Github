#!/usr/bin/env python3
"""Verify per-case state and verdict integrity; does not authenticate state origin."""
from __future__ import annotations
import argparse,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
try:
    from etb_q1e.core import verdict,canonical,load_json_strict
except ModuleNotFoundError:
    # Full downloadable research package can self-verify without installing Q1E.
    # GitHub 4-file runner patch instead uses the already installed original etb_q1e module.
    import types,zipfile
    zfile=ROOT/'inputs/ETB_Q1E_ClaimWitness_v0.9.4.zip'
    if not zfile.is_file():raise
    with zipfile.ZipFile(zfile) as z:
        source=z.read('ETB_Q1E_ClaimWitness_v0.9.4/etb_q1e/core.py')
    module=types.ModuleType('archived_q1e_core_verifier')
    exec(compile(source,str(zfile)+'::etb_q1e/core.py','exec'),module.__dict__)
    verdict,canonical,load_json_strict=module.verdict,module.canonical,module.load_json_strict
PLAN=ROOT/'protocol/native_execution_plan_v095.json'
PLAN_SHA='5a3e8481425e5722a0e85ae0be39f9646a7c386d797682b4de21aa7eb9f5c87a'
EXPECTED={'C1_RESERVATION','C2_BOOKING_FIELDS','C3_COMMIT_CONSISTENCY','C4_PROCESS_AUTH_ROOT'}

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(outdir:Path):
    problems=[];data={}
    try:
        if digest(PLAN)!=PLAN_SHA:raise ValueError('PLAN_DRIFT')
        plan=load_json_strict(PLAN)
        summary=load_json_strict(outdir/'SUMMARY.json')
        if summary['frozen_plan_sha256']!=PLAN_SHA:raise ValueError('RUN_PLAN_HASH_DRIFT')
        if summary['source_commit']!=plan['source_commit'] or summary['task_id']!=plan['task_id']:
            raise ValueError('SOURCE_TASK_DRIFT')
        if summary['cases_expected']!=len(plan['cases']):raise ValueError('CASE_COUNT_DRIFT')
        want_dirs={c['id'] for c in plan['cases']}
        observed_dirs={x.name for x in outdir.iterdir() if x.is_dir()}
        if want_dirs!=observed_dirs:raise ValueError('CASE_DIRECTORY_SET_MISMATCH')
        for c in plan['cases']:
            case_dir=outdir/c['id']
            try:
                expected_files={'pre.json','post.json','case_verdict.json','MANIFEST.sha256.json','receipt.json'}
                if {x.name for x in case_dir.iterdir() if x.is_file()} != expected_files:raise ValueError('CASE_FILE_SET_MISMATCH')
                mf=load_json_strict(case_dir/'MANIFEST.sha256.json')
                if set(mf)!={'pre.json','post.json','case_verdict.json'}:raise ValueError('CASE_MANIFEST_SET_BAD')
                for name,h in mf.items():
                    if not re.fullmatch('[0-9a-f]{64}',h) or digest(case_dir/name)!=h:
                        raise ValueError('HASH_MISMATCH:'+name)
                pre=load_json_strict(case_dir/'pre.json');post=load_json_strict(case_dir/'post.json')
                actual=verdict(pre,post);archived=load_json_strict(case_dir/'case_verdict.json')
                if actual!=archived:raise ValueError('VERDICT_REPLAY_MISMATCH')
                record=load_json_strict(case_dir/'receipt.json')
                if record['case_id']!=c['id'] or record['expected_matched'] is not True:raise ValueError('CASE_NOT_CONFIRMED')
                observed=[actual['claims'][name]['status'] for name in ('C1_RESERVATION','C2_BOOKING_FIELDS','C3_COMMIT_CONSISTENCY')]
                if observed!=record['claim_statuses'] or record['new_reservations_observed']!=c['expected_new_reservations'] or record['tool_errors_observed']!=c['expected_tool_errors']:
                    raise ValueError('RECEIPT_EXPECTATION_MISMATCH')
                if actual['claims']['C4_PROCESS_AUTH_ROOT']['status']!='NOT_IDENTIFIED' or actual['q1_status']!='Q1_BLOCKED':
                    raise ValueError('ILLICIT_Q1_PROMOTION')
            except Exception as e:problems.append({'case_id':c['id'],'error':type(e).__name__+':'+str(e)})
        if summary['cases_completed']!=len(plan['cases']) or summary['cases_matching']!=len(plan['cases']) or summary['errors']:
            problems.append({'error':'SUMMARY_NOT_QUALIFIED'})
        if summary['q1_status']!='Q1_BLOCKED' or summary['q2_confirmatory_eligible'] is not False:
            problems.append({'error':'ILLICIT_SUMMARY_PROMOTION'})
        data={'source_commit':plan['source_commit'],'cases':len(plan['cases'])}
    except Exception as e:problems.append({'error':type(e).__name__+':'+str(e)})
    return {'status':'NATIVE_CASE_BUNDLE_INTEGRITY_PASS_SOURCE_SCOPED_ONLY' if not problems else 'NATIVE_CASE_BUNDLE_NOT_CONFIRMED',
            'issues':problems,'details':data,'not_independent_oracle':True,'q1_status':'Q1_BLOCKED','q2_confirmatory_eligible':False}

def main():
    a=argparse.ArgumentParser();a.add_argument('--out-dir',required=True)
    args=a.parse_args()
    r=verify(Path(args.out_dir))
    print(json.dumps(r,indent=2))
    return 0 if not r['issues'] else 2
if __name__=='__main__':raise SystemExit(main())
