"""Synthetic end-to-end CLI checks. No user sources or live Office/Origin needed."""
import tempfile
import unittest
from pathlib import Path

from smoke_pipeline import run_smoke


class PipelineTests(unittest.TestCase):
    def test_extract_guarded_edit_replace_and_protect(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'smoke'
            report = run_smoke(output)
            self.assertEqual(report['status'], 'passed')
            self.assertTrue(report['source_unchanged'])
            self.assertTrue(report['embedded_payloads_unchanged'])
            self.assertTrue(report['native_text_and_geometry_unchanged'])
            self.assertIn('not run', report['svg_rasterization'])
            self.assertEqual(report['powerpoint_open'], 'not run')
            self.assertTrue((output / 'preservation.json').is_file())
            with self.assertRaisesRegex(ValueError, 'new output directory'):
                run_smoke(output)


if __name__ == '__main__':
    unittest.main()
