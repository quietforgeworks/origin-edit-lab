import hashlib
from itertools import product
from pathlib import Path
import random
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'code'))
from experimental_exact_fpc import (analyze_exact_budgets, encode_bits_exact_budget,
    ExperimentalFPCError, UnreachableBudgetError, ResourceLimitError, MAX_VALUES,
    MAX_STREAM_BYTES)

def pinned(name, digest):
    path = ROOT / 'reference' / (name + '.py')
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != digest:
        raise ValueError('reference source digest mismatch')
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(source, str(path), 'exec'), module.__dict__)
    return module

baseline = pinned('fpc_numeric', '43c3415066ed12f1f158e8406f6d62d1dc767daea537e31441865934e6c70dbc')
independent = pinned('independent_fpc_decoder', '0ad34fbaedf86655085e6302d864a3456af6377f7d00e641a2879dbf79734d89')
WIDTHS = (0, 1, 2, 3, 5, 6, 7, 8)
MASK = 2**64 - 1
SENTINEL = 0x81AA74FE1C132C0E
EDGES = [0, 2**63, 1, MASK, 2**52 - 1, 2**52, 0x7FEFFFFFFFFFFFFF,
         0x7FF0000000000000, 0xFFF0000000000000, 0x7FF0000000000001,
         0x7FF8000000000000, 0xFFF8123456789ABC, SENTINEL]

def packed(words):
    return b''.join(x.to_bytes(8, 'little') for x in words)

