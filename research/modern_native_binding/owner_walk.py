"""Bounded read-only CPYUA ownership walk; unknown transport stops a chain.

Record semantics are narrow: complete sparse graph/layer/annotation/curve
records and contiguous old-format-corresponding axis groups. Opaque property
payloads stay opaque. No values are inferred from previews or name proximity.
"""
from pathlib import Path
import hashlib,json,struct,sys,os,tempfile,re
import sparse_transport as s
MAX_BLOB=16*1024*1024
MAX_OBJECTS=4096
MAX_PAGE_ANCHORS=8192
MAX_OWNED_SPANS=65536
ZERO_LIST=bytes.fromhex('00000000000a')
class Unknown(ValueError):pass

def need(ok,msg,p):
 if not ok:raise Unknown(f'{msg} at {p}')
def take(b,p,expected,meaning):
 need(b[p:p+len(expected)]==expected,meaning,p);return p+len(expected)
def _compact_blob(b,p,*,long_zero=False):
 """Bound a transport payload without interpreting its opaque contents."""
 start=p;need(0<=p<len(b),'blob bounds',p)
 if b[p]==0:
  if long_zero:
   end=take(b,p,b'\0\0\0\0\n','long-empty blob')
  else:end=p+1
  return {'kind':'empty-long' if long_zero else 'empty-compact','offset':start,'end':end,'payload_bytes':0,'payload_sha256':s.sha(b'')}
 raw=None;encoded=None
 try:
  n,q=s.uleb(b,p);end=q+n
  if 0<n<=MAX_BLOB and end<len(b) and b[end]==10:
   raw={'kind':'raw-length-LF','offset':start,'payload_start':q,'payload_end':end,'end':end+1,'payload_bytes':n,'payload_sha256':s.sha(b[q:end])}
 except s.Reject:pass
 if b[p]==0x81:
  try:
   n,q=s.uleb(b,p+1);m,r=s.uleb(b,q);end=r+m
   if 0<n<=MAX_BLOB and 0<m<=MAX_BLOB and end<=len(b):
    encoded={'kind':'encoded81-opaque','offset':start,'payload_start':r,'end':end,'declared_decoded_bytes':n,'payload_bytes':m,'payload_sha256':s.sha(b[r:end]),'codec_semantics':'UNKNOWN; bounded transport only'}
  except s.Reject:pass
  need(not(raw and encoded),'ambiguous raw ULEB / encoded81 transport',p)
 if raw:return raw
 if encoded:return encoded
 raise Unknown(f'no uniquely bounded raw/encoded81 blob at {p}')

class OwnedRanges(list):
 def __init__(self,budget):super().__init__();self.budget=budget

def claim(owned,lo,hi,role):
 if owned is not None:
  need(0<=lo<hi,'invalid owned interval',lo)
  budget=getattr(owned,'budget',None)
  if budget is not None:
   need(budget['claims']<MAX_OWNED_SPANS,'global owned-span budget',lo);budget['claims']+=1
  owned.append({'start':lo,'end':hi,'role':role})
def record(b,p,owned=None):
 f=s.frame(b,p);claim(owned,p,f['end'],'sparse_record');return f
def compact_blob(b,p,*,long_zero=False,owned=None):
 obj=_compact_blob(b,p,long_zero=long_zero);claim(owned,obj['offset'],obj['end'],'bounded_'+obj['kind']);return obj

def annotation(b,p,owned=None):
 start=p;h=record(b,p,owned);need(len(h['raw']) in (111,133,138,154,159,161),'annotation header size',p)
 name=h['raw'][70:111].split(b'\0')[0]
 need(name and all(32<=x<127 for x in name),'annotation fixed-name field',p)
 p=take(b,h['end'],b'\0','annotation header separator');style=record(b,p,owned);p=style['end']
 data=compact_blob(b,p,long_zero=True,owned=owned);p=data['end']
 third=compact_blob(b,p,owned=owned);p=third['end']
 extra=compact_blob(b,p,owned=owned);p=extra['end']
 p=take(b,p,b'\0','annotation end separator')
 out={'kind':'annotation','offset':start,'end':p,'name':name.decode('ascii'),'header':s.meta(h),'style':s.meta(style),'data':data,'third_block':third,'opaque_properties':extra}
 if name in (b'XB',b'XT',b'YL',b'YR',b'ZF',b'ZB',b'Legend') and data['kind']=='raw-length-LF':
  text=b[data['payload_start']:data['payload_end']]
  if text.endswith(b'\0'):
   try:out['text']=text[:-1].decode('utf8')
   except UnicodeDecodeError:out['text']='UNKNOWN: non-UTF8'
  if len(style['raw'])>4:out['stored_font_u8']=style['raw'][4];out['font_literal_offset']=style['mapping'][4]
 return out

