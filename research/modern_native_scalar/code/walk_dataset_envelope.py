"""Sequential read-only subset CPYUA dataset envelope walker.

No byte/name search, numeric value decoding, data fitting, or source writes.
Every object begins at the previous object's validated end. Unknown framing
stops, retaining its pending dataset slot. This is NOT a full Origin parser.
"""
from pathlib import Path
import sys,json,hashlib,struct,collections,re,os,stat
MAX_BYTES=64*1024*1024;MAX_ROWS=5_000_000;MAX_DATASETS=10000;MAX_HEADER=4096;MAX_TOTAL_ROWS=20_000_000;MAX_SEGMENTS=100_000;MAX_FILE_GROUPS=4096;MAX_FILE_SEGMENTS=8192
class Unsupported(ValueError):
 def __init__(self,reason,offset):super().__init__(reason);self.reason=reason;self.offset=offset
def need(ok,reason,p):
 if not ok:raise Unsupported(reason,p)
def exact(b,p,v,reason):need(b[p:p+len(v)]==v,reason,p);return p+len(v)
def sha(b):return hashlib.sha256(b).hexdigest()
def uleb(b,p):
 start=p;value=0
 for i in range(5):
  need(p<len(b),'ULEB truncated',p);x=b[p];p+=1;value|=(x&127)<<(7*i)
  if x<128:
   need((i==0 or x!=0) and value<=0xffffffff,'ULEB noncanonical/overflow',start);return value,p
 raise Unsupported('ULEB overlong',start)
def sparse(b,p):
 start=p;p=exact(b,p,b'\x80','expected sparse descriptor/header');n,q=uleb(b,p);end=q+n
 need(0<n<=MAX_HEADER and end<=len(b),'sparse frame bounds',start);out=bytearray()
 while q<end:
  x=b[q];q+=1
  if x<128:
   need(q+x<=end,'sparse literal overrun',q);out+=b[q:q+x];q+=x
  elif x<192:out+=bytes(x-125)
  elif x<196:
   need(q<end,'sparse repeat overrun',q);out+=b[q:q+1]*(x-189);q+=1
  else:raise Unsupported('unknown sparse opcode',q-1)
  need(len(out)<=MAX_HEADER,'sparse expansion cap',q)
 return bytes(out),end

def blob(b,p):
 start=p;need(p<len(b),'opaque blob missing',p)
 if b[p]==0:return {'start':p,'end':p+1,'kind':'empty','bytes':0}
 raw=None;encoded=None
 try:
  n,q=uleb(b,p);end=q+n
  if 0<n<=MAX_BYTES and end<len(b) and b[end]==10:
   raw={'start':start,'end':end+1,'kind':'raw-length-LF','bytes':n,'sha256':sha(b[q:end])}
 except Unsupported:pass
 if b[p]==0x81:
  try:
   decoded,q=uleb(b,p+1);packed,q=uleb(b,q);end=q+packed
   if 0<decoded<=MAX_BYTES and 0<packed<=MAX_BYTES and end<=len(b):
    encoded={'end':end,'decoded_bytes':decoded,'packed_bytes':packed}
  except Unsupported:pass
 need(not(raw is not None and encoded is not None),'ambiguous raw ULEB / encoded81 transport',p)
 if raw is not None:return raw
 if encoded is not None:raise Unsupported('unsupported encoded81 dataset-property transport',p)
 raise Unsupported('no uniquely bounded raw dataset-property blob',p)

def legacy(b,p):
 need(p+5<=len(b),'global header bounds',p);n=int.from_bytes(b[p:p+4],'little');exact(b,p+4,b'\n','global header length delimiter');q=p+5;end=q+n
 need(n<=MAX_HEADER and end<len(b),'global header size',p)
 if n:exact(b,end,b'\n','global header end delimiter');end+=1
 return {'start':p,'end':end,'bytes':n,'sha256':sha(b[q:q+n])}

def prolog(b):
 need(type(b)is bytes and 16<len(b)<=MAX_BYTES,'file bounds/type',0);nl=b.find(b'\n',0,100);need(nl>=0 and re.fullmatch(rb'CPYUA [0-9]+\.[0-9]+ [0-9]+',b[:nl]) is not None,'CPYUA signature',0)
 p=nl+1;meta=blob(b,p);p=meta['end'];p=exact(b,p,b'PrvwOPJU','preview pointer marker');need(p+8<=len(b),'preview pointer bounds',p);pointer=int.from_bytes(b[p:p+8],'little');p+=8
 global_header=legacy(b,p);p=global_header['end'];p=exact(b,p,b'\0\0\0\0\n','global end marker')
 return {'signature':b[:nl].decode('ascii'),'initial_metadata':meta,'preview_pointer':pointer,'global_header':global_header,'dataset_list_start':p},p

