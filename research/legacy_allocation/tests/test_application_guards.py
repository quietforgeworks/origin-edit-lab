import copy,sys,unittest,xml.etree.ElementTree as E
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from verify_application import diff

class XMLComparisonTests(unittest.TestCase):
 def test_identical(self):
  a=E.fromstring('<p><a>payload </a>tail</p>');self.assertEqual(diff(a,copy.deepcopy(a)),[])
 def test_leading_whitespace_preserved(self):
  self.assertTrue(diff(E.fromstring('<p>value</p>'),E.fromstring('<p> value</p>')))
 def test_trailing_whitespace_preserved(self):
  self.assertTrue(diff(E.fromstring('<p>value</p>'),E.fromstring('<p>value </p>')))
 def test_tail_whitespace_preserved(self):
  self.assertTrue(diff(E.fromstring('<p><a/>value</p>'),E.fromstring('<p><a/>value </p>')))
 def test_none_empty_not_normalized(self):
  a=E.Element('p');b=E.Element('p');b.text='';self.assertTrue(diff(a,b))
 def test_extra_children_detected(self):
  self.assertTrue(diff(E.fromstring('<p/>'),E.fromstring('<p><a/></p>')))
 def test_attribute_changes_detected(self):
  self.assertTrue(diff(E.fromstring('<p row="50"/>'),E.fromstring('<p row="51"/>')))
 def test_only_documented_metadata_excluded(self):
  self.assertEqual(diff(E.fromstring('<p uuid="a" creation_time="1"/>'),E.fromstring('<p uuid="b" creation_time="2"/>')),[])
  self.assertTrue(diff(E.fromstring('<p name="a"/>'),E.fromstring('<p name="b"/>')))

if __name__=='__main__':unittest.main(verbosity=2)
