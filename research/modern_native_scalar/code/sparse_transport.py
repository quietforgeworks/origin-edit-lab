"""Generic bounded sparse transport subset; no user fixtures or file paths.

Unknown repeat opcodes remain rejected rather than guessed.
"""
import hashlib
MAX_PACKED=8192;MAX_DECODED=16384
sha=lambda b:hashlib.sha256(b).hexdigest()
class Reject(ValueError):pass
def require(ok,msg):
 if not ok:raise Reject(msg)
def uleb(b,p,limit=None):
 end=len(b) if limit is None else limit;v=0
 for i in range(5):
  require(0<=p<end<=len(b),'varint bounds');c=b[p];p+=1;v|=(c&127)<<(7*i)
  if c<128:
   require(i==0 or c!=0,'noncanonical varint');require(v<=0xffffffff,'varint overflow');return v,p
 raise Reject('overlong varint')
def sparse(b,start,end):
 require(0<=start<=end<=len(b),'sparse bounds');p=start;out=bytearray();mapping=[];ops=[]
 while p<end:
  off=p;c=b[p];p+=1;dp=len(out)
  if c<128:
   require(p+c<=end,'literal overrun');out.extend(b[p:p+c]);mapping.extend(range(p,p+c));p+=c;kind='literal' if c else 'zero-length-noop';n=c
  elif c<192:n=c-125;out.extend(bytes(n));mapping.extend([None]*n);kind='implicit-zero'
  elif c<196:
   require(p<end,'repeat overrun');n=c-189;out.extend(bytes([b[p]])*n);mapping.extend([None]*n);p+=1;kind='repeat'
  else:raise Reject('unknown opcode')
  require(len(out)<=MAX_DECODED,'decoded bound');ops.append({'offset':off,'source_end':p,'decoded_offset':dp,'count':n,'kind':kind})
 return bytes(out),mapping,ops
def frame(b,p):
 require(0<=p<len(b) and b[p]==128,'not sparse-prefix80');n,start=uleb(b,p+1)
 require(0<n<=MAX_PACKED,'packed bound');end=start+n;raw,mapping,ops=sparse(b,start,end)
 return {'offset':p,'start':start,'end':end,'packed_count':n,'decoded_bytes':len(raw),'raw':raw,'mapping':mapping,'ops':ops,'sha256':sha(raw),'encoded_sha256':sha(b[p:end]),'trailing_zero_byte':end<len(b) and b[end]==0}
def meta(f,include_raw=False):
 out={k:v for k,v in f.items() if k not in ('raw','mapping','ops')}
 if include_raw:out['decoded_hex']=f['raw'].hex();out['literal_offset_map']=f['mapping'];out['operations']=f['ops']
 return out
