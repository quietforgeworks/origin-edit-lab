"""Strict bounded LZ4 block decoding experiment. No Origin semantic writes."""
MAX_BYTES=16*1024*1024
class DecodeRefused(ValueError):pass

def need(ok,msg):
 if not ok:raise DecodeRefused(msg)
def decode_block(raw:bytes,expected:int)->bytes:
 need(type(raw)is bytes and type(expected)is int,'Types must be bytes/int')
 need(0<len(raw)<=MAX_BYTES and 0<expected<=MAX_BYTES,'Bound exceeded')
 out=bytearray();p=0;last_match_start=None
 def extension(length):
  nonlocal p
  if length!=15:return length
  while True:
   need(p<len(raw),'Truncated extension');x=raw[p];p+=1;length+=x
   need(length<=expected,'Length exceeds output bound')
   if x!=255:return length
 while p<len(raw):
  token=raw[p];p+=1
  literals=extension(token>>4)
  need(p+literals<=len(raw) and len(out)+literals<=expected,'Literal bounds')
  out.extend(raw[p:p+literals]);p+=literals
  if p==len(raw):
   need(len(out)==expected,'Wrong final output size')
   if last_match_start is not None:
    need(literals>=5,'LZ4 terminal sequence requires five literals')
    need(last_match_start<=expected-12,'LZ4 last match starts too near block end')
   return bytes(out)
  need(p+2<=len(raw),'Truncated offset');offset=int.from_bytes(raw[p:p+2],'little');p+=2
  need(0<offset<=len(out),'Invalid match offset')
  match=extension(token&15)+4
  need(len(out)+match<=expected,'Match exceeds output bound')
  last_match_start=len(out)
  for _ in range(match):out.append(out[-offset])
 raise DecodeRefused('No terminal literal sequence')
