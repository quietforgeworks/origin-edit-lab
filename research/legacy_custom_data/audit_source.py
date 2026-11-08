"""Read-only source/report inventory check. Keep its manifest digest externally."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import stat

def need(condition,message):
 if not condition:raise ValueError(message)

def strict_json(raw):
 def pairs(items):
  out={}
  for key,value in items:
   need(key not in out,'duplicate manifest key');out[key]=value
  return out
 def constant(_):raise ValueError('nonfinite manifest number')
 def number(token):
  value=float(token);need(math.isfinite(value),'nonfinite manifest number');return value
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant,parse_float=number)

def inventory(root):
 files=[]
 for directory in ('src','tests','inputs','evidence'):
  path=root/directory
  need(not path.is_symlink() and path.is_dir(),'source directory missing or symlink')
  for candidate in path.rglob('*'):
   need(not candidate.is_symlink(),'source member symlink')
   need(candidate.is_dir() or stat.S_ISREG(candidate.stat().st_mode),'nonregular source member')
   if candidate.is_file():files.append(candidate)
 for candidate in root.iterdir():
  if candidate.name=='SOURCE-MANIFEST.json' or candidate.name.endswith('.sha256'):continue
  if candidate.is_file() and (candidate.suffix in ('.md','.py') or candidate.name in ('.gitignore','LICENSE')):files.append(candidate)
 application=root/'application'
 need(not application.is_symlink() and application.is_dir(),'application source directory missing or symlink')
 for candidate in application.iterdir():
  if candidate.is_file() and candidate.suffix!='.so':files.append(candidate)
 for path in files:
  need(not path.is_symlink() and stat.S_ISREG(path.stat().st_mode),'source member not regular')
 return {str(p.relative_to(root)): {'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(files)}

def audit(root, expected_manifest_sha256=None):
 root=Path(root).absolute();path=root/'SOURCE-MANIFEST.json'
 need('..' not in root.parts,'parent traversal in source root')
 for part in (root,*root.parents):need(not part.is_symlink(),'source root ancestor symlink')
 need(not path.is_symlink(),'manifest symlink')
 raw=path.read_bytes()
 if expected_manifest_sha256 is not None:need(hashlib.sha256(raw).hexdigest()==expected_manifest_sha256,'manifest external hash differs')
 manifest=strict_json(raw)
 need(set(manifest)=={'schema','files','limits'},'manifest keys differ')
 need(manifest['schema']=='custom-fixed50-source-manifest-v1','unknown manifest schema')
 actual=inventory(root)
 need(json.dumps(actual,sort_keys=True,allow_nan=False)==json.dumps(manifest['files'],sort_keys=True,allow_nan=False),'source/report inventory/hash/size mismatch')
 return {'source_inventory':'PASS','files':len(actual),'bytes':sum(x['bytes'] for x in actual.values()),'manifest_sha256':hashlib.sha256(raw).hexdigest(),'origin_lifecycle':'NOT_RUN','public_publication':False}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--expected-manifest-sha256');a=p.parse_args()
 print(json.dumps(audit(a.root,a.expected_manifest_sha256),indent=2))
