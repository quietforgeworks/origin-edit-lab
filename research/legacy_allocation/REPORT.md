# Boundary-based allocation resize: independently read/rendered, native safety unresolved

This report accompanies the current source-only package. It records earlier
fixture-bearing experiments; native outputs and full application evidence from
those runs are external to this package. Current integration changes and checks
are noted below and in `review/REVIEW.md`.

## Result

The isolated exact-fixture research now has real **51-, 257- and 1024-row
allocation** candidates, rather than merely longer active prefixes inside the
old 50-cell allocation. Official LabPlot 2.12.1 imported them through its real
Origin dialog and freshly rendered their native Graph2 object. This is actual
independent application behavior, not a self-parser, reconstructed preview,
Python rendering or Origin acceptance.

- 51 rows: 102 public-API X/Y doubles and 51 real logical points, all bit-exact.
- 257 rows: 514 doubles and 257 logical points, all bit-exact.
- 1024 rows: 2048 doubles and 1024 logical points, all bit-exact.
- Each case emitted two passive `pointsUpdated` Qt signals, with ranges
  `[0,50]`, `[0,256]` and `[0,1023]` respectively. Every emitted point matched its
  input binary64 bits. The curve's own source columns had exactly n rows, all
  valid and unmasked, with matching bits.
- Negative zero was tested after the former boundary, at zero-based Y row 50,
  additionally 256 for the larger cases, and 1023 for the largest. Initial X/Y
  negative zero and a long decimal input were also retained and audited.
- The application-owned LML save had exactly four non-generated differences:
  A and B `rows` attributes, plus A and B binary64 payloads. Those saved values
  independently matched the actual Column API. Graph configuration, styles,
  axes, source bindings and all other project content were unchanged.
- The original 25 dataset identities/order and 478 framed-record count are
  unchanged. No new dataset IDs were introduced. Every native graph/style byte,
  every unedited record and the entire opaque tail were preserved after relocation.
- Source inputs and each imported private snapshot remained byte-exact. Rollback
  recovered the original fixture's exact SHA-256 in all three cases.

The native-safe export API still **fails closed by default**. Only an explicitly
named LabPlot-only research mode writes these candidates. The result breaks the
LabPlot-side allocation barrier; it does not establish safe native Origin
allocation expansion. Unknown metadata semantics are still unproved.

## Exact file and edit boundaries

Source: the KDE public `origin8_test_tree_import.opj`, 231,494 bytes, SHA-256
`ea50c9b97b063898f654a6189b30ca5d8be8b52ad4c9469b3934cd009185265a`.
The full source hash is required, so the adapter cannot silently generalize to
another project or an already modified candidate.

The source starts with a 17-byte format signature, a 75-byte framed global
header and its zero-size end marker. Dataset list entries follow as three
sequential frames: header, data, mask. The first two entries are Book1_A and
Book1_B, whose header frames start at 103 and 760 and whose data frames start at
249 and 906. Both headers are 140 bytes. Both data payloads originally have 500
bytes, 50 tagged numeric cells of 10 bytes each. Their mask frames are empty.
There are 25 dataset entries; the zero-size list terminator starts at 35,764.

For each of these two entries, the patcher:

1. Changes only header payload `+0x19` total rows and `+0x21` exclusive active end
   from 50 to n. It keeps begin row `+0x1d` zero and all other header bytes exact.
2. Replaces that entry's data payload with n numeric cells, each `00 00` followed
   by the audited little-endian binary64. It changes that frame's own length
   prefix to `10*n` and preserves the exact framing delimiters.
3. Reassembles the sequential record stream from four explicit non-overlapping
   splices. It does not search for and rewrite occurrences of the number 50,
   invent enclosing lengths, or interpret opaque fields as row counts.

For `d=10*(n-50)`, the B header/data move by d; all original bytes from offset
1,412 onward move by 2d unchanged. Source gap bytes are copied intact. All 478
frames are walked again from the actual candidate boundaries. Every unedited
frame is compared exactly to its corresponding original frame; headers are
compared after masking only the two documented four-byte fields. The opaque
suffix is compared by exact source reconstruction/hash, not interpreted.

Thus final file sizes are 231,514, 235,634 and 250,974 bytes. The framed-region
ends move from 228,955 to 228,975, 233,095 and 248,435 respectively. The native
Graph2 span relocates intact and retains SHA-256
`e9bb6b64ee536d6f6aaa8129c24e357d0f9a83eb41dfb58e61985638b01f8024`.

