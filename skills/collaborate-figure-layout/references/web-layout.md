# Lightweight direct-interaction layout

## One small interaction surface

Show only this task's real scientific thumbnails on a canvas headed “拖动图片编排”. Let the user drag, pull a side wider, resize from a corner, remove an unselected element and undo. Keep sibling plots independently draggable while retaining their common `parentPanelId`. Do not expose a material library, source upload manager, automatic-layout button, numerical dimensions, ratios, gap values or typography controls. The assistant handles arrangement requests in chat.

Default to a self-contained local offline HTML. Give screenshot-first instructions, Shift-click multi-selection, arrow-key adjustment, bounded group drag and undo. Keep optional local layout save/export and drop-in recovery simple; they are not required for screenshot feedback. Keyboard shortcuts must leave editable controls alone. Only for a newly requested online alternative, keep its surface to title, pictures and a small truthful save status. Restoring a layout file is not a scientific-asset uploader. Never label an offline export as a message sent to the assistant.

A preview may stretch while the user drags its rough box. Export that geometry as composition intent only. Preserve original source/crop/aspect outside the page; restore appropriate scientific proportions and readable text during refinement.

## Prepare a task, not a reusable asset library

Curate semantic panels from the PPT before building the page. Render each complete panel from real source objects to a PNG thumbnail; do not use a single child image for a composite. Retain original source bindings privately. Keep `projectId`, stable panel IDs and `mapHash` bound to the private manifest; do not append to its hashed core while retaining an old hash.

`assets/web-layout/` is a generic template with no user figures, labels, source files, saved state or deployment identity. `online/` contains the optional private Site backend template. The scripts do not publish a site, start a bridge or modify scientific sources.

Prepare a private task-local `previews.json` mapping each panel ID to its actual PNG path. Use the same binding manifest as the optional box-PPT helper; that helper's draft PPT need not be delivered in browser mode.

For the default local offline page:

```sh
python scripts/prepare_web_project.py binding.json previews.json --mode offline --output-dir page --thumbnail-record thumbnail-record.json
```

This writes a self-contained `page/index.html`; save that file locally in the user's requested workspace, not its auxiliary inputs. Do not upload the page, scientific previews or sources by default. Verify the file actually exists on the requested computer; a cloud path is not a completed Mac/Windows save. It embeds display thumbnails and escapes task text for safe HTML inclusion. There is no network connection or automatic assistant readback. A blocked local-storage API must not prevent interaction/export.

Only after an explicit request to use hosting and the necessary authorized data-sharing scope, prepare a private online alternative:

```sh
python scripts/prepare_web_project.py binding.json previews.json --mode online --output-dir site --thumbnail-record thumbnail-record.json
```

This is not the default and must not be activated merely because a connector exists. Follow `$orbit:sites` and the available Sites implementation skill. Use the same verified task Site when one exists; otherwise register a real Site and its returned identity. Follow the generated template's build/readme interface. Never invent a Site ID or reuse a test identity. Keep actual hosting owner-private and verify access before sharing. Do not work around an access denial by widening sharing. Deliver a private online link only when its real interactive page works; otherwise state the blocker and offer the offline exchange.

If a previously bound group is deliberately split into independent plots, the helper accepts `--migration-file` for an explicitly inspected old-map-to-new-child mapping. Use it only after checking both private bindings and exact source membership. It carries old selection/omission to known children and divides only rough display boxes; it does not approve the new refinement geometry. Do not infer mappings from labels or filenames, and never invent migration state for a screenshot-only handoff.

The helper emits only view-safe project metadata, stable IDs, labels, rough bounds, parent-panel association and thumbnails. It strips `sourceBindings`/`sourceAssetIds` from the page. The thumbnail record retains hashes and source associations **outside** the output. Do not put original PPT/Origin/OLE files, internal paths, credentials, confirmation evidence or the binding manifest in either hosted output or this skill.

## Receive the screenshot first

