"""Experimental same-length CPYUA scalar source writer, not a general OPJU writer.

Supported classes and exact observed version/record profiles are explicit. Values
are raw stored integers, NOT Origin UI units. No numeric datasets or opaque blobs
are decoded or rewritten. Every output is a new file; caches stay stale.
"""
from pathlib import Path
import hashlib,json,re,sys,os,stat,secrets
import owner_walk as w
import sparse_transport as s
import native_binding as root
SCHEMA='cpyua-native-scalar-plan-v1'
PROFILES={
 'CPYUA 4.3268 195': {'parameter':515,'title_style':103},
 'CPYUA 4.3683 132': {'parameter':519,'title_style':111},
 'CPYUA 4.3811 222': {'parameter':519,'title_style':111},
}
FIELDS=('curve.line_width','annotation.font','axis.tick_font','axis.line_width')
DEPENDENCIES={'owner_walk.py':'b7ae97ff5ac699d1d9737404f292a51e10a02c2df00b6bed0135feeecc893404','sparse_transport.py':'7ac8ecc8025f8c8b700197c1cb4e5bb50a1d808cb9cd28bf2afdc912e06cd80a'}
DEPENDENCIES.update({'native_binding.py':'2f54d94c26a998069209e30e4f62f70ce69e1579c50dcc42bfa9beabc9264e07','walk_dataset_envelope.py':'fe3f6998cc5cf09c5f955c7e02ac5d7126a83d30d2d50380a90f2680bc5be575'})
class Rejected(ValueError):pass

def need(test,message):
 if not test:raise Rejected(message)
