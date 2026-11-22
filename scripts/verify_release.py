#!/usr/bin/env python3
"""Manifest + structural fail-closed release verifier; never executes the external benchmark."""
from __future__ import annotations
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from etb_github.contract import sha,readj,freeze_check
PRIOR_SHA='8b1f1f13483fa6924535732e05ddc6a583ae3a3425502a1e726f2d6792780f82'

def verify():
 errors=[]
 try:
  manifest=readj(ROOT/'MANIFEST.sha256.json')
  for name,digest in manifest.items():
   if not re.fullmatch(r'[a-f0-9]{64}',digest) or name.startswith('/') or '..' in Path(name).parts:errors.append('BAD_MANIFEST_ENTRY:'+name);continue
   p=ROOT/name
   if not p.is_file() or sha(p)!=digest:errors.append('FILE_MISMATCH:'+name)
  redact=readj(ROOT/'protocol/q0_redaction_v080.json')
  if redact.get('source_sha256')!='345f4f6673bf31fcec0d50bde87ff970b00d0171da504c383ea02b050a6c10cc' or redact.get('public_sha256')!=sha(ROOT/'inputs/Q0_public_census.json') or redact.get('prior_v072_private_zip_sha256')!=PRIOR_SHA:errors.append('REDACTION_PROVENANCE_MISMATCH')
  if '/Users/' in (ROOT/'inputs/Q0_public_census.json').read_text():errors.append('UNREDACTED_PUBLIC_Q0')
  freeze,fe=freeze_check();errors.extend(fe)
  work=(ROOT/'.github/workflows/etb-q1-native-preflight.yml').read_text()
  for req in ['workflow_dispatch:', 'permissions:', 'contents: read', 'runs-on: ubuntu-24.04',
              'persist-credentials: false','uv sync --frozen','uv==0.13.9','--upstream-lock vendor/tau2-bench/uv.lock','actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683',
              'actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02',freeze['source_commit']]:
   if req not in work:errors.append('WORKFLOW_REQUIREMENT_MISSING:'+req)
  if not re.search(r'(?m)^on:\n  workflow_dispatch:\s*$',work):errors.append('WORKFLOW_MANUAL_ONLY_NOT_VERIFIED')
  if any(re.search(r'(?m)^\s*'+re.escape(s)+r'\s*:',work) for s in ('pull_request','pull_request_target','push','workflow_run','schedule')):errors.append('UNAPPROVED_WORKFLOW_EVENT')
  if 'attestations: write' in work or 'id-token: write' in work or 'contents: write' in work:errors.append('UNEXPECTED_PRIVILEGED_SCOPE')
 except (KeyError,OSError,ValueError,TypeError) as e:errors.append('RELEASE_PARSE_ERROR:'+str(e)[:160])
 return {'status':'ETB_Q1_V080_RELEASE_VERIFY_PASS' if not errors else 'ETB_Q1_V080_RELEASE_VERIFY_FAIL',
         'files_checked':len(manifest) if isinstance(locals().get('manifest'),dict) else 0,
         'prior_v072_sha256_pinned_private_not_bundled':PRIOR_SHA,'q0_sha256_expected':freeze['q0_sha256'] if isinstance(locals().get('freeze'),dict) else None,
         'issues':sorted(set(errors)),
         'github_external_runs_executed_here':0,'native_llm_agent_runs':0,
         'independent_root_verified':False,'q1_status':'Q1_BLOCKED','confirmatory_eligible':False}

def main():
 r=verify();print(json.dumps(r,indent=2));return 0 if not r['issues'] else 2
if __name__=='__main__':raise SystemExit(main())
