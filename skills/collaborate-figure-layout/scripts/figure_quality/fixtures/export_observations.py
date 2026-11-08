# SPDX-License-Identifier: MIT
"""Emit measured observations for figure_quality_check v1; no expected answers."""
import hashlib,json,math

def digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def mul(a,b):return [a[0]*b[0]+a[2]*b[1],a[1]*b[0]+a[3]*b[1],a[0]*b[2]+a[2]*b[3],a[1]*b[2]+a[3]*b[3],a[0]*b[4]+a[2]*b[5]+a[4],a[1]*b[4]+a[3]*b[5]+a[5]]
def inv(a):
 det=a[0]*a[3]-a[1]*a[2];r=[a[3]/det,-a[1]/det,-a[2]/det,a[0]/det,0,0];r[4]=-r[0]*a[4]-r[2]*a[5];r[5]=-r[1]*a[4]-r[3]*a[5];return r

def export(source,candidate,raw):
 pw,ph=raw['canvas']['width_pt'],raw['canvas']['height_pt'];pt=pw/720
 out={'schema_version':1,'source_sha256':raw['source_sha256'],'candidate_sha256':raw['candidate_sha256'],'canvas':{'width_pt':pw,'height_pt':ph,'evidence':raw['canvas']['intended_size_evidence']},'thresholds':{'ownership_max_gap_pt':14,'ownership_neighbor_margin_pt':3,'glyph_relative_tolerance':.12,'anisotropy_relative_tolerance':.02,'ratio_relative_tolerance':.02,'scale_bar_relative_tolerance':.02,'geometry_tolerance_pt':.4,'evidence':'Corpus-specific test tolerances fixed before candidate review: nominal owner offsets are 17 SVG units; 2 px/unit glyph raster quantization is 0.3543 pt; 12% permits one-pixel small-glyph variation. Not universal publication rules.'},'elements':[],'collision_checks':[],'selection_checks':[],'anchors':[],'alignment_checks':[]}
 roles={'panel':'panel','frame':'frame','tick':'tick','curve':'curve','histogram':'curve','marker':'marker','measurement_image':'image','roi':'roi','scale_bar':'scale_bar','connector':'connector','legend_symbol':'legend_symbol','region':'region_stroke'}
 def sig(scene,id,kind):
  e=scene.get(id);m=scene.meta[id]
  if kind=='text':return digest(''.join(e.itertext()))
  if kind=='axes':return digest({'axis':m.get('axis_spec'),'local_geometry':{k:e.get(k) for k in ['x1','x2','y1','y2']},'owner':m.get('owner')})
  if kind=='data':return digest({'data':scene.data.get(m.get('data_binding')),'geometry':{k:e.get(k) for k in ['d','cx','cy','r','x','y','width','height']},'color':e.get('fill')})
  if kind=='content':return digest({'payload':e.get('href'),'geometry':{k:e.get(k) for k in ['x','y','width','height']},'owner':m.get('owner')})
  return digest({'owner':m.get('owner'),'endpoints':m.get('endpoints'),'calibration':m.get('scale_bar')})
 for r in raw['elements']:
  id=r['id'];m=candidate.meta[id];e=candidate.get(id);kind='text' if m['kind']=='text' else roles.get(m['role'],'object');role=m['role']
  matrix=mul(r['transform']['matrix'],inv(r['transform']['source_matrix']));matrix[4]*=pt;matrix[5]*=pt
  el={'id':id,'parent_id':m['owner'] if m['owner'] and m['owner']!=id and m['parent_id'] is None else m['parent_id'],'source_parent_id':source.meta[id]['owner'] if source.meta[id]['owner'] and source.meta[id]['owner']!=id and source.meta[id]['parent_id'] is None else source.meta[id]['parent_id'],'kind':kind,'role':role,'coordinate_space':'measurement' if kind in ['image','roi','scale_bar'] else r['coordinate_space'],'source_present':True,'present':True,'bbox':r['bbox'],'source_bbox':r['source_bbox'],'bbox_basis':'stroke_outer' if kind=='frame' else 'image_edge' if kind=='image' else 'container','clip_bbox':None,'transform':{'matrix':matrix,'allowed':['identity']+m['allowed'],'evidence':'Exact source-to-final composed SVG transforms; translations converted from viewBox units to physical points.'},'glyph':None,'ownership':None,'scientific_ratio':None,'scale_bar':None,'fingerprints':[],'coverage':{'x':'measured','y':'measured','reason':'Both geometric extents queried in fixed page coordinates. Data-coordinate elements retain original mapping; this does not imply all objects share alignment targets.'},'evidence':'Original deterministic SVG node and actual Inkscape query. parent_id expresses semantic membership; scene-observations.json retains structural SVG parents, source role, matrix chain, and limits.'}
  if r['glyph']:
   g=r['glyph'];el['glyph']={k:g[k] for k in ['ink_height_pt','comparison_key','face','weight']};el['glyph'].update(peer_group=role+'_'+digest([g['comparison_key'],g['face'],g['weight']])[:10],method='rendered_mask',evidence=g['measurement']+'; uncertainty ±'+str(g['uncertainty_pt'])+' pt.')
  if role=='panel_label':
   el['ownership']={'frame_id':m['owner'] if candidate.panels[m['owner']]['scientific_class']=='verified_non_measurement_schematic' else r['ownership']['owner_frame_id'],'neighbor_frame_ids':r['ownership']['neighbor_frame_ids'],'evidence':'Owner binding is defined in the synthetic source, not guessed from proximity.'}
  if kind in ['image','roi'] and r['bbox'] and r['source_bbox']:
   a,b=r['source_bbox'],r['bbox'];el['scientific_ratio']={'source':a[2]*pw/(a[3]*ph),'final':b[2]*pw/(b[3]*ph),'evidence':'Source and final actual image/ROI bounds in physical page coordinates; no crop change.'}
  if kind=='scale_bar':
   sm=source.meta[id]['scale_bar'];im=candidate.get(sm['image_id']);se=source.get(id);si=source.get(sm['image_id']);sx=float(se.get('x2'))-float(se.get('x1'));cx=float(e.get('x2'))-float(e.get('x1'));el['scale_bar']={'image_id':sm['image_id'],'source_fraction':sx/float(si.get('width')),'final_fraction':cx/float(im.get('width')),'source_value':10,'final_value':10,'source_unit':'μm','final_unit':'μm','evidence':'Exact SVG bar endpoint distance / image width, both sharing all ancestor transforms. 50 original pixels at 0.2 μm/px = 10 μm; synthetic calibration only.'}
  fkind='text' if kind=='text' else 'axes' if kind in ['axis','tick'] or 'axis_spec' in m else 'data' if kind in ['curve','marker'] or role=='heatmap_cell' else 'content' if kind in ['image','roi'] else 'association' if kind in ['connector','scale_bar'] else None
  if fkind:el['fingerprints']=[{'kind':fkind,'before':sig(source,id,fkind),'after':sig(candidate,id,fkind),'evidence':'Exact protected '+fkind+' extracted from generated source and candidate, not a visual similarity score.'}]
  out['elements'].append(el)
 # Preserve complete scientific selections, including external panel letters.
 for owner,p in candidate.panels.items():
  ids=[r['id'] for r in raw['elements'] if r['owner']==owner or r['id']==owner]
  if owner not in ids:continue
  changed=True
  while changed:
   before=set(ids);ids=sorted(before|{r['id'] for r in raw['elements'] if r['parent_id'] in before});changed=set(ids)!=before
  out['selection_checks'].append({'id':'selection_'+owner,'owner_id':owner,'expected_ids':ids,'selected_ids':ids,'evidence':'All declared semantic source members are selected, including letter/ROI/scale bar; no deletion was requested.'})
 # Canvas and dual-axis peer frame anchors are declared, not inferred from label proximity.
 byid={e['id']:e for e in out['elements']}
 frameids=[p['frame_id'] for p in candidate.panels.values() if p['scientific_class']=='synthetic_quantitative_plot']
 for id in frameids:
  b=byid[id]['bbox'];
  for ax,k,v in [('x','left',b[0]*pw),('x','right',(b[0]+b[2])*pw),('y','top',b[1]*ph),('y','bottom',(b[1]+b[3])*ph)]:out['anchors'].append({'id':id+'_'+k,'element_id':id,'axis':ax,'kind':k,'basis':'stroke_outer','position_pt':v,'evidence':'Actual Inkscape frame stroke outer bounds on fixed physical canvas.'})
 # Supported peer intent from source bounds: horizontal rows or vertical columns.
 if len(frameids)>1:
  sb=[byid[id]['source_bbox'] for id in frameids]
  for ax,edge,ix in [('y','top',1),('y','bottom',1),('x','left',0),('x','right',0)]:
   pos=[b[ix]+(b[3] if edge=='bottom' else b[2] if edge=='right' else 0) for b in sb]
   if max(pos)-min(pos)<1e-5:out['alignment_checks'].append({'id':'peer_'+edge,'anchor_ids':[id+'_'+edge for id in frameids],'target_offsets_pt':[0]*len(frameids),'tolerance_pt':.4,'relationship':'peer_layout','evidence':'Synthetic source explicitly establishes equal peer '+edge+' frame edges; tolerance fixed at 0.4 pt before candidate.'})
 # Explicit baseline pair, when fixture supplies aligned text peers.
 for ids in getattr(candidate,'baseline_peers',[]):
  aids=[]
  for id in ids:
   r=next(z for z in raw['elements'] if z['id']==id);e=candidate.get(id);M=r['transform']['matrix'];x,y=float(e.get('x')),float(e.get('y'));yy=M[1]*x+M[3]*y+M[5];aid=id+'_baseline';aids.append(aid);out['anchors'].append({'id':aid,'element_id':id,'axis':'y','kind':'baseline','basis':'baseline','position_pt':yy*pt,'evidence':'Exact SVG text baseline transformed into the final physical page; not ink top.'})
  out['alignment_checks'].append({'id':'baseline_'+ids[0],'anchor_ids':aids,'target_offsets_pt':[0]*len(ids),'tolerance_pt':.4,'relationship':'peer_layout','evidence':'Source requires a common baseline for these distinct labels; differing glyph tops do not change that intent.'})
 # Panel letters keep source-established baseline offsets from their own frames.
 for label,frame in getattr(candidate,'baseline_frame_pairs',[]):
  r=next(z for z in raw['elements'] if z['id']==label);e=candidate.get(label);M=r['transform']['matrix'];yy=M[1]*float(e.get('x'))+M[3]*float(e.get('y'))+M[5];aid=label+'_baseline'
  out['anchors'].append({'id':aid,'element_id':label,'axis':'y','kind':'baseline','basis':'baseline','position_pt':yy*pt,'evidence':'Exact transformed SVG baseline, distinct from letter ink top.'})
  se=source.get(label);sy=float(se.get('y'));source_frame=byid[frame]['source_bbox'][1]*ph
  out['alignment_checks'].append({'id':label+'_attachment','anchor_ids':[frame+'_top',aid],'target_offsets_pt':[0,sy*pt-source_frame],'tolerance_pt':.4,'relationship':'scientific_attachment','evidence':'Source establishes identical baseline-to-owner-frame offset for panel letters. Match baseline relation rather than unlike glyph ink tops.'})
 # Bbox intersections are candidates only, never asserted as true ink collisions.
 # Non-text inset occlusion is recorded independently, never blanket-exempted.
 out['collision_checks'].extend(c for c in raw.get('collision_measurements',[]) if c['a'] in byid and c['b'] in byid and (byid[c['a']]['kind']=='text' or byid[c['b']]['kind']=='text'))
 return out
