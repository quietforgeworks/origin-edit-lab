# Synthetic scientific figure validation corpus

This generator produces 12 original deterministic source/candidate pairs. Every figure is visibly marked synthetic. Values, textures, labels and calibration examples are invented mathematical test inputs, not experimental observations or scientific findings. No external assets or private source figures are used.

The new first-party generator, exporter, tests and generated synthetic content use the project's [MIT terms](figure-quality-license.txt). Third-party dependencies retain their own licenses. Fixture dimensions, typefaces, calibration values and tolerances are test inputs, not layout defaults for real figures.

## Run

Use Python 3 with installed NumPy, Pillow, Inkscape and Liberation Sans:

```sh
python scripts/figure_quality/fixtures/generate_cases.py --output "$NEW_CASE_DIR"
FIGURE_CORPUS_DIR="$NEW_CASE_DIR" python scripts/figure_quality/fixtures/test_cases.py -v
FIGURE_CORPUS_DIR="$NEW_CASE_DIR" python -O scripts/figure_quality/fixtures/test_cases.py -v
```

Or generate and test in one command:

```sh
python scripts/figure_quality/fixtures/test_cases.py --generate "$NEW_CASE_DIR" -v
```

Run from the skill root with `NEW_CASE_DIR` set to an unused path outside the skill. The generator refuses any existing destination, including an empty directory, before writing. Verify dependencies are already available; the commands do not install them. No network or source-image download is needed. The deterministic SVG/data content repeats byte-for-byte for the same generator. Raster bytes and glyph measurements are renderer/font/version dependent; record the local tool versions rather than claiming cross-machine raster identity.

## Forward testing

Give an independent evaluator only `OUTPUT/cases`, the skill under test, and the case's request. Do not provide this generator, its tests, or `OUTPUT/private-ground-truth` before the evaluator locks its report. Source and candidate files are intentionally both available: the task tests scientific fidelity, not merely screenshot aesthetics.

Each case contains editable SVG, same-page 1440 × 840 PNG, original source arrays, candidate arrays, MIT synthetic-content provenance, and neutral observations. The intended physical output is explicitly 180 × 105 mm. The microscopy-like image uses a deterministic 330 × 220 Gaussian/noise array and clearly simulated calibration. Its original image bytes remain embedded and unchanged in both variants.

`observations.json` follows the bounded figure-quality checker schema. Its `parent_id` describes semantic panel membership. `scene-observations.json` separately retains actual SVG parents, source matrices, composed matrices, scientific roles and original renderer observations. A scientific panel can therefore include a label outside its native group without falsifying structural provenance.

## Evidence and limitations

- Geometric bounds come from actual Inkscape `--query-all`. They are labeled containers unless actual frame stroke/image edges support a stronger claim. A query box is not raster ink or a true text baseline.
- Glyph heights come from isolated text masks at the final linear transform, fixed 2 px/viewBox-unit scale and a stated threshold. Horizontal peer strings are compared only when exact text, face, weight and role agree. Rotated glyph ink remains unmeasured by the atlas rather than falsely certified.
- Selected collision pairs have independent opaque-mask renders on the same fixed canvas. Non-text map/colorbar occlusion remains in `scene-observations.json`, because the bounded checker currently checks text-involving collisions only.
- Explicit peer left/right frame anchors and panel-letter baseline attachment constraints cover a staircase-width failure that a left-edge-only audit misses.
- Exact source/candidate fingerprints protect text, data, axes, image payloads and associations. The corpus includes a subtle localized data and unit change to show why attractive pixels do not establish fidelity.
- Clean controls can return `review_needed`: incomplete measurements, bounding-box collision candidates, or application lifecycle evidence must not be converted to a false pass. The tests are not an aesthetic score or a claim of complete automated recognition.
- No PPT, Origin, OLE, PowerPoint reopen, Origin refresh, or native application persistence is tested. SVG editability and actual Inkscape rendering are the only application claims.

## Package boundary

Only the reusable generator, observation exporter, tests, narrow painted-occlusion helper and separate inset-control builder under `scripts/figure_quality/fixtures/`, plus their compact usage/license references, are bundled. Exclude generated cases, PNG contact sheets, run reports, caches, and `private-ground-truth` from a reusable skill package. Generate those into an isolated evaluation workspace when needed.

## Fixture 1.1 correction: inherited source occlusion

The original locked 12-case review is retained. Case01 was incorrectly called clean: its opaque inset hides part of the main curve even though source and candidate are identical. Exact preservation is a fidelity result, not a visibility pass. Required inset membership does not freeze its location. Corrected classification gives four clean controls and eight flawed cases in that original set.

Revision 1.1 changes classification, microscopy panel-summary placement metadata (source-local y=70 from the actual SVG), and independent evidence only. The original source/candidate SVG and data content are unchanged. Its narrow painted-occlusion helper compares actual same-canvas renders, a diagnostic copy omitting the named occluder, and the isolated original target; it does not modify the source or claim general image recognition. Case01 still correctly returns review_needed from the bounded text-only checker. The independent non-text occlusion gate fails instead.

The painted-occlusion helper is synthetic-fixture evidence only: it requires known original IDs, a verified foreground/target pair, painter order and suitable target color. It refuses existing evidence directories. It is not a general image parser, occlusion recognizer or replacement for whole-figure viewing.

A separate optional control is generated with `python scripts/figure_quality/fixtures/build_inset_control.py NEW_DIRECTORY`. It moves the complete inset into a free region and verifies all member IDs/text/data, zero main-curve loss, and zero whole-inset-mask intersections with the main curve and frame. This control is not a replacement for, or a selective rerun of, the original evaluation. Inspect its actual full render before claiming visual acceptance.
