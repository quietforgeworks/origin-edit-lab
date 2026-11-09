# Python route: whole-figure display refinement

For font size, character spacing, line/paragraph spacing and reference whitespace, follow [reference-led typography](typography-reference.md) before choosing or applying numerical targets.

Selecting Python means review and refine **all displayed objects in the approved figure**, not merely resize outer PPT containers. Rough boxes specify composition intent; restore the internals so text and axes are not stretched. Do not claim the full refinement finished after only moving/resizing hosts.

## Required object-by-object work

For each panel and its independent native PPT members, inspect and record:
1. Outer PPT placement, aspect and both applicable OLE/preview display frames.
2. Inner plotting area size and aspect, axis geometry, clipping and margins. Use the actual visible plotting area, not image-file whitespace.
3. Titles, axes, tick labels, units, legends, panel letters, annotations, superscripts and symbols. Calibri by default, role-based equal final visual size, proper glyph proportions and readability.
4. Axis/frame/curve line widths, markers, dashes, fills and legend samples at final presentation size. Explicitly restore source-established square/triangle and other glyph proportions in both data points and legend swatches, separately from plot geometry; preserve data centers and meaningful shape/size encodings. See [marker-glyph restoration](aesthetic-review.md#restore-plot-and-legend-marker-glyphs).
5. Inter-panel spacing, plot-edge and text-edge alignments, label-to-panel proximity, annotation clearances and non-overlap.
6. Distortion of all the above. Measurement images retain valid physical aspect and scale bars. Scientific coordinates/data must remain unchanged unless separately authorized.
7. Native editability, independent object/group identity, scientific data preservation and updated active/fallback previews.

“Every object” means all selected output content and its independent native components. Intentionally omitted/off-canvas content remains preserved in the original and receives an explicit exclusion rationale. Do not silently drop unsupported objects or their text from the audit.

## Route capability and safe implementation

- Native PPT text/shapes/arrows: use the bounded native-text adapter where supported and a separately tested, source-bound OOXML edit for geometry. Keep them native and independently editable. Never bake them into the panel thumbnail.
- Origin OLE with a faithful editable SVG preview: existing guarded SVG tool handles supported appearance/text style properties; external-preview replacement preserves live OLE. It **does not rewrite path geometry**. Inner plot resizing requires a separately implemented and tested semantic transform that treats plot geometry, axes, clips, labels and constant-size text independently. Until available for the actual object, record `blocked`; uniformly stretching the SVG is not a substitute.
- WMF/EMF: verify an untouched conversion baseline before editing. Reject a converter that damages glyphs, clips or markers; try another supported faithful extraction/rendering intermediate within the selected cache layer before declaring the facet blocked. Inspect the actual text/path semantics of that intermediate. Neither outlines nor a successful export alone prove font/inner-size editing capability; preserve the OLE and state the exact remaining blocker if no safe route succeeds.
- PNG-only scientific plot: existing bytes do not supply original data, text or axis semantics. Safe crop/placement alone cannot fulfill an inner-plot or font rewrite. Use an already authorized source if available; otherwise flag unsupported facets and ask only for a necessary change of source/route/scope. Never inpaint scientific axes/text/data or invent a redraw.
- Non-measurement diagram/model illustration: proportional adaptation follows existing illustration policy; preserve scientific meaning and disclose generated content. This exception does not cover measured graphs/micrographs.
- Native Origin fields: only reviewed supported plans qualify as actual source edits. Retain exact source/data checks and separate native reopen evidence. An external cache change is still a cache change.

The chosen Python route does not silently start Windows Origin, use a VM, expand permissions or flatten a slide. On a blocked object continue independent supported edits in a new candidate, state the incomplete facets, and preserve the last verified source. Do not label the whole figure complete until remaining scope is resolved.

## Executable coverage gate

After `inspect_pptx.py` creates the current inventory, initialize the whole-slide checklist:

```sh
python scripts/python_display_coverage.py init native-inventory.json --slide 1 --output display-coverage.json
```

This creates pending facets for each inventoried object and structural member. Fill statuses `verified-change`, `verified-unchanged`, `not-applicable`, `blocked` or `pending`. Resolved facets need a reason and independently produced evidence file references `{ "path": "audit.json", "sha256": "actual SHA-256" }`; paths resolve relative to the plan. A facet is unchanged only after inspecting it, not because no editing command exists. `not-applicable` needs evidence (e.g. a native arrow has no plotting area). Inventory is candidate-level and cannot replace scientific segmentation or visual inspection.

```sh
python scripts/python_display_coverage.py check native-inventory.json --plan display-coverage.json
```

Exit 2 means blocked/incomplete/invalid; exit 0 means recorded coverage is complete, **not** that visual quality or Origin activation is certified. Missing objects, missing facets, changed source binding or altered evidence fail. The gate is read-only and does not perform an edit.

After actual panel refinement, update its workbench thumbnail from the resulting per-object preview through `update-previews` under a current lock. Update native PPT geometry/text separately, keeping source identity. Refresh the whole-slide review at the final physical size. Check the full display, not only thumbnails; preserve and compare payloads, object types, group parents and both OLE/preview frames. Report PowerPoint rendering and Origin activation/refresh separately.

## Required actual text corrections, not checklist-only approval

For the final candidate, **apply** the selected font sizes, line/paragraph spacing and collision corrections, then re-render. An audit that names defects without correcting them is an incomplete result. Maintain equal rendered visual size for the same role across panels, while preserving the intended hierarchy between panel labels, titles, axis titles, ticks and annotations. Final physical scale and nonuniform host/group transforms matter; identical point sizes alone do not prove consistency.

Treat line spacing separately from font size. Measure multiline text, super/subscripts and glyph ink; adjust baseline distance and paragraph gaps to remove crowding without wasting space. Do not blindly apply a fixed percentage or shrink every label to fit.

Inspect text–text, text–axis/tick/frame, text–curve/marker, text–shape/arrow/legend and cross-panel collisions. Resolve through supported text movement, gap/margin adjustment, paragraph spacing, layout changes or explicitly chosen type-scale correction. Preserve annotation meaning, association, anchor and reading order. Never erase scientific curves, move data points, paint over measurements, clip letters, hide text or flatten native labels to make overlap disappear. Show changed alignment proposals if a correction changes the approved geometry materially.

The executable coverage gate now requires separate `line_paragraph_spacing` and `occlusion_resolution` facets for every inventoried object/member. `verified-unchanged` means actual inspection found no correction necessary. A reported unresolved collision is `blocked`, not a successful final audit. If no supported source operation can safely fix a cache/PNG/Origin text problem, preserve that source, report the exact object and operation, and do not claim the final typography is done.

Native root PPT text has bounded writing for `font` (font/size/tracking/kerning), `paragraph_spacing` (line/before/after points), and `translate` (safe text-shape movement). See [native-ppt-text.md](native-ppt-text.md). These do not automatically solve all collisions, wrap layout, group transforms, or internal Origin labels. Visual re-rendering remains essential.
