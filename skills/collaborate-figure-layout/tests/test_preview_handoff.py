import base64,copy,io,unittest,struct,zlib
from PIL import Image
import test_local_handoff as fixtures
class PreviewHandoff(unittest.TestCase):
 def setUp(self):
  f=fixtures.HandoffTests();f.setUp();self.addCleanup(f.doCleanups);self.s=f.store
  b=io.BytesIO();Image.new('RGB',(8,8),'red').save(b,format='PNG');self.png=base64.b64encode(b.getvalue()).decode()
  self.k=self.s.lock_action({'action':'acquire','revision':0})['lock']['id']
  self.req={'projectId':self.s.source['projectId'],'mapHash':self.s.source['mapHash'],'revision':0,'lockId':self.k,'previews':{'p1':self.png}}
 def test_update_preserves_layout_source_and_invalidates_confirmation(self):
  source=copy.deepcopy(self.s.source);layout=copy.deepcopy(self.s.doc['layout'])
  result=self.s.update_previews(self.req);self.assertEqual(result['revision'],1);self.assertEqual(self.s.source,source);self.assertEqual(self.s.doc['layout'],layout);self.assertIsNone(self.s.doc['confirmation'])
  self.s.lock_action({'action':'release','lockId':self.k});self.s.commit(layout,1,'user');self.assertIn('p1',self.s.doc['displayPreviews'])
 def test_wrong_lock_and_stale_revision(self):
  for key,value,error in [('lockId','bad',PermissionError),('revision',99,RuntimeError),('mapHash','bad',ValueError),('projectId','bad',ValueError)]:
   req=copy.deepcopy(self.req);req[key]=value
   with self.assertRaises(error):self.s.update_previews(req)
   self.assertEqual(self.s.doc['revision'],0)
 def test_unknown_target_and_bad_png(self):
  for previews in ({'unknown':self.png},{'p1':'not base64'},{'p1':base64.b64encode(b'<svg/>').decode()},{'p1':self.png[:-4]},{}):
   req=copy.deepcopy(self.req);req['previews']=previews
   with self.assertRaises(ValueError):self.s.update_previews(req)
   self.assertEqual(self.s.doc['revision'],0)
 def test_crc_valid_but_undecodable_png_rejected(self):
  def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
  data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))+chunk(b'IDAT',b'not a zlib stream')+chunk(b'IEND',b'')
  self.req['previews']={'p1':base64.b64encode(data).decode()}
  with self.assertRaises(ValueError):self.s.update_previews(self.req)
  self.assertEqual(self.s.doc['revision'],0)
 def test_cancelled_work_cannot_publish(self):
  self.s.lock_action({'action':'cancel'})
  with self.assertRaises(PermissionError):self.s.update_previews(self.req)
if __name__=='__main__':unittest.main()
