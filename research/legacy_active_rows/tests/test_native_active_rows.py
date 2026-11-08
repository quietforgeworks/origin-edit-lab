import copy,csv,io,json,math,os,random,struct,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import native_active_rows as p
from numeric_support import convert_number,publish_noreplace
HERE=Path(__file__).resolve().parents[1]
FIXTURE=Path(os.environ.get('ORIGIN_PUBLIC_FIXTURE',str(HERE.parent/'origin-data-generation/native-generation-v3/inputs/origin8_test_tree_import.opj')))
def raw(n=7):return ('A,B\n'+''.join(('-0,-0\n' if i==0 else f'{i}.1,0.12345678901234567\n') for i in range(n))).encode()
class InputTests(unittest.TestCase):
 def test_allowed_counts(self):
  for n in (7,49,50):self.assertEqual(len(p.parse_csv(raw(n))[0]),n)
 def test_unvalidated_counts(self):
  for n in (0,1,6,8,48,51,257):
   with self.assertRaises(p.Rejected):p.parse_csv(raw(n))
 def test_range_count_types(self):
  for n in (True,False,7.,'7',None,-1,51,257):
   with self.assertRaises(p.Rejected):p.ranges(n)
 def test_csv_shape_encoding(self):
  for data in (b'',raw().replace(b'A,B',b'X,Y'),raw()+b'\n',raw().replace(b'-0,-0',b'-0,-0,3'),raw().replace(b'-0,-0',b'-0'),b'\xff'+raw(),raw().replace(b'-0,-0',b'"unterminated'),b'x'*32769):
   with self.assertRaises(p.Rejected):p.parse_csv(data)
 def test_bad_numbers(self):
  for token in ('NaN','nan','Infinity','1e999','1e-999','2.2250738585072009e-308','9007199254740993','1_000','0x1p0',' 1','1 ','','true','=1+1'):
   with self.assertRaises(p.Rejected):p.parse_csv(raw().replace(b'-0,-0',(token+',0').encode(),1))
 def test_axis_bounds(self):
  for token in ('-5.001,0','55.001,0','0,-0.1000001','0,1.100001'):
   with self.assertRaises(p.Rejected):p.parse_csv(raw().replace(b'-0,-0',token.encode(),1))
 def test_rounding_ledger(self):
  v,e=convert_number('0.1','toy',1,'A');self.assertEqual(e['conversion'],'rounded_to_nearest_ties_even');self.assertNotEqual(e['signed_decimal_error_binary64_minus_input'],'0');self.assertEqual(e['binary64_little_endian_hex'],struct.pack('<d',v).hex())
 def test_negative_zero(self):
  v,e=convert_number('-0.000','toy',1,'A');self.assertEqual(struct.pack('<d',v).hex(),'0000000000000080');self.assertTrue(e['negative_zero'])
 def test_missing_sentinel_refused(self):
  with self.assertRaises(p.Rejected):convert_number(repr(p.MISSING),'toy',1,'A')
