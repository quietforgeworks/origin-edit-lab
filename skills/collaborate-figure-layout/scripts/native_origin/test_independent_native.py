import sys, unittest, io, zipfile, struct, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_reviewed_patch import synthetic_cfb, plan_for
from reviewed_patch import patch_native, sha, PatchError, write_new
from ppt_contents_patch import patch_contents, patch_ppt
class Audit(unittest.TestCase):
 def ppt(self, extras={}):
  self.cfb,self.source=synthetic_cfb(); self.plan=plan_for(self.source); self.member='ppt/embeddings/oleObject1.bin'; b=io.BytesIO()
  with zipfile.ZipFile(b,'w') as z:
   z.writestr(self.member,self.cfb)
   for name,data in extras.items(): z.writestr(name,data)
  return b.getvalue()
 def test_signed_ppt_rejected(self):
  data=self.ppt({'_xmlsignatures/sig1.xml':b'<Signature/>'})
  with self.assertRaises(ValueError):patch_ppt(data,self.member,sha(data),sha(self.cfb),self.plan)
 def test_all_other_bytes_exact(self):
  cfb,src=synthetic_cfb(); out,_=patch_contents(cfb,sha(cfb),plan_for(src))
  self.assertEqual(len(out),len(cfb)); self.assertEqual([i for i in range(len(cfb)) if out[i]!=cfb[i]],[1553])
 def test_wrong_candidate_hash_rejected(self):
  cfb,src=synthetic_cfb(); plan=plan_for(src); plan['candidate_sha256']='a'*64
  with self.assertRaises(PatchError):patch_contents(cfb,sha(cfb),plan)
 def test_fat_self_cycle_rejected(self):
  cfb,src=synthetic_cfb(); data=bytearray(cfb); struct.pack_into('<I',data,1024+2*4,2)
  with self.assertRaises(ValueError):patch_contents(bytes(data),sha(data),plan_for(src))
 def test_other_stream_overlap_rejected(self):
  cfb,src=synthetic_cfb(); data=bytearray(cfb); struct.pack_into('<I',data,512+2*128+116,2)
  with self.assertRaises(ValueError):patch_contents(bytes(data),sha(data),plan_for(src))
 def test_symlink_output_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   dest=Path(t)/'out'; target=Path(t)/'absent'; dest.symlink_to(target)
   with self.assertRaises(FileExistsError):write_new(dest,b'new')
   self.assertFalse(target.exists())
if __name__=='__main__':unittest.main()
