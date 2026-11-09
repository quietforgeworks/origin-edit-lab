# Python direct editing of scientific figures

Read this for the code route after source inventory and route selection. The bundled helpers are self-contained; installing another skill is not required to run them. They are bounded tools from `edit-origin-in-ppt`, not a whole-slide editor or general Origin writer. The bounded native text adapter and reviewed Origin plan executor are separate supported paths, described below. Use the **same** [aesthetic review](aesthetic-review.md) and [source preservation](source-preservation.md) criteria as both native-Origin routes. An execution choice never changes the target look or approves unrelated scientific/style changes.

## Contents

- [Python direct-edit workflow](#python-direct-edit-workflow)
- [Choose the exact layer](#choose-the-exact-layer)
- [Setup and source binding](#setup-and-source-binding)
- [1. Extract the current visible representation](#1-extract-the-current-visible-representation)
- [2. Establish the conversion baseline before editing](#2-establish-the-conversion-baseline-before-editing)
- [3. Apply a guarded SVG appearance plan](#3-apply-a-guarded-svg-appearance-plan)
- [4. Replace the selected external PPT preview](#4-replace-the-selected-external-ppt-preview)
- [5. Direct native PPT OOXML edits: narrow recipe, not bundled automation](#5-direct-native-ppt-ooxml-edits-narrow-recipe-not-bundled-automation)
- [6. Verify and report the actual evidence](#6-verify-and-report-the-actual-evidence)
- [Revisions and rollback](#revisions-and-rollback)
- [Portable tests and provenance](#portable-tests-and-provenance)

## Python direct-edit workflow

This is the executable workflow for **用 Python 直接修改（这种修改可能会导致 Origin 重新打开时格式改变）**. Use it after the current route choice, whether the figure came from interactive layout or an already arranged figure. The CLI chain below is for **PPTX inputs only**. For a standalone image, inspect/preserve its actual bytes and format; use only an authorized supported image operation or resolve an existing editable source when the requested change needs one. Do not run a PPT parser on a PNG or turn raster scientific data into invented editable axes/text.

The shipped PPT write path is **extract → guarded SVG appearance edit → render → replace the selected external PPT preview → verify**. Native PPT objects/host geometry use the narrow Python/OOXML recipe below, not the preview-replacement command. Internal OLE caches have no bundled writer. A separately reviewed same-length native plan can run through [native-origin-plans.md](native-origin-plans.md); this does not discover fields or provide general graph editing.

1. **Freeze and identify the input.** From the skill directory, resolve the current source and a new private revision directory. The following Bash examples use assistant-filled values; obtain actual paths, part names, hashes and selectors from this task, not these illustrative names. Check dependencies under [setup](#setup-and-source-binding).

   ```sh
   set -e
   set -C  # Refuse shell report overwrites too.
   CODE="$PWD/scripts/source_edit"
   SRC=/absolute/private/task/source.pptx
   RUN=/absolute/private/task/revision-001
   mkdir "$RUN"
   python scripts/inspect_pptx.py "$SRC" --output "$RUN/native-inventory.json" > "$RUN/native-inspection.json"
   python "$CODE/pptx_origin.py" inspect "$SRC" > "$RUN/preview-inventory.json"
   ```

   Use `native-inventory.json`'s `assets[].source.kind`, structural members, host IDs, XML paths and transforms to recognize native shapes/text, pictures, groups, charts and OLE hosts. Use `preview-inventory.json` for the current one-based slide, `ole:N`/`picture:N` key and exact media/payload parts. Inspect actual renders and signatures as well: these inventories do not certify scientific grouping, active compatibility branches or native Origin validity.
2. **Choose the actual edited layer.** For a PPT host move/resize or native text/shape/connector edit, go to [the task-specific OOXML recipe](#5-direct-native-ppt-ooxml-edits-narrow-recipe-not-bundled-automation). A picture/OLE external-preview appearance edit follows steps 3–7. For PNG-only scientific content, do not invent an SVG/text/curve representation; retain it or obtain a supported source. For a reviewed native plan use [the bounded executor](native-origin-plans.md). For unsupported native fields or internal OlePres changes, stop and report the missing operation; never invent offsets. Do not substitute external-preview changes for requested native changes.
3. **Extract and establish an unchanged baseline.** Set `SVG_PART` to the selected object's actual current SVG part, then run:

   ```sh
   python "$CODE/pptx_origin.py" extract "$SRC" --part "$SVG_PART" --output "$RUN/original.svg" > "$RUN/extraction.json"
   python "$CODE/svg_edit.py" inspect "$RUN/original.svg" > "$RUN/svg-inventory.json"
   inkscape "$RUN/original.svg" --export-type=png --export-background=white --export-background-opacity=1 --export-filename="$RUN/baseline.png"
   ```

   Retain and separately validate the current PNG/other fallback and embedded source using [extraction](#1-extract-the-current-visible-representation). If there is no SVG, use the inspected original WMF/EMF and the supported extraction/conversion branch below; compare its **unedited** rendering to the trusted original before proceeding. Inkscape commands require a verified installed converter. Neither a successful conversion nor an extracted cache proves native Origin editability.
4. **Bind the plan and approval before applying it.** Prepare the exact targets, inspected old/new values, protected content and changed-part allowlist. For alignment/geometry, show clean/guide proposals, resolve questions, then enforce [the guide approval gate](#guide-approval-gate-and-its-precise-limits) in the actual writer. A narrowly approved appearance-only edit needs its source/style binding, not a fabricated alignment plan. Build `style-plan.json` with only the real `source_sha256`/`edits` schema below; its SVG hash guards old appearance and `expected_text` guards any separately authorized leaf-text correction. No `expected_style` field exists. Retain trusted confirmation separately; JSON approval strings cannot create permission.
5. **Apply only the supported appearance change.** Once that gate is satisfied, run:

   ```sh
   python "$CODE/svg_edit.py" edit "$RUN/original.svg" "$RUN/changed.svg" --plan "$RUN/style-plan.json" > "$RUN/svg-edit-report.json"
   inkscape "$RUN/changed.svg" --export-type=png --export-background=white --export-background-opacity=1 --export-filename="$RUN/changed.png"
   ```

   Verify approved style changes, unchanged scientific paths/text/transforms/clips and both rendered representations at identical scale. This editor does not transform path geometry. An explicitly requested first-effect proposal may stop at this separately named SVG/PNG, with originals untouched; it does not authorize reinsertion or final-source application.
6. **Guard the deck and publish a new candidate.** For an approved external-preview result, set `SLIDE`, `OBJECT_KEY` and `EXPECTED_SOURCE_SHA256` from the approved current task binding. Immediately before replacement, compare against that trusted deck hash, not a newly calculated hash substituted into the plan:

   ```sh
   python - "$SRC" "$EXPECTED_SOURCE_SHA256" <<'PY'
   import hashlib, pathlib, sys
   if hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest() != sys.argv[2]:
       raise SystemExit("Source changed; stop and rebind the plan")
   PY
   python "$CODE/pptx_origin.py" replace "$SRC" "$RUN/candidate.pptx" --slide "$SLIDE" --object "$OBJECT_KEY" --png "$RUN/changed.png" --svg "$RUN/changed.svg" --acknowledge-stale-ole > "$RUN/replacement.json"
   python "$CODE/pptx_origin.py" verify "$SRC" "$RUN/candidate.pptx" > "$RUN/preservation.json"
   python "$CODE/pptx_origin.py" inspect "$RUN/candidate.pptx" > "$RUN/candidate-inventory.json"
   ```

   This invocation is for an OLE preview. For an ordinary picture, use its `picture:N` key and omit `--acknowledge-stale-ole`. Recheck the bound target and source reported by the writer as well as the hash. The CLI has no expected-deck-hash flag and does not authenticate consent; the caller owns those checks. It synchronizes the supported external PNG/SVG and paired VML references, **not** internal OlePres or Origin content. OLE refresh can restore the old appearance.
7. **Verify, deliver or stop.** Apply [verification](#6-verify-and-report-the-actual-evidence): exact approved package/XML/style differences, original/payload preservation, independent fallback validation, full-slide/detail rendering and the same final-size aesthetics as the MCP/bridge routes. Read the comparison report; `verify` returning zero is not an acceptance decision. Before final delivery, add and validate the required visible reference lines, grouped natively in editable PPT, through [the guide-only workflow](guide-tool.md); this is separate from the preview replacer and never moves scientific objects. Deliver only the requested format and state its edited layer. Mark actual PowerPoint reopening, Origin reopening and OLE refresh **not run** unless performed. A failed check leaves a rejected candidate, not a finished result.
8. **Revise without overwriting.** Keep the original and prior revisions. Use [revisions and rollback](#revisions-and-rollback) to select a verified base, rebind any changed source/plan and write the next fresh output. Never "undo" by overwriting the original or reverse-patching an uncertain result.

## Choose the exact layer

- **PPT host placement/size:** the picture or OLE `graphicFrame`'s slide geometry and its group transforms. Moving/scaling this host changes where/how large it appears in PPT, not Origin graph-page/layer geometry or nominal native font/line properties. Unequal x/y scaling can distort scientific marks and glyphs. Host and cached-picture transforms are distinct; inspect both, including compatibility branches, and change only a verified coherent set through the task-specific OOXML recipe.
- **Native PowerPoint objects:** native text/runs, pictures, shapes and connectors in slide XML. A narrow, task-specific OOXML patch is possible after its selectors, old values and transform handling are tested. No universal native-slide patcher is included. Native Office charts require their own chart/workbook model, not an Origin operation. A preview replacement does not modify native-object geometry or text.
- **Independent derived preview:** an extracted/converted SVG or rendered PNG edited outside the deck. This is an effect proposal only until explicitly reinserted. It neither changes a PPT cache nor becomes editable Origin data.
- **External visible preview:** media referenced by DrawingML and sometimes paired VML. `pptx_origin.py replace` changes exactly the selected object's visible media references, cloning assets to protect shared uses. This is the implemented source-file appearance route.
- **Internal OLE presentation cache:** streams such as `\x02OlePres000` inside a Compound File. `cfb_extract.py` can inventory/extract exact streams, but no internal OlePres editor or universal decoder is included. An external preview change leaves these streams unchanged.
- **Actual Origin payload:** project/graph data inside an OLE `Contents` stream or an independent OPJ/OPJU. It may not be a complete standalone project. The bounded executor can apply only an independently reviewed exact same-length plan; see [native-origin-plans.md](native-origin-plans.md). It does not discover or infer valid graph fields. `compat.py` reports metadata and offers snapshot comparisons, not a parser, serializer or compatibility certification.

PNG/JPEG scientific text and curves cannot become native editable objects by relabeling the file. Do not use a generative redraw, broad white masking, guessed values or new curves to imitate a source edit. Use authorized source data or obtain agreement for an explicitly limited preview result. Do not apply blanket direct EMF, internal OlePres or OPJU style changes: offsets, duplicated representations, length/checksum dependencies and object semantics require a separately implemented and tested operation. This route does not activate Origin, a Windows bridge or a VM.

## Setup and source binding

Python 3.10+ with `lxml` and Pillow is required for PPTX/SVG operations. CFB/WMF extraction, `layout_plan.py` and `compat.py` use the standard library. Inkscape is optional for conversion/rasterization; use only a verified available installation. No Office, Origin or `python-pptx` dependency is required by the bundled source-edit helpers. Check installed dependencies on the selected computer; obtain applicable authorization before new installation. Never package a machine-local interpreter note.

Commands below run from the skill directory or use an absolute `CODE` path resolved from that directory. Keep actual inputs, plans, reports and outputs in a separate private task workspace. Use fresh output names; do not overwrite the source or a previous candidate. Shell `>` redirects can overwrite reports even when the Python writer refuses source/output overwrites, so use new report names too.

```sh
CODE="$PWD/scripts/source_edit"
python -c "import sys,lxml,PIL; print(sys.version); print(lxml.__version__,PIL.__version__)"
python "$CODE/pptx_origin.py" inspect source.pptx > inventory.json
```

Record source SHA-256, original file identity, slide/order, shape/group ancestry, semantic panel membership, exact object key, every active/fallback media part, relationship and embedded payload hash. Keep screenshot evidence or the returned-layout/project binding separate from thumbnail identity; never fabricate an exported record from a screenshot. `scripts/inspect_pptx.py` provides broader native-shape candidates; `pptx_origin.py inspect` supplies replacement keys and media/OLE relationships. Render and inspect real slide content before selecting a target.

Slide numbers are **one-based** in presentation order, not inferred from `slideN.xml`. Logical keys such as `ole:0` and `picture:0` are **zero-based within their kind** and come from the current inventory. The supported VML Choice/DrawingML Fallback pair is one logical OLE object. Object indexes can change after structural edits: re-inspect rather than carrying an index blindly into a new version. `progId`/Origin hints do not prove Origin payload validity.

`safe_replace_supported` is structural eligibility, not decoded-media or render validation. Independently check every referenced active/fallback asset for nonempty bytes, correct signature/content type and successful decoding with the suitable reader. A good SVG does not validate its PNG fallback. Resolve missing, corrupt or mismatched alternatives before declaring a working result. Linked/external content is not silently fetched or replaced. The writer refuses unsupported branches, signed files, unsafe ZIPs, broken internal relationships, strict/unknown OOXML and non-`.pptx` input. Legacy `.ppt`, encrypted packages and `.pptm` need a separately supported route.

Before any actual edit, bind the inspected source and target to an explicit task plan: exact old values, proposed values, protected content, applicable style/guide approval and expected changed parts. The stable replacement CLI does **not** accept an expected-source-hash argument or authenticate consent. The caller must compare the current deck hash to the trusted task manifest immediately before invoking it and verify the result's source hash. The helper additionally checks that the source did not change during its own operation. Do not treat a report or a file's embedded approval string as permission.

## 1. Extract the current visible representation

These part names are illustrative. Substitute exact parts from the current inventory; never choose them by a filename pattern alone.

```sh
python "$CODE/pptx_origin.py" extract source.pptx --part ppt/media/image14.wmf --output original.wmf
python "$CODE/pptx_origin.py" extract source.pptx --part ppt/embeddings/oleObject3.bin --output original.bin
python "$CODE/cfb_extract.py" original.bin --report streams.json
python "$CODE/cfb_extract.py" original.bin --stream Contents --output contents.payload --report contents-report.json
python "$CODE/compat.py" contents.payload > payload-metadata.json
```

Extraction writes exact package/stream bytes and does not activate them. CFB's CLI `--stream` names an exact **root-level** stream. For nested streams, use its read-only `CompoundFile.read_stream(tuple_of_inventory_path_components)` API after checking the inventory. Do not rename `.bin` or `Contents` to `.opju` and call it compatible. `compat.py` accepts a file for metadata inspection regardless of suffix and explicitly reports `parsed: false` and `compatibility_complete: false`.

If the object already has an active SVG extension, extract and edit **that current SVG**, plus retain its PNG fallback. Do not revert to an older preserved WMF or the unchanged OLE payload. If the source is WMF and contains a supported embedded EMF, extract the stored original rather than redraw it:

```sh
python "$CODE/wmf_emf_extract.py" original.wmf original.emf --report extraction.json
```

Both extractor CLIs optionally accept `--expected-sha256` from the inventory. EMF record-envelope checks and pen color metadata are read-only evidence, not permission to patch those offsets or proof of rendered style. Multiple/unsupported WMFC sequences, malformed records, CFB ambiguity or unsupported content must remain reported blockers.

## 2. Establish the conversion baseline before editing

For a genuine safe SVG, no conversion is needed. Otherwise only use a converter verified for this input/operation. A typical **already installed Inkscape** invocation is:

```sh
inkscape original.emf --export-type=svg --export-plain-svg --export-filename=original.svg
inkscape original.svg --export-type=png --export-background=white --export-background-opacity=1 --export-filename=baseline.png
```

Preserve the original extracted bytes. Compare the converted baseline against the original rendered panel at identical crop, canvas and physical scale **before** making changes. Check all scientific symbols, Chinese/Greek text, superscripts/subscripts, fonts, curves, axes/ticks, clipping, dashed lines, gradients, transparency and marker positions. WMF conversion can lose glyphs; EMF can also contain multiple/EMF+ representations. A successful export is not proof of a faithful conversion. If conversion changes protected content, stop that branch or agree on a narrower result; do not quietly accept a replacement image as equivalent.

Record which application produced the original view, the converter/version and the actual baseline checks. If no trusted original rendering is available, mark conversion fidelity unverified and do not claim a faithful final source edit. Rendering alone cannot restore outlined text to text runs.

## 3. Apply a guarded SVG appearance plan

```sh
python "$CODE/svg_edit.py" inspect original.svg > svg-inventory.json
python "$CODE/svg_edit.py" edit original.svg changed.svg --plan style-plan.json > svg-edit-report.json
```

The assistant prepares `style-plan.json` from inspection and the approved intent. Do not ask the user to edit JSON. Its exact top-level keys are `source_sha256` and a nonempty `edits` list. Example schema (replace the hash/selector/values with inspected, authorized values):

```json
{
  "source_sha256": "VERIFIED_SHA256_FROM_SVG_INSPECTION",
  "edits": [
    {"selector": {"id": "curve1"}, "set": {"stroke": "#d62728", "stroke-width": "2.5"}}
  ]
}
```

Select exactly one unique ID or an exact child-index `path` returned by inspection, for example `{"path":[0,2,1]}`. Merge multiple properties for the same element; duplicate target edits are rejected. Allowed properties are `fill`, `stroke`, `stroke-width`, `stroke-dasharray`, `opacity`, `fill-opacity`, `stroke-opacity`, `font-size`, `font-family`, `font-weight`, `font-style` and `text-anchor`. Geometry attributes, path data and transforms are not supported edit properties. The complete SVG SHA-256 binds the inspected old appearance; no `expected_style` field exists. Record the effective old style separately and verify the resulting computed appearance, including CSS inheritance and transforms.

For an explicitly requested text correction only, a leaf `text`/`tspan` edit also needs exact `expected_text` and new `text`, e.g. `{"selector":{"id":"xlabel"},"expected_text":"Time","text":"Time (s)"}`. This interface does not authorize changing scientific labels/values during a layout-only task. Mixed text/tspan structures and outlines cannot be flattened into editable text. Preserve rich scientific strings and run structure; adjust only approved appearance, not data or axis semantics.

The writer refuses existing outputs, stale source hashes, active/external SVG content and unsupported properties. It writes a new SVG, reparses it and reports rendering as unverified. XML whitespace/prefix serialization can differ; compare semantic nodes and exact scientific content, not just the XML byte diff. Prove curve paths, source canvas/viewBox, transforms, clipping, unrelated elements and all protected text remain unchanged. A label `font-size` is in SVG coordinates: compare final physical glyph size and stroke width after all transforms/PPT scaling, not raw source numbers. Use [aesthetic-review.md](aesthetic-review.md) for grouping, hierarchy, palette and spacing decisions.

Render and inspect the candidate using the same renderer/settings as the baseline:

```sh
inkscape changed.svg --export-type=png --export-background=white --export-background-opacity=1 --export-filename=changed.png
```

Use sufficient raster resolution for the intended physical output and matching SVG/PNG aspect. The replacer tolerates up to 1% aspect-ratio discrepancy, but this numerical check is not visual approval and does not justify distortion. Check both representations; compare SVG path/text structure as well as pixels. A style-only result should change only approved appearance regions.

## 4. Replace the selected external PPT preview

For a previously approved OLE-preview scope, using a slide/key from the current inventory:

```sh
python "$CODE/pptx_origin.py" replace source.pptx candidate.pptx --slide 11 --object ole:1 --png changed.png --svg changed.svg --acknowledge-stale-ole > replacement.json
python "$CODE/pptx_origin.py" verify source.pptx candidate.pptx > preservation.json
python "$CODE/pptx_origin.py" inspect candidate.pptx > candidate-inventory.json
```

For an ordinary picture, use its exact `picture:N` key and omit `--acknowledge-stale-ole`. `--png` is required. `--svg` is optional:

- PNG + SVG: updates DrawingML with matching raster fallback and SVG extension. In the supported paired VML case, VML references the new PNG too.
- PNG only: removes the selected object's old SVG extension, so the old active vector cannot silently remain visible. Choose this only if the intended output allows losing that selected preview's vector representation.

No direct EMF/WMF replacement flag is provided. There is no generalized AlternateContent writer. Only the inspected, tested single VML Choice + DrawingML Fallback pair is supported; shared VML drawing parts and inconsistent branches are refused instead of affecting another slide. Keep an unsupported structure intact and report it rather than stripping its fallback.

The helper adds new media and relationships, leaving old media and relationship definitions available for other users of shared assets. It changes the selected slide/relationship parts, content types only when necessary, and the supported VML part/relationships when present. It leaves every embedded payload byte unchanged. Replacement does not reposition the object or synchronize an internal OlePres cache.

Explain the exact consequence: **the slide's visible preview changed; embedded Origin data and graph objects did not. Opening or refreshing that OLE object can restore the old preview.** The command's acknowledgment flag is a technical guard, not a substitute for user authorization. Do not silently use this route when the required deliverable is a truly edited Origin project.

## 5. Direct native PPT OOXML edits: narrow recipe, not bundled automation

For supported top-level text-shape typography and translations, first use the tested [native PPT adapter](native-ppt-text.md). The following recipe remains necessary for unsupported groups, connectors and other object families.

Native objects can be changed with code, but neither `layout_boxes.py` nor `pptx_origin.py` is a scientific-source layout writer. A box-page arrangement is not a ready-to-apply native-PPT geometry plan. Create and test a **task-specific** patcher for the exact supported object/transform families; if that cannot be done safely, remain at proposal and explain the missing implementation.

1. Load exact read-only bytes with `pptx_origin.Package`; check its source hash, relationships and the task manifest. Refuse signed packages (`_xmlsignatures/`), as the low-level save API does not perform the preview replacer's signature check. Resolve the actual slide part and a unique native `p:cNvPr/@id` together with its ancestry and expected object kind. Never select by text, color, or approximate location alone. Build a semantic group mapping for image, ROI, caption, legend and panel label, plus separate connector endpoint owners.
2. Inspect and record precise old XML attributes, node/run structure, original relationship IDs, crop and group transforms. For ordinary `p:sp`/`p:pic`, position usually lives in `p:spPr/a:xfrm/a:off` and size in `a:ext`; `p:graphicFrame` uses `p:xfrm`. Groups use `a:chOff`/`a:chExt` in addition to outer transforms. Resolve nested scaling, rotation and flips before deriving final slide coordinates. One point is 12,700 EMU. Do not confuse text/ink baselines with bounding boxes.
3. Define the smallest authorized field changes. For a tested **ungrouped, unrotated translation only**, calculate each slide-coordinate delta as `round((approved_anchor_pt - measured_old_anchor_pt) * 12700)` and add it to the guarded old `a:off/@x` or `@y`; leave `a:ext`, crop and native font/line sizes unchanged. A host bounding-box edge is not automatically the measured plot/ink anchor. Translating a panel means all declared semantic members move together. Crop (`a:srcRect`), aspect, scientific strings and glyph/run structure stay protected unless separately authorized. A connector to a stationary owner keeps its fixed endpoint; do not translate the whole connector blindly or break `a:stCxn`/`a:endCxn` attachments. Grouped/rotated geometry needs its own tested coordinate mapping; unsupported transforms must be reported, not coerced into simple x/y. Resizing a PPT host is a separate approved operation, not a way to set an Origin layer width or repair internally distorted text.
4. If approved typography changes native text, preserve each `a:p`, `a:r`, `a:rPr`, `a:t` and baseline/formatting relationship. `a:rPr/@sz` uses hundredths of a point; inherited paragraph/theme/default size also matters. Native line width `a:ln/@w` is in EMU. Do not rebuild the text box, concatenate runs, normalize scientific Unicode/spaces, or assign one raw font size to every semantic role.
5. Before **any** final layout mutation, validate the complete shown proposal and trusted confirmation as described below. Compare every selector, expected old attribute/subtree/hash and proposed change against the exact loaded bytes. Refuse ambiguous IDs, missing/extra group members, unresolved attachments, non-finite coordinates, duplicate/conflicting targets and any stale input. Use explicit exceptions, not Python `assert` as a runtime safety guard.
6. Apply only the allowlisted fields to a copied XML tree. Test that tree before writing. For a known narrow change set, the existing API `pptx_origin.save_package(pkg, changes, additions, target)` can publish the new package without reconstructing unrelated parts; `changes` is a dictionary of exact package part names to verified new bytes and `additions` is empty unless separately planned. This low-level API **does not** check your selectors, approval, semantic membership, allowed fields or render quality; the task-specific patcher must do all of those. Do not serialize the entire deck through a convenience library or rebuild unknown OLE/chart objects.
7. Test the actual patcher on a synthetic version of the object structure first. Cover desired edit, old-value/hash mismatches, duplicate/unknown IDs, existing/symlink output and `python -O`. For group/connector work, prove all declared member translations, both endpoint owners and exact fixed endpoint coordinates, unchanged crop/aspect/text/runs, and refusal of unsupported transforms. Then apply once to a new candidate and verify its exact XML/package diff, semantic content and rendered appearance. Do not call the recipe itself a tested native writer.

### Guide approval gate and its precise limits

`layout_plan.py` is a **read-only binding checker**. It does not move objects, measure glyph ink or authenticate a user. The version-1 plan has exactly `schema_version` (integer 1), `plan_version`, source/guide SHA-256 values, `alignments`, and `questions`. Each alignment has `id`, `reference`, `target`, finite `coordinate_pt`, and `certainty` (`clear` or `needs_confirmation`). Each anchor has exactly `panel`, `object`, `role`, `edge`, `basis`, `axis`.

- Roles: `plot_frame`, `panel_title`, `x_axis_title`, `y_axis_title`, `legend_title`, `other_title`, `panel_label`, `tick_label`, `condition_label`, `reference_label`.
- Edges: `left`, `right`, `top`, `bottom`, `center_x`, `center_y`, `baseline`; x/y must match the final transformed coordinate direction.
- Basis: `stroke_outer` for frames, `ink` for text edges/centers, `baseline` for a measured true baseline. Do not move ticks away from their data values merely to align labels.

```sh
python "$CODE/layout_plan.py" inspect plan.json > guide-review.json
python "$CODE/layout_plan.py" check plan.json --source source.pptx --guides shown-guides.png --approval approval.json
```

Only after the user confirms the **shown** proposal, record a private approval object with exactly `decision: "approve"`, matching `plan_version`, `source_sha256`, `guides_sha256`, canonical `plan_sha256`, the exact `alignments` binding list from the summary, and `user_confirmation` pointing to/quoting the trusted conversation. Use `plan_sha256` returned by inspection: it hashes canonical validated JSON, not raw file bytes. Empty `questions` is required. Changed source, guide, version, coordinate or any plan content invalidates approval.

The actual patcher must call `require_alignment_approval(source_bytes, guides_bytes, plan, approval)` before changing anything, on the same bytes it will use, then apply old-value guards and recheck source/guide hashes before publishing. A prior standalone CLI check is not an authorization token for later changed inputs.

Photo/micrograph edges, ROIs, connectors and semantic groups are **not valid v1 roles**. Do not rename them to fit the schema or pass a valid plot subset and then edit unchecked objects. Keep a complete task plan including source and shown-guide hashes, the actual screenshot/returned-layout evidence hashes, all membership, old/new values, attached/fixed endpoints and style decisions. A task-specific guard must bind and validate this complete plan against trusted confirmation, in addition to v1 where applicable. Until tested, proposal/review is the supported outcome. An alignment approval does not approve unrelated palette, data, text or typography changes.

## 6. Verify and report the actual evidence

`verify` is a comparison report, **not an automatic pass/fail verdict**: inspect `changed_existing_parts`, `added_parts`, `removed_parts`, `embedded_payloads_unchanged`, `unchanged_slides` and `relationship_errors` against the planned allowlist. Independently compare preserved part bytes/hashes and exact target XML/relationships; unchanged slide XML alone does not prove unchanged rendering when resources are shared. Check each active/fallback media part again after replacement. Confirm that outputs contain the intended non-no-op change and source hash is unchanged.

Render the candidate with a trusted renderer in an isolated profile, with macros/external-link updates disabled. Inspect full slides and detail crops at final output scale. Compare every unaffected slide when possible, and every protected neighboring object on a changed slide. Compare native text/runs, paths, axes/ticks/data, crop/aspect and fixed endpoints independently of appearance. Apply the shared [aesthetic review](aesthetic-review.md), not a different code-route style.

For equal-canvas opaque before/after PNGs, use an identity-coordinate overlay:

```sh
python "$CODE/pixel_overlay.py" before.png after.png overlay.png --old-sha256 VERIFIED_OLD_HASH --new-sha256 VERIFIED_NEW_HASH --old-opacity 0.35
```

It retains new nonwhite RGB pixels exactly and puts old gray behind them. It never aligns/resizes images to hide movement. Transparency must first be rendered on white consistently. The overlay is review evidence, not proof of editable source or data preservation; also compare allowed changed regions and semantic invariants.

Report separately: synthetic tests; actual source inventory and baseline conversion; guarded modification; package/content preservation; rendered visual review; actual PowerPoint reopen/inspection; actual Origin open/save and PPT/OLE refresh. Mark unavailable stages **not run**. A Linux/Inkscape result is not a macOS/PowerPoint test. A preview-only deliverable cannot claim native Origin styling or refresh safety. Deliver only the artifact the user asked for, with required visible reference lines and the exact edited layer stated; a clean companion is additional, not a replacement for the final guide-visible result.

## Revisions and rollback

Keep the original, extracted exact bytes, approved plan and every candidate as distinct revisions in the private task workspace. A failure after output creation may leave a file behind; label it rejected and do not deliver it or retry into the same path. No failure authorizes broadening the operation, changing route or overwriting a previous result.

- For a correction, select the intact original or an explicitly accepted, verified revision as the new base. Recheck its hash and target inventory. If the source/plan changed, bind the new values and matching confirmation before generating `revision-002/candidate.pptx`; never copy an old source hash into a new plan to bypass a guard.
- To roll back, return to the verified earlier file. Do not reverse-patch uncertain XML/media or delete rejected evidence automatically. If a separately named recovery file is requested, an exclusive byte-copy is sufficient. Set these values from the verified revision record, then use:

  ```sh
  python - "$VERIFIED_BASE" "$NEW_RECOVERY_PPTX" "$EXPECTED_BASE_SHA256" <<'PY'
  import hashlib, pathlib, sys
  source, target = map(pathlib.Path, sys.argv[1:3])
  expected = sys.argv[3]
  data = source.read_bytes()
  if hashlib.sha256(data).hexdigest() != expected:
      raise SystemExit("Recovery base hash mismatch")
  with target.open("xb") as stream:  # No overwrite, including existing symlinks.
      stream.write(data)
  if source.read_bytes() != data or target.read_bytes() != data:
      raise SystemExit("Recovery verification failed; do not use this output")
  PY
  ```

  The new recovery file restores exactly that revision; it is not a newly refined figure. Re-render/reopen only to the extent needed for the claim being made. Deliver only the requested accepted revision, with its actual verification scope, not every scratch candidate.

## Portable tests and provenance

The seven runtime helpers in `scripts/source_edit/` are byte-for-byte copies of the inspected stable `edit-origin-in-ppt` utilities: `pptx_origin.py`, `svg_edit.py`, `cfb_extract.py`, `wmf_emf_extract.py`, `layout_plan.py`, `pixel_overlay.py`, `compat.py`. Their bounded behavior is preserved. No user fixture, scientific image, private report or local-runtime file is bundled. Independently authored native_ppt and native_origin adapters are separately tested with synthetic inputs; they do not carry private fixed-source profiles or claim general Origin compatibility. Synthetic fixture generators create all test assets in temporary directories. The copied regression tests are retained, with package fixture references replaced by generated fixtures and external-corpus cases omitted. New tests cover snapshot helpers and the complete CLI chain.

Run these separately from the page/layout test suite, from the skill root:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s scripts/source_edit -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python -O -m unittest discover -s scripts/source_edit -p 'test_*.py' -v
python scripts/source_edit/smoke_pipeline.py --output-dir NEW_PRIVATE_TEST_DIRECTORY
python scripts/source_edit/smoke_pipeline.py --output-dir ANOTHER_NEW_TEST_DIRECTORY --render
```

`--render` requires installed Inkscape. Without it, the smoke uses known synthetic primitive PNGs for package plumbing and explicitly records SVG rasterization as **not run**. The optional renderer test is skipped if Inkscape is absent; report that skip instead of counting it as executed. The smoke accepts no real source deck and writes only a new directory. It extracts an actual synthetic source SVG/PNG/CFB, performs a hash-guarded SVG appearance change, replaces synchronized paired preview references, verifies unchanged payload/shared picture/native text/geometry/untouched slide, and produces package protection reports. Synthetic CFB/package envelopes are not real editable Origin graphs or Office compatibility evidence.

At this integration, 121 synthetic tests passed normally and with optimization, and the operation smoke passed with installed Inkscape in both modes. The rendered change was bounded to the intended synthetic curve; all tested package/content protections passed. Real-file EMF-to-SVG conversion fidelity, PowerPoint, macOS, Origin native reopening and refresh were **not run**. Re-run the relevant regression commands when this toolkit, its dependencies/environment or operation family changes. For an unchanged verified toolkit, reuse the recorded template evidence while checking each new source, plan, output and render; the recorded result never certifies a future user file or task-specific native patcher. See [fast-path.md](fast-path.md).
