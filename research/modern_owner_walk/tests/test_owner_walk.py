"""Synthetic-only parser checks. No user input bytes or identifiers in fixtures."""
from pathlib import Path
import struct,sys,unittest,tempfile,os,subprocess,shutil
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
import owner_walk as w

def uleb(n):
 out=bytearray()
 while True:
  x=n&127;n>>=7;out.append(x|(128 if n else 0))
  if not n:return bytes(out)
def sparse(raw):
 parts=[bytes([len(raw[i:i+127])])+raw[i:i+127] for i in range(0,len(raw),127)]
 enc=b''.join(parts);return b'\x80'+uleb(len(enc))+enc

def blob(raw):return uleb(len(raw))+raw+b'\n'
def annotation(name='XB',text=b't\0',encoded=False):
 h=bytearray(161);h[70:70+len(name)]=name.encode();style=bytearray(111);style[4]=17
 body=(b'\x81'+uleb(100)+uleb(3)+b'xyz') if encoded else blob(text)
 return sparse(h)+b'\0'+sparse(style)+body+b'\0\0\0'
def curve(x=1,y=2,kind=200,pre=b'',post=b''):
 h=bytearray(519);h[0]=1;struct.pack_into('<H',h,4,y);struct.pack_into('<H',h,35,x);h[76]=kind
 return sparse(h)+(blob(pre) if pre else b'\0')+blob(bytes.fromhex('01588009980340b3'))+(blob(post) if post else b'\0')
def layer(*,x=1,kind=200,label=b'',extra=b'',annotations=None):
 h=bytearray(409);h[:4]=bytes.fromhex('00001f00');out=sparse(h)+blob(label)+b'\0'+(blob(extra) if extra else b'\0')
 out+=(annotation() if annotations is None else annotations)+w.ZERO_LIST+curve(x=x,kind=kind)+w.ZERO_LIST+w.ZERO_LIST
 for axis in range(3):
  for role in range(6):
   record=bytearray(519);record[0]=17;struct.pack_into('<H',record,21,19 if role==2 else 625 if role==3 else 0);out+=sparse(record)
  out+=w.ZERO_LIST
 return out+b'\0'
def page(name='Synthetic',layers=None,extra=b''):
 h=bytearray(199);h[2:2+len(name)]=name.encode();return sparse(h)+(blob(extra) if extra else b'\0')+b'\0\0'+(layer() if layers is None else layers)+w.ZERO_LIST
def filedata(**kw):return b'CPYUA 4.3811 222\n'+page(**kw)

