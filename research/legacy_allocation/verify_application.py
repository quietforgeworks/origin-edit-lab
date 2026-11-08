"""Verify actual LabPlot output without parsing any Origin source bytes.

This compares app-owned saves, passive XYCurve point-signal observations and
Column::valueAt bits against raw synthetic CSV read independently in Python.
A separate source-artifact audit regenerates the resized edit from its pinned
original; none of the numerical readback checks use an OPJ parser.
"""
from pathlib import Path
import base64,collections,csv,hashlib,io,json,lzma,math,struct,xml.etree.ElementTree as E
from verify_source_artifacts import verify_case_source,verify_original_source
ROOT=Path(__file__).resolve().parent
APP=ROOT/'application/results'
def need(condition,message):
 if not condition:raise RuntimeError(message)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(name):
 raw=(APP/name/'imported-application.lml').read_bytes()
 if raw.startswith(b'\xfd7zXZ\x00'):raw=lzma.decompress(raw)
 return E.fromstring(raw)
def diff(a,b,path='/project'):
 out=[]
 if a.tag!=b.tag:out.append({'path':path,'before_tag':a.tag,'after_tag':b.tag})
 for k in sorted(set(a.attrib)|set(b.attrib)):
  if k not in ('uuid','creation_time') and a.get(k)!=b.get(k):out.append({'path':path+'/@'+k,'before':a.get(k),'after':b.get(k)})
 for name in ('text','tail'):
  aa=getattr(a,name);bb=getattr(b,name)
  if aa!=bb:out.append({'path':path+'/'+name+'()','before':aa,'after':bb})
 if len(a)!=len(b):out.append({'path':path,'before_children':len(a),'after_children':len(b)})
 count={}
 for x,y in zip(a,b):
  count[x.tag]=count.get(x.tag,0)+1
  tag=x.tag+(f'[@name={x.get("name")!r}]' if x.get('name') is not None else f'[{count[x.tag]}]')
  out+=diff(x,y,path+'/'+tag)
 return out

