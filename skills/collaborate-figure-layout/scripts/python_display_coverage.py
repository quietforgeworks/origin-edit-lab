#!/usr/bin/env python3
"""Read-only whole-page display-edit coverage gate; never edits PPT or certifies rendering."""
import argparse,hashlib,json,re
from pathlib import Path
FACETS=('host_geometry','internal_plot_geometry','text_typography','line_paragraph_spacing','occlusion_resolution','strokes_markers','spacing_alignment','distortion','native_editability','data_preservation','preview_sync')
SCHEMA='python-display-coverage/v1'
def sha(data):return hashlib.sha256(data).hexdigest()
def targets(inv,slide):
 if inv.get('schema')!='figure-layout-inventory/v1':raise ValueError('Unsupported inventory')
 if type(slide)!=int or slide<1:raise ValueError('Invalid slide')
 out={}
 for a in inv['assets']:
  s=a['source']
  if s['slideNumber']!=slide:continue
  members=[{'xmlPath':s['xmlPath'],'shapeType':s['shapeType']}]+s.get('structuralMembers',[])
  for m in members:
   key=a['id']+'|'+m['xmlPath'];out[key]={'assetId':a['id'],'xmlPath':m['xmlPath'],'shapeType':m['shapeType'],'sourceKind':s['kind']}
 if not out:raise ValueError('No inventoried objects on selected slide')
 return out
def initialize(inv,raw,slide):
 return {'schema':SCHEMA,'inventory_sha256':sha(raw),'source_sha256':inv['source']['fileHash'],'slide':slide,'objects':[dict(id=k,**v,facets={f:{'status':'pending','reason':'','evidence':[]} for f in FACETS}) for k,v in targets(inv,slide).items()]}
def check(inv,raw,plan,base):
 if plan.get('schema')!=SCHEMA or plan.get('inventory_sha256')!=sha(raw) or plan.get('source_sha256')!=inv['source']['fileHash']:raise ValueError('Source/inventory binding mismatch')
 known=targets(inv,plan.get('slide'));seen=set();blockers=[]
 for obj in plan.get('objects',[]):
  key=obj.get('id')
  if key not in known or key in seen:raise ValueError('Unknown or duplicate object')
  seen.add(key)
  if any(obj.get(k)!=v for k,v in known[key].items()):raise ValueError('Object identity changed')
  facets=obj.get('facets',{})
  if set(facets)!=set(FACETS):raise ValueError('Missing or unknown display facets')
  for facet,item in facets.items():
   status=item.get('status');reason=item.get('reason');evidence=item.get('evidence')
   if status not in ('pending','blocked','verified-change','verified-unchanged','not-applicable'):raise ValueError('Invalid status')
   if not isinstance(evidence,list):raise ValueError('Evidence must be list')
   if status in ('pending','blocked'):
    blockers.append({'object':key,'facet':facet,'reason':reason or status});continue
   if not isinstance(reason,str) or not reason.strip() or not evidence:raise ValueError('Resolved facet requires explanation and evidence')
   for e in evidence:
    if not isinstance(e,dict) or not isinstance(e.get('path'),str) or not re.fullmatch('[0-9a-f]{64}',str(e.get('sha256',''))):raise ValueError('Invalid evidence reference')
    path=(base/e['path']).resolve()
    if not path.is_file() or sha(path.read_bytes())!=e['sha256']:raise ValueError('Evidence missing or changed')
 if seen!=set(known):raise ValueError('Omitted inventoried objects; document exclusions in each facet with evidence')
 return {'coverage_complete':not blockers,'blockers':blockers,'object_count':len(known),'facet_count':len(FACETS),'scientific_source_edited':False,'visual_quality_verified':False,'origin_activation_verified':False,'limitations':['Evidence hashes prove file identity, not correctness of observations. Independently inspect every claim, scientific grouping, render and target-host lifecycle.','This gate does not modify the inner plot, redraw text, or turn unsupported editing into a supported operation.']}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['init','check']);p.add_argument('inventory',type=Path);p.add_argument('--slide',type=int);p.add_argument('--plan',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
 try:
  raw=a.inventory.read_bytes();inv=json.loads(raw)
  if a.action=='init':
   result=initialize(inv,raw,a.slide)
   if not a.output:raise ValueError('init requires new --output')
   with a.output.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
  else:
   if not a.plan:raise ValueError('check requires --plan')
   result=check(inv,raw,json.loads(a.plan.read_text()),a.plan.parent);print(json.dumps(result,ensure_ascii=False,indent=2))
   if not result['coverage_complete']:raise SystemExit(2)
 except (OSError,ValueError,TypeError,KeyError) as e:p.exit(2,str(e)+'\n')
if __name__=='__main__':main()
