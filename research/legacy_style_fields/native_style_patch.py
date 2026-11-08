"""Bounded, exact-source legacy OPJ experiments; never edits previews or data.

Profiles describe genuine public KDE fixtures. Writes touch only independently
source-mapped semantic records. Unknown bytes and numerical bit patterns remain
byte identical. No Origin rendering/validation is claimed by this module.
"""
from pathlib import Path
import hashlib,json,struct
ROOT=Path(__file__).resolve().parent
import os
BASE=Path(os.environ.get('ORIGIN_RESEARCH_FIXTURE_ROOT',ROOT/'fixtures'))
PROFILES={
 'two_graphs':dict(path=BASE/'2graphs.opj',sha='bd25404bf20d008918c6fa6ad2bd610bedd28dca43ce0e52ee9c0b9a490e58ef',size=87541,tail=53075,frames=220,window=(2106,195),layer=(2307,385),curve=(9599,519),axis_starts=(11191,14346,17501),axis_size=519,titles={'XB':(5260,138,5404,103,5513,6),'YL':(4990,138,5134,103,5243,6)},source_name='2graphs.opj'),
 'single_axes':dict(path=BASE/'single_layer_two_axes.opj',sha='907538ce3633a51cdde39c4f3dc729b569bfaffedd33274b1367e1f791e9e961',size=77973,tail=63572,frames=134,window=(16479,245),layer=(16730,341),curve=(54021,489),axis_starts=(54637,57612,60587),axis_size=489,titles={'XB':(51511,111,51628,62,51696,15),'YL':(51300,111,51417,62,51485,15)},source_name='single_layer_two_axes.opj'),
}
def sha(b):return hashlib.sha256(b).hexdigest()
class Rejected(ValueError):pass
def need(ok,msg):
 if not ok:raise Rejected(msg)
def frame(b,p,n):
 need(type(p)is int and type(n)is int and p>=0 and n>=0,'bad record')
 need(p+5+n+bool(n)<=len(b),'truncated record')
 need(b[p:p+4]==struct.pack('<I',n) and b[p+4]==10,'record framing changed')
 need(not n or b[p+5+n]==10,'record closing delimiter')
 return b[p+5:p+5+n]
def snapshot(b,key):
 p=PROFILES[key];need(type(b)is bytes and len(b)==p['size'],'file size/type')
 pos=b.index(b'\n')+1;fs=[]
 while pos<p['tail']:
  n=struct.unpack_from('<I',b,pos)[0];d=frame(b,pos,n);fs.append((pos,n,d));pos+=5+n+bool(n)
 need(pos==p['tail'] and len(fs)==p['frames'],'full framed stream differs')
 wd=frame(b,*p['window']);ly=frame(b,*p['layer']);cv=frame(b,*p['curve'])
 need(wd[2:27].split(b'\0')[0]==b'Graph1','graph identity')
 # Axis parameters occur in three six-record groups, each followed by zero.
 axes={};recsize=p['axis_size']
 for axis,start in zip('XYZ',p['axis_starts']):
  records=[frame(b,start+i*(recsize+6),recsize) for i in range(6)]
  frame(b,start+6*(recsize+6),0)
  axes[axis]={'minor_grid_width':struct.unpack_from('<H',records[0],21)[0],'major_grid_width':struct.unpack_from('<H',records[1],21)[0],
   'near_tick_font_u16':struct.unpack_from('<H',records[2],21)[0],'near_tick_bold_bit':bool(records[2][26]&8),
   'near_axis_width_u16':struct.unpack_from('<H',records[3],21)[0],
   'far_tick_font_u16':struct.unpack_from('<H',records[4],21)[0],'far_axis_width_u16':struct.unpack_from('<H',records[5],21)[0]}
 titles={}
 for name,(hp,hn,sp,sn,tp,tn) in p['titles'].items():
  h=frame(b,hp,hn);s=frame(b,sp,sn);t=frame(b,tp,tn)
  need(h[70:111].split(b'\0')[0]==name.encode(),'title identity')
  titles[name]={'stored_font_u8':s[4],'text_bytes_hex':t.hex(),'rotation_tenths':struct.unpack_from('<h',s,2)[0]}
 data=[];caches=[]
 for i,(at,n,d) in enumerate(fs):
  # Pinned fixtures' dataset descriptors, not a general heuristic serializer.
  if n in (140,147) and d[22:24] in (b'!Q',b'!a'):
   name=d[88:113].split(b'\0')[0].decode('ascii');dp,dn,raw=fs[i+1]
   alloc,begin,end=struct.unpack_from('<III',d,25);stride=d[61]
   need(stride==10 and dn==alloc*stride and begin<=end<=alloc,'dataset allocation')
   data.append({'name':name,'header_record':at,'header_sha256':sha(d),'data_record':dp,'data_sha256':sha(raw),'allocated':alloc,'begin':begin,'end':end,
    'cells':[{'mask_hex':raw[j:j+2].hex(),'binary64_le_hex':raw[j+2:j+10].hex()} for j in range(0,dn,10)]})
  if n>=111 and d[70:111].split(b'\0')[0]==b'TemplateEMF':
   style=fs[i+1];img=fs[i+2]
   caches.append({'name':'TemplateEMF','annotation_record':at,'payload_record':img[0],'payload_bytes':img[1],'sha256':sha(img[2]),'first_40_bytes_hex':img[2][:40].hex()})
 need(len(data)==(4 if key=='two_graphs' else 2),'dataset inventory count')
 return {'sha256':sha(b),'frames':[[a,n] for a,n,d in fs],'page_pixels':list(struct.unpack_from('<HH',wd,35)),'layer_client_rect_i16':list(struct.unpack_from('<hhhh',ly,113)),
 'curve_binding':{'x_index':struct.unpack_from('<H',cv,35)[0],'y_index':struct.unpack_from('<H',cv,4)[0],'type':cv[76]},'curve_line_width_stored':struct.unpack_from('<H',cv,21)[0],
 'axes':axes,'titles':titles,'datasets':data,'known_cached_payloads':caches,'opaque_tail_sha256':sha(b[p['tail']:]),'opaque_tail_bytes':len(b)-p['tail']}
