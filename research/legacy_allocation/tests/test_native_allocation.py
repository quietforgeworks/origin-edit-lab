import copy,csv,io,json,os,random,struct,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import native_allocation as p
import make_cases
from unittest.mock import patch
from make_cases import toy_csv
from numeric_support import convert_number,publish_noreplace
from verify_source_artifacts import canonical,verify_case_source
FIXTURE=Path(os.environ['ORIGIN_PUBLIC_FIXTURE']) if os.environ.get('ORIGIN_PUBLIC_FIXTURE') else None

class InputTests(unittest.TestCase):
 def test_research_count_whitelist(self):
  for n in p.COUNTS:self.assertEqual(len(p.parse_csv(toy_csv(n))[0]),n)
 def test_unvalidated_counts(self):
  for n in (0,1,7,49,50,52,256,258,1023,1025):
   with self.subTest(n=n),self.assertRaises(p.Rejected):p.parse_csv(('A,B\n'+'0,0\n'*n).encode())
 def test_bad_csv(self):
  raw=toy_csv(51)
  for b in (b'',b'\xff',raw+b'\n',raw.replace(b'A,B',b'X,Y'),raw.replace(b'-0,-0',b'1,2,3',1),raw.replace(b'-0,-0',b'1',1),raw.replace(b'-0,-0',b'"unfinished',1),b'0'*262145):
   with self.assertRaises(p.Rejected):p.parse_csv(b)
 def test_numeric_hazards(self):
  for token in ('NaN','Infinity','1e999','1e-999','2.2250738585072009e-308','9007199254740993','1_000','0x1p0',' 1','1 ','','true','=1+1'):
   with self.subTest(token=token),self.assertRaises(p.Rejected):p.parse_csv(toy_csv(51).replace(b'-0,-0',(token+',0').encode(),1))
 def test_axis_bounds(self):
  for row in (b'-5.1,0',b'55.1,0',b'0,-.1000001',b'0,1.1000001'):
   with self.assertRaises(p.Rejected):p.parse_csv(toy_csv(51).replace(b'-0,-0',row,1))
 def test_negative_zero(self):
  v,m=convert_number('-0.00','toy',1,'A');self.assertEqual(struct.pack('<d',v).hex(),'0000000000000080');self.assertTrue(m['negative_zero'])
 def test_rounding_ledger(self):
  v,m=convert_number('0.1','toy',1,'A');self.assertEqual(m['conversion'],'rounded_to_nearest_ties_even');self.assertNotEqual(m['signed_decimal_error_binary64_minus_input'],'0');self.assertEqual(m['binary64_little_endian_hex'],struct.pack('<d',v).hex())
 def test_missing_sentinel(self):
  with self.assertRaises(p.Rejected):convert_number(repr(p.MISSING),'toy',1,'A')
 def test_default_export_fails_closed(self):
  for mode in (False,None,1,'true'):
   with self.assertRaisesRegex(p.Rejected,'Origin-safe allocation expansion refused'):p.patch_bytes(b'',toy_csv(51),research_only=mode)
 def test_default_generate_creates_nothing(self):
  with tempfile.TemporaryDirectory() as d:
   dest=Path(d)/'out'
   with self.assertRaisesRegex(p.Rejected,'Origin-safe'):p.generate('absent','absent',dest)
   self.assertEqual(list(Path(d).iterdir()),[])
 def test_frame_hazards(self):
  for b,pos in ((b'',0),(b'\0'*5,0),(b'\xff'*4+b'\n',0),(b'\1\0\0\0\nZ!',0),(b'\0'*8,-1),(b'\0'*8,True)):
   with self.assertRaises(p.Rejected):p.frame(b,pos)
 def test_frame_roundtrip(self):
  for raw in (b'',b'0',b'\0\n\xff'*100):self.assertEqual(p.frame(p.framed(raw),0)['payload'],raw)
 def test_canonical_signedzero_boolean_types(self):
  self.assertNotEqual(canonical({'x':-0.}),canonical({'x':0.}));self.assertNotEqual(canonical({'x':1}),canonical({'x':True}))
 def test_atomic_no_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/'stage';b=Path(d)/'out';a.mkdir();b.mkdir();(a/'sentinel').write_text('intact')
   with self.assertRaises(p.Rejected):publish_noreplace(a,b)
   self.assertEqual((a/'sentinel').read_text(),'intact');self.assertEqual(list(b.iterdir()),[])
 def test_nested_symlink_preflight(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'real/child').mkdir(parents=True);(root/'alias').symlink_to(root/'real',target_is_directory=True)
   with self.assertRaises(p.Rejected):p.checked_path(root/'alias/child/out')
 def test_parent_traversal_preflight(self):
  with self.assertRaises(p.Rejected):p.checked_path('ordinary/../out')

