---
name: collaborate-figure-layout
description: Collaborate on scientific figures in two modes, interactive rough layout from an early PowerPoint, or light refinement of an already arranged figure. Identify and preserve PNG, native PPT and Origin sources; provide a local offline draggable HTML or a quick assistant arrangement; recover rough composition from screenshots; apply shared scientific aesthetics and confirmed guides through Python edits, available Windows Origin MCP, or an explicitly authorized Mac VM command-line bridge. Use for the complete collaboration workflow, not a material library, universal Origin writer or automatic permission to start a bridge.
---

# Scientific figure collaboration and refinement

Use one workflow with distinct stages:

**Source PPT → identified scientific panels → draggable/assistant-proposed layout → confirmed aesthetic plan → selected editing route → verified requested output.**

The user provides this task's material in one PPT, sometimes as many small objects on one slide. Do not ask them to build an asset library, specify technical dimensions or operate a complete software product. Keep the original scientific files intact and all task evidence private. A rough layout, an effect preview and an edited scientific source are different deliverables.

## Three integrated layers

This workflow combines three layers; no stage is complete by making a classification alone:

1. **Default aesthetics and scientific exceptions:** choose semantic groups and measured final-size targets, restore unintended stretching, confirm exact guide relationships and pass the complete visual/font audit. Use the shared aesthetic/alignment/quality modules for both entry modes and all routes.
2. **File handling and executable code:** identify the real source layer, bind its unchanged input, use the actual supported tools/commands/dependencies, verify allowed changes, preserve revisions and roll back safely. An unsupported operation remains a precise blocker, not an assumed capability.
3. **Communication and collaboration:** infer already clear choices, ask only unresolved decisions, explain the actual edit layer and its consequences, show the complete guide proposal, keep progress truthful and deliver the requested artifact. Follow [collaboration-dialogue.md](references/collaboration-dialogue.md) at each handoff, not only at the end.

## Read the relevant module

