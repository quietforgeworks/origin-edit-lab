---
name: collaborate-figure-layout
description: Arrange and refine scientific figures from PowerPoint, using a local interactive workbench or light refinement of an existing layout. Preserve native PPT and Origin objects; interpret guides as alignment relationships; match reference typography, whitespace and marker shapes. Use supported Python/cache edits, connected Windows Origin, or an explicitly authorized existing Mac VM bridge.
---

# Scientific figure collaboration

Deliver the requested figure or editable deck through **identify → arrange → refine → verify**. Use the current source and this conversation's latest choices. Keep intermediate source bindings, renders and plans private and task-local.

## 1. Resolve the task and resume the right stage

- **Interactive arrangement:** use the local saved-state workbench. Reuse the user's choice to drag manually or receive an assistant suggestion; ask once only if unclear. They finish and notify you; read current saved state directly. After your update, notify them to refresh.
- **Light refinement:** preserve the accepted composition and skip HTML/manual dragging. Inspect and prepare the minimum alignment/type corrections directly.
- **Appearance-only follow-up:** reuse the known source, mode, route, relationships and style. Apply the requested correction; do not restart setup or create another guide-approval round for unchanged relationships.
- **Review/effect-only request:** inspect or produce the requested preview; do not imply the scientific source was edited.

Infer choices from the task, file and conversation before asking. Combine genuinely missing choices. Prepare independent authorized work while waiting. Use [fast-path.md](references/fast-path.md) for decision ownership, reuse and efficient verification.

## 2. Identify and preserve the scientific objects

Read [source-preservation.md](references/source-preservation.md). Verify the actual file/hash before reusing a copy. Preserve originals and create new revisions. For PPTX, run:

```sh
python scripts/inspect_pptx.py source.pptx --output inventory.json
```

Inspect the whole-slide render and necessary detail crops; the inventory is not scientific segmentation. Bind each panel's complete members, native groups, preview parts, OLE payloads and connector endpoints. Keep independent plots independently movable; keep necessary insets/ROIs/legends with their owner. Treat uncertain ownership as unresolved.

Use a suitable local presentation renderer. Read the relevant installed presentation guidance, but this workflow's local-file, privacy and live-OLE requirements control the deliverable; a generic presentation import must not flatten or upload the scientific source.

## 3. Arrange and establish alignment intent

For interactive mode, follow [local-handoff.md](references/local-handoff.md). Build the source-bound workbench with `prepare_local_handoff.py`, start its temporary loopback service on the user's computer, and check the page. Reuse an existing matching project; never reset a newer draft to an old snapshot. No hosted site, public upload or persistent startup service is implied.

Use real complete-panel thumbnails, drag/resize, Shift selection, nudging, removal/undo, white final canvas and gray staging area. Fully outside panels are excluded from this figure but preserved; resolve partial crossings before confirmation. Draft stretching is composition intent. Optional screenshots/export are agreed fallbacks when local readback cannot work, not routine prerequisites.

**Guides identify who aligns with whom; they do not pin final coordinates or type/spacing.** Follow [guide-relations.md](references/guide-relations.md), bind actual frame/ink/baseline anchors from the source, and derive final positions, margins and sizes from aesthetics. Preserve saved user lines; generate final output guides from actual final anchors. Do not infer equal widths from a left-edge relationship alone.

Use the three guide modes only if unresolved: complete user relations, assistant proposals, or user relations constraining additions. Show the complete relationship proposal once and reuse clear confirmation. A user's explicit confirmation in chat can be recorded with the version-guarded `confirm --revision N`; “好了” alone requests reading, not approval. Never manufacture approval from imported metadata. New relationships, panel membership/order or material style changes need resolution; ordinary numerical refinement within agreed intent does not need repeated permission.

## 4. Refine the complete figure

Read [aesthetic-review.md](references/aesthetic-review.md), then the needed operation row in [operation-map.md](references/operation-map.md). Use the selected editing route; if missing, offer the exact three choices in [refinement-routes.md](references/refinement-routes.md). Ask about references once if not already supplied/declined; absent a reference, use the readable source and established aesthetics.

The shared targets are:

