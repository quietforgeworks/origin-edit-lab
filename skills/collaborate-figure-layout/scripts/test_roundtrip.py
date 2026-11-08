import sys,tempfile,json,zipfile,copy,unittest
from pathlib import Path
from xml.etree import ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parent));import layout_boxes as l
class Roundtrip(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.source=self.root/'original.pptx';self.source.write_bytes(b'synthetic-source-only-fixture');self.inventory=self.root/'inventory.json'
  self.inventory.write_text(json.dumps({'assets':[{'id':f'a{i}','name':f'Figure {i+1}','source':{'kind':'pptx-native','fileName':'original.pptx','fileHash':l.fhash(self.source),'slidePart':'ppt/slides/slide1.xml','shapeId':str(i+1)}} for i in range(12)]}))
  self.spec=self.root/'spec.json';self.spec.write_text(json.dumps({'panels':[{'id':f'F{i+1:02d}','name':f'Figure {i+1}','sourceAssetIds':[f'a{i}']} for i in range(12)]}));self.deck=self.root/'draft.pptx';self.binding=self.root/'binding.json';l.create(self.inventory,self.deck,self.binding,self.spec)
 def tearDown(self):self.tmp.cleanup()
 def edit(self,fn):
  with zipfile.ZipFile(self.deck) as z:d={n:z.read(n) for n in z.namelist()}
  root=l.parse_xml(d['ppt/slides/slide1.xml']);fn(root.find('p:cSld/p:spTree',l.NS));d['ppt/slides/slide1.xml']=l.xbytes(root);out=self.root/'returned.pptx'
  with zipfile.ZipFile(out,'w') as z:
   for n,b in d.items():z.writestr(n,b)
  return out
 def read(self,p):
  out=self.root/'read.json';l.read_layout(p,self.binding,out,[self.source]);return json.loads(out.read_text())
 def test_plain_roundtrip(self):
  r=self.read(self.deck);self.assertEqual(len(r['selectedPanels']),12);self.assertTrue(r['originalSourceVerified']);self.assertEqual(r['omittedPanelIds'],[])
 def test_move_resize_delete(self):
  def edit(t):
   shapes=t.findall('p:sp',l.NS);xf=shapes[1].find('p:spPr/a:xfrm',l.NS);xf.find('a:off',l.NS).set('x',str(20*l.EMU));xf.find('a:ext',l.NS).set('cx',str(90*l.EMU));t.remove(shapes[-1])
  r=self.read(self.edit(edit));self.assertEqual(r['selectedPanels'][0]['bounds']['x'],20);self.assertEqual(r['selectedPanels'][0]['bounds']['w'],90);self.assertEqual(r['omittedPanelIds'],['F12'])
 def test_duplicate_rejected(self):
  with self.assertRaisesRegex(ValueError,'Duplicate panel'):self.read(self.edit(lambda t:t.append(copy.deepcopy(t.findall('p:sp',l.NS)[1]))))
 def test_rotation_rejected(self):
  def edit(t):t.findall('p:sp',l.NS)[1].find('p:spPr/a:xfrm',l.NS).set('rot','5400000')
  with self.assertRaisesRegex(ValueError,'Rotated'):self.read(self.edit(edit))
 def test_group_translation(self):
  def edit(t):
   s=t.findall('p:sp',l.NS)[1];t.remove(s);g=ET.SubElement(t,l.tag('p:grpSp'));nv=l.sub(g,'p:nvGrpSpPr');l.sub(nv,'p:cNvPr',{'id':100,'name':'group'});l.sub(nv,'p:cNvGrpSpPr');l.sub(nv,'p:nvPr');xf=l.sub(l.sub(g,'p:grpSpPr'),'a:xfrm');l.sub(xf,'a:off',{'x':10*l.EMU,'y':5*l.EMU});l.sub(xf,'a:ext',{'cx':280*l.EMU,'cy':200*l.EMU});l.sub(xf,'a:chOff',{'x':0,'y':0});l.sub(xf,'a:chExt',{'cx':280*l.EMU,'cy':200*l.EMU});g.append(s)
  r=self.read(self.edit(edit));p=next(p for p in r['selectedPanels'] if p['id']=='F01');self.assertEqual(p['bounds']['x'],22);self.assertEqual(p['bounds']['y'],31)
 def test_nonfinite_box_rejected(self):
  def edit(t):t.findall('p:sp',l.NS)[1].find('p:spPr/a:xfrm/a:off',l.NS).set('x','NaN')
  with self.assertRaisesRegex(ValueError,'Non-finite'):self.read(self.edit(edit))
 def test_curated_spec_required(self):
  with self.assertRaisesRegex(ValueError,'assistant-curated'):l.create(self.inventory,self.root/'new.pptx',self.root/'new-binding.json')
 def test_binding_tamper_rejected(self):
  m=json.loads(self.binding.read_text());m['panels'][0]['sourceBindings'][0]['shapeId']='999';self.binding.write_text(json.dumps(m))
  with self.assertRaisesRegex(ValueError,'manifest changed'):self.read(self.deck)
 def test_source_mismatch_not_approved(self):
  self.source.write_bytes(b'changed');r=self.read(self.deck);self.assertFalse(r['originalSourceVerified']);self.assertEqual(len(r['missingSourceHashes']),1)
 def test_overwrite_refused(self):
  with self.assertRaisesRegex(ValueError,'Output already'):l.create(self.inventory,self.deck,self.binding,self.spec)
 def test_unmapped_new_shape_reported(self):
  r=self.read(self.edit(lambda t:t.append(l.text_shape(100,'New shape','new',20,20,20,20))));self.assertEqual(r['warnings'][0]['type'],'unmapped-shape')
 def test_lost_name_retains_description(self):
  def edit(t):t.findall('p:sp',l.NS)[1].find('p:nvSpPr/p:cNvPr',l.NS).set('name','Rectangle 5')
  r=self.read(self.edit(edit));self.assertEqual(len(r['selectedPanels']),12)
 def test_lost_both_markers_not_guessed(self):
  def edit(t):
   c=t.findall('p:sp',l.NS)[1].find('p:nvSpPr/p:cNvPr',l.NS);c.set('name','Rectangle 5');c.attrib.pop('descr')
  r=self.read(self.edit(edit));self.assertEqual(r['omittedPanelIds'],['F01']);self.assertEqual(r['warnings'][0]['type'],'unmapped-shape')
if __name__=='__main__':unittest.main()
