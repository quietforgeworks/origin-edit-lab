#!/usr/bin/env python3
"""Validate a browser box-layout export against the private source binding; no source edits."""
import argparse
import json
import math
from pathlib import Path
import layout_boxes as lb

LIMIT=10*1024*1024

def read_json(path):
    if Path(path).stat().st_size>LIMIT:raise ValueError('Layout/manifest exceeds size limit')
    return json.loads(Path(path).read_text(encoding='utf-8'),parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Non-finite JSON value')))

def finite(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)

def read_layout(path,manifest_path,output,source_paths=()):
    if Path(output).exists():raise ValueError('Output exists; choose a new report filename')
    m=read_json(manifest_path);p=read_json(path)
    core={k:v for k,v in m.items() if k not in ['mapHash','createdAt','inventoryPath','initialDraftSha256']}
    if m.get('schema')!=lb.FMT or lb.jhash(core)!=m.get('mapHash'):raise ValueError('Private source binding is changed or unsupported')
    if p.get('schema')!=lb.FMT or p.get('projectId')!=m['projectId'] or p.get('mapHash')!=m['mapHash']:raise ValueError('Browser export has a stale or foreign source binding')
    canvas=p.get('canvas',{})
    if canvas.get('unit')!='mm' or not all(finite(canvas.get(k)) and 0<canvas[k]<=1000 for k in ('width','height')):raise ValueError('Invalid canvas')
    if any(abs(canvas[k]-m['canvas'][k])>1e-6 for k in ('width','height')):raise ValueError('Canvas changed; review a matching binding before use')
    selected=p.get('selectedPanels');omitted=p.get('omittedPanelIds')
    if not isinstance(selected,list) or not isinstance(omitted,list):raise ValueError('Missing selected/omitted panel lists')
    wanted={x['id']:x for x in m['panels']}
    if len(selected)>len(wanted) or len(omitted)>len(wanted):raise ValueError('Excessive panel list')
    if any(not isinstance(x,str) for x in omitted) or len(set(omitted))!=len(omitted):raise ValueError('Invalid omitted IDs')
    seen=set();found=[];warnings=[]
    for item in selected:
        ident=item.get('id')
        if not isinstance(ident,str) or ident not in wanted or ident in seen:raise ValueError('Duplicate or unbound panel ID')
        seen.add(ident);box=item.get('bounds',{})
        if not all(finite(box.get(k)) for k in ('x','y','w','h')) or min(box['w'],box['h'])<=0:raise ValueError('Non-finite or non-positive box geometry')
        if any(abs(box[k])>10000 for k in ('x','y','w','h')):raise ValueError('Box geometry exceeds task limits')
        if box['x']<0 or box['y']<0 or box['x']+box['w']>canvas['width']+1e-6 or box['y']+box['h']>canvas['height']+1e-6:warnings.append({'type':'off-canvas','panelId':ident})
        original=wanted[ident]
        if 'parentPanelId' in item and item['parentPanelId']!=original.get('parentPanelId'):raise ValueError('Common panel identity differs from private binding')
        for key in ('sourceBindings','sourceAssetIds'):
            if key in item and lb.jhash(item[key])!=lb.jhash(original[key]):raise ValueError('Exported source mapping differs from private binding')
        text=item.get('text',item.get('name',original['name']))
        if not isinstance(text,str) or len(text)>2000:raise ValueError('Invalid panel label')
        found.append({'id':ident,'bounds':{k:box[k] for k in ('x','y','w','h')},'text':text,'sourceAssetIds':original['sourceAssetIds'],'sourceBindings':original['sourceBindings'], **({'parentPanelId':original['parentPanelId']} if 'parentPanelId' in original else {})})
    if seen&set(omitted) or seen|set(omitted)!=set(wanted):raise ValueError('Selected/omitted panel IDs do not partition the original set')
    expected={s.get('fileHash') for panel in m['panels'] for s in panel['sourceBindings'] if s.get('fileHash')}
    provided={lb.fhash(x) for x in source_paths}
    source_verified=bool(expected) and expected.issubset(provided)
    if not found:warnings.append({'type':'no-selected-panels'})
    refinement=p.get('refinement',m['refinement'])
    if not isinstance(refinement,dict) or refinement.get('mode') not in ('existing-aesthetics','user-references') or not isinstance(refinement.get('references',[]),list):raise ValueError('Invalid requested refinement template')
    note=p.get('note','')
    if not isinstance(note,str) or len(note)>2000:raise ValueError('Invalid layout note')
    report={'schema':lb.FMT,'projectId':m['projectId'],'mapHash':m['mapHash'],'returnedLayoutSha256':lb.fhash(path),'originalSourceVerified':source_verified,'missingSourceHashes':sorted(expected-provided),'canvas':canvas,'selectedPanels':found,'omittedPanelIds':sorted(omitted),'warnings':warnings,'refinement':refinement,'note':note,'geometryIsApproximateIntent':True,'temporaryPreviewDistortionIsNotSourceTransform':True,'semanticGuideApprovalRequired':True,'userChatApprovalStillRequired':True,'scientificSourceEdited':False}
    report['layoutIntentHash']=lb.jhash(report)
    with Path(output).open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2,allow_nan=False)
    return {'layoutReport':str(output),'selectedPanelCount':len(found),'omittedPanelIds':sorted(omitted),'warnings':warnings,'originalSourceVerified':source_verified,'layoutIntentHash':report['layoutIntentHash']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('layout');p.add_argument('--manifest',required=True);p.add_argument('--output',required=True);p.add_argument('--source',action='append',default=[])
    args=p.parse_args()
    try:print(json.dumps(read_layout(args.layout,args.manifest,args.output,args.source),ensure_ascii=False,indent=2))
    except (ValueError,KeyError,TypeError,OSError) as e:p.exit(2,str(e)+'\n')

if __name__=='__main__':main()
