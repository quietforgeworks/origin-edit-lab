import copy,json,tempfile,unittest,struct,zlib
from pathlib import Path
import layout_boxes as lb
import read_web_layout as web
import prepare_web_project as prep

class BrowserReturn(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.source=self.root/'original.pptx';self.source.write_bytes(b'synthetic-source-bytes')
  inv={'assets':[{'id':'A','name':'Synthetic figure','source':{'kind':'pptx-native','fileHash':lb.fhash(self.source),'slidePart':'ppt/slides/slide1.xml','shapeId':'2'}}]}
  (self.root/'inventory.json').write_text(json.dumps(inv));(self.root/'panels.json').write_text(json.dumps({'panels':[{'id':'F01','name':'Synthetic figure','sourceAssetIds':['A']}]}))
  self.binding=self.root/'binding.json';lb.create(self.root/'inventory.json',self.root/'draft.pptx',self.binding,self.root/'panels.json')
  m=json.loads(self.binding.read_text());self.p={'schema':lb.FMT,'projectId':m['projectId'],'mapHash':m['mapHash'],'canvas':m['canvas'],'selectedPanels':[{'id':'F01','bounds':{'x':20,'y':30,'w':120,'h':25}}],'omittedPanelIds':[],'refinement':{'mode':'user-references','references':[]},'note':'Use the supplied palette as a proposal'}
 def read(self,p=None):
  path=self.root/'returned.json';path.write_text(json.dumps(self.p if p is None else p));out=self.root/'intent.json'
  web.read_layout(path,self.binding,out,[self.source]);return json.loads(out.read_text())
 def test_valid_rough_stretch_is_intent(self):
  r=self.read();self.assertEqual(r['selectedPanels'][0]['bounds']['w'],120);self.assertEqual(r['refinement']['mode'],'user-references');self.assertTrue(r['originalSourceVerified']);self.assertTrue(r['temporaryPreviewDistortionIsNotSourceTransform']);self.assertTrue(r['userChatApprovalStillRequired']);self.assertFalse(r['scientificSourceEdited'])
 def test_duplicate_id_rejected(self):
  self.p['selectedPanels'].append(copy.deepcopy(self.p['selectedPanels'][0]))
  with self.assertRaises(ValueError):self.read()
 def test_foreign_project_rejected(self):
  self.p['projectId']='foreign'
  with self.assertRaises(ValueError):self.read()
 def test_nonfinite_rejected(self):
  self.p['selectedPanels'][0]['bounds']['x']=float('nan')
  with self.assertRaises(ValueError):self.read()
 def test_source_mapping_substitution_rejected(self):
  self.p['selectedPanels'][0]['sourceBindings']=[{'fileHash':'f'*64}]
  with self.assertRaises(ValueError):self.read()
 def test_missing_selection_rejected(self):
  self.p['selectedPanels']=[]
  with self.assertRaises(ValueError):self.read()
 def test_omission_is_not_source_deletion(self):
  self.p['selectedPanels']=[];self.p['omittedPanelIds']=['F01'];r=self.read();self.assertEqual(r['omittedPanelIds'],['F01']);self.assertFalse(r['scientificSourceEdited']);self.assertTrue(self.source.exists())
 def test_browser_approval_cannot_authenticate(self):
  self.p['approved']=True;self.p['userChatApprovalStillRequired']=False;r=self.read();self.assertTrue(r['userChatApprovalStillRequired'])
 def test_prepare_minimal_page_preserves_private_mapping(self):
  def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
  png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\x00\xff\xff\xff'))+chunk(b'IEND',b'')
  image=self.root/'thumb.png';image.write_bytes(png);mapping=self.root/'previews.json';mapping.write_text(json.dumps({'F01':str(image)}))
  result=prep.prepare(self.binding,mapping,self.root/'page',self.root/'thumbnail-record.json')
  project=json.loads((self.root/'page/project.json').read_text());self.assertNotIn('inventoryPath',project);self.assertNotIn('sourceBindings',project['panels'][0]);self.assertTrue((self.root/'page/previews/F01.png').exists());self.assertFalse(result['hostingPerformed'])
  exported={**self.p,'selectedPanels':[{'id':'F01','bounds':project['panels'][0]['initialBounds']}]};r=self.read(exported);self.assertTrue(r['originalSourceVerified']);self.assertEqual(r['selectedPanels'][0]['sourceBindings'][0]['shapeId'],'2')
 def test_source_change_not_verified(self):
  self.source.write_bytes(b'changed');r=self.read();self.assertFalse(r['originalSourceVerified'])
 def test_no_source_paths_read_from_export(self):
  self.p['sourcePath']='/a/path/that/must/not/be/read';r=self.read();self.assertTrue(r['originalSourceVerified'])

if __name__=='__main__':unittest.main(verbosity=2)
