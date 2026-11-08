"""Synthetic safety gates; no private inputs needed. Every assert is unittest."""
from pathlib import Path
import copy,os,sys,json,tempfile,subprocess,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
import native_scalar_writer as n,verify_native_delta as v
from test_owner_walk import filedata as scan_filedata,layer,page,annotation,sparse
from test_native_binding import project
def filedata(extra_pages=(),**kwargs):
 graph=scan_filedata(**kwargs).split(b"\n",1)[1]+b"\0"
 return project(pages=[graph]+[p+b"\0" for p in extra_pages])

def fixture():
 b=filedata();inv=n.root.checked_root(b);c=inv['pages'][0]['layers'][0]['curves'][0];f=n.s.frame(b,c['offset']);r=bytearray(b)
 for pos,x in zip(f['mapping'][21:23],(232,3)):r[pos]=x
 return bytes(r)
SEL={'page':'Synthetic','layer':1,'field':'curve.line_width','curve':1,'x_selector':1,'y_selector':2,'plot_type':200}

def execute(b=None,sel=None,value=1500):
 b=fixture() if b is None else b;sel=SEL if sel is None else sel
 p=n.prepare(b,sel,value,expected_source_sha256=n.digest(b));r,m=n.apply(b,p,expected_source_sha256=n.digest(b),expected_plan_sha256=n.digest(n.canonical(p)))
 return b,p,r,m

