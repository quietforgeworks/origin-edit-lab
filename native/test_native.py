"""Positive, preservation, refusal and output-safety tests for one exact template."""
from pathlib import Path
import copy
import json
import math
import struct
import tempfile
import unittest

import generate_native as g
import verify_native as verifier


HERE = Path(__file__).resolve().parent


@unittest.skipUnless((HERE/'inputs/original-object90.ole.bin').is_file(), 'Optional external Origin fixture not supplied; native application compatibility is unverified')
class NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (HERE/'inputs/original-object90.ole.bin').read_bytes()
        cls.csv = (HERE/'inputs/synthetic-demo.csv').read_bytes()
        cls.columns = g.parse_csv(cls.csv)
        cls.native, cls.ole, cls.nd, cls.od, cls.report = g.build_native(cls.source, cls.columns)
        cls.before = g.AllocatedCFB(cls.source)
        cls.after = g.AllocatedCFB(cls.ole)

    def test_01_source_template_identity(self):
        self.assertEqual(g.sha(self.source), g.SOURCE_CFB_SHA)
        self.assertEqual(g.sha(self.before.read_stream('Contents')), g.SOURCE_NATIVE_SHA)

    def test_02_all_input_values_recovered_by_both_decoders(self):
        for c, wanted in zip(self.report['column_evidence'], self.columns):
            actual, _ = g.opju_codec._decode_record(self.native, c['ff_offset'])
            self.assertEqual([struct.pack('<d', float(v)) for v in actual], [struct.pack('<d', v) for v in wanted])
            direct, _, _ = g.parse_record(self.native, c['ff_offset'])
            self.assertEqual(direct, [g.numeric_bits(v) for v in wanted])

    def test_03_only_real_residual_bytes_changed(self):
        self.assertEqual(len(self.native), 13662)
        self.assertEqual(len(self.ole), len(self.source))
        allowed = {i for o, n in self.report['permitted_residual_spans'] for i in range(o, o+n)}
        old = self.before.read_stream('Contents')
        self.assertTrue(set(self.report['native_changed_offsets']) <= allowed)
        for i, (a, b) in enumerate(zip(old, self.native)):
            if i not in allowed: self.assertEqual(a, b)

    def test_04_positive_zero_is_preserved_as_zero_not_missing(self):
        self.assertEqual(self.report['column_evidence'][1]['before_values'][-1], 0.0)
        self.assertEqual(self.report['column_evidence'][1]['output_binary64_hex'][-1], '0000000000000000')
        self.assertEqual(self.report['column_evidence'][0]['input_values'][0], 2.0)

    def test_05_other_streams_allocation_cache_unchanged(self):
        self.assertEqual(self.before.streams, self.after.streams)
        self.assertEqual(self.before.physical_owners, self.after.physical_owners)
        self.assertEqual(self.before.mini_owners, self.after.mini_owners)
        for path in self.before.streams:
            if path != ('Contents',): self.assertEqual(self.before.read_stream(path), self.after.read_stream(path))

    def test_06_graph_selectors_and_dataset_metadata_unchanged(self):
        old = g.read_modern_xy_bindings(self.before.read_stream('Contents'))
        new = g._read_modern_xy_bindings_unscoped(self.native)
        self.assertEqual(g.snapshot_without_values(old), g.snapshot_without_values(new))

    def test_07_both_artifacts_restore_exactly(self):
        self.assertEqual(g.restore_delta(self.native, self.nd), self.before.read_stream('Contents'))
        self.assertEqual(g.restore_delta(self.ole, self.od), self.source)

    def test_08_acceptance_and_stale_cache_honestly_labeled(self):
        self.assertFalse(self.report['cached_preview_matches_candidate_data'])
        self.assertFalse(self.report['original_smooth_curve_recalculated'])
        self.assertFalse(self.report['full_standalone_OPJU'])
        self.assertFalse(self.report['worksheet_row_alignment_verified'])
        self.assertEqual(self.report['Origin_reopen_save'], 'NOT RUN')

    def test_09_wrong_source_hash_refused(self):
        for b in (self.ole, self.source[:-1], self.source+b'\0'):
            with self.assertRaises(ValueError): g.build_native(b, self.columns)

    def test_10_mutable_source_refused(self):
        with self.assertRaises(ValueError): g.build_native(bytearray(self.source), self.columns)

    def test_11_changed_row_count_refused(self):
        for n in (0, 1, 8, 10, 100):
            with self.assertRaises(ValueError): g.build_native(self.source, [[1]*n, [1]*n])

    def test_12_column_count_refused(self):
        for c in ([], [self.columns[0]], self.columns*2):
            with self.assertRaises(ValueError): g.build_native(self.source, c)

    def test_13_nonfinite_missing_bool_types_refused(self):
        for value in (None, True, False, '3', float('nan'), float('inf'), -float('inf'), g.ORIGIN_MISSING):
            c = copy.deepcopy(self.columns); c[0][0] = value
            with self.assertRaises(ValueError): g.build_native(self.source, c)

    def test_14_large_integer_precision_loss_refused(self):
        with self.assertRaises(ValueError): g.numeric_bits(2**53+1)

    def test_15_noop_refused(self):
        c = [x['stored_values'] for x in g.read_modern_embedded_numeric(self.before.read_stream('Contents'))['columns']]
        with self.assertRaisesRegex(ValueError, 'No-op'): g.build_native(self.source, c)

    def test_16_unencodable_ordinary_data_refused(self):
        c = copy.deepcopy(self.columns); c[1] = [0,10,25,35,30,20,10,5,0]
        with self.assertRaisesRegex(ValueError, 'residual exceeds'): g.build_native(self.source, c)

    def test_17_csv_blank_missing_non_numeric_refused(self):
        for token in ('', 'NaN', 'nan', 'NA', '--', 'inf', 'Infinity', 'True', '=1+1'):
            with self.assertRaises(ValueError): g.parse_csv(self.csv.replace(b'2,25', f'{token},25'.encode()))

    def test_18_csv_shape_and_header_refused(self):
        for data in (self.csv.replace(b'x,y', b'X,Y'), self.csv+b'1,2\n', self.csv.replace(b'40,0\n', b''), self.csv.replace(b'2,25', b'2,25,3')):
            with self.assertRaises(ValueError): g.parse_csv(data)

    def test_19_csv_overflow_underflow_magnitude_refused(self):
        for token in ('1e999', '-1e999', '1e-999', '1e-291', '1e291'):
            with self.assertRaises(ValueError): g.parse_csv(self.csv.replace(b'2,25', f'{token},25'.encode()))

    def test_20_csv_signed_zero_not_silently_normalized(self):
        c = g.parse_csv(self.csv.replace(b'2,25', b'-0,25'))
        self.assertEqual(struct.pack('<d', c[0][0]).hex(), '0000000000000080')

    def test_21_csv_bom_scientific_notation(self):
        self.assertEqual(g.parse_csv(b'\xef\xbb\xbf'+self.csv.replace(b'5,55', b'5e0,5.5e1')), self.columns)

    def test_22_csv_size_and_encoding_refused(self):
        for data in (b'a'*16385, b'\xff'+self.csv):
            with self.assertRaises(ValueError): g.parse_csv(data)

    def test_23_in_memory_failure_does_not_modify_source(self):
        initial = bytes(self.source)
        c = copy.deepcopy(self.columns); c[1][8] = 1234567
        with self.assertRaises(ValueError): g.build_native(self.source, c)
        self.assertEqual(self.source, initial)

    def test_24_original_and_twofold_y_accepted(self):
        c = [x['stored_values'][:] for x in g.read_modern_embedded_numeric(self.before.read_stream('Contents'))['columns']]
        c[1] = [2*v for v in c[1]]
        raw, _, _, _, report = g.build_native(self.source, c)
        self.assertNotEqual(raw, self.native)
        self.assertEqual(report['column_evidence'][1]['input_values'][-1], 0.0)

    def test_25_output_directory_exclusive_create(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, 'must be new'):
                g.generate(HERE/'inputs/original-object90.ole.bin', HERE/'inputs/synthetic-demo.csv', Path(td))

    def test_26_rejected_generation_writes_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td); bad = td/'bad.csv'; bad.write_bytes(self.csv.replace(b'2,25', b'NaN,25')); out = td/'output'
            with self.assertRaises(ValueError): g.generate(HERE/'inputs/original-object90.ole.bin', bad, out)
            self.assertFalse(out.exists())

    def test_27_symlink_output_refused(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td); link = td/'output'; link.symlink_to(td/'absent', target_is_directory=True)
            with self.assertRaises(ValueError): g.generate(HERE/'inputs/original-object90.ole.bin', HERE/'inputs/synthetic-demo.csv', link)
            self.assertFalse((td/'absent').exists())

    def test_28_separate_verifier_on_fresh_generation(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)/'out'
            g.generate(HERE/'inputs/original-object90.ole.bin', HERE/'inputs/synthetic-demo.csv', out)
            self.assertEqual(verifier.verify(HERE/'inputs/original-object90.ole.bin', out)['status'], 'PASS')

    def test_29_manifest_tampering_refused(self):
        d = copy.deepcopy(self.nd); d['result_sha256'] = '0'*64
        with self.assertRaises(ValueError): g.restore_delta(self.native, d)

    def test_30_generated_artifact_is_not_opju(self):
        self.assertTrue(self.native.startswith(b'CPYUA 4.3268 195\n'))
        self.assertTrue(self.ole.startswith(bytes.fromhex('d0cf11e0a1b11ae1')))
        self.assertFalse(list((HERE/'generated-demo').glob('*.opju')))


if __name__ == '__main__':
    unittest.main(verbosity=2)
