from pathlib import Path
import argparse,base64,csv,hashlib,json,lzma,math,struct,sys,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description='Independent public-fixture/native and actual-LabPlot observation checks')
parser.add_argument('fixture',type=Path)
parser.add_argument('--evidence-root',type=Path,default=ROOT/'source-snapshot')
parser.add_argument('--output',type=Path,help='Optional new JSON output file, refuses overwrite')
args=parser.parse_args();SRC=args.evidence_root.resolve();FIXTURE=args.fixture.resolve()
sha=lambda b:hashlib.sha256(b).hexdigest()
def check(ok,why):
 if not ok:raise RuntimeError(why)
def records(b):
 out=[];p=17
 for i in range(478):
  n=int.from_bytes(b[p:p+4],'little');check(b[p+4]==10,'frame prefix');end=p+5+n+bool(n);check(not n or b[end-1]==10,'frame suffix');out.append((p,end,b[p+5:p+5+n]));p=end
 return out,p
original=FIXTURE.read_bytes();origrec,end=records(original)
check(sha(original)=='ea50c9b97b063898f654a6189b30ca5d8be8b52ad4c9469b3934cd009185265a','wrong public fixture')
reports=[]
for n in (51,257,1024):
 folder=SRC/f'candidates/generated{n}';raw=(folder/'raw.csv').read_bytes();rows=list(csv.reader(raw.decode().splitlines()));check(rows[0]==['A','B'] and len(rows)==n+1,'CSV shape');expected=[[struct.pack('>d',float(s)).hex() for s in r] for r in rows[1:]]
 b=(folder/'candidate.opj').read_bytes();recs,stop=records(b);check(len(b)==len(original)+20*(n-50),'file growth');check((folder/'rollback.opj').read_bytes()==original,'rollback exact')
 changes=[]
 for idx,(old,new) in enumerate(zip(origrec,recs)):
  if idx in (3,6):
   c=0 if idx==3 else 1;check(len(new[2])==n*10,'data length')
   for r in range(n):check(new[2][r*10:r*10+2]==b'\0\0' and new[2][r*10+2:r*10+10][::-1].hex()==expected[r][c],'cell bits')
  elif idx in (2,5):
   aa=bytearray(old[2]);bb=bytearray(new[2]);check(struct.unpack_from('<III',bb,25)==(n,0,n),'header rows')
   for off in (25,33):aa[off:off+4]=bb[off:off+4]=b'\0'*4
   check(aa==bb,'header complement')
  else:check(original[old[0]:old[1]]==b[new[0]:new[1]],'unapproved frame difference')
 check(original[end:]==b[stop:],'opaque tail')
 check(original[1412:]==b[1412+20*(n-50):],'entire suffix')
 reports.append({'case':n,'candidate_sha256':sha(b),'all_frames_complement_and_suffix_exact':True,'binary64_cells_verified':2*n,'rollback_exact':True})
