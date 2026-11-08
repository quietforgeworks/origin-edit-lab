# Evidence and limitations

This public tree is tested on Linux, Python 3.12. The default test runner runs both normal Python and `python -O`, using only generated synthetic inputs. Synthetic OOXML fixtures are package-logic tests, not independently Office-validated presentations.

A clean checkout runs:

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

**These application stages have not been run.** macOS is not certified by Linux tests. A complete OPJU writer, arbitrary graph serialization, resized compressed records and general native style editing are not implemented.

Work on isolated copies. Do not open untrusted embedded objects automatically. No Origin, Office or VM is launched by the public scripts. Reports, extracted data and reverse manifests may contain original content; review them before sharing.

## Modern read-only research supplements

`research/modern_binding_diagnostics` reproduces a pinned extractor's wrong-X and sheet-deduplication counterexample against 110 public hash-verified inputs. Its counts remain scanner candidates, not supported bindings. The default suite runs 32 synthetic tests with one explicit external-runtime opt-in skip; independent normal/optimized external proof runs matched the published counts.

`research/modern_owner_walk` follows bounded object ownership inside identified graph pages. The source modules match the independently reviewed parser revision; 49 package tests pass locally in both modes, including an optional existing-liblz4 test. That one test skips if the runtime is absent. Initial page discovery, opaque properties, complete dataset identities, and Origin acceptance remain outside scope. These supplements change no preview or native-writer APIs and include no private fixture data.
