"""Adversarial checks on actual-app evidence. Existing run is read-only."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('observe_verify',ROOT/'application/verify_observation.py')
v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
c=v.c
BUNDLE=ROOT/'runs/custom50'
ANCHORS={'expected_csv_sha256':'fe668293f9efbc5591636554489d49cb1b377ef993b218a70b04d4d0aa92afc0','expected_declaration_sha256':'7bd4af26d0aa4aae07923741d7e990c3238a94ae5a6dc950db17a58d23d0d6e1','research_opt_in':True}
class ObservationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)/'observation'
  shutil.copytree(ROOT/'application/results50',cls.root)
  for snapshot in cls.root.glob('*/source-evidence.opj'):snapshot.chmod(0o600)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def verify(self):return v.verify(BUNDLE,self.root,**ANCHORS)
 def changed(self,relative,data):
  path=self.root/relative;original=path.read_bytes()
  try:
   path.write_bytes(data)
   with self.assertRaises(Exception):self.verify()
  finally:path.write_bytes(original)
 def test_genuine_current_run(self):self.assertEqual(self.verify()['status'],'PASS')
 def test_every_observed_API_cell(self):
  raw=(self.root/'custom/Book1/native-app-values.tsv').read_text();lines=raw.splitlines()
  for i in range(1,len(lines)):
   bad=list(lines);row=bad[i].split('\t');row[2]=('f' if row[2][0]!='f' else '0')+row[2][1:];bad[i]='\t'.join(row)
   self.changed('custom/Book1/native-app-values.tsv',('\n'.join(bad)+'\n').encode())
 def test_every_curve_row_and_logical_point(self):
  raw=(self.root/'custom/curve-observation.json').read_bytes()
  for field in ('x_bits','y_bits'):
   for row in range(50):
    obj=json.loads(raw);obj['rows'][row][field]='ffffffffffffffff'
    self.changed('custom/curve-observation.json',c.json_bytes(obj))
  for column in range(2):
   for row in range(50):
    obj=json.loads(raw);obj['point_signal_emissions'][0]['logical_points_binary64'][row][column]='ffffffffffffffff'
    self.changed('custom/curve-observation.json',c.json_bytes(obj))
 def test_runtime_receipt_source_hashes_saved_payloads(self):
  for name in ('run-receipt.json','original/source-evidence.opj','custom/source-evidence.opj','original/input.before.sha256','original/input.after.sha256','custom/input.before.sha256','custom/input.after.sha256','original/exit-status.txt','custom/exit-status.txt','original/imported-application.lml','custom/imported-application.lml'):
   raw=bytearray((self.root/name).read_bytes());raw[len(raw)//2]^=1;self.changed(name,bytes(raw))
  for kind in ('runtime_sha256','observer_sha256','unknown'):
   obj=json.loads((self.root/'run-receipt.json').read_bytes());obj[kind]='wrong'
   self.changed('run-receipt.json',c.json_bytes(obj))
 def test_duplicate_nonfinite_and_bool_row(self):
  for raw in (b'{"x":1,"x":1}',b'{"x":NaN}',b'{"x":1e999}'):
   self.changed('custom/curve-observation.json',raw);self.changed('run-receipt.json',raw)
  obj=json.loads((self.root/'custom/curve-observation.json').read_bytes());obj['rows'][0]['row']=False
  self.changed('custom/curve-observation.json',c.json_bytes(obj))
if __name__=='__main__':unittest.main(verbosity=2)
