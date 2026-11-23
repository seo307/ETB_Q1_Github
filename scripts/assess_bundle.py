#!/usr/bin/env python3
from pathlib import Path
import sys,json,argparse
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from etb_q1e.core import verify_bundle, canonical
p=argparse.ArgumentParser();p.add_argument('--bundle',required=True);p.add_argument('--out');a=p.parse_args()
result=verify_bundle(a.bundle)
if a.out:
    if Path(a.out).exists():raise SystemExit('REFUSE_OVERWRITE')
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_bytes(canonical(result))
print(json.dumps(result,indent=2))
sys.exit(0 if result['status']=='Q1E_WITNESS_BUNDLE_VERIFIED_SOURCE_SCOPED' else 2)
