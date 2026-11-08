"""Narrow experimental active-prefix edits in one hash-pinned legacy OPJ.

Only 7, 49 and 50 active rows, still allocated as 50, are accepted. This is a
source-to-LabPlot research adapter, NOT proof of Origin compatibility. It does
not edit the unresolved graph/worksheet range-like fields, serialize a graph,
resize records, sanitize a source template, or remove its inactive raw cells.
"""
from __future__ import annotations
import argparse, csv, io, json, math, shutil, struct, tempfile
from pathlib import Path
from numeric_support import Rejected, require, sha, convert_number, publish_noreplace, MISSING

TEMPLATE_HASH='ea50c9b97b063898f654a6189b30ca5d8be8b52ad4c9469b3934cd009185265a'
TEMPLATE_SIZE=231494
SOURCE_URL='https://github.com/KDE/labplot/blob/0bd2e4094e92e74052ec161022d4e60aeb7605cd/tests/import_export/Project/data/origin8_test_tree_import.opj'
DATASETS=(('Book1_A',103,249,1),('Book1_B',760,906,2))
SUPPORTED_ACTIVE_ROWS=(7,49,50)
PROFILE='same-allocation-active-prefix-experiment-v1'

def record(blob,p,n):
    require(type(p) is int and type(n) is int and p>=0 and n>=0,'bad frame request')
    require(p+5+n+(n!=0)<=len(blob),'truncated frame')
    require(struct.unpack_from('<I',blob,p)[0]==n and blob[p+4]==10,'frame header changed')
    require(not n or blob[p+5+n]==10,'frame delimiter changed')
    return blob[p+5:p+5+n]

def cstring(b):
    require(b'\0' in b,'missing string terminator')
    try:return b.split(b'\0',1)[0].decode('ascii')
    except UnicodeError as exc:raise Rejected('non-ASCII identity') from exc

def inspect(blob):
    require(isinstance(blob,bytes) and len(blob)==TEMPLATE_SIZE,'unexpected file size/type')
    require(blob[:17]==b'CPYA 4,2878 724#\n','wrong source format signature')
    frames=[];p=17
    while p<228955:
        require(p+5<=len(blob),'truncated framing')
        n=struct.unpack_from('<I',blob,p)[0];record(blob,p,n);frames.append((p,n));p+=5+n+bool(n)
    require(p==228955 and len(frames)==478,'framed region boundary changed')
    columns=[]
    for name,hp,dp,idx in DATASETS:
        require((hp,140) in frames and (dp,500) in frames,'dataset frame ownership changed')
        h,d=record(blob,hp,140),record(blob,dp,500)
        require(cstring(h[88:113])==name and h[61]==10,'dataset identity/value width changed')
        require(struct.unpack_from('<H',h,22)[0]==(0x5121 if idx==1 else 0x6121),'dataset type changed')
        allocated,begin,end=struct.unpack_from('<III',h,25)
        require(allocated==50 and begin==0 and end in SUPPORTED_ACTIVE_ROWS,'unsupported dataset bounds')
        cells=[]
        for r in range(50):
            require(d[r*10:r*10+2]==b'\0\0','cell tag changed')
            b=d[r*10+2:r*10+10];v=struct.unpack('<d',b)[0]
            require(math.isfinite(v) and v!=MISSING,'nonfinite or missing source cell')
            cells.append(b.hex())
        columns.append({'name':name,'allocated':allocated,'begin':begin,'end_exclusive':end,'binary64_le':cells})
    require(columns[0]['end_exclusive']==columns[1]['end_exclusive'],'X/Y active bounds differ')
    for hp,idx,name,designation,x in [(123513,1,'A',3,0),(124015,2,'B',0,1)]:
        h=record(blob,hp,489)
        require(struct.unpack_from('<H',h,4)[0]==idx and cstring(h[18:30])==name,'worksheet binding changed')
        require(h[17]==designation and struct.unpack_from('<H',h,35)[0]==x,'worksheet designation changed')
        require(struct.unpack_from('<II',h,7)==(0,50),'unresolved worksheet bytes changed')
    w,l,c=record(blob,182277,244),record(blob,182527,341),record(blob,219404,489)
    require(cstring(w[2:27])=='Graph2','graph identity changed')
    require((struct.unpack_from('<H',c,35)[0],struct.unpack_from('<H',c,4)[0])==(1,2),'graph source bindings changed')
    require(c[76]==202 and c[17]==1,'line-symbol curve changed')
    require(struct.unpack_from('<II',c,7)==(0,50),'unresolved graph bytes changed')
    require(struct.unpack_from('<ddd',l,15)==(-5.,55.,10.) and struct.unpack_from('<ddd',l,58)==(-.1,1.1,.2),'axes changed')
    return {'sha256':sha(blob),'size':len(blob),'frame_count':len(frames),'columns':columns,
            'graph_source_bindings_one_based':{'x':1,'y':2},'graph_span':[182277,228955],
            'graph_sha256':sha(blob[182277:228955]),'opaque_tail_sha256':sha(blob[228955:]),
            'unresolved_curve_fields_u32_at_7_11':[0,50]}

def ranges(n):
    require(type(n) is int and n in SUPPORTED_ACTIVE_ROWS,'unvalidated active-row count; allocation changes unsupported')
    return sorted([(hp+5+33,4,'end_exclusive') for _,hp,_,_ in DATASETS]+[(dp+7+r*10,8,'cell') for _,_,dp,_ in DATASETS for r in range(n)])

