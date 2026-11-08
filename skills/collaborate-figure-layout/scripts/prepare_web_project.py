#!/usr/bin/env python3
"""Prepare the small private layout page from a source binding and actual PNG thumbnails."""
import argparse
import importlib.util
import hashlib
import json
import re
import shutil
import struct
from pathlib import Path
import layout_boxes as lb
from read_web_layout import read_json

ROOT=Path(__file__).resolve().parent.parent

def prepare(binding_path,previews_path,out_dir,record_path,title='拖动图片编排',mode='offline',migration_path=None):
    if mode not in ('offline','online'):raise ValueError('Mode must be offline or online')
    out=Path(out_dir);record=Path(record_path)
    if out.exists() or record.exists():raise ValueError('Output already exists; choose new task paths')
    if out.resolve()==record.resolve() or out.resolve() in record.resolve().parents:raise ValueError('Keep the private thumbnail record outside the hosted output')
    m=read_json(binding_path);images=read_json(previews_path)
    core={k:v for k,v in m.items() if k not in ['mapHash','createdAt','inventoryPath','initialDraftSha256']}
    if m.get('schema')!=lb.FMT or lb.jhash(core)!=m.get('mapHash'):raise ValueError('Binding changed or unsupported')
    expected={p['id'] for p in m['panels']}
    if not isinstance(images,dict) or set(images)!=expected:raise ValueError('Provide one actual thumbnail for every bound panel')
    prepared=[];rows=[]
    for panel in m['panels']:
        ident=panel['id']
        if not re.fullmatch('[A-Za-z0-9_-]{1,32}',ident):raise ValueError('Unsafe panel ID')
        path=Path(images[ident]);size=path.stat().st_size
        if size>30*1024*1024:raise ValueError('Thumbnail exceeds limit')
        data=path.read_bytes()
        if len(data)<24 or data[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('Thumbnails must be actual rendered PNG files')
        w,h=struct.unpack('>II',data[16:24])
        if not w or not h or w*h>100000000:raise ValueError('Invalid or excessive thumbnail dimensions')
        filename=f'previews/{ident}.png'
        prepared.append((filename,data))
        rows.append({'panelId':ident,'previewSha256':hashlib.sha256(data).hexdigest(),'width':w,'height':h,'sourceAssetIds':panel['sourceAssetIds']})
    assets=ROOT/'assets/web-layout'
    for name in ('index.html','app.js','style.css'):
        if not (assets/name).is_file():raise ValueError('Reusable page template is incomplete')
    project={'schema':lb.FMT,'projectId':m['projectId'],'mapHash':m['mapHash'],'title':str(title)[:160],
             'canvas':m['canvas'],'panels':[{'id':p['id'],'name':p['name'],'initialBounds':p['initialBounds'],'preview':f"previews/{p['id']}.png", **({'parentPanelId':p['parentPanelId']} if 'parentPanelId' in p else {})} for p in m['panels']],
             'refinement':{'mode':m['refinement'].get('mode','existing-aesthetics'),'references':[]},'geometryIsApproximateIntent':True}
    if migration_path:
        migration=read_json(migration_path)
        if not isinstance(migration,dict) or not re.fullmatch('[0-9a-f]{64}',migration.get('fromMapHash','')) or not isinstance(migration.get('splitPanels'),dict):raise ValueError('Invalid layout migration')
        child_ids=set()
        for parent,children in migration['splitPanels'].items():
            if not re.fullmatch('[A-Za-z0-9_-]{1,64}',parent) or not isinstance(children,list) or len(children)<2 or len(set(children))!=len(children) or any(c not in expected or c in child_ids for c in children):raise ValueError('Invalid layout split mapping')
            child_ids.update(children)
        project['layoutMigration']={'fromMapHash':migration['fromMapHash'],'splitPanels':migration['splitPanels']}
    out.mkdir(parents=True,exist_ok=False)
    target=out
    if mode=='online':
        shutil.copytree(assets/'online',out,dirs_exist_ok=True)
        target=out/'dist'
        target.mkdir(exist_ok=True)
    (target/'previews').mkdir(exist_ok=False)
    for name,data in prepared:(target/name).write_bytes(data)
    (target/'project.json').write_text(json.dumps(project,ensure_ascii=False,indent=2),encoding='utf-8')
    output_file=None
    if mode=='offline':
        spec=importlib.util.spec_from_file_location('figure_offline_builder',assets/'build-offline.py')
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        builder.build(target/'project.json',target/'index.html',assets)
        output_file=str(target/'index.html')
    audit={'schema':'figure-layout-thumbnails/v1','projectId':m['projectId'],'mapHash':m['mapHash'],'thumbnails':rows,'sourceObjectsEmbedded':False}
    record.parent.mkdir(parents=True,exist_ok=True)
    with record.open('x',encoding='utf-8') as f:json.dump(audit,f,ensure_ascii=False,indent=2)
    return {'outputDirectory':str(out),'outputFile':output_file,'mode':mode,'thumbnailRecord':str(record),'panelCount':len(rows),'accessVerified':False,'hostingPerformed':False,'requiresPrivateSiteSetup':mode=='online','originalSourceEdited':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('binding');p.add_argument('previews');p.add_argument('--output-dir',required=True);p.add_argument('--thumbnail-record',required=True);p.add_argument('--title',default='拖动图片编排');p.add_argument('--mode',choices=['offline','online'],default='offline');p.add_argument('--migration-file');a=p.parse_args()
    try:print(json.dumps(prepare(a.binding,a.previews,a.output_dir,a.thumbnail_record,a.title,a.mode,a.migration_file),ensure_ascii=False,indent=2))
    except (ValueError,KeyError,TypeError,OSError) as e:p.exit(2,str(e)+'\n')

if __name__=='__main__':main()