class TransportTests(unittest.TestCase):
 def test_complete_synthetic_ownership(self):
  r=w.inventory(filedata());self.assertEqual(r['summary']['complete_page_chains'],1);self.assertEqual(r['summary']['curves_walked'],1);self.assertEqual(r['summary']['axis_records_walked'],18)
 def test_named_title_from_sequential_parent(self):
  l=w.inventory(filedata())['pages'][0]['layers'][0];self.assertEqual(l['annotations'][0]['name'],'XB');self.assertEqual(l['annotations'][0]['text'],'t');self.assertEqual(l['annotations'][0]['stored_font_u8'],17)
 def test_two_layers_keep_distinct_owner_intervals(self):
  r=w.inventory(filedata(layers=layer()+layer()));ls=r['pages'][0]['layers'];self.assertEqual(len(ls),2);self.assertEqual(ls[0]['end'],ls[1]['offset']);self.assertNotEqual(ls[0]['curves'][0]['offset'],ls[1]['curves'][0]['offset'])
 def test_two_pages(self):
  r=w.inventory(b'CPYUA 4.3811 222\n'+page('One')+page('Two'));self.assertEqual([p['name'] for p in r['pages']],['One','Two']);self.assertTrue(all(p['chain_complete'] for p in r['pages']))
 def test_nonempty_layer_label_and_properties(self):
  r=w.inventory(filedata(layers=layer(label=b'Right',extra=b'opaque')));self.assertTrue(r['pages'][0]['chain_complete']);self.assertEqual(r['pages'][0]['layers'][0]['layer_name_bytes'],5)
 def test_histogram_zero_x_never_filled(self):
  c=w.inventory(filedata(layers=layer(x=0,kind=219)))['pages'][0]['layers'][0]['curves'][0];self.assertEqual(c['x_selector_u16'],0);self.assertEqual(c['plot_type_u8'],219);self.assertIn('UNKNOWN',c['selector_binding'])
 def test_curve_extra_properties(self):
  b=curve(pre=b'header props',post=b'other props');r=w.curve(b,0);self.assertEqual(r['end'],len(b));self.assertEqual(r['header_opaque_properties']['payload_bytes'],12)
 def test_encoded81_stays_opaque(self):
  r=w.inventory(filedata(layers=layer(annotations=annotation(encoded=True))));a=r['pages'][0]['layers'][0]['annotations'][0];self.assertEqual(a['data']['kind'],'encoded81-opaque');self.assertEqual(a['data']['declared_decoded_bytes'],100);self.assertNotIn('text',a)
 def test_nested_candidate_not_duplicate_standalone_page(self):
  r=w.inventory(filedata(extra=b'\n'+page('Embedded')));self.assertEqual(r['summary']['pages'],1);self.assertEqual(len(r['nested_page_candidates']),1)
 def test_truncation_not_complete(self):
  r=w.inventory(filedata()[:-1]);self.assertFalse(r['pages'][0]['chain_complete'])
 def test_nonempty_axisbreak_not_skipped(self):
  b=filedata();r=w.inventory(b);l=r['pages'][0]['layers'][0];at=l['curves'][0]['end']+len(w.ZERO_LIST);bad=b[:at]+b'\1'+b[at+1:];q=w.inventory(bad);self.assertFalse(q['pages'][0]['chain_complete']);self.assertIn('axis-break',q['pages'][0]['blocker'])
 def test_corrupt_annotation_length_stops_chain(self):
  b=filedata();r=w.inventory(b);at=r['pages'][0]['layers'][0]['annotations'][0]['data']['offset'];bad=b[:at]+b'\x7f'+b[at+1:];q=w.inventory(bad);self.assertFalse(q['pages'][0]['chain_complete']);self.assertEqual(q['summary']['curves_walked'],0)
 def test_encoded81_bounds_fail_closed(self):
  with self.assertRaises(w.Unknown):w.compact_blob(b'\x81\x64\x20abc',0)
 def test_noncanonical_varint_rejected(self):
  with self.assertRaises(w.Unknown):w.compact_blob(b'\x82\x00ab\n',0)
 def test_missing_dataplot_magic_rejected(self):
  b=curve();b=b.replace(bytes.fromhex('01588009980340b3'),b'abcdefgh')
  with self.assertRaises(w.Unknown):w.curve(b,0)
 def test_unsupported_sparse_opcode_not_silently_skipped(self):
  with self.assertRaises(w.s.Reject):w.s.frame(b'\x80\x01\xc6',0)
 def test_no_mutation(self):
  b=filedata();before=w.s.sha(b);w.inventory(b);self.assertEqual(w.s.sha(b),before)
 def test_wrong_signature_rejected(self):
  with self.assertRaises(w.Unknown):w.inventory(b'not-a-native-project')

