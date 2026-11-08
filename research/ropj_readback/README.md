# Ropj legacy-workbook readback

Small, read-only acceptance harness for **externally supplied synthetic OPJ workbooks**. It calls the real CRAN Ropj API, then checks all returned numeric cells as little-endian binary64 bytes and checks column long names/units against the external CSV/schema.

It does not write OPJ, install/download software, run Origin scripts, upload files, or publish anything. Supply your own official R/Ropj installation and synthetic fixtures. Python 3.9+ and Ropj **0.3-7** are required; other Ropj versions stop explicitly instead of silently inheriting this result.

## Historical result and limits

- Four synthetic workbooks with 7, 161, 162 and 257 rows, each with three columns: **1,761 double values and 12 column long-name/unit pairs matched**. Signed zero and ordinary decimals were preserved. Column commands were empty and source hashes stayed unchanged.
- Ropj and LabPlot share **liborigin ancestry**. This is another actual software/API execution, not an independently designed parser.
- Ropj returned character vectors for a separate public mixed-type fixture. Its current importer formats numeric members of mixed columns using C++ `std::to_string`, normally **six fractional decimal places**, which can lose precision. This harness refuses text/mixed columns and never converts those strings back into an apparent numeric pass.
- Ropj's return interface does not expose original graphs and does not support the modern OPJU format. No line width, font, layout, curve binding/range, or native graph rendering is verified here.
- Official Origin Viewer was obtained during separate research but **never executed**: Wine's local IPC socket was denied in that environment. Neither this result nor a future Viewer pass proves full Origin editor update/save/reopen compatibility.
- Empty returned column commands are a narrow observation, not a complete audit of every possible Origin auto-execution hook. The readback only returns command strings; it does not evaluate them.

See `facts.json` and `sources.json` for compact evidence boundaries and official sources. No vendor binary, license text, native fixture, or research dataset is included.

## External fixture contract

Each explicitly named case directory must contain `workbook.opj`, `raw.csv`, and `schema.json`. Use one workbook, one worksheet, all-double columns, and no missing values. A CPYA prefix is only a scope check; the real reader must still parse the file. Do not rename OPJU files to OPJ.

The CSV has a header row and rectangular finite decimal data. The schema supplies `source_kind: "synthetic_demo"`, `numeric_mode: "binary64"`, an ASCII workbook short name in `book`, and ordered `columns`, each containing nonempty printable ASCII `header` and `unit` strings. CSV headers must match that order. Column metadata must return exactly `header + CRLF + unit`, with an explicitly empty command string.

Expected floating-point values are generated at run time from the supplied decimal tokens with Python's binary64 conversion, **not mathematical arbitrary-precision decimal equality**. Nonzero underflow, nonfinite tokens, and integers that would change during conversion are refused. Maximums: 32 MiB per input file, 65,535 rows, 256 columns, and one million cells. Files and case directories cannot be symlinks. The synthetic declaration is user-supplied, not an automated proof of data ownership or provenance.

No expected research values or OPJ writer are embedded. Use synthetic workbooks prepared by an authorized external writer and retain their corresponding CSV/schema. Unit-test values are created openly from row index `i`: X=`i`, Y=`(-1)^i * (i+1)/10`, with Y at row zero set to negative zero. Their fake OPJ header stub is never sent to Ropj.

## Run

Configure your existing R package-library environment so that the selected Rscript finds Ropj 0.3-7. No install or auto-discovery is performed. The executable and fixture paths are explicit inputs:

```sh
python verify.py --rscript "$RSCRIPT" --fixtures "$SYNTHETIC_FIXTURES" \
  --case decimal7 --case decimal161 --case decimal162 --case decimal257 \
  --out readback-run
```

`readback-run` must be new, its parent must exist, and it must be outside the fixture directory. Each accepted case records reader identity, exact readback, metadata, input hashes, and verification. `summary.json` appears only after all cases pass. If something fails, the process exits nonzero and may leave partial local diagnostics, **not a successful result**. These generated files can contain supplied fixture data and local runtime diagnostics; review them before sharing. Nothing sends them anywhere.

## Test

```sh
python -m unittest -v
python -O -m unittest -v
```

Without explicitly supplied runtime/fixture environment variables, the real-reader test is **skipped**, not passed. The source-only contract tests remain active, including under `-O`.

```sh
export ROPJ_TEST_RSCRIPT="$RSCRIPT"
export ROPJ_TEST_FIXTURES="$SYNTHETIC_FIXTURES"
# Optional: comma-separated immediate case names; the four names above are default.
python -m unittest -v
python -O -m unittest -v
```

Tests do not download dependencies or create native OPJ. `testsummary.json` records both source-only and real-runtime runs. Dependency licenses remain with their upstream packages; this directory does not add or change the receiving repository's license.
