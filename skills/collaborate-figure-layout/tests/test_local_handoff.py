import copy,hashlib,base64,importlib.util,json,re,sys,tempfile,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import prepare_local_handoff as build
import test_prepare_web_project as fixtures
spec=importlib.util.spec_from_file_location('handoff_server',ROOT/'assets/local-handoff/server.py')
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)

class HandoffTests(unittest.TestCase):
 def setUp(self):
  self.fixture=fixtures.PrepTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups);self.p=self.fixture.p
  build.build(self.p/'binding.json',self.p/'previews.json',self.p/'out',self.p/'record.json')
  self.store=server.Store(self.p/'out')
 def test_generated_page_private_binding_and_csp(self):
  html=(self.p/'out/index.html').read_text();self.assertNotIn('PRIVATE_SOURCE_SENTINEL',html);self.assertNotIn('__SOURCE_JSON__',html)
  scripts=re.findall(r'<script>(.*?)</script>',html,re.S);self.assertEqual(len(scripts),1)
  digest=base64.b64encode(hashlib.sha256(scripts[0].encode()).digest()).decode();self.assertIn("script-src 'sha256-"+digest+"'",html)
  self.assertFalse((self.p/'out/session.json').exists());self.assertNotIn('sourceBindings',(self.p/'out/source.json').read_text())
 def test_no_overwrite(self):
  with self.assertRaises(ValueError):build.build(self.p/'binding.json',self.p/'previews.json',self.p/'out',self.p/'other.json')
 def test_lock_write_and_expiration(self):
  s=self.store;l=copy.deepcopy(s.doc['layout']);lock=s.lock_action({'action':'acquire','revision':0})['lock']
  with self.assertRaises(PermissionError):s.commit(l,0,'user')
  with self.assertRaises(PermissionError):s.commit(l,0,'assistant','bad')
  with self.assertRaises(PermissionError):s.confirm(0)
  s.commit(l,0,'assistant',lock['id']);self.assertEqual(s.doc['revision'],1)
  with self.assertRaises(RuntimeError):s.commit(l,0,'assistant',lock['id'])
  s.work_lock['expiresAt']=time.time()-1;self.assertIsNone(s.lock_status())
  with self.assertRaises(PermissionError):s.commit(l,1,'assistant',lock['id'])
  s.commit(l,1,'user')
 def test_cancel_prevents_late_write(self):
  s=self.store;k=s.lock_action({'action':'acquire','revision':0})['lock']['id'];s.lock_action({'action':'cancel'})
  with self.assertRaises(PermissionError):s.commit(s.doc['layout'],0,'assistant',k)
 def test_user_guides_protected(self):
  s=self.store;l=copy.deepcopy(s.doc['layout']);g={'id':'g1','axis':'x','pos':50,'color':'#189db7','kind':'frame','owner':'user','label':'frame','targets':['p1']};l['guides']=[g];s.commit(l,0,'user')
  k=s.lock_action({'action':'acquire','revision':1})['lock']['id']
  l['guides'][0]['pos']=51
  with self.assertRaises(ValueError):s.commit(l,1,'assistant',k)
  l['guides']=[]
  with self.assertRaises(ValueError):s.commit(l,1,'assistant',k)
  self.assertEqual(s.doc['revision'],1)
 def test_user_correction_of_assistant_guide_becomes_protected(self):
  s=self.store;l=copy.deepcopy(s.doc['layout']);l['guides']=[{'id':'g1','axis':'x','pos':50,'color':'#189db7','kind':'frame','owner':'assistant','label':'frame','targets':['p1']}]
  k=s.lock_action({'action':'acquire','revision':0})['lock']['id'];s.commit(l,0,'assistant',k);s.lock_action({'action':'release','lockId':k})
  l['guides'][0]['pos']=51;s.commit(l,1,'user');self.assertEqual(s.doc['layout']['guides'][0]['owner'],'user')
  k=s.lock_action({'action':'acquire','revision':2})['lock']['id']
  with self.assertRaises(ValueError):s.commit(l,2,'assistant',k)
 def test_stage_proposal_confirmation_invalidation(self):
  s=self.store
  with self.assertRaises(ValueError):s.confirm(0)
  l=copy.deepcopy(s.doc['layout']);l['guideWorkflow']={'mode':'auto','proposalReady':False};s.commit(l,0,'user')
  with self.assertRaises(ValueError):s.confirm(1)
  k=s.lock_action({'action':'acquire','revision':1})['lock']['id'];l['guideWorkflow']['proposalReady']=True;s.commit(l,1,'assistant',k);s.lock_action({'action':'release','lockId':k})
  out=s.confirm(2);self.assertEqual(out['confirmation']['revision'],2);self.assertEqual(len(out['refinementInput']['selectedPanels']),2)
  s.commit(l,2,'user');self.assertIsNone(s.doc['confirmation'])
 def test_outside_exclusion_and_partial_rejection(self):
  s=self.store;l=copy.deepcopy(s.doc['layout']);l['guideWorkflow']={'mode':'complete','proposalReady':False};l['selectedPanels'][0]['bounds']['x']=-40;s.commit(l,0,'user')
  r=s.confirm(1);self.assertEqual(r['refinementInput']['excludedOutsidePanelIds'],['p1'])
  l['selectedPanels'][0]['bounds']['x']=-.001;s.commit(l,1,'user')
  with self.assertRaises(ValueError):s.confirm(2)
  self.assertIsNone(s.doc['confirmation'])
if __name__=='__main__':unittest.main()
