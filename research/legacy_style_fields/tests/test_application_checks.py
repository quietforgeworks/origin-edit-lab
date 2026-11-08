"""Regression checks for exact XML comparison and bounded source acceptance."""
import copy,os,sys,unittest
from pathlib import Path
import xml.etree.ElementTree as E
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import compare_application as app
import native_style_patch as patch
import verify_results as verify
import font_boundary_candidate as font

class ExactXMLTests(unittest.TestCase):
 def test_leading_text_space(self):self.assertTrue(app.diff(E.fromstring('<a> x</a>'),E.fromstring('<a>x</a>')))
 def test_trailing_text_space(self):self.assertTrue(app.diff(E.fromstring('<a>x </a>'),E.fromstring('<a>x</a>')))
 def test_leading_tail_space(self):self.assertTrue(app.diff(E.fromstring('<a><b/> x</a>'),E.fromstring('<a><b/>x</a>')))
 def test_trailing_tail_space(self):self.assertTrue(app.diff(E.fromstring('<a><b/>x </a>'),E.fromstring('<a><b/>x</a>')))
 def test_indentation_difference_detected(self):self.assertTrue(app.diff(E.fromstring('<a>\n<b/>\n</a>'),E.fromstring('<a><b/></a>')))
 def test_none_vs_empty_not_collapsed(self):
  a=E.Element('a');b=E.Element('a');b.text='';self.assertTrue(app.diff(a,b))
 def test_only_documented_volatile_attributes_ignored(self):self.assertEqual(app.diff(E.fromstring('<a uuid="1" creation_time="x"/>'),E.fromstring('<a uuid="2" creation_time="y"/>')),[])
 def test_other_attribute_change_detected(self):self.assertTrue(app.diff(E.fromstring('<a width="1"/>'),E.fromstring('<a width="2"/>')))

class SourceEvidenceTests(unittest.TestCase):
 def setUp(self):
  self.path=patch.PROFILES['single_axes']['path']
  if not self.path.is_file():self.skipTest('Optional exact public KDE fixture not materialized')
  self.source=self.path.read_bytes();self.candidate,self.manifest,*_=patch.patch(self.source,'single_axes','xb_tick_font',26)
 def test_exact_artifacts_accepted(self):verify.verify_source_candidate(self.source,self.candidate,self.manifest,'single_axes')
 def test_cache_tamper_rejected_even_with_updated_hash(self):
  inventory=patch.snapshot(self.source,'single_axes');off=inventory['known_cached_payloads'][0]['payload_record']+5+100
  changed=self.candidate[:off]+bytes([self.candidate[off]^1])+self.candidate[off+1:]
  m=copy.deepcopy(self.manifest);m['candidate_sha256']=patch.sha(changed)
  with self.assertRaises(patch.Rejected):verify.verify_source_candidate(self.source,changed,m,'single_axes')
 def test_false_manifest_preservation_rejected(self):
  m=copy.deepcopy(self.manifest);m['all_other_bytes_unchanged']=False
  with self.assertRaises(patch.Rejected):verify.verify_source_candidate(self.source,self.candidate,m,'single_axes')

class FontProbeGuardTests(unittest.TestCase):
 def test_wrong_source_rejected(self):
  with self.assertRaises(patch.Rejected):font.prepare(b'not a fixture')
 def test_wrong_type_rejected(self):
  with self.assertRaises(patch.Rejected):font.prepare('not bytes')
 def test_correct_size_wrong_hash_rejected(self):
  with self.assertRaises(patch.Rejected):font.prepare(bytes(font.SIZE))

class FontProbeFixtureTests(unittest.TestCase):
 def setUp(self):
  path=patch.BASE/'strings_testing.opj'
  if not path.is_file():self.skipTest('Optional exact public strings fixture not materialized')
  self.source=path.read_bytes()
 def test_exact_single_byte_and_rollback(self):
  candidate,m,restored=font.prepare(self.source)
  self.assertEqual(restored,self.source);self.assertEqual([i for i,(a,b) in enumerate(zip(candidate,self.source)) if a!=b],[font.OFFSET]);self.assertEqual(patch.sha(candidate),font.CANDIDATE_SHA256)
 def test_repatch_rejected(self):
  candidate,*_=font.prepare(self.source)
  with self.assertRaises(patch.Rejected):font.prepare(candidate)

if __name__=='__main__':unittest.main()
