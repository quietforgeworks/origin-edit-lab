"""Read-only CPYUA 4.3268 embedded-graph FPC record adapter.

Adapter authored from byte inspection of the second CC-BY scientific PPTX.
Depends on approved Apache-2.0 quantized revision
431deeb7c8473503970ca56b78cc1678f57d373d and numpy; retain its LICENSE/NOTICE
when bundling upstream code. Uses its FPC decoder, name grammar, graph-page
scanner and curve-token grammar, but does not modify upstream modules.

Difference: these embedded records use 00 05, not upstream's 0a 05 prefix.
This recovers numeric payloads, NOT graphs or established X/Y curve bindings.
"""
from __future__ import annotations
import hashlib
import re
from quantized.io.origin_project import opju_codec as codec
from quantized.io.origin_project.opju_figure_curves import opju_pages, column_id_table, _CURVE_TOKEN

HEADER=b'CPYUA 4.3268 195\n'
# Bounded unsigned LEB128, followed optionally by a verified but undecoded
# leading-gap field seen in object66. No arbitrary intervening bytes accepted.
RECORD=re.compile(rb'\x00\x05(?:[\x80-\xff]{0,4}[\x00-\x7f])(?P<gap>\x01\x00\x00)?\xff\xff')

def read_modern_embedded_numeric(blob: bytes) -> dict:
 if not blob.startswith(HEADER):raise ValueError('Unsupported embedded CPYUA version')
 names=[(m.start(),m.end(),m.group().decode('latin1')) for m in codec._NAME.finditer(blob)
        if m.start()>0 and blob[m.start()-1]==len(m.group())]
 columns=[];rejected=[];cursor=0
 for idx,(name_start,name_end,name) in enumerate(names):
  if name_start<cursor:continue
  bound=names[idx+1][0] if idx+1<len(names) else len(blob)
  matches=list(RECORD.finditer(blob,name_end,min(name_end+48,bound)))
  if not matches:continue
  if len(matches)!=1:rejected.append({'name':name,'reason':'ambiguous record headers'});continue
  m=matches[0];ff=m.end()-2
  got=codec._decode_record(blob,ff)
  if got is None or not codec._plausible(got[0]):
   rejected.append({'name':name,'reason':'FPC record failed structural/plausibility check'});continue
  values,end=got;cursor=end
  columns.append({'name':name,'name_offset':name_start,'record_offset':m.start(),
                  'ff_offset':ff,'end_offset':end,'prefix_hex':blob[m.start():ff].hex(),
                  'undecoded_gap_flags':(m.group('gap') or b'').hex(),
                  'stored_values':values.tolist(),'stored_count':len(values),
                  'worksheet_alignment_verified':False})
 pages=opju_pages(blob);ids=column_id_table(blob,pages);tokens=[]
 for m in _CURVE_TOKEN.finditer(blob):
  kind=m.group(1)[0];width=1 if kind==1 else 2
  if kind not in (1,3) or m.end()+width>len(blob):continue
  tokens.append({'offset':m.start(),'token_kind':kind,'selector':int.from_bytes(blob[m.end():m.end()+width],'little')})
 return {'source_sha256':hashlib.sha256(blob).hexdigest(),'source_kind':'extracted Origin OLE Contents',
         'format':'CPYUA 4.3268 195','columns':columns,'rejected':rejected,
         'pages':[{'offset':p,'name':n} for p,n in pages],'curve_tokens':tokens,
         'upstream_column_id_count':len(ids.ids),'resolved_curves':[],
         'warning':'Numeric records recovered; no independent numeric oracle, row alignment or curve-to-dataset identity verified'}