def digest(data):return hashlib.sha256(data).hexdigest()
def canonical(obj):return (json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode()
def anchor(data,expected,label):
 need(type(expected)is str and re.fullmatch('[0-9a-f]{64}',expected) is not None,label+' external SHA256 required')
 need(digest(data)==expected,label+' external anchor mismatch')
def dependencies():
 for name,h in DEPENDENCIES.items():anchor((Path(__file__).parent/name).read_bytes(),h,'dependency '+name)
def shape(data):
 need(type(data)is bytes,'bytes required');dependencies()
 try:inv=root.checked_root(data)
 except ValueError as e:raise Rejected('incomplete or unsupported sequential root: '+str(e)) from e
 inv['signature']=inv['dataset_envelope']['prolog']['signature']
 need(inv['signature'] in PROFILES,'unsupported exact CPYUA version profile')
 for p in inv['pages']:p['name']=p['name']['utf8']
 return inv,PROFILES[inv['signature']]
def select(data,selector):
 """Resolve an explicit owner path; never search for the requested field value."""
 need(type(selector)is dict,'selector object required')
 base={'page','layer','field'};field=selector.get('field');need(field in FIELDS,'unsupported field class')
 extras={'curve.line_width':{'curve','x_selector','y_selector','plot_type'},'annotation.font':{'annotation'},'axis.tick_font':{'axis','side'},'axis.line_width':{'axis','side'}}[field]
 need(set(selector)==base|extras,'exact selector keys required')
 inv,profile=shape(data)
 need(not(inv['signature']=='CPYUA 4.3683 132' and field=='curve.line_width'),'curve width profile lacks independent real type200 corpus coverage')
 need(type(selector['page'])is str and selector['page'],'page name required')
 pages=[p for p in inv['pages'] if p['name']==selector['page']]
 need(len(pages)==1,'missing or ambiguous page name, including incomplete candidates');p=pages[0]
 need(p['chain_complete'],'selected page ownership chain incomplete')
 for other in inv['pages']:
  if other is p:continue
  need(not(p['header']['offset']<=other['header']['offset']<p['end']),'overlapping page ownership')
 ln=selector['layer'];need(type(ln)is int and 1<=ln<=len(p['layers']),'layer ordinal outside complete page')
 l=p['layers'][ln-1];need(l['kind']=='graph' and l['chain_complete'],'selected layer is not a complete graph')
 need(all(x['kind']=='graph' for x in p['layers']),'mixed graph/worksheet page unsupported for writing')
 owner={'root_page_ordinal1':p['page_ordinal1'],'dataset_list_end':inv['dataset_envelope']['dataset_list_end'],'page_list_end':inv['parsed_until'],'dataset_section_sha256':digest(data[:inv['dataset_envelope']['dataset_list_end']]),'unknown_project_tail_sha256':digest(data[inv['parsed_until']:]),'page':p['name'],'page_header_sha256':p['header']['sha256'],'page_offset':p['header']['offset'],'page_end':p['end'],'layer':ln,'layer_header_sha256':l['header']['sha256'],'layer_offset':l['offset'],'layer_end':l['end']}
 if field=='curve.line_width':
  cn=selector['curve'];need(type(cn)is int and 1<=cn<=len(l['curves']),'curve ordinal outside layer');c=l['curves'][cn-1]
  for key,actual in [('x_selector',c['x_selector_u16']),('y_selector',c['y_selector_u16']),('plot_type',c['plot_type_u8'])]:need(type(selector[key])is int and selector[key]==actual,'curve '+key+' does not match owned record')
  need(c['plot_type_u8']==200,'only native line plot type200 supported for curve width')
  need(c['x_selector_u16']>0 and c['y_selector_u16']>0,'zero selectors are not accepted line-curve identities')
  need(all(c[k]['status']=='resolved sequential descriptor slot' for k in ('x_reference','y_reference')),'curve selector outside complete dataset list')
  f=s.frame(data,c['header']['offset']);need(len(f['raw'])==profile['parameter'],'unsupported curve header/version profile');dp,n=21,2
  owner.update(curve=cn,x_selector=c['x_selector_u16'],y_selector=c['y_selector_u16'],plot_type=200,curve_end=c['end'])
 elif field=='annotation.font':
  name=selector['annotation'];need(name in ('XB','XT','YL','YR','ZF','ZB'),'only named axis-title annotations supported')
  names=[a for a in l['annotations'] if a['name']==name];need(len(names)==1,'missing or ambiguous named axis title');a=names[0]
  need(a['data']['kind']=='raw-length-LF' and 'text'in a and not a['text'].startswith('UNKNOWN:'),'opaque or unknown title body unsupported')
  f=s.frame(data,a['style']['offset']);need(len(f['raw'])==profile['title_style'],'unsupported title style/version profile');dp,n=4,1
  owner.update(annotation=name,annotation_header_sha256=a['header']['sha256'],annotation_offset=a['offset'],annotation_end=a['end'],text_payload_sha256=a['data']['payload_sha256'])
 else:
  axis,side=selector['axis'],selector['side'];need(axis in ('X','Y','Z') and side in ('near','far'),'axis and side must be explicit')
  gs=[g for g in l['axis_groups'] if g['axis']==axis];need(len(gs)==1,'unique owned axis group required');g=gs[0]
  role=side+('_tick_labels' if field=='axis.tick_font' else '_axis_line');rs=[r for r in g['records'] if r['role']==role];need(len(rs)==1,'unique axis member required');r=rs[0]
  f=s.frame(data,r['frame']['offset']);need(len(f['raw'])==profile['parameter'],'unsupported axis header/version profile');dp,n=21,2
  owner.update(axis=axis,side=side,role=role,axis_group_offset=g['offset'],axis_group_end=g['end'])
 need(f['offset']>=l['offset'] and f['end']<=l['end'],'target record not wholly inside layer')
 return inv,p,l,f,owner,dp,n

def prepare(data,selector,new_value,*,expected_source_sha256,units='stored_integer'):
 anchor(data,expected_source_sha256,'source');need(units=='stored_integer','unknown UI units; only stored_integer is accepted')
 inv,p,l,f,owner,dp,n=select(data,selector)
 need(type(new_value)is int and 0<new_value<256**n,'new value must be a nonzero in-range exact integer')
 old=f['raw'][dp:dp+n];new=new_value.to_bytes(n,'little');need(old!=new,'no-op change refused')
 need(all((a==0)==(b==0) for a,b in zip(old,new)),'zero-mask pattern change unsupported')
 edits=[]
 for i,(a,b,pos) in enumerate(zip(old,new,f['mapping'][dp:dp+n])):
  if a==b:continue
  need(type(pos)is int,'changed byte lacks one-to-one literal provenance; repeat/implicit-zero edits unsupported')
  need(data[pos]==a,'encoded literal preimage mismatch');edits.append({'offset':pos,'before':a,'after':b})
 need(edits and len({e['offset'] for e in edits})==len(edits),'ambiguous literal mapping')
 return {'schema':SCHEMA,'source_sha256':digest(data),'source_bytes':len(data),'signature':inv['signature'],'selector':selector,'units':'stored_integer','owner':owner,'record_offset':f['offset'],'record_end':f['end'],'record_decoded_bytes':len(f['raw']),'record_sha256':f['sha256'],'record_encoded_sha256':f['encoded_sha256'],'decoded_offset':dp,'field_bytes':n,'before_value':int.from_bytes(old,'little'),'after_value':new_value,'literal_edits':edits,'limits':{'ui_scale_verified':False,'Origin_acceptance':'NOT_RUN','complete_project_parser':False,'root_page_discovery':'strict sequential prolog + complete dataset list + complete page list; no scan','dataset_binding':'selectors preserved, not resolved by this writer','data_preservation':'all non-target bytes preserved; not proof all rows are understood','cache_policy':'unchanged; visible PPT remains stale until Origin refresh, unverified'}}

def apply(data,plan,*,expected_source_sha256,expected_plan_sha256):
 anchor(canonical(plan),expected_plan_sha256,'plan');anchor(data,expected_source_sha256,'source')
 need(type(plan)is dict and plan.get('schema')==SCHEMA,'unknown plan schema')
 check=prepare(data,plan.get('selector'),plan.get('after_value'),expected_source_sha256=expected_source_sha256,units=plan.get('units'))
 need(canonical(plan)==canonical(check),'plan differs from freshly derived owned source plan')
 result=bytearray(data)
 for e in plan['literal_edits']:result[e['offset']]=e['after']
 result=bytes(result)
 _,_,_,a,_,dp,n=select(data,plan['selector']);_,_,_,b,owner,_,_=select(result,plan['selector'])
 need(owner==plan['owner'],'owner context changed')
 need(a['mapping']==b['mapping'] and a['ops']==b['ops'],'sparse control or encoded length changed')
 need(a['raw'][:dp]+a['raw'][dp+n:]==b['raw'][:dp]+b['raw'][dp+n:],'decoded record complement changed')
 need(int.from_bytes(b['raw'][dp:dp+n],'little')==plan['after_value'],'stored value reread mismatch')
 changed=[i for i,(x,y) in enumerate(zip(data,result)) if x!=y];need(changed==sorted(e['offset'] for e in plan['literal_edits']),'native full complement changed')
 manifest={'schema':'cpyua-native-scalar-delta-v1','plan':plan,'plan_sha256':expected_plan_sha256,'source_sha256':digest(data),'result_sha256':digest(result),'source_bytes':len(data),'result_bytes':len(result),'changed_offsets':changed,'native_complement_preserved':True,'controls_preserved':True,'cache_policy':plan['limits']['cache_policy']}
 return result,manifest

def restore(result,manifest,*,expected_source_sha256,expected_result_sha256,expected_manifest_sha256):
 anchor(canonical(manifest),expected_manifest_sha256,'manifest');anchor(result,expected_result_sha256,'result')
 need(type(manifest)is dict and manifest.get('schema')=='cpyua-native-scalar-delta-v1','unknown restoration schema')
 need(manifest['source_sha256']==expected_source_sha256 and manifest['result_sha256']==expected_result_sha256,'manifest source/result external anchors')
 restored=bytearray(result)
 for e in manifest['plan']['literal_edits']:
  need(type(e['offset'])is int and 0<=e['offset']<len(result) and result[e['offset']]==e['after'],'restore literal bounds/preimage');restored[e['offset']]=e['before']
 restored=bytes(restored);anchor(restored,expected_source_sha256,'restored source')
 again,m=apply(restored,manifest['plan'],expected_source_sha256=expected_source_sha256,expected_plan_sha256=manifest['plan_sha256'])
 need(again==result and canonical(m)==canonical(manifest),'restoration manifest does not reproduce exact edit')
 return restored

def parent_fd(path):
 """Open every directory component without following links; hold the final dirfd."""
 path=Path(os.path.abspath(os.fspath(path)))
 need(os.name=='posix' and all(hasattr(os,k) for k in ('O_NOFOLLOW','O_NONBLOCK','O_DIRECTORY','O_CLOEXEC')),'safe POSIX file operations unavailable')
 fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC)
 try:
  for component in path.parts[1:-1]:
   other=os.open(component,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd)
   os.close(fd);fd=other
  return fd,path.name
 except BaseException:os.close(fd);raise