## Why these changes suffice for the tested reader

The following observations are about the pinned official LabPlot/liborigin
reader, not a complete Origin specification:

- `OriginAnyParser.cpp` lines 92–94 obtains file length from the stream, not a
  stored file-size field. Lines 114–122 iterate dataset entries until the
  zero-size terminator. Lines 245–280 implement local size-prefix/delimiter
  records. Lines 329–391 consume each dataset's header, data and mask frames.
  These frames are siblings in the list, not a single outer byte-counted payload.
- The dataset branch's seeks use current stream positions plus just-read record
  lengths. Resizing the own data frame and relocating subsequent frames updates
  every boundary this reader consumes there. No stored absolute file pointer or
  parent dataset-list byte length is read in this branch. This does **not** prove
  no such dependency exists in bytes that the reader ignores.
- Lines 1139–1144 read total/begin/end rows at `+0x19/+0x1d/+0x21`. Lines
  1222–1224 retain these values. Lines 1241–1246 derive the number of numeric
  cells from data-payload bytes divided by the cell width.
- Dataset IDs are ordinal: lines 114 and 1306 initialize/increment the dataset
  index. No dataset was added, deleted or reordered. Graph curve payload IDs
  at `+0x04` and `+0x23` are resolved using `findDataByIndex(w-1)` at lines
  2388–2413. The original X=1, Y=2 IDs remain unchanged.
- `OriginProjectParser.cpp` lines 858–868 allocate the spreadsheet from its
  parsed vectors. Lines 933–936 and 945–962 copy the active numeric rows.
- The actual imported XYCurve's passive Qt signal exposes logical points used
  by its normal render path. No observer data injection, column mutation,
  manual recalc or independently computed plot is used.

All existing unrelated windows, folders, notes, matrices and other spreadsheets
survived as the same app-owned parsed XML content. Object counts remain six
spreadsheets, two workbooks, three matrices, three notes, two folders, one graph
worksheet and one XYCurve. Exact XML text/tail whitespace is compared; only
generated UUID/creation times plus separately hashed dock state, modification
time and thumbnail are excluded. This is a parsed XML comparison, not byte-for-
byte LML serialization equivalence.

## Native safety blocker and non-inferences

Three unresolved property headers retain the pair `(0,50)` at payload `+7/+11`:
Book1_A worksheet property, Book1_B worksheet property, and the graph curve.
Their original frame offsets are 123,513, 124,015 and 219,404; the candidate
offsets are those values plus `20*(n-50)`. They were **not changed**.

The reader does not use these fields to limit its curve to 50 points. Seeing
1024 points demonstrates the tested reader's behavior only. Origin could use
them as a native subset, cached bound or another dependency. It could truncate
the curve, normalize the project or handle relocation differently. Unknown
absolute pointers or enclosing sizes in opaque content have not been ruled out.
Byte preservation does not establish that every retained field is semantically
valid after expansion.

The inspected pinned quantized writer is not an applicable oracle for these
unknown fields. Its different 147-byte dataset header writes an allocation
value at `+6`; this exact legacy fixture's `+6` integers are 250 and 65,786, not
50. That writer also places a global size at payload +115, outside this legacy
fixture's 75-byte global header, and uses different worksheet/property layouts.
Those rules were not transplanted. Quantized was inspected, not executed here.

Consequently `patch_bytes`/`generate` without an explicit `research_only=True`
and both generation CLIs without `--labplot-only-research` reject before
creating output. The toy wrapper `make_cases.main()` likewise requires literal
`research_only=True` before accessing the fixture environment variable or any
input/output paths; a refused CLI invocation also avoids bytecode creation.
The refusal applies even to the three LabPlot-passing counts. No speculative
selector, unknown pointer or enclosing-length edit was attempted or promoted.

**Origin reopen, redraw, update, recalculation, save and saved-OPJ reopen: NOT
RUN. Official Origin Viewer: NOT RUN here.** LabPlot's save is LML; no native
Origin round-trip is claimed. A controlled Origin test against these exact
candidates remains necessary before promoting any native-safe route, including
testing all rows selected, original binding/style retention, ordinary updates,
recalculation and a save/reopen cycle. If Origin exposes a dependent field,
identify it by native evidence rather than overwriting guesses.

## Guardrails and tests

