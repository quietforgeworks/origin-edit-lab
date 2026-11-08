"""Conservative CPYA 4.3268 embedded-graph dataset/curve adapter (stdlib).

Independent binary observations from CC-BY-4.0 Zenodo 20155927 PPTX.
NO order-based mapping, nearest-value matching, or guessed X bindings.
Y: repeated format/state/count metadata must match exactly ONE dataset header.
X: explicit anchor selector is reported, but its identity table is not decoded;
a sole same-sheet designated-X is only a candidate, never a resolved binding.
This reader does not modify files and is NOT a lossless Origin implementation.
"""
from __future__ import annotations
import hashlib
import re
import struct

HEADER = b'CPYA 4.3268 195 W64 #\n'
DATAPLOT = b'\x58\0\0\0\x98\x03\x40\xb3'
NAME = re.compile(rb'[A-Za-z][A-Za-z0-9 ]*_[A-Za-z0-9]+(?:@[0-9]+)?\Z')
# (dataset-header offset, curve-anchor offset, width).
MIRRORED_FIELDS = ((33,11,4),(20,15,2),(6,21,14),(22,37,2))

class UnsupportedEmbeddedOrigin(ValueError): pass

def blocks(blob: bytes) -> tuple[list[dict],int]:
 if not blob.startswith(HEADER):raise UnsupportedEmbeddedOrigin('Unvalidated CPYA version/header')
 out=[];pos=len(HEADER)
 while pos+5<=len(blob):
  size=struct.unpack_from('<I',blob,pos)[0]
  if blob[pos+4]!=10:break
  start=pos+5
  if size==0:pos=start;continue
  end=start+size
  if end>=len(blob) or blob[end]!=10:break
  out.append({'offset':pos,'payload_offset':start,'size':size,'payload':blob[start:end]});pos=end+1
 return out,pos

def _identity(name: str) -> str:
 book,col=name.rsplit('_',1)
 return book+('@'+col.split('@',1)[1] if '@' in col else '')

def _dataset_signature(payload: bytes) -> bytes:
 return b''.join(payload[d:d+w] for d,c,w in MIRRORED_FIELDS)

def _anchor_signature(payload: bytes) -> bytes:
 return b''.join(payload[c:c+w] for d,c,w in MIRRORED_FIELDS)

def read_embedded_curve_bindings(blob: bytes) -> dict:
 bs,end=blocks(blob);datasets=[];curve_records=[];graph=None;layer=0
 for i,b in enumerate(bs):
  p=b['payload'];s=b['size']
  if s==147:
   raw=p[88:111].split(b'\0',1)[0]
   if NAME.fullmatch(raw) and i+1<len(bs):
    data=bs[i+1];allocated=struct.unpack_from('<I',p,25)[0]
    if data['size']!=allocated*10:continue
    name=raw.decode('ascii');datasets.append({'name':name,'sheet':_identity(name),
     'header_offset':b['payload_offset'],'data_offset':data['payload_offset'],
     'stored_rows':allocated,'count_field':struct.unpack_from('<I',p,33)[0],
     'designation_bytes':p[22:24].hex(),'signature':_dataset_signature(p).hex()})
  if s>=150 and p[:2]==b'\0\0' and i+1<len(bs) and bs[i+1]['payload'][:4]==b'\0\0\x1f\0':
   raw=p[2:34].split(b'\0',1)[0]
   if re.fullmatch(rb'[A-Za-z][A-Za-z0-9 _-]*',raw):graph=raw.decode('ascii');layer=0
  if s>=90 and p[:4]==b'\0\0\x1f\0':layer+=1
  if s!=515 or p[:4]!=b'\1\0\0\0' or i+1>=len(bs) or bs[i+1]['payload'][:8]!=DATAPLOT:continue
  curve_records.append({'graph':graph,'layer':layer,'anchor_offset':b['payload_offset'],
                        'y_selector':struct.unpack_from('<H',p,4)[0],
                        'x_selector':struct.unpack_from('<H',p,35)[0],
                        'signature':_anchor_signature(p).hex()})
 # Refuse duplicate dataset names and nonunique metadata matches.
 names=[d['name'] for d in datasets]
 for curve in curve_records:
  candidates=[d for d in datasets if d['signature']==curve['signature']]
  curve.update(y=None,x=None,x_candidate=None,status='unresolved-y',y_candidates=[d['name'] for d in candidates])
  if len(candidates)!=1 or curve['y_selector']==0:continue
  y=candidates[0]
  if names.count(y['name'])!=1:continue
  curve.update(y=y['name'],y_header_offset=y['header_offset'],status='y-metadata-match-x-unresolved')
  xs=[d for d in datasets if d['sheet']==y['sheet'] and d['designation_bytes']=='2151']
  if len(xs)==1 and curve['x_selector']!=0:
   curve['x_candidate']=xs[0]['name']
   curve['x_candidate_basis']='unique same-sheet X-designated dataset; selector identity unverified'
 # Same nonzero ID pointing to incompatible unique Y matches invalidates both.
 conflicting={c['y_selector'] for c in curve_records if len({k['y'] for k in curve_records if k['y_selector']==c['y_selector'] and k['y'] is not None})>1}
 for c in curve_records:
  if c['y_selector'] in conflicting:c.update(y=None,x=None,x_candidate=None,status='conflicting-y-selector')
 return {'source_sha256':hashlib.sha256(blob).hexdigest(),'format':'CPYA 4.3268 embedded graph',
         'datasets':datasets,'curves':curve_records,'walk_end':end,'trailing_bytes':len(blob)-end,
         'mirrored_fields':[{'header_offset':d,'anchor_offset':c,'width':w} for d,c,w in MIRRORED_FIELDS],
         'resolved_xy_count':0,'y_metadata_matches':sum(c['y'] is not None for c in curve_records),
         'warning':'Y matches use independently repeated metadata, not decoded identity table. X selectors unresolved. No Origin oracle.'}
