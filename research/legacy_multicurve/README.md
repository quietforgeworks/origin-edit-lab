# Independent XY curves: LabPlot-only native-record experiment

This source-only research grows one public legacy OPJ graph from one curve to
**2, 5 or 10 independently bound XY curves**, with 50 explicitly supplied pairs
per curve. Official LabPlot 2.12.1 imported, drew and saved all tested values and
source identities exactly. The last case has A/B through S/T in existing Book1.
This does **not** create new sheets or establish Origin compatibility.

**Origin-safe export is deliberately refused by default.** The explicit
`--labplot-only-research` flag permits experimental legacy OPJ candidates while
unknown native object/count metadata and Origin lifecycle remain unverified.
No OPJU writer, hidden-field repair, template sanitizer, fitting, digitizing or
preview replacement is offered. The existing single-entry B legend and cloned
black styles are retained; this is not a finished publication-quality figure.

See [REPORT.md](REPORT.md) for historical application evidence and unsupported fields, and [repository packaging notes](../../docs/native-data-packaging.md) for current inventories and source-only tests.

## External inputs

Nothing is downloaded or installed by these scripts.

- Exact [public KDE fixture](https://github.com/KDE/labplot/blob/0bd2e4094e92e74052ec161022d4e60aeb7605cd/tests/import_export/Project/data/origin8_test_tree_import.opj).
- Fixture SHA-256: `ea50c9b97b063898f654a6189b30ca5d8be8b52ad4c9469b3934cd009185265a`.
- For actual-application replication: separately verified official LabPlot
  2.12.1 runtime and Qt headers/compiler. `LABPLOT_RUNTIME_ROOT` contains the
  existing `squashfs-root/` and `debian-runtime/`. The runner pins the executable
  and importer library hashes and uses private HOME/XDG/temp directories.

## Reproduce in a fresh source copy

```sh
export ORIGIN_PUBLIC_FIXTURE=/absolute/path/to/origin8_test_tree_import.opj
export LABPLOT_RUNTIME_ROOT=/absolute/path/to/verified/runtime
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -v
for n in 2 5 10; do
  python make_cases.py --template "$ORIGIN_PUBLIC_FIXTURE" --count "$n" --labplot-only-research
done
bash application/build.sh
bash application/run.sh original "$ORIGIN_PUBLIC_FIXTURE"
for n in 2 5 10; do
  bash application/run.sh "curves$n" "candidates/curves$n/candidate.opj"
  python verify_source.py --case "curves$n" --input "candidates/curves$n/candidate.opj"
  python verify_application.py --count "$n"
  python -O verify_application.py --count "$n"
done
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -v
```

48 tests pass with the exact fixture and real-app evidence. Without app evidence,
19 app-observation tests explicitly skip. Without the fixture, 13 native tests
also explicitly skip. The remaining 16 tests run with only Python's standard
library. Actual-app tests validate observer and saved-file evidence, not Origin.
The app's planned 11-second timeout happens after Save As and observations;
LabPlot saves LML, **not OPJ or OPJU**.

The toy generator uses exact Decimal arithmetic and labels all data synthetic.
A direct research call accepts only the strict explicit-XY synthetic JSON schema:

```sh
python native_multicurve.py --template "$ORIGIN_PUBLIC_FIXTURE" \
  --raw candidates/synthetic2.json --out a-fresh-output-directory \
  --labplot-only-research
```

Every X and Y array must contain exactly 50 numeric strings. Missing X, unequal
lengths, missing cells, NaN/Infinity, Origin's missing sentinel, overflow,
underflow/subnormals and lossy integer conversions fail closed. Fractional
conversion to binary64 is recorded with the original lexeme and exact rounding
error. Signed zero is preserved. Raw JSON is copied unchanged alongside each
candidate. Output never overwrites an existing destination.

Path checks reject symlinks and parent traversal; regular-file reads are bounded
and reject FIFO inputs. Preflight and final publication assume trusted, stable
ancestor directories. They are not a defense against concurrent ancestor swaps.
Final destination publication uses Linux `renameat2(RENAME_NOREPLACE)`.

## Distribution boundary

The public source package contains authored source/tests/docs and compact
synthetic-result evidence only. Native fixture/candidates/rollbacks, original
payload fragments, screenshots, LML saves, application binaries, compiled
observers, profiles and third-party implementation are excluded. Running the
experiment produces fixture-bearing local artifacts: **do not publish the entire
working directory**. External fixture/application/source retain their licenses.
No private user files were read, no Mac/VM was accessed, no new unrecognized
software was downloaded or run, and no stable skill or published repository was
changed by those original experiment runs. This repository distributes only the
reviewed authored sources and compact evidence described above.
