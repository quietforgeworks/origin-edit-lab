import copy, hashlib, sys, tempfile, unittest, zipfile
from pathlib import Path
from lxml import etree as E
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import normalize_ole_display as m

class DisplayTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name)
 def fixture(self, divergence=False, mismatch=False, linked=False):
  xml=f'''<p:sld xmlns:p="{m.P}" xmlns:a="{m.A}" xmlns:r="{m.R}" xmlns:mc="{m.MC}"><p:cSld><p:spTree><p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="7" name="Synthetic plot"/></p:nvGraphicFramePr><p:xfrm><a:off x="1" y="2"/><a:ext cx="30" cy="40"/></p:xfrm><a:graphic><a:graphicData><mc:AlternateContent><mc:Choice xmlns:v="urn:schemas-microsoft-com:vml" Requires="v"><p:oleObj r:id="o1" progId="Origin95.Graph" imgW="100" imgH="200"><p:embed/></p:oleObj></mc:Choice><mc:Fallback><p:oleObj r:id="o1" progId="Origin95.Graph" imgW="100" imgH="200"><p:embed/><p:pic><p:blipFill><a:blip r:embed="i1"/></p:blipFill><p:spPr><a:xfrm><a:off x="1" y="2"/><a:ext cx="30" cy="40"/></a:xfrm></p:spPr></p:pic></p:oleObj></mc:Fallback></mc:AlternateContent></a:graphicData></a:graphic></p:graphicFrame></p:spTree></p:cSld></p:sld>'''
  root=E.fromstring(xml.encode())
  if divergence:root.find('.//mc:Choice/p:oleObj',m.NS).set('imgW','101')
  if mismatch:root.find('.//p:pic/p:spPr/a:xfrm/a:ext',m.NS).set('cx','31')
  rel=f'<Relationships><Relationship Id="o1" Type="{m.R}/oleObject" Target="../embeddings/synthetic.bin"/><Relationship Id="i1" Type="{m.R}/image" Target="../media/synthetic.png"'+(' TargetMode="External"' if linked else '')+'/></Relationships>'
  src=self.p/'source.pptx'
  with zipfile.ZipFile(src,'w') as z:
   for n,b in {'ppt/slides/slide1.xml':E.tostring(root),'ppt/slides/_rels/slide1.xml.rels':rel.encode(),'ppt/embeddings/synthetic.bin':b'SYNTHETIC-NOT-ORIGIN','ppt/media/synthetic.png':b'SYNTHETIC-NOT-PNG','unrelated.bin':b'untouched'}.items():z.writestr(n,b)
  return src
 def run_it(self,src,out='result.pptx',sha=None):return m.normalize(src,self.p/out,sha or hashlib.sha256(src.read_bytes()).hexdigest(),'ppt/slides/slide1.xml')
 def test_normalize_preserves_payload_relationship_and_metadata(self):
  src=self.fixture();r=self.run_it(src);self.assertEqual(r['normalized_objects'],1)
  with zipfile.ZipFile(src) as a,zipfile.ZipFile(self.p/'result.pptx') as b:
   root=E.fromstring(b.read('ppt/slides/slide1.xml'));self.assertEqual(len(root.findall('.//p:oleObj',m.NS)),1);self.assertEqual(root.findall('.//mc:AlternateContent',m.NS),[])
   for n in a.namelist():
    if n!='ppt/slides/slide1.xml':self.assertEqual(a.read(n),b.read(n))
   self.assertEqual(root.find('.//p:oleObj',m.NS).get('imgW'),'100')
  self.assertEqual(r['origin_activation'],'NOT_TESTED')
 def test_idempotent_direct_representation(self):
  self.run_it(self.fixture());r=self.run_it(self.p/'result.pptx','again.pptx');self.assertEqual(r['normalized_objects'],0);self.assertEqual(r['changed_parts'],[])
 def test_stale_hash_no_output(self):
  with self.assertRaises(ValueError):self.run_it(self.fixture(),sha='0'*64)
  self.assertFalse((self.p/'result.pptx').exists())
 def test_divergent_branch_no_output(self):
  with self.assertRaises(ValueError):self.run_it(self.fixture(divergence=True))
  self.assertFalse((self.p/'result.pptx').exists())
 def test_mismatched_dual_frames_no_output(self):
  with self.assertRaises(ValueError):self.run_it(self.fixture(mismatch=True))
  self.assertFalse((self.p/'result.pptx').exists())
 def test_external_image_no_output(self):
  with self.assertRaises(ValueError):self.run_it(self.fixture(linked=True))
  self.assertFalse((self.p/'result.pptx').exists())
 def test_no_overwrite(self):
  src=self.fixture();self.run_it(src)
  with self.assertRaises(ValueError):self.run_it(src)
 def mutate_fixture(self, fn):
  src=self.fixture()
  with zipfile.ZipFile(src) as z:parts={n:z.read(n) for n in z.namelist()}
  root=E.fromstring(parts['ppt/slides/slide1.xml']);fn(root);parts['ppt/slides/slide1.xml']=E.tostring(root)
  with zipfile.ZipFile(src,'w') as z:
   for n,b in parts.items():z.writestr(n,b)
  return src
 def test_transform_rotation_mismatch(self):
  src=self.mutate_fixture(lambda root:root.find('.//p:pic/p:spPr/a:xfrm',m.NS).set('rot','5400000'))
  with self.assertRaises(ValueError):self.run_it(src)
 def test_duplicate_fallback_rejected(self):
  def add(root):
   alt=root.find('.//mc:AlternateContent',m.NS);alt.append(copy.deepcopy(alt.find('mc:Fallback',m.NS)))
  with self.assertRaises(ValueError):self.run_it(self.mutate_fixture(add))
 def test_multiple_choice_previews_rejected(self):
  def add(root):
   choice=root.find('.//mc:Choice/p:oleObj',m.NS);pic=root.find('.//mc:Fallback/p:oleObj/p:pic',m.NS)
   choice.extend([copy.deepcopy(pic),copy.deepcopy(pic)])
  with self.assertRaises(ValueError):self.run_it(self.mutate_fixture(add))
 def test_unknown_branch_rejected(self):
  def add(root):E.SubElement(root.find('.//mc:AlternateContent',m.NS),'{urn:unknown}unsupported')
  with self.assertRaises(ValueError):self.run_it(self.mutate_fixture(add))
if __name__=='__main__':unittest.main()
