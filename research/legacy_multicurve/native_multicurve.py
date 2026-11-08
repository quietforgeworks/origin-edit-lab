"""Explicit independent XY insertion, pinned legacy fixture, LabPlot-only.

This is NOT an Origin writer. Native-safe export fails before any I/O. The
research flag acknowledges unresolved global, opaque ID/count and per-object
metadata. No unknown field is guessed or normalized.
"""
from pathlib import Path
import argparse,copy,json,os,shutil,stat,struct,tempfile
from legacy_records import Walk,framed,name
from numeric_support import require,sha,convert_number,publish_noreplace
TEMPLATE_HASH='ea50c9b97b063898f654a6189b30ca5d8be8b52ad4c9469b3934cd009185265a'
SOURCE_URL='https://github.com/KDE/labplot/blob/0bd2e4094e92e74052ec161022d4e60aeb7605cd/tests/import_export/Project/data/origin8_test_tree_import.opj'
PROFILE='pinned-legacy-independent-xy-labplot-only-v1'
BLOCKER='Origin-safe export refused: global count-like fields, opaque cloned metadata and native lifecycle have not been verified'
SERIES_COUNTS=(2,5,10)
ROWS=50

def checked_path(path):
    p=Path(path);require('..' not in p.parts,'parent traversal refused');p=p.absolute()
    for a in (p,*p.parents):require(not a.is_symlink(),'symlink component refused')
    return p

def read_regular(path,limit):
    p=checked_path(path);s=p.stat();require(stat.S_ISREG(s.st_mode),'regular file required');require(s.st_size<=limit,'input byte limit')
    with p.open('rb') as f:
        b=f.read(limit+1)
    require(len(b)<=limit,'input byte limit');return b

def parse_raw(raw):
    require(type(raw) is bytes and len(raw)<=262144,'input byte limit')
    def pairs(items):
        d={}
        for k,v in items:require(k not in d,'duplicate JSON key');d[k]=v
        return d
    try:obj=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs)
    except (UnicodeError,ValueError,TypeError) as exc:raise ValueError('invalid strict UTF-8 JSON') from exc
    require(type(obj) is dict and set(obj)=={'schema','data_kind','series'},'unknown input keys')
    require(obj['schema']=='explicit-xy-v1' and obj['data_kind']=='synthetic','only explicitly synthetic experimental inputs')
    series=obj['series'];require(type(series) is list and len(series) in SERIES_COUNTS,'unsupported series count')
    parsed=[];ledger=[]
    for i,s in enumerate(series):
        require(type(s) is dict and set(s)=={'series_id','sheet','x_column','y_column','x','y'},'exact per-series fields required')
        xname=chr(65+2*i);yname=chr(66+2*i)
        require(s['series_id']==f'S{i+1:02d}' and s['sheet']=='Book1' and s['x_column']==xname and s['y_column']==yname,'explicit unique sequential identities required')
        require(type(s['x']) is list and type(s['y']) is list and len(s['x'])==len(s['y'])==ROWS,'each explicit X/Y must contain exactly 50 pairs; missing or unequal arrays rejected')
        values=[]
        for c in ('x','y'):
            col=[]
            for r,token in enumerate(s[c],1):
                v,item=convert_number(token,s['sheet'],r,s[c+'_column']);lo,hi=((-5.,55.) if c=='x' else (-.1,1.1))
                require(lo<=v<=hi,'value outside preserved graph axes');col.append(v);item['series_id']=s['series_id'];ledger.append(item)
            values.append(col)
        parsed.append({'identity':{k:s[k] for k in ('series_id','sheet','x_column','y_column')},'x':values[0],'y':values[1],
                       'x_dataset_id':1 if i==0 else 24+2*i,'y_dataset_id':2 if i==0 else 25+2*i})
    return obj,parsed,ledger

