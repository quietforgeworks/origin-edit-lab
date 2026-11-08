# Optional PPT box-draft exchange

Use this reference only when the user chooses the PowerPoint fallback. Local offline HTML with screenshot feedback is the default in the main skill.

## Bundled tools

The Python helpers use only the standard library. They read sources and write new task files; they do not apply scientific-source edits. Check dependencies/renderers separately before visual verification. An ordinary editable-PowerPoint inspection and an actual Origin reopen remain separate checks.

```sh
python scripts/inspect_pptx.py original.pptx --output inventory.json
python scripts/layout_boxes.py create inventory.json boxes.pptx --manifest binding.json --spec panels.json
python scripts/layout_boxes.py read returned.pptx --manifest binding.json --output intent.json --source original.pptx
```

Always curate an explicit `panels.json` before `create`. Example structure, with real inspected IDs substituted:

```json
{
  "panels": [
    {"id": "F01", "name": "器件结构", "sourceAssetIds": ["actual-asset-id"], "category": "schematic"},
    {"id": "F02", "name": "性能曲线", "sourceAssetIds": ["actual-plot-id", "actual-legend-id"], "category": "curve"}
  ],
  "refinement": {"mode": "existing-aesthetics", "references": []}
}
```

A semantic panel may bind several inventory entries. Use `mode: "user-references"` when that template was selected, and record task-local reference provenance. Optional draft canvas/bounds are assistant choices, not fields to ask the user to fill out. The initial tool supports 1–40 readable boxes on one draft slide; split larger sets into separately bound figures rather than silently omitting panels.

`read` returns selected panels with original source bindings, omitted panel IDs, ambiguity warnings, source-hash verification and a layout-intent hash. Pass the original with `--source`; repeat it when a task legitimately has multiple source files. If `originalSourceVerified` is false, investigate the mismatch before scientific-source application. Missing/duplicate markers and unsupported geometry are not permission to guess. Nonrotated native group translation/scaling is supported; inspect reported warnings before using the result.

Run `python scripts/test_roundtrip.py` and `python scripts/test_inventory.py` for portable synthetic checks. These do not establish PowerPoint or Origin acceptance.

## Task artifacts

Keep four distinct task-local objects:

1. The preserved original scientific PPT and its SHA-256.
2. A curated panel inventory connecting each stable panel ID and short label to exact source members, source part hashes and semantic relationships.
3. A new editable PPT with one labelled rectangle per selected scientific panel. The rectangle itself contains its text; do not create separately drifting captions. Store stable identity in object metadata and a project/source binding in the document, not only visible text.
4. The user's returned draft, its hash and a readback report of recognized boxes, omitted boxes, duplicates, unknown objects and supported geometry.

In this optional mode, the user exchanges PPT files only. Do not make JSON export/import, source-map maintenance, or precise geometry entry part of the PowerPoint fallback. The assistant handles any internal manifest.

## Draft construction

Use a neutral, readable arrangement with labels that identify the actual scientific content. There is no requirement to reproduce the source slide's tiny scattered objects. Keep box emphasis/ordering intelligible without overdesigning the draft. Preserve each box's stable ID even when its text changes.

Creating a fresh box PPT is not editing the original scientific PPT. Do not load and re-save the original through a writer that can discard unsupported OOXML/OLE parts. After construction, inspect the actual draft render and verify its IDs/source binding before delivery.

## Returned layout interpretation

Verify exact project/source identity against the task inventory. Extract positions and extents using the actual slide coordinate system. Convert units consistently and reject malformed/unsupported geometry. Do not silently apply group transforms, rotations, copied duplicate IDs or unbound new boxes.

Known deleted boxes mean an unselected subset. Known boxes with changed text retain their scientific binding but surface material changes in intended labels. New/duplicate boxes may express desired reuse or a new panel; ask when the source identity cannot be established. Keep original sources intact in every case.

Interpret relative placement, broad aspect, emphasis and grouping. The final figure may adjust exact dimensions, gaps and alignment for the chosen aesthetic template and actual content. Explain only material interpretation choices and obtain the guide-first approval for the complete refinement before scientific source edits.

## Approval and execution boundary

A returned draft is evidence of composition intent, not a signed precise geometry specification or authorization for unrelated scientific changes. Build a source-bound complete plan containing exact original/returned hashes, source object members, old values, final transforms, fixed/moving connector endpoints, semantic guide anchors, requested styles, unresolved questions and hashes of the shown clean/guide proposal. Record trusted conversation confirmation privately.

Use the bundled `scripts/source_edit/layout_plan.py` alignment-plan gate only for its actual supported roles. For whole-slide objects beyond that schema, a separately tested full-plan guard must cover them. Do not label a photograph or connector a plot frame merely to pass. Recheck source bytes and old values before writing a new output, and verify structure plus rendered appearance afterward.
