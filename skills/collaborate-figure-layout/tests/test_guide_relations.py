"""Behavioral tests of relationship-only guide handoff, not native rendering."""
import copy, importlib.util, json, unittest
from pathlib import Path
import test_local_handoff as fixtures
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('relation_projection', ROOT/'assets/local-handoff/guide_relations.py')
relations=importlib.util.module_from_spec(spec);spec.loader.exec_module(relations)

class RelationTests(unittest.TestCase):
 def setUp(self):
  f=fixtures.HandoffTests();f.setUp();self.addCleanup(f.doCleanups);self.fixture=f;self.store=f.store
  self.layout=copy.deepcopy(f.store.doc['layout'])
  self.layout['guides']=[{'id':'peers','axis':'x','pos':12,'color':'#189db7','kind':'frame','owner':'user','label':'p1 and p2 left frames','targets':['p1','p2']}]
  self.layout['guideWorkflow']={'mode':'complete','proposalReady':False}
 def test_drawing_position_color_owner_do_not_set_final_coordinate(self):
  first=relations.from_layout(self.layout);other=copy.deepcopy(self.layout)
  other['guides'][0].update(pos=90,color='#000000',owner='assistant')
  self.assertEqual(first,relations.from_layout(other))
  self.assertNotIn('"pos":',json.dumps(first));self.assertNotIn('coordinate_pt',json.dumps(first))
 def test_target_order_is_not_a_pin_but_relationship_changes_are_bound(self):
  first=relations.from_layout(self.layout);other=copy.deepcopy(self.layout);other['guides'][0]['targets'].reverse()
  self.assertEqual(first,relations.from_layout(other))
  for key,value in [('axis','y'),('kind','title'),('targets',['p2']),('label','align title baselines')]:
   other=copy.deepcopy(self.layout);other['guides'][0][key]=value
   self.assertNotEqual(first['guideIntentSha256'],relations.from_layout(other)['guideIntentSha256'])
 def test_no_single_or_unbound_hint_is_falsely_declared_source_resolved(self):
  for targets in [[],['p1'],['p1','p2']]:
   self.layout['guides'][0]['targets']=targets
   self.assertTrue(relations.from_layout(self.layout)['alignmentRelations'][0]['anchorBindingRequired'])
 def test_duplicate_or_unknown_target_rejected(self):
  for targets in [['p1','p1'],['unknown'],[True]]:
   self.layout['guides'][0]['targets']=targets
   with self.assertRaises(ValueError):relations.from_layout(self.layout)
 def test_confirmation_exposes_relations_not_drawable_positions(self):
  s=self.store;s.commit(self.layout,0,'user');d=s.confirm(1);i=d['refinementInput']
  self.assertNotIn('guides',i);self.assertEqual(i['guidePositionPolicy'],'display-only')
  self.assertEqual(i['panelGeometryPolicy'],'rough-composition-intent')
  self.assertEqual(i['alignmentRelations'][0]['targetPanelIds'],['p1','p2'])
  self.assertEqual(d['layout']['guides'][0]['pos'],12)
  self.assertEqual(d['confirmation']['guideIntentSha256'],relations.from_layout(d['layout'])['guideIntentSha256'])
 def test_explicit_absolute_mode_and_duplicate_targets_fail_closed(self):
  for edit in ['absolute','duplicate']:
   l=copy.deepcopy(self.layout)
   if edit=='absolute':l['guideSemantics']='absolute-coordinates'
   else:l['guides'][0]['targets']=['p1','p1']
   with self.assertRaises(ValueError):fixtures.server.valid(l,self.store.source)
 def test_reference_style_mode_survives_save_and_restart(self):
  self.layout['refinement']={'mode':'user-references','references':[]};self.store.commit(self.layout,0,'user')
  restarted=fixtures.server.Store(self.fixture.p/'out')
  self.assertEqual(restarted.doc['layout']['refinement']['mode'],'user-references')
 def test_legacy_projection_drops_coordinate_claims_and_does_not_mutate_state(self):
  old={'selectedPanels':copy.deepcopy(self.layout['selectedPanels']),'guides':copy.deepcopy(self.layout['guides']),'sourcePreserved':True,'targetCoordinates':{'p1':12}}
  saved=copy.deepcopy(old);result=relations.normalize_refinement_input(self.layout,old)
  self.assertEqual(old,saved);self.assertNotIn('guides',result);self.assertNotIn('targetCoordinates',result)
  self.assertEqual(result['guidePositionPolicy'],'display-only')
 def test_saved_relation_tampering_is_rejected(self):
  x=relations.from_layout(self.layout);x['alignmentRelations'][0]['axis']='y'
  with self.assertRaises(ValueError):relations.normalize_refinement_input(self.layout,x)
 def test_user_hint_drawing_is_protected_without_becoming_layout_pin(self):
  s=self.store;s.commit(self.layout,0,'user');k=s.lock_action({'action':'acquire','revision':1})['lock']['id']
  proposed=copy.deepcopy(s.doc['layout']);proposed['selectedPanels'][0]['bounds']['x']+=3
  out=s.commit(proposed,1,'assistant',k)
  self.assertEqual(out['layout']['guides'][0],self.layout['guides'][0])
  self.assertEqual(out['layout']['selectedPanels'][0]['bounds']['x'],self.layout['selectedPanels'][0]['bounds']['x']+3)
  self.assertEqual(relations.from_layout(out['layout']),relations.from_layout(self.layout))
if __name__=='__main__':unittest.main()
