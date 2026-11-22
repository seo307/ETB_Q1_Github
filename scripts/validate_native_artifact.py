#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from etb_github.validate import check_artifact
p=argparse.ArgumentParser();p.add_argument('--artifact-dir',required=True);a=p.parse_args()
i=check_artifact(a.artifact_dir)
print(json.dumps({'status':'NATIVE_ARTIFACT_SOURCE_SCOPED_PASS' if not i else 'NATIVE_ARTIFACT_BLOCKED',
 'issues':i,'native_agent_runs':0,'independent_root_verified':False,'q1_status':'Q1_BLOCKED','confirmatory_eligible':False},indent=2))
raise SystemExit(0 if not i else 2)
