# Independent review and reproduction, 2026-11-08

The bounded findings are supported. This review does not establish Origin application acceptance.

## Checks actually performed

- Read every file in the original 17-file proposed publication, its full retained evidence and the relevant official reader source. Verified all 365 retained-evidence hashes and ten external/source provenance hashes against local files; no mismatch was found. The external runtime was the existing verified official LabPlot 2.12.1 release, not newly downloaded code.
- Rebuilt both observer libraries from the proposed source. Executed twelve new isolated-profile GUI runs: two style baselines, eight single-field style variants and two title-font cases. The observer invokes normal application import, coordinate-mode selection and save actions, and reads official Column double accessors. It contains no Origin parser or assignment of target graph font, stroke or geometry properties.
- Re-created all eight candidates and complete manifests from pinned originals. Every byte outside the intended 2-byte field or 8-byte rectangle remained equal; actual changed-byte counts were 1/2/2/7 for each fixture. Full source numerical masks/bits, graph bindings, record framing and opaque tails were unchanged. The known 32,588-byte EMF cache was unchanged across all four single-axes variants.
- Compared original and independently generated app saves with an exact XML comparator. All text and tails were literally equal. Each fixture had exactly 2/4/1/6 expected attribute differences for font/axis stroke/curve stroke/rectangle. All 128 or 64 allocated app-native binary64 cells, including empty allocated cells, were equal between each baseline and candidate.
- Inspected the actual baseline and four single-axes screenshots. Requested size/stroke/rectangle changes are visible. Graph regions are pixel-identical between the original captures and independent reruns. Larger tick labels and smaller rectangles visibly overlap; these are parameter probes, not publishable layouts.
- Reproduced the font boundary: only source byte 147865 changes 22 to 30 in the third fixture; the importer supplies 26pt/36pt, then the actual Qt current-font reset yields 9pt. The stripped-executable call sequence agrees with official source, without claiming a captured TextLabel symbol stack.

## Corrections made in the reviewed source copy

1. Removed `.strip()` from XML text/tail comparison and added leading/trailing whitespace regression tests. The old comparator could miss a whitespace-only edit, but no such difference occurred in either the original evidence or the independent rerun.
2. Made the acceptance verifier regenerate source candidates, full manifests and restoration instead of printing an unverified preservation flag. A regression test mutates the real EMF cache and updates its candidate hash; the reviewed verifier rejects it.
3. Added the third fixture's public provenance and a strict one-case title diagnostic helper. This does not expand supported editing fields.
4. Restricted runner case names, modes and argument counts, rejected existing profiles, and made input/setup failures stop before application launch. Runtime location remains explicit; nothing is automatically downloaded.
5. Documented visual overlap, XML exclusions and RGBA screenshot hashing. The newly authored source follows the repository MIT license; upstream dependencies and fixtures are not included.

The reviewed source passes 47 tests in both normal and optimized Python with all three fixtures. Source-only runs pass 33 and skip 14 optional fixture methods. The strengthened acceptance verifier passes all eight independently reproduced cases in both Python modes. An additional fresh baseline run checks the revised shell runner; this smoke run is separate from the twelve reproduction runs.

## Remaining limits

Native patching is deliberately limited to exact public legacy hashes. Observers depend on a pinned Qt/LabPlot ABI and a timed GUI schedule, not a general supported automation API. Runtime verification and preparation remain explicit prerequisites. No binaries, screenshots, project files or numerical datasets are published. Origin reopen/save/update/recalculation, official Origin Viewer acceptance, modern native formats, other layouts and unknown metadata semantics are not validated.