def curve(b,p,owned=None):
 start=p;h=record(b,p,owned);need(len(h['raw']) in (489,515,519),'curve header size',p)
 # Do not confuse worksheet property records or annotation styles with curves.
 need(h['raw'][:4]==b'\1\0\0\0','graph curve header type',p)
 header_prop=compact_blob(b,h['end'],owned=owned);p=header_prop['end'];body=compact_blob(b,p,owned=owned);p=body['end']
 need(body['kind']=='raw-length-LF' and b[body['payload_start']:body['payload_start']+8]==bytes.fromhex('01588009980340b3'),'DataPlot body identity',start)
 prop=compact_blob(b,p,owned=owned);p=prop['end']
 return {'kind':'curve','offset':start,'end':p,'header':s.meta(h),'header_opaque_properties':header_prop,'body':body,'opaque_properties':prop,'x_selector_u16':struct.unpack_from('<H',h['raw'],35)[0],'y_selector_u16':struct.unpack_from('<H',h['raw'],4)[0],'plot_type_u8':h['raw'][76],'stored_line_width_u16':struct.unpack_from('<H',h['raw'],21)[0],'selector_binding':'UNKNOWN pending complete typed dataset-list proof'}

def axes(b,p,owned=None):
 out=[]
 for letter in 'XYZ':
  records=[];start=p
  for role in ('minor_grid','major_grid','near_tick_labels','near_axis_line','far_tick_labels','far_axis_line'):
   h=record(b,p,owned);d=h['raw'];need(len(d) in (489,515,519) and d[:6]==bytes.fromhex('110000000000'),'axis parameter record',p)
   records.append({'role':role,'frame':s.meta(h),'stored_u16_at21':struct.unpack_from('<H',d,21)[0],'literal_map_at21':h['mapping'][21:23]});p=h['end']
  p=take(b,p,ZERO_LIST,'axis list terminator')
  out.append({'axis':letter,'offset':start,'end':p,'records':records,'semantic_basis':'Sequential X/Y/Z lists and six-role structure corroborated by fixed liborigin; no UI scaling assertion'})
 return out,p

def layer(b,p,owned=None):
 start=p;h=record(b,p,owned);d=h['raw'];need(len(d) in (341,361,385,393,405,409) and d[:4] in (bytes.fromhex('00001f00'),bytes.fromhex('00001700'),bytes.fromhex('00005f00')),'layer header',p)
 out={'kind':'layer','offset':start,'header':s.meta(h),'annotations':[],'curves':[],'axis_groups':[],'chain_complete':False}
 name_count,name_start=s.uleb(b,h['end']);name_end=name_start+name_count;need(name_count<=4096 and name_end<len(b) and b[name_end]==10,'layer post-header name frame',h['end']);claim(owned,h['end'],name_end+1,'layer_post_header_name_frame');out['layer_name_bytes_sha256']=s.sha(b[name_start:name_end]);out['layer_name_bytes']=name_count;out['layer_name_semantics']='length-bounded post-header text; not a global ID';p=take(b,name_end+1,b'\0','layer metadata separator');prop=compact_blob(b,p,owned=owned);out['opaque_properties']=prop;p=prop['end'];out['annotation_list_start']=p
 try:
  while b[p:p+6]!=ZERO_LIST:
   need(len(out['annotations'])<MAX_OBJECTS,'annotation count bound',p);a=annotation(b,p,owned);out['annotations'].append(a);p=a['end']
  p=take(b,p,ZERO_LIST,'annotation list terminator');out['curve_list_start']=p
  while b[p:p+6]!=ZERO_LIST:
   need(len(out['curves'])<MAX_OBJECTS,'curve count bound',p);c=curve(b,p,owned);out['curves'].append(c);p=c['end']
  p=take(b,p,ZERO_LIST,'curve list terminator')
  # Nonempty modern axis-break serialization is not silently skipped.
  p=take(b,p,ZERO_LIST,'empty axis-break list')
  out['axis_groups'],p=axes(b,p,owned)
  out['trailing_opaque_properties']=compact_blob(b,p,owned=owned);p=out['trailing_opaque_properties']['end']
  out.update(chain_complete=True,end=p,parsed_until=p)
 except (s.Reject,Unknown,IndexError) as e:
  out.update(parsed_until=p,blocker=str(e),end=None)
 return out

def page(b,header,budget=None):
 owned=OwnedRanges(budget if budget is not None else {'claims':0});claim(owned,header['offset'],header['end'],'window_header');out={'kind':'page','name':header['name'],'header':header,'layers':[],'chain_complete':False,'owned_intervals':owned};p=header['end']
 try:
  # Extra post-header records are bounded, not assigned guessed meanings.
  opaque=[]
  for _ in range(3):
   obj=compact_blob(b,p,owned=owned);opaque.append(obj);p=obj['end']
  out['post_header_opaque']=opaque
  while b[p:p+6]!=ZERO_LIST:
   need(len(out['layers'])<MAX_OBJECTS,'layer count bound',p)
   item=layer(b,p,owned);out['layers'].append(item)
   if not item['chain_complete']:out.update(parsed_until=item['parsed_until'],blocker=item['blocker']);return out
   p=item['end']
  p=take(b,p,ZERO_LIST,'page layer-list terminator');out.update(chain_complete=True,end=p,parsed_until=p)
 except (s.Reject,Unknown,IndexError) as e:out.update(parsed_until=p,blocker=str(e))
 return out

