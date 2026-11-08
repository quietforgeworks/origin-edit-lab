"""Review-regression and fault-injection tests, only on local disposable files."""
from pathlib import Path
import ast
import copy
import errno
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import generate_native as g
import verify_native as v
import atomic_output as atomic
import csv_contract

HERE = Path(__file__).resolve().parent
SOURCE = HERE/'inputs/original-object90.ole.bin'
CSV = HERE/'inputs/synthetic-demo.csv'


@unittest.skipUnless(SOURCE.is_file(), 'Optional external Origin fixture not supplied')
class Revision2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.out = self.root/'result'
        self.source_hash = g.sha(SOURCE.read_bytes())

    def generate(self, data=None):
        input_path = CSV
        if data is not None:
            input_path = self.root/'input.csv'
            input_path.write_bytes(data)
        return g.generate(SOURCE, input_path, self.out)

    def assert_clean_failure(self):
        self.assertFalse(os.path.lexists(self.out))
        self.assertFalse(list(self.root.glob('.origin-native-partial-*')))
        self.assertEqual(g.sha(SOURCE.read_bytes()), self.source_hash)

    def tamper_native(self, update_inventory=False):
        self.generate()
        raw_path = self.out/'synthetic-demo.origin_payload'
        ole_path = self.out/'synthetic-demo.ole.bin'
        raw = bytearray(raw_path.read_bytes()); raw[13000] ^= 1
        ole = bytearray(ole_path.read_bytes())
        physical = g.AllocatedCFB(bytes(ole)).mapping('Contents', 13000, 1)[0][1]
        ole[physical] ^= 1
        raw_path.write_bytes(raw); ole_path.write_bytes(ole)
        if update_inventory:
            inventory_path = self.out/'artifacts.json'
            inventory = json.loads(inventory_path.read_text())
            for path in (raw_path, ole_path):
                inventory['files'][path.name] = {'sha256': g.sha(path.read_bytes()), 'bytes': path.stat().st_size}
            inventory_path.write_text(json.dumps(inventory))

    def run_verifier(self, optimized):
        flags = ['-B', '-O'] if optimized else ['-B']
        return subprocess.run([sys.executable, *flags, str(HERE/'verify_native.py'), str(SOURCE), str(self.out)], capture_output=True, text=True)

    def test_31_no_assert_statements_in_acceptance_gate(self):
        tree = ast.parse((HERE/'verify_native.py').read_text())
        self.assertFalse(any(isinstance(node, ast.Assert) for node in ast.walk(tree)))

    def test_32_normal_and_optimized_unknown_byte_tamper_refused(self):
        self.tamper_native()
        for optimized in (False, True):
            result = self.run_verifier(optimized)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('"status": "PASS"', result.stdout)
            self.assertIn('Artifact hash/size mismatch', result.stderr)

    def test_33_optimized_scope_check_not_only_inventory_hash(self):
        self.tamper_native(update_inventory=True)
        result = self.run_verifier(True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Changed native bytes escape', result.stderr)

    def test_34_optimized_valid_candidate_passes(self):
        self.generate()
        result = self.run_verifier(True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'PASS')

    def test_35_bom_roundtrip_passes_shared_strict_parser(self):
        data = b'\xef\xbb\xbf'+CSV.read_bytes()
        self.generate(data)
        self.assertEqual((self.out/'synthetic-demo.csv').read_bytes(), data)
        self.assertEqual(v.verify(SOURCE, self.out)['status'], 'PASS')
        self.assertEqual(self.run_verifier(True).returncode, 0)

    def test_36_large_constant_x_native_generation_has_no_preview_dependency(self):
        y = g.parse_csv(CSV.read_bytes())[1]
        data = ('x,y\n'+''.join(f'{2**54},{value}\n' for value in y)).encode()
        self.generate(data)
        self.assertEqual(v.verify(SOURCE, self.out)['status'], 'PASS')
        record = json.loads((self.out/'verification.json').read_text())
        self.assertEqual(record['column_evidence'][0]['input_values'], [float(2**54)]*9)
        self.assertFalse(list(self.out.glob('*.svg'))+list(self.out.glob('*.png')))
        self.assertFalse(hasattr(g, 'preview_svg'))

    def test_37_original_native_ole_hashes_unchanged(self):
        self.generate()
        self.assertEqual(g.sha((self.out/'synthetic-demo.origin_payload').read_bytes()), 'bf5b9fcf743ef1657040208ad0969fed13516d23b6a25cb58bdac2dae6cbfc98')
        self.assertEqual(g.sha((self.out/'synthetic-demo.ole.bin').read_bytes()), '86431bbeeb56d99f4bcc11b521780260d86a4f3fd8021ec3ec44dede376373dc')
        self.assertEqual(set(p.name for p in self.out.iterdir()), v.ARTIFACT_NAMES | {'artifacts.json'})

    def test_38_enospc_after_17_bytes_cleans_and_retry_works(self):
        real_open = Path.open
        class DiskFull:
            def __init__(self, file): self.file = file
            def __enter__(self): return self
            def __exit__(self, *args): self.file.close()
            def write(self, data):
                self.file.write(data[:17]); self.file.flush()
                raise OSError(errno.ENOSPC, 'Injected disk full')
        def open_fault(path, mode='r', *args, **kwargs):
            file = real_open(path, mode, *args, **kwargs)
            return DiskFull(file) if mode == 'xb' and path.name == 'synthetic-demo.origin_payload' else file
        with mock.patch.object(Path, 'open', open_fault):
            with self.assertRaises(atomic.PublicationError) as error: self.generate()
        self.assertFalse(error.exception.published)
        self.assertIsNone(error.exception.staging_path)
        self.assert_clean_failure()
        self.generate()
        self.assertEqual(v.verify(SOURCE, self.out)['status'], 'PASS')

    def test_39_short_write_is_not_success(self):
        real_open = Path.open
        class ShortWrite:
            def __init__(self, file): self.file = file
            def __enter__(self): return self
            def __exit__(self, *args): self.file.close()
            def write(self, data): return self.file.write(data[:17])
        def open_fault(path, mode='r', *args, **kwargs):
            file = real_open(path, mode, *args, **kwargs)
            return ShortWrite(file) if mode == 'xb' else file
        with mock.patch.object(Path, 'open', open_fault):
            with self.assertRaisesRegex(atomic.PublicationError, 'Short write'): self.generate()
        self.assert_clean_failure()

    def test_40_file_fsync_failure_cleans(self):
        with mock.patch.object(atomic.os, 'fsync', side_effect=OSError(errno.EIO, 'Injected fsync error')):
            with self.assertRaises(atomic.PublicationError): self.generate()
        self.assert_clean_failure()

    def test_41_publish_failure_cleans(self):
        with mock.patch.object(atomic, 'rename_noreplace', side_effect=OSError(errno.EIO, 'Injected publish failure')):
            with self.assertRaises(atomic.PublicationError): self.generate()
        self.assert_clean_failure()

    def test_42_existing_file_is_not_overwritten(self):
        self.out.write_bytes(b'preserve me')
        with self.assertRaises(ValueError): self.generate()
        self.assertEqual(self.out.read_bytes(), b'preserve me')
        self.assertFalse(list(self.root.glob('.origin-native-partial-*')))

    def test_43_existing_empty_directory_is_not_replaced(self):
        self.out.mkdir(); before = atomic.identity(self.out)
        with self.assertRaises(ValueError): self.generate()
        self.assertEqual(atomic.identity(self.out), before)
        self.assertEqual(list(self.out.iterdir()), [])

    def test_44_existing_dangling_symlink_is_not_replaced(self):
        self.out.symlink_to(self.root/'absent', target_is_directory=True)
        with self.assertRaises(ValueError): self.generate()
        self.assertTrue(self.out.is_symlink())
        self.assertFalse((self.root/'absent').exists())

    def race_destination(self, kind):
        real_rename = atomic.rename_noreplace
        def raced(source, destination, function):
            if kind == 'directory': destination.mkdir()
            elif kind == 'populated':
                destination.mkdir(); (destination/'sentinel').write_bytes(b'preserve')
            elif kind == 'symlink': destination.symlink_to(self.root/'absent', target_is_directory=True)
            elif kind == 'file': destination.write_bytes(b'preserve')
            return real_rename(source, destination, function)
        with mock.patch.object(atomic, 'rename_noreplace', raced):
            with self.assertRaises(atomic.PublicationError) as error: self.generate()
        self.assertFalse(error.exception.published)
        self.assertFalse(list(self.root.glob('.origin-native-partial-*')))

    def test_45_racing_empty_directory_not_overwritten(self):
        self.race_destination('directory')
        self.assertEqual(list(self.out.iterdir()), [])

    def test_46_racing_nonempty_directory_not_overwritten(self):
        self.race_destination('populated')
        self.assertEqual((self.out/'sentinel').read_bytes(), b'preserve')

    def test_47_racing_symlink_not_overwritten(self):
        self.race_destination('symlink')
        self.assertTrue(self.out.is_symlink())
        self.assertFalse((self.root/'absent').exists())

    def test_48_racing_file_not_overwritten(self):
        self.race_destination('file')
        self.assertEqual(self.out.read_bytes(), b'preserve')

    def test_49_post_publish_uncertainty_reconciled(self):
        real_rename = atomic.rename_noreplace
        def uncertain(source, destination, function):
            real_rename(source, destination, function)
            raise OSError(errno.EIO, 'Injected exception after successful rename')
        with mock.patch.object(atomic, 'rename_noreplace', uncertain):
            report = self.generate()
        self.assertTrue(report['publication']['published'])
        self.assertTrue(report['publication']['recovered_uncertain_publish'])
        self.assertEqual(v.verify(SOURCE, self.out)['status'], 'PASS')

    def test_50_post_publish_directory_fsync_discloses_complete_state(self):
        real_fsync = atomic.fsync_directory
        def fault(path):
            if Path(path) == self.root: raise OSError(errno.EIO, 'Injected parent directory fsync failure')
            real_fsync(path)
        with mock.patch.object(atomic, 'fsync_directory', fault):
            with self.assertRaises(atomic.PublicationError) as error: self.generate()
        self.assertTrue(error.exception.published)
        self.assertEqual(error.exception.final_path, str(self.out))
        self.assertIn('Complete candidate is published', str(error.exception))
        self.assertEqual(v.verify(SOURCE, self.out)['status'], 'PASS')

    def test_51_cleanup_failure_reports_hidden_partial_path(self):
        with mock.patch.object(atomic, 'rename_noreplace', side_effect=OSError(errno.EIO, 'Injected publication error')):
            with mock.patch.object(atomic.shutil, 'rmtree', side_effect=OSError(errno.EACCES, 'Injected cleanup error')):
                with self.assertRaises(atomic.PublicationError) as error: self.generate()
        self.assertFalse(error.exception.published)
        self.assertFalse(self.out.exists())
        path = Path(error.exception.staging_path)
        self.assertTrue(path.name.startswith('.origin-native-partial-'))
        self.assertEqual(path.parent, self.root)
        self.assertTrue(path.exists())
        shutil.rmtree(path)

    def test_52_staged_artifact_not_visible_before_publish(self):
        real_rename = atomic.rename_noreplace
        def inspect(source, destination, function):
            self.assertFalse(os.path.lexists(destination))
            self.assertTrue(source.name.startswith('.origin-native-partial-'))
            self.assertEqual(v.verify(SOURCE, source)['status'], 'PASS')
            real_rename(source, destination, function)
        with mock.patch.object(atomic, 'rename_noreplace', inspect): self.generate()
        self.assertEqual(v.verify(SOURCE, self.out)['status'], 'PASS')

    def test_53_unsupported_atomic_primitive_refuses_without_staging(self):
        with mock.patch.object(atomic, 'load_rename_noreplace', side_effect=atomic.PublicationError('Unsupported', final_path=self.out)):
            with self.assertRaises(atomic.PublicationError): self.generate()
        self.assert_clean_failure()

    def test_54_csv_size_bound_applies_to_actual_read(self):
        data = self.root/'large.csv'; data.write_bytes(b'x'*20000)
        with self.assertRaisesRegex(ValueError, 'exceeds 16384'): g.generate(SOURCE, data, self.out)
        self.assert_clean_failure()

    def test_55_signed_zero_full_roundtrip(self):
        self.generate(CSV.read_bytes().replace(b'2,25', b'-0,25'))
        self.assertEqual(v.verify(SOURCE, self.out)['status'], 'PASS')
        report = json.loads((self.out/'verification.json').read_text())
        self.assertEqual(report['column_evidence'][0]['output_binary64_hex'][0], '8000000000000000')

    def test_56_verifier_uses_same_parser(self):
        self.assertIs(g.parse_csv, csv_contract.parse_csv)
        self.assertIs(v.parse_csv, csv_contract.parse_csv)

    def test_57_incomplete_or_extra_artifacts_refused(self):
        self.generate()
        (self.out/'unexpected').write_bytes(b'extra')
        with self.assertRaisesRegex(ValueError, 'inventory'): v.verify(SOURCE, self.out)
        (self.out/'unexpected').unlink()
        (self.out/'artifacts.json').unlink()
        with self.assertRaisesRegex(ValueError, 'inventory'): v.verify(SOURCE, self.out)

    def test_58_artifact_symlink_refused(self):
        self.generate()
        path = self.out/'synthetic-demo.csv'; saved = self.root/'saved.csv'
        path.rename(saved); path.symlink_to(saved)
        with self.assertRaisesRegex(ValueError, 'nonsymlink'): v.verify(SOURCE, self.out)


if __name__ == '__main__':
    unittest.main(verbosity=2)