# Independent actual application numeric and serialized-content readback, not author flags.
def verify_application(n):
 run=SRC/f'application/results/expanded{n}';baseline=SRC/'application/results/original';rows=list(csv.reader((SRC/f'candidates/raw{n}.csv').read_text().splitlines()))[1:];expected=[[struct.pack('>d',float(s)).hex() for s in r] for r in rows]
 obs=list(csv.DictReader((run/'Book1/native-app-values.tsv').open(),delimiter='\t'));check(len(obs)==2*n,'API observation count');cells={(int(r['row']),int(r['column'])):r['hex_binary64'] for r in obs};check(len(cells)==2*n,'unique API cells')
 for r,pair in enumerate(expected):
  for c,bits in enumerate(pair):check(cells[(r,c)]==bits,'API cell bits')
 curve=json.loads((run/'curve-observation.json').read_text());check(curve['x_bound'] and curve['y_bound'] and curve['signal_spy_valid'],'curve observation bound');check(curve['x_allocated_rows']==curve['y_allocated_rows']==n,'curve column rows');check(len(curve['rows'])==n,'curve source length')
 for r,c in enumerate(curve['rows']):check(c['row']==r and c['x_valid'] and c['y_valid'] and not c['x_masked'] and not c['y_masked'] and [c['x_bits'],c['y_bits']]==expected[r],'curve source bits')
 check(len(curve['point_signal_emissions'])>0,'passive signal emissions')
 for e in curve['point_signal_emissions']:check(e['logical_point_count']==n and e['start_index']==0 and e['end_index']==n-1 and e['logical_points_binary64']==expected,'actual curve logical points')
 def xml(folder):
  raw=(folder/'imported-application.lml').read_bytes();return ET.fromstring(lzma.decompress(raw) if raw.startswith(b'\xfd7zXZ\0') else raw)
 a=xml(baseline);b=xml(run)
 # Compare exact graph and all other serialized project content after specific documented volatile metadata.
 def normalize(e,root=False):
  attrs={k:v for k,v in e.attrib.items() if k not in ('uuid','creation_time') and not(root and k in ('dockWidgetState','modificationTime','thumbnail'))}
  return (e.tag,attrs,e.text,e.tail,[normalize(c) for c in e])
 ag=a.find(".//worksheet[@name='Graph2']");bg=b.find(".//worksheet[@name='Graph2']");check(ag is not None and bg is not None,'Graph2 exists');check(normalize(ag)==normalize(bg),'complete graph complement')
 bindings=bg.find('.//xyCurve/general').attrib;check(bindings['xColumn']=='test_tree_import/Folder1/Book1/A' and bindings['yColumn']=='test_tree_import/Folder1/Book1/B','curve bindings')
 for c,name in enumerate('AB'):
  path=".//folder[@name='Folder1']/child_aspect/spreadsheet[@name='Book1']/column[@name='"+name+"']";ac=a.find(path);bc=b.find(path);check(ac is not None and bc is not None and ac.attrib['rows']=='50' and bc.attrib['rows']==str(n),'saved allocation');payload=base64.b64decode(bc.find('output_filter').tail,validate=True);check(len(payload)==8*n,'saved binary64 length')
  for r in range(n):check(payload[r*8:r*8+8][::-1].hex()==expected[r][c],'saved binary64 exact')
  bc.attrib['rows']=ac.attrib['rows'];bc.find('output_filter').tail=ac.find('output_filter').tail
 check(normalize(a,True)==normalize(b,True),'other application project content')
 for d,source in ((baseline,original),(run,(SRC/f'candidates/generated{n}/candidate.opj').read_bytes())):
  check((d/'source-evidence.opj').read_bytes()==source,'application native snapshot');check((d/'input.before.sha256').read_bytes()==(d/'input.after.sha256').read_bytes(),'input untouched');check((d/'input.before.sha256').read_text().split()[0]==sha(source),'before hash matches source');check('OBSERVER_INPUT='+str(d/'source-evidence.opj') in (d/'application.log').read_text(),'actual import path');check((d/'exit-status.txt').read_text().strip()=='124','expected planned timeout')
 # Baseline signal/Column data tied to actual original source cells.
 basecurve=json.loads((baseline/'curve-observation.json').read_text());origpoints=[[origrec[3][2][r*10+2:r*10+10][::-1].hex(),origrec[6][2][r*10+2:r*10+10][::-1].hex()] for r in range(50)]
 check(len(basecurve['point_signal_emissions'])>0,'baseline passive emissions')
 for e in basecurve['point_signal_emissions']:check(e['logical_point_count']==50 and e['start_index']==0 and e['end_index']==49 and e['logical_points_binary64']==origpoints,'baseline curve exact')
 baseapi=list(csv.DictReader((baseline/'Book1/native-app-values.tsv').open(),delimiter='\t'));check(len(baseapi)==100,'baseline API count');basecells={(int(v['row']),int(v['column'])):v['hex_binary64'] for v in baseapi};check(len(basecells)==100,'baseline unique cells')
 for r in range(50):
  for c in range(2):check(basecells[(r,c)]==origpoints[r][c],'baseline API bit exact')
 return {'case':n,'api_cells_bit_exact':2*n,'passive_curve_emissions':len(curve['point_signal_emissions']),'all_points_bit_exact':n,'curve_range':[0,n-1],'saved_binary64_exact':True,'graph_and_project_complement_exact':True,'input_and_snapshot_verified':True,'baseline_50_curve_points_exact':True,'exit_code':124,'Origin_validation':'NOT_RUN'}
result={'native_candidate_checks':reports,'independent_application_reruns':[verify_application(n) for n in (51,257,1024)]}
if args.output:
 with args.output.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