def discover_page_headers(b):
 found=[];attempts=0
 for match in re.finditer(rb'\x0a\x00?\x80',b):
  need(len(found)<MAX_OBJECTS,'page count budget before decoding another candidate',match.start())
  need(attempts<MAX_PAGE_ANCHORS,'page-anchor decode budget',match.start());attempts+=1
  at=match.end()-1
  try:f=s.frame(b,at)
  except s.Reject:continue
  d=f['raw']
  if len(d) not in (195,199,205,245,253,261,269):continue
  name=d[2:27].split(b'\0')[0]
  if not re.fullmatch(rb'[A-Za-z0-9][A-Za-z0-9_ -]{0,24}',name):continue
  found.append(s.meta(f)|{'separator_offset':match.start(),'name':name.decode('ascii'),'name_basis':'decoded fixed window name slot; candidate only until its scoped chain is walked','template_name_hex':d[69:89].hex(),'page_extent_u16_candidate':list(struct.unpack_from('<HH',d,35))})
 return found

def inventory(b):
 need(type(b)is bytes and 16<=len(b)<=MAX_BLOB,'file type/size bound',0)
 need(b.startswith(b'CPYUA '),'CPYUA signature',0)
 line_end=b.find(b'\n',0,101);need(line_end>=0,'bounded signature line',0)
 try:signature=b[:line_end].decode('ascii')
 except UnicodeDecodeError:raise Unknown('non-ASCII CPYUA signature')
 headers=discover_page_headers(b)
 pages=[];nested=[];budget={'claims':0}
 for h in headers:
  owners=[p for p in pages if any(a['start']<=h['offset']<a['end'] for a in p['owned_intervals']) or (p['chain_complete'] and p['header']['offset']<h['offset']<p['end'])]
  if owners:
   nested.append({'candidate':h,'within_page_offset':owners[-1]['header']['offset'],'status':'not a standalone page; starts inside an already bounded outer-owned interval, even if later outer parsing fails'})
  else:pages.append(page(b,h,budget))
 return {'source_sha256':s.sha(b),'source_bytes':len(b),'signature':signature,'read_only':True,'pages':pages,'nested_page_candidates':nested,
 'summary':{'pages':len(pages),'complete_page_chains':sum(p['chain_complete'] for p in pages),'layers_started':sum(len(p['layers']) for p in pages),'complete_layer_chains':sum(l['chain_complete'] for p in pages for l in p['layers']),'annotations_walked':sum(len(l['annotations']) for p in pages for l in p['layers']),'curves_walked':sum(len(l['curves']) for p in pages for l in p['layers']),'axis_records_walked':sum(sum(len(g['records']) for g in l['axis_groups']) for p in pages for l in p['layers'])},
 'limitations':['Window headers are candidate-discovered; later ownership links are sequentially walked, not nearest-preceding guessed','Opaque property payloads and encoded81 codec semantics remain undecoded','Full dataset list, global project tree, matrix/function plots and nonempty axis breaks are not accepted by this walker','No writes, redraws, fits, or Origin acceptance']}

def read_source(source):
 source=Path(source)
 need(source.is_file(),'source must be a regular file',0)
 size=source.stat().st_size
 need(16<=size<=MAX_BLOB,'source size preflight',0)
 with source.open('rb') as f:data=f.read(MAX_BLOB+1)
 need(len(data)==size and len(data)<=MAX_BLOB,'source changed size or exceeds bounded read',0)
 return data

def validate_output(source,output):
 source=Path(source);output=Path(output)
 need(source.is_file(),'source must be an existing file',0)
 need(source.resolve()!=output.resolve(strict=False),'output aliases source',0)
 need(not os.path.lexists(output),'output must be a new file, not a symlink or hardlink',0)
 need(output.parent.is_dir(),'output parent must exist',0)
 need(not any(x.is_symlink() for x in (output,*output.parents)),'output path must not traverse symlinks',0)
 return output

def atomic_new_output(source,output,data):
 output=validate_output(source,output)
 fd,stage=tempfile.mkstemp(prefix='.owner-inventory-',dir=output.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  # Hard-link creation is atomic and cannot replace an existing destination.
  os.link(stage,output,follow_symlinks=False)
 finally:
  os.unlink(stage)

if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
 validate_output(args.source,args.out);b=read_source(args.source);r=inventory(b)
 need(read_source(args.source)==b,'source changed during inventory',0)
 atomic_new_output(args.source,args.out,(json.dumps(r,indent=2,ensure_ascii=False)+'\n').encode())
 print(json.dumps(r['summary']))