def inspect(blob,n):
    require(type(n) is int and n in (1,)+SERIES_COUNTS,'bad series count')
    w=Walk(blob).run();require(len(w.datasets)==25+2*(n-1),'dataset count mismatch')
    require(len(w.windows)==7 and [a['name'] for a in w.windows]==['Book3','MBook1','Book2','Book1','MBook2','Book4','Graph2'],'window inventory mismatch')
    sheet=w.windows[3]['layers'][0];graph=w.windows[6]['layers'][0]
    require(len(w.windows[3]['layers'])==len(w.windows[6]['layers'])==1,'layer mismatch')
    require(len(sheet['curves'])==2*n and len(graph['curves'])==n,'column/curve count mismatch')
    require(len(w.frames)==478+12*(n-1),'frame count mismatch')
    for i in range(n):
        ids=(1,2) if i==0 else (24+2*i,25+2*i)
        for c,did in enumerate(ids):
            h,d,m=w.datasets[did-1];col=chr(65+2*i+c)
            require(h.length==140 and d.length==500 and m.length==0,'unsupported dataset layout')
            require(name(h.payload[88:113])=='Book1_'+col,'dataset identity mismatch')
            require(struct.unpack_from('<III',h.payload,25)==(50,0,50),'dataset rows mismatch')
            require(h.payload[61]==10 and struct.unpack_from('<H',h.payload,22)[0]==(0x5121,0x6121)[c],'cell type mismatch')
            sh=sheet['curves'][2*i+c][0].payload
            require(len(sh)==489 and name(sh[18:30])==col and struct.unpack_from('<H',sh,4)[0]==did,'worksheet identity/selector mismatch')
            require(sh[17]==(3,0)[c] and struct.unpack_from('<H',sh,35)[0]==(0,ids[0])[c],'worksheet X/Y designation mismatch')
            require(struct.unpack_from('<II',sh,7)==(0,50),'opaque worksheet bounds changed')
        ch=graph['curves'][i][0].payload
        require(len(ch)==489 and (struct.unpack_from('<H',ch,35)[0],struct.unpack_from('<H',ch,4)[0])==ids,'explicit graph XY selectors mismatch')
        require(struct.unpack_from('<II',ch,7)==(0,50) and ch[76]==202 and ch[17]==1,'cloned graph metadata changed')
    return w

def column_payload(values):return b''.join(b'\0\0'+struct.pack('<d',v) for v in values)

