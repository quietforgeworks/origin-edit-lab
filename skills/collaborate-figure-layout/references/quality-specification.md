# Per-task scientific figure quality specification

For font size, character spacing, line/paragraph spacing and reference whitespace, follow [reference-led typography](typography-reference.md) before choosing or applying numerical targets.

This module makes the shared aesthetics executable as **measured design decisions and acceptance evidence**, not a beauty score. Use it with [aesthetic-review.md](aesthetic-review.md), [alignment-review.md](alignment-review.md), [style-options.md](style-options.md), [source-preservation.md](source-preservation.md) and [verification-and-delivery.md](verification-and-delivery.md). It adds no source writer, native API or automatic permission.

Both entry modes and all three editing routes have the same final visual target. Interactive mode first recovers composition intent; light refinement preserves the accepted arrangement and limits changes. Neither a rough stretch nor a similar reference figure permits moving data relative to axes, relabeling observations, changing values or inventing evidence. Resolve the existing reference-image question once before refinement; no reference means use the established style, not stop.

## Review matrix and correction order

Use this matrix on the actual final-size render. For each applicable row, record observed issue → supported correction → reviewed evidence (or verified-unchanged / blocked with a reason). Cover every selected member; reuse shared evidence without duplicating forms. The table is a decision aid, not a new executable schema or automatic aesthetic score.

| Layer | Inspect | Correct through the supported layer | Acceptance evidence |
|---|---|---|---|
| Whole figure | Reading order, emphasis, outer whitespace, row/column rhythm, completeness | Redistribute blank space and panel geometry within agreed intent | Whole view at final size; source/content coverage |
| Relationships | Requested edges, centers/baselines and label ownership | Derive common positions from aesthetics; do not pin sketch lines or infer extra equal widths | Actual final anchors and positive owner/neighbor gaps |
| Typography | Face/weight/size by role, all native/cache labels, inset readability, glyph aspect | Reference-scaled sizes and undistorted glyphs | Same-role peer glyphs, smallest labels, no substitution/cropping |
| Text spacing | Tracking/kerning, scientific spaces, superscripts, multiline baselines, paragraph gaps | Correct advances/baselines and text boxes; retain exact scientific meaning | Full words/units and dense crops, not nominal point values only |
| Axes and frame | Tick attachment, visible frame bounds, titles/units, line hierarchy and clips | Move appearance anchors and tune strokes without changing ranges/ticks/data mapping | Both directions at final size; source-axis invariants |
| Curves and encodings | Path completeness, color/category mapping, error bars, uncertainty and meaningful marker sizes | Preserve encodings; adjust only authorized presentation properties | Data/path or native-data checks plus visible full curves |
| Color and contrast | Series/legend mapping, light curves, background contrast, requested print/grayscale use | Preserve source palette by default; improve permitted stroke/readability; obtain a clear mapping for requested recoloring | Final-size category distinction without altered scientific color/scale meaning |
| Markers and legends | Square/triangle/circle/composite shape, fills, rotation, sample matching | Restore individual glyphs about data centers; match legend counterpart | Source geometry, centers, actual rendered shape and legend association |
| Annotations/insets | Pulse labels, callouts, ROI/scale bars, legend/colorbar ownership | Reposition in verified empty space; keep complete native components | Text–text, text–stroke and non-text occlusion checks, all close neighbors |
| Scientific imagery | Micrograph/model aspect, contextual crop, valid scale bars | Faithful proportional/crop operations only when appropriate | Intact measurement geometry; no generative evidence replacement |
| Delivery | Editable types/groups, OLE/cache consistency, final guides and active/fallback media | Supported native/cache writes and reversible guide group | Protected content, exact allowed diff, final render and separately stated app checks |

Fix in this order: scientific loss/ownership → clipping or deformation → unreadable type/encodings → collisions → alignment/gutters → minor styling. Solve a shared cause before tuning individual symptoms. Do not trade data, readable reference type or correct symbols for a tidy box grid. A visible failure remains a failure even if a parser/checklist passes.