class Writer(unittest.TestCase):
 def test_scalar_and_independent_restore(self):
  b,p,r,m=execute();self.assertEqual(v.verify(b,r,SEL,1000,1500)['semantic_delta'][0]['after'],1500)
  self.assertEqual(n.restore(r,m,expected_source_sha256=n.digest(b),expected_result_sha256=n.digest(r),expected_manifest_sha256=n.digest(n.canonical(m))),b)
 def test_four_classes(self):
  for sel,new in [(SEL,1500),({'page':'Synthetic','layer':1,'field':'annotation.font','annotation':'XB'},54),({'page':'Synthetic','layer':1,'field':'axis.tick_font','axis':'X','side':'near'},48),({'page':'Synthetic','layer':1,'field':'axis.line_width','axis':'X','side':'near'},1250)]:
   with self.subTest(field=sel['field']):b,p,r,m=execute(sel=sel,value=new);v.verify(b,r,sel,p['before_value'],new)
 def test_type200_width_not_enabled_for_unobserved_3683_profile(self):
  b=fixture().replace(b'4.3811 222',b'4.3683 132')
  with self.assertRaisesRegex(n.Rejected,'real type200 corpus'):execute(b)
 def test_unknown_units(self):
  with self.assertRaisesRegex(n.Rejected,'units'):n.prepare(fixture(),SEL,1500,expected_source_sha256=n.digest(fixture()),units='points')
 def test_unknown_version(self):
  b=fixture().replace(b'4.3811',b'4.9999')
  with self.assertRaisesRegex(n.Rejected,'version'):execute(b)
 def test_zero_mask_change(self):
  with self.assertRaisesRegex(n.Rejected,'zero-mask'):execute(value=256)
 def test_zero_rejected(self):
  with self.assertRaises(n.Rejected):execute(value=0)
 def test_same_value_rejected(self):
  with self.assertRaises(n.Rejected):execute(value=1000)
 def test_bool_not_integer(self):
  with self.assertRaises(n.Rejected):execute(value=True)
 def test_unknown_field(self):
  with self.assertRaises(n.Rejected):execute(sel=SEL|{'field':'data.value'})
 def test_unknown_selector_keys(self):
  with self.assertRaises(n.Rejected):execute(sel=SEL|{'offset':777})
 def test_wrong_selector(self):
  for k,x in [('curve',2),('layer',0),('x_selector',2),('y_selector',3),('plot_type',202)]:
   with self.subTest(key=k):
    with self.assertRaises(n.Rejected):execute(sel=SEL|{k:x})
 def test_wrong_line_type(self):
  b=filedata(layers=layer(kind=202))
  with self.assertRaisesRegex(n.Rejected,'type200'):execute(b,SEL|{'plot_type':202})
 def test_duplicate_page(self):
  b=filedata(extra_pages=[page()])
  with self.assertRaisesRegex(n.Rejected,'ambiguous page'):execute(b)
 def test_duplicate_named_title(self):
  b=filedata(layers=layer(annotations=annotation()+annotation()))
  with self.assertRaisesRegex(n.Rejected,'ambiguous named'):execute(b,{'page':'Synthetic','layer':1,'field':'annotation.font','annotation':'XB'},54)
 def test_opaque_title_rejected(self):
  b=filedata(layers=layer(annotations=annotation(encoded=True)))
  with self.assertRaisesRegex(n.Rejected,'opaque'):execute(b,{'page':'Synthetic','layer':1,'field':'annotation.font','annotation':'XB'},54)
 def test_incomplete_page_rejected(self):
  with self.assertRaisesRegex(n.Rejected,'incomplete'):execute(fixture()[:n.root.checked_root(fixture())['parsed_until']-1])
 def test_source_anchor(self):
  with self.assertRaisesRegex(n.Rejected,'anchor'):n.prepare(fixture(),SEL,1500,expected_source_sha256='0'*64)
 def test_source_changed_after_plan(self):
  b,p,r,m=execute();bad=b[:-1]+b'x'
  with self.assertRaises(n.Rejected):n.apply(bad,p,expected_source_sha256=n.digest(b),expected_plan_sha256=n.digest(n.canonical(p)))
 def test_plan_external_anchor_tamper(self):
  b,p,r,m=execute();q=copy.deepcopy(p);q['after_value']=1750
  with self.assertRaisesRegex(n.Rejected,'plan external anchor'):n.apply(b,q,expected_source_sha256=n.digest(b),expected_plan_sha256=n.digest(n.canonical(p)))
 def test_restamped_malicious_plan(self):
  b,p,r,m=execute();q=copy.deepcopy(p);q['literal_edits'][0]['offset']+=1
  with self.assertRaisesRegex(n.Rejected,'freshly derived'):n.apply(b,q,expected_source_sha256=n.digest(b),expected_plan_sha256=n.digest(n.canonical(q)))
 def test_restore_manifest_external_anchor(self):
  b,p,r,m=execute();bad=copy.deepcopy(m);bad['source_sha256']='0'*64
  with self.assertRaisesRegex(n.Rejected,'manifest external anchor'):n.restore(r,bad,expected_source_sha256=n.digest(b),expected_result_sha256=n.digest(r),expected_manifest_sha256=n.digest(n.canonical(m)))
 def test_restamped_manifest_wrong_external_source(self):
  b,p,r,m=execute();bad=copy.deepcopy(m);bad['source_sha256']='0'*64
  with self.assertRaisesRegex(n.Rejected,'source/result external'):n.restore(r,bad,expected_source_sha256=n.digest(b),expected_result_sha256=n.digest(r),expected_manifest_sha256=n.digest(n.canonical(bad)))
 def test_restore_tampered_result(self):
  b,p,r,m=execute()
  with self.assertRaisesRegex(n.Rejected,'result external anchor'):n.restore(r[:-1]+b'x',m,expected_source_sha256=n.digest(b),expected_result_sha256=n.digest(r),expected_manifest_sha256=n.digest(n.canonical(m)))
 def test_independent_verifier_wrong_other_byte(self):
  b,p,r,m=execute();bad=r[:-1]+b'x'
  with self.assertRaises(ValueError):v.verify(b,bad,SEL,1000,1500)
 def test_profile_header_mismatch(self):
  b=fixture().replace(b'CPYUA 4.3811 222',b'CPYUA 4.3268 195')
  with self.assertRaisesRegex(n.Rejected,'header/version'):execute(b)
 def test_changed_repeat_not_literal(self):
  # A repeated nonzero width low/high byte has no one-to-one source provenance.
  from unittest.mock import patch
  b=fixture();original=n.s.frame
  def masked(data,at):
   f=original(data,at)
   if len(f['raw'])==519 and f['raw'][0]==1:f['mapping'][21:23]=[None,None]
   return f
  with patch.object(n.s,'frame',masked):
   with self.assertRaisesRegex(n.Rejected,'literal provenance'):execute(b)

 def test_scan_only_graph_rejected(self):
  with self.assertRaisesRegex(n.Rejected,'sequential root'):execute(scan_filedata())
 def test_scan_function_is_never_called(self):
  from unittest.mock import patch
  with patch.object(n.w,'inventory',side_effect=AssertionError('scan forbidden')):execute()
 def test_unknown_tail_preserved(self):
  b,p,r,m=execute();end=n.root.checked_root(b)['parsed_until'];self.assertEqual(b[end:],r[end:]);self.assertEqual(b[end:],b'UNVALIDATED-TAIL')
 def test_graph_hidden_in_tail_is_not_selectable(self):
  b=fixture()+page('Hidden')
  with self.assertRaisesRegex(n.Rejected,'missing or ambiguous'):execute(b,SEL|{'page':'Hidden'})
 def test_bad_dataset_list_blocks_write(self):
  b=fixture();r=n.root.checked_root(b);at=r['dataset_envelope']['dataset_list_terminator']['start'];bad=b[:at]+b'X'+b[at+1:]
  with self.assertRaisesRegex(n.Rejected,'sequential root'):execute(bad)

