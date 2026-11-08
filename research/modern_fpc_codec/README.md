# Exact-bit FPC numeric stream research

This isolated, source-only codec milestone encodes arbitrary binary64 **bit patterns** into reversible FPC numeric streams. It does not write an OPJU, edit a CFB/PPT container, generate an Origin graph, or demonstrate acceptance by Origin. Nothing in this package splices bytes into a native file. It neither digitizes curves nor refits data.

## License

The newly authored code and documentation in this package are distributed under the MIT license in `LICENSE`, with the same copyright notice as the authorized project repository. This grant does not relicense third-party software, public native inputs, or source material identified in `SOURCES.md`. Quantized remains Apache-2.0; its code is not bundled here. The test loader only accepts separately supplied SHA-pinned source copies.

## Interface

`code/fpc_numeric.py` needs only Python 3.10+ standard library; tested with CPython 3.12.14 on cloud Linux.

- `encode_bits(raw_le: bytes, *, max_values=1_000_000, max_output_bytes=8_500_000) -> bytes`
- `decode_bits(stream: bytes, count: int, *, exact=True, max_values=1_000_000, max_input_bytes=8_500_000, max_output_bytes=8_000_000) -> (raw_le: bytes, bytes_consumed: int)`

Each eight bytes of `raw_le` is one **opaque little-endian uint64 representation** of a binary64 value. Supply original bit representations, not decimal text or a float-converted NaN. Every bit is preserved, including signed zero, subnormals, infinities, signaling/quiet NaNs and payloads, and Origin's finite missing sentinel. There are no float operations, missing-cell conversions, rounding, fitting or numeric reinterpretation in the codec.

Both calls initialize new 4,096-entry FCM and DFCM state tables. Empty input is supported. A stream has no count header. The caller must retain the exact count in separately validated metadata. Return bytes are deterministic. Input is immutable `bytes`, not `bytearray` or a view. Invalid sizes/types, truncation, trailing data in strict mode, and exceeded budgets raise `FPCError`, including under Python `-O`.

The default hard cap is one million values. Caller limits can only tighten caps. Encoded/raw byte budgets are checked before the corresponding allocation/append; they do not claim to be whole-process heap quotas. Tables, integer objects and temporary bytes add bounded overhead. The encoder returns no partial output on failure.

The encoder emits low nibble first and then high nibble, with that pair's residuals following the control byte. Width codes mean `(0,1,2,3,5,6,7,8)` bytes. A four-byte residual is stored in five bytes. Bit 3 chooses DFCM. The encoder selects the numerically smaller unsigned XOR residual; ties select FCM. The unused high nibble of an odd stream is zero. Other valid encodings can represent the same data. General byte identity with Origin is neither required nor established; the bounded corpus observations are recorded in `REPORT.md`.

## Exactness argument

Assume encoder and decoder have equal state before a value, initially all zero. They compute identical FCM and modulo-2^64 DFCM predictions. Let the selected predictor be `P` and the source word be `V`. The encoder emits `R = V XOR P`; the selected width stores every nonzero bit of `R`. Promoting width four to five only adds a zero byte. The decoder therefore recovers `(V XOR P) XOR P = V` exactly. Both then use the same recovered word for the same modular stride, table assignments and hash updates, so the state equality is preserved by induction. Pairing only changes framing, not sequential updates. Odd streams do not decode the unused high nibble. This establishes the codec identity under the stated grammar, not that every Origin variant uses that grammar.

## Framing and integrity limitations

- `exact=True` proves full consumption of the supplied byte extent, not the count's correctness or stream integrity.
- Example: `[1,1]` encodes as `01 01`. Both count one and count two consume those two bytes because the second residual has zero width. Count must come from trusted, validated outer framing.
- `exact=False` returns the end consumed for the requested count and leaves any later bytes unconsumed. It is intended for a **complete known-count stream** followed by a trailer/next stream. An arbitrary shorter prefix can stop inside a pair; its offset is not a resumable decoder checkpoint, and predictor state is not returned.
- FPC has no checksum. A mutation can be a valid stream containing different data. Tests distinguish deterministic rejection from valid-but-changed decoding.
- A fresh encoder call is a reset boundary. Concatenated independently encoded streams must be decoded separately with each original count. No cross-stream state is supported or inferred.

