# Exact-budget FPC research, revision 2

This source-only research package encodes opaque little-endian uint64 words into an **exact requested FPC stream byte length**, if that length is mathematically reachable. It is not an Origin project, page, graph, OPJU, CFB or PowerPoint writer. No native source is patched by this package. **Origin acceptance of its nonminimal encodings has not been tested.**

The reviewed numeric implementation is unchanged. Revision 2 completes the previously interrupted portable and public-harness review, adds a fixed-manifest integrity check and six boundary-contract tests, and freezes evidence. It is an unpublished candidate pending the parent review, not a promotion into a supported native editor.

## Interface and contract

Python 3.10+ standard library is sufficient for the codec and portable tests. Executed here on Linux CPython 3.12.14, ordinary mode and `-O`.

```python
from experimental_exact_fpc import analyze_exact_budgets, encode_bits_exact_budget
info = analyze_exact_budgets(raw_le)
wire = encode_bits_exact_budget(raw_le, budget_bytes)
```

The module is in `code/`. `raw_le` must be exact immutable `bytes`, with eight bytes per word. It preserves the original 64 bits, including signed zero, subnormals, infinities, signaling/quiet NaN payloads and the finite Origin missing sentinel. Do not convert decimal text or float-converted NaNs back to bits and call that preservation.

- `analyze_exact_budgets` returns count, control-byte count, minimum, maximum and one or two inclusive reachable intervals.
- `encode_bits_exact_budget` returns exactly the requested bytes or raises. It never changes the word count, appends arbitrary padding, truncates residuals or returns partial output.
- Limits: one million words, eight million input bytes, 8.5 million encoded bytes. Caller `max_values` and `max_output_bytes` can only tighten the limits. These are bounded algorithm/data limits, not whole-process memory or wall-clock quotas.
- Each call starts fresh predictor state. Output is deterministic: smaller unsigned residual, FCM on ties, then lexicographically smallest width sequence admitting a reachable suffix. Minimum-budget output matches the pinned baseline.
- Count is **external trusted metadata**, not stored in FPC. Exact consumed extent does not authenticate count or data. For example, `01 01` decodes as `[1]` or `[1,1]` depending on supplied count. There is no checksum. Valid mutations may decode to changed words. All 16 nibble values are legal, and readers ignore an unused odd high nibble; the encoder emits zero there.
- Prefix decode offsets are not resumable predictor checkpoints. Separate encoded segments must be decoded separately using their validated counts and reset boundaries.

## Reachability

Allowed residual widths are `W=(0,1,2,3,5,6,7,8)`. Let each word's minimum width be `m_i`, `C=ceil(n/2)`, `L=C+sum(m_i)`, and `U=C+8n`. Ignore width-8 minima, which have no flexibility.

- No flexible word: only `L=U` is reachable.
- Every flexible minimum equals 3: every size in `[L,U]` except `L+1`.
- Exactly one flexible minimum `m` is 0, 1 or 2: every size except `L+4-m`.
- Otherwise every integer size in `[L,U]` is reachable.

The code uses two bounded passes and at most eight width choices per word. `independent-review/REACHABILITY_PROOF.md` gives the proof. Nonminimal widths add zero high bytes **inside a valid residual**, not after the stream. Native Origin acceptance of that choice remains unknown.

## Reproduce portable checks

Run in an extracted disposable copy if preserving the original package manifest is important. `PYTHONDONTWRITEBYTECODE=1` avoids bytecode files. The independent scripts write generated JSON next to themselves; frozen results are stored separately in `results/`.

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python -O -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python independent-review/reachability_oracle.py
PYTHONDONTWRITEBYTECODE=1 python -O independent-review/reachability_oracle.py
PYTHONDONTWRITEBYTECODE=1 python independent-review/adversarial_review.py
PYTHONDONTWRITEBYTECODE=1 python -O independent-review/adversarial_review.py
```

The exact portable reference copies are hash-pinned before execution. No additional package installation, download or native application is required. See `REPORT.md` for counts and qualifications.

## Optional unchanged external decoder and public fixtures

The external comparison requires an existing approved quantized source root containing `io/origin_project/{container,opju_codec}.py`, at the exact source hashes in `SOURCES.md`, plus NumPy. The loader executes only the two verified read buffers, not package initializers. It does not download or install anything.

```sh
PYTHONDONTWRITEBYTECODE=1 python code/run_codec_experiments.py \
  --quantized-root QUANTIZED_SOURCE_ROOT \
  --public-source-dir PUBLIC_SOURCE_DIRECTORY --out NEW_RESULT.json
```

Repeat with `python -O` and a different output path. Omit `--public-source-dir` for synthetic-only external tests. Output files use exclusive creation. The three public files are named, linked and hash-pinned in `evidence/public-template-streams.json`. Their bytes and the external source are deliberately not bundled.

The fixture manifest itself is SHA-pinned at runtime; it is a **fixed reviewed fixture**, not a general caller-supplied manifest API. Its 13 intervals derive from a previously reviewed sequential-envelope corpus. This harness does not independently discover new native framing. The auditor checked every record and provenance field against the original pinned reports.

The unchanged external decoder maps finite sentinel `0x81aa74fe1c132c0e` to NaN. Its result is checked exactly after that explicitly documented normalization; both integer-only decoders preserve all original bits, including the sentinel. The optional adapted decoder function exists in the inherited reference loader but is **not used** by this experiment. No external decoder is treated as the Origin application.

Public examples use synthetic `float(i)` ramps only to test original stream lengths. They are not scientific replacements, fitted curves, native edits or graph exports. All original files are checked before and after and are never written.

## Unsupported layers

This closes a numeric stream budget issue only when the requested same-count data fits a reachable budget. It does not solve native dataset/page/container serialization, ownership and worksheet binding, cell semantics, repeated segments, outer checksums/offsets/lengths, row metadata, graph dependencies, complete unknown-record preservation, CFB allocation, cache synchronization, graph generation or application lifecycle acceptance.

True Origin cold-open, edit, save, reopen and image/vector export are **not run**. No installed Origin, VM or bridge is used. No editable native artifact or Origin-generated image is produced. Parser agreement, source hashes and mathematical reachability do not substitute for those stages.

## License

Newly authored code and documentation and the inherited project reference code are MIT under `LICENSE`. This does not relicense quantized (Apache-2.0), public native inputs (Etalab-2.0) or their source material. No third-party source or public native files are bundled. See `SOURCES.md`.
