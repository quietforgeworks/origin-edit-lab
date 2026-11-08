"""Validate actual LabPlot column API, XYCurve signals and saved LML, not OPJ parsing.

Read-only comparison to externally anchored input and exact native bundle.
This establishes this importer run only, not Origin lifecycle compatibility.
"""
import argparse
import base64
import collections
import csv
import importlib.util
import io
import json
import lzma
import math
from pathlib import Path
import struct
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('custom',ROOT/'src/custom_data.py')
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
s=importlib.util.spec_from_file_location('observe',ROOT/'application/observe.py')
o=importlib.util.module_from_spec(s);s.loader.exec_module(o)

def diff(a,b,path='/project'):
 out=[]
 if a.tag!=b.tag:out.append({'path':path,'before_tag':a.tag,'after_tag':b.tag})
 for k in sorted(set(a.attrib)|set(b.attrib)):
  if k not in ('uuid','creation_time') and a.get(k)!=b.get(k):out.append({'path':path+'/@'+k,'before':a.get(k),'after':b.get(k)})
 for name in ('text','tail'):
  if getattr(a,name)!=getattr(b,name):out.append({'path':path+'/'+name+'()'})
 if len(a)!=len(b):out.append({'path':path,'before_children':len(a),'after_children':len(b)})
 count={}
 for x,y in zip(a,b):
  count[x.tag]=count.get(x.tag,0)+1
  tag=x.tag+(f'[@name={x.get("name")!r}]' if x.get('name') is not None else f'[{count[x.tag]}]')
  out+=diff(x,y,path+'/'+tag)
 return out

def load_lml(path):
 raw=c.read_file(path,10000000)
 if raw.startswith(b'\xfd7zXZ\x00'):
  decompressor=lzma.LZMADecompressor();raw=decompressor.decompress(raw,max_length=10000001)
  c.need(decompressor.eof and len(raw)<=10000000,'oversized or truncated LML')
 return E.fromstring(raw)

