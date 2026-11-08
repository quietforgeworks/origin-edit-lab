"""Experimental CPYUA embedded graph explicit-selector binding.

Sparse-frame decoder newly authored from on-disk record boundaries and grammar
observations, with bounded full-record validation; no GPL implementation code.
CPYA selector semantics independently corroborated by liborigin static source
(cited in embedded_selector_binding.py) apply to the reconstructed same-layout
headers. Numeric decoder remains the approved Apache-2.0 quantized dependency
via modern_embedded_reader.py. No Origin rendering/save validation claimed.
"""
from __future__ import annotations
import struct
import hashlib
from modern_embedded_reader import read_modern_embedded_numeric
from embedded_curve_adapter import NAME, _dataset_signature, _anchor_signature

class SparseFormatError(ValueError):pass

def read_varint(blob:bytes,pos:int)->tuple[int,int]:
 value=shift=0
 for _ in range(5):
  if pos>=len(blob):raise SparseFormatError('Truncated varint')
  byte=blob[pos];pos+=1;value|=(byte&127)<<shift
  if byte<128:return value,pos
  shift+=7
 raise SparseFormatError('Overlong varint')

def decode_sparse(blob:bytes,start:int,end:int,*,max_output:int=1024)->bytes:
 if not 0<=start<=end<=len(blob):raise SparseFormatError('Bad frame bounds')
 out=bytearray();pos=start
 while pos<end:
  code=blob[pos];pos+=1
  if 0x80<=code<=0xbf:
   out.extend(b'\0'*(code-0x80+3))
   # Skip is its OWN opcode. The next opcode can be RLE, not only literal!
  elif 0xc0<=code<=0xc3:
   if pos>=end:raise SparseFormatError('Truncated repeat opcode')
   out.extend(bytes([blob[pos]])*(code-0xc0+3));pos+=1
  elif code<0x80:
   if pos+code>end:raise SparseFormatError('Literal crosses frame boundary')
   out.extend(blob[pos:pos+code]);pos+=code
  else:raise SparseFormatError('Unknown sparse opcode')
  if len(out)>max_output:raise SparseFormatError('Sparse output exceeds guard')
 return bytes(out)

def sparse_frame(blob:bytes,pos:int)->tuple[bytes,int,int]:
 if not 0<=pos<len(blob) or blob[pos]!=0x80:raise SparseFormatError('Not a supported sparse frame')
 size,start=read_varint(blob,pos+1)
 if size>2048:raise SparseFormatError('Sparse frame too large')
 end=start+size+1 # observed CPYUA frame stores byte length minus one
 return decode_sparse(blob,start,end),start,end

