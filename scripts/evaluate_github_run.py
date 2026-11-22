#!/usr/bin/env python3
"""Evaluate downloaded GitHub REST observations against downloaded native artifact; no network call."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from etb_github.github_api import assess
from etb_github.contract import readj,canonical
p=argparse.ArgumentParser();p.add_argument('--run-json',required=True);p.add_argument('--jobs-json',required=True)
p.add_argument('--native-dir',required=True);p.add_argument('--out',required=True)
a=p.parse_args();out=Path(a.out)
if out.exists():p.error('REFUSE_OVERWRITE')
try:
 result=assess(readj(a.run_json),readj(a.jobs_json),a.native_dir)
except (OSError,ValueError,TypeError) as e:
 result={'status':'GITHUB_NATIVE_PREFLIGHT_BLOCKED','q1_status':'Q1_BLOCKED','q2_confirmatory_eligible':False,
  'independent_administrative_root_verified':False,'issues':['SOURCE_LOAD_ERROR:'+str(e)[:160]]}
out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(canonical(result)+b'\n')
print(json.dumps(result,indent=2))
raise SystemExit(0 if result.get('status')=='GITHUB_HOSTED_NATIVE_PREFLIGHT_CORROBORATED' else 2)
