#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Behavioral corpus invariants, not a scientific-figure aesthetic score.
Run generate_cases.py first, or run this file with --generate <fresh-output>.
"""
import argparse,base64,hashlib,json,math,os,re,tempfile,unittest
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
import generate_cases as gen

ROOT=Path(os.environ.get('FIGURE_CORPUS_DIR',str(Path(__file__).parent/'generated')))
def read(n,file='observations.json'):return json.loads((ROOT/'cases'/f'case-{n:02d}'/file).read_text())
def elems(n):return {r['id']:r for r in read(n)['elements']}
def xml(n,which='candidate'):return ET.parse(ROOT/'cases'/f'case-{n:02d}'/(which+'.svg')).getroot()
def node(n,id,which='candidate'):return xml(n,which).find('.//*[@id="'+id+'"]')

class ScientificFixtureTests(unittest.TestCase):
 def test_refuse_existing_generation_directory(self):
  with tempfile.TemporaryDirectory() as temp:
   destination=Path(temp)/'existing';destination.mkdir();sentinel=destination/'keep.txt';sentinel.write_text('preserve')
   with self.assertRaises(FileExistsError):gen.generate(destination)
   self.assertEqual(sentinel.read_text(),'preserve');self.assertEqual(list(destination.iterdir()),[sentinel])
 def test_generated_provenance_uses_project_mit(self):
  self.assertIn('Copyright (c) 2026 quietforgeworks',(ROOT/'LICENSE.txt').read_text())
  for n in range(1,13):
   provenance=read(n,'provenance.json');self.assertEqual(provenance['license'],'MIT');self.assertEqual(provenance['copyright'],'Copyright (c) 2026 quietforgeworks')
   self.assertTrue(provenance['synthetic']);self.assertTrue(provenance['no_private_material']);self.assertTrue(provenance['no_measured_data'])
 def test_all_12_reproducible_original_scenes(self):
  self.assertEqual(len(gen.CASES),12)
  for make in gen.CASES:
   a,b,_=make();aa,bb,_=make()
   self.assertEqual(ET.tostring(a.root),ET.tostring(aa.root));self.assertEqual(ET.tostring(b.root),ET.tostring(bb.root))
   self.assertEqual(a.data,aa.data)
 def test_fixed_canvas_hashes_and_actual_nonblank_renders(self):
  for n in range(1,13):
   d=ROOT/'cases'/f'case-{n:02d}';o=read(n)
   for w in ['source','candidate']:
    self.assertEqual(gen.sha(d/(w+'.svg')),o[w+'_sha256'])
    im=Image.open(d/(w+'.png'));self.assertEqual(im.size,(1440,840));a=np.array(im.convert('RGB'));self.assertGreater(np.count_nonzero(np.min(a,axis=2)<220),10000)
   self.assertAlmostEqual(o['canvas']['width_pt'],180/25.4*72)
 def test_own_source_arrays_not_measurements_and_data_change_is_localized(self):
  for n in range(1,13):
   source=read(n,'source-data.json');candidate=read(n,'candidate-data.json')
   if n==12:
    changed=[k for k in source if source[k]!=candidate[k]];self.assertEqual(changed,['series_q']);a=np.array(source['series_q']['y']);b=np.array(candidate['series_q']['y']);self.assertEqual(np.where(a!=b)[0].tolist(),list(range(28,36)))
   else:self.assertEqual(source,candidate)
 def test_svg_remains_editable_and_image_payload_intact(self):
  for n in range(1,13):
   root=xml(n);self.assertGreater(len(root.findall('.//{'+gen.NS+'}text')),3)
   self.assertGreaterEqual(len(root.findall('.//*[@id]')),10)
   self.assertFalse(root.findall('.//{'+gen.NS+'}script'))
  for n in [9,10]:
   a=node(n,'texture_image','source').get('href');b=node(n,'texture_image').get('href');self.assertEqual(a,b)
   blob=base64.b64decode(a.split(',',1)[1]);self.assertEqual(Image.open(__import__('io').BytesIO(blob)).size,(330,220))
 def test_log_mapping_keeps_geometric_ticks_and_inset(self):
  xs=[float(node(1,'p1_xtick'+str(i)).get('x1')) for i in range(4)]
  np.testing.assert_allclose(np.diff(xs),[185,185,185],rtol=0,atol=1e-5)
  self.assertIsNotNone(node(1,'inset_curve'));self.assertIsNotNone(node(1,'inset_xlabel'))
  p=read(1,'source-data.json')['p1_curve'];d=node(1,'p1_curve').get('d');xy=np.array([[float(a),float(b)] for a,b in re.findall(r'([\d.e+-]+),([\d.e+-]+)',d)])
  np.testing.assert_allclose(xy[:,0],75+np.log10(np.array(p['x'])/.1)/3*555,atol=.001)
  np.testing.assert_allclose(xy[:,1],350-np.log10(np.array(p['y'])/.1)/2*270,atol=.001)
 def test_raster_masks_verify_real_overlap_not_rectangles(self):
  for n in [2,4,6]:
   checks=read(n)['collision_checks'];self.assertTrue(checks)
   for c in checks:self.assertEqual(c['method'],'rendered_mask');self.assertTrue(c['intersects'],(n,c))
  self.assertFalse(read(1)['collision_checks'])
  c=read(1,'scene-observations.json')['painted_occlusion_measurements'][0];self.assertTrue(c['intersects']);self.assertGreater(c['lost_target_fraction'],.1)
 def test_clipping_and_letter_ownership_observable(self):
  e=elems(2)['p2_xlabel'];self.assertGreater(e['bbox'][0]+e['bbox'][2],1.05)
  p=elems(4);label=p['p2_letter'];self.assertEqual(label['ownership']['frame_id'],'p2_frame')
  own=p['p2_frame']['bbox'][0];self.assertGreater((own-(label['bbox'][0]+label['bbox'][2]))*read(4)['canvas']['width_pt'],25)
 def test_explicit_both_edges_and_baseline_not_ink_top(self):
  o=read(3);a={r['id']:r for r in o['anchors']};checks={r['id']:r for r in o['alignment_checks']}
  self.assertIn('peer_left',checks);self.assertIn('peer_right',checks)
  left=[a[i]['position_pt'] for i in checks['peer_left']['anchor_ids']];right=[a[i]['position_pt'] for i in checks['peer_right']['anchor_ids']]
  self.assertLess(max(left)-min(left),.1);self.assertGreater(max(right)-min(right),30)
  c=checks['p1_letter_attachment'];p=[a[x]['position_pt'] for x in c['anchor_ids']];self.assertGreater(abs((p[1]-p[0])-c['target_offsets_pt'][1]),2)
  self.assertEqual(a['p1_letter_baseline']['basis'],'baseline')
 def test_dense_pulses_not_simplified_or_erased(self):
  d=read(5,'source-data.json')['dense_pulses'];y=np.array(d['y']);local=(y[1:-1]>y[:-2])&(y[1:-1]>y[2:])&(y[1:-1]>.5)
  self.assertGreater(np.count_nonzero(local),55);self.assertEqual(len(d['x']),2600)
  self.assertEqual(node(5,'dense_pulses','source').get('d'),node(5,'dense_pulses').get('d'))
  self.assertEqual(node(5,'dense_pulses').get('d').count('L'),2599)
 def test_dual_axes_are_distinct_not_deletable_decoration(self):
  raw=read(7,'scene-observations.json');p=next(x for x in raw['elements'] if x['id']=='p1');self.assertEqual(p['axis_spec']['axis_count'],3)
  self.assertEqual(node(7,'right_ylabel').text,'Response B (%)');self.assertEqual(node(7,'p1_ylabel').text,'Response A (a.u.)')
  self.assertEqual(read(7,'source-data.json'),read(7,'candidate-data.json'))
 def test_nested_transform_and_optical_glyph_sizes(self):
  e=elems(8);m=e['p2_xticklabel1']['transform']['matrix'];self.assertAlmostEqual(m[0],1.026);self.assertAlmostEqual(m[3],.7776)
  a=e['p1_sample']['glyph']['ink_height_pt'];b=e['p2_sample']['glyph']['ink_height_pt'];self.assertLess(b/a,.8)
  self.assertEqual(node(8,'p1_sample').get('font-size'),node(8,'p2_sample').get('font-size'))
  self.assertEqual(e['p2_sample']['glyph']['method'],'rendered_mask')
 def test_physical_aspect_and_scale_bar_independent_checks(self):
  clean=elems(9);bad=elems(10)
  self.assertAlmostEqual(clean['texture_image']['scientific_ratio']['source'],clean['texture_image']['scientific_ratio']['final'])
  r=bad['texture_image']['scientific_ratio'];self.assertGreater(abs(r['final']/r['source']-1),.4)
  sb=bad['scale_bar']['scale_bar'];self.assertGreater(sb['final_fraction']/sb['source_fraction'],1.2);self.assertEqual(sb['final_value'],10)
 def test_schematic_body_change_preserves_labels_and_topology(self):
  self.assertNotEqual(node(11,'body1','source').get('height'),node(11,'body1').get('height'))
  for id in ['body_label1','body_label2','body_label3','connector0','connector1']:
   a=node(11,id,'source');b=node(11,id);self.assertEqual(ET.tostring(a),ET.tostring(b))
  image_roles=[e for e in read(11)['elements'] if e['kind']=='image'];self.assertFalse(image_roles)
 def test_exact_fingerprints_find_data_and_unit_mutation(self):
  e=elems(12)
  for id,kind in [('series_q','data'),('p1_xlabel','text')]:
   f=e[id]['fingerprints'][0];self.assertEqual(f['kind'],kind);self.assertNotEqual(f['before'],f['after'])
  f=e['series_r']['fingerprints'][0];self.assertEqual(f['before'],f['after'])
 def test_complete_selection_includes_inset_and_external_letter(self):
  o=read(1);p=next(x for x in o['selection_checks'] if x['owner_id']=='p1')
  self.assertIn('inset_curve',p['expected_ids']);self.assertIn('p1_letter',p['expected_ids']);self.assertEqual(p['expected_ids'],p['selected_ids'])
  for n in range(1,13):
   ids=[e['id'] for e in read(n)['elements']];self.assertEqual(len(ids),len(set(ids)))
   for e in read(n)['elements']:
    self.assertTrue(e['source_present']);self.assertTrue(e['present']);self.assertIsNotNone(e['bbox'])
    if e['parent_id']:self.assertIn(e['parent_id'],ids)
 def test_ground_truth_separate_from_blind_case_inputs(self):
  self.assertTrue((ROOT/'private-ground-truth'/'manifest.json').is_file())
  for p in (ROOT/'cases').rglob('*.json'):
   obj=json.loads(p.read_text());self.assertNotIn('expected_issues',obj)
  self.assertFalse(any((ROOT/'cases').rglob('*.py')))
 def test_microscopy_panel_metadata_matches_actual_source_image_placement(self):
  for n in [9,10]:
   raw=read(n,'scene-observations.json');panel=next(p for p in raw['panels'] if p['owner']=='p1');im=node(n,'texture_image','source')
   self.assertEqual(panel['box_coordinate_space'],'source_local_viewbox')
   self.assertEqual(panel['box'],[float(im.get(k)) for k in ['x','y','width','height']])
   e=next(e for e in raw['elements'] if e['id']=='texture_image');self.assertAlmostEqual(e['source_bbox'][1],float(im.get('y'))/420,places=5)
 def test_source_equality_does_not_exempt_actual_nontext_occlusion(self):
  self.assertEqual(node(1,'p1_curve','source').get('d'),node(1,'p1_curve').get('d'))
  self.assertEqual(ET.tostring(node(1,'inset','source')),ET.tostring(node(1,'inset')))
  check=read(1,'scene-observations.json')['painted_occlusion_measurements'][0]
  self.assertTrue(check['painter_order_verified']);self.assertGreater(check['lost_target_pixels'],300)
  self.assertEqual(check['source_svg_sha256'],read(1)['candidate_sha256'])
 def test_occlusion_detector_is_pair_specific_and_does_not_infer_quality(self):
  from painted_occlusion import measure
  source,_,_=gen.line_case();source.transform('inset',[1,0,0,1,-350,200])
  with tempfile.TemporaryDirectory() as tmp:
   tmp=Path(tmp);source.save(tmp/'diagnostic-control.svg');h=gen.sha(tmp/'diagnostic-control.svg');c=measure(tmp/'diagnostic-control.svg','inset','p1_curve',tmp/'evidence')
   self.assertEqual(c['lost_target_pixels'],0);self.assertEqual(gen.sha(tmp/'diagnostic-control.svg'),h)
   self.assertTrue(c['limits'])

 def test_clean_inset_control_preserves_all_members_and_clears_curve_and_frame(self):
  from build_inset_control import build
  with tempfile.TemporaryDirectory() as tmp:
   report=build(Path(tmp)/'fresh-control')
   self.assertEqual(report['changed_attribute_owners'],['inset'])
   self.assertEqual(report['candidate_occlusion']['lost_target_pixels'],0)
   self.assertGreater(report['source_occlusion']['lost_target_pixels'],300)
   self.assertTrue(report['source_data_unchanged']);self.assertTrue(report['all_text_and_ids_preserved'])
   for c in report['complete_inset_vs_curve_and_frame_masks']:self.assertFalse(c['intersects'],c)
   for id in ['inset_frame','inset_curve','inset_xlabel','inset_ylabel','inset_xtick0','inset_ytick0']:self.assertIn(id,report['inset_descendant_ids'])

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--generate',type=Path);args,rest=p.parse_known_args()
 if args.generate:ROOT=args.generate;gen.generate(ROOT)
 unittest.main(argv=[__file__]+rest)