def _read_modern_xy_bindings_unscoped(blob:bytes)->dict:
 """Internal structural experiment ONLY: no complete unknown-slot grammar."""
 result=read_modern_embedded_numeric(blob)
 pages=result['pages']
 if not pages:raise SparseFormatError('No graph page boundary')
 data_end=min(p['offset'] for p in pages);frames=[]
 for pos in range(data_end):
  if blob[pos]!=0x80:continue
  try:h,start,end=sparse_frame(blob,pos)
  except SparseFormatError:continue
  if len(h)!=147 or end>=data_end:continue
  if blob[end]!=5:raise SparseFormatError('Unrecognized numeric envelope after dataset header; refuse to skip selector slot')
  name=h[88:113].split(b'\0',1)[0]
  if not NAME.fullmatch(name):raise SparseFormatError('Unknown dataset identity before graph')
  frames.append({'offset':pos,'start':start,'end':end,'header':h,'name':name.decode('ascii')})
 if not frames or len(set(f['name'] for f in frames))!=len(frames):raise SparseFormatError('Ambiguous dataset headers')
 columns={c['name']:c for c in result['columns']}
 if len(columns)!=len(frames) or any(f['name'] not in columns for f in frames):
  raise SparseFormatError('Sparse header inventory and independently decoded numeric inventory disagree')
 for i,f in enumerate(frames):
  c=columns[f['name']];h=f['header'];allocated=struct.unpack_from('<I',h,25)[0]
  if f['end']!=c['record_offset']+1 or c['stored_count']>allocated:
   raise SparseFormatError('Dataset header/numeric envelope boundary disagreement')
  f.update(selector=i+1,allocated_rows=allocated,last_row_field=struct.unpack_from('<I',h,33)[0])
 curves=[]
 for token in result['curve_tokens']:
  matches=[]
  for pos in range(max(data_end,token['offset']-5),token['offset']+1):
   try:a,start,end=sparse_frame(blob,pos)
   except SparseFormatError:continue
   if len(a)!=515 or a[:4]!=b'\1\0\0\0':continue
   # DataPlot magic immediately after its length prefix and literal-1 tag.
   if blob.find(b'\x01\x58\x80\x09\x98\x03\x40\xb3',end,end+12)<0:continue
   matches.append((pos,end,a))
  c={'token_offset':token['offset'],'x':None,'y':None,'status':'unresolved-sparse-anchor'}
  if len(matches)!=1:curves.append(c);continue
  pos,end,a=matches[0];yi=struct.unpack_from('<H',a,4)[0];xi=struct.unpack_from('<H',a,35)[0]
  c.update(anchor_frame_offset=pos,anchor_frame_end=end,y_selector=yi,x_selector=xi,anchor_hex=a.hex())
  if not 1<=yi<=len(frames) or not 1<=xi<=len(frames):
   c['status']='out-of-range-selector';curves.append(c);continue
  y,x=frames[yi-1],frames[xi-1]
  if _dataset_signature(y['header'])!=_anchor_signature(a):
   c['status']='selector-y-metadata-disagrees';curves.append(c);continue
  c.update(x=x['name'],y=y['name'],status='xy-selector-resolved',
           row_alignment_verified=False,
           basis='explicit selectors in fully reconstructed 515-byte anchor plus repeated Y-header metadata')
  curves.append(c)
 result['dataset_manifest']=[{k:v for k,v in f.items() if k!='header'}|{'header_hex':f['header'].hex()} for f in frames]
 result['resolved_curves']=curves
 result['resolved_xy_count']=sum(c['status']=='xy-selector-resolved' for c in curves)
 result['warning']='Experimental binary-supported dataset links; row alignment, full axes, Origin render/save acceptance remain unverified'
 return result


# Exact inspected sources only: scanning 147-byte headers cannot establish a
# complete generic slot inventory when unknown matrix/text record kinds exist.
KNOWN_SOURCE_PROFILES = {'73d800c56814c8870e30bcebc20d931aa6f222480d7e42a7b3401def81fa323f': 'oleObject90-Contents.origin_payload', 'b6b673b7d930bb72a028f59c61fe3d6a04c89632489ff6cedb86445791304712': 'oleObject35-Contents.origin_payload', 'c586c88034ecfb2d9ad1157ff3b87b055414610ed8bd4a22959ba0f27ff998db': 'oleObject106-Contents.origin_payload', '71bc52236036014c740f42453a44aa495a39a123616a9e92e386071dc5ac42a3': 'oleObject52-Contents.origin_payload', '25c752c2c2ad373211040a4d70d4ee278cebbf868a0fbdd09c5a21a10282fd66': 'oleObject66-Contents.origin_payload'}

def read_modern_xy_bindings(blob:bytes)->dict:
 """Public research API: fail closed outside five fully inspected sources."""
 sha=hashlib.sha256(blob).hexdigest()
 if sha not in KNOWN_SOURCE_PROFILES:
  raise SparseFormatError("No inspected exact-source selector profile; unknown dataset slots cannot be ruled out")
 result=_read_modern_xy_bindings_unscoped(blob)
 result["source_profile"]=KNOWN_SOURCE_PROFILES[sha]
 result["scope"]="exact inspected original payload; not a generic dataset-list parser"
 return result
