# Native active-row research: bounded success, allocation expansion still blocked

## Result

The exact public legacy OPJ native line-and-symbol template now has a narrowly tested **7-row, 49-row and 50-row active-prefix route**, with its original **50-row allocation unchanged**. This is not a general variable-length OPJ writer and is not Origin application acceptance.

In unmodified official LabPlot 2.12.1, all three candidates were imported through the real application's Origin import dialog and freshly drawn. Read-only public column APIs returned all 14, 98 and 100 active X/Y binary64 values bit-for-bit, including negative zero and long decimal inputs after the explicitly audited binary64 conversion. The remaining 86, 2 and 0 app cells respectively were missing/invalid.

The actual imported XYCurve's `pointsUpdated` Qt signal was observed passively with QSignalSpy. It emitted exactly 7, 49 and 50 logical points, with ranges 0–6, 0–48 and 0–49. Every emitted X/Y point was bit-for-bit identical to the corresponding raw CSV value. Two such emissions were captured per final case. These are the application's own curve geometry inputs, not reconstructed data, predicted point counts, extracted previews or locally plotted replacements. The observer did not call recalc, retransform, change columns, or supply data; selecting the imported graph caused the observed normal application rendering.

The actual app-owned saved project differs from the paired original import only in the two Book1 column payloads, after excluding documented generated metadata. The complete Graph2 object, axes, curve styles and explicit `test_tree_import/Folder1/Book1/A` and `/B` source bindings are unchanged. All six spreadsheet, two workbook, three matrix, three note, two folder, one graph-worksheet and one xyCurve objects remain present. The parsed-element comparison includes exact XML text and tail payloads, without whitespace normalization. It is not a raw-byte LML serialization comparison.

**51 and 257 requested rows were refused before creating an output directory.** They were not generated, opened, or validated, and are not failed application imports. Allocation expansion remains unimplemented because this template's complete native range and resizing dependencies are not established.

## Structural ownership, not a search-and-replace guess

The exact template has SHA-256 `ea50c9b97b063898f654a6189b30ca5d8be8b52ad4c9469b3934cd009185265a`, 231,494 bytes, 478 framed records before offset 228,955, and an opaque tail thereafter.

- Two data headers begin at frame offsets 103 and 760. Each is a 140-byte header owned by Book1_A or Book1_B, immediately followed by its 500-byte numeric data frame at 249 or 906. The 10-byte cell width gives 50 allocated cells per column.
- Official 2.12.1 `OriginAnyParser.cpp` reads three consecutive integers at data-header payload offset 0x19 and stores them as numRows, beginRow and endRow. The source template values are 50, 0, 50. Only the last of these, at payload 0x21 (absolute offsets 141 and 798), changes for the 7/49-row candidates. Allocation, first row and data-frame sizes stay exact.
- Official `OriginProjectParser.cpp` allocates a spreadsheet using the parsed data vector's length, then reads numeric data only from beginRow inclusive to endRow exclusive. Thus 50 allocated app cells and 7/49 active values are different facts, both tested.
- Official `XYCurve.cpp` copies only valid, unmasked X/Y rows into its logical-point vector and emits that vector from `pointsUpdated` before mapping it to the drawing. The observed signal and actual source-column validity independently confirm the selected plotted rows.
- The curve still binds X/Y dataset IDs 1/2 at graph-curve payload offsets 0x23/0x04, which the official parser explicitly consumes. These fields and the entire graph region are byte-identical.

There are also `(0,50)` pairs at worksheet/graph property-header payload offsets +7/+11. Previous multi-fixture correlation did not prove their semantics. The reviewed official liborigin parser and old importOPJ documentation do not establish their meaning, and the inspected quantized revision's different workbook writer does not provide an applicable graph-range oracle. They remain **opaque and unchanged**. This experiment validates a dataset active prefix that the tested application uses for the curve; it does **not** claim to implement native per-curve subset selection or decode those fields.

For full expansion, changing only the known allocation and data-frame lengths would leave these unresolved native fields and other possible size/offset dependencies unproved. A reader ignoring a field cannot validate its new value. No speculative resize candidate is promoted as safe.

## Scope and preservation

