# Preview helpers

A PPTX may contain an embedded Origin OLE object and a separate visible preview. These are distinct. The preview workflow changes the visible picture while preserving the original embedded bytes. Activating or refreshing Origin can restore the old appearance. Do not use this path to claim a native data or graph-object edit.

Inspect first, and use the exact slide/object/part reported:

```sh
python preview/pptx_origin.py inspect source.pptx > inventory.json
python preview/pptx_origin.py extract source.pptx --part ppt/media/selected.wmf --output original.wmf
python preview/wmf_emf_extract.py original.wmf original.emf --report emf.json
python preview/cfb_extract.py original.bin --stream Contents --output Contents.payload --report streams.json
```

The EMF extractor validates a complete EMF embedded in WMF rather than redrawing it. Optional installed Inkscape can convert EMF to SVG, but conversion is not presumed lossless. Inspect fonts, scientific symbols and curve geometry.

For an SVG, `svg_edit.py inspect` reports exact element IDs/paths and a source hash. Supply a JSON plan with `source_sha256` and an explicit `edits` list. Each edit selects an element by unique `id` or inspected `path`, and sets permitted appearance properties or guarded text. It refuses external/active content and cannot recover text already converted to outlines.

```sh
python preview/svg_edit.py inspect original.svg
python preview/svg_edit.py edit original.svg changed.svg --plan plan.json
python preview/pptx_origin.py replace source.pptx changed.pptx --slide 1 --object ole:0 --png changed.png --svg changed.svg --acknowledge-stale-ole
python preview/pptx_origin.py verify source.pptx changed.pptx
```

The editor supports only the inspected layouts, including the tested paired VML Choice/DrawingML Fallback. Shared media is cloned for the selected object. SVG and PNG fallback must match in aspect ratio. Strict/unknown OOXML layouts, signed files, external image targets and unsupported AlternateContent are refused. `.ppt`, `.pptm` and encrypted files are not converted.

Verification compares package members and embedded payload hashes. Unchanged package members preserve uncompressed content; this preview path does not promise byte-identical ZIP encoding. Always keep the source, examine the changed slide and independently test your target Office version. No universal file-safety or Office compatibility claim is made.

## Layout proposals and comparison overlays

For multi-panel alignment, typography and spacing, follow the [visual-layout workflow](visual-layout.md). Draw and show a guide proposal first, resolve uncertain panel/object/role/edge choices, and obtain explicit confirmation of that exact proposal before applying alignment. The [approval gate](alignment-plan.md) checks the complete plan, version, source and guide hashes plus exact anchor bindings. It is read-only: it neither draws guides nor moves objects, and it cannot authenticate user approval. A task-specific editor still needs guarded geometry edits and independent preservation checks.

[Typography and palette choices](style-options.md) describe reference-panel or project-scaled fonts and six starting palettes. Style choices need their own authorization, preserve scientific series meaning, and require actual contrast checks. No palette is guaranteed universally accessible.

The PNG overlay helper uses identical canvas coordinates, without registration or resizing. Old content is grayscale on white at 35% opacity by default; each nonwhite new RGB pixel stays fully opaque and unchanged. Inputs must be opaque single-frame PNGs with inspected SHA-256 hashes, and the output must be new. See [overlay usage and verification](visual-layout.md#independent-verification-and-overlays).

```sh
python preview/layout_plan.py inspect plan.json > review-summary.json
python preview/pixel_overlay.py old.png new.png overlay.png \
  --old-sha256 VERIFIED_OLD_HASH --new-sha256 VERIFIED_NEW_HASH
```

These helpers do not modify PPTX/OLE source objects. Alignment application, guide generation/removal, palette application, and client rendering are workflow requirements, not newly implemented editing APIs. Existing preview APIs and the native experiment are unchanged.
