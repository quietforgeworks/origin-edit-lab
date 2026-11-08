"""Explicit opt-in interoperability tests against SHA-pinned approved sources."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "independent-review")]
from test_fpc_numeric import sequences, EDGES, packed, MISSING_BITS
from fpc_numeric import encode_bits, decode_bits
from independent_fpc_decoder import decode_strict
from verified_oracle import external_decoder, decode_raw_adapter, PINS, REVISION


def need(condition, message):
    if not condition: raise ValueError(message)


def run(root):
    import numpy as np
    digest = hashlib.sha256()
    counts = {"sequences": 0, "values": 0, "unchanged_external_bit_exact_sequences": 0,
              "sequences_with_missing_sentinel": 0, "missing_sentinel_values": 0}
    with external_decoder(root) as external:
        for words in [EDGES, EDGES[::-1], [MISSING_BITS], [], *sequences()]:
            raw = packed(words)
            wire = encode_bits(raw)
            original, used = external._decode(wire + b"TRAILER", len(words))
            result = original.view("<u8").tobytes()
            expected = bytearray(raw)
            missing_count = 0
            for index, word in enumerate(words):
                if word == MISSING_BITS:
                    expected[index*8:(index+1)*8] = np.asarray([np.nan], dtype="<f8").tobytes()
                    missing_count += 1
            need(result == bytes(expected), "unchanged external output differs beyond documented sentinel mapping")
            need(used == len(wire), "unchanged external consumed trailer")
            adapted, consumed = decode_raw_adapter(external, wire + b"TRAILER", len(words))
            need((adapted, consumed) == (raw, len(wire)), "adapted external mismatch")
            need(decode_strict(wire, len(words)) == words, "independent mismatch")
            need(decode_bits(wire, len(words)) == (raw, len(wire)), "own decoder mismatch")
            digest.update(raw)
            digest.update(wire)
            counts["sequences"] += 1
            counts["values"] += len(words)
            counts["missing_sentinel_values"] += missing_count
            counts["sequences_with_missing_sentinel"] += bool(missing_count)
            counts["unchanged_external_bit_exact_sequences"] += not bool(missing_count)
    return {"summary": counts, "aggregate_raw_and_encoded_sha256": digest.hexdigest(),
            "python": platform.python_version(), "numpy": np.__version__,
            "optimize": sys.flags.optimize, "quantized_revision": REVISION,
            "external_source_hashes": PINS, "all_raw_adapter_and_independent_checks_exact": True,
            "all_unchanged_checks_match_documented_missing_normalization": True,
            "native_origin_acceptance": False}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quantized-root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    result = run(args.quantized_root)
    with args.out.open("x") as output: json.dump(result, output, indent=2)
    print(json.dumps(result["summary"], sort_keys=True))
