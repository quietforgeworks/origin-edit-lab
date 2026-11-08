# Shared scientific aesthetic review

Use this reference to turn the user's rough arrangement into a coherent scientific figure. The same visible target applies to all three execution routes: direct Python editing, native Origin on Windows through an actually available MCP, and the Mac-to-VM CLI bridge. Implementation and preservation boundaries belong in [refinement-routes.md](refinement-routes.md); no route earns a lower visual standard. Direct Python output can look correct while reopening or refreshing in Origin changes its formatting, so distinguish the verified appearance from native reopen/refresh persistence.

Use the latest accepted effect image as private task evidence, not a reusable skill asset. Retain its exact version in the task. This reference records its transferable design principles, not its scientific content, screenshot, identifier or hash.

## Contents

- [Shared target look](#shared-target-look)
- [Reuse stable defaults](#reuse-stable-defaults)
- [Understand and group the evidence](#understand-and-group-the-evidence)
- [Fast initial HTML suggestion](#fast-initial-html-suggestion)
- [Refine composition without distortion](#refine-composition-without-distortion)
- [Restore final fonts and geometry](#restore-final-fonts-and-geometry)
- [Resolve clear PNG or vector distortion](#resolve-clear-png-or-vector-distortion)
- [Typography and visible stroke scale](#typography-and-visible-stroke-scale)
- [Titles, panel letters and dense annotations](#titles-panel-letters-and-dense-annotations)
- [Axes, colors and scientific meaning](#axes-colors-and-scientific-meaning)
- [Proposal and acceptance](#proposal-and-acceptance)
- [Final complete-role audit](#final-complete-role-audit)

## Shared target look

The default accepted style is **compact scientific**: a white-background, publication-style multi-panel figure rather than a card dashboard.

- Use plain white, clear panel letters, restrained plot frames and the existing scientific palette. Avoid decorative cards, shadows, rounded containers and interface styling in the finished figure.
- Keep a coherent evidence sequence and purposeful unequal emphasis. A dominant overview with an inset may stay larger; related measurements can form matched columns with comparisons beneath. This is a useful pattern, not a compulsory grid.
- Align confirmed peers by actual plot-frame stroke edges, including lower comparison panels. Deliberately balance row tops, text baselines, panel letters and the visual extent of images; equal container widths alone do not establish alignment.
- Keep vertically related panels compact. Remove excess outer blank space before shrinking content. Retain room for tick labels, axis titles, conditions and legends instead of cropping them to shorten a column.
- Use one clean sans-serif family across comparable roles. Arial or an Arial-compatible face such as Liberation Sans suits this target when available. Check actual glyphs and metrics in each renderer rather than assuming matching names guarantee matching appearance.
- Preserve role hierarchy: axis titles modestly larger than ticks; conditions and legends comparable to readable tick text; panel letters bold and larger; dense references smaller but legible. An axis-title/tick visual-height ratio near 1.15–1.2 can be a starting sample for this accepted look, never a universal requirement.
- Keep titles close to their axes with small, consistently positive ink gaps. Keep conditions near their own plots and panel letters visually attached to their own panels.
- Match peer frame/tick weights at final scale while preserving meaningful curve hierarchy, markers, transparency and uncertainty bands. Do not make every stroke identical or make dense waveforms artificially thin.

Use final physical output size and readable scientific content to resolve tradeoffs. If one route cannot realize a detail safely, name the remaining detail and distinguish the last verified appearance from unfinished source work.

## Reuse stable defaults

Use these established aesthetics as defaults after the refinement reference-image question below is answered; do not reopen an unchanged reference choice or ask the user to select the established rules again. Reuse a recorded, verified version of the role hierarchy, unit conversions, anchor schema, guide construction and same-canvas comparison method when their assumptions and implementation have not changed. Keep reusable rules in the skill and source-specific measurements/evidence in the private task. Do not rerun a full implementation benchmark or rediscover palette definitions for every layout.

Revalidate a reusable method when its version, dependencies, rendering environment or relevant assumptions change, or when a result exposes a mismatch. Reuse does not carry over per-run source hashes, source type/capability classification, integrity checks, current plan/guide approval or actual result inspection. An unchanged method can be reused; a different source still needs correct bindings and a checked result.

## Understand and group the evidence

Inspect a clean full-slide render and native-resolution crops before packing objects. Inventory plots, photographs, micrographs, arrays, diagrams, ROI marks, native text, legends, captions, panel letters, insets and connectors. Record visible scientific units, not merely PowerPoint top-level shapes.

For each proposed panel, establish:

- Exact source members and representations: the image/plot plus required ROI, title, legend, condition text, panel label and other associated annotations.
- Its supported scientific role: overview or mechanism, measurement or characterization, performance, comparison or control, or application. Use the source and user context as evidence; record uncertainty rather than inventing a conclusion.
- Its links to other panels: shared specimen, measurement condition, category, statistical summary or demonstrated comparison. Group related curves and statistics using labels, legends, source bindings or explicit user explanation, not matching colors or proximity alone.
- Its density and required readable features: long axis titles, multiple curves, small uncertainty marks, micrograph scale bars, references, dense labels or a nested inset.

A native PPT group can contain multiple independently useful plots, and a scientific panel can span several groups. Preserve each separable plot's stable identity and common parent-panel association. Keep a micrograph with its necessary ROI/scale bar; do not detach it because another placement looks cleaner. Record cross-panel connectors separately by both endpoint owners; see [alignment-review.md](alignment-review.md).

Render each thumbnail from the complete bound scientific unit. A cropped child image is not a faithful preview of a composite panel. The draggable thumbnail and its rough box may stretch for composition, but that temporary display transform must not change original image aspect, crop, glyph shape or scientific geometry.

## Fast initial HTML suggestion

Default to a **local offline HTML** arrangement, with no deployment or upload of the scientific sources/thumbnails for layout. The normal return path is the user's screenshot; an exported layout file is optional, not required. When the user asks to work faster, make one useful coarse arrangement promptly rather than beginning a typography or source-editing pass.

1. Retain every identified scientific unit unless the user has confirmed a subset, directly or through a verified optional layout export. A busy screenshot, occluded panel or absent crop is not evidence of deletion. Preserve source text and measurement units too.
2. Use the available source-linked thumbnails. Group related curves with their statistical/comparison panels when the scientific association is supported. Leave uncertain memberships explicit rather than guessing a story.
3. Adjust only initial box positions, relative size, row/column relationships, emphasis and coarse gaps. Preserve the user's already expressed sequence or dominant result. Do not normalize fonts, recolor, thin lines, rewrite labels or alter axes at this stage.
4. Generate any static companion preview from the **same geometry, selected panel set, ordering and thumbnail assets** as that HTML proposal. Label it as an initial arrangement preview, not a finished scientific figure or a screenshot of a browser session that did not occur.
5. State briefly what is ready for review and invite the user to return a screenshot after arranging it. Read that screenshot as approximate position, grouping and emphasis; derive exact anchors from the original scientific source during refinement. Do not require JSON/export or precise spacing/dimensions just to continue.
6. Defer exact scientific proportions, semantic guides, final font sizes and line weights to refinement. Simple multi-selection, if supported by the current local template, is a coarse movement convenience; it neither establishes scientific membership nor grants permission to change source groups.

Use [web-layout.md](web-layout.md) for local interaction and optional export. Do not claim access to unsent local browser state; the returned screenshot is sufficient to begin a composition proposal when its relationships are clear. Reuse applicable tests for an unchanged template version rather than claiming a fresh browser session was tested. If actual browser execution is denied or unsupported, state that limit; a static same-geometry preview supports composition review but does not prove dragging or persistence. Do not bypass a denied test or describe the static preview as interactive.

## Refine composition without distortion

Preserve the user's composition direction and unequal emphasis; treat rough dimensions as intent rather than precision specifications. Choose proportions and spacing from the content and intended output size. Ask where a scientific association, omission or alignment priority is genuinely unresolved, and follow the material-specific rule below when stretching causes clear PNG/vector distortion.

Prefer the smallest useful changes in this order:

1. Translate complete semantic panels and redistribute unused whitespace.
2. Trim or reduce only non-scientific outer blank margins, preserving labels, scale bars, ROI context and deliberate insets.
3. Make small local annotation translations where needed for positive clearance.
4. Restore rough-stretch damage to final typography and scientific geometry as required below. Propose other supported plot-geometry changes or a limited scale adjustment only if earlier steps cannot provide readability. Use the material-specific rule below: adapt confirmed illustrative modeling/schematic objects automatically, preserve warned micrograph draft stretching, and ask for the remaining clear-distortion cases. A changed source crop or scientific aspect is not implied by rough-box stretching.

Use few purposeful alternatives if needed: a balanced set of peers, an overview followed by evidence, or a dominant result with compact supporting panels. Allocate area by scientific importance and information density, not solely by panel category. Do not enlarge an empty schematic while forcing a dense comparison plot into unreadable space.

Align naturally related rows and columns rather than imposing one grid on every object. A plot's frame, axis titles and label ink have different extents. Resolve their relationship using [alignment-review.md](alignment-review.md), not a global equal-width operation. Preserve deliberate insets and meaningful size differences.

If adapting a published reference, inspect the actual figure and retain its verified citation/link with the specific feature being adapted. A conventional scientific look is not evidence of a journal requirement or literature research. Never claim scientific support or fabricate a narrative from visual arrangement alone.

## Restore final fonts and geometry

**Rough dragging/stretching must never leave distorted fonts, axes or ticks in the final figure.** The screenshot records approximate layout, not the final rendering to reproduce literally. Restore normal glyph aspect and source-consistent text structure, axis/tick geometry, visible frame/line weights, and scientific image aspect before final delivery. Restore originally circular markers/icons that became elliptical from rough scaling; do not round intentional scientific ellipses or alter meaningful geometry. This restoration rule takes priority over retaining a stretched preview appearance.

Work from the intact original scientific/native objects or their faithful original representation, using the selected route's actually supported edits and a fresh render. A plot can be resized through supported geometry operations while preserving data-coordinate mappings, correctly positioned ticks, undistorted glyphs and compensated strokes. Do not merely stretch the entire picture, or flatten a deformed thumbnail/screenshot/cache into the final slide. If only an original undistorted raster is available, fit it uniformly and adjust the surrounding layout; do not invent missing source structure to repair it.

“Restore” means recover from real source information, not regenerate measured curves, infer data from pixels or fabricate a scientific redraw. If the required native/source operation is unsupported, retain the faithful source and explain the remaining layout limitation rather than claiming the distorted output is fixed. Verify restored fonts, axes, ticks, markers and strokes in the final full figure and detail crops, not only in nominal style values.

The micrograph draft exception below still applies: keep the stretched rough HTML box with a warning until refinement, then restore physical aspect and check the scale bar. Eligible schematic bodies may adapt proportionally, but their text and icons still need standard, legible proportions. A keep-deformation choice for other eligible artwork does not authorize final stretched typography, distorted axes or misrepresented scientific evidence.

## Resolve clear PNG or vector distortion

When stretching a PNG or vector object causes clear visible deformation, identify the object and its scientific role, then follow the appropriate rule below. A rough thumbnail stretch is composition intent only; it is not approval to distort scientific evidence. The rules below distinguish authorized automatic illustrative adaptation, other appearance choices, and protected measurement images.

**Confirmed non-measurement modeling illustrations and schematics:** adapt proportions to the layout automatically, without a per-object keep-versus-generate question. Preserve their established style, exact labels, components, connections and key meaning; adapt the illustrative body proportions needed for a coordinated fit while restoring standard text/icon proportions. Prefer a faithful minimal adaptation of the original objects when supported. Show the result in the complete refinement proposal rather than asking routine object-by-object questions.

“Model” is not proof that an object is decorative. Simulation field maps, physically dimensioned geometry, scale-marked structures and any model output whose shape or color encodes quantitative results remain scientific evidence. Preserve their meaningful geometry/scales, and resolve an uncertain classification before automatically adapting them.

**Other clearly distorted PNG/vector objects:** ask whether to retain the deformation or, where eligible, generate a proportional adaptation: “这张图拉伸后有明显形变。你想保留这个形变，还是调用生成能力，做一个保持原有风格、仅调整比例以适配布局的版本？” In this branch, generate only after the user chooses it. If they retain the deformation, record the eligible artwork-body decision in the current proposal instead of later correcting that body silently; final text, icons, axes and scientific geometry must still follow the restoration rule above. Do not offer generation for protected scientific evidence.

For any generative adaptation, use the required image-generation/editing tool under the current imagegen instructions; do not substitute an unsupported generation workflow. Keep the original style, subject, composition, palette, labels, components and relationships as far as possible; change proportions only as needed for a coordinated fit. Do not embellish, omit or invent content. Retain the original, create a separate candidate and inspect it against the source, especially text, arrows, counts, geometry and scientific semantics. Request correction or reject the candidate if those meanings changed. Do not promise pixel-identical content, exact style preservation or editable-vector output from a generated raster. Mark a generated schematic clearly as an adapted illustration, not original scientific data, and show it for review before final replacement.

**SEM, TEM, optical microscopy and other images with physically meaningful aspect are a distinct draft exception.** In the rough local HTML and returned screenshot, keep the user's stretched box by default rather than silently resetting it. Tell the user that the image has physical-aspect distortion and must be corrected later, for example: “这张显微图已经发生比例形变。我先保留你的排版，正式出图前需要恢复真实比例，并核对标尺。” This preserves composition intent, not permission to publish distorted measurement evidence. In the final scientific figure, restore the correct physical aspect from the original and keep the scale bar/calibration correct. Include that correction in the refined proposal; ask if the original aspect or calibration cannot be established. Never use generated content to “correct” a micrograph into supposed measurement data.

**Scientific evidence is never eligible for a generated substitute.** Do not generate replacements for data plots, micrographs, measured images or other measurement evidence. For other evidence-bearing objects with distortion, explain the boundary and offer uniform scaling, a faithful crop that preserves evidence/context, or a redraw from the actual original data where appropriate. A request to keep rough deformation cannot justify presenting misleading scientific geometry as an undistorted measurement in the final output. If the chosen appearance would change the interpretation, explain that problem and agree on a faithful alternative. Never use generated curves or textures to imitate the original measurements.

## Typography and visible stroke scale

Before fine stretching/refinement, ask whether the user has reference images unless they have already supplied them or answered this question for the unchanged task. If none, use the established aesthetics by default; if provided, inspect the actual references. Focus on spacing between individual panels, final visible glyph sizes, and the number and form of axes. Reuse the unchanged choice without asking again. Follow [style-options.md](style-options.md) to turn those observations into the proposal; a reference supplies separate role targets, not one number to copy everywhere.

Classify panel letters, panel/section titles, axis titles, ticks, conditions, legends, photograph captions, diagram/network labels, references and subordinate subscript/superscript runs. Include native PPT text and embedded text. Dense references can be smaller, but conditions should not be shrunk simply to escape a collision.

Measure final rendered glyphs and strokes after the entire transform chain: source/device coordinates, text and ancestor transforms, SVG viewBox, crop and picture extent, nested PPT group mappings, rotation/flips, host placement and rendering scale. Check nonuniform scaling, wrapping/autofit, font substitution and clipping. A nominal point size, Origin font integer or EMF `lfHeight` is not a final physical size.

Use matching glyphs or strings in the same face/weight for visual comparisons where possible; unrelated characters have different ink heights. Inspect axis titles, ticks, panel letters and dense subordinate runs at final publication/display size as well as in detailed crops. Recheck after geometry changes.

Preserve exact source text and run structure: case, punctuation, scientific symbols, italic variables, bold emphasis, number–unit spaces, and subscript/superscript contents and positioning. A user's spoken example identifies a label; it does not replace the source's measured value. Typography edits cannot simplify chemical formulas or flatten rich text without losing meaning.

Compare actual visible line thickness in both directions after transforms. Frame/tick peers should look compatible; data curves, uncertainty bands, markers and reference lines can retain distinct roles. Nonuniform transforms can change horizontal and vertical stroke thickness differently. Preserve alpha, dash patterns and marker/curve association, and do not redraw, smooth or fit data to recreate a style.

## Titles, panel letters and dense annotations

Keep axis titles close to their own axes while measuring the **ink-to-ink or ink-to-stroke gap**, including neighboring ticks and conditions. A text box includes padding; a baseline is not the bottom of its glyphs. Check rotated titles in their transformed orientation. Keep a visible positive gap at final viewing size without creating a large blank gutter.

Place every panel letter close to its **own** panel’s visible upper-left edge/plot frame, measuring actual glyph ink rather than the text-box corner. Reduce excessive horizontal separation by default; a letter must not sit near the midpoint between adjacent panels or seem to label both. Measure ink-to-owner and ink-to-neighbor clearances and inspect ownership at final viewing size; choose the smallest balanced positive gap that preserves labels/titles and clear association, not a fixed universal number. Same-row baselines and same-role size should be coherent, but never at the cost of belonging clearly to the intended panel. Retain case/bold hierarchy and do not invent a panel from an uncertain spoken letter.

For dense comparison labels, frequency/condition annotations and references:

- Translate minimally before considering smaller type. Inspect the whole run, including superscripts, descenders and adjacent characters.
- Keep positive clearance from all nearby boundaries: markers, error bars, plot borders, ROI edges and neighboring labels, not just the nearest one.
- Measure clearance to a rotated ellipse or slanted region against its transformed boundary, not only its axis-aligned bounding rectangle.
- Preserve label-to-marker/category association. Color alone is not proof of the association. Do not guess a target, move labels into another cluster, or add misleading leader lines.
- A separately proposed thin leader can help only when the correct attachment is known and the user accepts that annotation change. Keep it unobtrusive and off the data; do not cover collisions with opaque white patches.

## Axes, colors and scientific meaning

Keep data, ranges, tick positions/values, numeric labels, grids, fitting and smoothing unchanged during aesthetic layout. Each tick label remains mapped to its actual tick. Different-length strings naturally have different outer ink extents; do not shift numerical centers away from ticks to align those edges.

A reference's axis count/form is visual evidence, not permission to add/remove data axes, secondary axes, scales, ranges or ticks. Distinguish a frame/spine styling change from a change to scientific coordinate meaning; propose uncertain or consequential changes for explicit confirmation through a supported route. A rough suggestion of 3–4 numeric labels on an ordinary-sized axis is only an optional design proposal, not a target that justifies rewriting axes. Preserve current labels, including on drafts. Any separately requested suppression or axis change must specify the exact affected labels/values and use a supported scientific edit path; general layout approval does not cover it.

Keep source palettes by default. Use [style-options.md](style-options.md) only when a reference or color change is requested. Show each series/category-to-color mapping before applying it, preserve meaning across panels, and distinguish categorical colors from ordered sequential/diverging scales. A palette selection in the page expresses intent, not permission to globally replace every matching RGB value.

## Proposal and acceptance

Use [alignment-review.md](alignment-review.md) for the guide-first sequence, exact anchors and complete-plan confirmation. Coarse region rectangles and a same-geometry HTML preview are composition aids, not approval for exact frame/ink/baseline or scientific-source changes.

A requested isolated effect/guide proposal may be made in a separately named disposable copy within the requested appearance scope before final-source confirmation. Keep originals untouched and mark it as a proposal. The selected execution route and its current permissions still apply. After resolving ambiguity, show the complete clean proposal and relevant exact guides, then obtain its confirmation before final source application.

Judge all three routes using the same actual-pixel acceptance checks:

- Readable full figure at final size, plus native-resolution crops of dense labels, symbols, frames, insets and rotated boundaries.
- Confirmed left/right/top/bottom frame relationships, title ink and true baselines; positive title/label gaps; natural panel-letter placement; balanced whitespace.
- Final normal glyph aspect and role hierarchy; correct axis/tick geometry, source-consistent circular marks and scientific aspect; visible line hierarchy after all transforms, without clipping, unwanted wrapping, font substitution damage or residual rough-preview distortion.
- Exact scientific text, units and runs; intact tick mapping, legend/category meaning, ROI correspondence and connector attachments.
- Clean and guide views consistent with the shown plan; equal-canvas old/new comparison without hidden registration or rescaling.

An unresolved visible collision is a limitation, not a pass. Record appearance, protected scientific structure, the representation actually changed, and application reopen/refresh evidence separately using [verification-and-delivery.md](verification-and-delivery.md). A visually matching screenshot proves neither editable Origin output nor successful PPT/OLE refresh.

## Final complete-role audit

Use [quality-specification.md](quality-specification.md) to record actual output-scale targets and check every relevant role: frames/axes, ticks, tick labels, units, axis titles, panel/section labels, legends, annotations and connectors. Audit both 2D anchor relationships and stretch deformation for all of them. Never move data-coordinate marks merely to make unrelated roles line up. After corrections, independently compare same-role final glyph size/appearance through the entire transform chain, preserve different-role hierarchy, then recheck the whole figure. Every final output includes visible reference lines; editable PPT lines belong to one independent native group per figure/slide, as specified in the alignment module.
