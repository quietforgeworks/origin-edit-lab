"""Source-only publication checks, independent of optional native/app evidence."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PackagingTests(unittest.TestCase):
    def test_frozen_multicurve_scientific_sources(self):
        root = ROOT / 'legacy_multicurve'
        manifest = json.loads((root / 'PACKAGE-INVENTORY.json').read_bytes())
        for item in manifest['files']:
            if Path(item['path']).suffix in ('.py', '.cpp', '.sh', '.inc'):
                self.assertEqual(hashlib.sha256((root / item['path']).read_bytes()).hexdigest(), item['sha256'], item['path'])

    def test_frozen_custom_scientific_sources(self):
        root = ROOT / 'legacy_custom_data'
        manifest = json.loads((root / 'review/HISTORICAL-SOURCE-MANIFEST.json').read_bytes())
        for name, item in manifest['files'].items():
            if Path(name).suffix in ('.py', '.cpp', '.sh', '.inc'):
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), item['sha256'], name)

    def test_historical_manifest_external_hashes(self):
        for name, expected in (
            ('legacy_multicurve/PACKAGE-INVENTORY.json', 'f6548e6f35769fd9884bf2a86020ee1de5c8f51b5bf694a2c64e3e3dd64e08f1'),
            ('legacy_custom_data/review/HISTORICAL-SOURCE-MANIFEST.json', '3b56217e1b537a61bcc6726b7110114bde0ecfe40d83fc0acb48000b6ef94645')):
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected)

    def test_current_custom_source_audit(self):
        root = ROOT / 'legacy_custom_data'
        audit = load('package_custom_audit', root / 'audit_source.py')
        digest = (root / 'SOURCE-MANIFEST.json.sha256').read_text().split()[0]
        self.assertEqual(audit.audit(root, digest)['source_inventory'], 'PASS')

    def test_current_multicurve_inventory(self):
        root = ROOT / 'legacy_multicurve'
        manifest = json.loads((root / 'CURRENT-INVENTORY.json').read_bytes())
        for item in manifest['files']:
            data = (root / item['path']).read_bytes()
            self.assertEqual(len(data), item['bytes'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), item['sha256'], item['path'])

    def test_every_synthetic_example_regenerates(self):
        verifier = load('package_provenance', ROOT / 'verify_native_data_provenance.py')
        result = verifier.verify()
        self.assertEqual(len(result['cases']), 6)
        self.assertTrue(all(c['synthetic_regeneration'] == 'PASS' for c in result['cases']))
        self.assertEqual(result['application_rerun'], 'NOT_RUN')

    def test_all_compact_evidence_matches_provenance_matrix(self):
        matrix = json.loads((ROOT / 'NATIVE-DATA-PROVENANCE.json').read_bytes())
        cases = {case['case'] for case in matrix['cases']}
        for item in matrix['evidence_files']:
            self.assertEqual(hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest(), item['sha256'], item['path'])
            self.assertTrue(set(item['related_cases']) <= cases)

    def test_measured_declaration_is_only_schema_example(self):
        root = ROOT / 'legacy_custom_data'
        adapter = load('package_custom_decl', root / 'src/custom_data.py')
        example = adapter.declaration((root / 'inputs/measured-declaration-example.json').read_bytes())
        self.assertEqual(example['declared_kind'], 'measured')
        self.assertIn('not independently verified', example['statement'])
        for n in (7, 49, 50):
            report = json.loads((root / f'evidence/generation-custom{n}.json').read_bytes())
            self.assertEqual(report['input_provenance']['caller_declaration']['declared_kind'], 'synthetic')
            self.assertEqual(report['output'], f'runs/custom{n}')

    def test_missing_external_input_skips_only_if_not_selected(self):
        bridge = load('package_bridge', ROOT / 'run_native_data_tests.py')
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(bridge.external('CUSTOM_TEMPLATE'))
            with patch.dict(os.environ, {'CUSTOM_TEMPLATE': ''}):
                with self.assertRaises(ValueError): bridge.external('CUSTOM_TEMPLATE')
            with tempfile.TemporaryDirectory() as d:
                with patch.dict(os.environ, {'CUSTOM_TEMPLATE': str(Path(d) / 'missing')}):
                    with self.assertRaises(ValueError): bridge.external('CUSTOM_TEMPLATE')
                with patch.dict(os.environ, {'CUSTOM_TEMPLATE': d}):
                    with self.assertRaises(ValueError): bridge.external('CUSTOM_TEMPLATE')

    def test_no_opt_in_means_no_source_io(self):
        adapter = load('package_custom_refusal', ROOT / 'legacy_custom_data/src/custom_data.py')
        with patch.object(adapter, 'read_file', side_effect=AssertionError('unexpected input read')):
            for flag in (False, None, 0, 1, 'yes'):
                with self.assertRaises(adapter.Rejected):
                    adapter.expected_artifacts(None, None, None, research_opt_in=flag)
                with self.assertRaises(adapter.Rejected):
                    adapter.verify(None, expected_csv_sha256=None, expected_declaration_sha256=None, research_opt_in=flag)


if __name__ == '__main__':
    unittest.main(verbosity=2)