def verify(n):
 original_source_audit=verify_original_source(ROOT)
 source_audit=verify_case_source(ROOT,n,app=True)
 name=f'expanded{n}';base=load('original');actual=load(name)
 raw=list(csv.reader(io.StringIO((ROOT/'candidates'/f'raw{n}.csv').read_text(encoding='utf-8'),newline='')));need(raw[0]==['A','B'] and len(raw)==n+1,'unexpected CSV shape')
 expected=[[struct.pack('>d',float(v)).hex() for v in row] for row in raw[1:]]
 appvalues=list(csv.DictReader(io.StringIO((APP/name/'Book1/native-app-values.tsv').read_text(encoding='utf-8'),newline=''),delimiter='\t'))
 need(len(appvalues)==2*n,'require all allocated app cells observed')
 observed={(int(r['row']),int(r['column'])):r['hex_binary64'] for r in appvalues}
 need(len(observed)==2*n,'duplicate cell observations')
 for r in range(n):
  for c in range(2):
   bits=observed[(r,c)]
   need(bits==expected[r][c],f'{name}: raw value bits differ at {r},{c}')
 curve=json.loads((APP/name/'curve-observation.json').read_text())
 need(curve['curve_found'] and curve['signal_spy_valid'] and curve['x_bound'] and curve['y_bound'],'missing real curve observation/binding')
 need(curve['x_allocated_rows']==curve['y_allocated_rows']==n,'allocated row count differs')
 need(len(curve['rows'])==n,'missing curve-linked source rows')
 for r,cell in enumerate(curve['rows']):
  need(cell['row']==r and not cell['x_masked'] and not cell['y_masked'],'curve row identity/masks differ')
  need(cell['x_valid'] is True and cell['y_valid'] is True,'wrong curve-linked source validity')
  need(cell['x_bits']==observed[(r,0)] and cell['y_bits']==observed[(r,1)],'curve reads different source bits')
 emissions=curve['point_signal_emissions'];need(len(emissions)>0,'no actual curve-render point signal observed')
 for emission in emissions:
  need(emission['logical_point_count']==n and emission['start_index']==0 and emission['end_index']==n-1,'incorrect actual curve-selected point count/range')
  need(emission['logical_points_binary64']==expected,'actual curve logical-point bits differ from raw CSV')
 # Confirm saved values too; recognizing the expected payload paths alone is insufficient.
 for c,label in enumerate('AB'):
  column=actual.find(".//folder[@name='Folder1']/child_aspect/spreadsheet[@name='Book1']/column[@name='"+label+"']")
  need(column is not None and column.get('rows')==str(n) and column.get('mode')=='0','missing saved double column')
  filters=column.findall('output_filter');need(len(filters)==1 and filters[0].tail is not None,'missing saved column payload')
  payload=base64.b64decode(filters[0].tail,validate=True)
  need(len(payload)==8*n,'saved column payload must contain exactly n binary64 values')
  for r in range(n):
   need(payload[r*8:r*8+8][::-1].hex()==observed[(r,c)],'saved column bits differ from actual Column API')
 bg=base.find(".//worksheet[@name='Graph2']");ag=actual.find(".//worksheet[@name='Graph2']")
 need(bg is not None and ag is not None,'missing native graph object')
 graphdiff=diff(bg,ag,'/Graph2');need(not graphdiff,'graph configuration/source binding changed')
 bindings=ag.find('.//xyCurve/general').attrib
 need(bindings['xColumn']=='test_tree_import/Folder1/Book1/A' and bindings['yColumn']=='test_tree_import/Folder1/Book1/B','wrong graph data sources')
 metadata={}
 for k in ('dockWidgetState','modificationTime','thumbnail'):
  metadata[k]={'original_sha256':sha(base.get(k,'').encode()),'candidate_sha256':sha(actual.get(k,'').encode())}
  base.attrib.pop(k,None);actual.attrib.pop(k,None)
 differences=diff(base,actual)
 allowed={"/project/child_aspect[4]/folder[@name='Folder1']/child_aspect[2]/spreadsheet[@name='Book1']/column[@name='A']/output_filter[1]/tail()", "/project/child_aspect[4]/folder[@name='Folder1']/child_aspect[2]/spreadsheet[@name='Book1']/column[@name='B']/output_filter[1]/tail()"}
 # Confirm the exact paths after comparison rather than accepting any data node.
 allowed |= {p.rsplit('/output_filter[1]/tail()',1)[0]+'/@rows' for p in list(allowed)}
 need({d['path'] for d in differences}==allowed and len(differences)==4,'unexpected complete-project difference fields/count')
 for d in differences:
  need("/folder[@name='Folder1']/" in d['path'] and "/spreadsheet[@name='Book1']/column[@name=" in d['path'] and (d['path'].endswith('/output_filter[1]/tail()') or (d['path'].endswith('/@rows') and d['before']=='50' and d['after']==str(n))),'unrelated serialized data/configuration changed')
 need(set(d['path'].split("/column[@name=")[1].split(']')[0] for d in differences)=={"'A'","'B'"},'both and only A/B payloads must differ')
 # Initial import and final Save As must not alter the native source file.
 need((APP/name/'exit-status.txt').read_text().strip()=='124','unexpected actual-app exit status')
 need((APP/name/'input.before.sha256').read_bytes()==(APP/name/'input.after.sha256').read_bytes(),'source file changed by application')
 report={'case':name,'active_rows':n,'allocated_rows':n,'actual_app_bit_exact_active_values':n*2,
   'actual_app_missing_inactive_values':0,'actual_curve_signal_emissions':len(emissions),
   'all_curve_logical_points_bit_exact_to_csv':True,'curve_selected_range':[0,n-1],
   'graph_object_unchanged_excluding_uuid_creation_time':True,'graph_source_bindings':bindings,
   'all_other_app_project_content_unchanged':True,'native_safe_export_supported':False,'project_differences':differences,
   'excluded_ui_metadata_hashes':metadata,'object_counts':dict(collections.Counter(e.tag for e in actual.iter() if e.tag in ('spreadsheet','workbook','matrix','note','folder','worksheet','xyCurve'))),
   'app_source_preserved':True,'source_artifact_audit':source_audit,
   'original_source_artifact_audit':original_source_audit,
   'saved_column_binary64_matches_actual_API':True,
   'visual_review':'NOT PERFORMED by this verifier; see separately recorded visual inspection',
   'Origin_acceptance_reopen_update_recalculate_save':'NOT_RUN'}
 return report
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--evidence-root',type=Path,default=ROOT,help='Read-only root containing candidates/ and application/results/')
 parser.add_argument('--output-dir',type=Path,help='Optional new report directory; refuses an existing path')
 args=parser.parse_args();ROOT=args.evidence_root.resolve();APP=ROOT/'application/results'
 results=[verify(n) for n in (51,257,1024)]
 if args.output_dir is not None:
  args.output_dir.mkdir(parents=False,exist_ok=False)
  (args.output_dir/'verified-results.json').write_text(json.dumps(results,indent=2,allow_nan=False)+'\n')
 print(json.dumps([{k:r[k] for k in ('case','active_rows','allocated_rows','actual_app_bit_exact_active_values','actual_app_missing_inactive_values','actual_curve_signal_emissions','all_curve_logical_points_bit_exact_to_csv','all_other_app_project_content_unchanged','saved_column_binary64_matches_actual_API','source_artifact_audit','visual_review')} for r in results],indent=2,allow_nan=False))
