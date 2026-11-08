#!/usr/bin/env python3
"""Build one self-contained offline layout page. No source objects or network calls."""
import argparse,base64,hashlib,json,math,re,struct
from pathlib import Path

SAFE_ID=re.compile(r'[A-Za-z0-9_-]{1,64}\Z')
HASH=re.compile(r'[0-9a-f]{64}\Z')

def finite_number(value):return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)
def normalize(project,base):
    if project.get('schema')!='figure-layout-roundtrip/v1' or not isinstance(project.get('projectId'),str) or not project['projectId'] or not HASH.fullmatch(project.get('mapHash','')):raise ValueError('Invalid project binding')
    canvas=project.get('canvas',{})
    if canvas.get('unit')!='mm' or not all(finite_number(canvas.get(k)) and 0<canvas[k]<=5000 for k in ['width','height']):raise ValueError('Invalid canvas')
    panels=project.get('panels')
    if not isinstance(panels,list) or not 1<=len(panels)<=200:raise ValueError('Invalid panel inventory')
    cleaned=[];seen=set();total=0
    for p in panels:
        ident=p.get('id','')
        if not isinstance(ident,str) or not SAFE_ID.fullmatch(ident) or ident in seen:raise ValueError('Unsafe or duplicate panel ID')
        seen.add(ident);b=p.get('initialBounds',{})
        if not all(finite_number(b.get(k)) for k in ['x','y','w','h']) or min(b['x'],b['y'])<0 or min(b['w'],b['h'])<=0 or b['x']+b['w']>canvas['width']+.01 or b['y']+b['h']>canvas['height']+.01:raise ValueError('Invalid panel bounds')
        ref=p.get('preview')
        if not isinstance(ref,str) or Path(ref).is_absolute():raise ValueError('Preview must be a local relative path')
        path=(base/ref).resolve()
        if base not in path.parents or not path.is_file():raise ValueError('Preview escapes project directory or is missing')
        data=path.read_bytes();total+=len(data)
        if total>32*1024*1024 or len(data)<24 or data[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('Preview must be a bounded PNG')
        w,h=struct.unpack('>II',data[16:24])
        if not w or not h or w*h>100000000:raise ValueError('Invalid PNG dimensions')
        q={'id':ident,'name':str(p.get('name',ident))[:160],'initialBounds':{k:b[k] for k in ['x','y','w','h']},'preview':'data:image/png;base64,'+base64.b64encode(data).decode()}
        if 'parentPanelId' in p:
            if not isinstance(p['parentPanelId'],str) or not SAFE_ID.fullmatch(p['parentPanelId']):raise ValueError('Invalid semantic parent ID')
            q['parentPanelId']=p['parentPanelId']
        cleaned.append(q)
    result={'schema':project['schema'],'projectId':project['projectId'],'mapHash':project['mapHash'],'canvas':{k:canvas[k] for k in ['width','height','unit']},'title':str(project.get('title','科研图布局'))[:160],'panels':cleaned,'refinement':{'mode':'user-references' if project.get('refinement',{}).get('mode')=='user-references' else 'existing-aesthetics','references':[]}}
    migration=project.get('layoutMigration')
    if migration:
        if not isinstance(migration,dict) or not HASH.fullmatch(migration.get('fromMapHash','')) or not isinstance(migration.get('splitPanels'),dict):raise ValueError('Invalid migration')
        split={};children=set()
        for parent,ids in migration['splitPanels'].items():
            if not SAFE_ID.fullmatch(parent) or not isinstance(ids,list) or len(ids)<2 or any(not isinstance(i,str) or i not in seen or i in children for i in ids) or len(set(ids))!=len(ids):raise ValueError('Invalid split mapping')
            split[parent]=ids;children.update(ids)
        result['layoutMigration']={'fromMapHash':migration['fromMapHash'],'splitPanels':split}
    return result

def build(project_path,output_path,template_dir):
    project_path=Path(project_path);output=Path(output_path);template=Path(template_dir)
    if output.exists():raise ValueError('Output exists; choose a new path')
    source=normalize(json.loads(project_path.read_text(encoding='utf-8')),project_path.parent.resolve())
    app=(template/'app.js').read_text(encoding='utf-8');style=(template/'style.css').read_text(encoding='utf-8');html=(template/'index.html').read_text(encoding='utf-8')
    if app.count('__LAYOUT_PROJECT__')!=1:raise ValueError('Invalid offline script template')
    app=app.replace('__LAYOUT_PROJECT__',json.dumps(source,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029'))
    if '</script' in app.lower() or any(word in app for word in ['fetch(','XMLHttpRequest','WebSocket','sendBeacon']):raise ValueError('Offline script must not make network requests')
    digest='sha256-'+base64.b64encode(hashlib.sha256(app.encode()).digest()).decode()
    for token,value in [('__SCRIPT_HASH__',digest),('__INLINE_STYLE__',style),('__INLINE_SCRIPT__',app)]:
        if html.count(token)!=1:raise ValueError('Invalid HTML template')
        html=html.replace(token,value)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as f:f.write(html)
    return {'output':str(output),'panelCount':len(source['panels']),'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'networkRequests':False,'originalSourceEdited':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('project');p.add_argument('--output',required=True);p.add_argument('--template-dir',default=str(Path(__file__).resolve().parent));a=p.parse_args()
    try:print(json.dumps(build(a.project,a.output,a.template_dir),ensure_ascii=False,indent=2))
    except (ValueError,TypeError,KeyError,OSError) as e:p.exit(2,str(e)+'\n')
if __name__=='__main__':main()