@unittest.skipUnless(FIXTURE.is_file(),'Exact separately obtained public fixture required')
class FixtureTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.src=FIXTURE.read_bytes();cls.assert_source=p.sha(cls.src)==p.TEMPLATE_HASH
 def setUp(self):self.assertTrue(self.assert_source)
 def test_patch_restore_all_supported(self):
  for n in (7,49,50):
   b,m,before,after=p.patch_bytes(self.src,raw(n));self.assertEqual(len(b),len(self.src));self.assertEqual(p.restore_bytes(b,m),self.src);self.assertEqual(after['columns'][0]['end_exclusive'],n);self.assertEqual(after['columns'][1]['end_exclusive'],n)
 def test_complete_allowed_diff(self):
  for n in (7,49,50):
   b,m,_,_=p.patch_bytes(self.src,raw(n));allow={i for q,s,_ in p.ranges(n) for i in range(q,q+s)};self.assertEqual([i for i,(x,y) in enumerate(zip(self.src,b)) if x!=y],m['changed_byte_offsets']);self.assertTrue(set(m['changed_byte_offsets'])<=allow);self.assertEqual(m['allowed_byte_count'],16*n+8)
 def test_native_graph_and_tail_exact(self):
  for n in (7,49,50):
   b,_,_,_=p.patch_bytes(self.src,raw(n));self.assertEqual(b[182277:],self.src[182277:])
 def test_inactive_raw_cells_retained(self):
  for n in (7,49):
   b,_,_,_=p.patch_bytes(self.src,raw(n))
   for _,_,dp,_ in p.DATASETS:self.assertEqual(b[dp+5+10*n:dp+505],self.src[dp+5+10*n:dp+505])
 def test_bound_field_ownership(self):
  b,_,_,_=p.patch_bytes(self.src,raw(7))
  for _,hp,dp,_ in p.DATASETS:self.assertEqual(struct.unpack_from('<III',b,hp+5+25),(50,0,7));self.assertEqual(struct.unpack_from('<I',b,dp)[0],500)
 def test_all_bits_and_ledger(self):
  for n in (7,49,50):
   b,m,_,a=p.patch_bytes(self.src,raw(n));values,ledger=p.parse_csv(raw(n));self.assertEqual(ledger,m['binary64_conversion_ledger'])
   for _,_,dp,c in p.DATASETS:
    for r in range(n):self.assertEqual(b[dp+7+10*r:dp+15+10*r],struct.pack('<d',values[r][c-1]))
 def test_random_numeric_roundtrips(self):
  rng=random.Random(9301)
  for n in (7,49,50):
   rr=('A,B\n'+''.join(f'{rng.random()*40:.17g},{rng.random():.17g}\n' for _ in range(n))).encode();b,m,_,_=p.patch_bytes(self.src,rr);self.assertEqual(p.restore_bytes(b,m),self.src)
 def test_modified_source_rejected(self):
  for offset in (0,4,141,256,123525,219416,228956):
   b=bytearray(self.src);b[offset]^=1
   with self.assertRaises(p.Rejected):p.patch_bytes(bytes(b),raw())
 def test_repatch_rejected(self):
  b,*_=p.patch_bytes(self.src,raw())
  with self.assertRaises(p.Rejected):p.patch_bytes(b,raw(49))
 def test_noop_rejected(self):
  columns=p.inspect(self.src)['columns'];vals=[[struct.unpack('<d',bytes.fromhex(c['binary64_le'][i]))[0] for c in columns] for i in range(50)]
  same=('A,B\n'+''.join(f'{a!r},{b!r}\n' for a,b in vals)).encode()
  with self.assertRaises(p.Rejected):p.patch_bytes(self.src,same)
 def test_framing_corruption(self):
  for off in (103,107,248,249,253,754):
   b=bytearray(self.src);b[off]^=1
   with self.assertRaises(p.Rejected):p.inspect(bytes(b))
 def test_opaque_fields_refused(self):
  for off in (123513+12,124015+16,219404+12,219404+16):
   b=bytearray(self.src);b[off]^=1
   with self.assertRaises(p.Rejected):p.inspect(bytes(b))
 def test_candidate_tamper(self):
  b,m,_,_=p.patch_bytes(self.src,raw());bad=bytearray(b);bad[2500]^=1
  with self.assertRaises(p.Rejected):p.restore_bytes(bytes(bad),m)
 def test_manifest_tamper(self):
  b,m,_,_=p.patch_bytes(self.src,raw())
  for key,val in (('profile','other'),('template_sha256','0'*64),('candidate_sha256','0'*64),('active_rows',True),('active_rows',49),('replacements',[])):
   mm=copy.deepcopy(m);mm[key]=val
   with self.assertRaises(p.Rejected):p.restore_bytes(b,mm)
 def test_replacement_tamper(self):
  b,m,_,_=p.patch_bytes(self.src,raw())
  for key,val in (('offset',True),('offset',1),('size',8),('kind','cell'),('old_hex','zz'),('new_hex','00'),('old_hex','00000000')):
   mm=copy.deepcopy(m);mm['replacements'][0][key]=val
   with self.assertRaises(p.Rejected):p.restore_bytes(b,mm)
 def test_unknown_rows_no_output(self):
  with tempfile.TemporaryDirectory() as d:
   for n in (51,257):
    csv=Path(d)/'raw.csv';csv.write_bytes(raw(n));dest=Path(d)/str(n)
    with self.assertRaises(p.Rejected):p.generate(FIXTURE,csv,dest)
    self.assertFalse(dest.exists())
 def test_generate_roundtrip_no_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   c=Path(d)/'raw.csv';c.write_bytes(raw());dest=Path(d)/'out';m=p.generate(FIXTURE,c,dest);self.assertEqual((dest/'rollback.opj').read_bytes(),self.src);self.assertEqual(p.sha((dest/'candidate.opj').read_bytes()),m['candidate_sha256'])
   with self.assertRaises(p.Rejected):p.generate(FIXTURE,c,dest)
 def test_symlink_no_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   c=Path(d)/'raw.csv';c.write_bytes(raw());dest=Path(d)/'out';dest.symlink_to(Path(d)/'absent')
   with self.assertRaises(p.Rejected):p.generate(FIXTURE,c,dest)
 def test_atomic_existing_directory(self):
  with tempfile.TemporaryDirectory() as d:
   stage=Path(d)/'stage';dest=Path(d)/'out';stage.mkdir();dest.mkdir();(stage/'sentinel').write_text('intact')
   with self.assertRaises(p.Rejected):publish_noreplace(stage,dest)
   self.assertEqual((stage/'sentinel').read_text(),'intact');self.assertEqual(list(dest.iterdir()),[])
if __name__=='__main__':unittest.main(verbosity=2)
