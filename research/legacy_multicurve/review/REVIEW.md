# Independent review: explicit multi-curve native-record insertion

## Decision

Accepted as a **source-only, exact-public-fixture, LabPlot-only research supplement** after the three corrections below. No blocking defect remains within that narrow scope. This is **not approval for Origin-safe export**. The default refusal must remain in every candidate-generating entrypoint.

The frozen author source manifest SHA-256 is `e531261e34f48ba3841020822b48e42787fe57bf8885d61bdef2f8c7cac48c26`. All 25 listed files were independently hashed before replication and checked again after tests. No source edits were made during the final review. The review's portable package adds only authored review/checking code and compact evidence.

## Findings and severity

1. **Medium, fixed: wrapper wrote before refusal.** The initial `make_cases.py` created a 4,169-byte synthetic JSON before noticing an existing candidate destination. The corrected wrapper preflights every path, the exact template and the complete intended transformation before writing. It exclusively creates raw input and cleans only its own unchanged raw inode after generation failure. Independent tests confirm existing output and ancestor-symlink refusals leave no new raw file, failure rollback is clean, and a replaced raw file survives unchanged.
2. **Medium, fixed: synthetic wrapper bypassed explicit research opt-in.** The initial wrapper unconditionally enabled research output. `make_case()` now defaults to refusal before I/O and its CLI requires `--labplot-only-research`. The core API/CLI already had the guard. Independent tests confirm all three APIs refuse with no research opt-in, including integer `1` rather than Boolean `True`.
3. **Low, fixed: evidence comparator erased XML whitespace.** The initial application verifier stripped all whitespace-only text/tails, weakening the claim of exact unrelated project preservation. Final code compares text and tails exactly. The only allowed structural indentation adjustment is the Book1 column sibling tail: every nonfinal column must match original A's tail, and the final column must match original B's tail. Original B's tail is restored after removing inserted columns. Regression tests reject unrelated, curve, and column whitespace mutations.
4. **Native compatibility blocker, intentionally unresolved.** The preserved global header contains a 16-bit value 26 at payload +4 while the candidate dataset inventory grows to 27/33/43. The official reader does not establish that field's meaning. Cloned opaque dataset, worksheet and graph metadata may include Origin identifiers, associations, counts or other state. All 50-row bounds remain `(50,0,50)` in dataset headers and `(0,50)` in worksheet/curve payloads, but preserving those bytes does not prove Origin semantics. Origin reopen, edit, refresh/recalculate, native save, close and saved-native-file reopen remain **NOT RUN**.

No claim is made for arbitrary templates, unequal rows, cross-sheet data, missing values, formulas, new worksheets, OPJU/OGGU, native sanitization, complete legends, or publication-quality styling. All new curves copy the same black style; the native template legend still contains only original B. The existing public fixture's unrelated content is retained, not sanitized.

## Independent native-file checks

The reviewer generated all three candidates from the frozen source and synthetic inputs in a separate replication tree. A separate checker imports no author parser/writer. It walks the exact framed stream and independently reconstructs the permitted frame changes from the original fixture and raw JSON.

- 2 curves: 234,416 bytes, 490 frames, 27 dataset records, 200 exact source cells. SHA-256 `3a4be4178c47eddf62287cd1a391ef5c6f4b0c01e997e4a8a64ce4c0def78218`.
- 5 curves: 243,182 bytes, 526 frames, 33 dataset records, 500 exact source cells. SHA-256 `459ba0e761c0e8abfb12e61fde627cb5418c302e54cff6776bb13d7f440f78e9`.
- 10 curves: 257,792 bytes, 586 frames, 43 dataset records, 1,000 exact source cells. SHA-256 `ffaf7eb4911fe7d27fe91802786a9cf3abfa32ae71052f5c17e6b391e8e6a1ba`.

The pinned original has 478 frames with tail starting at byte 228955. The independent reconstruction uses original zero-sentinel frame indices 77, 265 and 453 for datasets, Book1 columns and Graph2 curves. Only original A/B data frames are replaced. All original dataset slots 1–25, including matrix-related slots, retain their order and contents except the intended A/B values. Appended pairs occupy 26/27 through 42/43. No existing slot is dropped or renumbered.

Every new header, mask, data frame and delimiter has the expected extent. Names, worksheet X/Y designation and graph selectors are checked for every pair A/B through S/T. Each numeric cell has the expected tag and binary64 bits. Cloned metadata is byte-exact except the enumerated selector/name fields. Every other original frame, global header and opaque tail is identical after relocation. Removing only insertions and restoring original A/B data recovers the exact original; each emitted rollback file also matches the fixture byte-for-byte. The conversion ledger preserves every raw lexeme, unique identity and expected binary64 result.

## Independently rerun actual application

The reviewer rebuilt the authored passive Qt observer. Its SHA-256 is `2e60593881838e6cd485e11b40ccce41dc4fa726b717e5f47187f486a6bcdca9`. The official LabPlot 2.12.1 executable and importer library hashes are pinned in `review/evidence/rebuilt-runtime-hashes.json`.

