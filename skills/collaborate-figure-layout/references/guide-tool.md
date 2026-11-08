# Grouped references on the final candidate

`alignment_guides.py` is a guide-only helper. Its input is the **verified clean FINAL candidate after any separately authorized scientific refinement**, not the old pre-refinement original. Keep that clean final candidate unchanged. The helper adds one native `p:grpSp` to the selected actual slide, behind all direct source shapes. Its name is `FIGURE_ALIGNMENT_GUIDES::v1`; its description contains only the stable versioned schema and group ID. Source hashes stay in the external trusted plan/report, never in the guide group. Each child is a dashed magenta native line, 0.5 pt, 65% opacity, without arrows. The group uses an identity transform in slide coordinates. Scientific shapes, labels, transforms, relationships, and embedded payloads are not edited.

## Required semantic preflight

Inventory the final candidate and explicitly classify any existing alignment references before invoking this helper. Reserved version-marked references are rejected. **Unmarked references cannot be recognized reliably from XML or appearance alone.** Existing annotations/connectors are preserved, and the tool does not prove that every unknown source shape is non-reference content. If preexisting references need removal or consolidation, stop at the supported boundary and use a separately approved, tested operation. Never silently delete scientific content or claim all references are grouped until that semantic check is complete. The present helper rejects source groups on the selected slide and does not merge them.

Choose each guide's meaning and confirm its exact coordinates through the workflow. A JSON plan, source hash, screenshot, or successful verification is not user approval and is not scientific validation. No alignments are guessed, detected, or snapped. The plan must contain explicit horizontal/vertical lines and stable numeric IDs. Guides use distinctive styling and metadata; check visually that they cannot be mistaken for scientific curves and remain visible where intended. Opaque scientific panels may cover background guides.

## Exact plan format

Example only, for a 9144000 × 5143500 EMU slide; replace the source hash, slide, IDs, and coordinates with the inspected and approved values. One millimetre is 36000 EMU; one inch is 914400 EMU. Use **integers**, not floating-point or rounded inferred coordinates. `slide` is 1-based presentation order resolved through presentation relationships, not a guessed `slideN.xml` filename. `group_id` and every line `id` must be positive, unique, and unused by any `p:cNvPr` on that slide. `key` is a unique ASCII semantic identifier. No additional fields or duplicate JSON keys are allowed.

```json
{
  "schema": "figure-alignment-guides/v1",
  "source_sha256": "REPLACE_WITH_SHA256_OF_VERIFIED_CLEAN_FINAL_PPTX",
  "slide": 1,
  "unit": "EMU",
  "group_id": 100,
  "lines": [
    {"id": 101, "key": "top_axis", "x1": 360000, "y1": 720000, "x2": 8784000, "y2": 720000},
    {"id": 102, "key": "left_axis", "x1": 360000, "y1": 720000, "x2": 360000, "y2": 4783500}
  ]
}
```

A line must have ascending endpoints, nonzero length, no diagonal, and both endpoints within the slide. Use 1–100 lines. There is no implied reversal, clipping, coordinate conversion, source editing, or approval flag.

## Commands

Run from the skill directory with Python 3 and `lxml` available. The bundled `scripts/source_edit/pptx_origin.py` remains unchanged.

```sh
python -c 'import hashlib,pathlib; print(hashlib.sha256(pathlib.Path("clean-final.pptx").read_bytes()).hexdigest())'
python scripts/alignment_guides.py add --source clean-final.pptx --plan approved-guides.json --output final-with-guides.pptx
python scripts/alignment_guides.py verify --source clean-final.pptx --plan approved-guides.json --guided final-with-guides.pptx
python scripts/alignment_guides.py restore --source clean-final.pptx --plan approved-guides.json --guided final-with-guides.pptx --output restored-clean-final.pptx
```

Keep `final-with-guides.pptx` as the final deliverable with its grouped references. `restore` is a verification/recovery operation, not a replacement deliverable that silently removes the required references. It requires the same clean final candidate and a valid guided candidate, then copies the clean final candidate's **exact original ZIP bytes** to a new filename. It does not reconstruct or revert to older scientific content. Inputs and existing outputs are never overwritten. All commands fail with a nonzero exit status if verification fails.

`verify` checks the exact marked group and only planned guide-line members; all IDs, positions, styles, and no-arrow settings; its position behind the original shapes; canonical full-slide equality after group removal; and byte equality of every other uncompressed package part, including embeddings. It also checks the entire candidate slide against the original plus exactly the planned group. It rejects additions/removals of package parts. Source and candidate hashes are rechecked before a successful verification result.

## Supported boundary and validation limits

This is not a general PPTX repair/reconstruction tool. It accepts a bounded transitional `.pptx` with an explicit slide size and ordinary direct `sp`, `pic`, `cxnSp`, or `graphicFrame` children on the selected slide. It rejects source groups, `AlternateContent`, slide timing/transitions, unsupported top-level extensions, nonidentity slide-root transforms, missing/duplicate structural IDs, preexisting reserved guide markers, external relationships, known macro/ActiveX/signature envelopes, broken internal relationships, unsafe ZIP members, and DTD/entity XML. Limits: 200 slides, 4000 package parts, 64 MiB per uncompressed part, 256 MiB package bytes, and 64 KiB plan. Embedded scientific payloads are opaque and are never executed or inspected as executable code. Refusal does not authorize flattening, rebuilding, ungrouping, or dropping unsupported content.

The reserved-marker check covers the entire package. Therefore this helper currently adds guides to only one selected figure slide in a deck and cannot be chained to guide additional slides. A multi-figure final deck needs a separately tested writer that preserves and validates one group per figure slide; do not claim that repeated calls complete that requirement or remove another slide’s guides to make a call pass.

Nested OLE-preview `p:pic` representations may repeat ID `0`; they are not structural slide members. Their original XML is preserved. New guide IDs still cannot collide with any existing ID, including preview IDs.

The report is **package/XML evidence only**. It explicitly reports PowerPoint and Origin reopening as unverified. No native application, bridge, MCP, or network operation is used. A real PowerPoint “delete this group” test needs application reopening and a fresh scientific-content comparison against the same clean final candidate. PowerPoint may rewrite package metadata, so do not claim ZIP equality after native saving. Visually inspect the final deck at its intended scale and verify labels, curves, guide visibility, and group selection before delivery; this helper cannot substitute for that application check.

Synthetic tests, including CLI execution and fail-closed checks, run in both modes:

```sh
python scripts/test_alignment_guides.py -v
python -O scripts/test_alignment_guides.py -v
```

The synthetic fixtures test package behavior, not native-app compatibility or scientific correctness.
