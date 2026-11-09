# Operation map: from observed defect to a supported edit

Choose the row matching the actual source representation. Inspect identity/old values first; perform only supported operations on a new revision. This map connects existing tools, not a claim that every listed aesthetic operation has a general-purpose writer.

| Object / need | Execute with | Required operation and boundary | Verify |
|---|---|---|---|
| Source inventory and panel ownership | `inspect_pptx.py`; whole-slide/detail render; source-preservation module | Bind complete scientific panels and nested members; inventory alone does not establish membership | IDs, group parents, relationships, original hashes, connector owners |
| Rough composition | `layout_boxes.py create` for binding; `prepare_local_handoff.py`; `assistant_layout.py` | Read/confirm current intent; write layout/previews under a revision lock. This does not edit the source | Project/map, exact current snapshot, selection/staging, recovery |
| Root-level native PPT text | `scripts/native_ppt/safe_edit.py`; [native text schema](native-ppt-text.md) | `font`: family, size, tracking/kerning with old-value guards; `paragraph_spacing`: fixed-point line/before/after; `translate`: text-only placement. Combine run changes in one operation | Exact scientific text, italic/sub/superscript attributes, unrelated XML/media/payloads; render glyphs/wrapping |
| Nested native text, shapes, arrows and whole-panel transforms | Tested task-specific OOXML operation following [code-editing.md](code-editing.md) | Preserve types and group ancestry; compose transforms and connector endpoints. No generic whole-slide writer is bundled | Old transforms, allowed differences, text/glyph proportions, endpoint ownership and complete render |
| Faithful SVG plot cache | `svg_edit.py` for supported appearance; `pptx_origin.py` for supported external preview replacement | Style operations do not resize plot internals. Geometry/text/marker separation needs a verified semantic transform for this actual representation | Paths/data mapping, text, clips, glyph shape, active/fallback previews and unchanged OLE |
| EMF/WMF or PDF-derived representation | Supported extraction/conversion, faithful unedited baseline, separately verified semantic operation | Diagnose glyph/clip/marker conversion errors. A different faithful converter in the selected cache route is allowed; source reconstruction must remain bounded and checked | Compare conversion baseline before styling; preserve scientific paths, symbols, clips and associations |
| PNG-only measured graph or micrograph | Faithful placement/crop within authorized scope | Raster bytes do not provide editable labels/data. Preserve physical aspect and scale bars; do not inpaint evidence or invent points | Original bytes/crop, physical geometry, readable unchanged content; report unsupported inner edits |
| Square/triangle/circle/composite symbols | Supported native/vector/cache glyph operation | Correct individual glyph deformation around its data center; preserve meaningful size/orientation encodings and matching legend | Source shape/angles, complete transform, centers, color/fill/strokes and legend identity |
| Existing Origin OLE display structure | `normalize_ole_display.py` for its tested equivalent branches | Only after coherent host/preview geometry. Keep actual independent OLE objects and original payloads | Branch equivalence, media/relationships, source hashes; actual target PowerPoint display |
| Actual native Origin styling | Connected Windows Origin tools, authorized existing VM bridge, or reviewed exact native plan | Verify tool/session and supported properties. No arbitrary native format writer or new bridge access | Data/axis/binding invariants, cold reopen, reinsertion and refresh separately |
| Final guide artwork | `alignment_guides.py` for supported simple slides; tested narrow writer otherwise | Derive positions from final anchors; one native guide-only group behind science. Do not ungroup source objects to fit helper limits | Exact guide removal/restoration and unchanged scientific content |
| Coverage and final QA | `python_display_coverage.py`, optional supplied-observation checker, actual renders | Record every selected member/facet; apply fixes and examine the result. Checkers do not identify sources or certify aesthetics automatically | [Quality review matrix](quality-specification.md#review-matrix-and-correction-order) and final application evidence |

## Efficient execution sequence

1. Freeze source/identity, inspect one baseline, map roles and requested relationships.
2. Select output scale/reference targets and identify which rows above are needed. Check real capability before promising a layer change.
3. Prepare one guarded operation plan for compatible edits. Preserve source data, groups, routes and user scope; avoid a new wrapper group or full-slide raster shortcut.
4. Generate a candidate and verify independent allowed differences; inspect changed details and the full figure.
5. Fix the actual remaining defect, then publish the verified result and current preview through the guarded handoff. Preserve newer user work.

A failed operation blocks that facet, not every independent task. State whether the missing part is identity, conversion fidelity, an editor property or application verification; use a supported alternative already within scope before asking to change route or deliverable.
