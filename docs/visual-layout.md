# Visual consistency and layout

Use this workflow for appearance edits to embedded figures and native PowerPoint annotations. It supplements [Preview helpers](preview.md); it does not implement native Origin graph editing. Preserve the original and use new output files.

## Contents

- Representation and edit plan
- Final visual typography and strokes
- Alignment and plot geometry
- Compact titles and clear annotations
- Removable guides
- Independent verification and overlays

## Representation and edit plan

Use a review-first workflow: inspect and measure → draw the guide proposal without moving source content → resolve uncertain anchor relationships → obtain confirmation of that exact proposal → apply → independently verify. Clear relationships can be identified automatically, but do not bypass the overall guide confirmation. Once confirmed, execute clear approved pairs without repeatedly asking. A guide-only request or approval to install the tools does not authorize changing a user's deck. See [Guide proposal and approval gate](alignment-plan.md) for the gate.

Identify which layer produces every visible element:

1. The embedded Origin source object and its scientific data/graph records.
2. External slide preview parts, potentially with Choice/Fallback, SVG/PNG or WMF/EMF alternatives.
3. Internal OLE presentation caches such as OlePres streams. Replacing an external preview leaves these unchanged.
4. Native PowerPoint text, lines, ellipses and other shapes on top of or beside the preview.

Record part names, relationship targets, shape IDs and hashes in the task's own plan, not in the public repository. Match actual source text and numeric values before editing. Treat a spoken example as a description of a label, not authorization to replace its source value. Keep ambiguous associations as unresolved rather than inventing scientific meaning.

Choose explicit, minimal changes: targets, old values, new values, allowed geometry/aspect changes and protected regions. Validate all targets before writing. Preserve OLE and unknown package parts byte-for-byte unless their modification is explicitly requested and supported. Never describe a preview or PowerPoint annotation edit as an Origin data/graph-object edit; refreshing the OLE may replace it.

Inspect representations before converting. WMF can carry a full EMF; EMF can contain EMF+ and fallback drawing records. EMF+ ARGB alpha and raster-operation (ROP) semantics can make a nominal color transparent or produce different visible output in another representation. A converter may replace transparency with an opaque fill, alter fonts or lose symbols. Extract originals first, establish a trusted baseline render, and compare each conversion's geometry, symbols, fonts, fills and alpha before editing. Do not promote an untested ad hoc converter to a general tool. If the conversion is not faithful, retain the original representation or stop that conversion path.

## Final visual typography and strokes

Ask whether to use a named reference panel or the project-scaled default described in [Typography and palette choices](style-options.md). Record the selection. The reference panel supplies a separate physical target for each role, not one common number for all text.

Classify semantic roles before choosing target styles: panel titles, axis titles, major tick labels, condition labels, legends and references. Unify within a role while retaining deliberate hierarchy, such as axis titles slightly larger than ticks. Choose project-specific sizes and tolerances from the actual rendered figure; do not treat one successful pair of sizes as a universal preset.

A nominal font size is not its size on the slide. Compute the full chain from each local glyph to final slide coordinates: local SVG/text transforms, ancestor transforms, root viewBox and preserveAspectRatio, picture extent/crop, nested PowerPoint group chOff/chExt mappings, rotation and flips. Native PowerPoint run size is in hundredths of a point, but group scaling still matters. Use 12,700 EMU per point and the actual render DPI. Do not substitute a single picture width ratio for this chain.

For a final local-to-slide linear matrix J in points per local unit, a local em height f maps along the glyph's vertical axis to f × ||J(0,1)||. This is a scale diagnostic, not an ink-bounds measurement. Examine both axes or singular values for nonuniform scale/skew. A glyph's outline, font face, weight, ascent and hinting still affect its visual size. Compare the same glyph or string from the same font/weight at final scale, not different letters' bounding heights. Recheck final SVG and final PPT render, including repeated scaling steps.

