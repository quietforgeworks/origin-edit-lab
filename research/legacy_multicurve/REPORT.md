# Result and boundary

The narrow experiment succeeds in **official LabPlot 2.12.1**, not verified Origin:

| Curves | Explicit column pairs in Book1 | Exact source cells | Exact drawn XY pairs | Dataset records | Frames |
| --- | --- | ---: | ---: | ---: | ---: |
| 2 | A/B, C/D | 200 | 100 | 27 | 490 |
| 5 | A/B through I/J | 500 | 250 | 33 | 526 |
| 10 | A/B through S/T | 1,000 | 500 | 43 | 586 |

Each series has its own explicitly identified X column, Y column, and global
1-based dataset selectors. All X vectors are pairwise different. An interior
negative-zero X in the second series breaks any accidental shared-A fallback.
This exercise retains one existing sheet, not one sheet per series.

## Sequential grammar and edits

The exact legacy fixture has a 17-byte signature followed by 478 sequential
length-framed records, ending at byte 228955, then an opaque preserved tail.
The forward walker follows the official reader's nested structure:

1. Global header and zero marker.
2. Dataset triples (header, data, mask), terminated by a zero header.
3. Window list, each containing layer lists.
4. Each layer has annotation, curve, axis-break and X/Y/Z axis-parameter lists.
5. Every list is terminated by a zero-length record, not a guessed stored count.

Unsupported annotation groups and unfamiliar fixture structure are rejected.
All input bytes are SHA-pinned before edits. This is not a general OPJ parser.

Two existing data frames for Book1 A/B receive synthetic values. For each added
series, two dataset triples are appended at the old dataset terminator, two
worksheet column header/data pairs at Book1's column terminator, and one graph
curve header/data pair at Graph2's curve terminator. Original dataset IDs 1–25
remain unchanged. The new IDs are 26/27 through 42/43.

Added datasets clone the two original header layouts, changing only their
fixed-width names and numerical payloads. New worksheet records change the
explicit dataset selector at +4, column name at +18, and Y-associated X selector
at +35. New graph curves change Y at +4 and X at +35. **No X=A inference occurs.**
The official reader uses graph Y +0x04 and X +0x23 to look up dataset ordinals.
All 50-row allocations/ranges remain 50. No unknown count, range or pointer is
patched speculatively. Five splices suffice; deleting only inserted bytes and
restoring only the two original data frames recovers every original byte.

## Independent real-application observations

The official executable/importer are hash-pinned. An authored Qt observer opens
only a private read-only snapshot using the app's actual import UI. It supplies
no numerical values and contains no Origin parser. It passively observes every
imported XYCurve, public `xColumn`/`yColumn` pointers and their actual object paths,
public column value/mask/validity APIs, and `pointsUpdated` signals emitted during
the app's redraw. It separately records the worksheet's public values and uses
normal Save As to create the app's LML project.

The Python verifier imports no native parser/writer. Against each retained raw
synthetic JSON, it compares:

- Every worksheet API binary64 cell.
- Every independently bound curve source column's identity and binary64 cell.
- Every pair in every captured actual curve point signal, preserving row order.
- Every saved LML column payload and the saved X/Y source binding.
- Each added column's metadata and each added curve's cloned configuration.
- All unrelated project values/configuration, including other sheets, matrices,
  folders, notes, graph axes and original curve styling.

For the last check, only intended new columns/curves are removed and original
A/B payloads restored. UUIDs and generated creation timestamps are normalized;
root modification time, thumbnail and dock UI state are separately hash-recorded
and excluded. XML text/tails are otherwise exact. The sole intended sibling
indent change after inserting columns is validated against the original
nonfinal/final column forms, then restored for the whole-project comparison.

All 2/5/10 cases pass in normal and optimized Python. Numerical source, bound
source, drawn logical points and saved values match bit-for-bit. The decimal
`0.1234567890123456789012345` is honestly recorded as rounded to binary64; the
original lexical value and exact rounding error remain in the local manifest.
No measured data was used.

Screenshots were visually inspected for all three cases. They show the actual
native-imported graph; 10 curves are visually cluttered because existing black
styles are cloned. Screenshots support, but do not prove, curve counts or data
preservation. The unchanged native legend shows only B. Added curves remain
visible but `legendVisible=0` in the importer's saved representation.

## Tests and hardening

48 tests pass both normally and with `python -O`: 16 input/guard tests, 13 native
fixture/wrapper tests, 19 real-evidence verifier tests. Negative cases include
missing X, unequal X/Y lengths, missing cells, duplicate identities, forbidden
numbers, wrong native X selectors, altered snapshots, lost/duplicated observations,
wrong bound/saved X, missing signals, point or saved-cell bit corruption, new
style/column changes, unrelated content and whitespace-only mutations.

Default native-safe APIs reject before I/O. The wrapper preflights source bytes
and all output destinations before any mkdir/write, creates raw files exclusively,
and rolls back only its own unchanged raw inode after a failed generation.
Tests cover existing/symlink destinations, bad templates, raw creation races and
output publication races. No assertions implement safety gates.

## Exact native blocker and limits

**Blocked action:** certify/export these candidates as safely editable Origin
projects. **Target:** legacy OPJ candidates with newly cloned dataset/column/curve
records. **Reason:** native semantics of opaque metadata and Origin's lifecycle
are unverified. This is a validation gap, not a tool denial or failed execution.

For example, the untouched global header payload has a 16-bit value 26 at +4,
but its meaning is not documented by the official reader, which reads only the
version from that header. It might be count-like; no conclusion or speculative
update is made. Cloned dataset/header/curve bytes may also carry identifiers,
association groups or hidden state that LabPlot ignores. Byte preservation cannot
prove those copies are valid new Origin objects. The third-party workbook writer
uses a different 147-byte dataset and 519-byte column layout; its field claims do
not establish semantics for this fixture's 140/489-byte records.

Origin reopen, edit, refresh/recalculate, save, close and save-cycle reopen were
**NOT RUN**. LabPlot reimport and LML save do not substitute for these steps.
The default gate stays closed even after all tests pass.

This experiment does not support unequal row lengths, missing values, errors,
formulas, cross-sheet XY pairs, new sheet/window creation, automatic legends,
new graph styles, arbitrary templates, OPJU writing or full data sanitization.
Unwanted original fixture content is retained byte-for-byte rather than deleted.

A next cloud-only step could inspect more public paired native files to resolve
opaque identifier/group/count semantics. An eventual controlled Origin oracle
would need to inspect each source binding, edit and recalculate each independent
series, save as supported by that Origin version, close/reopen, and verify all
original unrelated objects. No user collaboration, Mac or VM action was attempted.
Until that oracle is available, this remains a useful importer experiment rather
than the requested finished native Origin workflow.

## Provenance

- Public fixture source and hash: README and `evidence/source-provenance.json`.
- Official LabPlot release source: `https://download.kde.org/stable/labplot/labplot-2.12.1.tar.xz`.
- Official source tar SHA-256: `e28155bfddf40e5b6f7c4791313556d1e48138044f216f210d515b9f6d6c106a`.
- Official `OriginAnyParser.cpp` SHA-256: `b43d1fbf3b70fd135188dcd12838c83b0886dc3444dbc63b086183e09f53d611`.
- Reader control flow: dataset lists around lines 110–130; window/layer/list
  grammar around 405–576; curve framing around 671–719; XY selectors 2387–2412.
- Native record walker, patcher, numerical conversion ledger, verifier, Qt
  observer and tests are authored research. No third-party implementation is
  included in the source package. Quantized source was read for comparison only;
  no quantized code is needed or executed by this experiment.
