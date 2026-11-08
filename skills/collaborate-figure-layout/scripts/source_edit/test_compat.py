"""Synthetic tests of the read-only snapshot helpers, never a native writer."""
import copy
import math
from pathlib import Path
import tempfile
import unittest
import compat


class CompatTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = {'workbooks': [{'name': 'B', 'sheets': [{'name': 'S', 'columns': [{'values': [1.0, None, 'Ω']}]}]}], 'graphs': ['protected']}
        self.edit = {'book': 'B', 'sheet': 'S', 'row': 0, 'col': 0, 'old': 1.0, 'new': 2.0}

    def test_only_expected_numeric_snapshot_changes(self):
        original = copy.deepcopy(self.snapshot)
        after = compat.apply_expected_edits(self.snapshot, [self.edit])
        self.assertEqual(original, self.snapshot)
        self.assertEqual(after['workbooks'][0]['sheets'][0]['columns'][0]['values'], [2.0, None, 'Ω'])
        self.assertFalse(compat.evaluate(self.snapshot, after, [self.edit], origin_reopened=True, source_unchanged=True)['compatibility_complete'])

    def test_old_value_duplicate_and_noop_guards(self):
        for edits in [[dict(self.edit, old=99)], [self.edit, self.edit], [dict(self.edit, new=1)], [dict(self.edit, new=math.nan)]]:
            with self.subTest(edits=edits), self.assertRaises(ValueError):
                compat.apply_expected_edits(self.snapshot, edits)

    def test_missing_and_extra_objects_are_not_discarded(self):
        self.assertTrue(compat.differences(self.snapshot, dict(self.snapshot, graphs=[])))
        self.assertTrue(compat.differences(self.snapshot, dict(self.snapshot, extra='object')))
        self.assertEqual(compat.normalize([math.nan, None, math.inf, '文字']), [{'$number': 'NaN'}, None, {'$number': '+Infinity'}, '文字'])

    def test_inspection_is_metadata_only(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'synthetic.opju'; source.write_bytes(b'CPYUA synthetic only')
            result = compat.inspect_file(source)
            self.assertFalse(result['parsed']); self.assertFalse(result['compatibility_complete'])
            self.assertFalse(result['origin_reopen_verified'])
            for output in [source, source.with_suffix('.opj')]:
                with self.assertRaises(ValueError): compat.validate_paths(source, output)
            output = Path(directory) / 'new.opju'; output.symlink_to(Path(directory) / 'absent')
            with self.assertRaises(ValueError): compat.validate_paths(source, output)


if __name__ == '__main__':
    unittest.main()
