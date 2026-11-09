# Preserve live Origin objects when changing Python display caches

Read after the Python editing route is selected, before writing or delivering a PPTX containing Origin OLE. This is an external display/cache path, not a native Origin file writer.

## Delivery invariants

- The actual refined working slide must retain each selected graph's real `p:graphicFrame` / `p:oleObj`, its ProgID, original local OLE relationship and embedded binary. Keeping originals only on a backup slide is not an acceptable replacement. Do not flatten the working slide into one PNG or place an opaque page image over real OLE objects.
- Each graph has its own cache image and clickable host rectangle. Preserve original data and curve association. Keep native PPT text, diagrams and ordinary pictures native where feasible. Preserve scientific-image aspect ratios and source order. A graph cache may include faithful labels, but must not accidentally crop them or cover a neighboring graph.
- Keep the host `p:xfrm` and fallback picture `a:xfrm` synchronized within the same parent coordinate system. Preserve existing `imgW`/`imgH` and other activation metadata unless a separately verified update requires changing them. Display bounds and Origin-internal sizes are different. Do not guess DPI/PPI or claim an update-stable size from static checks.
- Reuse source relationship targets for OLE. Add new image parts with correct content types and image relationships for new caches. Do not replace an EMF part with PNG bytes while leaving its extension/content type unchanged. Verify every embedded payload and protected relationship by hash.
- Group removable reference lines as one native PPT group. Avoid filled overlays above graphs. Resolve selected source membership before hiding an unselected panel; keep its original safely available.

## Mac compatibility normalization

An observed failure had `mc:AlternateContent` branches where a Choice held an Origin `oleObj` without a `p:pic`, while Fallback held the same OLE with an explicit picture. A Linux render succeeded, but Mac PowerPoint displayed blank graph regions. A safe-copy test using the equivalent **direct `p:oleObj` with its explicit individual `p:pic`** displayed correctly in actual Mac PowerPoint. This is a tested repair for that structure, not proof that every blank plot has this cause.

Use the bounded helper only after geometry and cache checks:

```sh
python scripts/normalize_ole_display.py reviewed-candidate.pptx mac-candidate.pptx \
  --expected-sha256 ACTUAL_REVIEWED_INPUT_SHA256 \
  --slide-part ppt/slides/slide2.xml > normalization-report.json
```

Find the working slide through presentation order and its relationship; `slide2.xml` is only an example. Never substitute a new hash when the reviewed input changed. Output must be a new revision. The helper validates matching embedded Origin branch content, exact dual-frame geometry, local existing image/OLE relationships and unchanged other package parts. It rejects divergent branches, linked objects, unsupported containers and missing previews. It does not synthesize cache artwork, change positions, authorize edits, or modify Origin binaries. Never blanket-delete compatibility branches of unrelated content.

## Evidence gates

1. **Structural:** inventory actual first/working-slide OLE objects, target mappings, binary hashes, cache formats, unique shape IDs, matching display rectangles, clip/bounds integrity and z-order. A count of twice the objects may be Choice/Fallback duplication, not twice as many graphs.
2. **Content and aesthetics:** compare faithful original render and every final panel. Verify scientific-image order, labels, data preservation, no distorted characters/markers, readable same-level typography and measured visible gutters. Treat EMF-to-SVG conversion as untrusted until compared; one observed conversion replaced round markers with colored squares and had to be rejected.
3. **Target host display:** open the final candidate in the user's actual Mac or Windows PowerPoint and inspect its real first slide, not only a screenshot generated elsewhere. LibreOffice/PDF success is useful but cannot certify PowerPoint. If unavailable, explicitly label the candidate unverified; do not silently treat that gate as passed.
4. **Origin lifecycle:** independently test double-click activation, edit/update, save/reopen and position/size stability in an authorized environment with Origin. Mac PowerPoint display alone does not validate Windows Origin activation. Do not start a VM or acquire new permissions merely because this reference describes a test.

Report each gate separately. A valid cache-only delivery states: original Origin objects/data retained; display caches and PPT layout changed; Origin may regenerate the old appearance when refreshed; actual activation/update tests passed, failed or were not run. Never call cache work a native Origin style edit.

## Confirmed scope of the motivating case

Actual Mac PowerPoint displayed the repaired page with ten independent selected Origin objects. Original OLE attributes, relationships and all eleven stored payloads were unchanged. The user confirmed appearance. Windows Origin activation and update-size stability were **not tested**. Do not publish the user's scientific deck, screenshots, local paths or data as a regression fixture. The public tests are synthetic.

## Native PPT editability and grouping gate

Preserve original PPT text, arrows, shapes and other native members on the working page, not only in a backup. Panel letters and editable text annotations must be native text shapes, not image crops or text baked into a regenerated cache. When promoting a visible cached panel letter to native PPT text, remove only its verified label region from that individual cache without obscuring scientific content, preserve the OLE payload, and disclose that Origin refresh can restore the old cached letter until native graph content is also changed. Do not claim this moves Origin-internal axis text into editable PPT text automatically.

Do not add a group around previously separate scientific objects. Coordinate them via the private layout map and individual transforms. Preserve original native arrow/shape/text object types and existing group relationships; flattening a newly introduced group must compose its transform accurately, not simply remove the wrapper. The only newly grouped final items allowed by default are alignment references, in their separate removable guide group.

Before acceptance, map source IDs to output IDs and compare native types and group ancestry. Check every new panel label has a text body and an exact value, locate/remediate duplicate cached letters, and visually inspect alignment, text bounds and connector endpoints. Native text extraction, object-type/parent-map checks and actual PowerPoint editing are separate evidence; report untested stages. Existing delivered versions that fail this gate require a new corrective copy, not a silent success claim.