def field_spec(key,field,value):
 p=PROFILES[key];a=p['axis_starts'][0];step=p['axis_size']+6
 if field in ('xb_tick_font','xb_axis_width','curve_line_width'):
  limit=255 if field=='xb_tick_font' else 65535
  need(type(value)is int and 1<=value<=limit,'integer outside tested field limits')
  off=(a+2*step+26 if field=='xb_tick_font' else a+3*step+26 if field=='xb_axis_width' else p['curve'][0]+26)
  return off,struct.pack('<H',value),{'encoding':'uint16_le','native_semantics':{'xb_tick_font':'Graph1.layer1.xAxis.tickAxis[0].fontSize','xb_axis_width':'Graph1.layer1.xAxis.formatAxis[0].thickness (stored/500)','curve_line_width':'Graph1.layer1.curve1.lineWidth (stored/500)'}[field]}
 if field=='layer_rect':
  need(type(value)is list and len(value)==4 and all(type(v)is int and 0<=v<=32767 for v in value),'rect requires four exact nonnegative int16')
  need(value[0]<value[2] and value[1]<value[3],'rect dimensions must be positive')
  return p['layer'][0]+5+113,struct.pack('<hhhh',*value),{'encoding':'four_int16_le','native_semantics':'Graph1.layer1.clientRect [left,top,right,bottom]; native page coordinate units; UI inch/cm mapping is not independently proven'}
 raise Rejected('unsupported field')
def patch(b,key,field,value):
 need(type(key)is str and key in PROFILES,'unsupported profile');p=PROFILES[key]
 need(type(b)is bytes and sha(b)==p['sha'],'exact original required; no repatching')
 before=snapshot(b,key);off,new,meaning=field_spec(key,field,value);old=b[off:off+len(new)]
 need(old!=new,'no-op')
 if field=='layer_rect':
  w,h=before['page_pixels'];need(value[2]<=w and value[3]<=h,'rect outside known page')
 out=b[:off]+new+b[off+len(new):];after=snapshot(out,key)
 need(before['datasets']==after['datasets'],'data bytes changed')
 need(before['curve_binding']==after['curve_binding'],'binding changed')
 need(before['known_cached_payloads']==after['known_cached_payloads'],'cache changed')
 need(before['opaque_tail_sha256']==after['opaque_tail_sha256'],'unknown tail changed')
 need(before['frames']==after['frames'],'record boundaries changed')
 need(b[:off]==out[:off] and b[off+len(new):]==out[off+len(new):],'bytes outside source field changed')
 m={'profile':key,'field':field,'requested_value':value,**meaning,'source_sha256':sha(b),'candidate_sha256':sha(out),'source_size':len(b),'candidate_size':len(out),'write':{'offset':off,'before_hex':old.hex(),'after_hex':new.hex()},
 'changed_offsets':[i for i,(x,y) in enumerate(zip(b,out)) if x!=y], 'allowed_range_half_open':[off,off+len(new)],'unchanged_complement_sha256':sha(b[:off]+b[off+len(new):]),
 'all_other_bytes_unchanged':True,'all_dataset_masks_and_binary64_bits_unchanged':True,'known_cache_payloads':before['known_cached_payloads'],'unknown_records_preserved':True,'Origin_reopen':'NOT RUN','Origin_save':'NOT RUN','native_algorithm_execution':'NOT RUN',
 'unknowns':['Origin version-specific page/layer scaling locks','font family mapping','opaque metadata and project-tail contents','modern OPJU serialization','complete object semantics'],
 'public_source':'https://github.com/KDE/labplot/blob/0bd2e4094e92e74052ec161022d4e60aeb7605cd/tests/import_export/Project/data/'+p['source_name']}
 need(restore(out,m)==b,'round trip')
 return out,m,before,after