def verify(bundle,observation,expected_csv_sha256,expected_declaration_sha256,research_opt_in=False):
 c.opt_in(research_opt_in)
 files=c.read_bundle(bundle)
 source=c.verify_artifacts(files,expected_csv_sha256=expected_csv_sha256,expected_declaration_sha256=expected_declaration_sha256,research_opt_in=True)
 path=c.checked_path(observation)
 receipt=c.strict_json(c.read_file(path/'run-receipt.json',100000))
 c.need(receipt['native_bundle_before_after_identical'] is True,'source preservation receipt differs')
 c.need(receipt['native_bundle_artifacts_sha256']=={k:c.sha(v) for k,v in files.items()},'observation native input anchor differs')
 c.need(receipt['expected_csv_sha256']==expected_csv_sha256 and receipt['expected_declaration_sha256']==expected_declaration_sha256,'observation raw input anchors differ')
 c.need(receipt['origin_lifecycle']=='NOT_RUN','unsupported Origin claim in receipt')
 expected_receipt={'schema':'custom-labplot-observation-v1','native_bundle_before_after_identical':True,'native_bundle_artifacts_sha256':{k:c.sha(v) for k,v in files.items()},'runtime_sha256':o.RUNTIME_HASHES,'observer_sha256':o.OBSERVER_HASH,'expected_csv_sha256':expected_csv_sha256,'expected_declaration_sha256':expected_declaration_sha256,'origin_lifecycle':'NOT_RUN','application_results_validation':'PENDING independent validator'}
 c.need(c.json_bytes(receipt)==c.json_bytes(expected_receipt),'complete runtime/observer/source receipt differs')
 for name,key in [('original','rollback.opj'),('custom','candidate.opj')]:
  directory=path/name
  c.need(c.read_file(directory/'source-evidence.opj',231494)==files[key],'observed native source bytes differ')
  expected_hash=(c.sha(files[key])+'\n').encode()
  c.need(c.read_file(directory/'input.before.sha256',1000)==expected_hash,'source before hash differs')
  c.need(c.read_file(directory/'input.after.sha256',1000)==expected_hash,'source after hash differs')
  c.need(c.read_file(directory/'exit-status.txt',100)==b'124\n','unexpected actual-app exit')
 rows=list(csv.reader(io.StringIO(files['raw.csv'].decode('utf-8'),newline=''),strict=True))
 c.need(rows[0]==['A','B'] and len(rows)-1==source['active_rows'],'input shape differs')
 n=len(rows)-1
 expected=[[struct.pack('>d',float(v)).hex() for v in row] for row in rows[1:]]
 appvalues=list(csv.DictReader(io.StringIO(c.read_file(path/'custom/Book1/native-app-values.tsv',100000).decode(),newline=''),delimiter='\t'))
 c.need(len(appvalues)==100,'all 100 allocated API cells required')
 observed={(int(r['row']),int(r['column'])):r['hex_binary64'] for r in appvalues}
 c.need(set(observed)=={(r,col) for r in range(50) for col in range(2)},'missing/duplicate/extra API cells')
 for r in range(50):
  for col in range(2):
   actual=observed[r,col]
   if r<n:c.need(actual==expected[r][col],f'API binary64 differs at row {r}, column {col}')
   else:c.need(math.isnan(struct.unpack('>d',bytes.fromhex(actual))[0]),'inactive API cell not missing')
 curve=c.strict_json(c.read_file(path/'custom/curve-observation.json',200000))
 for k in ('curve_found','signal_spy_valid','x_bound','y_bound'):c.need(curve[k] is True,'real curve signal/binding missing')
 for k in ('x_allocated_rows','y_allocated_rows'):c.need(type(curve[k]) is int and curve[k]==50,'wrong curve allocation')
 c.need(len(curve['rows'])==50,'all curve rows required')
 for r,cell in enumerate(curve['rows']):
  c.need(type(cell['row']) is int and cell['row']==r,'wrong curve row identity')
  c.need(cell['x_masked'] is False and cell['y_masked'] is False,'curve cell masked')
  c.need(cell['x_valid'] is (r<n) and cell['y_valid'] is (r<n),'curve cell validity differs')
  c.need(cell['x_bits']==observed[r,0] and cell['y_bits']==observed[r,1],'curve source differs from API')
 emissions=curve['point_signal_emissions']
 c.need(type(emissions) is list and len(emissions)>0,'actual point-signal observation missing')
 for event in emissions:
  for key,value in [('logical_point_count',n),('start_index',0),('end_index',n-1)]:
   c.need(type(event[key]) is int and event[key]==value,'actual curve selection differs')
  c.need(event['logical_points_binary64']==expected,'actual curve logical points differ from raw source')
 base=load_lml(path/'original/imported-application.lml')
 actual=load_lml(path/'custom/imported-application.lml')
 for col,label in enumerate('AB'):
  column=actual.find(".//folder[@name='Folder1']/child_aspect/spreadsheet[@name='Book1']/column[@name='"+label+"']")
  c.need(column is not None and column.get('rows')=='50' and column.get('mode')=='0','missing saved double column')
  filters=column.findall('output_filter');c.need(len(filters)==1 and filters[0].tail is not None,'missing saved payload')
  payload=base64.b64decode(filters[0].tail,validate=True)
  c.need(len(payload)==400,'wrong saved payload length')
  for r in range(50):c.need(payload[r*8:r*8+8][::-1].hex()==observed[r,col],'saved bits differ from actual API')
 bg=base.find(".//worksheet[@name='Graph2']");ag=actual.find(".//worksheet[@name='Graph2']")
 c.need(bg is not None and ag is not None,'actual graph missing')
 c.need(not diff(bg,ag,'/Graph2'),'actual graph object/configuration changed')
 bindings=ag.find('.//xyCurve/general').attrib
 c.need(bindings['xColumn']=='test_tree_import/Folder1/Book1/A' and bindings['yColumn']=='test_tree_import/Folder1/Book1/B','actual graph bound to wrong source')
 excluded={}
 for key in ('dockWidgetState','modificationTime','thumbnail'):
  excluded[key]={'original':c.sha(base.get(key,'').encode()),'candidate':c.sha(actual.get(key,'').encode())}
  base.attrib.pop(key,None);actual.attrib.pop(key,None)
 differences=diff(base,actual)
 allowed={"/project/child_aspect[4]/folder[@name='Folder1']/child_aspect[2]/spreadsheet[@name='Book1']/column[@name='A']/output_filter[1]/tail()", "/project/child_aspect[4]/folder[@name='Folder1']/child_aspect[2]/spreadsheet[@name='Book1']/column[@name='B']/output_filter[1]/tail()"}
 c.need(len(differences)==2 and {d['path'] for d in differences}==allowed,'unrelated saved project data/configuration changed')
 return {'status':'PASS','application':'official LabPlot 2.12.1','active_rows':n,'allocated_rows':50,
  'raw_csv_sha256':expected_csv_sha256,'declaration_sha256':expected_declaration_sha256,
  'candidate_sha256':c.sha(files['candidate.opj']),
  'active_api_cells_bit_exact':2*n,'inactive_api_cells_missing':2*(50-n),
  'actual_curve_point_signal_emissions':len(emissions),'actual_curve_points_bit_exact':True,
  'saved_LML_column_bits_match_API':True,'graph_source_bindings':bindings,
  'graph_config_unchanged_except_uuid_creation_time':True,'only_saved_project_data_changes':differences,
  'excluded_UI_metadata_hashes':excluded,'native_source_unchanged':True,
  'source_integrity':source,'origin_lifecycle':'NOT_RUN',
  'visual_review':'NOT_RUN by this numerical verifier',
  'limits':'Importer observation only; no Origin open, edit, update, recalculate, native save or reopen test.'}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for f in ('bundle','observation','expected-csv-sha256','expected-declaration-sha256'):p.add_argument('--'+f,required=True)
 p.add_argument('--accept-labplot-only-research',action='store_true')
 a=vars(p.parse_args());a['research_opt_in']=a.pop('accept_labplot_only_research')
 print(json.dumps(verify(**a),indent=2,allow_nan=False))
