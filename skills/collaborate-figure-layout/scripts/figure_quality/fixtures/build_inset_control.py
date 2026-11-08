# SPDX-License-Identifier: MIT
"""Build a separate clean-placement control; never replace locked cases."""
from pathlib import Path
import argparse,json
import generate_cases as gen
from painted_occlusion import measure

def build(out):
 out=Path(out)
 if out.exists():raise FileExistsError('Use a new output directory; preserve existing review artifacts.')
 out.mkdir(parents=True)
 (out/'LICENSE.txt').write_text((Path(gen.__file__).resolve().parents[3]/'references'/'figure-quality-license.txt').read_text())
 source,candidate,_=gen.line_case();candidate.transform('inset',[1,0,0,1,0,88])
 source.save(out/'source-occluded.svg');candidate.save(out/'candidate-clear.svg')
 gen.render(out/'source-occluded.svg',out/'source-occluded.png');gen.render(out/'candidate-clear.svg',out/'candidate-clear.png')
 original=measure(out/'source-occluded.svg','inset','p1_curve',out/'source-evidence')
 clean=measure(out/'candidate-clear.svg','inset','p1_curve',out/'candidate-evidence')
 candidate.collision_pairs=[('inset','p1_curve'),('inset','p1_frame')]
 complete_group_masks=gen.measure_collisions(candidate,out)
 source_nodes={e.get('id'):e for e in source.root.iter() if e.get('id')};candidate_nodes={e.get('id'):e for e in candidate.root.iter() if e.get('id')}
 if source_nodes.keys()!=candidate_nodes.keys():raise AssertionError('All semantic node IDs must remain')
 changes=[]
 for id,e in source_nodes.items():
  other=candidate_nodes[id]
  if e.attrib!=other.attrib:changes.append(id)
  if e.text!=other.text:raise AssertionError('All source text must remain exact')
 if changes!=['inset']:raise AssertionError('Only the complete inset group transform may change')
 if source.data!=candidate.data:raise AssertionError('No source data may change')
 report={'synthetic':True,'license':'MIT','purpose':'Independent control, not a replacement or cherry-picked rerun of the locked 12-case evaluation.','change':{'id':'inset','field':'transform','old':None,'new':[1,0,0,1,0,88],'scope':'Translate the complete bound inset group into the lower-right free region; do not delete inset, labels, or data.'},'source_occlusion':original,'candidate_occlusion':clean,'complete_inset_vs_curve_and_frame_masks':complete_group_masks,'inset_descendant_ids':[e.get('id') for e in candidate.get('inset').iter() if e.get('id')],'source_data_unchanged':True,'all_text_and_ids_preserved':True,'changed_attribute_owners':changes,'visual_acceptance':'Requires actual full-render review in addition to this pair-specific mask evidence.'}
 gen.jdump(out/'control-report.json',report);gen.jdump(out/'source-data.json',source.data);return report

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args();r=build(a.output);print(json.dumps({'source_lost_pixels':r['source_occlusion']['lost_target_pixels'],'candidate_lost_pixels':r['candidate_occlusion']['lost_target_pixels']}))
