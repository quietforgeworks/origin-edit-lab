"""Portable synthetic tests: no external packages, native files or downloads."""
import hashlib
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "code"), str(ROOT / "independent-review")]
from fpc_numeric import encode_bits, decode_bits, FPCError, MAX_VALUES, MAX_RAW_BYTES, MAX_STREAM_BYTES
from independent_fpc_decoder import decode_prefix, decode_strict

MASK = (1 << 64) - 1
MISSING_BITS = 0x81AA74FE1C132C0E
EDGES = [0, 1, (1 << 52) - 1, 1 << 52, 0x8000000000000000,
         0x8000000000000001, 0x800FFFFFFFFFFFFF, 0x8010000000000000,
         0x7FEFFFFFFFFFFFFF, 0xFFEFFFFFFFFFFFFF, 0x7FF0000000000000,
         0xFFF0000000000000, 0x7FF0000000000001, 0xFFF0000000000001,
         0x7FF8000000000000, 0xFFF8000000000000, 0x7FFFFFFFFFFFFFFF,
         MASK, MISSING_BITS]


def packed(words):
    return b"".join(w.to_bytes(8, "little") for w in words)


def sequences(total=6000):
    """Deterministic integer-only corpus, independent of floats/math libs."""
    r = random.Random(0xF0C20261108)
    for i in range(total):
        n = r.randrange(0, 258)
        kind = i % 12
        if kind == 0:
            words = [r.getrandbits(64) for _ in range(n)]
        elif kind == 1:
            words = [r.choice(EDGES) for _ in range(n)]
        elif kind == 2:
            start, delta = r.getrandbits(64), r.getrandbits(64)
            words = [(start + k * delta) & MASK for k in range(n)]
        elif kind == 3:
            word = r.getrandbits(64)
            words = [word] * n
        elif kind == 4:
            words = [1 << r.randrange(64) for _ in range(n)]
        elif kind == 5:
            # Hash collision emphasis: top 24 bits zero for small words.
            words = [r.randrange(1 << 24) for _ in range(n)]
        elif kind == 6:
            # Signaling and quiet NaNs, both signs, arbitrary payloads.
            words = [0x7FF0000000000000 | (r.getrandbits(52) or 1) |
                     (r.randrange(2) << 63) for _ in range(n)]
        elif kind == 7:
            words = [(k * 0x1000000000001) & MASK for k in range(n)]
        elif kind == 8:
            base = r.getrandbits(64)
            words = [(base ^ ((k % 3) << (8 * (k % 8)))) & MASK for k in range(n)]
        elif kind == 9:
            words = [0 if k % 2 else 1 << 63 for k in range(n)]
        elif kind == 10:
            words = [r.randrange(1 << 52) | (r.randrange(2) << 63) for _ in range(n)]
        else:
            words = [(r.getrandbits(40) << 24) | (k % 5) for k in range(n)]
        yield words


