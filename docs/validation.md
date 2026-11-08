# Evidence and limitations

This public tree is tested on Linux, Python 3.12. The default test runner runs both normal Python and `python -O`, using only generated synthetic inputs. Synthetic OOXML fixtures are package-logic tests, not independently Office-validated presentations.

A clean checkout on the recorded Linux/Python 3.12 environment runs 701 tests per Python mode: **498 pass and 203 explicitly skip**, with no failures. This includes the optional system liblz4 test, which skips on systems without liblz4 (497 pass, 204 skip). The previous 560 tests and all reviewed scientific modules are retained unchanged. The new binding and scalar packages add 27 and 114 synthetic tests respectively; their overlapping module/test names are deliberately isolated in separate subprocesses.

The original suites include:

- 118 preview/helper tests: 116 pass, 2 external real-file tests skip.
- 72 native tests: 14 synthetic tests pass, 58 exact-template tests skip because the external OLE is not included.
- 25 Ropj readback tests: 24 synthetic contract tests pass, 1 real-reader test skips without the explicit external runtime and synthetic fixtures.
- 47 bounded legacy-style tests: 33 synthetic/unit tests pass, 14 exact public-fixture tests skip without their separately supplied source files.
- 64 bounded legacy active-row tests: 32 source-only tests pass, 32 exact public-fixture tests skip without their separately supplied source file.

In a separate local verification copy, the exact public-source OLE fixture was supplied: all 72 native tests passed in normal and optimized Python. That external binary is not committed. The test environment used NumPy 2.3.5, lxml 6.1.1 and Pillow 13.0.0.

