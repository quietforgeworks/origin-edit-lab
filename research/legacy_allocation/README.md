# Legacy OPJ allocation expansion: LabPlot-only experiment

This source-only research package is not stable Origin support. One pinned public legacy OPJ
has been resized from 50 allocated X/Y cells to **51, 257 and 1024 cells**.
Unmodified official **LabPlot 2.12.1** independently imported and drew all three.
Its public Column API and passive XYCurve signal returned every binary64 value
bit-for-bit, including negative zero beyond the old 50-row boundary.

**Origin-safe export remains blocked.** The default API/CLI refuses to generate
a file. The explicit `--labplot-only-research` option produces experimental
candidates with unresolved native safety, not files certified for Origin.
Unknown worksheet/curve range-like fields stay `(0,50)` and are never guessed.
Origin reopen, update, recalculate, save and native save-cycle reopen were not run.

See `REPORT.md` for the boundary proof, real-app observations and exact blocker.
The recorded experiments did not change stable code, user PPT files, Mac or VM.
No new unknown software was downloaded or executed during those experiments. Only the public fixture and toy CSV
were used; no data was digitized, fitted, smoothed or downsampled.

## External prerequisites

- [Exact public KDE fixture](https://github.com/KDE/labplot/blob/0bd2e4094e92e74052ec161022d4e60aeb7605cd/tests/import_export/Project/data/origin8_test_tree_import.opj)
- Fixture SHA-256: `ea50c9b97b063898f654a6189b30ca5d8be8b52ad4c9469b3934cd009185265a`
- For fresh app replication: the separately verified official LabPlot 2.12.1
  runtime, compatible Qt headers and compiler. `LABPLOT_RUNTIME_ROOT` points to
  the existing `squashfs-root/` and `debian-runtime/` parent. Scripts do not fetch
  or install software. The app executable/importer hashes are pinned.

```sh
export ORIGIN_PUBLIC_FIXTURE=/absolute/path/to/origin8_test_tree_import.opj
export LABPLOT_RUNTIME_ROOT=/absolute/path/to/verified-labplot-runtime
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -v
```

59 tests pass with the exact fixture. Without it, 28 pass and 31 explicitly skip.
The patcher and tests use Python's standard library; the observer needs Qt.

## Regenerate the research

Use a fresh directory without generated candidates, application results or
profiles. The retained CSV files are hash-pinned. Their convenience generator
also checks exact hashes and refuses any platform/libm difference.

```sh
python make_cases.py --labplot-only-research
bash application/build.sh
bash application/run.sh original "$ORIGIN_PUBLIC_FIXTURE"
for n in 51 257 1024; do
  bash application/run.sh expanded$n candidates/generated$n/candidate.opj
done
python verify_application.py --output-dir fresh-verification
python -O verify_application.py
```

The app's planned 11-second timeout occurs after Save As and captures. Each run
uses private HOME/XDG/temp profiles and a read-only private snapshot. The observer
does not edit columns, invoke recalc or inject curve points. LabPlot's Save As
writes LML, not OPJ. Screenshots are supporting evidence, not numerical proof.

Direct generation requires an explicit research flag:

```sh
python native_allocation.py --template "$ORIGIN_PUBLIC_FIXTURE" \
  --csv candidates/raw257.csv --out fresh257 --labplot-only-research
```

Both generation CLIs require `--labplot-only-research`. The toy wrapper
`make_cases.main()` also requires literal `research_only=True`; its default
rejects before reading the fixture environment variable, accessing inputs or
creating outputs. A refused CLI invocation leaves no import bytecode behind.
The native patcher retains its separate default refusal. Candidate output
is atomic and no-overwrite. A manifest, exact raw CSV copy, before/after structure
inspection and byte-exact original rollback accompany each candidate. The
rollback helper is a recovery operation, not a candidate-validation oracle;
`verify_source_artifacts.py` regenerates and compares complete artifacts.
All existing input/output path components, including ancestors, are checked
for symlinks; runner input/profile/runtime ancestors are checked too. These
checks assume trusted, stable ancestor directories and are not a sandbox
against concurrent ancestor substitution. The final destination's atomic
no-overwrite guard also rejects a directory raced into that exact destination.
The case-generation wrapper checks paths before any read/write and creates
missing toy CSV exclusively, so it cannot overwrite a file raced into place.

## Current source-only contents and provenance

This directory is the reviewed **source-only package**, not the original
fixture-bearing research workspace. It contains authored Python/C++/shell
source, tests, documentation, the MIT license, three hash-pinned synthetic CSV
files, and compact evidence reports/logs. See `review/REVIEW.md` for independent
review and the integration hardening note.

It excludes native fixtures, generated candidates/manifests/rollbacks, full
before/after dumps, `application/results`, profiles, screenshots, application
saves/binaries, original payload fragments and third-party implementation.
The full source-bearing application comparison reports are not bundled.
Regenerating the research locally creates excluded artifacts; keep those local
and do not add them to a source-only distribution. External prerequisites retain
their own licenses. This is not a private-template sanitizer.

`PACKAGE-INVENTORY.json` records the current included files and hashes, excluding
itself to avoid a circular hash. `evidence/source-freeze-manifest.json` is
unchanged historical evidence of the earlier author freeze, before public
packaging and integration hardening. It is not the current package inventory;
its old hashes, test counts and recorded paths are preserved rather than
rewritten. Historical logs describe the earlier runs; the new wrapper checks
are recorded in `review/evidence/post-integration-*.log`.