def restore(candidate,m):
 need(type(m)is dict and m.get('profile') in PROFILES,'restore profile')
 key=m['profile'];p=PROFILES[key];off,new,meaning=field_spec(key,m.get('field'),m.get('requested_value'))
 need(m.get('source_sha256')==p['sha'] and m.get('source_size')==p['size'],'restore source')
 need(type(candidate)is bytes and len(candidate)==p['size']==m.get('candidate_size') and sha(candidate)==m.get('candidate_sha256'),'restore candidate')
 need(m.get('allowed_range_half_open')==[off,off+len(new)],'restore range')
 write=m.get('write',{});need(write.get('offset')==off and write.get('after_hex')==new.hex(),'restore write')
 try:old=bytes.fromhex(write['before_hex'])
 except (KeyError,TypeError,ValueError):raise Rejected('restore preimage')
 need(len(old)==len(new) and candidate[off:off+len(new)]==new,'restore length/value')
 out=candidate[:off]+old+candidate[off+len(new):]
 need(sha(out)==p['sha'],'exact restored hash')
 return out

def publish_directory(out, files):
 """Same-filesystem staging and Linux atomic no-replace publication."""
 import ctypes,errno,tempfile,shutil
 out=Path(out)
 need(out.parent.is_dir(), 'output parent must exist')
 need(not out.exists() and not out.is_symlink(),'output already exists')
 stage=Path(tempfile.mkdtemp(prefix='.native-style-',dir=out.parent))
 try:
  for name,raw in files.items():
   need(Path(name).name==name,'invalid artifact name')
   with (stage/name).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
   need((stage/name).read_bytes()==raw,'write verification failed')
  libc=ctypes.CDLL(None,use_errno=True)
  need(hasattr(libc,'renameat2'),'atomic no-replace directory publication unavailable')
  call=libc.renameat2;call.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint];call.restype=ctypes.c_int
  if call(-100,os.fsencode(stage),-100,os.fsencode(out),1):
   code=ctypes.get_errno();raise Rejected('atomic publication failed: '+os.strerror(code))
 finally:
  if stage.exists():shutil.rmtree(stage)

def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 commands=parser.add_subparsers(dest='command',required=True)
 patch_cmd=commands.add_parser('patch');patch_cmd.add_argument('--profile',choices=PROFILES,required=True);patch_cmd.add_argument('--input',type=Path,required=True);patch_cmd.add_argument('--field',choices=['xb_tick_font','xb_axis_width','curve_line_width','layer_rect'],required=True);patch_cmd.add_argument('--value',required=True,help='JSON exact integer or [left,top,right,bottom]');patch_cmd.add_argument('--out',type=Path,required=True)
 inspect=commands.add_parser('inspect');inspect.add_argument('--profile',choices=PROFILES,required=True);inspect.add_argument('--input',type=Path,required=True)
 rollback=commands.add_parser('restore');rollback.add_argument('--candidate',type=Path,required=True);rollback.add_argument('--manifest',type=Path,required=True);rollback.add_argument('--out',type=Path,required=True)
 args=parser.parse_args()
 if args.command=='patch':
  value=json.loads(args.value);c,m,b,a=patch(args.input.read_bytes(),args.profile,args.field,value)
  files={'candidate.opj':c,'restored.opj':restore(c,m)}
  for name,obj in [('manifest',m),('before',b),('after',a)]:files[name+'.json']=(json.dumps(obj,indent=2)+'\n').encode()
  publish_directory(args.out,files);print(json.dumps(m,indent=2))
 elif args.command=='inspect':print(json.dumps(snapshot(args.input.read_bytes(),args.profile),indent=2))
 else:
  c=args.candidate.read_bytes();m=json.loads(args.manifest.read_text());b=restore(c,m)
  publish_directory(args.out,{'restored.opj':b});print(json.dumps({'restored_sha256':sha(b),'bytes':len(b)}))
if __name__=='__main__':main()
