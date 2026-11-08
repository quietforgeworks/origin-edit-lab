# Evidence and limitations

This initial public tree is tested on Linux, Python 3.12. The default test runner runs both normal Python and `python -O`, using only generated synthetic inputs. Synthetic OOXML fixtures are package-logic tests, not independently Office-validated presentations.

A clean checkout runs:

- 86 preview/helper tests: 84 pass, 2 external real-file tests skip.
- 72 native tests: 14 synthetic tests pass, 58 exact-template tests skip because the external OLE is not included.

In a separate local verification copy, the exact public-source OLE fixture was supplied: all 72 native tests passed in normal and optimized Python. That external binary is not committed. The test environment used NumPy 2.3.5, lxml 6.1.1 and Pillow 13.0.0.

The skipped native tests cover two-decoder agreement, nonnumeric-byte preservation, source guards, restoration, strict input handling, optimized-mode verification and publication failures. They can be enabled by providing the exact external fixture described in `native/README.md`. A passing decoder or byte comparison is not an application acceptance test.

Before describing native output as editable and compatible, separately verify:

1. Actual Origin version and successful open without corruption warnings.
2. Worksheet data, stored-value versus UI-row alignment, X/Y bindings and graph inventory.
3. Requested changes and preservation of labels, axes, smoothing/fits, formulas, error bars and unknown objects.
4. Native redraw/recalculation, save, close and reopen.
5. PowerPoint activation, OLE refresh, save and reopen, including preview consistency.

**These application stages have not been run.** macOS is not certified by Linux tests. A complete OPJU writer, arbitrary graph serialization, resized compressed records and general native style editing are not implemented.

Work on isolated copies. Do not open untrusted embedded objects automatically. No Origin, Office or VM is launched by the public scripts. Reports, extracted data and reverse manifests may contain original content; review them before sharing.
