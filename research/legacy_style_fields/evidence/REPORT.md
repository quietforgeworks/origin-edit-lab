# Native legacy OPJ style research, 2026-11-08

## Results

Two genuine public KDE OPJ fixtures now have eight source-only edits independently observed in official LabPlot 2.12.1. The changes are confined to Graph1's bottom-X tick font, bottom-X axis stroke, first curve stroke, or native layer rectangle. This is not an image-preview edit, new graph serialization, or a claim of Origin compatibility.

- Tick font: stored 18 → 26, only one changed byte per file. LabPlot's bottom-X label size changes 76 → 110 scene-size units in `2graphs.opj`, and 75 → 108 in `single_layer_two_axes.opj`. The title moves to make room; other axis fonts remain unchanged.
- Axis stroke: stored 750 → 1250. LabPlot changes only the bottom-X axis, its major/minor tick strokes, and the dependent title position. Native reader semantics are stored integer / 500; Origin's own UI units were not independently checked.
- Curve stroke: stored 500 → 1250 in the first fixture, 250 → 1250 in the second. Each complete app-owned project changes only the targeted curve width. The single-axes baseline is clamped by the reader's one-pixel minimum, so visual width ratios must not be naively inferred from its baseline.
- Layer rectangle: `clientRect [left,top,right,bottom]` changes from [1151,571,5537,4105] to [1351,721,5337,3955], and from [590,296,2841,2126] to [790,446,2641,1976]. The actual application shrinks the plot area. All four measured paddings match the documented reader conversion; only padding and dependent X/Y title positions change.

Every candidate retains every non-target byte, all source numerical binary64 bits and cell masks, graph bindings, record boundaries, and opaque tail. The actual app's direct Column double access verifies all 128 allocated cells in the two-graph project and all 64 in the single-axes project remain identical. Complete XML text AND tails are compared, not only object counts. Only volatile creation timestamps, UUIDs, and three explicitly hashed project UI metadata fields are excluded.

The single-axes file has an actual `TemplateEMF` payload of 32,588 bytes. Its source payload SHA-256 and all bytes remain identical in all four variants, while the app redraws the requested source changes. The first fixture has no `TemplateEMF` record identified by this narrow profile; it is not claimed to have no possible opaque cache.

## Why the previous title font22 → 30 experiment looked unchanged

The failure is now localized within this reader rather than attributed to the native source field:

1. The real app receives the original title font22 as 26pt after its page scaling, and the edited font30 as 36pt. A read-only interception of the actual Qt `QTextEdit::setFontPointSize` records those values and corresponding HTML.
2. The subsequent real `QTextEdit::setCurrentFont` applies the old `Sans Serif,9,...` font. The incoming 26pt/36pt HTML becomes 9pt HTML at this exact boundary.
3. Both source files end with identical 9pt titles. This matches the official `TextLabel.cpp` existing-text path, which remembers the old current font, installs new HTML, selects all, then reapplies the old font.
4. The callsite is in the executable, not the exported `liblabplot` method. Its image-relative offset is `0x7657e0`; the executable is ELF EXEC with load base `0x400000`, so the return virtual address is `0xb657e0`. Disassembly shows `currentFont → setHtml → selectAll → setCurrentFont`, matching the official source and same-version exported library. The app is stripped at this address; no direct TextLabel symbol stack is claimed. The earlier attempted TextLabel-symbol hook produced zero observations, retained as a negative result.

This explains the size loss in LabPlot. It does not prove that Origin respects the edit or that all other rich-text/family cases have the same complete cause. No unsupported global-number replacement was used to obtain it.

## Important layer-mode limitation

LabPlot's default “layers as separate plot areas” route uses fixed padding. Its single-layer counter is incremented and then adds one again before the `numberOfLayer == 1` check, so the inspected path does not use native clientRect there. These geometry experiments explicitly select the existing “layers as coordinate systems” UI option (index 1), without modifying the importer. A paired baseline uses the same mode and fresh isolated profile. The native source edit is unchanged between modes; this setting determines whether this reader observes it.

## Implementation and checks

- `native_style_patch.py`: hash-locked exact-source profiles; structural record checks; narrow typed field edits; complete data bit inventories; cache/opaque-byte protection; reversible manifests; atomic no-overwrite output. It is intentionally not a general OPJ parser or writer.
- The original 26 methods plus 21 independent-review regression methods now total 47 passing methods in normal Python and `python -O` with all three exact fixtures. Source-only runs execute 33 methods and skip 14 fixture-dependent methods. Checks include exact byte-diff preservation, complete numerical masks/bits, rollback, malformed framing, wrong source, repatching, no-op, booleans/floats, rectangle bounds, manifest/candidate tampering, no-overwrite publication, XML text/tail whitespace, font-probe guards and shell input rejection.
- CLI patch and restore executed, with restored bytes equal to the pinned original.
- `application/`: local observer source, isolated runner, actual app-owned saves, read-only numerical logs, captures, and font boundary logs. The final twelve GUI runs use a single frozen observer build; earlier exploratory runs are retained separately, not used as final acceptance.
- `compare_application.py` checks complete serialized projects and actual double readback. Its reviewed version compares text and tails exactly, without trimming whitespace; regression tests cover leading/trailing text and tail spaces. `verify_results.py` asserts the exact allowed result fields/counts and conversion formulas for all eight candidates, and independently regenerates each candidate and its full manifest from the pinned original before reporting source/cache preservation.
- `verified-results.json`, `application-summary.json`, `font-overwrite-evidence.json`, and `source-provenance.json` are the compact evidence index. Full baseline/candidate manifests and raw observations remain in the research directory.

The existing verified official LabPlot AppImage and source archive were reused. The inspected quantized revision is `431deeb7c8473503970ca56b78cc1678f57d373d`; it was inspected but not executed by this phase. No latest upstream code, user Mac, VM, user PPT, or stable installed skill was used or modified.

## Explicitly not validated

Origin application reopen/update/save/recalculate: **NOT RUN**. Official Origin Viewer execution: **NOT RUN**; a separate attempt encountered Linux/Wine IPC restrictions before opening these candidates. Modern OPJU/OGGU edits, arbitrary projects, hidden algorithms, page/layer font-scaling locks, exact Origin UI physical units, and font-family mappings remain unsupported/unknown.

Raw numerical data is never reconstructed from image pixels, fitted, smoothed, downsampled, or rounded. No native algorithm or opaque parameter was altered or executed.

## Publication boundary

Independent review rebuilt the observers and completed twelve fresh-profile LabPlot runs: two style baselines, eight style edits and two title-font probes. All eight native edits, bit inventories and app-owned saves reproduced. The original and independently rendered Graph1 regions for the five inspected single-axes cases are pixel-identical. Screenshot pixel hashes use tightly packed row-major RGBA bytes, with crop rectangles in Pillow's half-open `(left, top, right, bottom)` convention.

The title-font diagnosis uses a separate third public fixture, `strings_testing.opj`, not either of the two style fixtures. The exact source, one-byte guarded diagnostic operation and invocation are documented in `REPRODUCING.md`; the diagnostic is not promoted into supported title editing.

The screenshots are parameter probes, not polished figure layouts. The larger bottom tick font and smaller layer rectangle visibly cause label overlap. Layout constraints and collision repair remain unimplemented.

`publication/` contains only newly authored research code/tests and compact style/provenance reports. No OPJ, OLE, PPT, screenshots, proprietary Origin binaries, third-party source implementations, or unverified-redistribution fixtures are included. The optional public-fixture tests need the exact separately obtained files. Neither this report nor the public package upgrades the stable skill's native-compatibility claims.
