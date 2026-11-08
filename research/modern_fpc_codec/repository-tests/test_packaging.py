"""Repository integration tests: recorded evidence is not an external rerun."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

PACKAGE = Path(__file__).resolve().parents[1]
REPOSITORY = PACKAGE.parents[1]
sys.path.insert(0, str(PACKAGE))
import verify_package as audit


class PackagingTests(unittest.TestCase):
    def test_current_source_inventory(self):
        self.assertTrue(audit.verify_inventory())

    def test_upstream_exact_selection(self):
        self.assertEqual(len(audit.verify_upstream()['retained_upstream_files']), 35)

    def test_optimized_report_exact_reconstruction(self):
        normal = (PACKAGE / 'results/public-corpus-normal.json').read_bytes()
        optimized = audit.reconstruct_optimized(normal)
        self.assertEqual([(i, x, y) for i, (x, y) in enumerate(zip(normal, optimized)) if x != y],
                         [(735, 48, 49)])
        self.assertEqual(json.loads(optimized)['optimize'], 1)

    def test_public_metadata_and_totals(self):
        self.assertEqual(audit.verify_corpus()['values'], 9949997)

    def test_external_synthetic_recorded_mode_agreement(self):
        normal = audit.load('results/external-synthetic-normal.json')
        optimized = audit.load('results/external-synthetic-optimized.json')
        self.assertEqual(normal.pop('optimize'), 0)
        self.assertEqual(optimized.pop('optimize'), 1)
        self.assertEqual(normal, optimized)

    def test_license_and_execution_boundaries(self):
        self.assertEqual((PACKAGE / 'LICENSE').read_bytes(), (REPOSITORY / 'LICENSE').read_bytes())
        integration = audit.load('INTEGRATION.json')
        for key in ('external_corpus_rerun_during_integration', 'external_runtime_executed_during_integration',
                    'native_application_run_during_integration', 'default_cli_changed',
                    'existing_dependencies_changed', 'new_third_party_executable_source_bundled'):
            self.assertIs(integration[key], False)
        deps = audit.load('evidence/dependencies.json')
        self.assertEqual(deps['container']['license'], 'Apache-2.0')
        self.assertEqual(deps['opju_codec']['license'], 'Apache-2.0')
        review = audit.load('evidence/independent-review.json')
        self.assertIn('not independent vendor-format provenance', review['specification_ancestry'])

    def test_source_only_privacy_boundaries(self):
        self.assertTrue(audit.verify_source_only())

    def test_root_inventory_and_checksum(self):
        manifest_path = REPOSITORY / 'SOURCE-PACKAGE-MANIFEST.json'
        manifest = json.loads(manifest_path.read_text())
        checksum = (REPOSITORY / 'SOURCE-PACKAGE-MANIFEST.json.sha256').read_text().split()[0]
        self.assertEqual(hashlib.sha256(manifest_path.read_bytes()).hexdigest(), checksum)
        self.assertEqual(manifest['file_count_excluding_this_manifest_and_its_checksum'], len(manifest['files']))
        self.assertEqual(manifest['bytes_excluding_this_manifest_and_its_checksum'],
                         sum(x['bytes'] for x in manifest['files']))
        for record in manifest['files']:
            audit.safe_relative(record['path'])
            data = (REPOSITORY / record['path']).read_bytes()
            self.assertEqual(len(data), record['bytes'], record['path'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), record['sha256'], record['path'])

    def test_corrupt_reconstruction_rejected(self):
        for value in (b'{}', b'{"optimize": 0}', b'"optimize": 0 "optimize": 0'):
            with self.assertRaises(ValueError):
                audit.reconstruct_optimized(value)

    def test_unsafe_inventory_paths_rejected(self):
        for path in ('', '/absolute', '../escape', 'a/../escape', 'a\\b', './relative'):
            with self.assertRaises(ValueError):
                audit.safe_relative(path)


if __name__ == '__main__':
    unittest.main()
