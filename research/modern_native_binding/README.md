# Modern CPYUA native reference research

Read-only research prototype for a restricted modern Origin dataset/page grammar. Not a general importer or native editor. No Origin or PowerPoint application validation is claimed.

## What is new

The parser starts at the prolog and requires a complete sequential dataset list before walking pages. Worksheet and graph ownership is established by exact containing record chains, never by scanning, nearest preceding labels, sheet suffixes, successful numerical decode order or preview geometry.

Worksheet column records contain a native dataset selector at decoded +4. Graph records contain native selectors at +35 and +4. A positive selector resolves to the same numbered slot in the complete dataset descriptor list. Zero remains unassigned, out-of-range remains unresolved, and duplicate worksheet memberships remain ambiguous. Zeroextent and special-type descriptor slots are retained. Names are display evidence, never identity authority.

A bounded post-page opaque block leads to the next page or the page-list terminator. `checked_root` requires all recognized dataset and page chains to complete. The remaining project tail is always unvalidated.

## API and tests

- `native_binding.walk(bytes)` returns the accepted prefix, blockers and reference evidence.
- `native_binding.checked_root(bytes)` or `walk(bytes, require_complete_page_list=True)` rejects incomplete dataset/page sections.
- `python native_binding.py INPUT --out NEW_REPORT.json --require-complete-page-list` writes only a new report. Existing outputs, source aliases, output symlinks and symlinked output parents are rejected. Input must be a bounded regular file.
- `python -m unittest -v test_native_binding` and `python -O -m unittest -v test_native_binding` run the 27 synthetic tests.
- `python prove_public.py --inputs SAMPLE_DIRECTORY --corpus original110 --out NEW_REPORT.json` verifies source hashes and reproduces public counts. Use `independent57` for the separate corpus or `all` with both corpora in the same directory. No downloading or sample extraction is performed by this proof utility.

The adjacent frozen dataset-envelope, owner and sparse helpers are explicit dependencies. The new parser does not invoke the owner's root scanner. The strict root gate is a necessary structural prerequisite for other research, not permission to edit, a rewrite certificate or an application acceptance result.

## Public evidence only

Source identities, license information and expected per-file counts are in `public_sources.json`. Aggregate counts are in `expected_public_counts.json`.

Original110: 109 complete dataset lists; 101 complete page lists. The 101 complete-section files contain 106 pages, 30 worksheet layers, 198 columns, 2,671 curves and 5,342 positive references. All 88 zeroextent descriptor slots are preserved. Across accepted prefixes, including incomplete files: 110 pages, 33 worksheet layers, 216 columns, 2,677 curves and 5,354 positive references. These latter counts must not be described as complete-file support.

Independent57: 40 complete dataset lists; 24 complete page lists. The 24 complete-section files contain 78 pages, 39 worksheet layers, 283 columns, 188 curves, 371 positive references and five zero references. Across accepted prefixes: 85 pages, 43 worksheet layers, 298 columns, 210 curves, 415 positive references and five zero references. Unknown forms remain rejected.

Real multi-sheet counterexamples corroborate why selectors matter. Public object51's tenth sheet, `points`, uses selectors 37–42 and 49 for A–G@7; sheet order does not equal the label suffix. Public object105 has extra selectors within sheet column chains, so descriptor slices are not generally contiguous. The independent `Fig._S7,_10.opju` sample has 16 pages, eight workbook/worksheet layers, 56 columns and 27 curves.

An independent cursor implementation rechecked the public page/layer/item boundaries, selector values and literal source maps; all public files were rehashed, including publisher MD5s for the separate corpus. Normal and optimized proof results agreed. Independent tests cover strict gates, truncation, reordered/duplicate memberships, zero/out-of-range references, unknown records, fake pages within opaque blobs and unsafe output paths. The previously reviewed dataset-envelope prerequisite was reused, not independently reimplemented in that check.

## Limits

This tool decodes structure and reference identities, not numeric arrays. Outer extents do not establish UI rows, active ranges, missing values or usable Cartesian series. Special plotting modes such as histograms, functions, matrices and contours can reinterpret selector fields and remain unevaluated. X=0 is never changed to column A.

No ambiguous raw-length/encoded81 case is resolved here. Unknown sparse opcodes, dataset row forms, annotations, nonempty worksheet axes or layer shapes stop parsing. General project-tail/tree/external-link behavior, arbitrary name encodings, cache updates, recalculation, rendering, reopen/save and application lifecycle remain outside scope.

Source files are bounded and read-only. No native samples, project data, compiled runtimes, screenshots or application-derived exports are included in this source-only package. Do not commit locally produced reports without separately checking their contents and rights.

## Sources and licensing

New research code is MIT licensed under the included LICENSE. Public sample bytes are not distributed here. Their source licenses remain CC-BY-4.0 for the listed Zenodo records and Etalab 2.0 for the Dataverse source. See SOURCES.md.