@unittest.skipUnless(FIXTURE is not None and FIXTURE.is_file(),'exact public fixture is external prerequisite')
class FixtureTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.src=FIXTURE.read_bytes()
  if p.sha(cls.src)!=p.TEMPLATE_HASH:raise RuntimeError('wrong external fixture')
  cls.cases={n:p.patch_bytes(cls.src,toy_csv(n),research_only=True) for n in p.COUNTS}
 def test_all_sizes_allocations(self):
  for n,(b,m,before,after) in self.cases.items():
   self.assertEqual(len(b),p.TEMPLATE_SIZE+20*(n-50));self.assertEqual(after['active_rows'],n);self.assertEqual(after['allocated_rows'],n);self.assertEqual(after['frame_count'],478)
 def test_exact_rollback(self):
  for b,m,_,_ in self.cases.values():self.assertEqual(p.restore_bytes(b,m),self.src)
 def test_full_suffix_relocated_intact(self):
  for n,(b,m,_,_) in self.cases.items():self.assertEqual(b[1412+20*(n-50):],self.src[1412:])
 def test_global_ids_preserved(self):
  for _,_,before,after in self.cases.values():self.assertEqual(before['dataset_ids_names'],after['dataset_ids_names']);self.assertEqual(len(after['dataset_ids_names']),25)
 def test_graph_tail_hashes_preserved(self):
  for _,_,before,after in self.cases.values():
   for k in ('graph_sha256','opaque_tail_sha256'):self.assertEqual(before[k],after[k])
 def test_header_fields_only(self):
  for n,(b,_,_,_) in self.cases.items():
   for old,new in ((103,103),(760,760+10*(n-50))):
    a=bytearray(p.frame(self.src,old)['payload']);c=bytearray(p.frame(b,new)['payload']);self.assertEqual(struct.unpack_from('<III',c,25),(n,0,n))
    for off in (25,33):a[off:off+4]=c[off:off+4]=b'\0'*4
    self.assertEqual(a,c)
 def test_every_cell_bit_exact(self):
  for n,(b,m,_,_) in self.cases.items():
   values,ledger=p.parse_csv(toy_csv(n));self.assertEqual(canonical(ledger),canonical(m['binary64_conversion_ledger']))
   for c,pos in ((0,249),(1,906+10*(n-50))):
    data=p.frame(b,pos)['payload'];self.assertEqual(len(data),n*10)
    for r in range(n):self.assertEqual(data[r*10:r*10+10],b'\0\0'+struct.pack('<d',values[r][c]))
 def test_signed_zero_after_old_limit(self):
  for n,(b,m,_,_) in self.cases.items():
   data=p.frame(b,906+10*(n-50))['payload']
   for r in (50,256,1023):
    if r<n:self.assertEqual(data[r*10+2:r*10+10].hex(),'0000000000000080')
 def test_unknown_metadata_stays_unchanged(self):
  for n,(b,_,_,_) in self.cases.items():
   for pos in (123513,124015,219404):self.assertEqual(p.frame(b,pos+20*(n-50))['payload'][7:15],struct.pack('<II',0,50))
 def test_altered_template_rejected(self):
  for pos in (0,103,249,756,123525,219416,228956):
   b=bytearray(self.src);b[pos]^=1
   with self.assertRaises(p.Rejected):p.patch_bytes(bytes(b),toy_csv(51),research_only=True)
 def test_repatch_rejected(self):
  for b,_,_,_ in self.cases.values():
   with self.assertRaises(p.Rejected):p.patch_bytes(b,toy_csv(51),research_only=True)
 def test_changed_framing_rejected(self):
  for pos in (103,107,248,249,253,754,759):
   b=bytearray(self.src);b[pos]^=1
   with self.assertRaises(p.Rejected):p.inspect(bytes(b),50)
 def test_changed_opaque_fields_rejected(self):
  for pos in (123513+12,124015+16,219404+12,219404+16):
   b=bytearray(self.src);b[pos]^=1
   with self.assertRaises(p.Rejected):p.inspect(bytes(b),50)
 def test_manifest_schema_attacks(self):
  b,m,_,_=self.cases[51]
  for key,v in (('profile','other'),('template_sha256','0'*64),('candidate_sha256','0'*64),('allocated_rows',True),('allocated_rows',52),('allocated_rows',257),('splices',[])):
   bad=copy.deepcopy(m);bad[key]=v
   with self.assertRaises(p.Rejected):p.restore_bytes(b,bad)
 def test_splice_schema_attacks(self):
  b,m,_,_=self.cases[51]
  for key,v in (('old_offset',True),('old_offset',0),('new_offset',0),('old_length',1),('new_length',500),('dataset_id_one_based',2),('kind','x'),('old_hex','zz'),('new_hex','00')):
   bad=copy.deepcopy(m);bad['splices'][0][key]=v
   with self.assertRaises(p.Rejected):p.restore_bytes(b,bad)
 def test_changed_candidate_hash_rejected(self):
  b,m,_,_=self.cases[51];b=bytearray(b);b[2500]^=1
  with self.assertRaises(p.Rejected):p.restore_bytes(bytes(b),m)
 def test_unrelated_mutation_rewritten_hash_rejected(self):
  b,m,_,_=self.cases[51];b=bytearray(b);b[5000]^=1;bad=copy.deepcopy(m);bad['candidate_sha256']=p.sha(b)
  with self.assertRaises(p.Rejected):p.restore_bytes(bytes(b),bad)
 def test_candidate_source_sourceimmutable(self):
  self.assertEqual(FIXTURE.read_bytes(),self.src)
 def test_generate_no_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   csvpath=Path(d)/'raw.csv';csvpath.write_bytes(toy_csv(51));dest=Path(d)/'out';p.generate(FIXTURE,csvpath,dest,research_only=True)
   self.assertEqual((dest/'rollback.opj').read_bytes(),self.src);self.assertEqual((dest/'raw.csv').read_bytes(),toy_csv(51))
   with self.assertRaises(p.Rejected):p.generate(FIXTURE,csvpath,dest,research_only=True)
 def test_symlinks_refused(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);raw=d/'raw.csv';raw.write_bytes(toy_csv(51));link=d/'link';link.symlink_to(raw);dest=d/'out'
   with self.assertRaises(p.Rejected):p.generate(FIXTURE,link,dest,research_only=True)
   dest.symlink_to(d/'missing')
   with self.assertRaises(p.Rejected):p.generate(FIXTURE,raw,dest,research_only=True)
 def test_nested_output_symlink_refused(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);(d/'real/child').mkdir(parents=True);(d/'alias').symlink_to(d/'real',target_is_directory=True);raw=d/'raw.csv';raw.write_bytes(toy_csv(51))
   with self.assertRaises(p.Rejected):p.generate(FIXTURE,raw,d/'alias/child/out',research_only=True)
   self.assertEqual(list((d/'real/child').iterdir()),[])
 def test_nested_input_symlink_refused(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);(d/'real/child').mkdir(parents=True);(d/'alias').symlink_to(d/'real',target_is_directory=True);raw=d/'real/child/raw.csv';raw.write_bytes(toy_csv(51))
   with self.assertRaises(p.Rejected):p.generate(FIXTURE,d/'alias/child/raw.csv',d/'out',research_only=True)
   self.assertFalse((d/'out').exists())
 def test_make_cases_candidates_symlink_refused_before_write(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);root=d/'source';target=d/'target';root.mkdir();target.mkdir();(root/'candidates').symlink_to(target,target_is_directory=True)
   with patch.object(make_cases,'ROOT',root),self.assertRaises(p.Rejected):make_cases.main(research_only=True)
   self.assertEqual(list(target.iterdir()),[])
 def test_make_cases_fixture_symlink_refused_before_output(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);fixture=d/'fixture.opj';fixture.symlink_to(FIXTURE)
   with patch.object(make_cases,'ROOT',d),patch.dict(os.environ,{'ORIGIN_PUBLIC_FIXTURE':str(fixture)}),self.assertRaises(p.Rejected):make_cases.main(research_only=True)
   self.assertFalse((d/'candidates').exists())
 def test_make_cases_csv_creation_race_no_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);csvpath=d/'candidates/raw51.csv';original=Path.open
   def race(path,mode='r',*args,**kwargs):
    if path==csvpath and mode=='xb':
     with original(path,'wb') as stream:stream.write(b'concurrent-sentinel')
    return original(path,mode,*args,**kwargs)
   with patch.object(make_cases,'ROOT',d),patch.object(Path,'open',race),self.assertRaises(p.Rejected):make_cases.main(research_only=True)
   self.assertEqual(csvpath.read_bytes(),b'concurrent-sentinel');self.assertFalse((d/'candidates/generated51').exists())
 def test_unknown_counts_no_output(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);raw=d/'raw.csv';raw.write_bytes(b'A,B\n'+b'0,0\n'*52)
   with self.assertRaises(p.Rejected):p.generate(FIXTURE,raw,d/'out',research_only=True)
   self.assertFalse((d/'out').exists())
 def test_source_audit_full_manifest_tamper(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'candidates').mkdir();raw=root/'candidates/raw51.csv';raw.write_bytes(toy_csv(51));dest=root/'candidates/generated51';p.generate(FIXTURE,raw,dest,research_only=True)
   verify_case_source(root,51)
   original=(dest/'manifest.json').read_text()
   for key,value in (('safe_native_export_supported',True),('unknown_metadata_preserved_not_semantically_validated',False),('allocated_rows',True)):
    m=json.loads(original);m[key]=value;(dest/'manifest.json').write_text(json.dumps(m))
    with self.assertRaises(p.Rejected):verify_case_source(root,51)
 def test_source_audit_signedzero_tamper(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'candidates').mkdir();raw=root/'candidates/raw51.csv';raw.write_bytes(toy_csv(51));dest=root/'candidates/generated51';p.generate(FIXTURE,raw,dest,research_only=True)
   m=json.loads((dest/'manifest.json').read_text());m['binary64_conversion_ledger'][0]['binary64_value']=0.;(dest/'manifest.json').write_text(json.dumps(m))
   with self.assertRaises(p.Rejected):verify_case_source(root,51)
 def test_source_audit_opaque_mutation_rewritten_manifest(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'candidates').mkdir();raw=root/'candidates/raw51.csv';raw.write_bytes(toy_csv(51));dest=root/'candidates/generated51';p.generate(FIXTURE,raw,dest,research_only=True)
   b=bytearray((dest/'candidate.opj').read_bytes());b[228976]^=1;(dest/'candidate.opj').write_bytes(b)
   m=json.loads((dest/'manifest.json').read_text());m['candidate_sha256']=p.sha(b);(dest/'manifest.json').write_text(json.dumps(m))
   with self.assertRaises(p.Rejected):verify_case_source(root,51)

if __name__=='__main__':unittest.main(verbosity=2)
