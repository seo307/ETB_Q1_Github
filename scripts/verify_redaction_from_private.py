#!/usr/bin/env python3
"""Offline only: compare operator-held original Q0 and the public redacted copy."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--private-q0',required=True);a=p.parse_args()
r=json.loads((ROOT/'protocol/q0_redaction_v080.json').read_text())
private=Path(a.private_q0).read_bytes();public=(ROOT/'inputs/Q0_public_census.json').read_bytes()
try:
 obj=json.loads(private);repo=obj['repository']
 if not isinstance(repo,str) or not repo.startswith('/'):raise ValueError('ORIGINAL_PATH_EXPECTED')
 derived=private.replace(json.dumps(repo,ensure_ascii=False)[1:-1].encode(),b'REDACTED_LOCAL_PATH')
 ok=(derived==public and hashlib.sha256(private).hexdigest()==r['source_sha256'] and hashlib.sha256(public).hexdigest()==r['public_sha256'] and
     set(json.loads(private))==set(json.loads(public)) and all(json.loads(private)[k]==json.loads(public)[k] for k in obj if k!='repository'))
except (ValueError,KeyError,TypeError):ok=False
print(json.dumps({'status':'Q0_REDACTION_VERIFIED' if ok else 'Q0_REDACTION_MISMATCH','original_sha256_expected':r['source_sha256'],'q1_status':'Q1_BLOCKED'}))
raise SystemExit(0 if ok else 2)