`native_active_rows.py` accepts only this exact source hash and the tested row counts 7/49/50. It rejects repatching, unknown counts, changed source bytes, malformed record framing, changed identities/bindings, invalid numerical tokens, nonfinite/missing values, conservative underflow cases and out-of-axis values. Only the two documented endRow integers and active binary64 cells are writable. It preserves every other byte, including all cell tags, inactive raw cells, allocation, native graph source, unresolved range-like fields, annotations and opaque tail. Atomic no-overwrite output and a manifest-backed, source-hash-verified exact rollback are provided.

The inactive raw cells are **retained, not erased or anonymized**. They become missing in this LabPlot import due to the active bounds. This code is not a private-template sanitizer. Only the public fixture and toy synthetic CSV were used. This package contains no user documents or data.

The fixed axes are X[-5,55], Y[-0.1,1.1]. Inputs outside those limits are refused. Nonzero start rows, arbitrary counts, disjoint ranges, independent X/Y lengths, graph-range edits, data-frame resizing and arbitrary OPJ/OPJU/OGGU projects are unsupported. The adapter performs no fitting, smoothing, downsampling or digitizing. The application performs its normal rendering.

## Evidence and tests

- `verified-results.json`: full local app comparisons, including original public-fixture payload differences. Do not put this complete file in the source-only public package.
- `application/results/{original,active7,active49,active50}/`: isolated real app runs, unchanged-source hashes, raw public-column doubles, passive curve signal records, app screenshots and app-owned LML saves.
- `application/final-observer.sha256`: one frozen observer binary for all four final runs. The earlier exploratory7 run is separate and not used as final acceptance.
- `candidates/generated{7,49,50}/`: raw CSV, native source candidate, full conversion ledger, structural before/after evidence and byte-exact rollback. Fixture-bearing files stay local.
- `refusal-evidence.json`: explicit 51/257 guard rejections with no output directory.
- `source-provenance.json` and `field-evidence.json`: official source/binary hashes, consumed field locations and precise limits.
- 64 tests pass normally and under `python -O`, with all public-fixture tests actually run. The original 28 tests are supplemented by 36 review regressions. They cover allowed masks, binary64 ledgers, inactive-byte preservation, wrong source, repatching, framing, opaque fields, row counts, rollback/candidate/manifest attacks, numerical hazards, atomic no-overwrite and symlinks.
- `verify_application.py` passes normally and under `python -O` against the retained evidence and independent app reruns. Application numerical and Qt observations do not use an OPJ parser. A separate source-artifact audit regenerates the exact bounded edit, validates complete manifests/inspections and links actual source snapshots/hash records to it. The whole-project comparison ignores only UUID/creation_time plus three separately hashed project UI attributes: dockWidgetState, modificationTime and thumbnail.
- All four final Graph2 screenshots were visually inspected. The 7-point active prefix, 49-point endpoint, 50-point curve and original public template differ as expected. Screenshots supplement, rather than replace, the signal and numerical tests.

The verified official LabPlot AppImage/runtime and source archive were reused. The inspected quantized revision `431deeb7c8473503970ca56b78cc1678f57d373d` was read but not executed. No new unknown upstream software was downloaded or run. App runs used private HOME/XDG/temp profiles and Qt offscreen. Exit 124 is expected: the app is deliberately terminated at 11 seconds after captures and Save As, without editing the source OPJ.

## Explicit validation limits

Origin reopen, redraw, update, recalculation, save and saved-native-file reopen: **NOT RUN**. Official Origin Viewer: **NOT RUN in this phase**. LabPlot's Save As writes its own LML format; it is not an Origin OPJ save-cycle test. The retained opaque fields could cause different native behavior or be normalized by Origin. No automatic-recalculation or full dependency-semantic safety is claimed. The source retains its original opaque content; byte preservation is not semantic proof.

The bounded source-to-LabPlot result is useful progress beyond fixed50, while Origin compatibility and allocation expansion remain blocked on independent native evidence. The stable compatibility claims must not be upgraded based on this experiment.

## Publication boundary

`publication/` is a prepared, source-only package containing this authored report, authored patcher/tests/observer/verifier, toy CSV, compact synthetic verification and source provenance. It contains no OPJ, OLE, PPT, screenshots, app binaries, full app saves, private data, or third-party source implementation. Fixtures are exact-hash external prerequisites and are not redistributed. See `REVIEW.md` for independent replication, verification corrections and distribution boundaries.