def patch_bytes(template,raw,*,research_only=False):
    require(research_only is True,BLOCKER)
    require(type(template) is bytes and sha(template)==TEMPLATE_HASH,'exact pinned public template required')
    before=inspect(template,1);obj,series,ledger=parse_raw(raw);n=len(series)
    sheet=before.windows[3]['layers'][0];graph=before.windows[6]['layers'][0]
    edits=[]
    def edit(p,old,new,kind):
        require(template[p:p+len(old)]==old,'old bytes mismatch')
        edits.append({'old_offset':p,'old_length':len(old),'new_length':len(new),'kind':kind,'old_sha256':sha(old),'new_sha256':sha(new),'new':new})
    for c,key in enumerate(('x','y')):
        d=before.datasets[c][1];edit(d.offset,template[d.offset:d.end],framed(column_payload(series[0][key])),'replace-original-'+key+'-data')
    ds=[];sc=[];gc=[]
    for i,s in enumerate(series[1:],1):
        for c,key in enumerate(('x','y')):
            h,d,m=before.datasets[c];hp=bytearray(h.payload);label='Book1_'+s['identity'][key+'_column']
            hp[88:113]=label.encode().ljust(25,b'\0')
            ds.append(framed(bytes(hp))+framed(column_payload(s[key]))+framed(m.payload))
            sh,sd=sheet['curves'][c];p=bytearray(sh.payload)
            struct.pack_into('<H',p,4,s[key+'_dataset_id']);p[18:30]=s['identity'][key+'_column'].encode().ljust(12,b'\0')
            if key=='y':struct.pack_into('<H',p,35,s['x_dataset_id'])
            sc.append(framed(bytes(p))+framed(sd.payload))
        gh,gd=graph['curves'][0];p=bytearray(gh.payload)
        struct.pack_into('<H',p,4,s['y_dataset_id']);struct.pack_into('<H',p,35,s['x_dataset_id'])
        gc.append(framed(bytes(p))+framed(gd.payload))
    for p,b,kind in ((before.datasets_end.offset,b''.join(ds),'append-datasets'),(sheet['curves_end'].offset,b''.join(sc),'append-worksheet-columns'),(graph['curves_end'].offset,b''.join(gc),'append-graph-curves')):edit(p,b'',b,kind)
    edits.sort(key=lambda e:e['old_offset']);parts=[];cursor=0;delta=0
    for e in edits:
        p=e['old_offset'];require(p>=cursor,'overlapping edits');parts.extend((template[cursor:p],e['new']));e['new_offset']=p+delta;delta+=e['new_length']-e['old_length'];cursor=p+e['old_length']
    parts.append(template[cursor:]);candidate=b''.join(parts);after=inspect(candidate,n)
    require(candidate[after.tail_start:]==template[before.tail_start:],'opaque tail changed')
    # Remove only inserted frames and restore only the original two data frames.
    reverse=[];cursor=0
    for e in edits:
        p=e['new_offset'];require(candidate[p:p+e['new_length']]==e['new'],'candidate splice mismatch')
        reverse.extend((candidate[cursor:p],template[e['old_offset']:e['old_offset']+e['old_length']]));cursor=p+e['new_length']
    reverse.append(candidate[cursor:]);require(b''.join(reverse)==template,'unrelated bytes altered')
    manifest={'profile':PROFILE,'template_sha256':TEMPLATE_HASH,'template_source_url':SOURCE_URL,'candidate_sha256':sha(candidate),'candidate_bytes':len(candidate),
        'raw_sha256':sha(raw),'data_kind':'synthetic','series_count':n,'rows_per_series':ROWS,'identities':[{**s['identity'],'x_dataset_id':s['x_dataset_id'],'y_dataset_id':s['y_dataset_id']} for s in series],
        'splices':[{k:v for k,v in e.items() if k!='new'} for e in edits],'binary64_conversion_ledger':ledger,
        'frame_count':len(after.frames),'dataset_count':len(after.datasets),'original_dataset_ids_preserved':True,'all_unrelated_original_bytes_preserved':True,
        'opaque_global_header_preserved_sha256':sha(before.global_header.payload),'opaque_tail_preserved_sha256':sha(template[before.tail_start:]),
        'safe_native_export_supported':False,'native_safety_blocker':BLOCKER,'Origin_reopen_update_recalculate_save':'NOT_RUN'}
    return candidate,manifest

def generate(template_path,raw_path,outdir,*,research_only=False):
    require(research_only is True,BLOCKER)
    outdir=checked_path(outdir);require(not outdir.exists(),'output exists');require(outdir.parent.is_dir(),'output parent missing')
    template=read_regular(template_path,262144);raw=read_regular(raw_path,262144);candidate,m=patch_bytes(template,raw,research_only=True)
    stage=Path(tempfile.mkdtemp(prefix='.multicurve-',dir=outdir.parent))
    try:
        for name,b in (('candidate.opj',candidate),('raw.json',raw),('rollback.opj',template),('manifest.json',(json.dumps(m,indent=2,allow_nan=False)+'\n').encode())):
            (stage/name).write_bytes(b);require((stage/name).read_bytes()==b,'write mismatch')
        require(read_regular(template_path,262144)==template and read_regular(raw_path,262144)==raw,'source changed')
        checked_path(outdir);publish_noreplace(stage,outdir)
    finally:
        if stage.exists():shutil.rmtree(stage)
    return m
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--template',type=Path,required=True);p.add_argument('--raw',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--labplot-only-research',action='store_true')
    a=p.parse_args();m=generate(a.template,a.raw,a.out,research_only=a.labplot_only_research);print(json.dumps({k:m[k] for k in ('series_count','candidate_sha256','safe_native_export_supported')}))
