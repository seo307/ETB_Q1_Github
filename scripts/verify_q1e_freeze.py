#!/usr/bin/env python3
"""Frozen Q1E controls; hash must be updated only by making a separately versioned study."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
FROZEN_SHA256='eaf1fddfeb0ba31c69a7410ff75a6aa435521625242921499c9813c973751f0d'
p=ROOT/'protocol/qualification_freeze_v094.json'
if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=FROZEN_SHA256:
    print(json.dumps({'status':'Q1E_FROZEN_PROTOCOL_MISMATCH','q1_status':'Q1_BLOCKED'}));sys.exit(2)
f=json.loads(p.read_text())
if f.get('source_commit')!='c06b07dd7c4d4ec61ba6ff9bcdf0b15dd7ef36d4' or f.get('no_go',{}).get('q2')!='NOT_ELIGIBLE':
    print(json.dumps({'status':'Q1E_FROZEN_PROTOCOL_INVALID','q1_status':'Q1_BLOCKED'}));sys.exit(2)
print(json.dumps({'status':'Q1E_PROSPECTIVE_NATIVE_PROTOCOL_FROZEN','sha256':FROZEN_SHA256,'q1_status':'Q1_BLOCKED','new_native_execution':False},indent=2))