Stroke width is also transformed. For ordinary geometric strokes, normal thickness under a linear transform is w × |det J| / ||J t|| for unit tangent t; nonuniform scale can therefore make horizontal and vertical frame strokes differ. Treat SVG non-scaling-stroke, rasterization and Office line semantics separately. Compensate the relevant frame strokes and verify in the final render; do not assume one numeric width is sufficient for all directions.

## Alignment and plot geometry

Map outer plot-frame stroke edges and every relevant title's actual ink left/right/top/bottom, centers and true baselines to one final coordinate system. Include panel titles, horizontal and vertical axis titles, legend titles and other titles, not only the surrounding frame. Rotated titles need transformed ink bounds and baseline direction. Inspect horizontal and vertical relationships and both sides/ends of each row or column. Include panel labels, tick labels and nearby condition/reference text as separate roles when relevant. A shared font size or baseline does not prove text edges align. Title centering on its own axis is a separate constraint from alignment to another panel; do not substitute one for the other.

Create a semantic anchor inventory before moving anything: panel, exact object, role, measurement basis (outer frame stroke, glyph ink or true baseline), edge/center, final coordinate axis and current value. Propose matching roles first; do not blindly align different axis-title roles or deliberate insets. Different-length tick strings naturally have different ink extents. Preserve each label's association with its data tick; do not shift numeric centers away from tick marks just to align outer text edges. A text-anchor change or enclosing layout adjustment can be proposed separately. If frame, title and tick-text constraints conflict, ask which takes priority rather than silently breaking one. For uncertain pairs, name the two objects and candidate edges and ask which must align. Draw proposed guides so the user can judge those exact anchors, then wait for the matching plan confirmation.

Align naturally near-matching rows or columns rather than forcing every panel into one grid. Preserve deliberate insets, scientific aspect ratios and meaningful panel-size differences. Pixel hints from one renderer are not enough to override correct OOXML coordinates: do not damage a valid layout to compensate for a single LibreOffice subpixel offset.

If a small plot-height adjustment is permitted, record the original and new bounds and aspect ratio. Apply the same coordinate mapping to curves, markers, ticks, gridlines and clip paths. Preserve scientific values, tick strings and curve geometry in data coordinates. Keep glyphs independent: transform their anchor positions while keeping their final size/shape unchanged. Compensate frame stroke widths. Verify both top and bottom alignment afterward; changing only the outer picture box can distort text and hide clipping. Do not force this into `svg_edit.py`, whose stable interface does not support geometry edits.

## Compact titles and clear annotations

Move axis titles closer when appropriate, but measure the gap between actual glyph ink and nearby tick labels/axes. Text boxes include padding and ascenders/descenders; a text bbox is not a glyph-ink bbox, and a baseline is not the bottom of the letters. Measure final rendered glyph masks or actual font outlines, including rotations, then verify full-slide readability. Keep a small positive gap rather than allowing apparent touching.

For frequency, condition, reference and similar labels:

- Preserve exact source text, units, case and scientific symbols unless the user requests a content edit.
- Prefer a minimal translation. Check the complete text run and adjacent characters, plot frame, nearby markers and all relevant region boundaries, not just the nearest edge.
- For a rotated ellipse or other slanted region, measure against its transformed boundary rather than the axis-aligned bbox alone. Multiple close boundaries must all retain clearance.
- Keep a modest project-specific gap. A readable full-page result and a native-resolution crop should both pass; an enlarged crop alone can conceal crowding at actual viewing scale.
- Preserve existing visual associations. If movement makes them unclear, a thin unobtrusive leader may help. Avoid covering data points or adding opaque white blocks. Color alone is not proof of label-to-series association, and a visual leader is not verified machine-readable binding.

## Removable guides

