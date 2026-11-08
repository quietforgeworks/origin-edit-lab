"""Locally authored adversarial tests; no external codec is executed here."""
import random
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code'))
from fpc_numeric import (encode_bits, decode_bits, FPCError, MAX_VALUES,
                         MAX_STREAM_BYTES, MAX_RAW_BYTES)
from independent_fpc_decoder import decode_prefix, decode_strict, DecodeError


def raw(words):
    return b''.join(word.to_bytes(8, 'little') for word in words)


class EncoderAdversarial(unittest.TestCase):
    def test_hand_calculated_encoder_bytes(self):
        # Encoder prefers FCM on identical XOR residuals.
        fixtures = [([], ''), ([0], '00'), ([0, 0, 0], '0000'),
                    ([1], '0101'), ([1, 1], '0101'),
                    ([1, 2, 3], '810108'),
                    ([1 << 63, 0], '870000000000000080')]
        for words, expected in fixtures:
            self.assertEqual(encode_bits(raw(words)), bytes.fromhex(expected))
        for bits in (0, 1, 8, 9, 16, 17, 24, 25, 32, 33, 40, 41, 48, 49, 56, 57, 64):
            value = (1 << bits) - 1
            needed = (bits + 7) // 8
            width = 5 if needed == 4 else needed
            code = (0, 1, 2, 3, 5, 6, 7, 8).index(width)
            self.assertEqual(encode_bits(raw([value])), bytes([code]) + value.to_bytes(width, 'little'))

    def test_seeded_exact_bits_differential(self):
        rng = random.Random(20261108)
        edge = [0, 1, (1 << 64)-1, 1 << 63, 0x7ff0000000000000,
                0xfff0000000000000, 0x7ff0000000000001,
                0x7ff8000000000000, 0xfff800000000007f,
                0x0010000000000000, 0x000fffffffffffff]
        cases = [edge, edge[::-1], [0] * 1001, list(range(1001)),
                 [(1 << 64) - 1 - i for i in range(1001)],
                 [rng.getrandbits(64) for _ in range(10001)]]
        for _ in range(100):
            cases.append([rng.getrandbits(64) for _ in range(rng.randrange(100))])
        for words in cases:
            stream = encode_bits(raw(words))
            self.assertEqual(decode_strict(stream, len(words)), words)
            self.assertEqual(decode_bits(stream, len(words)), (raw(words), len(stream)))
            self.assertEqual(encode_bits(raw(words)), stream)

    def test_exact_budget_and_every_smaller_budget(self):
        words = [0x123456789abcdef0, 0xfedcba9876543210, 0x7ff0000000000001]
        stream = encode_bits(raw(words))
        for limit in range(len(stream)):
            with self.assertRaises(FPCError):
                encode_bits(raw(words), max_output_bytes=limit)
        self.assertEqual(encode_bits(raw(words), max_output_bytes=len(stream)), stream)
        self.assertEqual(encode_bits(b'', max_output_bytes=0, max_values=0), b'')
        for kwargs in ({'max_values': 2}, {'max_input_bytes': len(stream)-1},
                       {'max_output_bytes': len(words)*8-1}):
            with self.assertRaises(FPCError):
                decode_bits(stream, len(words), **kwargs)
        self.assertEqual(decode_bits(stream, 3, max_values=3,
                         max_input_bytes=len(stream), max_output_bytes=24), (raw(words),len(stream)))

    def test_knob_types_bounds(self):
        for function, args, knobs in (
                (encode_bits, (b'',), {'max_values':MAX_VALUES, 'max_output_bytes':MAX_STREAM_BYTES}),
                (decode_bits, (b'', 0), {'max_values':MAX_VALUES, 'max_input_bytes':MAX_STREAM_BYTES,
                                         'max_output_bytes':MAX_RAW_BYTES})):
            for knob, ceiling in knobs.items():
                for value in (-1, ceiling+1, True, False, 1.0, None, '0'):
                    with self.assertRaises(FPCError):
                        function(*args, **{knob:value})
        for value in (-1, MAX_VALUES+1, True, False, 1.0, None, '0'):
            with self.assertRaises(FPCError):
                decode_bits(b'', value)
        for value in (0, 1, None, 'true'):
            with self.assertRaises(FPCError):
                decode_bits(b'', 0, exact=value)
        for value in (bytearray(), memoryview(b''), '', None):
            with self.assertRaises(FPCError):
                encode_bits(value)
            with self.assertRaises(FPCError):
                decode_bits(value, 0)
        for length in (1, 7, 9):
            with self.assertRaises(FPCError):
                encode_bits(b'\0' * length)
        with self.assertRaises(FPCError):
            encode_bits(b'\0' * (MAX_RAW_BYTES + 8))
        with self.assertRaises(FPCError):
            decode_bits(b'\0' * (MAX_STREAM_BYTES + 1), 0)

    def test_prefix_count_semantic_limit(self):
        # Neither count nor checksum is embedded: strict cannot detect wrong
        # count when omitted high-half residual is zero-width.
        stream = encode_bits(raw([1, 1]))
        self.assertEqual(decode_bits(stream, 1), (raw([1]), len(stream)))
        full = encode_bits(raw([1, 123456]))
        prefix, used = decode_bits(full, 1, exact=False)
        self.assertEqual(prefix, raw([1]))
        self.assertLess(used, len(full))
        with self.assertRaises(FPCError):
            decode_bits(full, 1)
        # Returned offset is consumed bytes, NOT a fresh-state resume point.
        self.assertEqual(decode_bits(b'trailing', 0, exact=False), (b'', 0))

    def test_arbitrary_stream_differential(self):
        rng = random.Random(93)
        for _ in range(3000):
            count = rng.randrange(13)
            data = bytes(rng.getrandbits(8) for _ in range(rng.randrange(110)))
            try:
                values, used = decode_prefix(data, count)
            except DecodeError:
                with self.assertRaises(FPCError):
                    decode_bits(data, count, exact=False)
            else:
                self.assertEqual(decode_bits(data, count, exact=False), (raw(values), used))
                if used == len(data):
                    self.assertEqual(decode_bits(data, count), (raw(values), used))
                else:
                    with self.assertRaises(FPCError):
                        decode_bits(data, count)

    def test_unused_high_nibble_and_fresh_state(self):
        stream = encode_bits(raw([1]))
        for nibble in range(16):
            alternate = bytes([(stream[0] & 15) | (nibble << 4)]) + stream[1:]
            self.assertEqual(decode_bits(alternate, 1), (raw([1]), len(stream)))
        encode_bits(raw([0xffffffffffffffff] * 4000))
        self.assertEqual(encode_bits(raw([1])), stream)
        decode_bits(stream, 1)
        self.assertEqual(decode_bits(b'\x00', 1), (raw([0]), 1))


if __name__ == '__main__':
    unittest.main()