## Verification layers

1. Hand-derived small byte fixtures, all widths/selectors, predictor hash/stride reuse and modular wrap.
2. `independent-review/independent_fpc_decoder.py`, authored by a separate reviewer from the supplied grammar **before reading this encoder**. It is independent implementation work, not an independently sourced Origin format oracle. It shares the same pinned-codec-derived algorithm specification.
3. Thousands of seeded exact uint64 sequences, edges, varied NaN payloads, trailer checks, malformed/truncated inputs, mutations, resets and hard-cap boundaries, under both ordinary Python and `-O`.
4. Previously approved, unchanged SHA-pinned quantized revision `431deeb7c8473503970ca56b78cc1678f57d373d`, with exact decoded bytes and consumed lengths compared externally. Only two verified source modules are executed, with no package initializer. Nothing is installed or downloaded.
5. Genuine allowlisted public native FPC streams, extracted only through complete sequentially parsed dataset envelopes. Original source files are SHA-checked before/after; an opt-in matrix parser's added streams are labeled separately. Source streams are independently decoded to exact bits, re-encoded, then decoded independently and externally. Original datasets are not rewritten. No claimed proof of cell meaning or dataset ownership is inferred merely from codec success.

### External oracle qualification

The unchanged quantized `_decode` API maps the finite Origin missing sentinel `0x81aa74fe1c132c0e` to NaN. It therefore cannot be a universal exact-bit oracle. Tests separately check:

- Its unchanged output exactly agrees with the source words except that explicit documented mapping; source and re-encoded streams give identical unchanged-API results and exact consumption.
- A clearly labeled **adapted external raw decoder** temporarily sets only its module's `ORIGIN_MISSING` global to NaN, disabling the equality-based normalization, then restores it in `finally`. The verified source code is unchanged. This synchronous, thread-unsafe, test-only adapter is not the unchanged external public API.
- Independent integer-only decoding and this package's integer-only decoding both retain all raw bits, including the sentinel.

Neither external route is native Origin acceptance. NumPy is required only for these optional external tests; the codec and synthetic portable suites do not require it. Dependencies and hashes are in `evidence/dependencies.json`.

## Reproduce the portable checks

From this package directory:

```
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python -O -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s independent-review -v
PYTHONDONTWRITEBYTECODE=1 python -O -m unittest discover -s independent-review -v
```

Optional external check, after explicitly supplying the already-approved pinned source tree (root contains `io/origin_project/container.py` and `opju_codec.py`):

```
python code/run_external_synthetic.py --quantized-root QUANTIZED_SOURCE_ROOT --out NEW_RESULT.json
```

Optional public audit requires the allowlisted public files, the two separately supplied SHA-pinned read-only envelope parsers, and the external decoder:

```
python code/run_public_corpus.py --manifest evidence/public_sources.json --source-dir PUBLIC_FILES_DIRECTORY --strict-parser STRICT_PARSER.py --matrix-parser MATRIX_PARSER.py --quantized-root QUANTIZED_SOURCE_ROOT --out NEW_RESULT.json
```

The corpus runner never installs or fetches anything. Public native files, original third-party sources, local path mappings, private files, raw numeric data, and native containers are deliberately excluded from the source-only package. Outputs use exclusive creation. Detailed public evidence is identified by public filename, source URL, source hash, byte interval, count and raw/encoded hashes, without embedding source values.

## Remaining work before native dataset rewrite

This milestone does not solve complete sequential CPYUA framing; ambiguous or unknown property transports; unhandled descriptors or scalar forms; verified dataset-to-book/sheet/plot ownership; replacement segment and repeat-run framing; descriptor/stored/active-row consistency; offsets, sizes, pointers and opaque trailing-section preservation when lengths change; CFB stream allocation/writeback; graph and analysis dependencies; transaction/recovery behavior; or Origin's actual open/edit/save acceptance. Arbitrary data generation must be integrated and reviewed separately, followed by native application validation. Preserving a fit's exact existing model/parameters does not authorize recalculating it elsewhere or claiming that a fit will update correctly when data changes.

See `REPORT.md` for measured scope and exclusions, not a blanket modern OPJU compatibility claim.
