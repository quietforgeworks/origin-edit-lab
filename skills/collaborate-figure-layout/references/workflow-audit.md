# Whole-workflow audit and release gates

This is a tested workflow with bounded file tools, not a universal autonomous figure editor. Each execution records its own evidence. Synthetic regression passes are not evidence that a particular user PPT opens in PowerPoint or Origin.

| Stage | Required behavior | Evidence/check |
|---|---|---|
| Intake | Identify current PPT, preserve original, map panels to exact source objects; flag ambiguous ownership | Inspect PPT package and source binding; verify unchanged source hashes |
| Mode | Interactive composition or light refinement; skip unnecessary setup | Chat choice or explicit user instruction, not a fictional page control |
| Arrangement | User drag or semantic assistant proposal; independent panels stay independent | Local controls tests; source/map identity preserved |
| Canvas | Whole outside excluded, partial overlap blocks confirmation, empty canvas rejected | Handoff stage failure tests |
| Guides | Five semantic colors; confirm relationships, not absolute drawing positions; protect user artwork and derive final coordinates from aesthetics | Handoff tests and actual same-origin HTTP flow; imported readiness cannot bypass waiting |
| Typography | Preserve reference/source size hierarchy; apply font size, character advances, baseline/paragraph spacing and ink-clearance corrections | [Reference-led typography](typography-reference.md); equivalent-scale comparison and final-version glyph/spacing review |
| Style | Reference images or defaults; Calibri role-based visual hierarchy; no scientific changes from style examples | Read applicable aesthetics and inspect final-size render; missing fonts reported |
| Route | Python, Windows Origin MCP, Mac bridge share same visual target | Chat selection; verify current tools and approved scope; no automatic route substitution |
| Lock | Real expiring lock, renewal, cancellation, no late writes; restart retains saved state | Expiration/cancellation/restart tests; UI modal control tests |
| Handoff | Compact reads by default, explicit versioned confirmation in page/chat, guarded writes and refresh notification | HTTP/CLI end-to-end test and local-page JS harness; no automatic content polling |
| Conflict | Keep user unsaved draft, do not overwrite newer state, preserve recoverable copy | Page conflict test; stale-revision and draft recovery controls |
| Refinement | Restore distorted text/axes; no generative measurement data; preserve all native PPT objects and Origin OLE | Per-object patch/invariant tests plus task-specific source/output audit |
| Return | Update previews and source geometry independently; preserve newer drafts and resolve new semantic/layout scope before applying it | Validated PNG preview update tests and page adopt tests |
| Deliver | Group guides only, maintain independent original object grouping, truthful cache/native reporting | Native/PPT tests, complete final-size visual audit, activation and refresh in actual target software when available |

The local JavaScript harness executes actual page code with a small simulated DOM. It checks state, controls and failure behavior, **not browser rendering, physical pointer capture or target-host fonts**. HTTP tests use only synthetic projects. Full browser, actual PowerPoint rendering, Origin activation/refresh, Windows MCP and Mac bridge checks remain per-task checks, not automatic claims from installation. When unavailable, name exactly what was not tested and preserve the last verified output.

All stages can return to an earlier decision without overwriting the source. A changed layout cancels confirmation. A changed guide mode requires a new assistant proposal for auto/constrained modes; adjusting a guide changes the saved snapshot but does not make its drawing position a pin. Use the decision rules in [fast-path.md](fast-path.md) to distinguish fresh-state checks, explicit appearance requests and genuinely new alignment intent. Failed scientific edits never turn into a flattened slide fallback. Lock cancellation means subsequent assistant writes must stop until a newly coordinated lock is acquired.

Guide-semantic audit: [guide-relations.md](guide-relations.md) separates drawing positions, alignment intent, guarded derived geometry and final native guide artwork. Test position-invariant intent, relationship changes, source-anchor resolution boundaries, project identity, legacy read normalization and preservation of current user drafts. Snapshot invalidation protects freshness; it does not make rough coordinates mandatory.