def bounded_regular(path,limit):
 path=Path(path)
 need(not any(x.is_symlink() for x in (path,*path.parents)),'input symlink traversal refused')
 directory,name=parent_fd(path)
 try:fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=directory)
 finally:os.close(directory)
 try:
  before=os.fstat(fd);need(stat.S_ISREG(before.st_mode),'input must be a regular file')
  need(0<before.st_size<=limit,'input exceeds bounded size')
  chunks=[];remaining=limit+1
  while remaining:
   part=os.read(fd,min(remaining,65536))
   if not part:break
   chunks.append(part);remaining-=len(part)
  data=b''.join(chunks);after=os.fstat(fd)
  need(len(data)==before.st_size and len(data)<=limit,'input size changed or exceeded limit')
  need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'input changed during read')
  return data
 finally:os.close(fd)

def new_output(source,output,data):
 """No-follow directory chain and atomic exclusive link; never replace a name."""
 w.validate_output(source,output)
 directory,name=parent_fd(output);temporary='.native-stage-'+secrets.token_hex(16);created=False
 try:
  fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=directory);created=True
  with os.fdopen(fd,'wb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
  os.link(temporary,name,src_dir_fd=directory,dst_dir_fd=directory,follow_symlinks=False)
 finally:
  if created:os.unlink(temporary,dir_fd=directory)
  os.close(directory)

def strict_json(data,*,max_bytes=65536):
 need(type(data)is bytes and 0<len(data)<=max_bytes,'bounded JSON required')
 def pairs(items):
  result={}
  for k,v in items:
   need(k not in result,'duplicate JSON key');result[k]=v
  return result
 def invalid(value):raise Rejected('non-finite JSON number refused')
 try:return json.loads(data.decode('utf8'),object_pairs_hook=pairs,parse_constant=invalid,parse_float=invalid)
 except (ValueError,UnicodeError,RecursionError) as e:raise Rejected('invalid strict JSON: '+str(e)) from e


def main():
 import argparse
 ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='operation',required=True)
 for op in ('plan','apply','restore'):
  p=sub.add_parser(op);p.add_argument('source',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--source-sha256',required=True)
  if op=='plan':p.add_argument('--selector',required=True);p.add_argument('--value',type=int,required=True)
  elif op=='apply':p.add_argument('--plan',type=Path,required=True);p.add_argument('--plan-sha256',required=True)
  else:p.add_argument('--manifest',type=Path,required=True);p.add_argument('--manifest-sha256',required=True);p.add_argument('--result-sha256',required=True)
 args=ap.parse_args();w.validate_output(args.source,args.out);data=bounded_regular(args.source,w.MAX_BLOB)
 if args.operation=='plan':out=canonical(prepare(data,strict_json(args.selector.encode()),args.value,expected_source_sha256=args.source_sha256))
 elif args.operation=='apply':
  plan=strict_json(bounded_regular(args.plan,65536));out,manifest=apply(data,plan,expected_source_sha256=args.source_sha256,expected_plan_sha256=args.plan_sha256)
  # Machine-readable restoration information is returned on stdout, never used as an external trust anchor.
  print(canonical(manifest).decode(),end='')
 else:out=restore(data,strict_json(bounded_regular(args.manifest,65536)),expected_source_sha256=args.source_sha256,expected_result_sha256=args.result_sha256,expected_manifest_sha256=args.manifest_sha256)
 need(bounded_regular(args.source,w.MAX_BLOB)==data,'source changed during operation');new_output(args.source,args.out,out)
if __name__=='__main__':main()
