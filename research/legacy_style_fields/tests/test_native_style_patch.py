"""Unit and optional public-fixture integration tests. No binary fixture vendored."""
import copy,json,struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import native_style_patch as p
class EncodingTests(unittest.TestCase):
 def test_tick_font(self):
  for key in p.PROFILES:self.assertEqual(p.field_spec(key,'xb_tick_font',26)[1],b'\x1a\0')
 def test_reject_float_font(self):
  for v in (26.0,True,'26',0,-1,256,None):
   with self.subTest(value=v),self.assertRaises(p.Rejected):p.field_spec('two_graphs','xb_tick_font',v)
 def test_reject_width(self):
  for v in (1.0,True,'500',0,-1,65536,None):
   with self.subTest(value=v),self.assertRaises(p.Rejected):p.field_spec('two_graphs','xb_axis_width',v)
 def test_width_encoding(self):self.assertEqual(p.field_spec('two_graphs','xb_axis_width',1250)[1],b'\xe2\x04')
 def test_rect_encoding(self):self.assertEqual(p.field_spec('single_axes','layer_rect',[790,446,2641,1976])[1],struct.pack('<hhhh',790,446,2641,1976))
 def test_rect_rejections(self):
  for v in ([1,2,0,3],[0,2,2,2],[0,0,40000,10],[-1,0,4,4],[0.,0,4,4],[False,0,4,4],[0,0,4],(0,0,4,4),None):
   with self.subTest(value=v),self.assertRaises(p.Rejected):p.field_spec('two_graphs','layer_rect',v)
 def test_unknown_field(self):
  with self.assertRaises(p.Rejected):p.field_spec('two_graphs','font_family','Arial')
 def test_frame(self):self.assertEqual(p.frame(b'\x03\0\0\0\nabc\n',0,3),b'abc')
 def test_empty_frame(self):self.assertEqual(p.frame(b'\0\0\0\0\n',0,0),b'')
 def test_bad_frames(self):
  for b in (b'',b'\x03\0\0\0\nabc',b'\x03\0\0\0!abc\n',b'\x03\0\0\0\nabc!',b'\x04\0\0\0\nabc\n'):
   with self.subTest(value=b),self.assertRaises(p.Rejected):p.frame(b,0,3)
 def test_negative_offsets(self):
  with self.assertRaises(p.Rejected):p.frame(b'',-1,0)
 def test_non_original_rejected(self):
  with self.assertRaises(p.Rejected):p.patch(b'not an Origin project','two_graphs','xb_tick_font',26)
 def test_unknown_profile(self):
  with self.assertRaises(p.Rejected):p.patch(b'', 'unknown','xb_tick_font',26)
