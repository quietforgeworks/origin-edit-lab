#!/usr/bin/env python3
"""Bounded local handoff; compact reads by default, explicit versioned confirmation."""
import argparse, base64, hashlib, importlib.util, json, urllib.request, urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('figure_guide_relations',ROOT/'guide_relations.py')
_rel=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_rel)

def load(path):
    value=json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(value,dict):raise ValueError('任务和操作清单必须是JSON对象。')
    return value

def fetch(url, body=None):
    origin=url.split('/api/',1)[0]
    req=urllib.request.Request(url,data=json.dumps(body).encode() if body is not None else None,
        headers={'Content-Type':'application/json','Origin':origin} if body is not None else {})
    with urllib.request.urlopen(req,timeout=5) as r:return json.loads(r.read())

def read_state(url, include_previews=False):
    if include_previews:return fetch(url+'/api/state')
    try:return fetch(url+'/api/state?view=summary')
    except urllib.error.HTTPError as e:
        if e.code!=404:raise
        return compact(fetch(url+'/api/state'))  # Legacy generated server.

def compact(result):
    result=dict(result)
    if 'displayPreviews' in result:
        result['displayPreviews']={k:{'sha256':v['sha256']} for k,v in result['displayPreviews'].items()}
    return result

def verify_task(result, expected):
    if not isinstance(result,dict) or not isinstance(result.get('layout'),dict):raise ValueError('服务返回的任务状态无效。')
    layout=result['layout']
    if layout.get('projectId')!=expected['projectId'] or layout.get('mapHash')!=expected['mapHash']:
        raise ValueError('服务任务与本地源绑定不一致，停止写入。')

def check_confirmation(result):
    c=result.get('confirmation');layout=result.get('layout')
    digest=hashlib.sha256(json.dumps(layout,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if not c or c.get('revision')!=result.get('revision') or c.get('layoutHash')!=digest or c.get('scope')!='layout-and-guides-only' or not isinstance(result.get('refinementInput'),dict):
        raise ValueError('当前版本尚未确认；明确确认后可在页面或用 confirm --revision 记录。')
    intent=_rel.from_layout(layout)
    if c.get('guideIntentSha256',intent['guideIntentSha256'])!=intent['guideIntentSha256']:
        raise ValueError('对齐关系与确认版本不一致。')
    result['refinementInput']=_rel.normalize_refinement_input(layout,result['refinementInput'])

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['read','read-confirmed','confirm','update-previews','apply','lock','renew','unlock'])
    p.add_argument('--layout',type=Path);p.add_argument('--previews',type=Path);p.add_argument('--revision',type=int)
    p.add_argument('--lock-id');p.add_argument('--label',default='助手正在调整参考线与布局')
    p.add_argument('--include-previews',action='store_true',help='Include PNG data URLs only when actually needed')
    a=p.parse_args()
    if a.action in ('lock','confirm','apply','update-previews') and a.revision is None:p.error(a.action+' requires --revision')
    if a.action in ('renew','unlock','apply','update-previews') and not a.lock_id:p.error(a.action+' requires --lock-id')
    if a.action=='apply' and a.layout is None:p.error('apply requires --layout')
    if a.action=='update-previews' and a.previews is None:p.error('update-previews requires --previews')
    try:
        session=load(ROOT/'session.json');expected=load(ROOT/'source.json');url=f"http://127.0.0.1:{session['port']}"
        current=read_state(url,a.include_previews if a.action.startswith('read') else False);verify_task(current,expected)
        body=None;endpoint='/api/state'
        if a.action=='confirm':
            # Caller must have explicit user confirmation of this exact current snapshot.
            endpoint='/api/confirm';body={'revision':a.revision}
        elif a.action=='apply':
            layout=load(a.layout);body={'layout':layout.get('layout',layout),'revision':a.revision,'author':'assistant','lockId':a.lock_id}
        elif a.action=='update-previews':
            manifest=load(a.previews)
            if any(manifest.get(k)!=expected[k] for k in ('projectId','mapHash')):
                raise ValueError('预览清单不属于当前任务，未发送任何修改。')
            if not isinstance(manifest.get('previews'),dict) or not manifest['previews']:raise ValueError('预览清单缺少有效的图片映射。')
            encoded={}
            for ident,path in manifest['previews'].items():
                image=Path(path);image=image if image.is_absolute() else a.previews.parent/image
                encoded[ident]=base64.b64encode(image.read_bytes()).decode()
            endpoint='/api/previews';body={'previews':encoded,'revision':a.revision,'lockId':a.lock_id}
        elif a.action in ('lock','renew','unlock'):
            endpoint='/api/lock';body={'action':{'lock':'acquire','renew':'renew','unlock':'release'}[a.action],
                'revision':a.revision,'lockId':a.lock_id,'label':a.label}
        if body is not None:
            body.update(projectId=expected['projectId'],mapHash=expected['mapHash'])
            if not a.include_previews:body['replyView']='summary'
            result=fetch(url+endpoint,body)
            if 'layout' in result:verify_task(result,expected)
        else:result=current
        if a.action in ('read-confirmed','confirm'):check_confirmation(result)
        print(json.dumps(result if a.include_previews else compact(result),ensure_ascii=False))
        return 0
    except urllib.error.HTTPError as e:
        print(e.read().decode());return 1
    except (OSError,ValueError,KeyError,TypeError,urllib.error.URLError) as e:
        print(json.dumps({'error':str(e)},ensure_ascii=False));return 1
if __name__=='__main__':raise SystemExit(main())