The original fixture and all 2/5/10 candidates were imported again using fresh reviewer-owned HOME, XDG, runtime and temporary directories. The observer opens only a read-only snapshot through the actual app UI. It does not parse Origin, supply numeric replacement data, add curves, set curve bindings or manually recalculate curves. It reads actual imported object pointers and public Column/XYCurve APIs, passively captures `pointsUpdated`, and performs Save As to the application's own LML format.

The independent checker reads actual observations and saved arrays, not author report flags:

- Exactly 2/5/10 actual XYCurve objects with distinct explicit X and Y column identities.
- Exactly 200/500/1,000 worksheet API cells, all matching source binary64 bits.
- Each curve's own bound X/Y columns contain all 50 expected valid, unmasked cells.
- Two passive point-update emissions per curve, each containing all 50 expected ordered pairs and range 0–49. That verifies 100/250/500 distinct source XY pairs per case, each observed twice.
- All X vectors are pairwise different, including the second X's interior negative zero; an accidental shared-A binding cannot pass.
- Every application-saved LML array and X/Y binding is exact.
- Every new column and curve has the declared cloned metadata/style. Only the original curve is enabled in the preserved legend.
- After removing intended inserted columns/curves and restoring original A/B payloads and the one structural sibling tail, the complete serialized project is identical except declared generated UUID/creation timestamps and root modification time, dock state and thumbnail. All XML text/tails are checked exactly.
- Baseline original API cells and original passive point emissions independently match the original native data.
- Original inputs, read-only imported snapshots, actual import paths and before/after hashes agree and remain unchanged.

The 10-curve actual screenshot was separately inspected: it shows a dense, overlapping black square-marked graph with original A/B axes and only B legend. Pixels are supplementary, not proof of exact curve count or values. All four planned application runs end with timeout status 124 after observations and Save As; this is not reported as a natural successful app exit. LML save is not native OPJ/OPJU save, and no Origin executable was run.

## Tests and safety boundary

- Final author suite on independently generated evidence: **48 tests pass**, both normally and under `python -O`.
- Source-only author suite: **16 pass, 32 explicitly skip**, both normally and optimized.
- Reviewer-authored guard suite: **13 tests pass**, both normally and optimized. These include no-I/O refusal at all entrypoints; missing/unequal input and identity checks; numeric conversion refusals; leaf/ancestor symlinks; FIFO inputs; source mutation; injected publication failure; concurrent directory/symlink destination preservation; and wrapper preflight/rollback with replacement ownership.
- Independent native/application checker passes normally and optimized on all 2/5/10 fresh reruns.
- Author application verifier independently passes on the reviewer's observations, normally and optimized.
- Both shell entrypoints pass `bash -n`.

Atomic `renameat2(RENAME_NOREPLACE)` publication prevents overwriting an existing or concurrently created destination on the supported Linux system. Failed pre-publication generation cleans staging. Path preflight assumes trusted, stable ancestors; it is not a security boundary against a hostile process replacing ancestor directories between checks. Crash durability and killed-process cleanup were not tested, and no filesystem sandbox guarantee is claimed. App runner results and profiles are intentionally retained for evidence rather than being a transactional workspace.

## Reader provenance and licensing

The official source archive was rehashed and selected source members checked against the extracted files. The reviewed source establishes sentinel-terminated lists, ordinal dataset allocation including matrix placeholders, graph selectors at +0x04/+0x23, the actual model internal-pointer identity and the `pointsUpdated` signature/render location. Source hashes are recorded in `review/evidence/source-provenance.json`.

The original GPL-licensed LabPlot/liborigin implementations remain external and are excluded from the portable package, as are their headers, archive, binaries and runtime. The observer uses Qt headers and existing application APIs; its authored source contains no copied Origin parsing implementation. The existing project MIT license is unchanged for authored material. This is a source-only review, not approval to redistribute a linked observer or any third-party binary under MIT. Such distribution needs a separate dependency/license review.

The portable package contains authored code/tests/docs, compact reports and hashes only. It excludes native files, fixture-bearing manifests/payloads, full application saves, screenshots, runtime/profile data, compiled observers and external source extracts. No private user files, Mac, VM, stable skill or published repository were accessed or changed by this review. Nothing was published.

## Reproduce review checks

First follow the source README to create all cases and actual application evidence with the external fixture/runtime. Then, from the package root:

```sh
python review/independent_checks.py "$ORIGIN_PUBLIC_FIXTURE" --evidence-root .
python -O review/independent_checks.py "$ORIGIN_PUBLIC_FIXTURE" --evidence-root .
export MULTICURVE_SOURCE="$PWD"
python review/test_independent_guards.py -v
python -O review/test_independent_guards.py -v
```

The independent checker writes nothing unless a new `--output` filename is supplied. No runtime, source archive or native fixture is downloaded by these checks.
