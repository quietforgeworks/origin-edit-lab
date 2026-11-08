"""Read-only allowlisted PUBLIC source interoperability audit.

No scan/resynchronization, source mutation, OPJU splicing or publication.
External parser/codec sources execute only after pinned SHA checks. Corpus
manifest carries only public identifiers; local paths are separate optional
input mappings and are never included in the report.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "independent-review")]
from fpc_numeric import encode_bits, decode_bits, MAX_VALUES
from independent_fpc_decoder import decode_strict
from verified_oracle import external_decoder, decode_raw_adapter, load_verified, PINS

STRICT_SHA = "fe3f6998cc5cf09c5f955c7e02ac5d7126a83d30d2d50380a90f2680bc5be575"
MATRIX_SHA = "8f9e49840b5c614b15bd5cabeea6d06290d9a579d16cab005e42e416c0f536aa"
MAX_CORPUS_VALUES = 30_000_000
MAX_CORPUS_STREAMS = 50_000
MISSING = bytes.fromhex("0e2c131cfe74aa81")


def need(value, reason):
    if not value: raise ValueError(reason)


def sha(data): return hashlib.sha256(data).hexdigest()


def intervals(parsed, data, parser):
    for dataset in parsed["datasets"]:
        # Only complete envelopes, never an unsupported pending record.
        if "end" not in dataset: continue
        for group in dataset.get("row_groups", []):
            for segment in group["segments"]:
                if segment["kind"] != "fpc-byte-extent": continue
                encoded, p = parser.uleb(data, segment["start"])
                need(-((encoded >> 1) ^ -(encoded & 1)) == segment["rows"], "segment count mismatch")
                need(data[p] == 12, "FPC marker mismatch")
                yield {"slot1": dataset["slot1"], "start": p + 1,
                       "end": segment["end"], "count": segment["rows"],
                       "experimental_matrix_framing": bool(dataset.get("EXPERIMENTAL_matrix_framing"))}


def run(args):
    import numpy as np
    strict = load_verified(args.strict_parser, "verified_strict", STRICT_SHA)
    matrix = load_verified(args.matrix_parser, "verified_matrix", MATRIX_SHA)
    manifest = json.loads(args.manifest.read_text())
    need(manifest["schema"] == 1 and len(manifest["files"]) <= 200, "unexpected corpus manifest")
    path_map = json.loads(args.local_map.read_text()) if args.local_map else None
    totals = Counter()
    files = []
    records = []
    nibble_counts = Counter()
    signatures = Counter()
    blockers = Counter()
    concatenated = hashlib.sha256()
    with external_decoder(args.quantized_root) as external:
        for entry in manifest["files"]:
            name = entry["file"]
            need(Path(name).name == name and entry["public"] is True, "nonpublic/nonlocal-name manifest entry")
            path = Path(path_map[name]) if path_map is not None else args.source_dir / name
            data = strict.read_bounded_source(path)
            need(sha(data) == entry["sha256"], "source SHA mismatch: " + name)
            default = strict.walk(data)
            experimental = matrix.walk(data, experimental_direct_matrix=True)
            default_keys = {(x["start"], x["end"], x["count"]) for x in intervals(default, data, strict)}
            streams = list(intervals(experimental, data, matrix))
            need(default_keys <= {(x["start"], x["end"], x["count"]) for x in streams}, "matrix removed strict streams")
            signatures[experimental.get("prolog", {}).get("signature", "unparsed")] += 1
            blockers[experimental.get("blocker", "complete")] += 1
            file_totals = Counter()
            for interval in streams:
                count, start, end = interval["count"], interval["start"], interval["end"]
                need(count <= MAX_VALUES, "public stream exceeds bounded codec count")
                need(totals["values"] + count <= MAX_CORPUS_VALUES, "corpus value budget exceeded")
                need(totals["streams"] < MAX_CORPUS_STREAMS, "corpus stream budget exceeded")
                source = data[start:end]
                # Primary raw decode comes from the independent implementation,
                # not the encoder's companion decoder.
                words = decode_strict(source, count)
                raw = b"".join(x.to_bytes(8, "little") for x in words)
                need(decode_bits(source, count) == (raw, len(source)), "original independent/own mismatch")
                original_adapter, original_consumed = decode_raw_adapter(external, source + b"TRAILER", count)
                need((original_adapter, original_consumed) == (raw, len(source)), "original external raw mismatch")
                wire = encode_bits(raw)
                need(encode_bits(raw) == wire, "nondeterministic encoding")
                need(decode_strict(wire, count) == words, "reencoded independent mismatch")
                need(decode_bits(wire, count) == (raw, len(wire)), "reencoded own mismatch")
                out, consumed = decode_raw_adapter(external, wire + b"TRAILER", count)
                need((out, consumed) == (raw, len(wire)), "reencoded external raw mismatch")
                baseline, used = external._decode(source + b"TRAILER", count)
                rewritten, used2 = external._decode(wire + b"TRAILER", count)
                need((used, used2) == (len(source), len(wire)), "unchanged external swallowed trailer")
                original_public = baseline.view("<u8").tobytes()
                rewritten_public = rewritten.view("<u8").tobytes()
                need(original_public == rewritten_public, "unchanged external values changed")
                missing_count = sum(raw[p:p+8] == MISSING for p in range(0, len(raw), 8))
                expected = bytearray(raw)
                for p in range(0, len(raw), 8):
                    if raw[p:p+8] == MISSING:
                        expected[p:p+8] = np.asarray([np.nan], dtype="<f8").tobytes()
                need(original_public == bytes(expected), "external normalization differs beyond sentinel")
                source_position = 0
                for pair in range(0, count, 2):
                    control = source[source_position]
                    source_position += 1
                    for half in range(min(2, count-pair)):
                        nibble = (control >> (half * 4)) & 15
                        nibble_counts[nibble] += 1
                        width = nibble & 7
                        source_position += width + (width >= 4)
                need(source_position == len(source), "control histogram extent mismatch")
                additional = (start, end, count) not in default_keys
                record = dict(file=name, source_sha256=entry["sha256"], **interval,
                              additional_to_strict=additional, original_stream_sha256=sha(source),
                              raw_bits_sha256=sha(raw), encoded_stream_sha256=sha(wire),
                              original_bytes=len(source), encoded_bytes=len(wire),
                              missing_sentinel_count=missing_count,
                              unchanged_external_raw_bit_exact=(missing_count == 0))
                records.append(record)
                concatenated.update(raw)
                for key, value in (("streams", 1), ("values", count), ("original_bytes", len(source)),
                                   ("encoded_bytes", len(wire)), ("missing_sentinel_values", missing_count),
                                   ("streams_with_missing_sentinel", bool(missing_count)),
                                   ("additional_to_strict_streams", additional),
                                   ("additional_to_strict_values", count if additional else 0),
                                   ("experimental_matrix_streams", interval["experimental_matrix_framing"])):
                    totals[key] += value
                    file_totals[key] += value
            need(sha(strict.read_bounded_source(path)) == entry["sha256"], "source changed: " + name)
            files.append({"file": name, "sha256_before": entry["sha256"],
                          "sha256_after": entry["sha256"], "source_bytes": len(data),
                          "source": entry["source"], "strict_summary": default["summary"],
                          "experimental_summary": experimental["summary"], "tested": dict(file_totals)})
            print(json.dumps({"file": name, "tested_streams": file_totals["streams"],
                              "tested_values": file_totals["values"]}), flush=True)
    summary = dict(totals, files=len(files), files_with_tested_streams=sum(bool(x["tested"].get("streams")) for x in files),
                   strict_complete_lists=sum(x["strict_summary"]["dataset_list_complete"] for x in files),
                   experimental_complete_lists=sum(x["experimental_summary"]["dataset_list_complete"] for x in files),
                   exact_raw_bit_roundtrips=True, all_original_hashes_unchanged=True,
                   independent_decode_and_external_comparison=True, native_origin_acceptance=False,
                   native_containers_modified=False)
    return {"summary": summary, "python": platform.python_version(), "numpy": np.__version__,
            "optimize": sys.flags.optimize, "aggregate_raw_bits_sha256": concatenated.hexdigest(),
            "dependency_hashes": dict(PINS, strict_parser=STRICT_SHA, matrix_parser=MATRIX_SHA),
            "signature_counts": dict(signatures), "first_blockers": dict(blockers),
            "original_control_nibble_counts": dict(sorted(nibble_counts.items())),
            "files": files, "streams": records}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, type=Path)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--source-dir", type=Path)
    group.add_argument("--local-map", type=Path)
    ap.add_argument("--strict-parser", required=True, type=Path)
    ap.add_argument("--matrix-parser", required=True, type=Path)
    ap.add_argument("--quantized-root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    result = run(ap.parse_args())
    # Exclusive create only, never overwrite any source/result.
    with ap.parse_args().out.open("x") as output: json.dump(result, output, indent=2)
    print(json.dumps(result["summary"], sort_keys=True))
