"""Exact-fixture LabPlot-only allocation experiment, not an Origin-safe writer.

Only documented dataset fields and their own record framing are edited. All
later bytes relocate unchanged. Unknown native range/pointer semantics remain
unproved; native-safe export is deliberately refused even after LabPlot success.
"""
from __future__ import annotations
import argparse, csv, io, json, math, shutil, struct, tempfile
from pathlib import Path
from numeric_support import Rejected, require, sha, convert_number, publish_noreplace, MISSING

TEMPLATE_HASH='ea50c9b97b063898f654a6189b30ca5d8be8b52ad4c9469b3934cd009185265a'
TEMPLATE_SIZE=231494
SOURCE_URL='https://github.com/KDE/labplot/blob/0bd2e4094e92e74052ec161022d4e60aeb7605cd/tests/import_export/Project/data/origin8_test_tree_import.opj'
COUNTS=(51,257,1024)
PROFILE='exact-fixture-labplot-only-allocation-resize-v1'
BLOCKER='Origin-safe allocation expansion refused: native meaning of worksheet/curve fields +7/+11 and any opaque absolute-offset dependencies is not established'
ORIGINAL_END=228955
FRAME_COUNT=478

def checked_path(path):
    """Reject lexical traversal and existing symlinks, including all ancestors.

    This is preflight validation, not a sandbox against concurrent ancestor
    replacement. Callers must use a trusted, stable working directory tree.
    """
    raw=Path(path)
    require('..' not in raw.parts,'parent traversal refused; use an explicit path')
    p=raw.absolute()
    for part in (p,*p.parents):
        require(not part.is_symlink(),'symlink path component refused: '+str(part))
    return p

def frame(blob,p):
    require(type(p) is int and p>=0 and p+5<=len(blob),'truncated frame header')
    n=struct.unpack_from('<I',blob,p)[0]
    require(blob[p+4]==10 and p+5+n+bool(n)<=len(blob),'bad frame length/delimiter')
    require(not n or blob[p+5+n]==10,'bad payload delimiter')
    return {'offset':p,'length':n,'end':p+5+n+bool(n),'payload':blob[p+5:p+5+n]}

def framed(payload):
    require(type(payload) is bytes and len(payload)<2**32,'bad frame payload')
    return struct.pack('<I',len(payload))+b'\n'+payload+(b'\n' if payload else b'')

def ascii_name(payload):
    require(b'\0' in payload,'unterminated identity')
    try:return payload.split(b'\0',1)[0].decode('ascii')
    except UnicodeError as exc:raise Rejected('invalid identity') from exc

def inspect(blob,rows):
    require(type(rows) is int and rows in (50,)+COUNTS,'unsupported allocation')
    delta=20*(rows-50)
    require(type(blob) is bytes and len(blob)==TEMPLATE_SIZE+delta,'wrong file size/type')
    require(blob[:17]==b'CPYA 4,2878 724#\n','wrong legacy signature')
    records=[];p=17
    for _ in range(FRAME_COUNT):
        f=frame(blob,p);records.append(f);p=f['end']
    require(p==ORIGINAL_END+delta,'wrong framed/tail boundary')
    require(records[0]['length']==75 and records[1]['length']==0,'global header framing changed')
    datasets=[];p=records[1]['end']
    while True:
        h=frame(blob,p)
        if h['length']==0:break
        require(h['length']==140,'unexpected dataset header width')
        d=frame(blob,h['end']);m=frame(blob,d['end'])
        require(m['length']==0,'dataset mask unsupported')
        datasets.append({'id_one_based':len(datasets)+1,'name':ascii_name(h['payload'][88:113]),
            'header':h,'data':d,'mask':m})
        p=m['end']
        require(len(datasets)<=25,'extra dataset')
    require(len(datasets)==25 and p==35764+delta,'dataset list or global ID count changed')
    for i,ds in enumerate(datasets[:2]):
        h=ds['header']['payload'];d=ds['data']['payload']
        require(ds['name']=='Book1_'+'AB'[i] and h[61]==10,'XY identity/cell width changed')
        require(struct.unpack_from('<H',h,22)[0]==(0x5121,0x6121)[i],'XY data type changed')
        require(struct.unpack_from('<III',h,25)==(rows,0,rows),'XY allocation/active bounds differ')
        require(len(d)==10*rows,'XY frame length differs')
        for r in range(rows):
            require(d[r*10:r*10+2]==b'\0\0','unsupported cell tag')
            v=struct.unpack_from('<d',d,r*10+2)[0]
            require(math.isfinite(v) and v!=MISSING,'missing/nonfinite cell')
    for ordinal,idx,name,designation,x in ((261,1,'A',3,0),(263,2,'B',0,1)):
        h=records[ordinal]['payload']
        require(len(h)==489 and struct.unpack_from('<H',h,4)[0]==idx and ascii_name(h[18:30])==name,'worksheet binding changed')
        require(h[17]==designation and struct.unpack_from('<H',h,35)[0]==x,'worksheet designation changed')
        require(struct.unpack_from('<II',h,7)==(0,50),'opaque worksheet fields changed')
    w,l,c=(records[i]['payload'] for i in (412,413,451))
    require(len(w)==244 and len(l)==341 and len(c)==489 and ascii_name(w[2:27])=='Graph2','graph ownership changed')
    require((struct.unpack_from('<H',c,35)[0],struct.unpack_from('<H',c,4)[0])==(1,2),'graph dataset IDs changed')
    require(c[76]==202 and c[17]==1 and struct.unpack_from('<II',c,7)==(0,50),'graph style/opaque selector changed')
    require(struct.unpack_from('<ddd',l,15)==(-5.,55.,10.) and struct.unpack_from('<ddd',l,58)==(-.1,1.1,.2),'axes changed')
    return {'sha256':sha(blob),'bytes':len(blob),'allocated_rows':rows,'active_rows':rows,
        'frame_count':len(records),'framed_end':records[-1]['end'],
        'frame_offsets_lengths':[[r['offset'],r['length']] for r in records],
        'dataset_ids_names':[[d['id_one_based'],d['name']] for d in datasets],
        'dataset_list_terminator':p,'graph_start':records[412]['offset'],
        'graph_sha256':sha(blob[records[412]['offset']:records[-1]['end']]),
        'opaque_tail_sha256':sha(blob[records[-1]['end']:]),
        'graph_dataset_ids_one_based':{'x':1,'y':2},'opaque_range_like_fields_preserved':[0,50]}