def dynamic_sizes(words):
    # Separate set-valued oracle, no closed-form reachability.
    f, d = {}, {}
    fh = dh = last = 0
    reachable = {0}
    for word in words:
        a, b = word ^ f.get(fh, 0), word ^ ((last + d.get(dh, 0)) & MASK)
        allowed = [w for w in WIDTHS if a < 1 << (8*w) or b < 1 << (8*w)]
        reachable = {s+w for s in reachable for w in allowed}
        stride = (word-last) & MASK
        f[fh], d[dh] = word, stride
        fh, dh = ((fh*64) ^ (word >> 48)) % 4096, ((dh*4) ^ (stride >> 40)) % 4096
        last = word
    return {s + (len(words)+1)//2 for s in reachable}

def seeded_sequences():
    rng = random.Random(20261108)
    yield []
    yield EDGES
    yield EDGES[::-1]
    for index in range(480):
        n = rng.randrange(0, 65)
        mode = index % 6
        if mode == 0: words = [rng.getrandbits(64) for _ in range(n)]
        elif mode == 1: words = [rng.getrandbits(rng.choice([0, 1, 8, 16, 24, 32, 40, 48, 56, 64])) for _ in range(n)]
        elif mode == 2: words = [rng.choice(EDGES) for _ in range(n)]
        elif mode == 3: words = [(i * 0x0100000000000001) & MASK for i in range(n)]
        elif mode == 4: words = [rng.getrandbits(64)] * n
        else: words = [0x7FF0000000000000 | rng.getrandbits(52) | 1 | (rng.randrange(2)<<63) for _ in range(n)]
        yield words

class ExactBudgetTests(unittest.TestCase):
    def check_stream(self, words, budget):
        raw = packed(words)
        wire = encode_bits_exact_budget(raw, budget)
        self.assertEqual(len(wire), budget)
        self.assertEqual(wire, encode_bits_exact_budget(raw, budget))
        self.assertEqual(baseline.decode_bits(wire, len(words)), (raw, budget))
        self.assertEqual(independent.decode_strict(wire, len(words)), words)
        self.assertEqual(baseline.decode_bits(wire+b'TRAILER', len(words), exact=False), (raw, budget))
        self.assertEqual(independent.decode_prefix(wire+b'TRAILER', len(words)), (words, budget))
        with self.assertRaises(baseline.FPCError): baseline.decode_bits(wire+b'\0', len(words))

    def test_exhaustive_small_actual_inputs_and_all_budgets(self):
        alphabet = (0, 1, 256, 65536, 1<<24, 1<<40, MASK)
        for n in range(4):
            for seq in product(alphabet, repeat=n):
                words = list(seq)
                allowed = dynamic_sizes(words)
                info = analyze_exact_budgets(packed(words))
                described = {x for lo, hi in info.reachable_intervals for x in range(lo, hi+1)}
                self.assertEqual(described, allowed)
                for budget in range((n+1)//2 + 8*n + 2):
                    if budget in allowed: self.check_stream(words, budget)
                    else:
                        with self.assertRaises(UnreachableBudgetError):
                            encode_bits_exact_budget(packed(words), budget)

    def test_seeded_sequences_and_boundary_budgets(self):
        rng = random.Random(9108)
        for words in seeded_sequences():
            raw = packed(words)
            allowed = dynamic_sizes(words)
            info = analyze_exact_budgets(raw)
            self.assertEqual({x for a,b in info.reachable_intervals for x in range(a,b+1)}, allowed)
            self.assertEqual(encode_bits_exact_budget(raw, info.minimum_bytes), baseline.encode_bits(raw))
            candidates = {info.minimum_bytes, info.maximum_bytes, info.minimum_bytes+1,
                          max(0,info.minimum_bytes-1), max(0,info.maximum_bytes-1),info.maximum_bytes+1}
            candidates.update(rng.choices(sorted(allowed), k=4))
            for budget in candidates:
                if budget in allowed: self.check_stream(words,budget)
                else:
                    with self.assertRaises(UnreachableBudgetError): encode_bits_exact_budget(raw,budget)

    def test_known_width_holes(self):
        # One zero word: control + W. One 3-byte word cannot use four bytes.
        self.assertEqual(analyze_exact_budgets(packed([0])).reachable_intervals, ((1,4),(6,9)))
        self.assertEqual(analyze_exact_budgets(packed([65536])).reachable_intervals, ((4,4),(6,9)))
        self.assertEqual(analyze_exact_budgets(packed([0,0])).reachable_intervals, ((1,17),))

    def test_exact_word_categories(self):
        for words in [EDGES, EDGES*3, [SENTINEL], [0]*17, [MASK]*18]:
            info = analyze_exact_budgets(packed(words))
            for lo,hi in info.reachable_intervals:
                for budget in range(lo,hi+1): self.check_stream(words,budget)

    def test_reset_separate_segments(self):
        words = EDGES*9
        for cut in (1,2,13,40):
            a,b = words[:cut],words[cut:]
            for seq in (a,b):
                raw=packed(seq);n=len(seq);budget=(n+1)//2+8*n
                wire=encode_bits_exact_budget(raw,budget)
                self.assertEqual(independent.decode_strict(wire,n),seq)

    def test_types_and_limits_fail_closed(self):
        for raw in (None,bytearray(8),memoryview(bytes(8)),[0],b'1'):
            with self.assertRaises(ExperimentalFPCError): analyze_exact_budgets(raw)
            with self.assertRaises(ExperimentalFPCError): encode_bits_exact_budget(raw,1)
        for bad in (True,False,-1,1.0,None,'1',MAX_STREAM_BYTES+1):
            with self.assertRaises(ExperimentalFPCError): encode_bits_exact_budget(b'',bad)
        for key,maximum in [('max_values',MAX_VALUES),('max_output_bytes',MAX_STREAM_BYTES)]:
            for bad in (True,-1,1.0,None,maximum+1):
                with self.assertRaises(ExperimentalFPCError): encode_bits_exact_budget(b'',0,**{key:bad})
        with self.assertRaises(ResourceLimitError): encode_bits_exact_budget(bytes(8),1,max_values=0)
        with self.assertRaises(ResourceLimitError): encode_bits_exact_budget(bytes(8),1,max_output_bytes=0)
        with self.assertRaises(ResourceLimitError): encode_bits_exact_budget(bytes(8*(MAX_VALUES+1)),1)
        self.assertEqual(encode_bits_exact_budget(b'',0,max_values=0,max_output_bytes=0),b'')
        with self.assertRaises(UnreachableBudgetError): encode_bits_exact_budget(b'',1)

    def test_immutable_and_odd_unused_nibble(self):
        raw=packed(EDGES)
        before=hashlib.sha256(raw).hexdigest()
        info=analyze_exact_budgets(raw)
        for budget in (info.minimum_bytes,info.maximum_bytes):
            wire=encode_bits_exact_budget(raw,budget)
            at=0
            for i in range(0,len(EDGES),2):
                control=wire[at];at+=1
                at+=WIDTHS[control&7]
                if i+1<len(EDGES):at+=WIDTHS[(control>>4)&7]
                else:self.assertEqual(control>>4,0)
            self.assertEqual(at,budget)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),before)

    def test_large_state_reuse_and_wrap(self):
        rng=random.Random(8192)
        words=[rng.getrandbits(64) for _ in range(20_000)]
        for offset in range(0,len(words),37):words[offset]=SENTINEL
        info=analyze_exact_budgets(packed(words))
        self.check_stream(words,info.maximum_bytes)
        self.assertEqual(encode_bits_exact_budget(packed(words),info.minimum_bytes),baseline.encode_bits(packed(words)))

if __name__ == '__main__': unittest.main()