For the final guide deliverable, build from the clean final deck. Use one clearly named independent native PowerPoint shape group for alignment references, with a tested identity group transform. Place it behind existing content in stacking order: in OOXML, this means before content siblings after the mandatory shape-tree properties, not appended in the foreground. Consider both horizontal and vertical guides for outer frame edges, title ink left/right/top/bottom edges, centers and true baselines, selected by semantic role. Do not omit title-edge guides simply because baseline guides already exist. Differentiate and label frame-stroke, title/text-ink and baseline guide types. Record which comparisons each guide represents; guides must not mask content or imply intentional insets are errors.

Covering all semantic anchors is an inspection requirement, not a requirement to draw every guide on one slide. By default, show only relevant comparison groups and proposed anchors; avoid unrelated global title lines that overwhelm content. Use separate groups or focused local views when needed.

These are removable drawing objects, not PowerPoint's View Guides. Keep them separate from data/annotation groups and use unique shape IDs. Deliver a clean version and a guide version. Removing only that group must recover the clean content and coordinates exactly. Prove this with XML/shape invariants and a render comparison; for a code-based removal, preserve or restore the exact clean slide bytes. Do not rewrite the clean deck merely to add guides.

Native annotation or guide helpers, if added for a task, must use explicit targets and source-hash/old-value guards, refuse duplicate IDs and existing outputs, preserve unknown parts, and verify clean restoration. No universal autolayout claim is needed.

## Independent verification and overlays

Have a separate read-only pass inspect the final files, not just the editing script's report. Render in isolation with macro/external-link updates disabled; do not save the deck through the renderer. Check both a full-page render and original-resolution crops of titles, frame edges, condition labels, symbols and region boundaries. Inspect the actual pixels.

Audit at least:

- Source unchanged; exact hashes for every unknown/unmodified package part and every protected OLE payload.
- Expected changed parts only, valid relationships and synchronized supported preview alternatives. Validate each referenced active/fallback media part for nonempty bytes, matching signature/content type and successful decoding; one SVG rendering successfully does not validate its PNG fallback.
- SVG path d values, scientific strings, tick values and font roles preserved, except for explicit authorized changes. When geometry is intentionally mapped, verify the declared mapping and all related clips/ticks instead of incorrectly demanding equal path bytes.
- Final font/line metrics after all transforms; title-ink gaps; frame top/bottom and corresponding baselines; label clearance against every close boundary.
- Pixel differences outside the authorized edit regions and all untouched slides. Separate conversion drift from intentional edits and disclose any unaccepted drift.
- Guide removal restores the clean version. A non-Choice layout with no VML may be tested for Linux fallback visibility, but that alone does not establish all-client support.

For a comparison overlay, render old and new at the identical slide dimensions, DPI, canvas, crop and origin. Do not auto-register, translate, rotate, rescale or crop-to-content: those operations can conceal the layout changes the comparison is meant to reveal. Reject mismatched canvases instead of silently fitting them.

`pixel_overlay.py` accepts two opaque PNGs and their inspected hashes. It converts only the old image to grayscale on white at configurable opacity (default 0.35). Every nonwhite pixel of the new render replaces the background with its original RGB value at full opacity, including colored lines and antialias pixels. Pure-white new pixels leave the gray old layer visible. This is an image comparison, not a recovered vector layer or scientific edit. Render transparency onto white explicitly before using this helper.

```sh
python preview/pixel_overlay.py old.png new.png overlay.png \
  --old-sha256 VERIFIED_OLD_HASH --new-sha256 VERIFIED_NEW_HASH \
  --old-opacity 0.35 > overlay-report.json
```

The helper uses exact white (255,255,255), performs no registration and reports hashes, dimensions and a pixel-difference bbox. It does not decide whether a difference is allowed or validate the renderer. Keep original and final renders alongside the overlay for unambiguous review.

Report the actual checks separately: package/geometry assertions, render/visual review, client applications and native Origin reopen. Linux rendering is not macOS or PowerPoint validation. If native Origin was not reopened, say **not run**. Do not claim source editability from a successful appearance comparison.
