import copy,hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import safe_edit as s
from test_safe_edit import fixture,zipbytes

class CharacterSpacingTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.source=Path(self.tmp.name)/'source.pptx';self.output=Path(self.tmp.name)/'output.pptx'
  self.data=fixture();self.source.write_bytes(self.data)
  self.op={'op':'font','slide':1,'shape_id':'2','old_text':'α² 中文','run':0,'old_run_text':'α² 中文','tracking_pt':0,'kerning_min_pt':8,'old_character_spacing':{'spc':None,'kern':None}}
 def plan(self,op=None):return {'version':1,'source_sha256':hashlib.sha256(self.data).hexdigest(),'operations':[copy.deepcopy(op or self.op)]}
 def test_applied_spacing_preserves_text_emphasis_scripts_and_payloads(self):
  op=dict(self.op,size_pt=12,fonts={'latin':'Calibri'});plan=self.plan(op);s.execute(self.source,plan,self.output,True)
  after,_,_=s.package(self.output.read_bytes());props=s.xml(after['ppt/slides/slide9.xml']).find('.//a:rPr',s.NS)
  self.assertEqual(props.get('spc'),'0');self.assertEqual(props.get('kern'),'800');self.assertEqual(props.get('baseline'),'30000');self.assertEqual(props.get('b'),'1');self.assertEqual(props.get('i'),'1')
  s.validate(self.data,self.output.read_bytes(),plan);self.assertEqual(self.source.read_bytes(),self.data)
 def test_missing_run_properties_are_supported(self):
  self.data=fixture(inherited=True);self.source.write_bytes(self.data);s.execute(self.source,self.plan(),self.output,True)
  s.validate(self.data,self.output.read_bytes(),self.plan())
 def test_stale_character_attributes_and_invalid_numbers_are_rejected(self):
  bad=copy.deepcopy(self.op);bad['old_character_spacing']['spc']='100'
  with self.assertRaises(ValueError):s.execute(self.source,self.plan(bad))
  for key,values in [('tracking_pt',[True,float('nan'),101,-21,.001]),('kerning_min_pt',[-1,401,False])]:
   for value in values:
    bad=copy.deepcopy(self.op);bad[key]=value
    with self.subTest(key=key,value=value),self.assertRaises(ValueError):s.execute(self.source,self.plan(bad))
 def test_unrequested_character_change_is_rejected_by_independent_validator(self):
  plan=self.plan();s.execute(self.source,plan,self.output,True);parts,_,_=s.package(self.output.read_bytes())
  root=s.xml(parts['ppt/slides/slide9.xml']);root.find('.//a:rPr',s.NS).set('kern','1000');parts['ppt/slides/slide9.xml']=s.E.tostring(root)
  with self.assertRaises(ValueError):s.validate(self.data,zipbytes(parts),plan)
 def test_only_requested_tracking_preserves_existing_kerning(self):
  parts,_,_=s.package(self.data);root=s.xml(parts['ppt/slides/slide9.xml']);root.find('.//a:rPr',s.NS).set('kern','1200');parts['ppt/slides/slide9.xml']=s.E.tostring(root)
  self.data=zipbytes(parts);self.source.write_bytes(self.data);op=copy.deepcopy(self.op);op.pop('kerning_min_pt');op['old_character_spacing']['kern']='1200'
  s.execute(self.source,self.plan(op),self.output,True);after,_,_=s.package(self.output.read_bytes());self.assertEqual(s.xml(after['ppt/slides/slide9.xml']).find('.//a:rPr',s.NS).get('kern'),'1200')
 def test_multiple_edits_parse_each_slide_once(self):
  parts,_,_=s.package(self.data);plan=self.plan();plan['operations'].append({'op':'paragraph_spacing','slide':1,'shape_id':'2','old_text':'α² 中文','paragraph':0,'old_spacing_xml':{'lnSpc':None,'spcBef':None,'spcAft':None},'line_pt':14})
  with patch.object(s,'xml',wraps=s.xml) as parse:s.resolve(parts,plan)
  self.assertEqual(parse.call_count,3) # presentation + relationships + one target slide
if __name__=='__main__':unittest.main()
