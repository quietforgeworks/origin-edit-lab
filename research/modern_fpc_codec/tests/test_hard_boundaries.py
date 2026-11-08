"""Real hard-cap boundary test, no floating point or external dependency."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code'))
from fpc_numeric import encode_bits, decode_bits, FPCError, MAX_VALUES, MAX_RAW_BYTES, MAX_STREAM_BYTES

class BoundaryTests(unittest.TestCase):
    def test_one_million_values_and_rejection_above(self):
        raw = bytes(MAX_RAW_BYTES)
        wire = encode_bits(raw)
        self.assertEqual(wire, bytes((MAX_VALUES + 1) // 2))
        self.assertEqual(decode_bits(wire, MAX_VALUES), (raw, len(wire)))
        for f in (lambda: encode_bits(raw + bytes(8)),
                  lambda: decode_bits(wire, MAX_VALUES + 1),
                  lambda: decode_bits(bytes(MAX_STREAM_BYTES + 1), 0)):
            with self.assertRaises(FPCError): f()

if __name__ == '__main__': unittest.main()