class FPCTests(unittest.TestCase):
    def check(self, words):
        raw = packed(words)
        encoded = encode_bits(raw)
        self.assertEqual(encoded, encode_bits(raw))
        self.assertEqual(decode_bits(encoded, len(words)), (raw, len(encoded)))
        self.assertEqual(decode_strict(encoded, len(words)), words)
        trailer = b"\xff\xff\x0cTRAILER"
        self.assertEqual(decode_bits(encoded + trailer, len(words), exact=False),
                         (raw, len(encoded)))
        self.assertEqual(decode_prefix(encoded + trailer, len(words)),
                         (words, len(encoded)))
        with self.assertRaises(FPCError):
            decode_bits(encoded + trailer, len(words))
        return encoded

    def test_manual_encoder_fixtures(self):
        fixtures = [([], ""), ([0], "00"), ([0, 0], "00"),
                    ([0, 0, 0], "0000"), ([1], "0101"),
                    ([1, 1], "0101"), ([1, 2, 3], "810108"),
                    ([0x1000000], "040000000100"),
                    ([0x100000000], "040000000001"),
                    ([0x8000000000000000], "070000000000000080"),
                    ([MASK, MASK - 1], "97ffffffffffffffff01")]
        for words, expected in fixtures:
            with self.subTest(words=words):
                self.assertEqual(self.check(words).hex(), expected)

    def test_all_widths_and_selectors(self):
        widths = (0, 1, 2, 3, 5, 6, 7, 8)
        for selector in (0, 8):
            for code, width in enumerate(widths):
                residual = (1 << (8 * width)) - 1 if width else 0
                wire = bytes([selector | code]) + residual.to_bytes(width, "little")
                expected = packed([residual])
                self.assertEqual(decode_bits(wire, 1), (expected, len(wire)))
                self.assertEqual(decode_strict(wire, 1), [residual])
                for end in range(len(wire)):
                    with self.assertRaises(FPCError):
                        decode_bits(wire[:end], 1)

    def test_edge_bits_and_nan_payloads(self):
        self.check(EDGES)
        self.check(EDGES[::-1] * 7)
        for position in range(64):
            self.check([1 << position, MASK ^ (1 << position), 0, 1 << 63])

    def test_thousands_deterministic_sequences(self):
        for index, words in enumerate(sequences()):
            with self.subTest(sequence=index):
                self.check(words)

    def test_reset_and_concatenated_prefixes(self):
        chunks = [[], [1, 2, 3], EDGES, [MASK, 0, MASK], [0, 0], [1]]
        combined = b"".join(encode_bits(packed(x)) for x in chunks)
        p = 0
        for words in chunks:
            raw, used = decode_bits(combined[p:], len(words), exact=False)
            self.assertEqual(raw, packed(words))
            self.assertEqual(used, len(encode_bits(raw)))
            p += used
        self.assertEqual(p, len(combined))

    def test_unused_odd_nibble_never_consumes_bytes(self):
        for high in range(16):
            wire = bytes([high << 4])
            self.assertEqual(decode_bits(wire, 1), (bytes(8), 1))
            self.assertEqual(decode_prefix(wire + bytes(8), 1), ([0], 1))

    def test_strict_types_and_budgets(self):
        for invalid in (True, -1, 1.0, "1", None, MAX_VALUES + 1):
            with self.assertRaises(FPCError): decode_bits(b"", invalid)
            with self.assertRaises(FPCError): encode_bits(b"", max_values=invalid)
        for invalid in (bytearray(), memoryview(b""), [], "", None):
            with self.assertRaises(FPCError): encode_bits(invalid)
            with self.assertRaises(FPCError): decode_bits(invalid, 0)
        for n in range(1, 8):
            with self.assertRaises(FPCError): encode_bits(bytes(n))
        with self.assertRaises(FPCError): encode_bits(bytes(8), max_values=0)
        with self.assertRaises(FPCError): encode_bits(bytes(8), max_output_bytes=0)
        with self.assertRaises(FPCError): encode_bits(packed([MASK]), max_output_bytes=8)
        self.assertEqual(len(encode_bits(packed([MASK]), max_output_bytes=9)), 9)
        with self.assertRaises(FPCError): encode_bits(bytes(8), max_output_bytes=MAX_STREAM_BYTES + 1)
        with self.assertRaises(FPCError): decode_bits(b"\0", 1, max_output_bytes=7)
        with self.assertRaises(FPCError): decode_bits(b"\0", 1, max_input_bytes=0)
        with self.assertRaises(FPCError): decode_bits(b"", 0, exact=1)
        with self.assertRaises(FPCError): decode_bits(b"", 0, max_output_bytes=MAX_RAW_BYTES + 1)
        self.assertEqual(encode_bits(b"", max_values=0, max_output_bytes=0), b"")
        self.assertEqual(decode_bits(b"", 0, max_values=0, max_input_bytes=0,
                                     max_output_bytes=0), (b"", 0))

    def test_every_truncation_rejected(self):
        for words in (EDGES, list(range(57)), [MASK] * 41):
            wire = encode_bits(packed(words))
            for end in range(len(wire)):
                with self.assertRaises(FPCError): decode_bits(wire[:end], len(words))

    def test_mutation_is_not_a_checksum(self):
        wire = encode_bits(packed([1]))
        mutated = wire[:-1] + b"\x02"
        self.assertEqual(decode_bits(mutated, 1)[0], packed([2]))
        # Single byte mutations either reject, or both independent readers
        # agree on exact bits/extent. Valid mutations are not silently called
        # corruption detection successes.
        wire = encode_bits(packed(EDGES))
        for p in range(len(wire)):
            for bit in (1, 8, 128):
                changed = wire[:p] + bytes([wire[p] ^ bit]) + wire[p+1:]
                try:
                    raw, used = decode_bits(changed, len(EDGES), exact=False)
                except FPCError:
                    with self.assertRaises(ValueError): decode_prefix(changed, len(EDGES))
                else:
                    words, other_used = decode_prefix(changed, len(EDGES))
                    self.assertEqual((raw, used), (packed(words), other_used))

    def test_compressed_count_cannot_self_identify(self):
        # Odd/even counts can consume identical bytes. Envelope metadata is
        # essential; strict byte consumption cannot establish correct count.
        wire = encode_bits(packed([1, 1]))
        self.assertEqual(decode_bits(wire, 1), (packed([1]), len(wire)))
        self.assertEqual(decode_bits(wire, 2), (packed([1, 1]), len(wire)))


if __name__ == "__main__": unittest.main()
