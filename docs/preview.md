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
