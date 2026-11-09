# Reference-led font size, character spacing, line spacing and whitespace

Read before typography refinement, especially when the user supplies an original figure, reports small text, or asks to match font-size proportions, whitespace or line spacing. These requirements apply to native PPT text and every selected per-object display cache in all three execution routes.

## Font policy

Use Calibri for native text and supported plot-cache text, preserving role hierarchy, italics and subordinate runs. Verify the actual face and glyphs after transforms; if unavailable, report the missing dependency rather than silently substituting. Do not install/redistribute proprietary fonts without the appropriate authorization/license. Native text remains native. Cache font changes leave the embedded Origin styling unchanged and may be replaced on refresh.

## Establish the target from the original

Treat the user-designated original/reference as the typography baseline. Preserve its readable role hierarchy and visual balance unless the user requests a departure. Do not replace that baseline with an arbitrary compact preset or shrink everything to fit rough panel boxes. A technically consistent figure can still fail because all its labels are too small.

Bind the current source and reference privately. If the matching editable original exists, inspect its actual type properties, effective transforms and untouched render. Measure panel letters, axis titles with units, ticks, legends, conditions, diagram labels and subordinate runs separately. Compare visible glyph size and whitespace at the same physical figure width or a clearly stated equivalent display scale. A screenshot alone establishes relative visual proportions, not absolute points or print dimensions; do not infer points from pixels/DPI without a physical-size binding.

Keep a small task-local type and spacing record: reference sample/role, current rendered size, target size or ratio, output dimensions, and intentional exceptions. Use a representative repeated glyph/string in the same face and weight for peer comparisons. An inset may need a separate role target, but do not make it miniature merely because it is an inset.

For example, if the actual original at the same output scale establishes approximately 10.5 pt ticks and 11.5–11.6 pt axis titles, retain that scale and derive annotation/panel-letter sizes from its hierarchy. Replacing it with 6.5 pt ticks and 7.2 pt titles without a matching user request is a regression. These values illustrate reference preservation; they are **not universal defaults** for other figures, panel sizes or publication widths. In the absence of a reference, start from the readable original, then choose project-specific targets and inspect them at final size.

## Correct font size and glyph proportions separately from plot geometry

Use Calibri by default; a user's explicit font choice takes precedence. Match the reference's size, weight, italic-variable treatment and subordinate-run hierarchy in the chosen face. Preserve all scientific words, values, signs, units and super/subscripts.

Set effective final size after the complete transform chain, including group scaling, OLE host and preview rectangles, SVG viewBox and cache pixel-to-physical mapping. Equal declared point sizes do not establish equal visible sizes. Changing plot width/height must not stretch letters, turn round markers into ellipses, or scale type incidentally with data geometry. Preserve data-to-axis mappings and scientific marker centers; use only a supported independently verified operation for this separation.

Preserve native PPT letters, labels and annotations as native text. Cache-only text changes do not modify Origin's underlying graph or internal presentation streams; disclose refresh limits. Never claim a generic cache writer or redraw method exists because a task-specific method worked once.

## Character spacing is an independent requirement

Use the intended font's normal advances and kerning as the baseline. Remove unintended tracking, distributed justification and character-by-character stretching when the user requests normal spacing. Do not blindly disable legitimate font kerning, force every character to the same width, or remove scientific word/number–unit spaces.

When a faithful converted cache splits text into separate glyphs/runs, validate ordering, the actual reference font, baselines and complete text before re-spacing it. A replacement font alone does not repair positions inherited from a stretched preview. Recompose only through a supported, guarded semantic text operation; preserve italic runs, signs and super/subscript offsets. An empty extracted text run can encode a visible space, and neighboring runs may each contain boundary whitespace: neither dropping all empty runs nor concatenating all advances blindly is safe. Compare the final visible words, unit gaps and exponent attachment against the untouched source. Extraction or OCR success alone is not this check.

