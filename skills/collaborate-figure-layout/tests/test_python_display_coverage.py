import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import python_display_coverage as c
class CoverageTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.base=Path(self.temp.name)
  self.inv={'schema':'figure-layout-inventory/v1','source':{'fileHash':'a'*64},'assets':[{'id':'a','source':{'slideNumber':1,'xmlPath':'/group','shapeType':'grpSp','kind':'pptx-group','structuralMembers':[{'xmlPath':'/group/text','shapeType':'sp'}]}}]};self.raw=json.dumps(self.inv).encode();self.plan=c.initialize(self.inv,self.raw,1)
 def test_host_only_edit_is_not_complete(self):
  r=c.check(self.inv,self.raw,self.plan,self.base);self.assertFalse(r['coverage_complete']);self.assertEqual(len(r['blockers']),2*len(c.FACETS))
 def test_missing_child_or_facet_rejected(self):
  p=copy.deepcopy(self.plan);p['objects'].pop()
  with self.assertRaises(ValueError):c.check(self.inv,self.raw,p,self.base)
  p=copy.deepcopy(self.plan);del p['objects'][0]['facets']['text_typography']
  with self.assertRaises(ValueError):c.check(self.inv,self.raw,p,self.base)
 def resolved(self):
  evidence=self.base/'synthetic-audit.txt';evidence.write_text('Synthetic recorded observation, not scientific evidence.')
  for obj in self.plan['objects']:
   for f in obj['facets'].values():f.update(status='verified-unchanged',reason='Synthetic test observation',evidence=[{'path':evidence.name,'sha256':c.sha(evidence.read_bytes())}])
 def test_complete_coverage_does_not_claim_render_or_activation(self):
  self.resolved();r=c.check(self.inv,self.raw,self.plan,self.base);self.assertTrue(r['coverage_complete']);self.assertFalse(r['visual_quality_verified']);self.assertFalse(r['origin_activation_verified'])
 def test_changed_evidence_and_source_rejected(self):
  self.resolved();(self.base/'synthetic-audit.txt').write_text('changed')
  with self.assertRaises(ValueError):c.check(self.inv,self.raw,self.plan,self.base)
  with self.assertRaises(ValueError):c.check(self.inv,self.raw+b' ',self.plan,self.base)
 def test_not_applicable_requires_observation(self):
  self.plan['objects'][0]['facets']['internal_plot_geometry']={'status':'not-applicable','reason':'','evidence':[]}
  with self.assertRaises(ValueError):c.check(self.inv,self.raw,self.plan,self.base)
if __name__=='__main__':unittest.main()
