import sys, unittest, tempfile, hashlib, copy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import safe_edit as s
from test_safe_edit import fixture, zipbytes
class Audit(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
  self.path=Path(self.tmp.name)/'source.pptx'
  self.op=dict(op='font',slide=1,shape_id='2',old_text='α² 中文',run=0,old_run_text='α² 中文',size_pt=12)
 def setup(self, change, inherited=False):
  parts,_,_=s.package(fixture(inherited=inherited)); change(parts)
  self.data=zipbytes(parts); self.path.write_bytes(self.data)
  self.plan=dict(version=1,source_sha256=hashlib.sha256(self.data).hexdigest(),operations=[self.op])
 def test_duplicate_txbody_rejected(self):
  def mutate(p):
   r=s.xml(p['ppt/slides/slide9.xml']); shape=r.find('.//p:sp',s.NS); shape.append(copy.deepcopy(shape.find('p:txBody',s.NS))); p['ppt/slides/slide9.xml']=s.E.tostring(r)
  self.setup(mutate)
  with self.assertRaises(ValueError): s.execute(self.path,self.plan)
 def test_duplicate_transform_rejected(self):
  def mutate(p):
   r=s.xml(p['ppt/slides/slide9.xml']); props=r.find('.//p:spPr',s.NS); props.append(copy.deepcopy(props.find('a:xfrm',s.NS))); p['ppt/slides/slide9.xml']=s.E.tostring(r)
  self.op=dict(op='translate',slide=1,shape_id='2',old_text='α² 中文',old_xfrm=dict(x='100',y='200',cx='300',cy='400',rot='0',flipH=None,flipV=None),dx_emu=1,dy_emu=2)
  self.setup(mutate)
  with self.assertRaises(ValueError): s.execute(self.path,self.plan)
 def test_duplicate_run_text_rejected(self):
  def mutate(p):
   r=s.xml(p['ppt/slides/slide9.xml']); run=r.find('.//a:r',s.NS); run.append(copy.deepcopy(run.find('a:t',s.NS))); p['ppt/slides/slide9.xml']=s.E.tostring(r)
  self.op['old_text']='α² 中文α² 中文'; self.setup(mutate)
  with self.assertRaises(ValueError): s.execute(self.path,self.plan)
 def test_scientific_payload_tamper_rejected(self):
  self.setup(lambda p: None); out=Path(self.tmp.name)/'out.pptx'; s.execute(self.path,self.plan,out,True)
  parts,_,_=s.package(out.read_bytes()); parts['ppt/embeddings/oleObject1.bin']+=b'!'
  with self.assertRaises(ValueError): s.validate(self.data,zipbytes(parts),self.plan)
 def test_new_run_properties_foreign_attr_rejected(self):
  self.setup(lambda p: None,True); out=Path(self.tmp.name)/'out.pptx'; s.execute(self.path,self.plan,out,True)
  parts,_,_=s.package(out.read_bytes()); parts['ppt/slides/slide9.xml']=parts['ppt/slides/slide9.xml'].replace(b'<a:rPr ',b'<a:rPr b="1" ')
  with self.assertRaises(ValueError): s.validate(self.data,zipbytes(parts),self.plan)
 def test_duplicate_shape_id_rejected(self):
  def mutate(p):
   r=s.xml(p['ppt/slides/slide9.xml']); tree=r.find('.//p:spTree',s.NS); tree.append(copy.deepcopy(tree.find('p:sp',s.NS))); p['ppt/slides/slide9.xml']=s.E.tostring(r)
  self.setup(mutate)
  with self.assertRaises(ValueError): s.execute(self.path,self.plan)
 def test_duplicate_slide_target_rejected(self):
  def mutate(p): p['ppt/_rels/presentation.xml.rels']=p['ppt/_rels/presentation.xml.rels'].replace(b'slide1.xml',b'slide9.xml')
  self.setup(mutate)
  with self.assertRaises(ValueError): s.execute(self.path,self.plan)
 def test_existing_symlink_not_overwritten(self):
  self.setup(lambda p:None); dest=Path(self.tmp.name)/'link.pptx'; dest.symlink_to(self.path)
  with self.assertRaises(ValueError): s.execute(self.path,self.plan,dest,True)
  self.assertEqual(self.path.read_bytes(),self.data)
 def test_dangling_symlink_not_created(self):
  self.setup(lambda p:None); dest=Path(self.tmp.name)/'link.pptx'; target=Path(self.tmp.name)/'absent.pptx'; dest.symlink_to(target)
  with self.assertRaises(FileExistsError): s.execute(self.path,self.plan,dest,True)
  self.assertFalse(target.exists())
 def test_signed_package_rejected(self):
  self.setup(lambda p:p.update({'_xmlsignatures/sig1.xml':b'<Signature/>'}))
  with self.assertRaises(ValueError): s.execute(self.path,self.plan)
 def test_xml_entities_rejected(self):
  def mutate(p): p['ppt/slides/slide9.xml']=b'<!DOCTYPE x [<!ENTITY ent "x">]>'+p['ppt/slides/slide9.xml']
  self.setup(mutate)
  with self.assertRaises(ValueError): s.execute(self.path,self.plan)
if __name__=='__main__':unittest.main()