The current suite has 59 tests passing normally and with `python -O`; none skip
when the exact public fixture is supplied. Without it, 28 pass and 31 explicitly
skip. Six integration tests cover wrapper API/CLI opt-in, refusal before
environment/path access, no default output and unchanged candidate hashes.
Earlier 53-test logs and the real-application verification remain historical
evidence; no application rerun was needed for this wrapper-only hardening. The
previous full app verifier passed normally and optimized; shell syntax checks
also passed.

Coverage includes all supported counts, relocated framing, the unchanged entire
post-XY suffix, global IDs, every cell bit and conversion ledger, signed zero
after row 50, exact rollback, changed source/repatch refusal, framing and opaque
field corruption, malformed CSV, unknown counts, nonfinite/missing/underflow/
lossy-integer rejection, fixed-axis limits, default native-safe refusal with no
output, no-overwrite/atomic publication, symlinks, manifest types/content,
rewritten candidate hashes, exact source/artifact regeneration, signed-zero
ledger corruption and XML whitespace/content preservation.

Independent review identified an initial nested-symlink gap in the preflight
checks. All existing input/output path ancestors are now checked, with explicit
nested-alias regressions. The runner checks input/profile/runtime ancestors.
This still assumes a trusted, stable directory tree: preflight is not an OS
sandbox against concurrent ancestor replacement. The final destination itself
retains its kernel-level atomic no-overwrite protection.
The reviewer also found a pre-validation write in the convenience case wrapper;
its fixture, directory, CSV and destination paths are now validated before
read/mkdir/write, and toy CSV creation uses exclusive `xb` mode. A simulated
concurrent CSV creation is refused while the concurrent file stays exact.

All three raw CSV files are retained unchanged and hash-pinned. The convenience
sinusoidal toy-data generator verifies these hashes to fail closed if a platform
libm changes its textual output. Verification reads the retained CSV directly.
Decimal-to-binary64 rounding is explicit per cell; long decimals are not claimed
to be exact decimals after conversion. Conservative subnormal/underflow rules
and the preserved native X[-5,55], Y[-0.1,1.1] axes remain enforced.

Unsupported: arbitrary templates or row counts, allocation shrinkage in this
adapter, unequal X/Y lengths, missing/masked/text cells, nonzero starts, disjoint
or per-curve subsets, adding/reordering datasets, multiple-curve/general graph
serialization, automatic axis rescaling, OPJU/OGGU, Origin-side correctness and
private-template sanitization. Other public-fixture sheets remain preserved.

## Included evidence and external regeneration outputs

The current source-only package includes:

- `candidates/raw{51,257,1024}.csv`: only the three synthetic, hash-pinned inputs.
- `evidence/compact-verification.json`: historical synthetic-only summary with
  source audit results and hashes, without original fixture payloads.
- `evidence/field-evidence.json`, `source-provenance.json` and
  `visual-inspection.json`: field/source basis, official artifact hashes and
  records identifying the screenshots inspected. The screenshots are excluded.
- `evidence/tests-*.log`, `application-verification-*.log` and `review/evidence/`:
  historical test/independent-review records and current post-integration logs.
- `PACKAGE-INVENTORY.json`: current package files/hashes, excluding itself.
- `evidence/source-freeze-manifest.json`: unchanged historical author-freeze
  evidence from before public packaging and integration hardening, not a current
  inventory. Its original hashes and earlier test records are intentionally kept.

The following are **not included**. They are created only by local regeneration:

- `candidates/generated{51,257,1024}/`: native candidate, conversion ledger,
  framed offsets, reversible source-bearing splices and exact native rollback.
- `application/results/{original,expanded51,expanded257,expanded1024}/`: actual
  application logs, imported native snapshots, source hashes, public-API doubles,
  passive curve observations, LML saves and screenshots.
- Full `verified-results.json` comparisons: these contain original public-fixture
  column payloads and must remain outside a source-only distribution.

The previously built authored observer has SHA-256
`3c4df197b6c6c960a44d31bf3f1a704580d63ba119ea927881c02925f2b7aa2a`.
Its source is included; the binary is not. The official executable/importer
library were hash-checked before the recorded runs. Each run used isolated cloud
HOME/XDG/temp profiles and Qt offscreen. Status 124 was the deliberate timeout
after successful captures and Save As. No Mac, VM or front-of-user interaction
occurred, and no new upstream binary was fetched.

The current package contains no native project samples, original payload
fragments, application saves/screenshots/binaries, third-party implementation or
private user data. The source-only distribution boundary and external
prerequisites are also documented in README. This integration changes no native
allocation algorithm, scientific output, numerical capability or compatibility
claim. Origin lifecycle acceptance remains NOT RUN.