def parse_csv(raw):
    require(type(raw) is bytes and len(raw)<=262144,'CSV byte limit exceeded')
    try:rows=list(csv.reader(io.StringIO(raw.decode('utf-8'),newline=''),strict=True))
    except (UnicodeError,csv.Error) as exc:raise Rejected('malformed UTF-8 CSV') from exc
    require(rows and rows[0]==['A','B'],'exact A,B header required')
    require(len(rows)-1 in COUNTS,'only 51,257,1024 rows validated for experiment')
    values=[];ledger=[]
    for r,row in enumerate(rows[1:],1):
        require(len(row)==2,'exactly two cells required');pair=[]
        for c,token in enumerate(row):
            v,item=convert_number(token,'Book1',r,'AB'[c]);lo,hi=((-5.,55.),(-.1,1.1))[c]
            require(lo<=v<=hi,'value outside unchanged native axes');pair.append(v);ledger.append(item)
        values.append(pair)
    return values,ledger

def _replacements(template,values):
    n=len(values);splices=[];p=103
    for c in range(2):
        h=frame(template,p);d=frame(template,h['end']);m=frame(template,d['end']);new=bytearray(h['payload'])
        struct.pack_into('<I',new,25,n);struct.pack_into('<I',new,33,n)
        payload=b''.join(b'\0\0'+struct.pack('<d',r[c]) for r in values)
        for f,replacement,kind in ((h,framed(bytes(new)),'dataset-header'),(d,framed(payload),'dataset-data-frame')):
            splices.append({'old_offset':f['offset'],'old_length':f['end']-f['offset'],'new_length':len(replacement),
                'kind':kind,'dataset_id_one_based':c+1,'old_hex':template[f['offset']:f['end']].hex(),'new_hex':replacement.hex()})
        p=m['end']
    return splices

def _apply(template,splices):
    pieces=[];cursor=0;delta=0
    for s in splices:
        p=s['old_offset'];require(p>=cursor,'overlapping splices');old=bytes.fromhex(s['old_hex']);new=bytes.fromhex(s['new_hex'])
        require(template[p:p+len(old)]==old,'splice old bytes differ')
        pieces.extend((template[cursor:p],new));s['new_offset']=p+delta
        delta+=len(new)-len(old);cursor=p+len(old)
    pieces.append(template[cursor:]);return b''.join(pieces)

