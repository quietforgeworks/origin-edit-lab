# Three execution routes, one visual target

Use the shared aesthetic/alignment criteria. Read [code-editing.md](code-editing.md) only for the Python route and the native sections below only for the selected native route; final checks are in [verification-and-delivery.md](verification-and-delivery.md). Established rules versus user references is a **style choice**; Python, Windows MCP and Mac VM bridge are **execution choices**. All three must meet the same confirmed visual plan and final-size acceptance criteria. Do not lower the visual target because a route is easier.

After the rough arrangement is understood, or immediately before an existing figure’s light refinement, offer:

1. **用 Python 直接修改（这种修改可能会导致 Origin 重新打开时格式改变）。** Explain the exact edited layer, including the risk that an OLE refresh restores an unchanged Origin preview.
2. **直接调用 Windows 中的 Origin 进行修改（Windows 电脑专用）。** Prefer the actual connected Origin MCP and its verified supported tools.
3. **调用虚拟机命令行桥接形式进行修改（Mac 专用）。** Use an available, reviewed bridge to real Windows Origin only within current authorization.

Do not ask again if the unchanged task already has a choice. Verify the actual computer, tool availability, source format and supported operations before promising execution. A filename, installed skill or attachment describing MCP/bridge software does not prove connectivity or permission. Identify an exact missing capability and ask before materially changing route or deliverable.

This reference provides selection and verification, not an MCP installer, bridge launcher, universal writer or PPT synchronizer. Installing/updating this skill does not authorize starting a stopped bridge, installing/running unrecognized software, expanding persistent access, changing security settings or resuming paused native development. Follow current tool-specific and confirmation requirements; do not preserve permissions as reusable skill defaults.

## Contents