class RegressionV2(unittest.TestCase):
 def test_incomplete_outer_still_owns_opaque_payload(self):
  b=filedata(extra=b'\n'+page('Embedded'))[:-1];r=w.inventory(b)
  self.assertEqual(len(r['pages']),1);self.assertFalse(r['pages'][0]['chain_complete']);self.assertEqual(len(r['nested_page_candidates']),1)
 def test_failed_annotation_after_bounded_opaque_still_masks_inner_page(self):
  h=bytearray(161);h[70:72]=b'XB';style=bytes(111)
  broken=sparse(h)+b'\0'+sparse(style)+blob(b'\n'+page('Hidden'))+b'\0\0\x01'
  r=w.inventory(filedata(layers=layer(annotations=broken)));self.assertEqual(len(r['pages']),1);self.assertFalse(r['pages'][0]['chain_complete']);self.assertEqual(len(r['nested_page_candidates']),1)
 def test_ambiguous_81_raw_length_never_guessed(self):
  b=uleb(129)+b'\x01'+b'x'*128+b'\n'
  with self.assertRaisesRegex(w.Unknown,'ambiguous'):w.compact_blob(b,0)
 def test_non_ascii_signature_is_clean_rejection(self):
  with self.assertRaises(w.Unknown):w.inventory(b'CPYUA 4.3811 \xff22\n'+page())
 def test_missing_signature_newline_rejected(self):
  with self.assertRaises(w.Unknown):w.inventory(b'CPYUA '+b'a'*101)
 def test_page_budget_checked_before_extra_decode(self):
  b=b'CPYUA 4.3811 222\n'+b'\n'.join(sparse(bytearray(b'\0\0Graph'+bytes(192))) for _ in range(4097))
  calls=0;original=w.s.frame
  def counted(*args):
   nonlocal calls;calls+=1;return original(*args)
  with patch.object(w.s,'frame',counted):
   with self.assertRaisesRegex(w.Unknown,'page count budget'):w.discover_page_headers(b)
  self.assertEqual(calls,4096)
 def test_global_claim_budget(self):
  owned=w.OwnedRanges({'claims':w.MAX_OWNED_SPANS})
  with self.assertRaisesRegex(w.Unknown,'global owned-span'):w.claim(owned,0,1,'test')
 def test_new_output_does_not_change_source(self):
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'source';src.write_bytes(b'example input');out=Path(d)/'new.json'
   w.atomic_new_output(src,out,b'result');self.assertEqual(src.read_bytes(),b'example input');self.assertEqual(out.read_bytes(),b'result')
 def test_same_path_rejected_without_change(self):
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'source';src.write_bytes(b'original')
   with self.assertRaises(w.Unknown):w.atomic_new_output(src,src,b'bad')
   self.assertEqual(src.read_bytes(),b'original')
 def test_hardlink_output_rejected_without_change(self):
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'source';src.write_bytes(b'original');out=Path(d)/'hardlink';os.link(src,out)
   with self.assertRaises(w.Unknown):w.atomic_new_output(src,out,b'bad')
   self.assertEqual(src.read_bytes(),b'original')
 def test_symlink_output_rejected_without_change(self):
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'source';src.write_bytes(b'original');out=Path(d)/'symlink';out.symlink_to(src)
   with self.assertRaises(w.Unknown):w.atomic_new_output(src,out,b'bad')
   self.assertEqual(src.read_bytes(),b'original');self.assertTrue(out.is_symlink())
 def test_existing_unrelated_output_is_not_overwritten(self):
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'source';src.write_bytes(b'original');out=Path(d)/'other';out.write_bytes(b'keep')
   with self.assertRaises(w.Unknown):w.atomic_new_output(src,out,b'bad')
   self.assertEqual(out.read_bytes(),b'keep')
 def test_symlink_parent_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);src=root/'source';src.write_bytes(b'original');folder=root/'real';folder.mkdir();alias=root/'alias';alias.symlink_to(folder,target_is_directory=True)
   with self.assertRaises(w.Unknown):w.atomic_new_output(src,alias/'out',b'bad')
   self.assertEqual(list(folder.iterdir()),[])
 def test_publication_race_cannot_clobber(self):
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'source';src.write_bytes(b'original');out=Path(d)/'out';real_link=os.link
   def racing(a,b,**kwargs):
    Path(b).write_bytes(b'winner');return real_link(a,b,**kwargs)
   with patch.object(w.os,'link',racing):
    with self.assertRaises(FileExistsError):w.atomic_new_output(src,out,b'bad')
   self.assertEqual(out.read_bytes(),b'winner');self.assertEqual(src.read_bytes(),b'original')

class PackagingV2(unittest.TestCase):
 def test_source_size_rejected_before_open_read(self):
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'large';src.write_bytes(b'x')
   with src.open('r+b') as f:f.truncate(w.MAX_BLOB+1)
   with patch.object(Path,'open',side_effect=AssertionError('should not read')):
    with self.assertRaisesRegex(w.Unknown,'preflight'):w.read_source(src)
 def test_relocated_self_contained_cli(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);code=root/'code';code.mkdir();run=root/'elsewhere';run.mkdir()
   original=Path(w.__file__).parent
   for name in ('owner_walk.py','sparse_transport.py'):shutil.copyfile(original/name,code/name)
   src=run/'source.bin';raw=filedata();src.write_bytes(raw);out=run/'result.json'
   proc=subprocess.run([sys.executable,'-B',str(code/'owner_walk.py'),str(src),'--out',str(out)],cwd=run,env={**os.environ,'PYTHONPATH':''},stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
   self.assertEqual(proc.returncode,0,proc.stderr);self.assertEqual(src.read_bytes(),raw);self.assertTrue(out.exists())
   # Existing output is also refused by the actual CLI, not only helper calls.
   again=subprocess.run([sys.executable,'-B',str(code/'owner_walk.py'),str(src),'--out',str(src)],cwd=run,env={**os.environ,'PYTHONPATH':''},stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
   self.assertNotEqual(again.returncode,0);self.assertEqual(src.read_bytes(),raw)

if __name__=='__main__':unittest.main(verbosity=2)
