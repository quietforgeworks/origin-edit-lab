"""Read-only independent-cursor and semantic-tree delta checks. No writer imports."""
import hashlib
import owner_walk as walker
import native_binding as root
from independent_cursor import verify_page,req

def semantic(x):
 if isinstance(x,dict):return {k:semantic(v) for k,v in x.items() if 'sha256' not in k}
 if isinstance(x,list):return [semantic(v) for v in x]
 return x

def differences(a,b,path=()):
 req(type(a)==type(b),'tree type changed')
 if isinstance(a,dict):
  req(a.keys()==b.keys(),'tree keys changed');return sum((differences(a[k],b[k],path+(k,)) for k in a),[])
 if isinstance(a,list):
  req(len(a)==len(b),'tree list size changed');return sum((differences(x,y,path+(i,)) for i,(x,y) in enumerate(zip(a,b))),[])
 return [] if a==b else [{'path':list(path),'before':a,'after':b}]

def verify(before,after,selector,before_value,after_value):
 req(type(before)is bytes and type(after)is bytes and len(before)==len(after),'source length/type')
 old=root.checked_root(before);new=root.checked_root(after)
 for tree in (old,new):
  for page in tree['pages']:page['name']=page['name']['utf8']
 req(old['dataset_envelope']['prolog']['signature']==new['dataset_envelope']['prolog']['signature'],'version changed')
 ps=[(i,p) for i,p in enumerate(old['pages']) if p['name']==selector['page']];req(len(ps)==1,'unique page');pi,p=ps[0];req(p['chain_complete'],'page incomplete')
 li=selector['layer']-1;l=p['layers'][li];req(l['chain_complete'],'layer incomplete')
 base=['pages',pi,'layers',li];field=selector['field']
 if field=='curve.line_width':
  ci=selector['curve']-1;c=l['curves'][ci];f=c['header'];dp,n=21,2;expected=base+['curves',ci,'stored_line_width_u16'];req((c['x_selector_u16'],c['y_selector_u16'],c['plot_type_u8'])==(selector['x_selector'],selector['y_selector'],selector['plot_type']),'curve context')
 elif field=='annotation.font':
  aas=[(i,a) for i,a in enumerate(l['annotations']) if a['name']==selector['annotation']];req(len(aas)==1,'unique annotation');ai,a=aas[0];f=a['style'];dp,n=4,1;expected=base+['annotations',ai,'stored_font_u8']
 else:
  gs=[(i,g) for i,g in enumerate(l['axis_groups']) if g['axis']==selector['axis']];req(len(gs)==1,'unique axis');gi,g=gs[0]
  role=selector['side']+('_tick_labels' if field=='axis.tick_font' else '_axis_line');rs=[(i,r) for i,r in enumerate(g['records']) if r['role']==role];req(len(rs)==1,'unique role');ri,r=rs[0];f=r['frame'];dp,n=21,2;expected=base+['axis_groups',gi,'records',ri,'stored_u16_at21']
 delta=differences(semantic(old),semantic(new));req(delta==[{'path':expected,'before':before_value,'after':after_value}],'not exactly intended semantic field')
 bc,bf=verify_page(before,p|{'end':p['body_end']});ap=new['pages'][pi];ac,af=verify_page(after,ap|{'end':ap['body_end']});req(bc==ac,'independent chain counts changed');req(len(bf)==len(af),'independent frame count')
 records=[]
 for (x,y,a),(u,v,b) in zip(bf,af):
  req((x,y,len(a))==(u,v,len(b)),'independent record topology changed')
  if a!=b:
   req(x==f['offset'],'wrong independently decoded record changed');req(a[:dp]+a[dp+n:]==b[:dp]+b[dp+n:],'independent record complement changed');req(int.from_bytes(a[dp:dp+n],'little')==before_value and int.from_bytes(b[dp:dp+n],'little')==after_value,'independent scalar reread')
   records.append({'offset':x,'end':y,'decoded_bytes':len(a),'decoded_differences':[i for i,(aa,bb) in enumerate(zip(a,b)) if aa!=bb]})
 req(len(records)==1,'independent changed record count')
 physical=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b]
 req(all(f['offset']<=i<f['end'] for i in physical),'whole source complement outside target frame changed')
 sf=walker.s.frame(before,f['offset']);changed_decoded=records[0]['decoded_differences'];req(physical==sorted(sf['mapping'][i] for i in changed_decoded),'whole source differences not exactly target field literals')
 # Restore without trusting any writer-generated manifest.
 restored=bytearray(after)
 for i in physical:restored[i]=before[i]
 req(bytes(restored)==before,'independent whole source restore')
 return {'independent_cursor_records_checked':len(bf),'independent_owner_counts':dict(bc),'semantic_delta':delta,'changed_records':records,'changed_native_offsets':physical,'native_non_target_complement_unchanged':True,'whole_native_restore_exact':True,'Origin_application_oracle':False,'numeric_rows_understood':False}
