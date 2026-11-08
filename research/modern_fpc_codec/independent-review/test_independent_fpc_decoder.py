import unittest
from independent_fpc_decoder import (decode_prefix, decode_strict, DecodeError,
                                     MAX_VALUES, MAX_INPUT_BYTES)


class SpecFixtures(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(decode_strict(b'', 0), [])
        self.assertEqual(decode_prefix(b'tail', 0), ([], 0))

    def test_width_codes(self):
        # One first value: both tables and last are zero, so value=residual.
        for code, width in enumerate((0, 1, 2, 3, 5, 6, 7, 8)):
            for selector in (0, 8):
                residual = bytes(range(1, width + 1))
                data = bytes([0xf0 | selector | code]) + residual
                expected = sum(byte << (8 * i) for i, byte in enumerate(residual))
                self.assertEqual(decode_strict(data, 1), [expected])

    def test_fcm_reuses_previous_cell(self):
        # 1 leaves fhash zero; second FCM zero residual predicts 1.
        self.assertEqual(decode_strict(bytes.fromhex('01 01'), 2), [1, 1])

    def test_dfcm_stride_and_pair_order(self):
        # First value 1 sets D[0]=1, dhash remains zero. Next DFCM predicts 2.
        # Third DFCM predicts 3, with odd unused high nibble set to 15.
        self.assertEqual(decode_strict(bytes.fromhex('81 01 f8'), 3), [1, 2, 3])

    def test_dfcm_wraparound(self):
        # FCM value 2^63 sets dhash=0: (stride>>40)&4095 = 0.
        # Next DFCM predicts (2^63+2^63) mod 2^64 = 0.
        self.assertEqual(decode_strict(bytes.fromhex('87 0000000000000080'), 2),
                         [1 << 63, 0])

    def test_negative_stride_bits(self):
        # After first max value dhash=4095 points to zero, so DFCM predicts max.
        # XOR 1 makes max-1; the stride is max modulo 2^64.
        self.assertEqual(decode_strict(bytes.fromhex('97 ffffffffffffffff 01'), 2),
                         [(1 << 64) - 1, (1 << 64) - 2])

    def test_fcm_hash_cell(self):
        # First 2^48 updates T[0], fhash becomes 1. T[1] predicts zero next.
        # Zero sets fhash=64. T[64] also starts at zero.
        self.assertEqual(decode_strict(bytes.fromhex('06 00000000000001 00'), 3),
                         [1 << 48, 0, 0])

    def test_prefix_and_strict(self):
        self.assertEqual(decode_prefix(bytes.fromhex('81 01 f8') + b'tail', 3),
                         ([1, 2, 3], 3))
        with self.assertRaises(DecodeError):
            decode_strict(bytes.fromhex('81 01 f8') + b'tail', 3)
        with self.assertRaises(DecodeError):
            decode_strict(b'\x00', 0)

    def test_every_truncation(self):
        data = bytes.fromhex('77 0102030405060708 1122334455667788 07 9988776655443322')
        self.assertEqual(decode_prefix(data, 3)[1], len(data))
        for length in range(len(data)):
            with self.assertRaises(DecodeError):
                decode_strict(data[:length], 3)

    def test_sizes_types_and_fresh_state(self):
        for count in (-1, MAX_VALUES + 1):
            with self.assertRaises(DecodeError):
                decode_prefix(b'', count)
        for count in (True, 1.0, '1', None):
            with self.assertRaises(TypeError):
                decode_prefix(b'', count)
        for data in (bytearray(), memoryview(b''), '', None):
            with self.assertRaises(TypeError):
                decode_prefix(data, 0)
        with self.assertRaises(DecodeError):
            decode_prefix(b'\0' * (MAX_INPUT_BYTES + 1), 0)
        self.assertEqual(decode_strict(bytes.fromhex('01 01'), 1), [1])
        self.assertEqual(decode_strict(b'\0', 1), [0])


if __name__ == '__main__':
    unittest.main()
