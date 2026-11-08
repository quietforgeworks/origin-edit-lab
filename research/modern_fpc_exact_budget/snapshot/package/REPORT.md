# Exact-budget FPC revision 2 validation

Status: bounded numeric-codec research candidate; portable/harness review completed, pending parent review before any release or capability promotion. Native Origin editing and image export remain unsupported by this artifact.

## What changed

The numeric implementation is identical to the originally reviewed SHA-256 `982b2c9119e8a460bcd850e46db14268164dc28a78faf38fc4153123e2031e25`. Only the external/public runner was hardened to pin its fixed manifest and record code hashes. Six supplemental contract tests and packaging/documentation were added. The original paused evidence was preserved. Whole-repository regressions were not repeated; this validation is confined to the codec, portable harness and their changed evidence/packaging.

## Executed portable checks

All counts below describe one mode, and were reproduced independently in both ordinary CPython 3.12.14 and `-O` on Linux. They are not combined double-count totals.

- Original author suite: 8 unittest groups passed in each mode (`results/author-*.log`). Final suite including the six new contract tests: 14 groups passed in each mode (`results/revision-*.log`). Checks remain active under `-O`.
- Portable independent sumset oracle: all 125,970 width-minimum multisets through length 12, 1,111 short streams, and 63,627 directly serialized schedules passed. Normal and optimized result JSON agree exactly (`results/oracle-*.json`).
- Portable independent adversarial review: 1,351 streams, 12,465 accepted exact budgets, 18,656 unreachable-budget refusals, and 43 malformed/limit calls in each mode. Each mode also fully decoded one million zero words at both 500,000-byte minimum and 8,500,000-byte maximum (`results/adversarial-*.json`). Timing is an observation, not a guarantee.
- New contract checks explicitly demonstrate that extent validation cannot authenticate the external count, that valid residual mutations can change data, and that ignored odd high nibbles are not malformed grammar. They do not claim every changed stream must be rejected.

The independent core proof/review predated implementation inspection; its historical report is `independent-review/IMPLEMENTATION_REVIEW.md`. Revision 2 reruns use the now-portable, hash-pinned included reference paths. The proof is about the supplied grammar, not Origin application behavior.

## Independently reproduced external/public checks

The final runner is SHA-256 `a0d2ea12255d8fdcecc8ebf0234ad3868a145db27ffe6d0bd755a33e7371df7b`. The new auditor executed it under both modes, using only the existing approved source copies and NumPy 2.3.5:

- 483 synthetic sequences, 1,264 exact-budget encodings, 781 nonminimal encodings, 39,543 decoded word occurrences and 566 finite missing-sentinel occurrences in each mode.
- Both integer decoders matched every original raw bit and exact consumed extent. The unchanged quantized API matched after its explicitly expected finite-sentinel-to-NaN mapping. Its source was not adapted for this experiment.
- All 13 recorded complete streams across three SHA-pinned public files decoded, re-encoded to the original exact byte length and decoded again. All 13 same-count synthetic ramps fit those budgets. All 13 independent seeded random-bit examples correctly refused those budgets.
- Every selected stream record exactly matched the prior pinned corpus report; all three source provenance records exactly matched the prior pinned manifest. Original public files were unchanged before/after. No native bytes were written.
- The new auditor separately tested malformed inputs and guarded fixtures in both modes, including actual entrypoint rejection of a tampered or symlinked manifest/source. Each mode also passed 430 additional malformed-input refusals. Audit counts and exact reviewed source hashes are retained in `../audit/PORTABLE_PUBLIC_AUDIT.md` and `../audit/audit-checks-*.json`.

The fixed manifest was originally trusted only through packaged provenance. The new audit identified that qualification, and the runner now checks its SHA before JSON parsing. This addresses fixed-fixture integrity; it is not a general untrusted manifest schema validator.

Concrete illustration: 181 synthetic `float(i)` values have minimum 259 bytes and maximum 1,539 bytes; all intervening sizes are reachable. The two public source budgets of 382 and 1,334 bytes both fit. A separately seeded random-bit 181-word sample has minimum 1,538 bytes and correctly fails both budgets. Synthetic fit-to-size is not a scientific data replacement or a native graph output.

## Evidence boundaries

1. **Raw numeric codec:** bit preservation, mathematical exact-budget reachability, deterministic byte extent, cap/malformed-input refusal, independent raw decoding and external API comparison were tested. This layer is the only completed capability in this revision.
2. **Native dataset/page/container serializer:** not implemented or tested here. No native file is patched. Same compressed length alone does not establish framing, count, row metadata, dataset ownership, graph binding, unknown-record preservation, repeated-segment handling or dependency correctness.
3. **Origin application lifecycle:** cold-open, edit, save, reopen and export are not run. Nonminimal-width acceptance by Origin is unknown. No graph/image/vector export was generated by Origin. No VM or application bridge was started.
4. **PowerPoint/OLE lifecycle:** no OLE or PPTX mutation, refresh or application inspection was performed in this revision.

The hard cap tests use zero data; varied-bit tests use smaller streams. The algorithm is O(n) with fixed predictor tables and a per-word minima array, but caps are not whole-process memory/time guarantees. The independent decoder shares the same supplied format specification and is not an independent Origin format source. Public provenance was checked locally against previously reviewed artifacts, not freshly relicensed or fetched remotely.

## Packaging

The source-only archive contains generic source, synthetic tests, public provenance metadata and reports. It excludes user files, native inputs, raw public scientific data, third-party source, caches, credentials, absolute local fixture mappings and application binaries. A manifest freezes every included file. No upload, publication or stable-skill promotion is performed by this task.
