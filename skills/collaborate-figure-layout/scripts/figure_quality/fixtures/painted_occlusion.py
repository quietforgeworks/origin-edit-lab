# SPDX-License-Identifier: MIT
"""Narrow actual-render evidence for a foreground object hiding a target curve.

Synthetic SVG fixtures only. This is not a complete scientific-occlusion detector.
It compares the unchanged actual render to an explicitly labeled verification
copy omitting only the occluder. Neither input nor delivered output is modified.
"""
from pathlib import Path
import copy,hashlib,re
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from generate_cases import render, q, sha

def measure(svg,foreground_id,target_id,outdir):
 svg=Path(svg);outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=False)
 before=sha(svg);root=ET.parse(svg).getroot();fg=root.find('.//*[@id="'+foreground_id+'"]');target=root.find('.//*[@id="'+target_id+'"]')
 if fg is None or target is None:raise ValueError('Both original SVG IDs must exist')
 order=list(root.iter())
 if order.index(fg)<=order.index(target):raise ValueError('Foreground must be painted after the target')
 color=target.get('stroke','')
 if not re.fullmatch(r'#[0-9a-fA-F]{6}',color):raise ValueError('This bounded fixture check requires an explicit six-digit target stroke color')
 rgb=np.array([int(color[k:k+2],16) for k in [1,3,5]],dtype=np.int16)
 actual=outdir/'actual.png';render(svg,actual)
 verify=copy.deepcopy(root);vf=verify.find('.//*[@id="'+foreground_id+'"]')
 parent=next(p for p in verify.iter() if vf in list(p));parent.remove(vf)
 verification_svg=outdir/'verification-without-occluder.svg';ET.ElementTree(verify).write(verification_svg,encoding='utf-8',xml_declaration=True)
 reference=outdir/'verification-without-occluder.png';render(verification_svg,reference)
 isolated=copy.deepcopy(root)
 def retain(n):
  for ch in list(n):
   if ch.tag==q('defs'):continue
   if ch.get('id')==target_id:continue
   if ch.find('.//*[@id="'+target_id+'"]') is not None:retain(ch)
   else:n.remove(ch)
 retain(isolated);isolated_svg=outdir/'verification-isolated-target.svg';ET.ElementTree(isolated).write(isolated_svg,encoding='utf-8',xml_declaration=True)
 target_png=outdir/'verification-isolated-target.png';render(isolated_svg,target_png)
 images=[np.array(Image.open(p).convert('RGB')).astype(np.int16) for p in [actual,reference,target_png]]
 if len({a.shape for a in images})!=1:raise ValueError('Rendering comparison must use identical canvas and scale')
 # Restrict to pixels independently verified as target-colored in BOTH the
 # isolated target and the counterfactual full render. No bbox proxy is used.
 target_mask=np.max(np.abs(images[2]-rgb),axis=2)<=12
 reference_mask=np.max(np.abs(images[1]-rgb),axis=2)<=12
 actual_mask=np.max(np.abs(images[0]-rgb),axis=2)<=12
 visible_without=target_mask & reference_mask;lost=visible_without & ~actual_mask
 count=int(lost.sum());total=int(visible_without.sum())
 overlay=np.full((*lost.shape,3),255,dtype=np.uint8);overlay[target_mask]=[210,210,210];overlay[lost]=[210,35,50];Image.fromarray(overlay).save(outdir/'lost-target-pixels.png')
 if sha(svg)!=before:raise RuntimeError('Original SVG changed during verification')
 return {'foreground_id':foreground_id,'target_id':target_id,'source_svg_sha256':before,'method':'same_canvas_actual_render_with_occluder_ablation_and_isolated_target','intersects':count>0,'lost_target_pixels':count,'target_pixels_without_occluder':total,'lost_target_fraction':count/total if total else None,'render_size_px':[images[0].shape[1],images[0].shape[0]],'rgb_tolerance':12,'painter_order_verified':True,'evidence':'Actual opaque rendering hides target-colored pixels present in the same-canvas verification render and isolated original target. Verification omission is diagnostic only; original source remains unchanged.','limits':['Only the named synthetic foreground/curve pair is tested.','Color-isolation requires an explicit unique target stroke and does not generalize to arbitrary transparency or image occlusion.','Zero detected lost pixels does not certify a clean figure, valid inset placement, or full visibility of unrelated evidence.']}