The 32 added layout/overlay tests use generated synthetic inputs. They cover approval bindings and stale-plan refusal, semantic anchor constraints, identity-coordinate pixels, opacity, source hashes and input/output refusals. They do not exercise an alignment editor, native guide generation/removal, palette application or a real Office client. See [layout approval](alignment-plan.md) and [visual verification](visual-layout.md#independent-verification-and-overlays).

The skipped native tests cover two-decoder agreement, nonnumeric-byte preservation, source guards, restoration, strict input handling, optimized-mode verification and publication failures. They can be enabled by providing the exact external fixture described in `native/README.md`. A passing decoder or byte comparison is not an application acceptance test.

The separately executed [Ropj experiment](../research/ropj_readback/README.md) passed all 25 tests in both normal and optimized Python with Ropj 0.3-7 and four external synthetic OPJ workbooks. The actual API returned 1,761 matching binary64 cells and 12 matching long-name/unit pairs. Its shared liborigin ancestry, mixed-column string rounding, absent graph interface and lack of OPJU support are explicit limits. The default source-only tests do not rerun that external evidence. No official Origin Viewer application ran in this investigation.

The [legacy-style research](../research/legacy_style_fields/README.md) separately ran all 47 tests with pinned public fixtures in both Python modes. Independent fresh-profile LabPlot application runs reproduced all eight source-field experiments and the separate title-font import diagnostic. Exact native bytes, numerical masks/bits, existing EMF cache and complete app-owned XML were checked. The default suite does not launch LabPlot or reproduce those external runs. Its source-only tests include exact whitespace differences, preservation-evidence tampering and runner path refusals. The title-font observation identifies a LabPlot import overwrite, not Origin behavior. Parameter-probe screenshots show label collisions in some cases, so these results do not establish finished layout quality or modern-format/Origin compatibility.

The [active-row research](../research/legacy_active_rows/README.md) separately passed all 64 tests in both Python modes with its pinned public template. Independent actual LabPlot reruns returned 14/98/100 active binary64 values and emitted 7/49/50 matching logical curve points. The complete saved-project comparison permits only the two data payload changes and separately checks their saved numerical bits. Source edits, manifests, input hashes and restoration are regenerated and checked rather than trusting preservation flags. Default tests do not run that application. Fifty allocated rows remain fixed; unproved range fields and inactive cells stay unchanged. Larger allocations, arbitrary row counts and Origin native save/reopen behavior remain unvalidated.

Before describing native output as editable and compatible, separately verify:

1. Actual Origin version and successful open without corruption warnings.
2. Worksheet data, stored-value versus UI-row alignment, X/Y bindings and graph inventory.
3. Requested changes and preservation of labels, axes, smoothing/fits, formulas, error bars and unknown objects.
4. Native redraw/recalculation, save, close and reopen.
5. PowerPoint activation, OLE refresh, save and reopen, including preview consistency.

**These application stages remain unvalidated and are not accepted as compatible.** Linux tests do not certify macOS. A complete OPJU writer, arbitrary graph serialization, resized compressed records and general native style editing are not implemented.

Work on isolated copies. Do not open untrusted embedded objects automatically. No Origin, Office or VM is launched by the public scripts. Reports, extracted data and reverse manifests may contain original content; review them before sharing.

## Modern read-only research supplements

`research/modern_binding_diagnostics` reproduces a pinned extractor's wrong-X and sheet-deduplication counterexample against 110 public hash-verified inputs. Its counts remain scanner candidates, not supported bindings. The default suite runs 32 synthetic tests with one explicit external-runtime opt-in skip; independent normal/optimized external proof runs matched the published counts.

`research/modern_owner_walk` follows bounded object ownership inside identified graph pages. The source modules match the independently reviewed parser revision; 49 package tests pass locally in both modes, including an optional existing-liblz4 test. That one test skips if the runtime is absent. Initial page discovery, opaque properties, complete dataset identities, and Origin acceptance remain outside scope. These supplements change no preview or native-writer APIs and include no private fixture data.

## Strict modern root/reference and scalar research supplements

[Modern native binding](../research/modern_native_binding/README.md) starts at the prolog and requires complete sequential dataset/page roots for its strict gate. The source-only suite passes 27 synthetic tests per mode. The separately reviewed public proof covers 167 pinned public sources: 101/110 original and 24/57 independent files have complete recognized dataset and page sections. The project tail is unvalidated in every case. Prefix counts from incomplete files are not full-file support. Numerical arrays, UI rows and special plot interpretation remain outside this reader's scope. A separate independent review passed 38 tests per mode; those review tests and external samples are not part of the default checkout suite.

[Modern native scalar](../research/modern_native_scalar/README.md) passes 114 synthetic tests per mode, including its intentionally frozen binding/ownership tests and synthetic native/CFB/PPT restoration and path guards. A separate independent review passed 49 tests per mode. Neither count is a new Origin application run.

Its four fields are type200 curve width, named axis-title font, axis tick font and axis line width, expressed only as raw stored integers. Every write is gated by the complete recognized dataset and page chains, exact owners, supported version profiles and external hashes. Only same-length one-to-one literal bytes can change; sparse controls, zero/nonzero patterns, repeat-backed edits and record resizing are excluded. Unknown project-tail bytes and all non-target native contents remain identical. Output files are new and exclusively created; native, CFB and PPT restoration requires independently retained anchors and reproduces the exact source bytes.

Historical public-source evidence records 101 complete-root inputs among 110 and 385 successful single-field trials: 82 curve-width trials plus 101 each for title, tick and axis-line fields. Nine inputs reject. A public four-field serial container trial preserves 516 other ZIP members, 319 other CFB streams, 102 OlePres streams and 152 media parts, with exact full-PPT restoration. These public corpus runs are recorded evidence, not repeated by the default synthetic runner. They do not decode or validate every scientific numerical value.

All four field classes have public real-source trials for CPYUA4.3268 build195. CPYUA4.3683 build132 has public title/tick/axis trials but type200 curve writing is disabled. CPYUA4.3811 build222 has generic synthetic shape coverage only in this public package. Native record layout does not establish modern Origin UI units. Origin opening, recalculation, save/reopen and PowerPoint activation/refresh remain **unvalidated, not accepted**; macOS writes remain unvalidated. The frozen public experiments record their own application stages as NOT_RUN. Caches intentionally remain stale.

The packages retain their reviewed MIT licenses and public-source attribution. Sources are CC-BY-4.0 Zenodo records and an Etalab 2.0 Dataverse dataset; source bytes, private fixtures and measured arrays are not bundled. Exact package snapshots are checked by their own inventories and the root source manifest. The binding inventory's historical candidate label describes that snapshot, not the current repository publication state. These supplements do not change older native/preview APIs, dependencies, permissions or historical evidence, and do not include the separate experimental direct-matrix codec.

## Legacy allocation expansion, application-specific research

`research/legacy_allocation` is an exact-fixture, explicit LabPlot-only allocation experiment. A separate reviewer rebuilt the observer and reran the original and 51/257/1024-row candidates in official LabPlot 2.12.1. The actual Column API, curve point signals and saved LML arrays matched every synthetic binary64 value; permitted native splices, unchanged graph/style bindings and exact rollback were independently checked. The current default source-only suite has 28 passes and 31 explicit fixture skips per mode; with the exact external fixture, all 59 tests pass. The later wrapper opt-in hardening regenerated byte-identical candidates and did not repeat those historical external application runs.

This does not verify Origin lifecycle compatibility. Unknown retained row-range fields and possible opaque dependencies remain blockers; native-safe export defaults to refusal. Native samples, binaries, full application saves and private data are excluded from the public source package.

## Multi-curve and declared custom-data source supplements

The two separate additions are explained in [packaging and provenance](native-data-packaging.md).
Per mode, the source-only additions run:

- Multicurve author tests: 48 discovered, 16 pass and 32 explicitly skip without
  external native fixture/application evidence.
- Multicurve independent guards: 13 explicit external-fixture skips. The separate
  bridge does not change any reviewed test or writer implementation.
- Custom adapter tests: 22 discovered, 3 source-audit tests pass and 19 native/app
  tests explicitly skip. The source audit validates the **current** public
  inventory; it is never bypassed because evidence is absent.
- Repository packaging/provenance checks: 10 pass. These hash-check every frozen
  scientific source and observer, current inventories and historical manifests,
  regenerate all six synthetic example inputs, check report hashes and reject
  explicitly selected but missing external inputs.

During packaging, the six native candidate hashes were also regenerated in
memory from the exact pinned public KDE fixture and matched the historical
application cases. No native binary was added to the repository. No LabPlot,
Origin, Office or VM was launched by this packaging validation. Historical app
reports are not claims that default checkout tests reran the application.

Multicurve remains one worksheet, 2/5/10 curves with independent X/Y and fixed
50-row bounds. The original one-entry B legend is unchanged. Custom input
remains one curve and 7/49/50 active rows in a fixed 50-row allocation, with
external CSV/declaration anchors, exact raw bytes and a full binary64 ledger.
Inactive 7/49-row template cells and all unrelated template contents remain.
Both default to refusal without an explicit research flag. Origin lifecycle
stages remain NOT_RUN, and macOS native writes remain unsupported.

Additional packaging checks with the separately supplied public fixture passed in both modes: all 13 independent multicurve guards; 29 multicurve author tests with 19 application-evidence skips; all 22 custom native/source/recorded-observation tests. The custom observation tests re-read existing actual LabPlot evidence, not a new app run. Exact suite counts and all 93 distinct added test IDs are recorded in [`NATIVE-DATA-VALIDATION.json`](../research/NATIVE-DATA-VALIDATION.json). The 13 reviewer guards and 10 packaging tests explain the 23 tests beyond the 48 author plus 22 custom tests; there is no duplicate discovery.
