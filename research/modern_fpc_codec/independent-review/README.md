# Independent FPC decoder review

This decoder was authored from the bitstream specification in the parent task before reading the encoder. It is an independent implementation of the **same specified algorithm**, not an independent Origin implementation or oracle. No native Origin acceptance, modern OPJU writing, container compatibility, or third-party codec execution is established by these tests.

## API and limits

- `decode_prefix(data: bytes, count: int)` returns exact uint64 bit-pattern integers and byte consumption. It permits trailing input and ignores an unused final high nibble.
- `decode_strict(data: bytes, count: int)` rejects trailing bytes.
- Both initialize fresh predictor tables and use no floating-point conversions.
- Counts are bounded at 1,000,000 and whole input length at 16,000,000 bytes. These are implementation resource limits, not claimed format limits. Boolean counts and mutable input are rejected.
- Checks use explicit exceptions and remain effective under Python `-O`.

## Verification

Ten unittest methods passed with both `python -m unittest -v` and `python -O -m unittest -v`. Tests use hand-derived bitstream fixtures rather than encoder output. They cover all eight residual widths and both selectors, pair order, ignored odd high nibble, FCM table reuse and hash selection, DFCM stride prediction and modular wraparound, negative stride bits, empty data, exact prefix consumption, strict trailing-byte rejection, every byte truncation of a mixed fixture, input/count limits and types, and fresh state.

Residual widths and control semantics come solely from the task's pinned-codec-derived specification. This test suite establishes agreement with that specification, not its correctness for every real Origin file.

## Encoder integration review

Reviewed `code/fpc_numeric.py` and `code/verified_oracle.py` only after the independent decoder and its hand-derived fixtures were complete. No encoder correctness or budget-check defect was identified in this review. The uint64 arithmetic, residual-width remapping (four bytes promoted to five), low/high ordering, state updates, and deterministic FCM tie choice match the supplied specification. Hard caps and caller-tightened limits are explicit and effective under optimization. Output budgets constrain encoded/raw bytes, not total Python heap consumption. Prefix decoding still validates the size of the entire supplied input.

Added seven adversarial test methods in `test_encoder_adversarial.py`, bringing the independent-review suite to 17 methods. Both normal and optimized runs pass. Coverage includes 3,000 seeded arbitrary-stream comparisons against the independent decoder, seeded exact-bit round trips (including special binary64 bit patterns without float conversion), hand-calculated encoder bytes, width boundaries, exact and undersized budgets, type/range rejection, odd nibble tolerance and fresh state. No external executable source was run by this review.

### Confirmed API limitation, not a defect

The FPC stream has no intrinsic count or checksum. Encoding `[1, 1]` produces bytes `01 01`. Decoding that stream with count one also passes strict mode because the second residual consumes zero bytes. Thus strict mode means byte-consumption equality, not proof of correct element count or integrity. Count must come from validated external metadata. Prefix offsets are not generally fresh-state resume points: predictor state is not returned, and an odd prefix may stop in the middle of a paired record. No resume claim should be made.

### External comparison ancestry

The test loader hashes the exact source buffer before execution and uses pinned approved modules. The adapter temporarily changes `module.ORIGIN_MISSING` to NaN and restores it in `finally`, suppressing the external decoder's finite-missing-sentinel normalization. Therefore its output is an **adapted external raw decoder comparison**, not the unchanged public external API. The adapter is explicitly synchronous/thread-unsafe and test-only. Independent integer-only decoding remains necessary for exact bit validation. These results do not establish an independently sourced native Origin oracle, OPJU writing compatibility, or native Origin acceptance.

## Final core and corpus-runner review

Final core SHA-256: `43c3415066ed12f1f158e8406f6d62d1dc767daea537e31441865934e6c70dbc`.
Test-only loader SHA-256: `2e6281e200590d83c063fd1e633caa09988f511ba34fe925c2807871a105b98d`.
The final core adds the requested explicit nonresumable-prefix documentation. All 17 independent-review tests were rerun against this core and pass normally and with `-O`.

Reviewed `code/run_public_corpus.py` and the normal-run report without rerunning the external corpus. The runner's raw truth begins with the independently authored integer decoder; it compares both original and reencoded streams against the own decoder and the adapted external decoder, including exact prefix consumption with a trailer. It additionally checks unchanged-external results against precisely the expected sentinel normalization. Original files are read-only and rehashed. No false-oracle substitution or native acceptance overclaim was found.

Independently reconciled the report's records and totals: 167 files, 159 with tested streams, 7,843 unique stream extents, 9,949,997 words, 2,404 streams additional to strict parsing, 2,050 experimental matrix-framed streams, and 60 sentinel values in 36 streams. All per-file before/after hashes match; all 7,843 original/reencoded stream SHA-256 pairs match. This last observation is limited to this corpus and is not universal encoder byte-identity proof. The control histogram totals 9,949,997 words. The optimized corpus report was still pending at this review checkpoint and is not certified by this review. This was a runner/report audit, not an independent rerun of the corpus or independent validation of container framing.

### Optimized completion and final freeze

The completed `results/public-corpus-optimized.json` is exactly equal to the normal result after removing only the `optimize` field (0 versus 1). This confirms identical full per-stream records, counts, source hashes, raw hashes, encoded hashes, dependency hashes, and all reported outcomes for both runs. Final core SHA-256 remains `43c3415066ed12f1f158e8406f6d62d1dc767daea537e31441865934e6c70dbc`.

Reviewed final package `README.md`, `SOURCES.md`, and `CHANGESET.md`: scope and oracle limitations are accurately qualified; no blocking scope overclaim found. The synthetic category evidence's aggregate raw-plus-encoded digest matches both external synthetic results (`756bc217cd94fc6ad5f89d0d448ba2883d0a9fc0703fa8189f5d002f20def595`). Category partitions sum to 767,387 words and NaN sign/category counts reconcile. Category evidence reports 36,034 positive zeros, 36,895 negative zeros, 39,604 signaling NaNs, 45,802 quiet NaNs, 65,627 distinct NaN bit patterns, and 3,308 finite missing sentinels. This checks report consistency, not an independent recount of generated inputs. No external corpus execution was repeated for the final review.

Review files are frozen after this entry; no blocking findings remain for the isolated exact-bit FPC research scope. Native container rewrite and Origin acceptance remain unverified and outside this approval.

### License-packaging documentation review

Reviewed the revised root `LICENSE`, `README.md`, `SOURCES.md`, `REPORT.md`, and `CHANGESET.md`. The MIT text bears Copyright (c) 2026 quietforgeworks and the documentation limits its grant to newly authored material. Quantized remains separately supplied Apache-2.0 software; third-party sources and native datasets are neither bundled nor relicensed by this grant. Algorithm provenance and implementation-independence limitations remain explicit. No-upload/no-publication statements now expressly describe the historical experiment, not subsequent package distribution. No licensing-boundary overclaim or stale current-publication statement was identified in these documents. This is a documentation consistency review, not independent legal clearance or verification of the upstream project's license bytes. No code, tests or results were modified and no corpus was rerun for this revision; subsequent integration and publication remain separate gates.