def parse_csv(raw):
    require(isinstance(raw,bytes) and len(raw)<=32768,'CSV bytes required, maximum 32768')
    try:rows=list(csv.reader(io.StringIO(raw.decode('utf-8'),newline=''),strict=True))
    except (UnicodeError,csv.Error) as exc:raise Rejected('malformed UTF-8 CSV') from exc
    require(rows and rows[0]==['A','B'],'require exact A,B header')
    n=len(rows)-1;ranges(n);values=[];ledger=[]
    for r,row in enumerate(rows[1:],1):
        require(len(row)==2,'exactly two cells per row required');pair=[]
        for c,token in enumerate(row):
            value,entry=convert_number(token,'Book1',r,'AB'[c])
            low,high=(-5.,55.) if c==0 else (-.1,1.1)
            require(low<=value<=high,'value outside preserved native axes')
            pair.append(value);ledger.append(entry)
        values.append(pair)
    return values,ledger

def patch_bytes(template,raw):
    require(isinstance(template,bytes) and len(template)==TEMPLATE_SIZE and sha(template)==TEMPLATE_HASH,'template must match exact public fixture')
    before=inspect(template);values,ledger=parse_csv(raw);n=len(values);result=bytearray(template)
    replacements=[]
    for _,hp,dp,idx in DATASETS:
        struct.pack_into('<I',result,hp+5+33,n)
        for r,pair in enumerate(values):struct.pack_into('<d',result,dp+7+r*10,pair[idx-1])
    result=bytes(result);after=inspect(result);allowed=set()
    for offset,size,kind in ranges(n):
        allowed.update(range(offset,offset+size))
        replacements.append({'offset':offset,'size':size,'kind':kind,'old_hex':template[offset:offset+size].hex(),'new_hex':result[offset:offset+size].hex()})
    changes=[i for i,(a,b) in enumerate(zip(template,result)) if a!=b]
    require(changes and set(changes)<=allowed,'no-op or unrelated bytes changed')
    untouched=bytes(v for i,v in enumerate(template) if i not in allowed)
    require(untouched==bytes(v for i,v in enumerate(result) if i not in allowed),'unapproved byte changed')
    require(before['graph_sha256']==after['graph_sha256'],'graph serialization changed')
    m={'profile':PROFILE,'template_sha256':TEMPLATE_HASH,'template_source_url':SOURCE_URL,
       'candidate_sha256':sha(result),'candidate_bytes':len(result),'raw_csv_sha256':sha(raw),
       'active_rows':n,'allocated_rows':50,'binary64_conversion_ledger':ledger,'replacements':replacements,
       'allowed_byte_count':len(allowed),'changed_byte_offsets':changes,'preserved_byte_sha256':sha(untouched),
       'native_graph_source_bytes_unchanged':True,'source_inactive_cells_retained':True,
       'unknown_curve_range_fields_untouched':True,'safe_for_private_template_sanitization':False,
       'Origin_reopen_update_save_recalculation':'NOT_RUN','native_row_expansion_supported':False,
       'acceptance_scope':'Experimental exact-template dataset active prefix; only separately observed LabPlot behavior. Not Origin compatibility.'}
    require(restore_bytes(result,m)==template,'rollback not byte-exact')
    return result,m,before,after

def restore_bytes(candidate,m):
    require(isinstance(m,dict) and m.get('profile')==PROFILE,'unknown manifest profile')
    require(isinstance(candidate,bytes) and len(candidate)==TEMPLATE_SIZE,'invalid candidate length/type')
    require(m.get('template_sha256')==TEMPLATE_HASH and m.get('candidate_sha256')==sha(candidate),'candidate or template hash differs')
    n=m.get('active_rows');expected=ranges(n);edits=m.get('replacements')
    require(isinstance(edits,list) and len(edits)==len(expected),'wrong replacement count')
    restored=bytearray(candidate)
    for e,(p,size,kind) in zip(edits,expected):
        require(isinstance(e,dict) and type(e.get('offset')) is int and type(e.get('size')) is int,'bad replacement types')
        require((e['offset'],e['size'],e.get('kind'))==(p,size,kind),'wrong replacement schema/range')
        try:old,new=bytes.fromhex(e['old_hex']),bytes.fromhex(e['new_hex'])
        except (KeyError,ValueError,TypeError) as exc:raise Rejected('bad replacement hex') from exc
        require(len(old)==len(new)==size and candidate[p:p+size]==new,'replacement content mismatch')
        restored[p:p+size]=old
    require(sha(restored)==TEMPLATE_HASH,'reconstructed source hash differs')
    # Hash guard makes all unlisted and inactive bytes part of verification.
    inspect(bytes(restored));return bytes(restored)

def generate(template_path,csv_path,outdir):
    outdir=Path(outdir).absolute()
    require(not outdir.exists() and not outdir.is_symlink(),'output exists; no overwrite')
    require(outdir.parent.is_dir(),'output parent must exist')
    template=Path(template_path).read_bytes();raw=Path(csv_path).read_bytes()
    candidate,m,before,after=patch_bytes(template,raw)
    stage=Path(tempfile.mkdtemp(prefix='.active-rows-',dir=outdir.parent))
    try:
        files={'candidate.opj':candidate,'raw.csv':raw,'rollback.opj':restore_bytes(candidate,m)}
        for name,b in files.items():(stage/name).write_bytes(b)
        for name,obj in [('manifest.json',m),('before.json',before),('after.json',after)]:(stage/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
        for name,b in files.items():require((stage/name).read_bytes()==b,'written file mismatch')
        publish_noreplace(stage,outdir)
    finally:
        if stage.exists():shutil.rmtree(stage)
    return m

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--template',required=True,type=Path);parser.add_argument('--csv',required=True,type=Path);parser.add_argument('--out',required=True,type=Path)
    a=parser.parse_args();m=generate(a.template,a.csv,a.out)
    print(json.dumps({k:m[k] for k in ('profile','active_rows','allocated_rows','candidate_sha256','acceptance_scope')}))
