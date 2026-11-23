#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from etb_github.q1b import verify_result_directory
p=argparse.ArgumentParser();p.add_argument('--artifact-dir',required=True);a=p.parse_args()
issues=verify_result_directory(a.artifact_dir,Path(__file__).resolve().parents[1])
status='Q1B_NATIVE_SEMANTIC_SOURCE_SCOPED_PASS' if not issues else 'Q1B_NATIVE_SEMANTIC_BLOCKED'
print(json.dumps({'status':status,'issues':issues,'q1_status':'Q1_BLOCKED','confirmatory_eligible':False},indent=2))
raise SystemExit(0 if not issues else 2)
