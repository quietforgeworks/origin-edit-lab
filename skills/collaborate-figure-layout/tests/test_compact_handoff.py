import copy,importlib.util,io,json,unittest,urllib.error,tempfile
from pathlib import Path
from unittest.mock import patch
import test_local_handoff as fixture
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('compact_cli',ROOT/'assets/local-handoff/assistant_layout.py')
cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)

class CompactHandoffTests(unittest.TestCase):
 def test_compact_snapshot_preserves_version_intent_and_raw_state(self):
  doc={'revision':8,'layout':{'guides':[{'pos':32}]},'confirmation':{'revision':8},'displayPreviews':{'a':{'sha256':'a'*64,'dataUrl':'data:image/png;base64,'+'A'*1000000}}}
  old=copy.deepcopy(doc);result=fixture.server.snapshot(doc)
  self.assertEqual(doc,old);self.assertEqual(result['layout'],doc['layout']);self.assertEqual(result['confirmation'],doc['confirmation'])
  self.assertLess(len(json.dumps(result)),500);self.assertEqual(result,cli.compact(doc))
  self.assertEqual(fixture.server.snapshot(doc,True),doc)
 def test_legacy_summary_404_falls_back_and_filters_without_mutation(self):
  error=urllib.error.HTTPError('http://127.0.0.1/api/state',404,'missing',{},io.BytesIO())
  state={'layout':{},'displayPreviews':{'a':{'sha256':'hash','dataUrl':'large'}}}
  with patch.object(cli,'fetch',side_effect=[error,state]) as fetch:
   result=cli.read_state('http://127.0.0.1')
  self.assertEqual(fetch.call_count,2);self.assertNotIn('dataUrl',result['displayPreviews']['a']);self.assertIn('dataUrl',state['displayPreviews']['a'])
 def test_non_404_failure_is_not_silently_retried(self):
  error=urllib.error.HTTPError('http://127.0.0.1',403,'denied',{},io.BytesIO())
  with patch.object(cli,'fetch',side_effect=error) as fetch:
   with self.assertRaises(urllib.error.HTTPError):cli.read_state('http://127.0.0.1')
   self.assertEqual(fetch.call_count,1)
 def test_non_object_manifest_is_a_bounded_error(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'manifest.json';p.write_text('[]')
   with self.assertRaises(ValueError):cli.load(p)
 def test_invalid_response_is_not_treated_as_task_state(self):
  for response in [[],None,{'layout':[]}]:
   with self.assertRaises(ValueError):cli.verify_task(response,{'projectId':'p','mapHash':'h'})
 def test_include_previews_requests_full_state_once(self):
  with patch.object(cli,'fetch',return_value={'revision':1}) as fetch:
   cli.read_state('http://127.0.0.1',True)
   fetch.assert_called_once_with('http://127.0.0.1/api/state')
if __name__=='__main__':unittest.main()
