import copy,hashlib,tempfile,unittest
from pathlib import Path
import safe_edit as s
from test_safe_edit import fixture,zipbytes
class ParagraphTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.source=self.root/'source.pptx';self.output=self.root/'result.pptx';self.data=fixture()
 def plan(self):
  parts,_,_=s.package(self.data);p=s.xml(parts['ppt/slides/slide9.xml']).find('.//a:pPr',s.NS)
  return {'version':1,'source_sha256':hashlib.sha256(self.data).hexdigest(),'operations':[{'op':'paragraph_spacing','slide':1,'shape_id':'2','old_text':'α² 中文','paragraph':0,'old_spacing_xml':s.spacing_xml(p),'line_pt':14,'before_pt':0,'after_pt':3.5}]}
 def run_edit(self,plan=None):
  self.source.write_bytes(self.data);p=plan or self.plan();s.execute(self.source,p,self.output,True);s.validate(self.data,self.output.read_bytes(),p);return s.package(self.output.read_bytes())[0]
 def test_actual_spacing_write_preserves_text_payload_and_shape(self):
  parts=self.run_edit();root=s.xml(parts['ppt/slides/slide9.xml']);self.assertEqual(root.find('.//a:lnSpc/a:spcPts',s.NS).get('val'),'1400');self.assertEqual(root.find('.//a:spcAft/a:spcPts',s.NS).get('val'),'350');self.assertEqual(parts['ppt/embeddings/oleObject1.bin'],b'OPAQUE\x00\xff payload');self.assertEqual(self.source.read_bytes(),self.data)
 def test_missing_properties_and_existing_percent_spacing(self):
  for variant in ('missing','percent'):
   with self.subTest(variant=variant):
    parts,_,_=s.package(fixture());old=b'<a:pPr><a:defRPr sz="1000"/></a:pPr>';new=b'' if variant=='missing' else b'<a:pPr marL="1"><a:lnSpc><a:spcPct val="120000"/></a:lnSpc><a:spcAft><a:spcPts val="500"/></a:spcAft><a:defRPr sz="1000"/></a:pPr>';parts['ppt/slides/slide9.xml']=parts['ppt/slides/slide9.xml'].replace(old,new);self.data=zipbytes(parts);self.run_edit();self.output.unlink()
 def test_bad_spacing_or_stale_old_value_rejected(self):
  for key,value in [('line_pt',0),('line_pt',True),('before_pt',-1),('after_pt',float('nan')),('paragraph',True),('old_spacing_xml',{})]:
   p=self.plan();p['operations'][0][key]=value;self.source.write_bytes(self.data)
   with self.assertRaises(ValueError):s.execute(self.source,p,self.output,True)
   self.assertFalse(self.output.exists())
 def test_tampering_other_paragraph_properties_rejected(self):
  p=self.plan();parts=self.run_edit(p);parts['ppt/slides/slide9.xml']=parts['ppt/slides/slide9.xml'].replace(b'sz="1000"',b'sz="1001"')
  with self.assertRaises(ValueError):s.validate(self.data,zipbytes(parts),p)
 def test_invalid_output_child_order_rejected(self):
  p=self.plan();parts=self.run_edit(p);root=s.xml(parts['ppt/slides/slide9.xml']);props=root.find('.//a:pPr',s.NS);node=props.find('a:lnSpc',s.NS);props.remove(node);props.append(node);parts['ppt/slides/slide9.xml']=s.E.tostring(root)
  with self.assertRaises(ValueError):s.validate(self.data,zipbytes(parts),p)
 def test_font_and_spacing_same_text_work_together(self):
  p=self.plan();p['operations'].append({'op':'font','slide':1,'shape_id':'2','old_text':'α² 中文','run':0,'old_run_text':'α² 中文','size_pt':12,'fonts':{'latin':'Calibri'}});parts=self.run_edit(p);self.assertIn(b'typeface="Calibri"',parts['ppt/slides/slide9.xml'])
if __name__=='__main__':unittest.main()
