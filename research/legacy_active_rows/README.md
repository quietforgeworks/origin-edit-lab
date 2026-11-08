# Bounded native OPJ active-row experiment

Audited research supplement, not stable Origin support. It preserves one exact public legacy OPJ template's 50 allocated rows while substituting toy X/Y values and its documented dataset active end row. Only tested counts **7, 49 and 50** are accepted. **51/257 expansion is refused.**

The unmodified official LabPlot 2.12.1 application independently read every active binary64 value and emitted precisely the corresponding 7/49/50 curve logical points, all bit-exact. Whole saved-project differences were limited to the two column payloads. See `evidence/REPORT.md`, `evidence/compact-verification.json`, `evidence/field-evidence.json` and `evidence/REVIEW.md` for exact scope, provenance and limitations.

Origin reopen/update/recalculate/save behavior remains **NOT RUN**. The unresolved graph and worksheet range-like fields stay untouched. Inactive raw template cells are retained, so this is not a sanitizer or a general OPJ writer.

The retained toy-data application observations can be rechecked without any OPJ file or app runtime:

```sh
python verify_synthetic_observations.py
python -O verify_synthetic_observations.py
```

This only checks captured numerical/curve-signal evidence, not a fresh application run or the full saved project.

## External prerequisites, not included

- Exact fixture: [KDE LabPlot public origin8_test_tree_import.opj](https://github.com/KDE/labplot/blob/0bd2e4094e92e74052ec161022d4e60aeb7605cd/tests/import_export/Project/data/origin8_test_tree_import.opj).
- SHA-256: `ea50c9b97b063898f654a6189b30ca5d8be8b52ad4c9469b3934cd009185265a`.
- For real-app replication: independently obtained official LabPlot 2.12.1 runtime and compatible Qt development headers. `LABPLOT_RUNTIME_ROOT` points to a directory with `squashfs-root/` and `debian-runtime/` arranged as in the experiment; the scripts do not download/install any software. Provenance hashes are in the evidence report.

## Patcher and tests

```sh
export ORIGIN_PUBLIC_FIXTURE=/absolute/path/to/origin8_test_tree_import.opj
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -v
python native_active_rows.py --template "$ORIGIN_PUBLIC_FIXTURE" --csv candidates/raw7.csv --out candidates/run7
```

The output directory must not already exist. The patcher emits the candidate, unchanged raw CSV, conversion ledger, structural inspection and byte-exact source rollback. No third-party code is needed for the Python patcher. It uses the standard library. Without the separately provided fixture, source-only numerical/input tests pass and fixture tests explicitly skip; the included full local logs used the actual pinned fixture.

To recreate the full set, choose a clean copy without preexisting generated directories, run `make_cases.py`, build the local observer, then run its `run.sh` for `original`, `active7`, `active49`, `active50`. `verify_application.py` checks app-owned outputs, including the actual curve's passive `pointsUpdated` signals, not an OPJ re-parser or displayed rounded text.

```sh
export LABPLOT_RUNTIME_ROOT=/absolute/path/to/verified-labplot-runtime
python make_cases.py
bash application/build.sh
bash application/run.sh original "$ORIGIN_PUBLIC_FIXTURE"
for n in 7 49 50; do
  bash application/run.sh active$n candidates/generated$n/candidate.opj
done
python verify_application.py --output-dir new-verification-reports
python -O verify_application.py
```

A deliberately timed-out app exit at 11 seconds is expected after its completed Save As and captures. Each run uses separate HOME/XDG/temp profiles. The helper does not mutate imported column data or issue a recalc command. The runner accepts only original/active7/active49/active50 and the published toy CSV; it refuses existing cases/profiles and path-like identifiers. `LABPLOT_RUNTIME_ROOT` must be set explicitly before building or running.

## Package boundary

Only newly authored project code/reporting, test logs, toy CSV and compact evidence are included. Native fixtures, original fixture payload fragments, app screenshots/saves, binaries and third-party source implementations are excluded. Do not commit generated `candidates/` output or `application/results/` when reproducing this work. Do not interpret the source-to-LabPlot success as Origin acceptance.

## License

The authored material uses the project's existing MIT license, included unchanged in `LICENSE`. The external KDE fixture, LabPlot, liborigin and Qt retain their own licenses and are not bundled. Distribution of separately built/linked software must comply with those licenses.