- [Shared application gate](#shared-application-gate)
- [1. Python direct edits in the PPT package](#1-python-direct-edits-in-the-ppt-package)
- [2. Windows native Origin through MCP](#2-windows-native-origin-through-mcp)
- [3. Mac VM command-line file bridge to real Origin](#3-mac-vm-command-line-file-bridge-to-real-origin)
- [Native edit and return checks for both Origin routes](#native-edit-and-return-checks-for-both-origin-routes)
- [Verification and delivery](#verification-and-delivery)

## Shared application gate

Keep originals read-only. Bind the current PPT, source payload, preview, panel membership, actual screenshot/saved arrangement or existing-figure evidence, complete plan and shown guides to verified hashes and stable IDs. Require the matching user confirmation, expected old values and explicit changes before applying the plan to final output. Imported approval strings and old requests are not authorization; changed inputs/targets/plans require matching confirmation.

For an explicitly requested first effect image, prepare a separately named disposable proposal copy within the requested appearance scope; retain all originals unchanged. Its creation is not approval to finalize or write back source objects. Use the selected engine when that is part of the request, and ask before substituting a materially different preview-only route. An Origin-generated proposal still requires the selected tool/session permissions; the Mac bridge additionally requires current-session execution approval below. Changes to scientific data, axis ranges or tick values are never implied by permission to preview.

For explicitly approved appearance-only edits with no alignment/geometry change, bind the exact styling operation without inventing a new alignment proposal. Confirm new alignment relationships or material composition changes first; ordinary derived positions and spacing within the current confirmed aesthetic scope do not require per-coordinate approval.

Use `aesthetic-review.md` for the shared visual checklist, rather than route-specific style defaults. Preserve datasets, missing-value positions, curve bindings, axis ranges, ticks, fits and smoothing unless separately requested and supported. Preserve exact scientific text/runs, semantic groups, image aspect/crop and fixed connector endpoints. Never redraw or fit curves to imitate the desired appearance.

## 1. Python direct edits in the PPT package

Classify the target before choosing a writer:

- **Native PowerPoint objects:** supported OOXML geometry/text/style changes need a tested, old-value-guarded plan preserving transforms, rich text, relationships and scientific membership. Native Office charts have their own chart/workbook model; they are not Origin objects.
- **External picture/OLE preview:** update the approved active media and required display alternatives, cloning shared media/relationships when necessary. Keep SVG/PNG and supported Choice/Fallback pairs consistent. This changes appearance, not embedded Origin content.
- **Internal OLE presentation cache:** OlePres streams are separate from external slide media and native Origin content. An external-preview helper does not synchronize them. Editing them needs a separately verified implementation and approval for that target.
- **Actual Origin content:** identify the genuine payload/stream and format. A narrow source-preserving patch is usable only for its verified fields and bound source, with old-value/offset/length/checksum guards and unknown-byte preservation. Never replace an example plan's hash or reuse its offsets to force a new figure through. A reader or data-only writer is not a source-preserving graph writer.

The bundled stable `scripts/source_edit/` preview utilities (see `code-editing.md`) do not edit Origin data or internal caches. Separately reviewed native patchers can have narrow restrictions, such as same-length changes in a particular FAT `Contents` stream, while explicitly leaving previews unchanged. Check those restrictions and independent Origin evidence; do not infer universal support from a filename or successful parse. See [bounded-native-methods.md](bounded-native-methods.md) for audited fixed-source methodology and evidence limits.

### Cache editing risks

Prefer an inspectable original-format edit when supported. EMF/WMF can contain nested EMFs, EMF+ content and compatibility branches. Bind every relevant representation; do not patch one and leave another stale. An extracted original EMF is not a newly converted SVG.

For record-level patches, trace reused handles, object selection, drawing-state save/restore and transforms. Font changes may also require coordinated advance widths, reference points and bounds. Transparent curves can be expanded filled outlines plus raster/ROP composition in a fallback branch: an EMF+ pen-width change alone is insufficient. Preserve the original width or select a supported Origin operation when these representations cannot be safely synchronized.

Do not automatically convert/reconstruct a cache to bypass a missing operation. If conversion is permitted, compare its unedited baseline against the original for symbols, text, curves, transparency, clipping and frame geometry before using it. Keep originals and disclose limitations; stop if protected scientific appearance cannot be preserved.

Write a new PPT. Compare protected package parts/streams and exact approved changes; render full slides and details. For preview-only results, disclose that embedded Origin content is unchanged and an OLE refresh may restore the old appearance. This cannot silently substitute for requested editable Origin changes.

## 2. Windows native Origin through MCP

Use the selected Windows computer and an actual connected Origin MCP when present. Discover the current tool catalog/schema and verify its environment and capabilities with the smallest relevant read-only call. Some tools expose only fixed projects or commands: do not invent selectors, unsafe arbitrary commands or hidden write access. An HTTP/API response, a similarly named MCP package or a saved status file is not proof that real Origin loaded the bound source.

Before writing, inspect the exposed operation, input/output paths, instance ownership and whether it executes supplied code, attaches to an existing document, starts Origin or saves over files. Use the user's approved source copy, specific appearance plan and new output path only. Respect required confirmation for a newly installed server, unrecognized code, credential/OAuth provisioning or expanded persistent access. The route choice alone does not approve those separate actions. Do not edit unsaved user work or terminate an unrelated Origin instance.

Prefer a new, independently owned Origin instance; if the MCP cannot isolate a source copy or constrain the operation, report that limitation and obtain any needed decision rather than silently taking over. Capture pre-edit data, bindings, graph/layer inventory and style baselines. Invoke only the supported approved properties, verify actual non-no-op changes, save a new native file, then independently reopen and compare semantic/visual invariants. Record actual tool names/version and results privately.

Apply the native edit/return verification below to MCP too. A successful MCP edit does not itself update the PPT's embedded source, external preview or internal OLE cache. Confirm a supported reinsertion path separately and verify the delivered PPT lifecycle. If the installed MCP lacks a necessary property or safe save/reopen operation, stop that part; do not silently fall back to Python or Mac bridge.

## 3. Mac VM command-line file bridge to real Origin

This is an **explicit opt-in exception for the user's separately provided and reviewed Mac–Windows file bridge**. The bounded code route does not operate a VM; its unsupported native writer does not make this separate Origin route permanently unavailable. Do not invoke GUI/VM clicking or invent a hidden bridge as a fallback.

Use existing task-local file transport and reviewed automation/API entrypoints to an independent Origin instance on Windows. This does not authorize a network listener, remote-control service, attaching to the user's open document, installations, startup tasks, security/network changes or broader folder access. Obtain any required new execution or access approvals separately under the current confirmation policy.

### Session and request gate

1. **Inspect:** collect a small task-private handoff record containing the reviewed bridge package/configuration, allowed task directory, source/profile hashes, supported operation plan, bounded rounds/duration and current session authorization. It is a record of checked inputs, not authorization by itself. Read the current package, scripts/version, source profile and operation allowlist. Historical results are evidence only for their tested source/environment. Recheck machine-specific font indexes and native storage codes on a new source or machine.
2. **Authorize and verify:** require current-session approval for this bridge, source, operations and finite duration/rounds. Do not auto-start/restart from an old approval. Follow the actual authorized activation procedure. A prepared directory, old status file or stopped session is not live connectivity. Never start, take over or stop another session.
3. **Bind:** require fresh matching session state, one active runner, an unexpired session and advancing request sequence. Bind source/configuration/script hashes and the approved operation plan. Verify that the current runner freezes fixed inputs into a fresh round directory and checks them before execution.
4. **Publish:** send only supported requests to the approved location, using fresh outputs and atomic publication where supported. Never replay archived requests, silently swap a frozen source or bypass a source-profile rejection. A new graph needs a new inspected profile, baseline and matching approval.
5. **Match results:** verify session, sequence, source/plan/input hashes and operation-specific stage evidence, including `phase_passed` where used. A `DONE` file or zero exit status alone is insufficient. Inspect an uncertain round before retrying; never accept another session's output.
6. **Stop safely:** mismatch, stale state, rejection, timeout or failed phase blocks that operation, not permission to widen access or switch to arbitrary commands. Stopping the owned runner may not prove its Origin child exited; verify ownership and report uncertainty. Never terminate unrelated Origin processes or discard unsaved user work.

Keep session identifiers, absolute task paths and machine configuration in private task state. Do not put credentials, access tokens, endpoints, archived requests or scientific sources/figures into the reusable skill. Do not encode today's bridge state as a permanent fact.

## Native edit and return checks for both Origin routes

- Load the bound source copy in a newly created independent Origin instance. Capture the relevant baseline: datasets and missing-value fingerprints, curve bindings, layers/groups, axes, text/styles and page/layer geometry. An empty workbook window does not prove an embedded graph lacks data.
- Change only approved, supported properties; save a new file; exit only the owned instance; reopen in another independent instance. Compare protected data/properties and rendered results after reopening. Native Save can change more bytes than a literal patch, so verify semantic/visual invariants too. Cold-test minimal patched candidates without an extra diagnostic save that would rewrite them.
- Distinguish graph-page size, layer/plot size and PPT host placement. One resized layer need not resize another. Check clipping, labels, insets and final glyph/stroke proportions, not just nominal values or API success.
- Return verified native files/exports. Native success does **not** prove PPT completion. Use a supported, confirmed reinsertion path and independently verify native payload, external preview, internal cache and host geometry. Never substitute an incomplete Origin export for a full preview. If faithful reinsertion is unsupported, report the remaining step rather than flattening the editable source.

## Verification and delivery

Apply the same `aesthetic-review.md` acceptance checklist to all three routes, using the confirmed reference and final physical size. Route selection does not approve extra scientific, typography or palette changes.

Report separately: static review; plan/unit checks; source preservation; native edit/reparse; independent Origin cold reopen; rendered review; actual PowerPoint open/display/save; and OLE activation/refresh. Mark unperformed stages **not run**. Neither parser success nor a historical sample proves the current application lifecycle.

Deliver only existing, verified new editable PPT/native files with required visible references in one independent native group per final PPT figure/slide, and a clean companion only as an addition. State exactly which representation changed and which remained unchanged. Keep originals and private provenance outside the skill. A layout page, cache-only image or unchanged copy is not a completed native-source refinement.

## Whole-display Python refinement requirement

When Python is selected, follow [whole-display refinement](python-whole-display.md): inspect and refine outer geometry, inner plotting-area dimensions/aspect, all text, axes, lines, spacing and distortion for every output object. Host-only resizing is not completed refinement. Use the executable coverage gate, preserve live OLE and native PPT objects, and report unsupported inner edits explicitly rather than inventing capability.
