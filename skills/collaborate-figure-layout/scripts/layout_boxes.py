#!/usr/bin/env python3
"""Create and read a lightweight, editable PowerPoint box layout.

This tool never edits or embeds the original scientific file. It writes a new,
ordinary OOXML deck containing rectangles and text only. JSON is an assistant-side
binding record; the user edits and returns only the .pptx file.
"""
import argparse, datetime, hashlib, json, math, re, uuid, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships','pr':'http://schemas.openxmlformats.org/package/2006/relationships','cp':'http://schemas.openxmlformats.org/officeDocument/2006/custom-properties','vt':'http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes'}
for k,v in NS.items(): ET.register_namespace(k,v)
EMU=36000
MARKER='FIGURE_LAYOUT::'
FMT='figure-layout-roundtrip/v1'

def jhash(v): return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def fhash(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def xbytes(e): return ET.tostring(e,encoding='utf-8',xml_declaration=True)
def tag(q): p,n=q.split(':'); return '{'+NS[p]+'}'+n
def sub(e,q,attrs=None,text=None):
    n=ET.SubElement(e,tag(q),{k:str(v) for k,v in (attrs or {}).items()});n.text=text;return n
def parse_xml(data):
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper(): raise ValueError('DTD/entity XML is not supported.')
    return ET.fromstring(data)
def load_zip(path):
    z=zipfile.ZipFile(path)
    infos=z.infolist()
    if len(infos)>10000 or len({x.filename for x in infos})!=len(infos): raise ValueError('Duplicate or excessive ZIP entries.')
    if sum(x.file_size for x in infos)>300*1024**2 or any(x.file_size>50*1024**2 or x.flag_bits&1 for x in infos): raise ValueError('Encrypted or oversized PPTX.')
    return z

def text_shape(shape_id,name,text,x,y,w,h,fill='EDF2EC',stroke='789075',font=16,descr=None):
    sp=ET.Element(tag('p:sp'));nv=sub(sp,'p:nvSpPr');p=sub(nv,'p:cNvPr',{'id':shape_id,'name':name})
    if descr:p.set('descr',descr)
    sub(nv,'p:cNvSpPr');sub(nv,'p:nvPr');props=sub(sp,'p:spPr');xf=sub(props,'a:xfrm');sub(xf,'a:off',{'x':round(x*EMU),'y':round(y*EMU)});sub(xf,'a:ext',{'cx':round(w*EMU),'cy':round(h*EMU)})
    geom=sub(props,'a:prstGeom',{'prst':'rect'});sub(geom,'a:avLst')
    if fill:sub(sub(props,'a:solidFill'),'a:srgbClr',{'val':fill})
    else:sub(props,'a:noFill')
    ln=sub(props,'a:ln',{'w':12700});sub(sub(ln,'a:solidFill'),'a:srgbClr',{'val':stroke}) if stroke else sub(ln,'a:noFill')
    tx=sub(sp,'p:txBody');sub(tx,'a:bodyPr',{'wrap':'square','lIns':90000,'rIns':90000,'tIns':60000,'bIns':60000,'anchor':'ctr'});sub(tx,'a:lstStyle')
    for line in text.split('\n'):
        para=sub(tx,'a:p');sub(para,'a:pPr',{'algn':'ctr'});run=sub(para,'a:r');rpr=sub(run,'a:rPr',{'lang':'zh-CN','sz':round(font*100),'dirty':'0'});sub(sub(rpr,'a:solidFill'),'a:srgbClr',{'val':'293C2F'});sub(rpr,'a:latin',{'typeface':'Arial'});sub(rpr,'a:ea',{'typeface':'Noto Sans CJK SC'});sub(run,'a:t',text=line);sub(para,'a:endParaRPr',{'lang':'zh-CN','sz':round(font*100)})
    return sp

def grid(n,width,height):
    cols=3 if n<=12 else 4 if n<=20 else 5
    cols=min(cols,max(1,n));rows=math.ceil(n/cols);m=12;top=26;gap=6
    w=(width-2*m-gap*(cols-1))/cols;h=(height-top-12-gap*(rows-1))/rows
    if min(w,h)<10:raise ValueError('Too many boxes for one readable slide. Split the task into figures.')
    return [{'x':m+(i%cols)*(w+gap),'y':top+(i//cols)*(h+gap),'w':w,'h':h} for i in range(n)]

def rels(items):
    root=ET.Element('{'+NS['pr']+'}Relationships')
    for id,kind,target in items:ET.SubElement(root,'{'+NS['pr']+'}Relationship',{'Id':id,'Type':'http://schemas.openxmlformats.org/officeDocument/2006/relationships/'+kind,'Target':target})
    return xbytes(root).replace(b'pr:',b'').replace(b'xmlns:pr=',b'xmlns=')

def build_deck(path,width,height,project_id,map_hash,panels):
    p=ET.Element(tag('p:presentation'));masters=sub(p,'p:sldMasterIdLst');sub(masters,'p:sldMasterId',{'id':2147483648,tag('r:id'):'rId1'});slides=sub(p,'p:sldIdLst');sub(slides,'p:sldId',{'id':256,tag('r:id'):'rId2'});sub(p,'p:sldSz',{'cx':round(width*EMU),'cy':round(height*EMU),'type':'custom'});sub(p,'p:notesSz',{'cx':6858000,'cy':9144000})
    slide=ET.Element(tag('p:sld'));common=sub(slide,'p:cSld',{'name':'布局草稿'});tree=sub(common,'p:spTree');nv=sub(tree,'p:nvGrpSpPr');sub(nv,'p:cNvPr',{'id':1,'name':''});sub(nv,'p:cNvGrpSpPr');sub(nv,'p:nvPr');grp=sub(tree,'p:grpSpPr');xf=sub(grp,'a:xfrm');[sub(xf,'a:'+name,attrs) for name,attrs in [('off',{'x':0,'y':0}),('ext',{'cx':0,'cy':0}),('chOff',{'x':0,'y':0}),('chExt',{'cx':0,'cy':0})]]
    tree.append(text_shape(2,'Layout instructions','拖动、拉宽或拉大方框；删除不用的图。保存此 PPT 后发回。',8,4,width-16,15,None,None,12))
    colors={'schematic':'E3EBDF','characterization':'EBEEE3','curve':'E3ECF0','comparison':'F1E7DB','summary':'EBE5F0','unknown':'EBEFEB'}
    for i,panel in enumerate(panels,3):
        marker=MARKER+project_id+'::'+panel['id'];label=panel['id']+'  '+panel['name'];b=panel['initialBounds'];descr=json.dumps({'schema':FMT,'projectId':project_id,'panelId':panel['id'],'mapHash':map_hash},separators=(',',':'))
        tree.append(text_shape(i,marker,label,b['x'],b['y'],b['w'],b['h'],colors.get(panel.get('category'),'EBEFEB'),'789075',14 if len(panels)<=12 else 12,descr))
    sub(sub(slide,'p:clrMapOvr'),'a:masterClrMapping')
    # Standard blank layout/master; all figure boxes have explicit local styling.
    master=ET.Element(tag('p:sldMaster'));cs=sub(master,'p:cSld');st=sub(cs,'p:spTree');nv=sub(st,'p:nvGrpSpPr');sub(nv,'p:cNvPr',{'id':1,'name':''});sub(nv,'p:cNvGrpSpPr');sub(nv,'p:nvPr');sub(st,'p:grpSpPr');sub(master,'p:clrMap',{'bg1':'lt1','tx1':'dk1','bg2':'lt2','tx2':'dk2','accent1':'accent1','accent2':'accent2','accent3':'accent3','accent4':'accent4','accent5':'accent5','accent6':'accent6','hlink':'hlink','folHlink':'folHlink'});ls=sub(master,'p:sldLayoutIdLst');sub(ls,'p:sldLayoutId',{'id':2147483649,tag('r:id'):'rId1'});sub(master,'p:txStyles')
    layout=ET.Element(tag('p:sldLayout'),{'type':'blank','preserve':'1'});cs=sub(layout,'p:cSld',{'name':'Blank'});st=sub(cs,'p:spTree');nv=sub(st,'p:nvGrpSpPr');sub(nv,'p:cNvPr',{'id':1,'name':''});sub(nv,'p:cNvGrpSpPr');sub(nv,'p:nvPr');sub(st,'p:grpSpPr');sub(sub(layout,'p:clrMapOvr'),'a:masterClrMapping')
    theme=ET.Element(tag('a:theme'),{'name':'Figure layout'});te=sub(theme,'a:themeElements');cl=sub(te,'a:clrScheme',{'name':'Figure layout'});
    for name,value in {'dk1':'000000','lt1':'FFFFFF','dk2':'293C2F','lt2':'F5F5F0','accent1':'537365','accent2':'64869A','accent3':'B29474','accent4':'937B9D','accent5':'89956E','accent6':'788A80','hlink':'0563C1','folHlink':'954F72'}.items():sub(sub(cl,'a:'+name),'a:srgbClr',{'val':value})
    fonts=sub(te,'a:fontScheme',{'name':'Figure layout'});
    for kind in ['majorFont','minorFont']:
        f=sub(fonts,'a:'+kind);sub(f,'a:latin',{'typeface':'Arial'});sub(f,'a:ea',{'typeface':'Noto Sans CJK SC'});sub(f,'a:cs',{'typeface':'Arial'})
    fmt=sub(te,'a:fmtScheme',{'name':'Figure layout'});fills=sub(fmt,'a:fillStyleLst');lns=sub(fmt,'a:lnStyleLst');effects=sub(fmt,'a:effectStyleLst');bgs=sub(fmt,'a:bgFillStyleLst')
    for _ in range(3):
        sub(sub(fills,'a:solidFill'),'a:schemeClr',{'val':'phClr'});ln=sub(lns,'a:ln',{'w':12700});sub(sub(ln,'a:solidFill'),'a:schemeClr',{'val':'phClr'});sub(ln,'a:prstDash',{'val':'solid'});sub(sub(effects,'a:effectStyle'),'a:effectLst');sub(sub(bgs,'a:solidFill'),'a:schemeClr',{'val':'phClr'})
    custom=ET.Element(tag('cp:Properties'))
    for i,(name,value) in enumerate([('FigureLayoutProjectId',project_id),('FigureLayoutMapHash',map_hash)],2):sub(sub(custom,'cp:property',{'fmtid':'{D5CDD505-2E9C-101B-9397-08002B2CF9AE}','pid':i,'name':name}),'vt:lpwstr',text=value)
    ct='http://schemas.openxmlformats.org/package/2006/content-types';types=ET.Element('{'+ct+'}Types')
    for ext,typ in [('rels','application/vnd.openxmlformats-package.relationships+xml'),('xml','application/xml')]:ET.SubElement(types,'{'+ct+'}Default',{'Extension':ext,'ContentType':typ})
    for part,typ in [('ppt/presentation.xml','presentationml.presentation.main'),('ppt/slides/slide1.xml','presentationml.slide'),('ppt/slideMasters/slideMaster1.xml','presentationml.slideMaster'),('ppt/slideLayouts/slideLayout1.xml','presentationml.slideLayout'),('ppt/theme/theme1.xml','theme'),('docProps/custom.xml','custom-properties')]:
        ctype='application/vnd.openxmlformats-officedocument.'+typ+'+xml';ET.SubElement(types,'{'+ct+'}Override',{'PartName':'/'+part,'ContentType':ctype})
    parts={'[Content_Types].xml':xbytes(types).replace(b'ns0:',b'').replace(b'xmlns:ns0=',b'xmlns='),'_rels/.rels':rels([('rId1','officeDocument','ppt/presentation.xml'),('rId2','custom-properties','docProps/custom.xml')]),'ppt/presentation.xml':xbytes(p),'ppt/_rels/presentation.xml.rels':rels([('rId1','slideMaster','slideMasters/slideMaster1.xml'),('rId2','slide','slides/slide1.xml')]),'ppt/slides/slide1.xml':xbytes(slide),'ppt/slides/_rels/slide1.xml.rels':rels([('rId1','slideLayout','../slideLayouts/slideLayout1.xml')]),'ppt/slideMasters/slideMaster1.xml':xbytes(master),'ppt/slideMasters/_rels/slideMaster1.xml.rels':rels([('rId1','slideLayout','../slideLayouts/slideLayout1.xml'),('rId2','theme','../theme/theme1.xml')]),'ppt/slideLayouts/slideLayout1.xml':xbytes(layout),'ppt/slideLayouts/_rels/slideLayout1.xml.rels':rels([('rId1','slideMaster','../slideMasters/slideMaster1.xml')]),'ppt/theme/theme1.xml':xbytes(theme),'docProps/custom.xml':xbytes(custom)}
    with zipfile.ZipFile(path,'x',zipfile.ZIP_DEFLATED) as z:
        for name,data in parts.items():z.writestr(name,data)

def create(inventory_path,output,manifest_path,spec_path=None):
    if Path(output).exists() or Path(manifest_path).exists(): raise ValueError('Output already exists; choose new filenames.')
    raw=json.loads(Path(inventory_path).read_text());assets=raw['assets'];byid={a['id']:a for a in assets}
    if len(byid)!=len(assets):raise ValueError('Duplicate inventory asset IDs.')
    spec=json.loads(Path(spec_path).read_text()) if spec_path else {}
    requests=spec.get('panels')
    if not requests:raise ValueError('Provide an assistant-curated --spec with semantic panels; raw shape inventories are not automatically treated as figures.')
    if not 1<=len(requests)<=40:raise ValueError('Choose 1–40 semantic figures (recommended 9–20), rather than every decorative shape.')
    w=float(spec.get('canvas',{}).get('width',280));h=float(spec.get('canvas',{}).get('height',200))
    if not 100<=w<=1000 or not 100<=h<=1000:raise ValueError('Draft canvas must be between 100 and 1000 mm.')
    initial=grid(len(requests),w,h);panels=[];seen=set()
    for i,p in enumerate(requests):
        pid=p.get('id',f'F{i+1:02d}');ids=p.get('sourceAssetIds',[])
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,32}',pid) or pid in seen:raise ValueError('Invalid/duplicate panel ID.')
        seen.add(pid)
        if not ids or len(set(ids))!=len(ids) or any(x not in byid for x in ids):raise ValueError('Unresolved source asset binding for '+pid)
        b=p.get('bounds',initial[i]);b={k:float(b[k]) for k in ['x','y','w','h']}
        if any(not math.isfinite(v) for v in b.values()) or min(b['w'],b['h'])<=0:raise ValueError('Invalid proposed bounds.')
        parent=p.get('parentPanelId')
        if parent is not None and (not isinstance(parent,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,32}',parent)):raise ValueError('Invalid common panel identity.')
        panel={'id':pid,'name':str(p['name'])[:120],'category':p.get('category','unknown'),'sourceAssetIds':ids,'sourceBindings':[byid[x].get('source',{}) for x in ids],'initialBounds':b}
        if parent is not None:panel['parentPanelId']=parent
        panels.append(panel)
    core={'schema':FMT,'projectId':str(uuid.uuid4()),'canvas':{'width':w,'height':h,'unit':'mm'},'panels':panels,'refinement':spec.get('refinement',{'mode':'existing-aesthetics','references':[]}), 'geometryIsApproximateIntent':True,'originalInventoryHash':jhash(raw),'scientificSourceEditsAuthorized':False}
    map_hash=jhash(core);manifest={**core,'mapHash':map_hash,'createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inventoryPath':str(Path(inventory_path).resolve())}
    build_deck(output,w,h,core['projectId'],map_hash,panels)
    manifest['initialDraftSha256']=fhash(output);Path(manifest_path).write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    return {'draft':str(output),'manifest':str(manifest_path),'draftSha256':manifest['initialDraftSha256'],'projectId':core['projectId'],'panelCount':len(panels)}

def properties(z):
    if 'docProps/custom.xml' not in z.namelist():return {}
    root=parse_xml(z.read('docProps/custom.xml'));return {p.get('name'):''.join(p.itertext()) for p in root}

def xf_values(shape):
    xf=shape.find('./p:spPr/a:xfrm',NS)
    if xf is None:xf=shape.find('./p:grpSpPr/a:xfrm',NS)
    if xf is None:return None
    if int(xf.get('rot','0'))%21600000 or xf.get('flipH') in ['1','true'] or xf.get('flipV') in ['1','true']:raise ValueError('Rotated/flipped layout boxes or groups need manual review.')
    off=xf.find('a:off',NS);ext=xf.find('a:ext',NS)
    if off is None or ext is None:return None
    values=[float(off.get('x')),float(off.get('y')),float(ext.get('cx')),float(ext.get('cy'))]
    if not all(math.isfinite(v) for v in values):raise ValueError('Non-finite geometry is invalid.')
    return (xf,*values)

def read_layout(draft,manifest_path,output,source_paths=None):
    if Path(output).exists():raise ValueError('Output already exists; choose a new layout report filename.')
    m=json.loads(Path(manifest_path).read_text());core={k:v for k,v in m.items() if k not in ['mapHash','createdAt','inventoryPath','initialDraftSha256']}
    if m.get('schema')!=FMT or jhash(core)!=m['mapHash']:raise ValueError('Internal binding manifest changed or is not supported.')
    wanted={p['id']:p for p in m['panels']};seen=set();found=[];warnings=[];errors=[]
    provided={fhash(p):str(p) for p in (source_paths or [])};expected={s.get('fileHash') for p in m['panels'] for s in p['sourceBindings'] if s.get('fileHash')};source_verified=bool(expected) and expected.issubset(provided)
    with load_zip(draft) as z:
        props=properties(z)
        if props.get('FigureLayoutProjectId')!=m['projectId'] or props.get('FigureLayoutMapHash')!=m['mapHash']:raise ValueError('Draft project marker is missing or does not match. Do not guess which source it belongs to.')
        presentation=parse_xml(z.read('ppt/presentation.xml'));sz=presentation.find('p:sldSz',NS);cw=float(sz.get('cx'))/EMU;ch=float(sz.get('cy'))/EMU
        if not all(math.isfinite(v) and v>0 for v in [cw,ch]):raise ValueError('Invalid slide dimensions.')
        rel=parse_xml(z.read('ppt/_rels/presentation.xml.rels'));mapping={r.get('Id'):r.get('Target') for r in rel if r.get('TargetMode')!='External'}
        slides=[]
        for s in presentation.findall('p:sldIdLst/p:sldId',NS):
            target=mapping.get(s.get(tag('r:id')),'');part='ppt/'+target.lstrip('/') if not target.startswith('/') else target.lstrip('/')
            if '..' in Path(part).parts:raise ValueError('Unexpected slide relationship path.')
            slides.append(part)
        def walk(container,slide_num,matrix=(1,1,0,0)):
            sx,sy,tx,ty=matrix
            if not all(math.isfinite(v) for v in matrix):raise ValueError('Non-finite group transform.')
            for shape in container:
                local=shape.tag.rsplit('}',1)[-1]
                if local=='grpSp':
                    vals=xf_values(shape)
                    if not vals:errors.append('Group transform missing.');continue
                    xf,x,y,w,h=vals;co=xf.find('a:chOff',NS);ce=xf.find('a:chExt',NS)
                    if co is None or ce is None or not all(math.isfinite(float(e.get(k))) for e,k in [(co,'x'),(co,'y'),(ce,'cx'),(ce,'cy')]) or min(float(ce.get('cx')),float(ce.get('cy')))<=0:errors.append('Invalid group transform.');continue
                    gx=w/float(ce.get('cx'));gy=h/float(ce.get('cy'));walk(shape,slide_num,(sx*gx,sy*gy,tx+sx*(x-float(co.get('x'))*gx),ty+sy*(y-float(co.get('y'))*gy)));continue
                if local not in ['sp','pic','graphicFrame','cxnSp']:continue
                nv=shape.find('./p:nvSpPr/p:cNvPr',NS)
                if nv is None:nv=shape.find('.//p:cNvPr',NS)
                if nv is None:continue
                name=nv.get('name','');desc=nv.get('descr','');marker_id=None
                if name.startswith(MARKER+m['projectId']+'::'):marker_id=name.split('::',2)[2]
                try:d=json.loads(desc)
                except (ValueError,TypeError):d={}
                if d.get('schema')==FMT:
                    if d.get('projectId')!=m['projectId'] or d.get('mapHash')!=m['mapHash']:errors.append('Conflicting marker on '+name);continue
                    if marker_id and marker_id!=d.get('panelId'):errors.append('Name/description panel IDs disagree.');continue
                    marker_id=d.get('panelId')
                if not marker_id:
                    if name!='Layout instructions':warnings.append({'type':'unmapped-shape','slide':slide_num,'name':name,'text':' '.join(shape.itertext())[:200]})
                    continue
                if marker_id not in wanted:errors.append('Unknown panel ID '+str(marker_id));continue
                if marker_id in seen:errors.append('Duplicate panel ID '+marker_id+'; a copied box must be resolved.');continue
                seen.add(marker_id);vals=xf_values(shape)
                if not vals:errors.append('Missing transform for '+marker_id);continue
                _,x,y,w,h=vals;b={'x':round((tx+sx*x)/EMU,6),'y':round((ty+sy*y)/EMU,6),'w':round(sx*w/EMU,6),'h':round(sy*h/EMU,6)}
                if not all(math.isfinite(v) for v in b.values()) or min(b['w'],b['h'])<=0:errors.append('Non-positive box '+marker_id);continue
                if b['x']<0 or b['y']<0 or b['x']+b['w']>cw+.001 or b['y']+b['h']>ch+.001:warnings.append({'type':'off-slide','panelId':marker_id})
                text='\n'.join(t.text or '' for t in shape.findall('.//a:t',NS));found.append({'id':marker_id,'slideNumber':slide_num,'bounds':b,'text':text,'sourceAssetIds':wanted[marker_id]['sourceAssetIds'],'sourceBindings':wanted[marker_id]['sourceBindings'], **({'parentPanelId':wanted[marker_id]['parentPanelId']} if 'parentPanelId' in wanted[marker_id] else {})})
        for n,part in enumerate(slides,1):
            tree=parse_xml(z.read(part)).find('p:cSld/p:spTree',NS)
            if tree is None:errors.append('No shape tree on slide '+str(n));continue
            walk(tree,n)
    if errors:raise ValueError('Cannot safely read layout: '+'; '.join(errors))
    report={'schema':FMT,'projectId':m['projectId'],'mapHash':m['mapHash'],'returnedDraftSha256':fhash(draft),'originalSourceVerified':source_verified,'missingSourceHashes':sorted(expected-set(provided)),'canvas':{'width':cw,'height':ch,'unit':'mm'},'selectedPanels':found,'omittedPanelIds':sorted(set(wanted)-seen),'warnings':warnings,'refinement':m['refinement'],'geometryIsApproximateIntent':True,'semanticGuideApprovalRequired':True,'userChatApprovalStillRequired':True,'scientificSourceEdited':False}
    report['layoutIntentHash']=jhash(report);Path(output).write_text(json.dumps(report,ensure_ascii=False,indent=2));return {'layoutReport':str(output),'selectedPanelCount':len(found),'omittedPanelIds':report['omittedPanelIds'],'warnings':warnings,'originalSourceVerified':source_verified,'layoutIntentHash':report['layoutIntentHash']}

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True)
    a=sp.add_parser('create');a.add_argument('inventory');a.add_argument('output');a.add_argument('--manifest',required=True);a.add_argument('--spec')
    a=sp.add_parser('read');a.add_argument('draft');a.add_argument('--manifest',required=True);a.add_argument('--output',required=True);a.add_argument('--source',action='append')
    args=ap.parse_args()
    try:
        result=create(args.inventory,args.output,args.manifest,args.spec) if args.cmd=='create' else read_layout(args.draft,args.manifest,args.output,args.source)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,KeyError,ET.ParseError,zipfile.BadZipFile,OSError) as e:ap.exit(2,str(e)+'\n')
if __name__=='__main__':main()