If text became outlines or conversion changes glyphs, use another faithful supported route or mark that operation blocked. Do not guess axis text, erase evidence, or present an unsupported font rewrite as finished.

## Line spacing, paragraph spacing and ink clearance

Measure multiline baseline distances and paragraph before/after gaps separately from font size and character spacing. Follow the reference's density and hierarchy; retain space for ascenders, descenders and super/subscripts. A fixed 100%, 115% or other percentage is not a universal solution. A two-line axis title may consist of separate objects: paragraph settings in one object do not correct the distance between them.

For native PPT, apply supported paragraph-spacing writes or a tested source-bound OOXML operation; preserve rich text and intentional line breaks. Prevent unintended wrapping/autofit and inspect the rendered result. The bounded native adapter accepts fixed-point paragraph spacing and explicit per-run tracking/kerning. It does not write percentage line spacing or perform automatic rich-text reflow; those need a separately supported operation.

For supported per-object cache text, correct real baseline/paragraph positions and advances rather than changing a metadata field or uniformly stretching a bitmap. Record which layer was changed. Maintain reading order and label ownership when repositioning separate text objects.

Increasing type requires rechecking actual glyph-ink gaps: tick-to-frame, tick-to-axis-title, title-to-unit, exponent-to-unit, caption-to-pulse, legend-to-data and label-to-own-panel. Include neighboring curves, markers, arrows and shapes, not only text boxes. Positive gaps at final scale are required; an empty bounding-box test is insufficient. Never fix a collision by hiding data or shrinking the entire figure back below the reference size.

## Whitespace must support the enlarged type

Compare the reference's inner text clearances, frame-to-frame gutters, title spacing and outer margins as distinct relationships. Preserve compactness without forcing all gaps to one value. Redistribute blank space and move an associated annotation into verified empty space before reducing the reference type scale. Keep panel letters close to their own visible upper-left edge and clear of neighboring titles, ticks and panels.

A changed composition can make the reference's exact annotation placement unsuitable. Choose a clear nearby position, keep the complete annotation/legend/pulse association, and explain a material relocation. Do not move curves, alter scientific axis ranges/ticks, hide a required axis, silently omit a label or trim scientific content to imitate the reference. Material changes to confirmed relationships, source membership or style follow the guide-confirmation boundary; routine derived positions/gaps within that intent do not require per-coordinate confirmation; an explicitly requested appearance correction does not require an invented new alignment gate.

While preparing the revision, preserve newer workbench drafts and user guides. Read the current revision before publishing. A new font preview does not authorize overwriting newer user geometry with an older confirmed snapshot. Keep file layout provenance and current-page layout separate, and update through the existing lock/revision interfaces.

## Apply, render and inspect the final result

Apply the chosen type sizes, normal character spacing and measured line/paragraph corrections to every supported affected role; a checklist or a larger CSS thumbnail is not the actual edit. After all layout/cache/native transforms are final:

- Compare reference and result at the same physical width/equivalent scale, including a whole-figure view and dense detail crops. Reject a visibly smaller hierarchy even if all new labels match one another.
- Audit matching rendered glyphs across same-role peers and inspect every intended exception. Check the smallest necessary labels, logarithmic ticks, rotated titles, legends and unit exponents. Nominal points are supporting evidence, not the visual verdict.
- Inspect character advances, number–unit spaces, baseline distance, paragraph gaps, line breaks and positive ink clearance independently. Recheck after every type-size change or geometry update.
- Verify all scientific strings/data, original OLE payloads, native object types/group parents and preview/display rectangles against the authorized change map. Keep the final guide group reversible.
- Distinguish renderer verification, actual target PowerPoint display and Origin activation/refresh. An earlier version's application check does not verify the latest typography revision.

Keep task-specific reference images, private files, paths, source hashes, example measurements and reports out of the reusable skill package. The release carries these reusable requirements, not the user's figure or a fixed source-specific writer.