- Inspect and bind sources: [source-preservation.md](references/source-preservation.md).
- Build/recover the small interactive page: [web-layout.md](references/web-layout.md). Read the available Sites skills only when using hosting/preview facilities.
- Use the optional labelled-box PPT exchange: [file-exchange.md](references/file-exchange.md), only when wanted or needed as an agreed fallback.
- Choose semantic layout and final visual style: [aesthetic-review.md](references/aesthetic-review.md), with [style-options.md](references/style-options.md) for reference/palette choices.
- Measure anchors, propose/confirm guides and preserve whole-slide relationships: [alignment-review.md](references/alignment-review.md).
- Select and authorize one of three editing routes: [refinement-routes.md](references/refinement-routes.md).
- Run the explicit **Python direct-edit workflow**: [code-editing.md](references/code-editing.md#python-direct-edit-workflow), with actual CLI commands and supported interfaces in the same module; bundled utilities are under `scripts/source_edit/`.
- Set measurable design targets and run the complete quality audit: [quality-specification.md](references/quality-specification.md).
- Add, inspect and restore one native guide group: [guide-tool.md](references/guide-tool.md).
- Verify and deliver the claimed result: [verification-and-delivery.md](references/verification-and-delivery.md).
- Assess supplied native-edit toolkits without generalizing fixed examples: [bounded-native-methods.md](references/bounded-native-methods.md).
- Reuse stable defaults efficiently without skipping per-file safety checks: [fast-path.md](references/fast-path.md).

Use the available presentation skill for actual PPT inspection/rendering. The installed `edit-origin-in-ppt` skill remains useful for its documented source boundaries; this skill includes a bounded copy of relevant proven utilities, not every capability of that separate skill or future versions.

## Choose the working mode at entry

Infer the mode when the user's request is clear; otherwise ask one short choice:

1. **互动式拉图：** start from material in a PPT, make the local draggable HTML, then recover the user's screenshot or provide an assistant arrangement. Follow stages 1–3 before refinement.
2. **已有版式轻微精修：** keep the almost-finished arrangement and automatically inspect alignment, role-based font/size consistency, spacing, titles, axes and obvious stretch distortion. Skip HTML and manual dragging. Go from source inspection directly to a minimal clean/guide proposal and refinement stages 4–7.

Mode 2 means automatic analysis/preparation, not bypassing guide confirmation or modifying unsupported raster content. Preserve the accepted composition, scientific labels/data and intended differences; avoid turning a small polish into a redesign. Ask for source PPT/Origin only when the supplied flat image cannot support the requested real edit and no matching source is already available. Never invent editable native objects from a screenshot. The same reference-image question, three execution-route choices, aesthetic target and verification rules apply to both modes; reuse applicable choices already given.

## 1. Resolve and preserve the source

Resolve the actual requested file and version. When the user names a desktop file, inspect that computer read-only; do not assume a cached upload is current. Reuse a cached copy only after its full hash matches. Do not move or overwrite originals. Record the source hash, slide order, media and embedded-object identities.

For a PPTX input, run:

```sh
python scripts/inspect_pptx.py original.pptx --output inventory.json
```

For an already arranged standalone PNG/figure image, preserve its bytes and inspect it directly; do not run a PPT parser or claim underlying editable objects. Bind any available matching source separately.

The PPT extractor is a candidate inventory, not a completed scientific grouping, OLE-stream inspection or visual-anchor audit. Inspect full-slide renders and detail crops. Bind actual slide/host IDs, XML paths, relationships, original transforms and part hashes. Nested OLE preview-picture IDs are representations, not independent scientific members; compatibility alternatives must not be guessed into one shape.

Curate scientific panels by meaning. Associate every intended image, plot, ROI, annotation, legend and panel letter with its source members. Native PPT groups need not equal scientific panels. Keep separable plots independently draggable, even under a shared printed letter, using stable child IDs and `parentPanelId`. Keep a necessary inset or image/ROI/legend together unless the source supports separating it. Track a connector's two endpoint owners independently.

Classify roles from evidence, such as schematic/overview, characterization, curves, statistics, controls, time/cycle response or literature comparison. Do not invent scientific claims from colors or a convenient category order. Ask about genuinely ambiguous identity, membership or attachment.

## 2. Make the rough composition useful immediately

For interactive mode only, at the first layout handoff, ask whether the user wants to drag or wants the assistant's suggestion, unless the latest instruction already answers that. Reuse an explicit current choice and follow later changes. This choice does not select or authorize the source-editing engine.

Use a minimal interface headed **拖动图片编排**: real thumbnails, direct drag, side/corner resizing, Shift-click multi-selection, arrow-key fine adjustment/group movement, selection/removal and undo. Shortcuts must not intercept editable controls; group moves retain relative geometry and respect the canvas boundary. Keep siblings independently movable while retaining common scientific association. Hide exact dimensions, ratios, margins, typography and grid controls. Do not add a material library or automatic-layout button; the user asks for automatic arrangements in chat.

Render thumbnails from complete source panels. A single descendant image cannot represent an entire composite. Keep display thumbnails/hash records separate from private scientific source bindings. The page must not contain raw PPT/Origin/OLE payloads, internal paths, credentials or approval evidence.

Temporary thumbnail stretching is permitted as coarse emphasis and composition, not final scientific geometry. For verified non-measurement modeling illustrations or schematics, adapt proportions to the layout without asking per object, preserving style, labels and scientific meaning; dimensional models/simulations are not automatically illustrative. For other PNG/vector objects with obvious distortion, ask whether to retain it or use generation to make a proportional adaptation matching the original style; do not decide silently. Generation requires that choice and cannot replace measured curves, micrographs or other scientific evidence. For those, explain the limitation and offer original-data layout, uniform scaling or faithful crop. For an authorized non-data schematic, preserve content/style as closely as possible and disclose that generation is not pixel-identical. For recognized SEM/TEM/optical micrographs, keep the stretched draft box by default but explicitly warn that physical proportions are distorted and need correction later. Do not silently correct the rough arrangement. Final scientific output must restore physical aspect and valid scale bars; generation cannot repair or replace evidence. For final output, restore correct font/glyph proportions, axes, ticks, line widths, circular symbols and scientific aspect from intact sources through supported edits and rendering. Never flatten a stretched draft thumbnail/cache into the final figure. Even an adapted schematic body retains undistorted labels/symbols; this does not permit inventing data. See the aesthetic module for this gate.

### When the user asks for a fast suggestion

Use the existing HTML framework. Select sensible relative positions and sizes from the actual content, retain all source units unless a subset has been confirmed, and keep related curves/statistics or images/ROIs associated. Change only rough initial geometry. Do not spend this stage on graph typography, line-width editing or Origin execution.

Write the recommendation into the interactive HTML so the user can adjust it, and provide a same-geometry static preview if useful. Identify it as a composition preview, not a browser screenshot or completed scientific refinement. Preserve old user work; use a new proposal identity/revision or a deliberate reset mechanism so saved browser state cannot silently replace the suggestion. If the source-bound manifest changes, recompute its binding hash rather than copying the old one.

### Default to a local offline HTML

Generate a self-contained local HTML, not a hosted website. **Do not upload the source, thumbnails or layout page, deploy a Site, or introduce an online connector by default.** Put the result only in the user's requested local workspace, preserving existing files. A static attachment preview is not an interactive page; explain how to open the local HTML in a browser. Follow the relevant desktop access rules rather than claiming an unverified local save.

The normal handoff is simple: the user drags the pictures, then sends a screenshot. Optional local save/export/restore is a recovery aid, not a prerequisite for collaboration. There is no automatic assistant access to local browser state. Online hosting or readback is an opt-in alternative only after a new explicit user request; see the web module's exact evidence/permission limits.

Test changed interaction when tools permit. If a browser tool explicitly rejects a protocol or access, stop that route rather than changing protocol/path to evade the denial. Distinguish static/function tests, browser tests and the user's actual machine behavior; report material limits accurately. Reuse version-matched prior template tests without rerunning the entire suite for every new layout.

## 3. Recover the screenshot's composition intent (interactive mode)

A returned screenshot is the default input. Match visible thumbnails/labels to the verified source and stable panel map. Recover relative order, grouping, width emphasis and approximate alignment, not final pixel coordinates. Read no unseen browser state. A cropped/occluded/absent panel is unresolved, not an instruction to omit or delete it. Ask the smallest question only when the ambiguity affects the proposal; continue independent work. Restore obscured labels only from verified full source previews.

Keep the screenshot and its source/version association private. Summarize the intended grouping briefly, then refine exact proportions, spacing and typography using the shared aesthetics. Do not require a JSON export when the screenshot sufficiently establishes intent. Only offer the optional saved-layout file if it would resolve missing selection or a genuinely ambiguous arrangement.

For an optional actual export, preserve the record and validate project ID, map hash, fixed canvas, source hashes and exact selected/omitted partition. Reject duplicate/unknown IDs, non-finite geometry, missing or stale source bindings. Resolve source membership from the trusted private manifest, not imported mappings/approval flags.

```sh
python scripts/read_web_layout.py returned-layout.json --manifest binding.json --output intent.json --source original.pptx
```

If authorized and supported, read a user-saved export from their connected computer using the expected filename/project; do not scan unrelated files or substitute developer test coordinates. Reading a saved file is not live synchronization. Omission is selection for this figure, not permission to delete source data.

## 4. Choose one execution route and one style template

Before refinement, offer these three choices, preserving the user's wording and explaining only the boundary relevant to this source:

1. **用 Python 直接修改（这种修改可能会导致 Origin 重新打开时格式改变）。** Identify whether the actual operation edits native PPT objects, an external preview/cache, or a separately supported source field. A cache-only edit can be replaced by Origin refresh; no general native Origin writer is promised.
2. **直接调用 Windows 中的 Origin 进行修改（Windows 电脑专用）。** Prefer the actual connected Origin MCP. Verify available tools, account/environment and supported operations; do not invent MCP tools or assume Origin is installed.
3. **调用虚拟机命令行桥接进行修改（Mac 专用）。** Use only the user's existing reviewed, available bridge and authorized Windows Origin environment. Choosing this route does not authorize new persistent access, broad commands or automatic restart of a stopped session.

Do not repeat an unchanged explicit route choice. Do not activate any route merely to offer it. Missing tools/permissions are a specific blocker, not permission to silently switch route or run paused development. All three routes share the same [aesthetic review](references/aesthetic-review.md), [alignment review](references/alignment-review.md) and verification criteria. Keep the accepted result's exact version/hash privately; never bundle its scientific image into this reusable skill.

Before refinement ask whether the user has reference images, unless they already supplied or declined them for this task. If none, use the established aesthetics; do not stall for a reference. Choose the style template separately:

- **Established aesthetics:** compact scientific layout, a clear role-based type hierarchy, visible-frame/ink/baseline alignment, title proximity, positive annotation gaps and preserved scientific meaning.
- **User reference figures/palette:** inspect supplied examples as style evidence, focusing on inter-panel gaps, visible font sizes, axis count and axis form; record their provenance and intended features, and resolve conflicting references or uncertain series-to-color mapping. Do not insert their scientific content as replacement data or claim to have researched papers that were not inspected. Axis count/style is a visual reference, not permission to add/remove a scientific axis, change ranges/ticks or hide necessary information; confirm uncertain semantic changes.

Keep every panel letter close to its own upper-left visible edge/plot frame, with clear ownership and no position near the neighboring panels’ midline. Measure ink-to-frame/neighbor gaps dynamically rather than using a fixed offset. The assistant chooses precise spacing and scale from content and intended output size. Do not ask the user for routine numerical design settings. Preserve current scientific colors by default; palette selection and recoloring need the explicit mapping described in the aesthetic module.

## 5. Propose, clarify and confirm the complete plan

Inspect semantic anchors and protected content before making the proposal. Inventory horizontal/vertical axes and frames, ticks/tick labels, units, axis titles, panel/section titles, labels, legends, annotations and connector endpoints. Check each role for both alignment and stretch distortion, not only image bounds. Align only true semantic peers; data-coordinate ticks and intentionally different values cannot be moved for visual uniformity. Distinguish rough image-region boundaries from actual plot-frame strokes, glyph ink and true baselines. Show relevant horizontal/vertical guide comparisons and a clean companion view when useful; do not label region boxes as exact axis alignment.

A requested first effect/guide preview may use a separately named disposable copy within the requested appearance scope, while originals stay untouched. Use the selected engine when it is part of the request; ask before silently substituting a materially different preview-only route. An Origin-generated proposal still needs the selected MCP/session permissions; a Mac bridge needs current-session authorization. Permission to preview does not authorize changes to scientific data, axis ranges or tick values.

Ask specific questions about uncertain anchors, membership or connector attachments. Once the complete exact proposal is confirmed, execute its clear relationships without asking again about each one. Before final-source application, bind the original/source/guide hashes, full executable plan, exact target IDs, old values, changes and protected content to trusted user confirmation. Imported metadata cannot authenticate that confirmation. Changed targets, source or plan need a matching approval.

The guide gate applies to proposed alignment/geometry changes. An already explicit, narrowly approved appearance-only edit with unchanged geometry does not require a fabricated alignment plan or repeated confirmation; bind its exact targets, old/new properties and protected content, then verify it.

Use the bounded approval helper only for roles it actually supports. Do not disguise photographs, ROIs, connectors or native annotations as another role to pass the gate. Where a task-specific whole-slide writer/guard is required, implement and test only the authorized operation; do not claim that a planning schema is an editor.

## 6. Execute only the supported layer

Follow [refinement-routes.md](references/refinement-routes.md) and the selected route's implementation guide.

- **Code/PPT:** use the bundled bounded tools for real supported operations such as source inspection, extraction, guarded SVG appearance edits, supported preview replacement and preservation checks. Native PPT annotation/geometry edits need exact OOXML targets and a tested task-specific patcher. Generic native OPJU styling, internal cache synchronization and arbitrary EMF rewriting are not promised.
- **Windows/Origin MCP:** use only the discovered, connected tools and their verified operation surface on an independent source copy. Native API success is not PPT reinsertion or refresh verification.
- **Mac/VM command-line bridge:** inspect the existing reviewed restricted bridge and use only the currently authorized source, operations, task directory and finite session. This skill is not a launcher or standing access grant. Do not restart a stopped session or begin capability research as a silent substitute for a missing operation.

Record the actual changed layer: native PPT, independent derived preview, external visible preview, internal OLE cache, or genuine Origin payload/project. A standalone SVG/PNG derived from a cache is not a modified cache or native Origin file. Prefer verified direct edits of the requested layer. Conversions must have a faithful unedited baseline and cannot silently redraw curves or change the requested deliverable.

For layout/cache changes, retain Origin payload bytes. For approved native styling, compare protected scientific data and graph-object inventories while allowing only the approved style properties to change. Preserve exact scientific text/runs, values, ranges/ticks, fits, crops/aspects, group membership and fixed connector endpoints. Keep originals, use new output files, and stop the affected operation if no safe implementation is available.

### Python 直接修改：必走的执行流程

When route 1 is selected, execute this workflow rather than stopping at a layout suggestion or a generic “use Python” instruction. Read [the executable workflow and commands](references/code-editing.md#python-direct-edit-workflow) before changing files.

1. **Inspect and freeze:** keep the original read-only, verify its hash and current version, for PPTX run `scripts/inspect_pptx.py` and `scripts/source_edit/pptx_origin.py inspect`, and bind exact slide/host IDs, relationships, payloads and current previews. Inventory is not scientific membership verification. For a standalone figure image, inspect its actual format/bytes instead; do not run a PPT parser or invent editable graph objects.
2. **Choose the actual edit layer:** distinguish PPT host placement from the plot's internal axes/page, native PPT text/shapes from embedded graphics, and external preview from internal OLE cache/native Origin payload. Do not resize only a host box and call its stretched fonts/axes refined.
3. **Prepare a faithful baseline and approved plan:** extract current representations, render the untouched baseline and inspect conversion fidelity if any conversion is needed. Apply the common aesthetic/reference rules. Show and confirm semantic guides before geometry changes; bind exact source/plan/targets/old values. Explicitly approved appearance-only edits need no fabricated alignment plan.
4. **Modify only supported properties:** use `svg_edit.py edit` for hash-bound SVG appearance changes. For native PPT geometry/text/lines, create and test a narrow exact-OOXML patcher with the complete approval/old-value guard; the package API is not itself that guard. No general native PPT layout writer, OPJU writer, internal OlePres editor or arbitrary EMF patcher is bundled. Stop unsupported operations rather than substituting a flattened picture or starting native development.
5. **Choose preview versus actual PPT write:** an independent SVG/PNG is a preview only. When external-PPT-preview replacement is approved, use `pptx_origin.py replace` with the inspected target and matching PNG/optional SVG, preserving OLE payloads and protected shared media. Check any supported VML/Fallback pair. State that Origin refresh may restore the old appearance; changing a cache is not changing Origin graph data.
6. **Verify before delivery:** run `pptx_origin.py verify` and inspect its report rather than treating it as a boolean pass. Independently compare the allowed parts/fields, protected data/text/geometry, source hash, shared objects and every active/fallback representation. Render and inspect final fonts, axes, ticks, proportions and exact confirmed alignments. Report PowerPoint/Origin/refresh checks separately.
7. **Deliver the requested layer:** provide only the requested new PPT or effect image, with a concise exact-change summary and compatibility limitations. Do not describe a preview, unchanged copy or unverified source as a finished native edit.
8. **Roll back without losing the original:** preserve the immutable original and candidate revisions. If validation fails, do not promote the candidate; retain it privately for diagnosis and continue from the original or last verified revision with a new output name. Do not “undo” native saves with guessed inverse byte patches or overwrite the original to restore it.

## 7. Verify what was actually achieved

Use [verification-and-delivery.md](references/verification-and-delivery.md). Independently inspect structure/content, rendered appearance and application behavior as separate evidence. Confirm protected parts and exact allowed changes; inspect full figures and detail crops at final viewing size. Verify fallback media as well as the primary preview. Complete a separate final font-size audit at actual output size after every object/group/text transform: compare same-role rendered glyph heights and visual size, not only nominal points. Preserve intentional role hierarchy and scientific text/runs, correct failures, then inspect the full figure again. Use the quality specification’s complete role/alignment/distortion checklist.

Do not equate parser success, a matching screenshot or a zero exit code with native editability, correct PowerPoint display or refresh-safe Origin integration. Record actual PowerPoint inspection, Origin cold reopen/save and OLE activation/refresh separately, with **not run** for missing evidence.

**Every final figure must include alignment reference lines.** In an editable PPT, put all reference lines for that figure/slide in one independent native group behind scientific content, clearly separate from data curves. Verify its membership and that hiding/removing it does not alter any scientific object; the guide removal/restore test must recover the clean content. PowerPoint cannot group across slides, so use one group per final figure/slide. A static screenshot must visibly include the reference lines; explain that a raster cannot independently hide/select them. Do not silently omit guides or substitute only a clean image. A clean companion can be additional, not the sole final deliverable.

Deliver only the requested format. A screenshot-first request gets the verified guided effect image, not an unsolicited PPT. Deliver editable PPT/Origin outputs only when they exist and their verification boundary is clear. State remaining visible problems or unsupported steps without calling the whole task finished. Keep private sources, binding records, session details, credentials and conversation evidence out of reusable resources and unrequested sharing.
