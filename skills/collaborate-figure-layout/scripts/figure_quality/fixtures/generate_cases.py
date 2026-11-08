#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate original, public-safe synthetic SVG figure-review cases.

No measurements, private sources, external downloads, or scientific findings.
Requires Python 3, NumPy, Pillow and an installed Inkscape executable.
Do not give the private-ground-truth directory or this generator to blind testers.
"""
from __future__ import annotations
import argparse, base64, copy, hashlib, io, json, math, os, shutil, subprocess, tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
from export_observations import export as export_checker
import numpy as np
from PIL import Image, ImageDraw

W,H=720,420
WIDTH_MM,HEIGHT_MM=180,105
PT_PER_UNIT=WIDTH_MM/25.4*72/W
SEED=412071
NS='http://www.w3.org/2000/svg'
XLINK='http://www.w3.org/1999/xlink'
ET.register_namespace('',NS)
ET.register_namespace('xlink',XLINK)
BLUE='#2878a8'; ORANGE='#d88232'; INK='#20252b'; GREEN='#3a8869'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jdump(p,v):Path(p).write_text(json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
def fmt(v):return f'{float(v):.6g}'
def q(tag):return '{'+NS+'}'+tag

def matmul(a,b):
 return [a[0]*b[0]+a[2]*b[1],a[1]*b[0]+a[3]*b[1],a[0]*b[2]+a[2]*b[3],a[1]*b[2]+a[3]*b[3],a[0]*b[4]+a[2]*b[5]+a[4],a[1]*b[4]+a[3]*b[5]+a[5]]
I=[1.,0.,0.,1.,0.,0.]

class Scene:
 def __init__(self,title):
  self.root=ET.Element(q('svg'),{'width':f'{WIDTH_MM}mm','height':f'{HEIGHT_MM}mm','viewBox':f'0 0 {W} {H}'})
  self.defs=ET.SubElement(self.root,q('defs'))
  self.meta={}; self.panels={}; self.data={}; self.notes=[]
  self.el('rect','page_background','background',x=0,y=0,width=W,height=H,fill='white',protected=False)
  self.text('synthetic_banner',360,20,'SYNTHETIC VALIDATION ONLY',11,anchor='middle',fill='#6c7279',role='provenance',protected=False)
  self.text('case_title',360,39,title,14,anchor='middle',role='condition',protected=False)
 def el(self,tag,id,role,parent=None,owner=None,protected=True,space='layout',**attrs):
  p=parent if parent is not None else self.root
  node=ET.SubElement(p,q(tag),{'id':id,**{k.replace('_','-'):str(v) for k,v in attrs.items()}})
  self.meta[id]={'id':id,'role':role,'kind':tag,'parent_id':p.get('id'),'owner':owner,'protected':protected,'coordinate_space':space,'local_matrix':I[:], 'allowed':['translate','uniform_scale'] if space=='layout' else []}
  return node
 def group(self,id,owner=None,matrix=None,parent=None,role='panel'):
  e=self.el('g',id,role,parent=parent,owner=owner,protected=False)
  if matrix is not None:self.transform(id,matrix)
  return e
 def transform(self,id,m):
  self.get(id).set('transform','matrix('+','.join(fmt(x) for x in m)+')');self.meta[id]['local_matrix']=list(m)
 def get(self,id):return self.root.find('.//*[@id="'+id+'"]')
 def text(self,id,x,y,text,size=13,parent=None,owner=None,role='annotation',anchor='start',fill=INK,weight='normal',protected=True,rotate=None,family='Liberation Sans'):
  e=self.el('text',id,role,parent,owner,protected=protected,x=x,y=y,font_family=family,font_size=size,font_weight=weight,text_anchor=anchor,fill=fill)
  e.text=str(text)
  if rotate:
   r=math.radians(rotate);c=math.cos(r);s=math.sin(r);self.transform(id,[c,s,-s,c,x-c*x+s*y,y-s*x-c*y])
  return e
 def rect(self,id,x,y,w,h,role,parent=None,owner=None,fill='none',stroke=INK,sw=1,**attrs):
  return self.el('rect',id,role,parent,owner,x=x,y=y,width=w,height=h,fill=fill,stroke=stroke,stroke_width=sw,**attrs)
 def line(self,id,x1,y1,x2,y2,role,parent=None,owner=None,color=INK,sw=1,**attrs):
  return self.el('line',id,role,parent,owner,x1=x1,y1=y1,x2=x2,y2=y2,stroke=color,stroke_width=sw,**attrs)
 def path(self,id,xy,role,parent=None,owner=None,color=BLUE,sw=1.7,**attrs):
  d='M '+' L '.join(f'{fmt(x)},{fmt(y)}' for x,y in xy)
  return self.el('path',id,role,parent,owner,space='data' if role in ['curve','uncertainty','histogram','marker'] else 'layout',d=d,fill='none',stroke=color,stroke_width=sw,**attrs)
 def axes(self,id,box,xlim,ylim,xlabel,ylabel,xticks=None,yticks=None,logx=False,logy=False,parent=None,letter=None):
  x,y,w,h=box;g=self.group(id,parent=parent,owner=id);self.panels[id]={'frame_id':id+'_frame','owner':id,'scientific_class':'synthetic_quantitative_plot','box':box,'axis_count':2}
  self.rect(id+'_frame',x,y,w,h,'frame',g,id,sw=1.0)
  if xticks is None:xticks=np.linspace(*xlim,5).tolist()
  if yticks is None:yticks=np.linspace(*ylim,5).tolist()
  def tx(v):return x+(math.log10(v/xlim[0])/math.log10(xlim[1]/xlim[0]) if logx else (v-xlim[0])/(xlim[1]-xlim[0]))*w
  def ty(v):return y+h-(math.log10(v/ylim[0])/math.log10(ylim[1]/ylim[0]) if logy else (v-ylim[0])/(ylim[1]-ylim[0]))*h
  for n,v in enumerate(xticks):
   xx=tx(v);self.line(f'{id}_xtick{n}',xx,y+h,xx,y+h+4,'tick',g,id)
   self.text(f'{id}_xticklabel{n}',xx,y+h+18,fmt(v),12,g,id,'tick_label','middle')
  for n,v in enumerate(yticks):
   yy=ty(v);self.line(f'{id}_ytick{n}',x-4,yy,x,yy,'tick',g,id)
   self.text(f'{id}_yticklabel{n}',x-8,yy+4,fmt(v),12,g,id,'tick_label','end')
  self.text(id+'_xlabel',x+w/2,y+h+39,xlabel,14,g,id,'axis_title','middle')
  self.text(id+'_ylabel',x-45,y+h/2,ylabel,14,g,id,'axis_title','middle',rotate=-90)
  if letter:self.text(id+'_letter',x-17,y-12,letter,18,self.root,id,'panel_label',weight='bold')
  self.meta[id]['axis_spec']={'xlim':xlim,'ylim':ylim,'xticks':xticks,'yticks':yticks,'xscale':'log' if logx else 'linear','yscale':'log' if logy else 'linear','axis_count':2}
  return g,tx,ty
 def curve(self,id,xs,ys,tx,ty,parent,owner,color=BLUE,**attrs):
  node=self.path(id,list(zip(map(tx,xs),map(ty,ys))),'curve',parent,owner,color=color,**attrs)
  self.data[id]={'x':list(map(float,xs)),'y':list(map(float,ys)),'provenance':'original deterministic synthetic function'}
  self.meta[id]['data_binding']=id
  return node
 def clip(self,id,box):
  cp=ET.SubElement(self.defs,q('clipPath'),{'id':id}); ET.SubElement(cp,q('rect'),dict(zip(['x','y','width','height'],map(str,box))));return 'url(#'+id+')'
 def save(self,path):
  ET.indent(self.root,space='  ');ET.ElementTree(self.root).write(path,encoding='utf-8',xml_declaration=True)
 def clone(self):return copy.deepcopy(self)


def line_case():
 s=Scene('Log response with a nested detail view')
 g,tx,ty=s.axes('p1',[75,80,555,270],[.1,100],[.1,10],'Synthetic input (a.u.)','Synthetic response (a.u.)',[.1,1,10,100],[.1,1,10],True,True,letter='a')
 xs=np.geomspace(.1,100,80);ys=.28+.7*np.sqrt(xs)
 s.curve('p1_curve',xs,ys,tx,ty,g,'p1')
 ig,itx,ity=s.axes('inset',[401,112,165,95],[1,3],[.8,1.7],'Input','Response',[1,2,3],[1,1.5],parent=g)
 # A deliberate inset is a scientific unit, not accidental overlap.
 s.get('inset_frame').set('fill','white');s.get('inset_ylabel').set('font-size','10');s.get('inset_xlabel').set('font-size','10')
 s.curve('inset_curve',np.linspace(1,3,30),.28+.7*np.sqrt(np.linspace(1,3,30)),itx,ity,ig,'inset',color=ORANGE)
 s.meta['inset']['semantic_relationship']='nested scientific panel; placement must not conceal evidence';s.panels['inset']['scientific_class']='synthetic_inset_plot'
 s.occlusion_pairs=[('inset','p1_curve')]
 return s,s.clone(),[{'category':'non_text_occlusion','targets':['inset','p1_curve'],'reason':'The opaque inset conceals a substantial main-curve segment in both source and candidate. Required inset membership does not approve its location; source equality is not visual acceptance.'}]

def hist_case():
 s=Scene('Paired synthetic distribution and response')
 a,tx,ty=s.axes('p1',[70,90,245,245],[0,5],[0,40],'Synthetic size (a.u.)','Count',[0,1,2,3,4,5],[0,10,20,30,40],letter='a')
 vals=[4,11,23,35,29,17,9,3];edges=np.linspace(.2,4.8,9)
 for i,v in enumerate(vals):s.rect('hist_bin'+str(i),tx(edges[i]),ty(v),tx(edges[i+1])-tx(edges[i])-2,ty(0)-ty(v),'histogram',a,'p1',fill=BLUE,stroke='white',sw=.6)
 s.data['histogram']={'edges':edges.tolist(),'counts':vals};s.meta['p1']['data_binding']='histogram'
 b,bx,by=s.axes('p2',[420,90,245,245],[0,5],[0,1],'Synthetic size (a.u.)','Fraction',[0,1,2,3,4,5],[0,.5,1],letter='b')
 x=np.linspace(0,5,60);s.curve('paired_curve',x,1/(1+np.exp(-2*(x-2.4))),bx,by,b,'p2',color=ORANGE)
 s.text('condition',197,74,'Condition Q',13,owner='p1',role='condition',anchor='middle')
 s.text('annotation',480,155,'Synthetic transition',12,b,'p2')
 c=s.clone();c.collision_pairs=[('condition','p1_xlabel')];c.get('condition').set('x','202');c.get('condition').set('y','374')
 c.get('p2_xlabel').set('x','683');c.get('p2_xlabel').set('text-anchor','start')
 return s,c,[{'category':'overlap','targets':['condition','p1_xlabel'],'reason':'Condition text crosses the axis title.'},{'category':'clipping','targets':['p2_xlabel'],'reason':'Axis title extends beyond the fixed page.'}]

def scatter_case(flaw=False):
 s=Scene('Synthetic scatter, regions, and reference annotations')
 rng=np.random.default_rng(SEED+3)
 for k,x0 in enumerate([70,420]):
  id=f'p{k+1}';g,tx,ty=s.axes(id,[x0,90,245,245],[0,1],[0,1],'Synthetic x (a.u.)','Synthetic y (a.u.)',[0,.5,1],[0,.5,1],letter=chr(97+k))
  s.rect(id+'_region',tx(.52),ty(.85),tx(.9)-tx(.52),ty(.4)-ty(.85),'region',g,id,fill='#e6f1ed',stroke=GREEN,sw=.8,stroke_dasharray='4 3')
  pts=rng.uniform(.08,.92,(28,2));s.data[id+'_points']={'xy':pts.tolist()}
  for j,(x,y) in enumerate(pts):
   s.el('circle',f'{id}_point{j}','marker',g,id,space='data',cx=tx(x),cy=ty(y),r=2.4,fill=BLUE,stroke='none');s.meta[f'{id}_point{j}']['data_binding']=id+'_points'
  s.line(id+'_ref',tx(.1),ty(.15),tx(.9),ty(.8),'scientific_reference',g,id,color=ORANGE,sw=1.2,stroke_dasharray='5 3')
  s.text(id+'_ref_label',tx(.09),ty(.08),'Ref. [4]',10,g,id,'reference')
  s.text(id+'_region_label',tx(.65),ty(.88),'Region R',11,g,id,'annotation','middle')
 c=s.clone();issues=[]
 if flaw:
  c.collision_pairs=[('p1_ref_label','p1_region_label')]
  c.get('p2_letter').set('x','354');c.get('p2_letter').set('y','85')
  c.get('p1_region_label').set('x','292');c.get('p1_region_label').set('y','322')
  c.get('p1_ref_label').set('x','294');c.get('p1_ref_label').set('y','322');c.get('p1_ref_label').set('text-anchor','middle')
  issues=[{'category':'panel_label_ownership','targets':['p2_letter'],'reason':'Panel b is detached into the inter-panel gutter.'},{'category':'overlap','targets':['p1_ref_label','p1_region_label'],'reason':'Two distinct semantic labels coincide.'}]
 return s,c,issues

def pulse_case():
 s=Scene('Dense deterministic synthetic pulse train')
 g,tx,ty=s.axes('p1',[75,80,555,270],[0,12],[-.3,1.5],'Synthetic time (ms)','Signal (a.u.)',[0,3,6,9,12],[-.3,0,.5,1,1.5],letter='a')
 xs=np.linspace(0,12,2600);ys=.1*np.sin(xs*67)+.035*np.cos(xs*211)
 centers=np.arange(.2,11.9,.19)
 for n,p in enumerate(centers):ys+=(.65+.25*math.sin(n*1.37)**2)*np.exp(-((xs-p)/.018)**2)
 ys+=.46*np.exp(-((xs-7.23)/.012)**2)
 s.curve('dense_pulses',xs,ys,tx,ty,g,'p1',sw=1.05)
 s.text('pulse_note',95,102,'Synthetic pulse-train simulation',12,g,'p1','condition')
 s.data['dense_pulses']['construction']={'pulse_centers':centers.tolist(),'extra_pulse_center':7.23,'sample_count':len(xs)}
 return s,s.clone(),[]

def heatmap_case():
 s=Scene('Synthetic quantitative field and calibrated colorbar')
 g=s.group('p1',owner='p1');s.panels['p1']={'frame_id':'map_frame','owner':'p1','scientific_class':'synthetic_quantitative_map','box':[90,80,420,270]}
 values=np.array([[math.sin(i/3)*math.cos(j/4)+.15*i/10 for i in range(16)] for j in range(10)])
 s.data['field']={'values':values.tolist(),'range':[-1,1.2]}
 def col(v):
  t=max(0,min(1,(v+1)/2.2));return '#%02x%02x%02x'%(int(48+190*t),int(86+120*(1-abs(2*t-1))),int(177-135*t))
 for j,row in enumerate(values):
  for i,v in enumerate(row):s.rect(f'cell_{j}_{i}',90+i*26.25,80+j*27,26.35,27.1,'heatmap_cell',g,'p1',fill=col(v),stroke='none',sw=0);s.meta[f'cell_{j}_{i}']['data_binding']='field'
 s.rect('map_frame',90,80,420,270,'frame',g,'p1')
 s.text('p1_letter',72,70,'a',18,owner='p1',role='panel_label',weight='bold')
 s.text('map_xlabel',300,386,'Synthetic x (a.u.)',14,g,'p1','axis_title','middle')
 s.text('map_ylabel',50,215,'Synthetic y (a.u.)',14,g,'p1','axis_title','middle',rotate=-90)
 cb=s.group('colorbar',owner='p1')
 for j in range(110):s.rect(f'cb_segment{j}',555,80+j*270/110,18,270/110+.1,'colorbar_segment',cb,'p1',fill=col(1.2-j*2.2/109),stroke='none',sw=0)
 s.rect('colorbar_frame',555,80,18,270,'colorbar',cb,'p1')
 for n,v in enumerate([-1,0,1.2]):
  yy=350-(v+1)/2.2*270;s.line('cb_tick'+str(n),573,yy,578,yy,'tick',cb,'p1');s.text('cb_text'+str(n),583,yy+4,fmt(v),12,cb,'p1','tick_label')
 s.text('cb_label',632,215,'Field (a.u.)',14,cb,'p1','axis_title','middle',rotate=-90)
 c=s.clone();c.collision_pairs=[('colorbar','map_frame'),('cb_label','cb_text1')];c.transform('colorbar',[1,0,0,1,-60,0]);c.get('cb_label').set('x','568');c.get('cb_label').set('transform','matrix(0,-1,1,0,370,783)');c.meta['cb_label']['local_matrix']=[0,-1,1,0,370,783]
 return s,c,[{'category':'occlusion','targets':['colorbar','map_frame'],'reason':'Colorbar overlaps data-bearing map cells.'},{'category':'overlap','targets':['cb_label','cb_text1'],'reason':'Colorbar title is moved into the tick-label area.'}]

def dual_case():
 s=Scene('Two distinct synthetic responses on separate axes')
 g,tx,ty=s.axes('p1',[95,80,490,270],[0,10],[0,1],'Synthetic time (s)','Response A (a.u.)',[0,2,4,6,8,10],[0,.5,1],letter='a')
 x=np.linspace(0,10,81);s.curve('response_a',x,.2+.06*x+.06*np.sin(x),tx,ty,g,'p1',color=BLUE)
 ty2=lambda v:350-v/100*270;s.curve('response_b',x,70-4*x+10*np.cos(x/2),tx,ty2,g,'p1',color=ORANGE)
 s.panels['p1']['axis_count']=3;s.meta['p1']['axis_spec']['axis_count']=3;s.meta['p1']['axis_spec']['right_ylim']=[0,100]
 for n,v in enumerate([0,50,100]):
  y=ty2(v);s.line('right_tick'+str(n),585,y,590,y,'tick',g,'p1',color=ORANGE);s.text('right_ticklabel'+str(n),597,y+4,v,12,g,'p1','tick_label',fill=ORANGE)
 s.text('right_ylabel',659,215,'Response B (%)',14,g,'p1','axis_title','middle',fill=ORANGE,rotate=-90)
 for k,(name,color) in enumerate([('Response A',BLUE),('Response B',ORANGE)]):
  s.line('legend_symbol'+str(k),113,105+k*19,135,105+k*19,'legend_symbol',g,'p1',color=color,sw=1.7);s.text('legend_text'+str(k),142,109+k*19,name,12,g,'p1','legend_text')
 return s,s.clone(),[]

def font_case():
 s=Scene('Matched roles through composed geometry transforms')
 for k,x0 in enumerate([70,420]):
  id=f'p{k+1}';outer=s.group(id+'_host',matrix=I)
  g,tx,ty=s.axes(id,[x0,90,245,245],[0,4],[0,4],'Synthetic x (a.u.)','Synthetic y (a.u.)',[0,2,4],[0,2,4],parent=outer,letter=chr(97+k))
  x=np.linspace(0,4,31);s.curve(id+'_curve',x,.4+.7*x,tx,ty,g,id)
  for n,v in enumerate([.6,1.5,2.6,3.5]):s.el('circle',id+'_marker'+str(n),'marker',g,id,space='data',cx=tx(v),cy=ty(.4+.7*v),r=3,fill=BLUE)
  s.text(id+'_sample',x0+122,72,'SAMPLE 0123',13,owner=id,role='condition',anchor='middle')
 c=s.clone();c.transform('p2_host',[1.08,0,0,.72,-33.6,25.2]);c.transform('p2',[.95,0,0,1.08,21, -7.2])
 # Same nominal font size, much smaller visual text due to ancestor transform.
 c.transform('p2_sample',[1,0,0,.68,0,23.04])
 return s,c,[{'category':'anisotropy','targets':['p2_host','p2','p2_marker0'],'reason':'Composed x/y scaling distorts glyphs, markers, strokes, and quantitative geometry.'},{'category':'optical_font_size','targets':['p1_sample','p2_sample','p2_xticklabel1'],'reason':'Equal nominal point sizes hide final ink-height mismatch.'}]

def make_texture():
 yy,xx=np.mgrid[:220,:330];rng=np.random.default_rng(SEED+9);a=np.full((220,330),.12)
 for _ in range(34):
  x,y=rng.uniform(10,320),rng.uniform(10,210);sx,sy=rng.uniform(4,11),rng.uniform(5,15);a+=rng.uniform(.17,.62)*np.exp(-((xx-x)/sx)**2-((yy-y)/sy)**2)
 a=np.clip(a+rng.normal(0,.025,a.shape),0,1);b=io.BytesIO();Image.fromarray(np.uint8(a*255)).save(b,format='PNG');return b.getvalue()

def micro_case(flaw=False):
 s=Scene('Synthetic microscopy-like texture, not an experiment')
 g=s.group('p1',owner='p1');s.panels['p1']={'frame_id':'texture_image','owner':'p1','scientific_class':'synthetic_measurement_like_image','box':[112.5,70,495,330],'box_coordinate_space':'source_local_viewbox'}
 data=make_texture();s.el('image','texture_image','measurement_image',g,'p1',x=112.5,y=70,width=495,height=330,preserveAspectRatio='none',href='data:image/png;base64,'+base64.b64encode(data).decode())
 s.meta['texture_image']['image']={'pixel_width':330,'pixel_height':220,'original_sha256':hashlib.sha256(data).hexdigest(),'physical_pixel_size_um':[.2,.2],'crop':[0,0,1,1]}
 s.rect('roi',220,142,100,80,'roi',g,'p1',stroke='#f6dc72',sw=1.4)
 s.text('roi_label',226,137,'ROI',12,g,'p1',fill='#f6dc72')
 s.line('scale_bar',491,369,566,369,'scale_bar',g,'p1',color='white',sw=5)
 s.text('scale_bar_label',528.5,390,'10 μm',13,g,'p1','scale_bar_label','middle',fill='white')
 s.meta['scale_bar']['scale_bar']={'image_id':'texture_image','label_id':'scale_bar_label','source_length_px':50,'physical_length_um':10,'orientation':'horizontal'}
 s.text('p1_letter',94,67,'a',18,owner='p1',role='panel_label',weight='bold')
 s.data['texture']={'generator':'sum of deterministic Gaussian blobs + fixed-seed noise','seed':SEED+9,'pixel_size_um':[.2,.2],'size_px':[330,220],'status':'SIMULATED CALIBRATION, NOT MEASURED'}
 c=s.clone();issues=[]
 if flaw:
  c.transform('p1',[1.1,0,0,.76,-36,16.8]);c.get('scale_bar').set('x2','585')
  issues=[{'category':'physical_aspect','targets':['texture_image','roi'],'reason':'Anisotropic group deformation changes physical aspect.'},{'category':'scale_bar','targets':['scale_bar'],'reason':'Scale bar length changes independently of the protected image/calibration.'}]
 return s,c,issues

def schematic_case():
 s=Scene('Non-measurement schematic with preserved topology')
 p=s.group('p1',owner='p1');s.panels['p1']={'frame_id':'body1','owner':'p1','scientific_class':'verified_non_measurement_schematic','box':[85,115,550,220]}
 s.text('p1_letter',73,153,'a',18,owner='p1',role='panel_label',weight='bold')
 for k,(x,t) in enumerate([(90,'Input'),(290,'Process'),(490,'Output')]):
  s.rect('body'+str(k+1),x,165,140,100,'schematic_body',p,'p1',fill=['#edf4f8','#f5eee5','#eaf3ec'][k],stroke=[BLUE,ORANGE,GREEN][k],sw=1.5,rx=8)
  s.text('body_label'+str(k+1),x+70,220,t,17,p,'p1','diagram_label','middle')
 for k,x in enumerate([230,430]):
  s.line('connector'+str(k),x,215,x+60,215,'connector',p,'p1',sw=1.8)
  s.path('arrowhead'+str(k),[(x+51,210),(x+60,215),(x+51,220)],'connector',p,'p1',color=INK,sw=1.8)
  s.meta['connector'+str(k)]['endpoints']=[{'owner':'body'+str(k+1),'anchor':'right_center'},{'owner':'body'+str(k+2),'anchor':'left_center'}]
 s.text('schematic_note',360,318,'Illustration only. Shapes have no physical scale.',12,p,'p1','condition','middle')
 c=s.clone()
 # Authorized illustrative body adaptation; labels, components, topology remain.
 for k in range(1,4):c.get('body'+str(k)).set('height','135');c.get('body'+str(k)).set('y','147.5')
 return s,c,[]

def mutation_case():
 s=Scene('Synthetic paired time series')
 g,tx,ty=s.axes('p1',[80,80,550,270],[0,8],[0,10],'Synthetic time (s)','Synthetic response (a.u.)',[0,2,4,6,8],[0,2,4,6,8,10],letter='a')
 xs=np.linspace(0,8,65);ys=1.1+.8*xs+.4*np.sin(xs)
 s.curve('series_q',xs,ys,tx,ty,g,'p1')
 s.curve('series_r',xs,ys+.7,tx,ty,g,'p1',color=ORANGE)
 s.text('legend_q',112,110,'Series Q',12,g,'p1','legend_text',fill=BLUE);s.text('legend_r',112,130,'Series R',12,g,'p1','legend_text',fill=ORANGE)
 c=s.clone();new=ys.copy();new[28:36]+=.35
 c.get('series_q').set('d','M '+' L '.join(f'{fmt(tx(x))},{fmt(ty(y))}' for x,y in zip(xs,new)))
 c.data['series_q']['y']=new.tolist();c.get('p1_xlabel').text='Synthetic time (ms)'
 return s,c,[{'category':'data_mutation','targets':['series_q'],'reason':'Eight plotted values changed without a scientific-edit request.'},{'category':'exact_text','targets':['p1_xlabel'],'reason':'Axis unit changed from s to ms without rescaling data.'}]

def alignment_case():
 s=Scene('Synthetic responses in three conditions')
 for k,y0 in enumerate([77,177,277]):
  id=f'p{k+1}';g,tx,ty=s.axes(id,[105,y0,435,57],[0,4],[0,4],'Synthetic x (a.u.)','Y',[0,2,4],[0,4],letter=chr(97+k))
  s.get(id+'_xlabel').set('font-size','10');s.get(id+'_xlabel').set('y',str(y0+89));s.get(id+'_ylabel').set('font-size','11')
  xx=np.linspace(0,4,25);s.curve(id+'_curve',xx,1+.6*xx,tx,ty,g,id)
 # Source letter baselines have equal owner-frame-relative attachment.
 s.baseline_frame_pairs=[(f'p{k}_letter',f'p{k}_frame') for k in [1,2,3]]
 c=s.clone()
 for k,scale in [(2,1.07),(3,1.13)]:
  id=f'p{k}';c.transform(id,[scale,0,0,1,105*(1-scale),0])
  for nodeid,m in c.meta.items():
   if m['owner']==id and m['kind']!='text':m['allowed']+=['anisotropic_scale']
   if m['parent_id']==id and m['kind']=='text':
    e=c.get(nodeid)
    if nodeid.endswith('_ylabel'):continue
    x=float(e.get('x'));c.transform(nodeid,[1/scale,0,0,1,x*(1-1/scale),0])
 c.get('p1_letter').set('y','60.8')
 return s,c,[{'category':'required_alignment','targets':['p1_frame','p2_frame','p3_frame'],'reason':'Declared peer left edges remain aligned but right edges form an unintended staircase.'},{'category':'baseline_alignment','targets':['p1_letter','p2_letter','p3_letter'],'reason':'First lowercase letter moves toward matching relative ink tops, but violates the common owner-frame baseline offset.'}]

CASES=[line_case,hist_case,alignment_case,lambda:scatter_case(True),pulse_case,heatmap_case,dual_case,font_case,micro_case,lambda:micro_case(True),schematic_case,mutation_case]


def render(svg,png,width=1440):
 env=os.environ.copy();env['INKSCAPE_PROFILE_DIR']=str(Path(svg).parent/'.inkscape');env['XDG_CACHE_HOME']=str(Path(svg).parent/'.cache')
 cmd=['inkscape',str(svg),'--export-area-page','--export-type=png',f'--export-width={width}','--export-background=white','--export-background-opacity=1',f'--export-filename={png}']
 result=subprocess.run(cmd,capture_output=True,text=True,env=env)
 if result.returncode:raise RuntimeError(result.stderr)
 return result.stderr

def query(svg):
 p=subprocess.run(['inkscape',str(svg),'--query-all'],capture_output=True,text=True,check=True)
 out={};nativeW=WIDTH_MM/25.4*96;nativeH=HEIGHT_MM/25.4*96
 for line in p.stdout.splitlines():
  try:
   name,x,y,w,h=line.split(',');out[name]=[float(x)/nativeW,float(y)/nativeH,float(w)/nativeW,float(h)/nativeH]
  except ValueError:continue
 return out

def transforms(scene):
 result={}
 def rec(id):
  if id in result:return result[id]
  m=scene.meta[id];result[id]=matmul(rec(m['parent_id']) if m['parent_id'] in scene.meta else I,m['local_matrix']);return result[id]
 for id in scene.meta:rec(id)
 return result

def fingerprint(scene,id):
 e=scene.get(id);m=scene.meta[id]
 payload={'role':m['role'],'text':''.join(e.itertext()) if e.tag==q('text') else None}
 if 'axis_spec' in m:payload['axis_spec']=m['axis_spec']
 if 'data_binding' in m:payload['data']=scene.data[m['data_binding']]
 if m['role'] in ['curve','marker','histogram','heatmap_cell','scientific_reference']:
  payload['geometry']={k:v for k,v in e.attrib.items() if k in ['d','x','y','width','height','cx','cy','r','fill','stroke']}
 if m['role']=='measurement_image':payload['image']=e.get('href');payload['preserveAspectRatio']=e.get('preserveAspectRatio')
 if m['role']=='connector':payload['endpoints']=m.get('endpoints')
 return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def glyph_metrics(scene,outdir):
 # Isolated glyph masks at exact final-scale linear transforms. Rotation is retained.
 # Use renderer query bounds to position a nonoverlapping atlas, not as ink evidence.
 tr=transforms(scene);atlas=ET.Element(q('svg'),{'width':'640','height':'1','viewBox':'0 0 640 1'})
 entries=[];y=0
 for id,m in scene.meta.items():
  if m['kind']!='text' or m['role']=='provenance':continue
  e=scene.get(id);M=tr[id];ang=math.degrees(math.atan2(M[1],M[0]))
  if abs(ang)>1:continue
  cell=ET.SubElement(atlas,q('g'),{'transform':f'translate(80,{y+55})'});t=copy.deepcopy(e);t.set('x','0');t.set('y','0');t.set('text-anchor','start');t.set('fill','black');t.set('transform','matrix('+','.join(fmt(z) for z in [M[0],M[1],M[2],M[3],0,0])+')');cell.append(t)
  entries.append((id,y));y+=90
 atlas.set('height',str(y));atlas.set('viewBox',f'0 0 640 {y}')
 svg=outdir/'glyph-atlas.svg';png=outdir/'glyph-atlas.png';ET.ElementTree(atlas).write(svg,encoding='utf-8',xml_declaration=True);render(svg,png,1280)
 a=np.array(Image.open(png).convert('RGB'));metrics={}
 for id,y in entries:
  crop=a[y*2:(y+90)*2];mask=np.min(crop,axis=2)<128;rows=np.where(mask.any(axis=1))[0];cols=np.where(mask.any(axis=0))[0]
  metrics[id]={'ink_height_pt':float((rows[-1]-rows[0]+1)/2*PT_PER_UNIT) if len(rows) else 0,'ink_width_pt':float((cols[-1]-cols[0]+1)/2*PT_PER_UNIT) if len(cols) else 0,'measurement':'isolated rendered text, threshold <128/255 at 2 px/viewBox unit, full composed linear transform','uncertainty_pt':PT_PER_UNIT/2,'comparison_key':''.join(scene.get(id).itertext()),'face':scene.get(id).get('font-family'),'weight':scene.get(id).get('font-weight'),'nominal_font_size':float(scene.get(id).get('font-size'))}
 svg.unlink();png.unlink();return metrics

def measure_collisions(scene,outdir):
 pairs=getattr(scene,'collision_pairs',[]);masks={};results=[]
 for id in sorted({x for pair in pairs for x in pair}):
  root=copy.deepcopy(scene.root)
  def prune(node,inside=False):
   inside=inside or node.get('id')==id
   for child in list(node):
    if child.tag==q('defs'):continue
    if inside:continue
    if child.get('id')==id or child.find('.//*[@id="'+id+'"]') is not None:prune(child,inside)
    else:node.remove(child)
  prune(root)
  for node in root.iter():
   if node.get('fill') and node.get('fill')!='none':node.set('fill','black')
   if node.get('stroke') and node.get('stroke')!='none':node.set('stroke','black')
  svg=outdir/'mask-tmp.svg';png=outdir/'mask-tmp.png';ET.ElementTree(root).write(svg,encoding='utf-8',xml_declaration=True);render(svg,png)
  masks[id]=np.min(np.array(Image.open(png).convert('RGB')),axis=2)<128
  svg.unlink();png.unlink()
 for a,b in pairs:
  n=int(np.count_nonzero(masks[a]&masks[b]));results.append({'a':a,'b':b,'method':'rendered_mask','intersects':bool(n),'evidence':f'Isolated opaque black masks rendered on identical 1440×840 canvas; threshold <128/255; intersecting pixels={n}. Source transforms preserved, no registration.','exemption':None})
 return results

def observations(source,candidate,case_dir):
 sb=query(case_dir/'source.svg');cb=query(case_dir/'candidate.svg');st=transforms(source);ct=transforms(candidate)
 gm=glyph_metrics(candidate,case_dir);collisions=measure_collisions(candidate,case_dir)
 from painted_occlusion import measure
 occlusion=[measure(case_dir/'candidate.svg',front,target,case_dir/'occlusion-evidence'/f'{front}-over-{target}') for front,target in getattr(candidate,'occlusion_pairs',[])]
 elements=[]
 for id,m in candidate.meta.items():
  e=candidate.get(id);rec={**m,'bbox':cb.get(id),'source_bbox':sb.get(id),'present':id in cb,'source_present':id in sb,'transform':{'matrix':ct[id],'source_matrix':st.get(id),'allowed':m['allowed'],'evidence':'composed exact SVG ancestor/local matrices; translation in viewBox units'},'glyph':gm.get(id),'fingerprints':[{'kind':'protected_semantics','before':fingerprint(source,id),'after':fingerprint(candidate,id),'evidence':'exact text, axis/data binding, quantitative geometry, image payload, or connector endpoints as applicable'}] if m['protected'] else []}
  if rec['glyph']:rec['glyph']['peer_group']=m['role'];rec['glyph']['evidence']='isolated Inkscape raster atlas at matched final scale'
  if m['role']=='panel_label':rec['ownership']={'owner_id':m['owner'],'owner_frame_id':candidate.panels[m['owner']]['frame_id'],'neighbor_frame_ids':[p['frame_id'] for k,p in candidate.panels.items() if k!=m['owner'] and p['scientific_class']!='synthetic_inset_plot']}
  if e.tag==q('text'):rec['text']=''.join(e.itertext());rec['source_text']=''.join(source.get(id).itertext())
  elements.append(rec)
 return {'schema_version':1,'synthetic':True,'source_file':'source.svg','candidate_file':'candidate.svg','source_sha256':sha(case_dir/'source.svg'),'candidate_sha256':sha(case_dir/'candidate.svg'),'canvas':{'width_pt':WIDTH_MM/25.4*72,'height_pt':HEIGHT_MM/25.4*72,'viewbox':[0,0,W,H],'render_width_px':1440,'render_height_px':840,'intended_size_evidence':'Explicit synthetic corpus design: 180 × 105 mm; not inferred from PNG metadata.'},'bbox_convention':{'units':'normalized canvas fractions','form':'x,y,width,height','measurement':'Inkscape --query-all geometric bounds; not asserted as full raster ink or baseline','native_query_css_px_per_svg_unit':WIDTH_MM/25.4*96/W},'panels':list(candidate.panels.values()),'collision_measurements':collisions,'painted_occlusion_measurements':occlusion,'elements':elements,'limits':['Synthetic fixtures only; no real measurement findings.','SVG render/editability only; does not establish PowerPoint, Origin, OLE, native reopen, or refresh persistence.','Object bounds support candidate overlap checks, not proof of semantic occlusion.','The absence of a supplied element is not evidence of absence in arbitrary inputs.','Glyph masks measure actual isolated raster ink under a stated threshold; optical readability still requires full-figure inspection.']}

def generate(out):
 license_text=(Path(__file__).resolve().parents[3]/'references'/'figure-quality-license.txt').read_text()
 out=Path(out);out.mkdir(parents=True,exist_ok=False)
 (out/'LICENSE.txt').write_text(license_text)
 cases=out/'cases';private=out/'private-ground-truth';cases.mkdir();private.mkdir()
 truth={'synthetic':True,'seed':SEED,'fixture_version':'1.1','cases':[]};index=[]
 for n,make in enumerate(CASES,1):
  cid=f'case-{n:02d}';d=cases/cid;d.mkdir(exist_ok=True);s,c,issues=make();s.save(d/'source.svg');c.save(d/'candidate.svg');render(d/'source.svg',d/'source.png');render(d/'candidate.svg',d/'candidate.png')
  jdump(d/'source-data.json',s.data);jdump(d/'candidate-data.json',c.data)
  raw=observations(s,c,d);jdump(d/'scene-observations.json',raw);jdump(d/'observations.json',export_checker(s,c,raw))
  jdump(d/'provenance.json',{'synthetic':True,'seed':SEED,'license':'MIT','copyright':'Copyright (c) 2026 quietforgeworks','source':'Original mathematical functions and deterministic pseudorandom arrays generated locally for figure-layout validation.','no_private_material':True,'no_measured_data':True,'case_id':cid,'source_svg_sha256':sha(d/'source.svg'),'candidate_svg_sha256':sha(d/'candidate.svg'),'source_data_sha256':sha(d/'source-data.json'),'candidate_data_sha256':sha(d/'candidate-data.json'),'generator':'generate_cases.py','generator_version':'1.1','physical_output_mm':[WIDTH_MM,HEIGHT_MM]})
  jdump(d/'request.json',{'request':'Review the candidate against the intact source for scientific figure-layout quality at 180 × 105 mm. Identify complete semantic panels, panel-letter ownership, occlusion/clipping, text/transform quality, and fidelity. Preserve all source content and scientific mappings. Propose only justified minimal fixes; do not rewrite data or relabel axes. Treat all figures as synthetic validation examples, not scientific findings.','available_inputs':['source.svg','source.png','candidate.svg','candidate.png','source-data.json','candidate-data.json','observations.json','provenance.json'],'not_required':['PowerPoint/Origin lifecycle claims','external publication']})
  index.append({'case_id':cid,'directory':cid,'request':'request.json','source':'source.png','candidate':'candidate.png'})
  truth['cases'].append({'case_id':cid,'expected_issues':issues,'clean':not issues,'protected_roles':sorted(set(m['role'] for m in s.meta.values() if m['protected'])),'rejection_conditions':['Deleting any true data pulse or marker to improve appearance','Regenerating a measurement-like image','Changing data or scientific text under a layout-only request'],'specific_expected':{'case-01':'Retain logarithmic axes and the complete inset, but flag the current inset location because its opaque fill hides the main curve. Membership is required; placement is not fixed.','case-04':'Reference labels are not panel letters; region and reference line are scientific content.','case-05':'Every dense pulse and extra spike is legitimate synthetic source content.','case-07':'Retain both y axes, distinct units, and correct series mapping.','case-09':'Preserve image texture, ROI, aspect, scale bar, and calibration.','case-11':'Illustrative body adaptation is allowed; preserve normal glyphs and connector topology.'}.get(cid)})
  shutil.rmtree(d/'.inkscape',ignore_errors=True);shutil.rmtree(d/'.cache',ignore_errors=True)
  print(f'{cid}: ready',flush=True)
 jdump(cases/'index.json',{'synthetic':True,'cases':index,'blind_review':'Do not consult generator or private-ground-truth until your report is locked.'});jdump(private/'manifest.json',truth)
 # A contact sheet is useful for visual QA; individual cases retain native detail.
 sheet=Image.new('RGB',(1440,12*295),'white');draw=ImageDraw.Draw(sheet)
 for n in range(1,13):
  for k,name in enumerate(['source','candidate']):
   im=Image.open(cases/f'case-{n:02d}'/(name+'.png'));im.thumbnail((700,260));sheet.paste(im,(k*720,30+(n-1)*295));draw.text((k*720+12,8+(n-1)*295),f'case-{n:02d} {name} / SYNTHETIC',fill='black')
 sheet.save(out/'qa-contact-sheet.png')
 return truth

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();generate(args.output)
