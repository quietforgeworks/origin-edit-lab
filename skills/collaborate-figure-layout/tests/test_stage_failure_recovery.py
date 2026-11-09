"""Stage transitions and failure recovery use generated synthetic projects only."""
import copy,unittest
import test_local_handoff as fixtures
server=fixtures.server
class StageRecoveryTests(unittest.TestCase):
 setUp=fixtures.HandoffTests.setUp
 def test_import_cannot_forge_proposal_readiness(self):
  s=self.store;l=copy.deepcopy(s.doc['layout']);l['guideWorkflow']={'mode':'auto','proposalReady':True};s.commit(l,0,'user')
  self.assertFalse(s.doc['layout']['guideWorkflow']['proposalReady'])
  with self.assertRaises(ValueError):s.confirm(1)
 def test_mode_change_requires_new_proposal(self):
  s=self.store;l=copy.deepcopy(s.doc['layout']);l['guideWorkflow']={'mode':'auto','proposalReady':True}
  k=s.lock_action({'action':'acquire','revision':0})['lock']['id'];s.commit(l,0,'assistant',k);s.lock_action({'action':'release','lockId':k})
  l['guideWorkflow']['mode']='constrained';s.commit(l,1,'user');self.assertFalse(s.doc['layout']['guideWorkflow']['proposalReady'])
  with self.assertRaises(ValueError):s.confirm(2)
 def test_user_guide_correction_can_still_confirm_existing_proposal(self):
  s=self.store;l=copy.deepcopy(s.doc['layout']);l['guideWorkflow']={'mode':'constrained','proposalReady':True}
  k=s.lock_action({'action':'acquire','revision':0})['lock']['id'];s.commit(l,0,'assistant',k);s.lock_action({'action':'release','lockId':k})
  l['guides']=[{'id':'g','axis':'x','pos':20,'color':'#189db7','kind':'frame','owner':'user','label':'frame','targets':['p1']}]
  s.commit(l,1,'user');self.assertTrue(s.doc['layout']['guideWorkflow']['proposalReady']);s.confirm(2)
 def test_empty_or_all_outside_cannot_confirm(self):
  s=self.store;l=copy.deepcopy(s.doc['layout']);l['guideWorkflow']={'mode':'complete','proposalReady':False}
  for p in l['selectedPanels']:p['bounds']['x']=-p['bounds']['w']
  s.commit(l,0,'user')
  with self.assertRaises(ValueError):s.confirm(1)
  l['omittedPanelIds']=[p['id'] for p in l['selectedPanels']];l['selectedPanels']=[];s.commit(l,1,'user')
  with self.assertRaises(ValueError):s.confirm(2)
 def test_restart_clears_lock_but_keeps_last_saved_revision(self):
  s=self.store;s.commit(s.doc['layout'],0,'user');k=s.lock_action({'action':'acquire','revision':1})['lock']['id']
  resumed=server.Store(s.root);self.assertEqual(resumed.doc,s.doc);self.assertIsNone(resumed.lock_status())
  with self.assertRaises(PermissionError):resumed.commit(resumed.doc['layout'],1,'assistant',k)
  resumed.commit(resumed.doc['layout'],1,'user')
 def test_revision_bool_is_rejected_at_lock(self):
  with self.assertRaises(RuntimeError):self.store.lock_action({'action':'acquire','revision':False})
if __name__=='__main__':unittest.main()
