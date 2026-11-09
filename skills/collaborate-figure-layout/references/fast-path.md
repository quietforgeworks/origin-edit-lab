# Efficient decisions, reuse and verification

## Decision ownership

Apply current user instructions first, then compatible choices already made in the conversation, then this skill's defaults. Preserve the scientific/source invariants of the chosen operation. A helper's exact hash/old-value guard protects an execution; it does not require the user to choose coordinates or reconfirm the same intent.

| Situation | Next action |
|---|---|
| Mode, route, reference and alignment intent are already clear | Resume the current stage; do not repeat the questions |
| User says “好了” after dragging | Read current saved state and inspect changes; do not infer confirmation |
| User explicitly confirms the just-reviewed current arrangement/relationships in chat | Record that exact revision with `confirm --revision N`, then `read-confirmed`; do not make them repeat the same confirmation in a button |
| User requests a clear font/spacing/marker correction | Reuse established relationships and route, apply the new appearance scope, and verify affected objects and neighbors |
| New source, selection/order, relationship meaning or material aesthetic intent | Resolve the changed scope, preserving independent completed work |
| A derivation changes numerical positions inside agreed relationships/aesthetic criteria | Rebind the concrete execution plan; no per-coordinate user approval |
| User edited the workbench during private processing | Preserve the newer draft; update only compatible previews or reconcile the changed scope, never replace it from a stale snapshot |
| A particular conversion/editor operation fails | Try a supported faithful alternative within the chosen layer; otherwise name that facet's blocker and continue independent work |

Use one concise request for genuinely unresolved choices. Ask reference/style questions once; no reference means the source/established aesthetic baseline. Do not ask about routine dimensions, margins or font sizes that can be derived from the reference.

## One task record, selective reading

Keep a small private record with current source/hash, mode, route, selected panels and source objects, reference/style targets, confirmed relationships, current saved revision, planned operations and verification evidence. No universal giant form is required. The executable coverage schema retains its required object/facet entries, but may reference one shared valid evidence file rather than duplicate prose for every run.

The main entrypoint selects the stage; [operation-map.md](operation-map.md) selects the operation. Read detailed schemas only for the chosen helper. References have defined owners: guide semantics in `guide-relations.md`, visual design in `aesthetic-review.md`, typography in `typography-reference.md`, numerical verification in `quality-specification.md`, runtime handoff in `local-handoff.md`. Do not recursively reread every linked file on every turn.

## Reuse without staleness

Reuse verified inventories, faithful baselines, source bindings and unchanged render measurements when their source hashes, selected parts, renderer and output scale still match. Check changed source/version once before preparing a write and again where the writer requires it. Do not keep re-extracting or converting identical caches.

Inspect one full baseline and the fragile regions first. Batch independent object inspections and renders. Apply compatible changes in one source-bound plan; then check actual allowed differences. Repair a shared root cause once, followed by per-instance exceptions and whole-figure review.

After an edit, recheck changed objects, transform descendants, neighboring ink, shared resources and final full-view composition. Reuse unchanged applicable checks. Default to a planned correction pass plus a verification-driven pass; further iterations need a specific remaining defect or new user direction. Never stop merely to satisfy that efficiency budget while a required fix remains safely achievable.

Run tool regressions when implementation/schema/behavior changes, not for every new figure. Per-file content preservation and final rendering are still required. A previously tested renderer/helper is reusable evidence of that capability only, never proof of a new figure's appearance or native lifecycle.

## Keep handoff small

`assistant_layout.py read` and `read-confirmed` return layout, relationships, revision and preview hashes by default. Use `--include-previews` only when the PNG payload is actually needed; do not dump it into the conversation. New servers support summary reads; the CLI falls back to filtering a legacy full response.

Prepare immutable private candidates and visual evidence without holding a workbench lock. Acquire a lock for shared-state changes/publication, after checking current revision. Keep it short, renew when necessary, release in `finally`, and stop writes if the user cancels it. The lock is not a substitute for source/plan guards.

Deliver a short result with the actual file/page and relevant limitations. Keep test logs, source mappings and unsupported-route diagnostics private unless needed to explain a real blocker.
