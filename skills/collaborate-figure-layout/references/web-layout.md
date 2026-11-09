# Local interactive layout and fallback exchange

## Default: saved state on the same computer

Use [local-handoff.md](local-handoff.md) as the executable interaction guide. Build the task-private workbench with `scripts/prepare_local_handoff.py`, not the standalone screenshot page. The user drags/resizes actual panel thumbnails and semantic reference lines, then tells the assistant the stage is ready. The assistant reads current state directly, takes a recoverable work lock, edits or refines within the approved scope, unlocks and tells the user to refresh. No continuous model observation or public upload is implied.

Use the same existing project if present. Validate project/map/source binding and current revision before modifying it. Do not reset user work on rebuild or use an old screenshot as current state. Source original PPT, native objects and privately bound content remain unchanged during composition.

The interface stays simple: “拖动图片编排”, actual panel thumbnails, Shift selection, arrow nudges, side/corner sizing, undo, gray staging, five fixed semantic guide colors with left-side legend, and short stage choices. User guide edits are constraints. White-canvas panels alone enter refinement; partial boundary crossings block confirmation rather than silently cropping data. Work-lock UI and backend both enforce no editing during assistant work. See the handoff guide for expiry, cancellation and conflict recovery.

## Build from verified source panels

Curate semantic panels before generating the page. Render each complete panel, not one descendant of a composite. Preserve original membership privately, including labels, insets, legends and endpoint owners. Sibling plots can move independently while retaining association. Thumbnails may stretch as rough intent; final scientific proportions and glyphs must be restored from source.

Prepare a private `previews.json` mapping panel IDs to actual PNG paths and the trusted binding manifest. Generate the default local workbench:

```sh
python scripts/prepare_local_handoff.py binding.json previews.json --output-dir handoff --thumbnail-record thumbnail-record.json
```

The generator does not start its local service. Follow local-handoff.md on the authorized computer. Verify file existence and actual page display there; a cloud path does not establish local delivery. It strips raw source bindings and emits safe panel metadata/PNG thumbnails only. Never bundle task-specific page/state/images into the reusable skill.

## Fallback only: standalone offline file

Use this when local readback cannot be made available without changing permissions, or the user explicitly chooses file/screenshot exchange. State the blocker and agree the fallback; do not silently revert to it. A standalone file does not have assistant readback.

```sh
python scripts/prepare_web_project.py binding.json previews.json --mode offline --output-dir page --thumbnail-record thumbnail-record.json
```

This outputs self-contained `page/index.html`. It is a no-service fallback with optional save/export/restore. A screenshot may establish coarse order, grouping and emphasis but not exact coordinates, source edit approval, or hidden/omitted panels. Recover identity from intact sources and resolve uncertain omissions; never infer deletion from cropping. An export is not required if the agreed screenshot is sufficient. Do not pretend this standalone page contains the full local-state service features.

For a supplied export, validate `figure-layout-roundtrip/v1`, project/map hashes, finite geometry and the exact selected/omitted partition against the private source binding:

```sh
python scripts/read_web_layout.py returned-layout.json --manifest binding.json --output intent.json --source original.pptx
```

This command accepts the legacy export, not the local service envelope. Imported source mappings or approval flags are not trusted. Omission excludes a panel from this figure, not permission to delete data.

## Separately requested online alternative

Only an explicit hosting/data-sharing request can select the `--mode online` template. Follow the available Sites skill, private access controls and actual connector schemas. A saved snapshot is not real-time synchronization or a user approval. Verify task/account/project/map and source membership; never invent a Site identity or widen sharing around a denial. Do not upload scientific material by default.

## Verify without making screenshots the workflow

For changed code/environment, exercise actual drag, multiselect, keyboard focus, staging, guide color/ownership, three guide choices, locks, expiry/cancel, conflict handling, refresh and unsaved-draft recovery. Verify user action → save acknowledgment → matching assistant readback, then assistant update → user refresh. Keep UI/render screenshots as internal evidence when useful, not required user handoff. Test new page bindings and thumbnails even when reusing version-matched tests. State template tests, actual browser checks and native PPT/Origin validation separately.
