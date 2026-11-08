"""Synthetic CFB/PPT wrappers, restore anchors, no-follow I/O adversarial checks."""
from pathlib import Path
import copy,io,json,os,struct,subprocess,sys,tempfile,unittest,zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
import native_scalar_writer as n,native_container as c
from test_native_scalar_writer import fixture,SEL
from cfb_read import CompoundFile
FREE=0xffffffff;END=0xfffffffe;FAT=0xfffffffd

def cfb(data):
 values=[('Contents',data),('\x02OlePres000',b'UNCHANGED CACHE'+bytes(4096-15))]
 sizes=[(len(v)+511)//512 for _,v in values];total=2+sum(sizes);header=bytearray(512);header[:8]=bytes.fromhex('d0cf11e0a1b11ae1');struct.pack_into('<HHHHH',header,24,0x3e,3,0xfffe,9,6);struct.pack_into('<9I',header,40,0,1,1,0,4096,END,0,END,0);struct.pack_into('<109I',header,76,0,*([FREE]*108))
 fat=[FREE]*128;fat[0]=FAT;fat[1]=END;directory=bytearray(512)
 def entry(index,name,kind,start,size,left=FREE,right=FREE,child=FREE):
  pos=index*128;raw=(name+'\0').encode('utf-16le');directory[pos:pos+len(raw)]=raw;struct.pack_into('<HBBIII',directory,pos+64,len(raw),kind,1,left,right,child);struct.pack_into('<IQ',directory,pos+116,start,size)
 entry(0,'Root Entry',5,END,0,child=1);offset=2;parts=[]
 for i,((name,value),count) in enumerate(zip(values,sizes),1):
  entry(i,name,2,offset,len(value),right=i+1 if i<len(values) else FREE)
  for sid in range(offset,offset+count):fat[sid]=sid+1 if sid<offset+count-1 else END
  parts.append(value+bytes(count*512-len(value)));offset+=count
 return bytes(header)+struct.pack('<128I',*fat)+bytes(directory)+b''.join(parts)

def ppt(raw):
 mem=io.BytesIO()
 with zipfile.ZipFile(mem,'w',compression=zipfile.ZIP_DEFLATED) as z:
  for name,value in [('[Content_Types].xml',b'<Types/>'),('ppt/presentation.xml',b'<presentation/>'),('ppt/embeddings/oleObject1.bin',raw),('ppt/media/preview.emf',b'unchanged preview'),('notes.txt',b'other')]:z.writestr(name,value)
 return mem.getvalue()

def trial(kind='cfb',serial=False):
 data=fixture();sourcecfb=cfb(data);source=sourcecfb if kind=='cfb' else ppt(sourcecfb);current=data;plans=[]
 changes=[(SEL,1500)]
 if serial:changes += [({'page':'Synthetic','layer':1,'field':'annotation.font','annotation':'XB'},54),({'page':'Synthetic','layer':1,'field':'axis.tick_font','axis':'X','side':'near'},48),({'page':'Synthetic','layer':1,'field':'axis.line_width','axis':'X','side':'near'},1250)]
 for sel,new in changes:
  p=n.prepare(current,sel,new,expected_source_sha256=n.digest(current));current,_=n.apply(current,p,expected_source_sha256=n.digest(current),expected_plan_sha256=n.digest(n.canonical(p)));plans.append(p)
 r,m=c.patch(source,plans,kind=kind,part='ppt/embeddings/oleObject1.bin' if kind=='pptx' else None,expected_source_sha256=n.digest(source),expected_cfb_sha256=n.digest(sourcecfb),expected_native_sha256=n.digest(data),expected_bundle_sha256=n.digest(n.canonical(plans)))
 return source,r,m

class Container(unittest.TestCase):
 def test_cfb_restore(self):
  b,r,m=trial();self.assertEqual(c.restore(r,m,expected_source_sha256=n.digest(b),expected_result_sha256=n.digest(r),expected_manifest_sha256=n.digest(n.canonical(m))),b);self.assertEqual(CompoundFile(b).read_stream('\x02OlePres000'),CompoundFile(r).read_stream('\x02OlePres000'))
 def test_ppt_restore_serial(self):
  b,r,m=trial('pptx',True);self.assertEqual(c.restore(r,m,expected_source_sha256=n.digest(b),expected_result_sha256=n.digest(r),expected_manifest_sha256=n.digest(n.canonical(m))),b);self.assertEqual(len(m['native_deltas']),4)
 def test_bad_container_source_anchor(self):
  b,r,m=trial()
  with self.assertRaisesRegex(n.Rejected,'container source'):c.patch(b,m['plans'],kind='cfb',expected_source_sha256='0'*64,expected_cfb_sha256=m['cfb_source_sha256'],expected_native_sha256=m['native_source_sha256'],expected_bundle_sha256=m['bundle_sha256'])
 def test_bad_bundle_anchor(self):
  b,r,m=trial()
  with self.assertRaisesRegex(n.Rejected,'bundle'):c.patch(b,m['plans'],kind='cfb',expected_source_sha256=n.digest(b),expected_cfb_sha256=m['cfb_source_sha256'],expected_native_sha256=m['native_source_sha256'],expected_bundle_sha256='0'*64)
 def test_bad_manifest_external_anchor(self):
  b,r,m=trial();bad=copy.deepcopy(m);bad['source_sha256']='0'*64
  with self.assertRaisesRegex(n.Rejected,'manifest external'):c.restore(r,bad,expected_source_sha256=n.digest(b),expected_result_sha256=n.digest(r),expected_manifest_sha256=n.digest(n.canonical(m)))
 def test_restamped_manifest_wrong_source(self):
  b,r,m=trial();bad=copy.deepcopy(m);bad['source_sha256']='0'*64
  with self.assertRaisesRegex(n.Rejected,'source/result anchors'):c.restore(r,bad,expected_source_sha256=n.digest(b),expected_result_sha256=n.digest(r),expected_manifest_sha256=n.digest(n.canonical(bad)))
 def test_changed_result_external_anchor(self):
  b,r,m=trial()
  with self.assertRaisesRegex(n.Rejected,'result external'):c.restore(r[:-1]+b'x',m,expected_source_sha256=n.digest(b),expected_result_sha256=n.digest(r),expected_manifest_sha256=n.digest(n.canonical(m)))
 def test_reused_old_plan_blocks_serial(self):
  b,r,m=trial();plans=m['plans']*2
  with self.assertRaises(n.Rejected):c.apply_native_bundle(CompoundFile(b).read_stream('Contents'),plans,expected_native_sha256=m['native_source_sha256'],expected_bundle_sha256=n.digest(n.canonical(plans)))
 def test_internal_cli_disabled(self):
  proc=subprocess.run([sys.executable,str(Path(c.__file__).with_name('writeback.py')),'restore'],capture_output=True,timeout=3);self.assertNotEqual(proc.returncode,0);self.assertIn(b'Internal byte-only helper',proc.stderr)
 def test_manifest_float_and_duplicate_rejected(self):
  for raw in (b'{"x":1e309}',b'{"x":1,"x":2}'):
   with self.assertRaises(n.Rejected):c.manifest_json(raw)
 def test_no_follow_ancestor_swap(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);parent=root/'parent';parent.mkdir();src=parent/'input';src.write_bytes(b'safe');other=root/'other';other.mkdir();(other/'input').write_bytes(b'unsafe');original=n.parent_fd
   def swapped(path):
    parent.rename(root/'old');parent.symlink_to(other,target_is_directory=True);return original(path)
   with patch.object(n,'parent_fd',swapped):
    with self.assertRaises(OSError):n.bounded_regular(src,1024)
 def test_new_output_is_exclusive(self):
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'src';src.write_bytes(b'original');out=Path(d)/'out';n.new_output(src,out,b'new')
   with self.assertRaises(ValueError):n.new_output(src,out,b'bad')
   self.assertEqual(out.read_bytes(),b'new');self.assertEqual(src.read_bytes(),b'original')

if __name__=='__main__':unittest.main(verbosity=2)
