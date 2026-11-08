# Independent review of the bounded active-prefix experiment

## Outcome

Ready as a source-only research supplement after the verification fixes below. The scientific result did not change: the one pinned public legacy OPJ fixture still allocates 50 cells per X/Y column and has separately observed 7-, 49- and 50-row active prefixes. This is not general variable-length Origin support.

An independent repeat of all four real LabPlot imports (original plus three toy candidates) used official LabPlot 2.12.1 and the identical authored observer binary, SHA-256 `3c4df197b6c6c960a44d31bf3f1a704580d63ba119ea927881c02925f2b7aa2a`. All 14/98/100 active X/Y binary64 values matched raw CSV, including signed zero. The 86/2/0 inactive app cells were missing. Each candidate emitted two passive Qt `pointsUpdated` observations containing exactly 7/49/50 bit-exact logical points and ranges 0–6/0–48/0–49. Saved LML column payloads also matched the actual Column API bit for bit.

The parsed XML comparison preserves exact element attributes, text and tails. Apart from documented generated UUID/creation timestamps and root dock state/modification timestamp/thumbnail, only the two Book1 A/B numeric payloads differ. Graph configuration and explicit A/B bindings match. XML parsing is not a raw-byte comparison of LML serialization.

## Verification defects corrected

1. The initial XML comparator stripped text/tail whitespace. It could miss changes to notes, labels and payload boundaries. It now distinguishes leading/trailing whitespace, indentation, `None` and empty text. The retained real saves still have exactly the same two differences under the corrected comparator.
2. Equal before/after hash-log files alone did not prove which source the application read. The verifier now regenerates each candidate from the exact public source and raw CSV, compares every candidate byte, canonically compares the complete manifest and inspections, verifies exact rollback, and links both application snapshots and hash records to those bytes. False preservation flags, unrelated/opaque-byte changes with rewritten hashes, type substitutions and loss of a signed-zero ledger value are rejected.
3. A permitted changed XML payload path did not by itself prove correct saved numeric content. The verifier now decodes each 50-cell saved binary64 payload and compares it to the actual API readback.
4. The original runner accepted arbitrary path-like case names, followed some symlinks and did not stop on every shell error. It now accepts only the four defined cases and plot mode, refuses reused profiles, result paths and symlink parents, validates the public/toy input, pins the official executable/importer library and imports a private per-run snapshot. Case generation also refuses CSV symlinks, changed preexisting CSV, existing outputs and existing reports.
5. Verification never declares visual inspection automatically. Its result explicitly says visual review is not performed by the code. Separately inspected graph captures are recorded in `visual-inspection.json`; the original rerun's first numbered window was a blank auxiliary dock, so its MainWin capture, window 2, was inspected instead.

## Independent source checks

The official executable, bundled library, AppImage and source archive match the recorded hashes. The inspected OriginAnyParser, OriginProjectParser and XYCurve source files are byte-identical to their members in the pinned official source archive.

The parser reads dataset `numRows`, `beginRow`, `endRow` at header payload offsets 0x19, 0x1d and 0x21. Data vector length comes from data-frame bytes divided by cell width. The importer allocates from vector length but copies active numeric rows only in `[beginRow,endRow)`. XYCurve adds only valid, unmasked source rows to its logical-point vector and emits that vector before mapping it to scene coordinates. AspectTreeModel indexes hold AbstractAspect pointers; AbstractAspect inherits QObject, and the observed signal signature matches the official XYCurve declaration. Graph X/Y dataset IDs are read at curve header offsets 0x23/0x04. The unresolved range-like fields at +7/+11 remain opaque and unchanged.

The original fixture's 100 actual API cells and both 50-point Qt emissions also independently match its exact native cell bits. Original fixture values and source payload fragments are not included in this package.

## Tests and boundaries

- 64 tests pass with the separately supplied public fixture, normally and under `python -O`.
- Without the fixture, 32 tests pass and 32 fixture-dependent tests explicitly skip, normally and under `python -O`.
- The corrected full verifier passes against both the retained initial app evidence and the four independent reruns, normally and under `python -O`.
- The source-only numerical/Qt observation verifier passes normally and under `python -O`.
- The runner's shell syntax checks pass. Real reruns complete Save As and then terminate with the planned timeout status 124.
- 51/257 rows remain refused before output creation. No allocation expansion was attempted.

Active masks permit 120/792/808 bytes for the three cases; 97/675/687 bytes actually change. Everything outside those exact masks, including inactive cells, graph bytes and opaque content, is preserved. Preservation does not establish the semantics of opaque content and does not sanitize a template.

Origin reopen, redraw, update, recalculation, native save and saved-native-file reopen remain NOT RUN. Modern OPJU/OGGU, arbitrary templates/counts, nonzero starts and per-curve subset selection remain unsupported. LabPlot writes LML, not an Origin OPJ save cycle.

## Distribution

Only authored source, reports, test logs, toy CSV and toy app-observation records are packaged. No native fixtures, original fixture payload fragments, screenshots, app saves/binaries, third-party source implementations, user data or private documents are included. External fixtures and dependencies retain their own licenses. The included MIT license is copied unchanged from the project's existing license and applies to the authored material, not those external artifacts.