def fpc_extent(b,p,rows):
 start=p;remaining=rows
 while remaining:
  need(p<len(b),'FPC control truncated',p);ctl=b[p];p+=1
  for shift in (0,4):
   width=(ctl>>shift)&7;width+=width>=4;need(p+width<=len(b),'FPC residual truncated',p);p+=width;remaining-=1
   if not remaining:break
 return p

def consume_resource(budget,key,limit,p):
 need(budget[key]<limit,'resource budget exceeded: file '+key,p);budget[key]+=1

def row_group(b,p,remaining,envelope_type,resource_budget=None):
 if resource_budget is None:resource_budget={'groups':0,'segments':0}
 consume_resource(resource_budget,'groups',MAX_FILE_GROUPS,p)
 start=p;scalar=b[p:p+2]!=b'\xff\xff'
 if not scalar:
  p+=2;count,p=uleb(b,p)
 else:count=1
 need(0<count<=remaining,'row group count outside envelope',start);need(p<len(b),'row group type missing',p);kind=b[p];p+=1
 need(kind in (0,1),'unsupported row group type '+str(kind),p-1);segments=[];done=0
 while done<count:
  need(len(segments)<MAX_SEGMENTS,'segment count cap',p)
  consume_resource(resource_budget,'segments',MAX_FILE_SEGMENTS,p)
  lo=p;enc,p=uleb(b,p);n=(enc>>1)^-(enc&1)
  if scalar:
   need(enc==0,'unsupported scalar segment form',lo);n=1
  need(n!=0 and abs(n)<=count-done,'row segment extent invalid',lo);need(p<len(b),'row segment tag missing',p);tag=b[p]
  if kind==0:p+=1
  if kind==0:
   if n<0:
    need(tag==12,'unknown numeric stream codec',p-1);p=fpc_extent(b,p,-n);segkind='fpc-byte-extent'
   else:
    widths={0x50:8,0x1a:2,0x11:1,0x64:0,0x65:0,0x23:3,0x35:5,0x47:7};need(tag in widths,'unknown numeric repeat tag '+hex(tag),p-1);need(p+widths[tag]<=len(b),'repeat payload truncated',p);p+=widths[tag];segkind='numeric-repeat' if tag!=0x65 else 'opaque-zero-width-tag65; value semantics unassigned'
  else:
   for _ in range(1 if n>0 else -n):
    value,p=uleb(b,p)
    if envelope_type==5:
     need(value<=MAX_BYTES and p+value<=len(b),'typed1 string byte bounds',p);p+=value
   segkind=('typed1-index' if envelope_type==4 else 'typed1-length-bounded-bytes')+('-repeat' if n>0 else '-literal')
   # Preserve only extents and a hash of encoded references, not cell values.
  done+=abs(n);segments.append({'start':lo,'end':p,'rows':abs(n),'kind':segkind,'tag':tag})
 return {'start':start,'end':p,'rows':count,'type':kind,'scalar':scalar,'segments':segments,'value_semantics':'opaque; only encoded extents retained'},p

def dataset(b,p,index,row_budget=MAX_TOTAL_ROWS,resource_budget=None):
 if resource_budget is None:resource_budget={'groups':0,'segments':0}
 start=p;h,p=sparse(b,p);record={'descriptor_semantics':'unclassified 147-byte dataset descriptor; boundary support is not a semantic type claim','slot1':index,'start':start,'descriptor_end':p,'descriptor_bytes':len(h),'descriptor_sha256':sha(h),'record_state':'pending'}
 # Preserve slot even if descriptor kind or payload proves unsupported.
 if len(h)>=113:
  record.update(name=h[88:113].split(b'\0')[0].decode('latin1'),data_type_u16=int.from_bytes(h[22:24],'little'),row_fields=list(struct.unpack_from('<III',h,25)),field82=int.from_bytes(h[82:86],'little'))
 try:
  need(len(h)==147,'unsupported descriptor size/type',start)
  record['header_properties']=blob(b,p);p=record['header_properties']['end'];need(p<len(b),'row envelope missing',p);dtype=b[p];p+=1;record['envelope_type']=dtype
  count,p=uleb(b,p);record['stored_extent_rows']=count;need(count<=MAX_ROWS and count<=row_budget,'row count/budget cap',p);need(dtype in (4,5),'unsupported dataset envelope type '+str(dtype),p-1)
  rows=[];done=0;record['row_groups']=rows
  while done<count:
   need(len(rows)<MAX_SEGMENTS,'row group count cap',p)
   group,p=row_group(b,p,count-done,dtype,resource_budget);rows.append(group);done+=group['rows']
  record['row_groups']=rows
  if count:p=exact(b,p,b'\xce\xfa','numeric envelope terminator')
  record['dataset_properties']=blob(b,p);p=record['dataset_properties']['end'];p=exact(b,p,b'\0\0\0','dataset trailing slots unsupported/nonempty')
  record.update(end=p,record_state='envelope-complete; numeric semantics not asserted')
  return record,p
 except Unsupported as e:
  record.update(parsed_until=e.offset,blocker=e.reason,record_state='unsupported; slot retained');return record,None