The user's normal return is a screenshot. Identify its panel thumbnails/labels against the private source map; recover relative grouping, order, emphasis and approximate placement. Do not convert screenshot pixels into exact final positions or assume omitted/hidden panels were deleted. Ask only when uncertain identity, selection or grouping materially changes the proposal. A clear screenshot is sufficient to proceed to semantic guide/appearance proposal; do not demand JSON for convenience.

The local page has no network synchronization. Preserve the screenshot privately and distinguish it from a saved layout record. Optional file export/restore is a recovery feature. If useful, accept an exported layout or read the exact user-saved file from an authorized connected computer after the user says it was saved. Use the expected project-specific filename, not unrelated downloads or agent-generated test records.

## Optional official connector or saved-state exchange

Only when an online workflow is explicitly requested, prefer a relevant official read-only connector over browser scraping where it supports the task. Discover and use its actual schema: a connector may take no parameters and expose one fixed project. Verify returned project ID, map hash and envelope/layout consistency, canvas, revision/time and panel IDs. Preserve the actual structured response privately. Before source geometry is applied, require a trusted manifest linking that **exact** project/map to the source file hash and object memberships. Missing/mismatched source bindings block application; do not associate projects by label, filename or similar images.

Read access proves only that a saved snapshot is retrievable. A revision, timestamp, `browser-layout` field or stored approval flag does not prove a user manipulated the page, can reach it, or approved source editing. Do not invent actor/save-event history. Never claim live synchronization from a fixed snapshot. An official connector's read permission does not authorize writes, deployment, an Origin session or broader access.

## Validate actual saved state when supplied

Online saving must be verified for the actual task/account: user operation → server acknowledgment → assistant tool-side read of the matching project, map hash and revision. A reachable empty database, a local developer fixture or a successful build is not that evidence. Do not call it direct readback until this loop has worked. Read the latest real saved revision when the user says they are done; do not assume a screenshot is current server state.

The online backend uses revision-checked writes and authenticated owner isolation. A stale revision or changed project binding is a conflict to resolve, not permission to overwrite server state. Browser-provided source mappings, identity headers or approval flags are never trusted. A server acknowledgment means saved, not scientifically approved.

Offline HTML/local browser state is not automatically visible to the assistant. If a saved-layout file is actually needed, ask for the optional export; do not require hand-editing JSON or make it a condition when the screenshot suffices. Local restore aids the user, not assistant access. Treat screenshots as coarse composition evidence when sufficient, leaving absent panels unresolved rather than inferring deletion.

The export uses `schema: "figure-layout-roundtrip/v1"`, unchanged `projectId` and `mapHash`, fixed `canvas: {width,height,unit:"mm"}`, `selectedPanels: [{id,bounds:{x,y,w,h},text?}]` and `omittedPanelIds`. Every original ID belongs to exactly one selected/omitted set. Reject duplicate or unknown IDs, stale bindings and non-finite or malformed geometry. Derive source membership and parent-panel association from the trusted manifest, never an imported override.

Validate a received export or a preserved real server layout record:

```sh
python scripts/read_web_layout.py returned-layout.json --manifest binding.json --output intent.json --source original.pptx
```

The helper records the raw layout hash, validates the binding/selection and rechecks supplied original hashes. It does not authenticate user approval or edit scientific sources. Resolve missing source verification, out-of-canvas content or empty selection before applying source edits. Treat omission as selection for this figure, not permission to delete scientific data.

## Check before delivery

When template behavior/version or relevant environment changes, test actual single/group drag, Shift selection, arrow-key nudging, editable-control focus, boundary protection, side widening, corner resize, removal/undo, optional export and drop-in restore on the delivered surface. Reuse unchanged version-matched template test evidence on later tasks, but check each new page's bindings, thumbnails, no-network configuration and composition. Verify an exported layout with the exact private binding and original hashes. Test different-project/mapHash refusal, unsafe IDs, malformed coordinates and untrusted text. Check that sibling plots move independently while the source association survives roundtrip. A static preview is not an interactive test.

Distinguish template/local tests from production access, real-user save/readback, and native-source refinement. Keep current test evidence in task notes, not hard-coded claims in the skill. After recovery, ask the refinement execution-route choice and apply the shared aesthetic/guide-first workflow in the main skill.