class PublicationTests(unittest.TestCase):
 def test_publish_and_refuse_overwrite(self):
  import tempfile
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'result';p.publish_directory(out,{'a.bin':b'abc'})
   self.assertEqual((out/'a.bin').read_bytes(),b'abc')
   with self.assertRaises(p.Rejected):p.publish_directory(out,{'a.bin':b'changed'})
   self.assertEqual((out/'a.bin').read_bytes(),b'abc')
 def test_symlink_output_refused(self):
  import tempfile
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'result';out.symlink_to(Path(d)/'missing')
   with self.assertRaises(p.Rejected):p.publish_directory(out,{'a.bin':b'abc'})
 def test_invalid_artifact_name_refused(self):
  import tempfile
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'result'
   with self.assertRaises(p.Rejected):p.publish_directory(out,{'../evil':b'abc'})
   self.assertFalse(out.exists());self.assertFalse((Path(d)/'evil').exists())
 def test_missing_parent_refused(self):
  import tempfile
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(p.Rejected):p.publish_directory(Path(d)/'missing'/'out',{'a':b'b'})
class PublicFixtureTests(unittest.TestCase):
 def setUp(self):
  if not all(x['path'].is_file() for x in p.PROFILES.values()):self.skipTest('Optional exact public KDE fixtures not materialized')
 def cases(self):
  for key,prof in p.PROFILES.items():
   b=prof['path'].read_bytes();r=p.snapshot(b,key)['layer_client_rect_i16']
   for field,v in [('xb_tick_font',26),('xb_axis_width',1250),('curve_line_width',1250),('layer_rect',[r[0]+200,r[1]+150,r[2]-200,r[3]-150])]:yield key,b,field,v
 def test_exact_diff_and_complete_preservation(self):
  for key,b,f,v in self.cases():
   with self.subTest(profile=key,field=f):
    c,m,a,z=p.patch(b,key,f,v);start,end=m['allowed_range_half_open']
    self.assertEqual(b[:start]+b[end:],c[:start]+c[end:]);self.assertEqual(a['datasets'],z['datasets']);self.assertEqual(a['known_cached_payloads'],z['known_cached_payloads']);self.assertEqual(a['frames'],z['frames']);self.assertEqual(a['curve_binding'],z['curve_binding']);self.assertEqual(a['opaque_tail_sha256'],z['opaque_tail_sha256']);self.assertEqual(p.restore(c,m),b)
 def test_all_repatches_rejected(self):
  for key,b,f,v in self.cases():
   c,*_=p.patch(b,key,f,v)
   with self.subTest(profile=key,field=f),self.assertRaises(p.Rejected):p.patch(c,key,f,v)
 def test_changed_unknown_byte_rejected(self):
  for key,b,f,v in self.cases():
   c=b[:-1]+bytes([b[-1]^1])
   with self.subTest(profile=key,field=f),self.assertRaises(p.Rejected):p.patch(c,key,f,v)
 def test_rollback_candidate_tamper(self):
  for key,b,f,v in self.cases():
   c,m,*_=p.patch(b,key,f,v);c=c[:-1]+bytes([c[-1]^1])
   with self.subTest(profile=key,field=f),self.assertRaises(p.Rejected):p.restore(c,m)
 def test_rollback_manifest_tamper(self):
  for key,b,f,v in self.cases():
   c,m,*_=p.patch(b,key,f,v)
   for change in ('offset','before','after','range','candidate_hash','source_hash','value'):
    t=copy.deepcopy(m)
    if change=='offset':t['write']['offset']+=1
    elif change=='before':t['write']['before_hex']='ff'*len(bytes.fromhex(t['write']['before_hex']))
    elif change=='after':t['write']['after_hex']='00'*len(bytes.fromhex(t['write']['after_hex']))
    elif change=='range':t['allowed_range_half_open'][0]+=1
    elif change=='candidate_hash':t['candidate_sha256']='0'*64
    elif change=='source_hash':t['source_sha256']='0'*64
    else:t['requested_value']=1 if type(v)is int else [1,2,3,4]
    with self.subTest(profile=key,field=f,tamper=change),self.assertRaises(p.Rejected):p.restore(c,t)
 def test_noop_rejected(self):
  for key,pr in p.PROFILES.items():
   with self.subTest(profile=key),self.assertRaises(p.Rejected):p.patch(pr['path'].read_bytes(),key,'xb_tick_font',18)
 def test_outside_page_rejected(self):
  for key,pr in p.PROFILES.items():
   with self.subTest(profile=key),self.assertRaises(p.Rejected):p.patch(pr['path'].read_bytes(),key,'layer_rect',[1,1,32767,32767])
 def test_data_binary64_bit_patterns(self):
  for key,pr in p.PROFILES.items():
   ss=p.snapshot(pr['path'].read_bytes(),key)
   for col in ss['datasets']:
    for cell in col['cells']:self.assertEqual(len(bytes.fromhex(cell['binary64_le_hex'])),8)
 def test_cache_is_actual_emf_payload(self):
  b=p.PROFILES['single_axes']['path'].read_bytes();ss=p.snapshot(b,'single_axes');cs=ss['known_cached_payloads'];self.assertEqual(len(cs),1);c=cs[0];self.assertEqual(c['payload_bytes'],32588);self.assertEqual(b[c['payload_record']+5+40:c['payload_record']+5+44],b' EMF')
if __name__=='__main__':unittest.main(verbosity=2)
