# Research contract

## Input, provenance and precision

CSV is exactly the frozen fixed50 active-prefix contract. Shapes 7/49/50 only. Fixed native X/Y column bindings Book1 A/B; exactly one graph curve. No allocation expansion or multicurve composition. Input declaration is a strict three-key JSON object, retained byte-for-byte. Caller-measured and caller-unspecified data are accepted without being recast as synthetic. This does not authenticate their source or verify measurement claims.

The existing conversion policy and exact per-cell ledger are unchanged. A 50-row native no-op refuses, as in the frozen algorithm. Output native values are binary64 conversions. Arbitrary-precision decimal strings and CSV serialization survive in the bundle, not as native text metadata. Original CSV quotes, CRLF/newlines, numeric lexemes and signed-zero spellings are not normalized. Neither input file is written.

## Native preservation and recovery

Only validated A/B active-prefix cell bytes and two dataset end-exclusive fields can differ. The allocation stays 50. All other bytes, graph serialization, stylesheet-like content, original graph bindings, opaque tail and unresolved curve/worksheet range fields remain byte-exact. With 7 or 49 rows, inactive native template A/B cells remain. `bundle.json` lists their dataset, row range, exact little-endian bits and hexadecimal float values. Other template books, graphs, matrices, notes and metadata remain even with 50 rows.

Recovery is exact to the hash-pinned original, plus exact raw input and declaration. Recovery is refused if any bundle artifact does not reproduce. This is rollback of a research template modification, not data scrubbing, generic repair or proof of native application editability.

## Trust and source verification

The new full-artifact API reuses exact reviewed active-prefix algorithms without changing them. `verify_candidate` is invoked with full manifest and both inspections. All eight generated artifacts are rebuilt from the exact pinned source plus raw inputs and compared as bytes. This is stronger than comparing Python object equality: schema types and negative zero cannot be silently conflated. Files are bounded and strict parsed before the legacy functions see them.

CSV and declaration anchors must be supplied independently at verification/recovery time. Without that external reference, a fully coordinated replacement of input and generated artifacts could be internally consistent but refer to different input. The anchors establish integrity relative to selected bytes, not authenticity, ownership, measurement quality, or non-repudiation.

Frozen vendor source inventory and hashes are hard-pinned before execution. `audit_source.py` verifies the separate authored source/report manifest and inventory; a trusted external digest of that manifest remains necessary to authenticate a distributed package. Source integrity is not third-party application acceptance.

## Filesystem and failures

Linux only. Native outputs use the unchanged `renameat2(RENAME_NOREPLACE)` helper, with no overwrite fallback. Leaf/ancestor symlinks, lexical traversal, nonregular or oversized files, and existing outputs refuse. Inputs are opened with `O_NOFOLLOW|O_NONBLOCK`, checked for identity/size/timestamp consistency, and snapshotted into bytes. Staging is created adjacent to the destination, never via unchecked TMPDIR. Native output and staging inside this package refuse except within its explicitly dedicated `runs/` descendants. Source, test, application, input and evidence directories are protected. Historical application evidence is retained at its recorded paths; future observations must use an external destination or `runs/`.

Stable trusted ancestor directories are required. This is not a hostile-concurrent-filesystem sandbox. No crash durability claim is made. Ordinary interrupted staging is removed. SIGKILL can leave staging. If publication has happened before a later error, the published directory remains; no rollback or removal is attempted. CLI failures report destination existence but do not infer ownership from it.

## Independent application boundary

The existing official LabPlot 2.12.1 executable, importer library and AppRun launcher are hash-pinned. Other runtime dependencies are not exhaustively pinned; the local run and receipts are evidence of the observed import, not cryptographically authenticated execution provenance. The existing observer source is copied unchanged and compiled locally without fresh downloads. A separate custom runner verifies the full native bundle, isolates empty per-run profiles and loads an exact native snapshot. It records actual `Column::valueAt` bits and actual `XYCurve::pointsUpdated` logical points, and saves real application LML. It does not parse OPJ cells or supply replacement curve values.

A separate validator independently converts the original CSV with Python float, checks every actual API cell and point signal, reads all saved column doubles, and compares the full saved project to a fresh baseline. Only two A/B saved data payloads may differ after declared UUID/creation-time and root UI-metadata exclusions. Screenshots/logs are supplemental, not part of numerical acceptance. The serialized native bundle always says its own source-only application check is NOT_RUN; the separate input-specific observation report records the actual application result.

LabPlot is an independent importer, not Origin. No Origin open/edit/update/recalculate/native-save/close/reopen lifecycle has run. No OPJU support, arbitrary template support, native-safe export claim, new-sheet writer, broader row count, multicurve/expansion combination, Mac write support, stable-workbench integration or native-binary distribution is provided by this research. Reviewed authored sources and compact evidence are distributed separately from local native artifacts.
