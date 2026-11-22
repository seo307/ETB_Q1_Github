#!/usr/bin/env python3
"""Packaging-only manifest generator, not run in field acquisition."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
items={}
for path in sorted(root.rglob('*')):
 if not path.is_file():continue
 rel=path.relative_to(root)
 if rel.as_posix()=='MANIFEST.sha256.json' or any(x in rel.parts for x in ('__pycache__','.git','vendor','.venv-tau2','results')):continue
 items[rel.as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
(root/'MANIFEST.sha256.json').write_text(json.dumps(items,sort_keys=True,indent=2)+'\n')
print(len(items))
