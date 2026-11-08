"""Independent LabPlot result comparison, never parses Origin project bytes."""
from pathlib import Path
import collections,csv,copy,hashlib,json,lzma,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parent/'application/results'
sha=lambda b:hashlib.sha256(b).hexdigest()
def load(case):
 raw=(ROOT/case/'imported-application.lml').read_bytes()
 if raw.startswith(b'\xfd7zXZ\x00'):raw=lzma.decompress(raw)
 (ROOT/case/'imported-application.xml').write_bytes(raw)
 return E.fromstring(raw)
def diff(a,b,path=''):
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
def numeric(case):
 out={}
 for p in (ROOT/case).glob('Book*/native-app-values.tsv'):
  rows=list(csv.DictReader(p.open(),delimiter='\t'))
  out[p.parent.name]={'native_double_bits':{str((r['row'],r['column'])):r['hex_binary64'] for r in rows},'cells':len(rows)}
 return out
def graph_fields(root):
 g={}
 for w in root.iter('worksheet'):
  g[w.get('name')]={'axes':{a.get('name'):{'labels':a.find('labels').attrib,'line':a.find('line').attrib,'title':a.find('textLabel/text').text} for a in w.iter('axis')},'plot_geometry':[x.find('geometry').attrib for x in w.iter('cartesianPlot')], 'curve_lines':[{y.tag:y.attrib for y in x if y.tag in ('line','lines')} for x in w.iter('xyCurve')], 'bindings':[x.find('general').attrib for x in w.iter('xyCurve')]}
 return g
def compare(base,case):
 b,a=load(base),load(case);before=graph_fields(b);after=graph_fields(a)
 rawdiff=diff(b,a,'/project');ignored=['dockWidgetState','modificationTime','thumbnail'];meta={k:{'before_sha256':sha(b.get(k,'').encode()),'after_sha256':sha(a.get(k,'').encode())} for k in ignored}
 for r in (a,b):
  for k in ignored:r.attrib.pop(k,None)
 differences=diff(b,a,'/project')
 nb,na=numeric(base),numeric(case)
 result={'baseline':base,'case':case,'method':'Unmodified official LabPlot 2.12.1 importer, app-owned LML serialization, public Column::valueAt double access, fresh GUI captures. Helpers never parse Origin files.','ignore_attributes':['uuid','creation_time'],'ignored_project_ui_metadata':meta,'complete_project_differences_excluding_ui_metadata':differences,'all_numeric_bits_equal':nb==na,'native_numeric_cells':sum(x['cells'] for x in na.values()),'before_graph_fields':before,'after_graph_fields':after,'Origin_acceptance':'NOT RUN'}
 (ROOT/case/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
 return result
if __name__=='__main__':
 summaries=[]
 for key in ('two_graphs','single_axes'):
  for f in ('xb_tick_font','xb_axis_width','curve_line_width','layer_rect'):
   r=compare(key+'-baseline',key+'-'+f);s={k:r[k] for k in ('baseline','case','all_numeric_bits_equal','native_numeric_cells','complete_project_differences_excluding_ui_metadata')};summaries.append(s)
 (ROOT.parent.parent/'application-summary.json').write_text(json.dumps(summaries,indent=2)+'\n')
 print(json.dumps(summaries,indent=2))