## Contents

- [1. Establish the task and its design record](#1-establish-the-task-and-its-design-record)
- [2. Measure in the final coordinate system](#2-measure-in-the-final-coordinate-system)
- [3. Resolve the design systematically](#3-resolve-the-design-systematically)
- [4. Apply independent acceptance gates](#4-apply-independent-acceptance-gates)
- [5. Correct narrowly and stop honestly](#5-correct-narrowly-and-stop-honestly)

## 1. Establish the task and its design record

First inspect one complete source view and the densest/most fragile regions. Identify missing panels, clipping, deformation, illegible roles and ambiguous scientific membership. This quick triage prioritizes work; it does not certify exact alignment, native editability or scientific equivalence.

Classify each complete semantic panel and its members: measured plot; micrograph/photograph with meaningful geometry; quantitative simulation/map; verified non-measurement illustration; native text/shape; ROI/inset; legend; connector. Separately record representation: native PPT, Origin payload, external/internal preview, SVG or raster. Unknown scientific role or source representation stays `unknown`; visual resemblance cannot establish either.

Set the intended output medium, figure width/height and final display scale from the user, actual venue specification or accepted source. Record the evidence and units. If unknown, select a clearly labeled provisional viewing size for the proposal and flag physical-size acceptance as unresolved; a screenshot's pixels or DPI tag alone do not establish print dimensions. Choose routine numbers yourself from measured samples rather than asking the user for every gap or font size.

Create a private design record before exact editing. A task-local record is not the bundled alignment helper's schema and cannot be passed to it as approval. Each target needs an actual old measurement, proposed value/range, units, measurement method, uncertainty/tolerance rationale and evidence. Reuse a versioned accepted style only where role, source semantics, output scale and renderer assumptions match. Defaults are starting values, never proof that a new figure passes. User preferences may override aesthetic defaults, not scientific fidelity or safety.

The following is an optional record example, not a mandatory form or measured user data. Keep only fields relevant to the task and reference shared unchanged evidence; do not copy the entire form for a small correction. Cover affected objects/roles and required final checks. Actual executable plan/coverage schemas remain strict and separate. Replace any used placeholders with evidence; `null` means unknown, not zero or passed. Keep the record private.

```yaml
spec_version: figure-quality-v1
revision: "<task proposal revision>"
source: {sha256: "<verified hash>", inventory: "<private record>"}
mode_route: {mode: "<interactive|light>", route: "<selected route>"}
output: {medium: "<print|screen>", width_pt: null, height_pt: null, display_px: null, evidence: "<source or explicit assumption>"}
style: {version: "<accepted preset revision>", reference: "<inspected reference or established style>", adopted_features: []}
objects:
  - {id: "<stable panel/member>", class: "<scientific role>", representation: "<actual layer>", members: [], endpoint_owners: [], protected: []}
coverage:
  - {id: "<every visible member>", role: "<actual role>", x_relation: "<peer/own-axis/intentional exception>", y_relation: "<peer/own-axis/intentional exception>", distortion_check: "pending", font_peer_set: "<role set or not text>"}
roles:
  - {role: "<tick label|unit|axis title|panel letter|legend|condition|reference>", sample: "<exact glyph/run ID>", old_ink_height_pt: null, target_ink_height_pt: null, font_weight: "<verified face/weight>", tolerance: "<method-bound>", evidence: "<render/crop>"}
strokes:
  - {role: "<frame|tick|curve|error bar|marker>", old_visible_pt: null, target_visible_pt: null, orientation: "<both directions>", evidence: "<sample>"}
relationships:
  - {ids: ["<reference>", "<target>"], basis: "<stroke|ink|baseline|image edge>", axis: "<x|y>", old_pt: null, target_pt: null, tolerance: "<basis and reason>"}
spacing:
  - {neighbors: ["<panel/member>", "<panel/member>"], basis: "<frame gap|nearest ink clearance>", old_pt: null, target_pt: null, minimum_clearance_pt: null, evidence: "<measured sample>"}
panel_letters:
  - {id: "<letter>", owner: "<scientific panel>", own_edge_gap_pt: null, neighboring_panel_distance_pt: null, target_gap_pt: null, ownership_fullview: "pending"}
colors: {mode: "<preserve|approved mapping>", series_mapping: [], contrast_evidence: "<actual final-scale tests>"}
change_map:
  - {target_id: "<exact object/field>", old: "<guarded old value>", new: "<approved new value>", expected_pixel_regions: "<old/new extents plus stroke/ink allowance>", invariants: []}
guides: {native_group_id: "<unique group>", members: [], behind_science: null, removal_equivalence: "not run"}
evidence: {clean_hash: "<shown clean view>", guide_hash: "<shown guide view>", confirmation: "<trusted user message>"}
acceptance: {structure: "pending", final_size: "pending", details: "pending", final_font_audit: "pending", guides: "pending", application_lifecycle: "not run"}
```

For a concrete relationship, record “the outer left frame of `<panel B>` equals the measured outer left frame of `<panel A>`,” with their real IDs and coordinates. For readable type, record the actual accepted tick sample and its final ink height, then derive each other role from that sample. Do not fill unknown quantities with plausible-looking numbers. A missing required measurement blocks only the affected exact claim or edit; prepare independent work normally.

## 2. Measure in the final coordinate system

Use slide points with a stated origin for geometry and final rendered pixels for appearance. Preserve the complete transform chain. `pt = EMU / 12700`; native text `sz / 100` gives nominal points, not ink height. For an unrotated PPT group, each local axis maps as `outerOff + (local - childOff) * outerExt / childExt`; compose ancestors. Rotation, flips, crops and nonuniform transforms require their actual mappings. An unsupported transform is unresolved, not an excuse to ignore it.

For a render of known final width `W_pt` and pixel width `W_px`, measure physical ink height or gap as `measured_px * W_pt / W_px`. Check height mapping too; disagreeing x/y scale reveals nonuniform output. This conversion is valid only for the same known page/crop and intended physical size. For screen output, inspect at the intended display pixels, not only a zoomed desktop preview. If actual physical display calibration is unknown, say so.

For a safely inspected SVG, verified installed Inkscape supports bounding-box queries and same-page rendering. Use new private output filenames and explicitly set the same width/background for before and after. These commands illustrate supported inspection, not native Origin editing:

```sh
inkscape "$INSPECTED_SVG" --query-all > "$NEW_BOUNDS_CSV"
inkscape "$INSPECTED_SVG" --export-area-page --export-type=png --export-width="$RENDER_WIDTH_PX" --export-background=white --export-background-opacity=1 --export-filename="$NEW_RENDER_PNG"
```

Resolve query IDs to actual scientific members and establish query units/viewBox-to-host mapping. Query bounds are candidate object bounds, not proof of true text baselines, glyph ink or frame-stroke boundaries. Inspect rendered crops or verified outlines for those anchors; use the actual text transform/metrics for baselines. If baseline data cannot be recovered, use a verified ink relationship and label it honestly instead of claiming baseline equality. Never infer ticks' data positions from their labels' bounding-box edges.

For typography, compare matching glyphs/strings in the same face and weight, including superscripts, descenders and rotated titles. Record representative and worst-case role samples; a single readable label does not certify every instance. Measure frame/tick/curve widths on straight portions away from intersections and compare horizontal and vertical directions. Inspect hairlines and faint colors at final size, since enlarged crops can conceal dropout.

Use exact approved coordinates in the model where supported. Choose visual tolerances *before* reviewing the candidate, from the render grid, measurement uncertainty and observed unchanged-baseline rendering variation. If a needed tolerance is unmeasurable, mark it unresolved. Do not adopt a universal pixel/font/spacing threshold or enlarge tolerance afterward to conceal an error. No tolerance can excuse clipped content, false scientific mapping or a visible collision.

For before/after review, render the same canvas, crop, origin, background and scale; retain separate source/candidate views. Use the identity PNG overlay described in [alignment-review.md](alignment-review.md#verify-pixels-and-compare-equal-canvases). Never register, rescale or crop-to-content to hide movement. The allowed-change map includes both the old and new extents of translated objects and affected edges, not an entire slide-sized permission mask. Check semantic invariants inside allowed regions as well as unexplained differences outside them.

## 3. Resolve the design systematically

**Composition and spacing.** Preserve the scientific sequence and user emphasis. List adjacency pairs and choose whether each gap is frame-to-frame, image-edge-to-edge or nearest-ink clearance. Measure both inter-panel gutters and internal title/annotation gaps from the actual visible ink/strokes. Record which gaps are intra-group and which are inter-group; preserve their accepted hierarchy instead of equalizing every empty rectangle. Establish repeated gaps from a readable accepted peer; allow declared exceptions for dense legends, unequal scientific roles and insets. Balance outer margins against the occupied scientific region. Redistribute unused whitespace before shrinking content; do not trim scale bars, context or labels to equalize boxes.

**Type and stroke roles.** Define separate targets for tick labels, units, axis titles, conditions, legends, panel titles/letters, diagram labels and references, with subordinate runs preserved. A unit embedded in a title follows that title's role, not an unrelated global unit-size rule. Start from a demonstrably readable tick sample at the chosen final size, then derive the restrained hierarchy in the accepted style. Carry frame/tick targets separately from curves, error bars, markers and uncertainty fills. Choose final visual weights, not copied native integers. Recheck all roles after any geometry change or font substitution; preserve scientific symbols and rich text exactly.

**Frames, titles and exact guides.** Specify both ends of each relevant column/row: outer left/right/top/bottom frame edges, image edges, title centers/ink edges and actual baselines. Decide explicitly whether a title centers on its own plot or aligns across peers. Attach letters to their own panel by measured ink offsets. When constraints conflict, preserve data mapping and readability, then adjust the enclosing layout rather than forcing every boundary into one grid. Show intentional offsets in the plan.

**Unmistakable panel-letter ownership.** Place each letter near its own upper-left visible image edge or plot frame, not near the middle of the gutter between neighboring panels. Measure its horizontal ink-to-own-frame gap and distance to neighboring panels before/after. Shorten an excessive owner gap while preserving positive clearance; derive the target from this layout and accepted sample, not a universal offset. Check the full figure for immediate letter-to-panel association. Equal letter size or a shared baseline never justifies an ambiguously detached letter.

Complete the two-dimensional coverage inventory for **every axis/spine, tick, tick label, unit, axis/panel title, panel label, legend symbol/text, annotation, connector, frame, image/ROI and scale bar**. Record each meaningful x/y edge, center, baseline, own-axis or attachment relation and its measured result. Give nonapplicable peer alignment an explicit scientific/design reason; never silently omit a role. Match true peers only: ticks stay at their data coordinates, units stay in their source runs, and unrelated annotations need not share a baseline. “Everything checked” means no unreviewed elements, not forcing all objects onto identical coordinates.

**Ticks, legends and associations.** Keep tick values/positions, scales, axis ranges, category order and scientific axis count unchanged unless a separate exact scientific edit is authorized and supported. Distinguish those source-data invariants from approved tick appearance: direction, length, stroke width, glyph face/size or label placement may change only within their exact approved scope, while values, scale, count, tick coordinates and value-to-position mapping remain protected. Do not hash approved cosmetic fields into a data fingerprint, or exclude data-bearing fields merely to make fingerprints match. Check each tick-to-value and legend-to-series mapping before/after. A reference's sparse axes do not authorize deleting labels. For a cramped legend, try free-space relocation or approved wrapping without changing entry order/association; check neighboring data and all entries. Never move observations or relabel data to make a reference style fit.

**Color and contrast.** Preserve source colors by default. For a requested change, map exact scientific IDs and legend keys to proposed colors, retaining sequential/diverging ordering and any meaningful midpoint. Test actual curve overlaps, markers, error bars, transparency and background at final size. Inspect grayscale; use color-vision simulation only when actually available and name the test performed. Contrast ratios, if computed, describe sampled colors, not guaranteed curve distinguishability. If series remain ambiguous, propose explicit redundant markers/dashes or a stronger approved mapping, not fewer series.

**Images and deformation.** Compare source and final aspect/crop for each image class. Micrographs, measured photographs, dimensional geometry and quantitative maps retain meaningful geometry, calibration, scale bars and ROI context. Confirmed rough stretching must be recovered from intact sources before final output, including normal glyphs, axis/tick geometry, strokes and originally circular markers. An undistorted raster can be fitted uniformly; it cannot supply editable curves. Only verified non-measurement artwork may adapt its body under the existing aesthetic rules, retaining labels, components and meaning. Generated lookalikes never replace scientific evidence.

Run the distortion audit against **every role in that coverage inventory**, not just pictures: axis/frame proportions and weights; tick lengths/positions; all text/units/subordinate runs; legend symbols; marker shapes; annotation and connector geometry. Compare each with the intact source and approved transform. Restore unintended anisotropic scale/skew while retaining deliberate rotations and meaningful ellipses. A normal-looking title cannot excuse a stretched tick label, unit or legend elsewhere. Re-render after restoration and revisit both alignment dimensions.

**Groups and connectors.** Compare the exact semantic member list before/after, including image, ROI, scale bar, captions, inset, legend and letter. Native group boundaries alone do not establish membership. Verify both connector endpoint owners and fixed/moving coordinates; a correct-looking arrow can still point to the wrong observation. Unknown attachment prevents that move, not all independent refinement.

**Mandatory final reference guides.** Each final figure slide in an editable PPT must contain **one independent native group containing all its alignment guides**, selectable/hidden/deleted together, behind scientific content and visually distinct from data. Do not scatter guides among scientific groups or confuse reference guides with scientific reference curves. Use the verified guide method in [alignment-review.md](alignment-review.md#create-removable-native-guides). Inspect the actual final file for one uniquely identified guide group per figure slide, unique shape IDs, expected guide-only member types/counts, correct stacking and no scientific members or changed connections. Choose visible comparison segments in available margins/gaps without obscuring evidence. Remove only that group on a verification copy and prove clean-content/coordinate/relationship equivalence and same-render equality; retain the group in the delivered final. A clean companion is additional, never a substitute. A final screenshot/image must visibly show the guides but cannot claim editable grouping. If the requested format or available writer cannot meet the requirement, disclose that precise limitation; do not claim the guide gate passed.

Marker-shape acceptance also covers squares, triangles and composite plot/legend glyphs: compare source proportions, angles and intended orientation after the full affine transform; preserve data centers and any measurement encoding. A matching glyph bounding box alone does not prove the square/triangle is restored. Follow [marker-glyph restoration](aesthetic-review.md#restore-plot-and-legend-marker-glyphs).

## 4. Apply independent acceptance gates

Run these against the actual final artifact, not only the proposal. Record `pass`, `fail`, `unverified` or `not run` with evidence; no averaged score can override a failed gate. Keep source integrity, measured geometry/shape and independently viewed whole-figure quality as separate decisions. A code-generated green report or complete supplied observation record cannot pass the visual gate.

1. **Scientific truth and source protection:** source hash unchanged; exact text/runs, data/bindings, axes/ticks, fits, image aspects/crops, ROI/scale bars and associations preserved except individually authorized changes. Check package/representation invariants for the selected route. For native saves use scientific comparisons, not assumed byte equality. Uninspectable properties remain unverified. Similar pixels alone never prove data preservation.
2. **Allowed-change map:** expected old/new fields and actual package/object differences agree; the requested change is present rather than a no-op. Review every changed region and protected neighbor, including shared-resource effects on other slides. Unexplained differences must be resolved, not dismissed by an aggregate pixel similarity score.
3. **Measured geometry and shape:** check scientific association constraints and the complete explicitly confirmed layout constraint set against actual final coordinates and transformed ink; do not freeze unconfirmed draft positions or gaps. Cover both true column bounds, real text baselines, letter ownership, whole composite centers, intra/inter-group clearances and full-affine marker shape. Missing measurements remain unverified; failed required relationships cannot be downgraded to optional exceptions. The [supplied-observation checker](observation-checker.md) can check its bounded schema, not discover or approve relationships.
4. **Full-view acceptance at final size:** all intended panels present and the sequence/emphasis clear; readable smallest necessary text; coherent role/stroke hierarchy; balanced margins and deliberate gaps; each letter unmistakably belongs to its own panel rather than the neighboring-panel midline; no detached letters, lost legends, residual stretching, clipping, illegible overlap or unexplained empty regions. A zoomed detail view cannot pass this gate for a crowded full figure. Judge inherited defects too: preserving the source or recognizing a deliberate inset does not establish that its placement leaves the underlying evidence visible.
5. **Detail acceptance:** inspect every altered object and fragile area, plus representative unchanged peers: superscripts/units, dense tick/legend text, rotated titles, uncertainty marks, curve intersections, scale bars, ROI edges and connector endpoints. Verify measured target relationships/tolerances and positive clearances. Full-view attractiveness cannot compensate for incorrect units, label associations or damaged scientific features.
6. **Independent final font audit:** after every PPT/group/SVG/text/host transform is final, compare actual rendered ink heights and perceived sizes within each genuine same-level peer set at the intended physical/display size. Compare matching glyphs in verified faces/weights; account for cap/x-height, glyph composition and rich-text runs rather than making unlike characters equal-height. Audit all peer instances, reporting min/max measurements and explained exceptions, not just nominal point sizes or a single sample. Preserve different-role hierarchy and sub/superscript semantics. Repair mismatched peers through supported edits, then recheck dense details, all affected clearances and the whole figure.
7. **Final guide acceptance:** each delivered figure slide contains its single reversible native guide group; clean and guided views share identical scientific geometry; actual removal/restore checks pass. Guided raster output visibly includes guides and is labeled raster. Guides must not hide or resemble evidence; inspect both final guided full-view and details, not just the clean companion.
8. **Claim-specific application evidence:** separately report rendering, actual PowerPoint viewing, actual Origin reopen/save and OLE refresh when relevant. Use [verification-and-delivery.md](verification-and-delivery.md); unavailable lifecycle checks remain `not run`. Beautiful rendered output does not certify a persistent native edit.

## 5. Correct narrowly and stop honestly

Use the smallest correction that addresses the measured defect: translate a bound group or annotation, reclaim non-scientific whitespace, then consider a supported geometry/type change. Do not start by shrinking all text, globally recoloring, reflowing every panel or replacing evidence. Re-render the affected region and the full figure after each candidate; repeat integrity and guide checks for every relevant change.

Default to one planned correction pass and one verification-driven correction pass after the initial proposal. This is an efficiency budget, not permission to accept a defect. Reuse unchanged measurements/tests; exactly recheck changed properties, transform descendants, adjacent clearances, shared resources and the final whole view. Rebind changed execution plans. Obtain new confirmation only for material changes of source, selection/order, relationship meaning or agreed aesthetic scope; routine numerical repairs within it remain authorized.

If the same defect persists, the source cannot support the target, or any fidelity check fails, stop the affected edit and preserve a rejected candidate separately. Return to the last intact verified source/accepted revision, never reverse-patch uncertain changes or overwrite originals. State the specific remaining issue and supported alternative; ask one focused question only when it affects the choice. More iterations are justified by a new measurable hypothesis or user direction, not blind retries. Deliver a preview with an explicit limitation when appropriate; do not label it a completed high-quality final figure.


