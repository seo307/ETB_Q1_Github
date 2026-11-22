#!/usr/bin/env python3
"""Read-only GitHub REST collection. Downloads raw run and jobs JSON; never claims root independence.

Public repositories work without a token (subject to rate limits). For private repositories,
export GH_TOKEN in the terminal session. The token is never saved in evidence files.
"""
from __future__ import annotations
import argparse,json,os,re,sys,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from etb_github.contract import readj

def acquire(repo,run_id,out,*,token=None,opener=None):
 if not re.fullmatch(r'[A-Za-z0-9_-][A-Za-z0-9_.-]*/[A-Za-z0-9_-][A-Za-z0-9_.-]*',repo) or '..' in repo:raise ValueError('BAD_REPOSITORY_ID')
 if not isinstance(run_id,int) or run_id<=0:raise ValueError('BAD_RUN_ID')
 out=Path(out)
 if out.exists():raise ValueError('REFUSE_OVERWRITE')
 if opener is None:opener=urllib.request.urlopen
 prefix=f'https://api.github.com/repos/{repo}/actions/runs/{run_id}'
 headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'ETB-Q1-v080-readonly'}
 if token:headers['Authorization']='Bearer '+token
 payloads=[]
 for suffix in ('','/jobs?per_page=100'):
  req=urllib.request.Request(prefix+suffix,headers=headers,method='GET')
  with opener(req,timeout=30) as response:
   if getattr(response,'status',200)!=200:raise ValueError('GITHUB_API_HTTP_ERROR')
   raw=response.read(4_000_001)
   if len(raw)>4_000_000:raise ValueError('GITHUB_API_RESPONSE_TOO_LARGE')
   json.loads(raw.decode('utf-8'))
  payloads.append(raw)
 # No partial directory left on invalid responses.
 out.mkdir(parents=True)
 (out/'run.json').write_bytes(payloads[0]);(out/'jobs.json').write_bytes(payloads[1])
 return {'status':'GITHUB_READ_ONLY_METADATA_ACQUIRED_NOT_VERIFIED','repository':repo,'run_id':run_id,'q1_status':'Q1_BLOCKED'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--repo',required=True,help='OWNER/REPO')
 p.add_argument('--run-id',required=True,type=int);p.add_argument('--out-dir',required=True)
 args=p.parse_args()
 try:result=acquire(args.repo,args.run_id,args.out_dir,token=os.getenv('GH_TOKEN'))
 except (ValueError,OSError,urllib.error.HTTPError,urllib.error.URLError) as e:
  result={'status':'GITHUB_API_ACQUISITION_BLOCKED','error':type(e).__name__+':'+str(e)[:200],'q1_status':'Q1_BLOCKED'}
 print(json.dumps(result,indent=2));return 0 if result['status'].startswith('GITHUB_READ_ONLY_') else 2
if __name__=='__main__':raise SystemExit(main())