class InputProtection(unittest.TestCase):
 def test_strict_json_duplicate(self):
  with self.assertRaises(n.Rejected):n.strict_json(b'{"a":1,"a":2}')
 def test_strict_json_nonfinite(self):
  for text in (b'{"x":NaN}',b'{"x":Infinity}',b'{"x":-Infinity}',b'{"x":1e309}',b'{"x":1.25}'):
   with self.assertRaises(n.Rejected):n.strict_json(text)
 def test_strict_json_oversize(self):
  with self.assertRaises(n.Rejected):n.strict_json(b' '*65537)
 def test_fifo_nonblocking_reject(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'fifo';os.mkfifo(p)
   with self.assertRaisesRegex(n.Rejected,'regular'):n.bounded_regular(p,1024)
 def test_directory_reject(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(n.Rejected,'regular'):n.bounded_regular(d,1024)
 def test_symlink_reject(self):
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'real';src.write_bytes(b'ok');p=Path(d)/'alias';p.symlink_to(src)
   with self.assertRaisesRegex(n.Rejected,'symlink'):n.bounded_regular(p,1024)
 def test_oversize_before_read(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'huge';p.write_bytes(b'123')
   with self.assertRaisesRegex(n.Rejected,'bounded'):n.bounded_regular(p,2)
 def test_cli_no_source_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'source';b=fixture();p.write_bytes(b)
   r=subprocess.run([sys.executable,str(Path(n.__file__)), 'plan',str(p),'--out',str(p),'--source-sha256',n.digest(b),'--selector',json.dumps(SEL),'--value','1500'],capture_output=True,timeout=5)
   self.assertNotEqual(r.returncode,0);self.assertEqual(p.read_bytes(),b)
 def test_cli_fifo_plan_reject_without_output(self):
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'source';b=fixture();src.write_bytes(b);p=Path(d)/'fifo';os.mkfifo(p);out=Path(d)/'out'
   r=subprocess.run([sys.executable,str(Path(n.__file__)),'apply',str(src),'--out',str(out),'--source-sha256',n.digest(b),'--plan',str(p),'--plan-sha256','0'*64],capture_output=True,timeout=5)
   self.assertNotEqual(r.returncode,0);self.assertFalse(out.exists());self.assertEqual(src.read_bytes(),b)

if __name__=='__main__':unittest.main(verbosity=2)
