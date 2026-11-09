#!/usr/bin/env python3
"""Loopback-only figure-layout session. No source-document editing, upload or autostart."""
import uuid,base64,struct,zlib,io
from PIL import Image
import argparse, copy, hashlib, json, math, os, re, tempfile, threading, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path


import importlib.util
_guide_spec=importlib.util.spec_from_file_location('figure_guide_relations',Path(__file__).with_name('guide_relations.py'))
_guide_module=importlib.util.module_from_spec(_guide_spec);_guide_spec.loader.exec_module(_guide_module)
guide_intent=_guide_module.from_layout
GUIDE_POLICY=_guide_module.POLICY

ROOT=Path(__file__).resolve().parent
LOCK=threading.RLock()
MAX=250_000

def compact(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(x): return hashlib.sha256(compact(x).encode()).hexdigest()
def write_json(path,obj):
    fd,name=tempfile.mkstemp(prefix='.atomic-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f: f.write(json.dumps(obj,ensure_ascii=False,indent=2)); f.flush(); os.fsync(f.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name): os.unlink(name)

def number(v): return type(v) in (int,float) and math.isfinite(v)
def valid(layout,source):
    if not isinstance(layout,dict) or layout.get('schema')!='figure-layout-roundtrip/v1' or layout.get('projectId')!=source['projectId'] or layout.get('mapHash')!=source['mapHash'] or layout.get('canvas')!=source['canvas']: raise ValueError('任务或画布不匹配')
    if layout.get('guideSemantics',GUIDE_POLICY)!=GUIDE_POLICY:raise ValueError('参考线仅表达对齐关系，不能设为绝对坐标约束')
    known={p['id'] for p in source['panels']}; seen=set(); out=copy.deepcopy(layout)
    if not isinstance(layout.get('selectedPanels'),list) or not isinstance(layout.get('omittedPanelIds'),list): raise ValueError('图片列表无效')
    for p in layout['selectedPanels']:
        if not isinstance(p,dict) or p.get('id') not in known or p['id'] in seen: raise ValueError('图片编号重复或未知')
        seen.add(p['id']); b=p.get('bounds',{})
        if not isinstance(b,dict) or set(b)!=set('xywh') or not all(number(b[k]) for k in 'xywh'): raise ValueError('坐标无效')
        if b['x']< -240 or b['y']< -240 or b['w']<=0 or b['h']<=0 or b['x']+b['w']>source['canvas']['width']+240.01 or b['y']+b['h']>source['canvas']['height']+240.01: raise ValueError('图片超出画布')
    for i in layout['omittedPanelIds']:
        if not isinstance(i,str) or i not in known or i in seen: raise ValueError('遗漏图片记录无效')
        seen.add(i)
    if seen!=known: raise ValueError('图片选择不完整')
    guides=layout.get('guides',[])
    if not isinstance(guides,list) or len(guides)>100: raise ValueError('参考线过多')
    ids=set(); kinds={'frame','title','label','center','custom'}
    for g in guides:
        if not isinstance(g,dict) or not isinstance(g.get('id'),str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',g['id']) or g['id'] in ids: raise ValueError('参考线编号无效')
        ids.add(g['id'])
        if g.get('axis') not in ('x','y') or not number(g.get('pos')) or not 0<=g['pos']<=source['canvas']['width' if g['axis']=='x' else 'height']: raise ValueError('参考线坐标无效')
        if not isinstance(g.get('color'),str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',g['color']): raise ValueError('颜色无效')
        if g.get('color')!={'frame':'#189db7','title':'#9855bd','label':'#d96046','center':'#bc892d','custom':'#607b63'}.get(g.get('kind')): raise ValueError('颜色必须对应语义类型')
        if g.get('kind') not in kinds or g.get('owner') not in ('user','assistant'): raise ValueError('参考线类型无效')
        if not isinstance(g.get('label'),str) or len(g['label'])>80: raise ValueError('参考线说明过长')
        if not isinstance(g.get('targets',[]),list) or any(not isinstance(t,str) or t not in known for t in g.get('targets',[])) or len(set(g.get('targets',[])))!=len(g.get('targets',[])): raise ValueError('参考线目标无效')
    wf=layout.get('guideWorkflow',{'mode':'unselected','proposalReady':False})
    if not isinstance(wf,dict) or wf.get('mode') not in ('unselected','complete','auto','constrained') or type(wf.get('proposalReady',False))!=bool: raise ValueError('参考线阶段无效')
    # Drop imported claims and all unknown properties. This is a layout, never scientific approval.
    return {'guideSemantics':GUIDE_POLICY,'guideWorkflow':{'mode':wf['mode'],'proposalReady':wf.get('proposalReady',False)},'schema':'figure-layout-roundtrip/v1','projectId':source['projectId'],'mapHash':source['mapHash'],'canvas':source['canvas'],'selectedPanels':[{'id':p['id'],'bounds':p['bounds']} for p in layout['selectedPanels']], 'omittedPanelIds':layout['omittedPanelIds'],'guides':[{k:g[k] for k in ('id','axis','pos','color','kind','owner','label')}|{'targets':g.get('targets',[])} for g in guides], 'note':str(layout.get('note',''))[:2000],'refinement':{'mode':'user-references' if isinstance(layout.get('refinement'),dict) and layout['refinement'].get('mode')=='user-references' else 'existing-aesthetics','references':[]},'geometryIsApproximateIntent':True,'previewStretchIsNotScientificEdit':True,'scientificSourceEdited':False}

def validate_png(encoded):
    if not isinstance(encoded,str) or len(encoded)>12*1024*1024:raise ValueError('PNG过大或无效')
    try:data=base64.b64decode(encoded,validate=True)
    except (ValueError,TypeError):raise ValueError('PNG编码无效')
    if data[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('仅允许PNG预览')
    offset=8;types=[]
    while offset<len(data):
        if offset+12>len(data):raise ValueError('PNG截断')
        n=struct.unpack('>I',data[offset:offset+4])[0];kind=data[offset+4:offset+8];end=offset+12+n
        if end>len(data) or zlib.crc32(data[offset+4:offset+8+n])&0xffffffff!=struct.unpack('>I',data[offset+8+n:end])[0]:raise ValueError('PNG块校验失败')
        types.append(kind)
        if len(types)==1:
            if kind!=b'IHDR' or n!=13:raise ValueError('PNG头无效')
            w,h=struct.unpack('>II',data[offset+8:offset+16])
            if not w or not h or w*h>25000000:raise ValueError('PNG尺寸无效')
        offset=end
        if kind==b'IEND':break
    if offset!=len(data) or not types or types[-1]!=b'IEND' or b'IDAT' not in types:raise ValueError('PNG结构无效')
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format!='PNG' or image.width*image.height>25000000 or getattr(image,'n_frames',1)!=1:raise ValueError('PNG预览尺寸或帧数无效')
            image.load()
    except (OSError,ValueError,Image.DecompressionBombError) as error:raise ValueError('PNG像素解码失败') from error
    return data

def snapshot(doc, include_previews=False):
    """Same version/layout semantics, without unnecessary PNG payloads for assistants."""
    out=copy.deepcopy(doc)
    if not include_previews and 'displayPreviews' in out:
        out['displayPreviews']={k:{'sha256':v['sha256']} for k,v in out['displayPreviews'].items()}
    return out

class Store:
    def __init__(self,root):
        self.work_lock=None; self.root=root; self.source=json.loads((root/'source.json').read_text()); self.path=root/'shared-state.json'; self.hist=root/'history';self.hist.mkdir(exist_ok=True)
        if self.path.exists():
            self.doc=json.loads(self.path.read_text());valid(self.doc['layout'],self.source)
        else:
            initial={'schema':'figure-layout-roundtrip/v1','projectId':self.source['projectId'],'mapHash':self.source['mapHash'],'canvas':self.source['canvas'],'selectedPanels':[{'id':p['id'],'bounds':p['initialBounds']} for p in self.source['panels']], 'omittedPanelIds':[], 'guides':[]}
            if (root/'initial-layout.json').exists():initial=json.loads((root/'initial-layout.json').read_text())
            self.doc={'revision':0,'layout':valid(initial,self.source),'updatedAt':time.time(),'author':'initial','confirmation':None};write_json(self.path,self.doc)
    def lock_status(self):
        with LOCK:
            if self.work_lock and self.work_lock['expiresAt']<=time.time():self.work_lock=None
            return copy.deepcopy(self.work_lock)
    def lock_action(self,req):
        with LOCK:
            current=self.lock_status();action=req.get('action')
            if action=='acquire':
                if current:raise RuntimeError('已有工作锁')
                if type(req.get('revision'))!=int or req.get('revision')!=self.doc['revision']:raise RuntimeError('版本变化')
                self.work_lock={'id':uuid.uuid4().hex,'label':str(req.get('label','助手正在工作'))[:120],'expiresAt':time.time()+180,'baseRevision':self.doc['revision']}
            elif action=='cancel':self.work_lock=None
            elif action in ('renew','release'):
                if not current or req.get('lockId')!=current['id']:raise PermissionError('工作锁已失效，请停止写入并重新协调')
                if action=='renew':self.work_lock['expiresAt']=time.time()+180
                else:self.work_lock=None
            else:raise ValueError('工作锁操作无效')
            return {'lock':self.lock_status()}
    def commit(self,layout,revision,author,lock_id=None):
        with LOCK:
            if type(revision)!=int or revision!=self.doc['revision']: raise RuntimeError('版本冲突')
            current=self.lock_status()
            if author=='user' and current:raise PermissionError('助手正在工作，草稿保留，暂不可提交')
            if author=='assistant' and (not current or current['id']!=lock_id):raise PermissionError('助手写入需要有效工作锁')
            clean=valid(layout,self.source)
            if author=='user':
                # Imported/local drafts cannot assert that an assistant proposal exists.
                previous_workflow=self.doc['layout'].get('guideWorkflow',{})
                requested_workflow=clean['guideWorkflow']
                requested_workflow['proposalReady']=bool(requested_workflow['proposalReady'] and previous_workflow.get('proposalReady') and requested_workflow['mode']==previous_workflow.get('mode'))
                previous={g['id']:g for g in self.doc['layout'].get('guides',[])}
                for g in clean['guides']:
                    if previous.get(g['id'])!=g:g['owner']='user'
            if author=='assistant':
                proposed={g['id']:g for g in clean['guides']}
                for g in self.doc['layout'].get('guides',[]):
                    if g['owner']=='user' and proposed.get(g['id'])!=g:
                        raise ValueError('助手不能覆盖用户参考线；请由用户调整后重试')
            nxt={'revision':revision+1,'layout':clean,'updatedAt':time.time(),'author':author,'confirmation':None}
            if 'displayPreviews' in self.doc:nxt['displayPreviews']=copy.deepcopy(self.doc['displayPreviews'])
            write_json(self.hist/f'{revision:06d}.json',self.doc);write_json(self.path,nxt);self.doc=nxt
            old=sorted(self.hist.glob('*.json'))
            # Bounded session history. Current state and confirmed snapshots remain separate.
            for p in old[:-200]:p.unlink()
            return copy.deepcopy(nxt)
    def update_previews(self,req):
        with LOCK:
            if type(req.get('revision'))!=int or req.get('revision')!=self.doc['revision']:raise RuntimeError('版本冲突')
            current=self.lock_status()
            if not current or current['id']!=req.get('lockId'):raise PermissionError('预览更新需要有效工作锁')
            if req.get('projectId')!=self.source['projectId'] or req.get('mapHash')!=self.source['mapHash']:raise ValueError('任务绑定不匹配')
            previews=req.get('previews');known={p['id'] for p in self.source['panels']}
            if not isinstance(previews,dict) or not previews or not set(previews)<=known:raise ValueError('预览目标无效')
            old=copy.deepcopy(self.doc.get('displayPreviews',{}));total=0
            for ident,encoded in previews.items():
                data=validate_png(encoded);total+=len(data)
                if total>8*1024*1024:raise ValueError('预览总大小过大')
                old[ident]={'dataUrl':'data:image/png;base64,'+encoded,'sha256':hashlib.sha256(data).hexdigest()}
            if sum(len(v['dataUrl']) for v in old.values())>32*1024*1024:raise ValueError('预览总大小过大')
            nxt=copy.deepcopy(self.doc);nxt.update(revision=self.doc['revision']+1,updatedAt=time.time(),author='assistant',confirmation=None,displayPreviews=old)
            nxt.pop('refinementInput',None)
            write_json(self.hist/f"{self.doc['revision']:06d}.json",self.doc);write_json(self.path,nxt);self.doc=nxt
            for old_path in sorted(self.hist.glob('*.json'))[:-200]:old_path.unlink()
            return {'revision':nxt['revision'],'previewHashes':{k:v['sha256'] for k,v in old.items()},'scientificSourceEdited':False}
    def confirm(self,revision):
        with LOCK:
            if type(revision)!=int or revision!=self.doc['revision']:raise RuntimeError('版本冲突')
            if self.lock_status():raise PermissionError('助手正在工作，请等待完成再确认')
            out=copy.deepcopy(self.doc)
            wf=out['layout'].get('guideWorkflow',{})
            if wf.get('mode','unselected')=='unselected':raise ValueError('请先选择参考线阶段')
            if wf['mode']!='complete' and not wf.get('proposalReady'):raise ValueError('等待助手添加参考线，刷新检查后再确认')
            inside=[];outside=[];partial=[];c=self.source['canvas']
            for p in out['layout']['selectedPanels']:
                b=p['bounds']
                if b['x']+b['w']<=0 or b['y']+b['h']<=0 or b['x']>=c['width'] or b['y']>=c['height']:outside.append(p['id'])
                elif b['x']<0 or b['y']<0 or b['x']+b['w']>c['width'] or b['y']+b['h']>c['height']:partial.append(p['id'])
                else:inside.append(p)
            if partial:raise ValueError('图片跨边界，请完整移入或移出：'+','.join(partial))
            if not inside:raise ValueError('成图画布为空，请至少保留一张完整图片')
            intent=guide_intent(out['layout'])
            out['refinementInput']={'selectedPanels':inside,'excludedOutsidePanelIds':outside,'sourcePreserved':True,**intent}
            out['confirmation']={'revision':revision,'layoutHash':digest(out['layout']),'confirmedAt':time.time(),'scope':'layout-and-guides-only','guideIntentSha256':intent['guideIntentSha256']}
            write_json(self.root/'confirmed-layout.json',out);write_json(self.path,out);self.doc=out
            return out

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def send(self,code,data,typ='application/json; charset=utf-8'):
        b=data if isinstance(data,bytes) else compact(data).encode()
        self.send_response(code);self.send_header('Content-Type',typ);self.send_header('Content-Length',str(len(b)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY');self.end_headers();self.wfile.write(b)
    def allowed(self,write=False):
        expected=f'127.0.0.1:{self.server.server_port}'
        if self.headers.get('Host')!=expected:return False
        origin=self.headers.get('Origin')
        if origin and origin!='http://'+expected:return False
        if self.headers.get('Sec-Fetch-Site')=='cross-site':return False
        return not write or (origin=='http://'+expected and self.headers.get('Content-Type','').split(';')[0]=='application/json')
    def do_GET(self):
        if not self.allowed():return self.send(403,{'error':'只允许本机同源访问'})
        if self.path=='/':return self.send(200,(ROOT/'index.html').read_bytes(),'text/html; charset=utf-8')
        if self.path=='/api/lock':return self.send(200,{'lock':self.server.store.lock_status()})
        if self.path in ('/api/state','/api/state?view=summary'):
            with LOCK:return self.send(200,snapshot(self.server.store.doc,include_previews=self.path=='/api/state'))
        return self.send(404,{'error':'not found'})
    def do_POST(self):
        if not self.allowed(True):return self.send(403,{'error':'只允许本机同源JSON请求'})
        try:
            n=int(self.headers.get('Content-Length','0'))
            if not 0<n<=(12*1024*1024 if self.path=='/api/previews' else MAX):raise ValueError('请求过大或为空')
            req=json.loads(self.rfile.read(n))
            if not isinstance(req,dict):raise ValueError('请求无效')
            for field in ('projectId','mapHash'):
                if field in req and req[field]!=self.server.store.source[field]:raise ValueError('请求不属于当前排版任务')
            if self.path=='/api/lock':return self.send(200,self.server.store.lock_action(req))
            if self.path=='/api/previews':return self.send(200,self.server.store.update_previews(req))
            if self.path=='/api/state':
                author=req.get('author')
                if author not in ('user','assistant'):raise ValueError('修改方无效')
                out=self.server.store.commit(req.get('layout'),req.get('revision'),author,req.get('lockId'))
            elif self.path=='/api/confirm':out=self.server.store.confirm(req.get('revision'))
            else:return self.send(404,{'error':'not found'})
            return self.send(200,snapshot(out) if req.get('replyView')=='summary' else out)
        except PermissionError as e:return self.send(423,{'error':str(e)})
        except RuntimeError:return self.send(409,{'error':'其他窗口或助手已更新；本地修改未覆盖远端，请先保存冲突副本再重新载入。'})
        except (ValueError,TypeError,KeyError) as e:return self.send(400,{'error':str(e)})

def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8766);a=p.parse_args()
    s=ThreadingHTTPServer(('127.0.0.1',a.port),Handler);s.store=Store(ROOT)
    write_json(ROOT/'session.json',{'pid':os.getpid(),'port':s.server_port,'url':f'http://127.0.0.1:{s.server_port}/','autostart':False})
    print(f'http://127.0.0.1:{s.server_port}/',flush=True)
    try:s.serve_forever()
    except KeyboardInterrupt:pass
    finally:s.server_close()
if __name__=='__main__':main()
