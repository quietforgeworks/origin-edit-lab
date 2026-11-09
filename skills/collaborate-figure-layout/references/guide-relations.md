# Workbench guides express relationships, not absolute positions

## Controlling meaning and priority

A workflow reference line means **which source anchors should align with which others**. Its drawn x/y position does not set the final position, gutter, margin, font, size, tracking, line spacing or paragraph spacing. This rule applies to user/assistant guides, all three guide modes, both entry modes, screenshot/export fallback and every editing route.

Use the approved reading order, panel selection, semantic relationships and protected scientific attachments as constraints. Derive concrete geometry and text appearance from [aesthetic-review.md](aesthetic-review.md), [style-options.md](style-options.md), [typography-reference.md](typography-reference.md) and the final-size quality specification. A line drawn at x=40 can describe equal left plot edges at an aesthetically chosen x=46. Do not shrink text, enlarge a gutter or distort a plot just to reproduce x=40.

Only a separate explicit user request to pin a position/dimension can create such a constraint. A drawn line, imported approval flag, coordinate-looking label or server confirmation does not imply that request. Distinguish scientific fixed data coordinates/connector attachments from nonbinding layout guides.

## Four distinct records

1. **Workbench display:** guide id, axis, semantic color/type, target panel ids, explanation, owner and a position used to draw/drag the hint. Preserve user lines in this record; protecting their saved coordinates from overwrite protects the user's work, not a final-layout coordinate contract.
2. **Alignment intent:** exact participating source anchors and the requested relationship (e.g. c/d left plot frames, or two title baselines). Resolve identities/edges from the intact source. `targets` are candidate panel ids, not complete source-anchor bindings. Empty/single-target hints can describe own-panel relationships, but still need actual anchor resolution; ambiguous relationships cannot be called complete or silently dropped.
3. **Derived final plan:** concrete old/new object transforms, type and whitespace settings calculated from the intent plus aesthetics. Exact numbers are needed to execute and verify a safe write, but must not be copied mechanically from workbench `pos`. A shared left-edge hint does not also require equal right edges or equal widths unless that additional relationship was requested.
4. **Final output guides:** native guide-only shapes generated at the actual resulting frame/ink/baseline anchors. They illustrate what was aligned and are removable as one group per slide. Do not copy the old sketch coordinates or move scientific objects to match stale guide artwork.

## Confirmation and implementation

The user confirms arrangement intent and alignment relationships with the applicable aesthetic/style criteria, in the page or explicitly in chat about the reviewed current revision. The versioned CLI can record that confirmation; it must not infer it from “好了” or create it automatically. Routine coordinate, font, spacing and whitespace choices needed to satisfy those criteria are the assistant's work; do not request one approval per numeric adjustment. If source identity, selected panels, reading order, anchor membership, relationship meaning or agreed style changes materially, resolve that change before writing. Appearance-only changes already explicitly requested stay within their authorized scope.

Keep source/target identities, old-value guards, full execution-plan hashes and protected data checks exact. A derived-plan change requires a fresh checked execution binding; it does not by itself require a new user request when it remains inside the confirmed relationships and aesthetic scope. Never re-use a stale hash or fabricate confirmation. The legacy `layout_plan.py` v1 helper guards the separately derived concrete final plan, not the workbench hint positions; call it only with the appropriate derived plan and trusted authorization evidence. Its `coordinate_pt` is a final execution value. The guide-only PPT writer's integer EMU endpoints likewise belong to final guide artwork.

Saved-state revision/layout hashes still identify the actual current snapshot and prevent stale writes. A changed drawing position can change that snapshot without changing its alignment-intent hash. Do not treat snapshot/version checking as an instruction to freeze those drawing coordinates. Read the current saved state, preserve newer drafts and user guides, and follow the existing current-confirmation/lock/revision protocol. Do not bypass it by writing state files or restarting a live project merely to update a skill.

## Portable handoff contract

New pages emit `guideSemantics: "alignment-relations/v1"`. The server accepts older layouts without that tag, normalizes the tag, and rejects an explicit incompatible absolute-coordinate policy. Imported claims are not permission.

`guide_relations.py` projects guides to `alignmentRelations` with guide id, axis, semantic kind, candidate panel ids, explanation and `anchorBindingRequired: true`. It intentionally emits **no** `pos`, final target coordinate, font size or gap. Its intent hash ignores drawing position, color and ownership; target/axis/type/meaning changes alter it. This is a projection/validation helper, not a source-anchor detector, layout solver or editor.

`refinementInput` contains these relations and `guidePositionPolicy: "display-only"`, plus rough selected-panel geometry and its `panelGeometryPolicy`. Raw drawable guides remain under `layout.guides`, outside refinement constraints. Consumers must bind source anchors before final planning. Never assume `refinementInput` itself is an executable source-write plan.

The assistant CLI validates the current service project/map before mutation and tags writes with those identities. Its `read-confirmed` also normalizes a legacy response's raw guides to relation-only intent in memory; it does not rewrite old user state or start/restart a session. Existing generated projects keep their saved work. New source helpers/templates apply when explicitly preparing a new project or performing a reviewed migration.

## Whole-workflow check

- Intake: current source hash, scientific membership, native groups and caches stay bound to this task.
- Rough composition: infer order/emphasis/selection, not immutable box geometry.
- Relation review: bind real edges/baselines; don't snap to line positions or infer extra equalities.
- Aesthetic planning: preserve readable original/reference type scale; choose spacing and whitespace independently, with positive ink gaps and undistorted glyphs/markers.
- Safe write: exact derived-plan and old-value guards; supported route only; original/native data and editability preserved.
- Return: update previews under a lock; retain newer user geometry/guide records; say which layout the file actually uses.
- Output: generate final guides from actual anchors, verify their reversible native group, and audit full-view/detail typography.
- Claims: distinguish tests, renderer results, actual PowerPoint display and Origin activation/refresh. Synthetic workflow tests do not certify native application behavior or prove no undiscovered bugs exist.