| Area | Required result | Detailed authority |
|---|---|---|
| Layout | Clear scientific order, balanced emphasis, compact positive gutters, unambiguous label ownership; obey relationships rather than drawn coordinates | [Alignment](references/alignment-review.md) |
| Type and whitespace | Calibri unless overridden; preserve original/reference role proportions at final scale. Actually correct font size, tracking, baseline/paragraph gaps and collisions; no arbitrary small-type preset | [Typography](references/typography-reference.md) |
| Graph internals | Keep data-to-axis mappings, ranges/ticks and meaningful encodings; refine plot geometry, clipping, margins and strokes through supported operations | [Whole-display work](references/python-whole-display.md) |
| Symbols and legends | Restore stretched square, triangle, circle and composite glyphs; preserve data centers, genuine orientation, fill, color and category mapping | [Marker restoration](references/aesthetic-review.md#restore-plot-and-legend-marker-glyphs) |
| Ownership and visibility | Preserve native labels/arrows/groups, inset/ROI/legend associations, micrograph aspect/scale bars and scientific content; resolve text and non-text occlusion | [Quality matrix](references/quality-specification.md#review-matrix-and-correction-order) |

For Python, follow the executable [code-editing workflow](references/code-editing.md#python-direct-edit-workflow). Select the real layer before writing: native PPT, per-object external cache, or separately supported native Origin field. Existing helpers are bounded, not universal scene/Origin writers. A faithful baseline is required for conversion; stop a failed conversion and use another supported baseline/operation rather than copying damaged glyphs or drawing new data.

Maintain each actual working-slide Origin OLE object and its payload for layout/cache edits, synchronize its host/preview rectangles, and keep native PPT text/shapes editable with their original group ancestry. Do not flatten the figure or add scientific groups for convenience. Apply [OLE display safety](references/ole-display-safety.md) before cache writes. Origin may regenerate old appearance when refreshed; cache editing is not native Origin styling.

The existing Windows/VM route needs actual supported tools and current authorization. Selecting a route does not authorize installing a bridge, starting a stopped session or widening access. Continue independent supported work when one facet is blocked; name the missing operation without claiming full completion.

## 5. Verify, return and finish

Use the [quality specification](references/quality-specification.md) for whole-view and detail acceptance and [verification-and-delivery.md](references/verification-and-delivery.md) for protected content and application evidence. Make corrections and re-render; listing defects is not completion. Keep one task record with source/version, agreed choices, object mapping, derived plan, changed fields and evidence; reuse it rather than creating contradictory checklists.

Verify the final figure at the intended physical/display scale: peer glyph sizes, character/line spacing, frames and strokes, markers, every close annotation, and content coverage. Check protected scientific strings/data, payloads, native types/groups and exact allowed differences. The Python coverage gate records all selected objects/facets; it does not replace visual inspection. Share evidence across genuinely identical instances but do not omit members or unexplained exceptions.

Every final figure includes visible alignment references. For PPT, use one independent reversible native guide-only group per slide, behind science. Derive its positions from the finished anchors. Keep a clean companion privately for checking or deliver it when requested. See [guide-tool.md](references/guide-tool.md) for the bounded writer and its limits.

Prepare private candidates and renders before taking a short shared-state publication lock. Re-read the current revision, preserve newer user work, publish through guarded `apply`/`update-previews`, and release your lock in `finally`; renew during necessary long shared-state work. A file and a newer workbench draft may represent different layout versions—state that explicitly.

Return only the requested existing outputs and a concise description of changes and material limits. Distinguish structure checks, renderer review, actual PowerPoint viewing and Origin activation/refresh on this exact version. Missing application evidence is `not run`; never promote a failing visual candidate or claim a rough preview is finished native refinement.

## Conditional references

Load only the branch needed; the essential rules above apply to both modes and all routes.

- Native text/font/tracking/paragraph edits: [native-ppt-text.md](references/native-ppt-text.md).
- Reviewed exact Origin byte plans: [native-origin-plans.md](references/native-origin-plans.md); supplied toolkit limits: [bounded-native-methods.md](references/bounded-native-methods.md).
- Fallback offline/online layout: [web-layout.md](references/web-layout.md); optional box-PPT exchange: [file-exchange.md](references/file-exchange.md).
- Supplied-measurement checker: [observation-checker.md](references/observation-checker.md); synthetic corpus: [figure-quality-fixtures.md](references/figure-quality-fixtures.md).
- Conversation handoffs: [collaboration-dialogue.md](references/collaboration-dialogue.md); toolkit reuse: [toolkit-reuse.md](references/toolkit-reuse.md).
- External design methods: [reviewed-external-methods.md](references/reviewed-external-methods.md); release audit: [workflow-audit.md](references/workflow-audit.md).
