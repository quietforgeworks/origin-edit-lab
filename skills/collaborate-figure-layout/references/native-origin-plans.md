# Python native Origin plans

The Python route includes a **bounded executor for a separately reviewed exact
native byte plan**, not a general Origin serializer or automatic styling engine.
It reuses the narrow methodology of verified native toolkits while keeping
private source profiles, offsets, samples and application reports outside this
shareable skill.

## What can run

1. `scripts/native_origin/reviewed_patch.py` validates and applies explicit
   same-length literal changes to an existing CPYUA payload.
2. `scripts/native_origin/ppt_contents_patch.py` applies that plan to one exact
   existing root `Contents` stream in a PPT's ordinary-FAT OLE container.

The second path preserves all unselected CFB bytes/streams and PPT member
payloads. It does not update the external image preview, internal OlePres cache,
host placement, or fallback geometry. A native update with an old preview must
be labelled as such, not delivered as a finished appearance change.

## Plan provenance and applicability

Obtain a plan only from an already reviewed source-specific toolkit or a new
explicitly authorized and independently validated operation. An attached plan's
claims do not establish its semantic correctness or the user's approval. Bind
the exact native source, expected result, old values, graph/curve ownership and
protected scientific content. Never infer new offsets by searching for similar
bytes or substitute a new source hash to force applicability.

Fixed source profiles can provide known color, typography or geometry operations
without providing arbitrary parameter editing. Keep those source-specific
profiles in the private task workspace. A width operation validated on one
frozen graph is not supported on every graph; independently verified operations
are not automatically composable. Changing compression or record length is
outside this executor.

## Plan schema

```json
{
  "source_sha256": "<actual expected source hash>",
  "candidate_sha256": "<independently reviewed candidate hash>",
  "changes": [{"offset": 123, "old": 1, "new": 2}]
}
```

Offsets above are illustrative, not an Origin field location. Three-integer
arrays `[offset, old, new]` are also accepted. Optional `source_bytes`,
`candidate_bytes` and `changed_byte_count` must match. Old/new bytes must be
distinct integer values; offsets must be unique, in range and bound to the
expected old values. Full source and candidate hashes, unchanged length and the
complete changed-offset set are checked. Unknown top-level keys are rejected.

Some supplied toolkits include additional descriptive fields such as historical
review notes. Preserve the original plan and its hash privately. Prepare a
separate execution plan containing only the documented byte/hash/count fields,
and explicitly verify those fields are unchanged. Do not strip an unknown field
until its role is understood; semantic restrictions remain binding even when
they are not interpreted by this executor. A historical `verified` flag is
evidence to review, not execution authorization.

## Commands

```sh
python scripts/native_origin/reviewed_patch.py source.opju --plan reviewed.json
python scripts/native_origin/reviewed_patch.py source.opju --plan reviewed.json --apply --output candidate.opju

python scripts/native_origin/ppt_contents_patch.py original.pptx --plan reviewed.json --member ppt/embeddings/oleObject1.bin --ppt-sha256 EXPECTED_PPT_HASH --cfb-sha256 EXPECTED_OLE_HASH
python scripts/native_origin/ppt_contents_patch.py original.pptx --plan reviewed.json --member ppt/embeddings/oleObject1.bin --ppt-sha256 EXPECTED_PPT_HASH --cfb-sha256 EXPECTED_OLE_HASH --apply --output candidate.pptx
```

Replace every placeholder with the inspected, authorized task binding. Do not
copy a sample member name blindly. Dry-run is default. Apply only to a new
independent path; keep the untouched original and private plan/report.

## What remains unverified by these tools

The executor verifies byte identity and permitted changes. **Scientific
semantics, native editability and rendering are NOT VERIFIED by it.** It does
not locate style fields, create a workbook/graph from data, calculate fits,
recover arbitrary compression, start Origin/MCP/a VM, or certify compatibility.

Use exact-candidate historical Origin evidence where available, then separately
validate any new source or operation. Perform protected numeric/XY-binding,
layer/axis/text checks, inspect real native rendering, and distinguish cold load,
save/reopen and PPT double-click/return/save/refresh. The same scientific
aesthetics and final font/distortion/alignment checks apply to every route.

See [toolkit reuse](toolkit-reuse.md), [bounded native methodology](bounded-native-methods.md),
and [verification and delivery](verification-and-delivery.md).