def walk(b):
 resource_budget={'groups':0,'segments':0}
 out={'resource_budget_used':resource_budget,'resource_limits':{'groups':MAX_FILE_GROUPS,'segments':MAX_FILE_SEGMENTS},'source_bytes':len(b),'source_sha256':sha(b),'read_only':True,'datasets':[],'dataset_list_complete':False,'numeric_values_decoded':False,'origin_acceptance':False}
 try:
  out['prolog'],p=prolog(b);row_budget=MAX_TOTAL_ROWS
  while 1:
   # CPYUA list terminator is five zero bytes and LF; the following
   # empty slot precedes the first sparse window header.
   if b[p:p+6]==bytes(5)+b'\n':
    out['dataset_list_terminator']={'start':p,'end':p+6};p+=6;p=exact(b,p,b'\0','pre-window-list opaque empty slot');w,end=sparse(b,p);need(len(w) in (195,199,205,245,253,261,269) and w[:2]==bytes(2),'window header following dataset list',p)
    out.update(dataset_list_complete=True,dataset_list_end=p,first_window_header={'start':p,'end':end,'decoded_bytes':len(w),'decoded_sha256':sha(w)},parsed_until=end);break
   need(len(out['datasets'])<MAX_DATASETS,'dataset count cap',p)
   rec,q=dataset(b,p,len(out['datasets'])+1,row_budget,resource_budget);out['datasets'].append(rec)
   if q is None:out.update(parsed_until=rec['parsed_until'],blocker=rec['blocker']);break
   row_budget-=rec.get('stored_extent_rows',0);p=q
 except Unsupported as e:out.update(parsed_until=e.offset,blocker=e.reason)
 out['summary']={'slots_seen':len(out['datasets']),'complete_dataset_envelopes':sum('end'in d for d in out['datasets']),'dataset_list_complete':out['dataset_list_complete'],'stored_extent_rows':sum(d.get('stored_extent_rows',0) for d in out['datasets']),'blocker':out.get('blocker')}
 return out
def read_bounded_source(path):
 """Nonblocking, no-follow open; fstat must prove regular before any read.

 This CLI file route deliberately requires POSIX nonblocking/no-follow flags.
 Unsupported platforms fail closed rather than using a potentially blocking open.
 """
 if os.name!='posix' or not all(hasattr(os,k) for k in ('O_NONBLOCK','O_NOFOLLOW','O_CLOEXEC')):
  raise ValueError('Safe regular-file opening is unavailable on this platform')
 flags=os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW|os.O_CLOEXEC
 fd=os.open(os.fspath(path),flags)
 with os.fdopen(fd,'rb',closefd=True) as stream:
  before=os.fstat(stream.fileno())
  if not stat.S_ISREG(before.st_mode):raise ValueError('Source must be a regular file')
  if not 16<before.st_size<=MAX_BYTES:raise ValueError('Source exceeds supported file size or is too short')
  data=stream.read(MAX_BYTES+1)
  after=os.fstat(stream.fileno())
  if len(data)>MAX_BYTES:raise ValueError('Source grew beyond supported file size')
  if len(data)!=before.st_size or before.st_size!=after.st_size or before.st_mtime_ns!=after.st_mtime_ns:
   raise ValueError('Source changed during read')
 return data

def write_new_result(path,result,*,source=None):
 """Create a new result only. Never follow an output symlink or overwrite.

 Source aliases and existing output files/directories are rejected. Exclusive
 creation remains the final race-safe no-overwrite guard, including hardlinks.
 """
 path=Path(path)
 if source is not None and path.resolve(strict=False)==Path(source).resolve(strict=True):
  raise ValueError('Output resolves to the source; choose a new result file')
 absolute=path.absolute()
 for parent in [absolute.parent,*absolute.parent.parents]:
  if parent.is_symlink():raise ValueError('Symlinked output parent is not allowed')
 if os.path.lexists(path):raise FileExistsError('Output already exists; choose a new result file')
 if not path.parent.is_dir():raise ValueError('Output parent must be an existing directory')
 payload=json.dumps(result,indent=2)+'\n'
 # Mode x uses O_CREAT|O_EXCL, so existing symlinks, hardlinks, directories,
 # and destinations created after the checks cannot be overwritten.
 with path.open('x',encoding='utf-8') as out:out.write(payload)

def main(argv=None):
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args(argv)
 try:
  result=walk(read_bounded_source(args.source));write_new_result(args.out,result,source=args.source)
 except (OSError,ValueError) as error:
  ap.exit(2,str(error)+'\n')
 print(json.dumps(result['summary']))
if __name__=='__main__':main()
