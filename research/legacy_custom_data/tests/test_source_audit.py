import importlib.util
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('source_audit',ROOT/'audit_source.py')
a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class SourceAuditTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)/'source';cls.root.mkdir()
  cls.raw=(ROOT/'SOURCE-MANIFEST.json').read_bytes();cls.digest=hashlib.sha256(cls.raw).hexdigest()
  manifest=json.loads(cls.raw);cls.members=manifest['files']
  for name in cls.members:
   dst=cls.root/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dst)
  (cls.root/'SOURCE-MANIFEST.json').write_bytes(cls.raw)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_exact_inventory(self):self.assertEqual(a.audit(self.root,self.digest)['source_inventory'],'PASS')
 def test_every_declared_source_or_report_tamper(self):
  for name in self.members:
   with self.subTest(name=name):
    path=self.root/name;original=path.read_bytes();path.write_bytes(original+b'\nTAMPER\n')
    try:
     with self.assertRaises(ValueError):a.audit(self.root,self.digest)
    finally:path.write_bytes(original)
 def test_extra_missing_symlink_external_manifest_anchor(self):
  extra=self.root/'src/injected.py';extra.write_text('x=1')
  with self.assertRaises(ValueError):a.audit(self.root,self.digest)
  extra.unlink()
  os.mkfifo(self.root/'src/fifo')
  with self.assertRaises(ValueError):a.audit(self.root,self.digest)
  (self.root/'src/fifo').unlink()
  application=self.root/'application';held=self.root/'application-holding'
  application.rename(held);application.symlink_to(ROOT/'application',target_is_directory=True)
  with self.assertRaises(ValueError):a.audit(self.root,self.digest)
  application.unlink();held.rename(application)
  path=self.root/'src/custom_data.py';raw=path.read_bytes();path.unlink()
  with self.assertRaises(ValueError):a.audit(self.root,self.digest)
  path.symlink_to(ROOT/'src/custom_data.py')
  with self.assertRaises(ValueError):a.audit(self.root,self.digest)
  path.unlink();path.write_bytes(raw)
  manifest=self.root/'SOURCE-MANIFEST.json';manifest.write_bytes(self.raw+b' ')
  with self.assertRaises(ValueError):a.audit(self.root,self.digest)
  manifest.write_bytes(self.raw)
  for raw in ('{"x":NaN}','{"x":1e999}','{"x":1,"x":1}'):
   with self.assertRaises(ValueError):a.strict_json(raw)
if __name__=='__main__':unittest.main(verbosity=2)
