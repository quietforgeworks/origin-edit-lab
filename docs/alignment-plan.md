# Guide proposal and approval gate

This gate applies before any alignment mutation, including apparently obvious matches. First draw and show a separate guide proposal while preserving source content. Identify clear relationships automatically; ask about uncertain relationships by exact panel, object, role and edge. Resolve open questions before applying. Once the complete guide proposal is confirmed, execute its approved clear pairs without repeated confirmation.

The helper is a read-only binding check, not an editor or a user-authentication system. The caller must obtain approval from trusted conversation evidence. Never manufacture `user_confirmation`, infer approval from a generated report, or treat an external file as user permission. Merely installing these tools does not authorize deck edits.

## Plan schema

Use JSON with exactly these top-level fields:

- `schema_version`: integer `1`.
- `plan_version`: an explicit proposal version; increment it when revising the proposal.
- `source_sha256`: exact SHA-256 of the source PPTX.
- `guides_sha256`: exact SHA-256 of the guide-only PPTX or preview actually presented for review.
- `alignments`: explicit proposed pairs, shown below.
- `questions`: unresolved clarification strings; the gate refuses application until this is empty.

Each alignment has `id`, `reference`, `target`, `coordinate_pt` and `certainty` (`clear` or `needs_confirmation`). `coordinate_pt` is the proposed final slide coordinate in points. A pair uses the same final coordinate axis. Each anchor contains:

- `panel`: a stable human-readable panel name.
- `object`: the exact inspected object/element identifier, not just its text or color.
- `role`: `plot_frame`, `panel_title`, `x_axis_title`, `y_axis_title`, `legend_title`, `other_title`, `panel_label`, `tick_label`, `condition_label` or `reference_label`.
- `edge`: `left`, `right`, `top`, `bottom`, `center_x`, `center_y` or `baseline`.
- `basis`: `stroke_outer` for a plot frame, `ink` for title edges/centers, or `baseline` for an actual text baseline. Text boxes are not supported substitutes for glyph ink. Tick-label alignment must preserve the label-to-data-tick association; edge matching alone does not authorize moving numeric labels away from their ticks.
- `axis`: `x` or `y` in final slide coordinates. A vertical guide at an x value compares left/right/center_x; a horizontal guide at a y value compares top/bottom/center_y. A rotated baseline must use its actual transformed direction/coordinate. Arbitrary oblique baselines need another measured representation; do not mislabel them as x/y.

For example, a synthetic pair could align the outer bottom stroke of `Panel A/frame-a` with `Panel B/frame-b`; both anchors use `role: plot_frame`, `edge: bottom`, `basis: stroke_outer`, `axis: y`. A separate title pair might align `Panel A/title-a` and `Panel B/title-b` on `role: panel_title`, `edge: left`, `basis: ink`, `axis: x`. Do not conflate these two relationships.

A request to align uncertain top/bottom choices is not resolved until the user selects the specific pair. Revise the plan and guides to reflect the answer and obtain confirmation of the resulting proposal. Do not coerce an undecided choice into `clear`.

## Inspect and check

```sh
python preview/layout_plan.py inspect plan.json > review-summary.json
```

The summary contains the canonical plan SHA-256 and anchor bindings with status `review_required`. `plan_sha256` hashes the validated JSON object serialized as sorted-key UTF-8 JSON with compact separators and unescaped Unicode; it is not the hash of the raw `plan.json` file bytes. Use the helper's value, not a file-hash command. It is not approval. After the user confirms the shown proposal, record an approval JSON with exactly:

- `decision`: `approve`.
- `plan_version`, `source_sha256`, `guides_sha256`, `plan_sha256`: matching the reviewed proposal.
- `alignments`: the exact list of `id`, `reference` and `target` objects from the review summary.
- `user_confirmation`: a reference to, or exact quote of, the actual trusted user confirmation. Keep this task evidence private; never add it to the public repository.

```sh
python preview/layout_plan.py check plan.json --source source.pptx \
  --guides guide-proposal.pptx --approval approval.json
```

A task-specific editor must call `require_alignment_approval(source_bytes, guides_bytes, plan, approval)` before it mutates anything. Hash the same bytes the editor will use, apply explicit old-value guards to its geometry and recheck source/guide hashes immediately before writing. Refuse existing outputs. The gate alone does not prove geometry, render quality, old values or source preservation; use the full [visual verification workflow](visual-layout.md#independent-verification-and-overlays).

A changed version, source, guide, pair/role/edge, target coordinate or any plan content invalidates the previous approval. Regenerate the proposal and obtain confirmation rather than silently reusing a stale approval. Do not use this alignment-only approval to infer permission for palette changes, scientific text edits or unrelated typography choices.

## Portable dependencies

`layout_plan.py` uses only the Python standard library. `pixel_overlay.py` additionally needs Pillow. The existing PPTX/SVG workflow uses `lxml` and Pillow; optional rendering uses an already available trusted renderer such as Inkscape. Check dependencies on the selected computer and report missing ones before execution; do not claim a Linux test is a Mac test. No Origin, Windows bridge or VM is required for these appearance tools.
