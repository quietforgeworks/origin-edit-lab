"""Portable regression tests for exact-budget boundaries, not native acceptance."""
import unittest
from unittest import mock

from test_exact_budget import (ExperimentalFPCError, UnreachableBudgetError,
    analyze_exact_budgets, encode_bits_exact_budget, baseline, independent,
    packed, SENTINEL)
import experimental_exact_fpc as target


class RevisionContractTests(unittest.TestCase):
    def test_opaque_subclasses_and_noninteger_limits_rejected(self):
        class ByteSubclass(bytes):
            pass
        class IntSubclass(int):
            pass
        for raw in (ByteSubclass(bytes(8)), bytearray(8), memoryview(bytes(8))):
            with self.assertRaises(ExperimentalFPCError):
                analyze_exact_budgets(raw)
            with self.assertRaises(ExperimentalFPCError):
                encode_bits_exact_budget(raw, 1)
        for key in ('budget_bytes', 'max_values', 'max_output_bytes'):
            for bad in (IntSubclass(1), True, False, 1.0):
                kwargs = dict(budget_bytes=1)
                kwargs[key] = bad
                with self.assertRaises(ExperimentalFPCError):
                    encode_bits_exact_budget(bytes(8), **kwargs)

    def test_early_bounds_refused_before_predictor_scan(self):
        with mock.patch.object(target, '_scan', side_effect=RuntimeError('scan called')):
            cases = ((bytes(8), 0, {}), (bytes(8), 10, {}),
                     (bytes(8), 1, {'max_values': 0}),
                     (bytes(8), 1, {'max_output_bytes': 0}),
                     (b'\0', 1, {}), (b'', -1, {}))
            for raw, budget, kwargs in cases:
                with self.assertRaises(ExperimentalFPCError):
                    encode_bits_exact_budget(raw, budget, **kwargs)

    def test_known_nonminimal_bytes_are_residuals_not_padding(self):
        self.assertEqual(encode_bits_exact_budget(packed([0]), 6), b'\x04' + bytes(5))
        self.assertEqual(encode_bits_exact_budget(packed([0]), 9), b'\x07' + bytes(8))
        with self.assertRaises(UnreachableBudgetError):
            encode_bits_exact_budget(packed([0]), 5)
        self.assertEqual(encode_bits_exact_budget(packed([0, 0]), 5), b'\x31' + bytes(4))
        self.assertEqual(independent.decode_prefix(b'\x31' + bytes(4) + b'NEXT', 2), ([0, 0], 5))

    def test_float_edges_remain_exact_words_for_every_reachable_size(self):
        # No float conversion, including signaling NaN payloads and signed NaNs.
        words = [0, 1 << 63, 1, (1 << 52) - 1, 1 << 52,
                 0x7FEFFFFFFFFFFFFF, 0x7FF0000000000000,
                 0xFFF0000000000000, 0x7FF0000000000001,
                 0xFFF0000000000001, 0x7FF8123456789ABC,
                 0xFFF8FEDCBA987654, SENTINEL]
        raw = packed(words)
        info = analyze_exact_budgets(raw)
        for low, high in info.reachable_intervals:
            for budget in range(low, high + 1):
                wire = encode_bits_exact_budget(raw, budget)
                self.assertEqual(len(wire), budget)
                self.assertEqual(baseline.decode_bits(wire, len(words)), (raw, budget))
                self.assertEqual(independent.decode_strict(wire, len(words)), words)

    def test_all_truncations_and_appended_bytes_refused_with_known_count(self):
        words = [0, 0x7FF0000000000001, SENTINEL, 1 << 63, 0]
        raw = packed(words)
        info = analyze_exact_budgets(raw)
        for budget in (info.minimum_bytes, info.maximum_bytes):
            wire = encode_bits_exact_budget(raw, budget)
            for cut in range(len(wire)):
                with self.assertRaises(baseline.FPCError):
                    baseline.decode_bits(wire[:cut], len(words))
                with self.assertRaises(independent.DecodeError):
                    independent.decode_strict(wire[:cut], len(words))
            for trailer in (b'\0', b'NEXT'):
                with self.assertRaises(baseline.FPCError):
                    baseline.decode_bits(wire + trailer, len(words))
                self.assertEqual(independent.decode_prefix(wire + trailer, len(words)),
                                 (words, budget))

    def test_extent_is_not_count_or_integrity_authentication(self):
        # Both trusted counts consume the same bytes. Native framing is separate.
        wire = encode_bits_exact_budget(packed([1, 1]), 2)
        self.assertEqual(wire, b'\x01\x01')
        self.assertEqual(independent.decode_strict(wire, 1), [1])
        self.assertEqual(independent.decode_strict(wire, 2), [1, 1])
        # A valid changed residual is accepted; no checksum is encoded here.
        self.assertEqual(independent.decode_strict(b'\x01\x02', 1), [2])
        # The encoder zeroes unused odd high nibbles; readers ignore them.
        self.assertEqual(independent.decode_strict(b'\xF1\x01', 1), [1])


if __name__ == '__main__':
    unittest.main()
