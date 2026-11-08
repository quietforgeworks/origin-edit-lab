# Alignment, guides and visual verification

Read this when turning an approximate arrangement into exact scientific geometry. Use [aesthetic-review.md](aesthetic-review.md) for the shared look and [refinement-routes.md](refinement-routes.md) for the selected writer and its permissions. These alignment and acceptance rules are identical for direct Python editing, Windows native Origin through an available MCP, and the Mac-to-VM CLI bridge. This reference supplies a review method, not a universal scene editor.

## Contents

- [Coarse regions versus exact anchors](#coarse-regions-versus-exact-anchors)
- [Build the semantic anchor inventory](#build-the-semantic-anchor-inventory)
- [Keep groups and connector endpoints distinct](#keep-groups-and-connector-endpoints-distinct)
- [Show, clarify and confirm the whole plan](#show-clarify-and-confirm-the-whole-plan)
- [Respect the bounded approval helper](#respect-the-bounded-approval-helper)
- [Measure transformations and clearance](#measure-transformations-and-clearance)
- [Create removable native guides](#create-removable-native-guides)
- [Verify pixels and compare equal canvases](#verify-pixels-and-compare-equal-canvases)

## Coarse regions versus exact anchors

**Coarse region guides** describe approximate panel placement, sequence, relative area and grouping. Examples are draggable thumbnail boxes, a screenshot's panel regions or a rough column outline. They can support an initial proposal without exact coordinates, but cannot establish true plot-frame, glyph-ink or baseline alignment. A selected box's size is not an instruction to stretch the original scientific object. Final fonts, axes, ticks, circular marks and scientific aspect must be restored from the intact source rather than copied from that distorted preview; see [the final restoration rule](aesthetic-review.md#restore-final-fonts-and-geometry).

The default handoff is a screenshot returned from the local offline HTML. Treat it as approximate intent and retain it as the arrangement evidence; a saved-state/JSON export is optional. Recover clear order, grouping and emphasis without demanding exact coordinates. Reconstruct precise anchors from the bound original source, and ask only about genuinely ambiguous membership, omission or relationships. A multi-selection used to move boxes together is not by itself a scientific group binding.

**Exact semantic guides** identify measured objects and the particular visible relationship being proposed: outer frame stroke, image edge, title ink edge, label center or true baseline. The shown proposal must make clear which relationships are intended and which objects remain deliberately offset.

A requested effect or guide preview may be created on a separately named disposable proposal copy within its requested appearance scope before final-source confirmation. Originals remain untouched; describe it as a proposal. An unchanged-source guide view is also valid for reviewing candidate anchors. Do not confuse permission to prepare either view with approval to commit the proposed geometry to final source output. Use the chosen route's existing authorization requirements; see the route guide rather than inventing a new editing path.

## Build the semantic anchor inventory

Record every relevant anchor in one final coordinate system, normally slide points with an explicit origin. Each entry needs:

- Stable panel identity and exact inspected object/element identity, including slide, shape/group path and representation where needed.
- Semantic role: frame, image, ROI, panel letter, panel/axis/legend/other title, tick, condition, reference, or connector endpoint.
- Measurement basis: outer visible stroke, actual image/ROI edge, glyph ink, true baseline or a verified endpoint/data anchor. A container or text-box edge is not a substitute.
- Edge or direction: left/right/top/bottom, center, or transformed baseline; final x/y coordinate or an explicitly measured oblique line.
- Current measurement, proposed target, reference object, confidence, and the scientific relationships that must remain unchanged.

Cover both axes and both ends of relevant rows/columns. Inspect outer frame left/right/top/bottom edges, not just width and height. A confirmed same-column relationship requires the true left **and** right bounds to match, unless the accepted plan explicitly specifies an unequal width. A matching left edge with a staircase on the right is not aligned. Preserve source-established scientific associations and explicitly confirmed composition constraints; do not treat rough source geometry as immutable or downgrade a declared required relationship merely to obtain a pass. Include panel titles, horizontal and vertical axis titles, legend titles, panel letters, and nearby conditions/references. A shared font size or baseline does not prove ink edges align. Conversely, equal nominal text-box tops or glyph tops do not prove true baselines align; compare the actual transformed baseline even when strings have different ascenders or descenders.

A vertical guide at x compares left/right/center-x anchors. A horizontal guide at y compares top/bottom/center-y anchors. For a rotated title, transform its ink outline and baseline direction before measuring. Do not label an oblique baseline as an ordinary horizontal or vertical coordinate merely to fit a schema.

Title centering on its own axis and cross-panel title alignment are different constraints. Tick labels with different string lengths can have different ink edges while remaining correctly centered on ticks. If frame, title and tick-text goals conflict, propose an enclosing layout or text-anchor adjustment that preserves scientific mapping, or ask which visible relationship matters most. Never detach numeric labels from their ticks.

Ignore hidden/transparent padding when measuring visual image edges, but preserve the scientific crop and ROI context. A rotated rectangle's axis-aligned envelope is not the same as its visible edge. Deliberate insets and unequal panel sizes are not alignment errors.

## Keep groups and connector endpoints distinct

Define semantic panel membership from scientific association. A move plan must list each image/plot, ROI, title, caption, legend and panel letter that travels with that panel. Keep separable plots independently addressable even when they share a printed panel letter or a native PPT group. Do not infer membership from proximity alone.

Treat each connector separately from rigid panel membership. Record its two owners or data anchors, endpoint identities and old coordinates, native connection IDs, arrow direction, rotation/flips and routing as applicable.

- If one owner moves, move only that owner's attached endpoint and preserve the stationary endpoint and meaning.
- If both owners move, derive each new endpoint from its own owner's approved transformation; do not blindly translate the complete line.
- Preserve native attachment and elbow routing semantics where supported. A visually nearby endpoint is not proof of attachment.
- An unresolved owner or attachment is a specific question to resolve before source application.

A visual leader added to improve label clearance needs a known correct association. Its appearance alone does not establish a machine-readable data binding.

## Show, clarify and confirm the whole plan

Use this sequence without requiring a separate question for every obvious match:

1. **Inspect and propose.** Identify clear matching peers automatically. Show a clean proposal and a guide view with their exact anchors. When asked only for a rough arrangement, label it coarse and postpone exact-source claims.
2. **Ask about real ambiguity.** Name the two objects and candidate relationships, for example: “Should this micrograph's visible bottom match the plot's outer bottom frame, or the panel-letter baseline?” Ask similarly precise membership or endpoint questions.
3. **Resolve and show the complete result.** Incorporate the answer into the plan and shown guides. Include clear and formerly uncertain relationships, not just the last pair discussed. Obtain confirmation of that complete version before final source application.
4. **Apply the confirmed plan.** Execute its clear approved relationships without repeatedly asking. If the bound source, shown guides or plan changes, including target, membership, endpoint, style or geometry, show the revised complete plan and obtain matching confirmation.

The task-local complete plan should contain exact source bindings and the arrangement evidence (normally the returned screenshot, or an optional verified export), proposal version and complete plan hash, hashes of the clean/guide views actually shown, all semantic members and connector attachments, target coordinate system, old values and proposed changes. Include unresolved questions, typography/palette decisions and protected scientific properties. A new guide file or revised plan must not inherit stale approval.

A user's arrangement approves the composition direction, not unrelated changes to axes, content, color or typography. An imported file's `approval` field or a generated review report is not authenticated conversation evidence. Record the actual user's confirmation privately and use the selected route's writer guards.

## Respect the bounded approval helper

The bundled `scripts/source_edit/layout_plan.py` is a read-only alignment approval helper. Reuse the verified schema/implementation version and its established tests when unchanged; do not rediscover its role vocabulary on every task. The current source, complete plan, shown guides, old-value guards and user confirmation still require their per-run checks. Its schema version 1 supports these roles:

`plot_frame`, `panel_title`, `x_axis_title`, `y_axis_title`, `legend_title`, `other_title`, `panel_label`, `tick_label`, `condition_label`, `reference_label`.

Supported bases are `stroke_outer` for plot frames, `ink` for text edges/centers and `baseline` for actual text baselines. Pairs use the same final coordinate axis; arbitrary oblique baselines require a different supported measured representation. The helper binds source, shown guides, full validated subset plan and exact anchor identities. Its canonical plan hash is generated by the helper, not a raw JSON file hash.

Use exactly these schema fields for the supported subset:

- Plan: `schema_version: 1`, an explicit string `plan_version`, `source_sha256`, `guides_sha256`, `alignments`, and `questions` (unresolved strings).
- Each alignment: unique `id`, `reference`, `target`, finite final-slide `coordinate_pt`, and `certainty` (`clear` or `needs_confirmation`). Reference and target must be distinct and use the same axis.
- Each anchor: `panel`, exact `object`, `role`, `edge`, `basis`, and `axis`. Edges are `left`, `right`, `top`, `bottom`, `center_x`, `center_y`, or `baseline`; axes are `x` or `y`. Preserve the actual scientific tick mapping for tick-label anchors.

```sh
python scripts/source_edit/layout_plan.py inspect plan.json > review-summary.json
```

The returned `review_required` summary is not approval. After the actual user confirms the complete shown proposal and questions are resolved, privately record an approval object with exactly `decision: "approve"`, matching `plan_version`, `source_sha256`, `guides_sha256`, `plan_sha256`, the summary's exact `alignments` binding list, and `user_confirmation` pointing to or quoting that trusted confirmation. Do not manufacture it from the generated summary.

```sh
python scripts/source_edit/layout_plan.py check plan.json \
  --source source.pptx --guides shown-guides.png --approval approval.json
```

A task-specific final-source editor must call `require_alignment_approval(source_bytes, guides_bytes, plan, approval)` before mutation, using the same bytes it will edit. Apply separate expected-old-value guards and recheck bindings immediately before writing a new output. A changed source, guide, version, target coordinate or any other plan content invalidates the old approval.

The helper is read-only: it neither edits content nor authenticates the user, proves old geometry, checks image appearance or validates all whole-slide objects. Photographs, micrographs, native image boundaries, ROI geometry and connector endpoints are **not version-1 roles**. Do not falsely relabel them `plot_frame` or `other_title` to pass the gate. A native text object may use a supported text role only when that is its real semantic role; “native” does not make an image a frame.

For a plan involving unsupported roles, bind the **complete combined plan**, including all members, endpoints, old values and changes, to the exact shown proposal and confirmation. Automated application additionally needs an independently tested whole-plan guard that checks those fields against the actual source bytes. Run the stable gate for its supported subset where applicable, but never treat that subset's success as approval or validation of unchecked objects. If no verified full-plan guard exists, remain at proposal/review for those changes.

Use the selected execution route for actual writer capabilities. This reference does not extend a helper, bypass its schema or establish that any native-source writer exists.

## Measure transformations and clearance

Before exact final alignment, remove rough-box deformation using intact source objects or a faithful original representation. Use supported native/source edits and render them, keeping normal glyph aspect, correct axis/tick mappings, source-consistent marker/icon shapes and scientific image aspect. Restore circular marks only when the original establishes they were circles; preserve meaningful ellipses and intended oblique geometry. A deformed thumbnail, screenshot or cache cannot be flattened and accepted as final output. With only an undistorted original raster, scale uniformly and change the layout rather than inventing editable curves or text.

Map each anchor and visible mark through the actual local-to-final chain: source/device frame, SVG or native object transforms, ancestor groups, viewBox, image crop/extent, PPT group `chOff`/`chExt`, rotation/flips and host placement. Use 12,700 EMU per point and the actual output DPI where applicable. A picture width ratio alone is insufficient.

A local em height f under a final linear transform J has vertical-axis scale diagnostic `f × ||J(0,1)||`. This is not the glyph's ink height. Inspect both axes or singular values for anisotropic scale/skew; compare real glyph outlines or masks in the intended font/weight after rendering.

For an ordinary geometric stroke of width w and unit tangent t, transformed normal thickness is `w × |det J| / ||J t||`. Horizontal and vertical strokes can therefore differ after nonuniform scaling. Treat non-scaling strokes, rasterized lines and Office line semantics separately; verify actual final pixels rather than assuming this formula covers every representation.

Measure title and annotation gaps from transformed ink to the neighboring stroke/ink boundary. Include superscripts, descenders, marker sizes, error bars and multiple nearby obstacles. For a rotated ellipse, use the transformed ellipse boundary rather than its axis-aligned bounding box. Keep a small positive gap at final physical size, chosen for this figure instead of a universal offset.

Distinguish a marker glyph from a scientific region before restoring shape. For a source-established round or elliptical marker, compose the full affine transform through every ancestor and restore only unintended glyph distortion; a data-coordinate center does not exempt its glyph shape. Preserve a deliberate rotation and original ellipse proportions. For a composite pictogram/marker, use the full semantic group, its center, and member relationships rather than shrinking individual leaves independently. A data-coordinate ROI, fitted ellipse, confidence region or dimensional shape is scientific geometry: do not force it to roundness or use peer-layout alignment to change its data mapping. Unknown role or unsupported transform remains unresolved.

Measure horizontal and vertical spacing from actual visible ink/strokes, including composite members and nearby obstacles, not only group boxes. Keep an explicit hierarchy for related items inside a group versus gaps between independent groups; use accepted source/plan relationships rather than imposing a universal ratio. If the group-to-group gap exceeds the plan or a label is optically detached, box nonintersection alone is insufficient. Required center/edge/gap relationships can be represented as measured semantic anchors and offsets; the [bounded checker](observation-checker.md) does not discover them or inspect their truth.

Try minimal translation and whitespace redistribution before shrinking text or scientific content. Keep panel letters visually near their own panel and condition labels with their own curve/group. Recheck association after local movement.

If supported plot-height/width adjustment is separately included in the confirmed plan, map curves, markers, ticks, grids and clip paths consistently while keeping their data-coordinate meaning. Transform text anchor positions without distorting glyphs; compensate visible frame weights and recheck both ends of the frame. Changing only the outer picture box can distort text or hide clipping. Do not pass unsupported geometry operations to an appearance-only helper.

A single renderer's subpixel hinting offset does not justify damaging valid OOXML geometry. Compare coordinate evidence with actual pixels and isolate renderer differences before proposing a correction.

## Create removable native guides

Every final figure includes visible alignment reference lines. For final editable PPT output, create one separate native `p:grpSp` containing **all** reference-line objects for that figure/slide. The group is independently selectable, hideable and deletable; it is not a PowerPoint View Guide and never a scientific/data curve. Multiple slides require one group per slide, since PPT cannot group across slides. A clean companion is optional but cannot replace the guided final version.

Place the group behind scientific content, after the mandatory shape-tree properties and before source objects. Use restrained contrast/weight so lines remain visible without obscuring axes, labels or data. Keep the exact measured horizontal/vertical relationships visible; include only relevant scientific alignment anchors, not decorative grids. Do not change source objects or scientific layers merely to make the references visible.

Use the bounded guide-only helper described in [guide-tool.md](guide-tool.md) once its target/plan format is verified. It is distinct from `layout_plan.py` (approval checking) and `pptx_origin.py` (preview/package helpers). It does not move scientific objects or determine which anchors should align. Bind exact source/slide/line coordinates and keep names/IDs unique. Unsupported structures need an explicit blocker or a separately tested narrow implementation, never an unverified full-deck rewrite.

Programmatically inspect group uniqueness, native group type, all expected guide members, exact coordinates and allowed member types. Remove only that group from a comparison tree and verify the scientific content/coordinates/text/relationships are unchanged. Also run the supported restoration path to a fresh file and compare it to the saved clean version. Actual manual deletion/hiding in PowerPoint is a separate app test, not established by XML verification.

For SVG/vector output, keep references in a distinct group when that format/tool supports it. For a final screenshot/PNG, visibly render the guides but do not claim independently editable or hideable grouping in raster pixels; preserve the separate guide layer in the working artifact. Clearly label the image as the guide-visible final effect. If the requested editable format cannot preserve the required group, report the limitation rather than omit it.

## Verify pixels and compare equal canvases

Review the produced files independently of the editing script's success report. Render a copy without saving back through the renderer, with macro/external-link updates disabled. Inspect the actual full-slide pixels at intended viewing size and native-resolution detail crops.

Check at minimum:

- Confirmed frame edges in both directions, title ink/center/baseline relations and deliberate offsets. Use numerical geometry or measured pixels as appropriate, not eyeballing container widths alone.
- Restored glyph aspect, axis/tick geometry, source-consistent circular marks and final glyph/stroke hierarchy; symbols and rich text, native-text wrapping/autofit, rotated titles, panel-letter proximity, positive label gaps and all close ellipse/ROI/marker boundaries. Confirm these in fresh source-based renders rather than deformed thumbnail/cache pixels.
- Scientific image aspect/crop, complete legends/scale bars, inset proportions, group membership and each fixed/moving connector endpoint.
- No unexplained pixel differences outside the authorized regions or on untouched slides.
- Consistency of clean, guide and final views and exact guide removal restoration. Use [verification-and-delivery.md](verification-and-delivery.md) for protected scientific/package checks and representation validation.

For an old/new overlay, render identical slide dimensions, DPI, canvas, crop and origin. Reject mismatched canvases. Do not auto-register, translate, rotate, rescale or crop-to-content, because those operations conceal the layout changes being reviewed. Flatten transparency onto the same explicit background, normally white, before comparison.

The bundled `scripts/source_edit/pixel_overlay.py` compares two inspected opaque PNGs at identity coordinates. It puts the old image in grayscale on white at configurable opacity (default 35%) and retains the new render's nonwhite RGB pixels at full opacity; exact-white new pixels leave the old layer visible. It does not align images or decide whether changes are allowed. Keep old, new and overlay images together so old “ghosts” are not mistaken for final output.

```sh
python scripts/source_edit/pixel_overlay.py old.png new.png overlay.png \
  --old-sha256 VERIFIED_OLD_HASH --new-sha256 VERIFIED_NEW_HASH \
  --old-opacity 0.35 > overlay-report.json
```

Use the overlay to inspect frame shifts, glyph movement, unexpected cropping and conversion drift, not to prove scientific equivalence. Distinguish intentional edits from unaccepted conversion/renderer differences. An overlay cannot establish actual PPT display, native Origin editability, save/reopen success or OLE refresh persistence. Use the separate evidence stages in [verification-and-delivery.md](verification-and-delivery.md) and mark unperformed checks **not run**.