def patch_bytes(template,raw,*,research_only=False):
    require(research_only is True,BLOCKER)
    require(type(template) is bytes and sha(template)==TEMPLATE_HASH,'exact public template required')
    before=inspect(template,50);values,ledger=parse_csv(raw);n=len(values)
    splices=_replacements(template,values);candidate=_apply(template,splices);after=inspect(candidate,n)
    require(before['dataset_ids_names']==after['dataset_ids_names'],'dataset global indices changed')
    require(before['graph_sha256']==after['graph_sha256'] and before['opaque_tail_sha256']==after['opaque_tail_sha256'],'graph/tail bytes changed')
    # Validate every relocated frame, not merely the graph. The complete original
    # stream is preserved except two documented header fields and two data frames.
    oldframes=before['frame_offsets_lengths'];newframes=after['frame_offsets_lengths']
    for i,((op,ol),(np,nl)) in enumerate(zip(oldframes,newframes)):
        a=frame(template,op);b=frame(candidate,np)
        if i in (3,6):require(nl==n*10,'wrong resized data frame')
        elif i in (2,5):
            aa=bytearray(a['payload']);bb=bytearray(b['payload'])
            for off in (25,33):aa[off:off+4]=bb[off:off+4]=b'\0'*4
            require(aa==bb and ol==nl,'unapproved dataset header mutation')
        else:require(template[op:a['end']]==candidate[np:b['end']],'unapproved relocated frame mutation')
    manifest={'profile':PROFILE,'template_sha256':TEMPLATE_HASH,'template_source_url':SOURCE_URL,
        'candidate_sha256':sha(candidate),'candidate_bytes':len(candidate),'raw_csv_sha256':sha(raw),
        'allocated_rows':n,'active_rows':n,'splices':splices,'binary64_conversion_ledger':ledger,
        'relocation_delta_bytes':20*(n-50),'unchanged_native_graph_bytes':True,
        'unchanged_global_dataset_indices':True,'unknown_metadata_preserved_not_semantically_validated':True,
        'safe_native_export_supported':False,'native_safety_blocker':BLOCKER,
        'Origin_reopen_update_recalculate_save':'NOT_RUN','acceptance_scope':'LabPlot-only exploratory exact-fixture allocation resize; NOT Origin compatibility'}
    require(restore_bytes(candidate,manifest)==template,'rollback failed')
    return candidate,manifest,before,after

def restore_bytes(candidate,m):
    require(type(m) is dict and m.get('profile')==PROFILE,'wrong manifest profile')
    require(type(candidate) is bytes and m.get('candidate_sha256')==sha(candidate),'candidate hash mismatch')
    n=m.get('allocated_rows');require(type(n) is int and n in COUNTS,'bad allocation')
    require(len(candidate)==TEMPLATE_SIZE+20*(n-50),'bad candidate length')
    edits=m.get('splices');require(type(edits) is list and len(edits)==4,'wrong splice count')
    pieces=[];cursor=0;delta=0
    expected=((103,146,'dataset-header',1),(249,506,'dataset-data-frame',1),(760,146,'dataset-header',2),(906,506,'dataset-data-frame',2))
    for e,(op,ol,kind,idx) in zip(edits,expected):
        require(type(e) is dict and all(type(e.get(k)) is int for k in ('old_offset','old_length','new_offset','new_length','dataset_id_one_based')),'bad splice types')
        nl=ol if kind=='dataset-header' else n*10+6
        require((e['old_offset'],e['old_length'],e['new_offset'],e['new_length'],e.get('kind'),e['dataset_id_one_based'])==(op,ol,op+delta,nl,kind,idx),'wrong splice schema/boundary')
        try:old=bytes.fromhex(e['old_hex']);new=bytes.fromhex(e['new_hex'])
        except (ValueError,TypeError,KeyError) as exc:raise Rejected('bad splice bytes') from exc
        p=op+delta;require(len(old)==ol and len(new)==nl and candidate[p:p+nl]==new,'splice content differs')
        pieces.extend((candidate[cursor:p],old));cursor=p+nl;delta+=nl-ol
    pieces.append(candidate[cursor:]);restored=b''.join(pieces)
    require(sha(restored)==TEMPLATE_HASH and m.get('template_sha256')==TEMPLATE_HASH,'rollback source mismatch')
    inspect(restored,50);return restored

def generate(template_path,csv_path,outdir,*,research_only=False):
    require(research_only is True,BLOCKER)
    outdir=checked_path(outdir);require(not outdir.exists(),'output exists')
    require(outdir.parent.is_dir(),'unsafe output parent')
    template_path=checked_path(template_path);csv_path=checked_path(csv_path)
    require(template_path.is_file() and csv_path.is_file(),'input must be regular non-symlink files')
    template=template_path.read_bytes();raw=csv_path.read_bytes();candidate,m,before,after=patch_bytes(template,raw,research_only=True)
    stage=Path(tempfile.mkdtemp(prefix='.labplot-only-resize-',dir=outdir.parent))
    try:
        files={'candidate.opj':candidate,'raw.csv':raw,'rollback.opj':restore_bytes(candidate,m)}
        for name,b in files.items():(stage/name).write_bytes(b)
        for name,obj in (('manifest.json',m),('before.json',before),('after.json',after)):(stage/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
        for name,b in files.items():require((stage/name).read_bytes()==b,'written artifact differs')
        for path in (template_path,csv_path,outdir):checked_path(path)
        require(template_path.read_bytes()==template and csv_path.read_bytes()==raw,'input changed during generation')
        publish_noreplace(stage,outdir)
    finally:
        if stage.exists():shutil.rmtree(stage)
    return m

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--template',required=True,type=Path);p.add_argument('--csv',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    p.add_argument('--labplot-only-research',action='store_true',help='Acknowledge unresolved native safety; never an Origin-safe export')
    a=p.parse_args();m=generate(a.template,a.csv,a.out,research_only=a.labplot_only_research)
    print(json.dumps({k:m[k] for k in ('allocated_rows','candidate_sha256','acceptance_scope','safe_native_export_supported')}))
