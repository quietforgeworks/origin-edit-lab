"""Separately authored byte cursor reused from prior independent audit.
Tests the same restricted grammar, NOT an independent Origin format oracle.
Only addition: collect each fully decoded frame for scalar complement auditing.
Original provenance is recorded in the research report. No writer imports.
"""
import collections
def req(x,m):
 if not x:raise ValueError(m)
class Cursor:
 def __init__(self,b,p):self.b=b;self.p=p;self.frames=[]
 def take(self,n):
  req(0<=n<=len(self.b)-self.p,'bounds');x=self.b[self.p:self.p+n];self.p+=n;return x
 def exact(self,b):req(self.take(len(b))==b,'delimiter')
 def var(self):
  n=0
  for i in range(5):
   c=self.take(1)[0];n+=(c&127)*128**i
   if c<128:
    req(n<=0xffffffff and (i==0 or c!=0),'canonical integer');return n
  raise ValueError('too long integer')
 def sparse(self):
  start=self.p;self.exact(b'\x80');n=self.var();req(0<n<=8192,'sparse packed length');raw=self.take(n);out=bytearray();i=0
  while i<n:
   op=raw[i];i+=1
   if op<=127:
    req(i+op<=n,'literal length');out.extend(raw[i:i+op]);i+=op
   elif op<=191:out.extend(b'\0'*(op-125))
   elif op<=195:
    req(i<n,'repeat length');out.extend(raw[i:i+1]*(op-189));i+=1
   else:raise ValueError('sparse opcode')
   req(len(out)<=16384,'decoded budget')
  self.frames.append((start,self.p,bytes(out)));return bytes(out)
 def blob(self,longzero=False):
  start=self.p
  if self.b[self.p]==0:
   self.exact(b'\0\0\0\0\n' if longzero else b'\0');return b'',start,self.p
  if self.b[self.p]==129:
   self.p+=1;decoded=self.var();packed=self.var();req(0<decoded<=16*1024*1024 and 0<packed<=16*1024*1024,'encoded budgets');self.take(packed);return None,start,self.p
  n=self.var();req(0<n<=16*1024*1024,'raw budget');data=self.take(n);self.exact(b'\n');return data,start,self.p
ZERO=b'\0'*5+b'\n'
def verify_page(b,p):
 c=Cursor(b,p['header']['offset']);req(len(c.sparse()) in (195,199,205,245,253,261,269),'page header');req(c.p==p['header']['end'],'page header end')
 for o in p['post_header_opaque']:
  d,a,z=c.blob();req((a,z)==(o['offset'],o['end']),'page opaque bounds')
 counts=collections.Counter()
 for l in p['layers']:
  req(c.p==l['offset'],'layer start');raw=c.sparse();req(len(raw) in (341,361,385,393,405,409) and raw[:4] in (b'\0\0\x1f\0',b'\0\0\x17\0',b'\0\0\x5f\0'),'layer header')
  n=c.var();c.take(n);c.exact(b'\n\0');c.blob();req(c.p==l['annotation_list_start'],'annotation start')
  for a in l['annotations']:
   req(c.p==a['offset'],'annotation offset');head=c.sparse();req(len(head) in (111,133,138,154,159,161),'annotation header');req(head[70:111].split(b'\0')[0].decode('ascii')==a['name'],'annotation name');c.exact(b'\0');style=c.sparse();c.blob(True);c.blob();c.blob();c.exact(b'\0');req(c.p==a['end'],'annotation end');counts['annotations']+=1
  c.exact(ZERO);req(c.p==l['curve_list_start'],'curve start')
  for a in l['curves']:
   req(c.p==a['offset'],'curve offset');head=c.sparse();req(len(head) in (489,515,519) and head[:4]==b'\1\0\0\0','curve header');req(int.from_bytes(head[35:37],'little')==a['x_selector_u16'] and int.from_bytes(head[4:6],'little')==a['y_selector_u16'],'curve selectors');c.blob();body,_,_=c.blob();req(body is not None and body.startswith(bytes.fromhex('01588009980340b3')),'curve body');c.blob();req(c.p==a['end'],'curve end');counts['curves']+=1
  c.exact(ZERO);c.exact(ZERO)
  for idx,g in enumerate(l['axis_groups']):
   req(g['axis']=='XYZ'[idx] and c.p==g['offset'],'axis group start')
   req(len(g['records'])==6,'axis records count')
   for rec in g['records']:
    req(c.p==rec['frame']['offset'],'axis record start');raw=c.sparse();req(len(raw) in (489,515,519) and raw[:6]==b'\x11'+b'\0'*5,'axis header');req(int.from_bytes(raw[21:23],'little')==rec['stored_u16_at21'],'axis field');req(c.p==rec['frame']['end'],'axis end');counts['axis_records']+=1
   c.exact(ZERO);req(c.p==g['end'],'axis list end')
  c.blob();req(c.p==l['end'],'layer end');counts['layers']+=1
 c.exact(ZERO);req(c.p==p['end'],'page end');counts['pages']+=1
 return counts,c.frames
