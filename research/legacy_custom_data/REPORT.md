# Historical application research result, 2026-11-08

Repository packaging note: this report records earlier local runs. Source-only checkout tests do not repeat those application runs. See [packaging notes](../../docs/native-data-packaging.md) for current distribution and integrity checks.

## Delivered

A separate full-artifact generator/verifier/recovery adapter under `src/`, with no change to the stable workbench or any frozen source. Only the fixed50, single-curve, active7/49/50 branch is supported. All conversion and byte-patch algorithms remain identical to their reviewed frozen copies. No expanded allocation or multicurve logic is combined into this branch.

The 50-row known-synthetic custom example is the primary case. Its source CSV SHA-256 is `fe668293f9efbc5591636554489d49cb1b377ef993b218a70b04d4d0aa92afc0`; native candidate SHA-256 is `ba87a622332f8ef1cbf1f13a148369ad903ec7988f36dea407a5b29c6f4b1aa0`. The raw input uses non-toy values, CRLF, quotes, distinct numeric spellings, signed zero, axis extremes, the exact halfway value above 1, the minimum normal binary64 neighborhood, and fractional rounding. All original CSV bytes survive, alongside the exact per-cell binary64 ledger.

The API retains `measured`, `synthetic` and `unspecified` declarations exactly, always with `independently_verified: false`. Schema tests simulate a measured declaration; the actual observed research cases are expressly synthetic. No real measurement claim has been verified or invented.

## Source-integrity and refusal tests

`tests/test_custom.py` passes under normal Python and `python -O`, with 14 test methods and adversarial subcases. Checks include:

- All three supported row counts, full ledgers, signed-zero bits, round-to-nearest-ties-even, inactive data disclosure and exact rollback.
- Every supported native cell edit plus both end fields: 218 per-offset mutations across active7/49/50, all rejected.
- Every generated artifact, all three cases: 24 independent one-byte mutations rejected.
- Original source, unknown/graph bytes, inactive cells, manifest/inspection/schema/type changes, duplicate JSON keys, NaN/Infinity, missing/extra bundle files, declared-measured preservation, and coordinated input/output substitution against external source anchors.
- Invalid/missing numbers, malformed CSV, unsupported counts, Origin missing sentinel, overflow, underflow, subnormals, lossy integers, out-of-axis values and exact opt-in type checks.
- Exact frozen source inventory/hash mutation; bounded regular inputs; symlink, traversal, FIFO, existing-output and macOS refusal; racing destination preservation; ordinary interruption cleanup and a simulated post-publication failure that leaves the published directory intact.

Normal and optimized logs are in `evidence/tests-normal.log` and `evidence/tests-optimized.log`. A separate 3-method source audit test suite passes normally and under `-O`, including tampering every declared source/report, extra/missing/symlink members and external manifest anchors. Source/report inventory checks require a trusted external manifest hash against coordinated package replacement.

## Fresh independent official application observation

No software or fixture was freshly downloaded. The existing official LabPlot 2.12.1 executable/importer and launcher matched their known hashes. The dependency graph is not exhaustively pinned; local execution provenance is not cryptographically authenticated. The unchanged authored observer was recompiled locally in this research directory. Each case and its fresh public-template baseline ran in isolated new profiles against read-only copied OPJ snapshots.

- custom50: 100/100 active API cells bit-exact, all 50 actual logical XY points bit-exact, two point-signal emissions, saved LML doubles bit-exact.
- custom49: 98/98 active API cells bit-exact, all 49 logical XY points bit-exact, two point-signal emissions, two inactive API cells missing.
- custom7: 14/14 active API cells bit-exact, all 7 logical XY points bit-exact, two point-signal emissions, 86 inactive API cells missing.

Native A/B inactive values physically remain for custom49/custom7, despite the importer exposing them as missing. The complete retained native values are recorded in bundle metadata. With custom50, every A/B cell is replaced, but unrelated source data remains.

The independent application validator compares native snapshot identity, all real column API bits, all curve-linked source bits and validity/masks, every logical point emission, both complete saved binary64 column payloads, exact graph bindings/configuration, and the full saved project against the fresh baseline. After explicit UUID/creation-time and root UI metadata exclusions, the only two saved-project differences are the A and B numeric payloads. It never parses native cells to fabricate the expected application result.

`evidence/application-verified7.json`, `application-verified49.json` and `application-verified50.json` record the input-specific results. `tests/test_observation.py` exercises every observed API cell, every linked curve row and every logical XY point (300 numerical mutations), receipt/runtime identity, source snapshots/hashes, saved LML and JSON/type errors. Normal and optimized logs are separate. Screenshots and logs are supplementary evidence; the machine acceptance checks numerical/model results, not screenshot appearance.

Visual inspection of `application/results50/custom/Graph2/002-window1.png` shows the actual LabPlot project tree and a bound line/symbol graph with the deliberately unsorted stress-input zigzag, endpoints and legend B. It is a research stress graph, not a publication-quality figure. Screenshot appearance does not establish exact numeric preservation or Origin editability.

## Remaining barriers

Origin open, edit, update, recalculate, native save, close and reopen are all NOT_RUN. The original unresolved range-like native fields remain unchanged rather than guessed. This research therefore cannot promise that Origin treats all rows, edits, recalculation or saving identically to LabPlot. A user needing dependable editable Origin delivery still requires actual Origin lifecycle testing on each supported boundary and a separate review.

This is not a generic template writer, OPJU writer, private-template sanitizer, arbitrary-precision native cell serializer, new-sheet generator, expanded-row/multicurve combination, Mac write primitive, stable release or native-binary distribution. Native-safe export remains blocked. Source code and reports are reviewable; actual native files, compiled helper, app profiles, saved LML and screenshots stay local and are not included in source-only distribution.
