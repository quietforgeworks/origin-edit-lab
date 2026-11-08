# Separate custom-data fixed50 research

Status: experimental public source-only research supplement. This is not an Origin-compatible release, stable skill, generic OPJ writer, or extension of the toy-only research workbench. The stable workbench and its frozen backends were not modified by this supplement. See [repository packaging notes](../../docs/native-data-packaging.md) for the current source inventory, historical evidence, and source-only test commands.

## Useful result

A genuinely non-toy, explicitly synthetic 50-row input was converted into the exact public legacy OPJ template and observed in the existing official LabPlot 2.12.1 application. All 100 worksheet values, saved LML doubles, and two actual XYCurve point-signal emissions match the input's binary64 conversions, including negative zero, decimal rounding, minimum-normal values and axis endpoints. Only the A/B data payloads changed in the saved application project; graph bindings/configuration were retained.

Fresh 7-row and 49-row runs passed too. These keep the template's unused native values physically present: 86 and 2 cells respectively. LabPlot displays those inactive cells as missing. This is not deletion, sanitization or proof of Origin's active-row semantics. The 50-row case replaces all A/B cells but still retains unrelated template data and objects.

Origin open, edit, update, recalculate, native save, close and reopen are all **NOT_RUN**. No preview image substitutes for native data. Screenshots are supplementary observations of the actual importing application, never the output model.

## Narrow supported input

- Exactly one explicit XY series, CSV header `A,B`, exactly 7, 49 or 50 rows. Each X and Y is a decimal string. No missing values, implicit X, masks, extra columns, new sheets, multiple curves, expansion, resampling or interpolation.
- Existing axes remain X [-5,55], Y [-0.1,1.1]. Input must satisfy the frozen finite normal binary64 contract. NaN, infinity, overflow, Origin missing sentinel, underflow, subnormal numbers and lossy integers refuse.
- Fractional decimal rounding to binary64 is allowed and disclosed per cell. Signed zero is preserved. Exact source CSV bytes and numeric lexemes remain in `raw.csv` and the full conversion ledger. OPJ cells hold converted binary64 values, not arbitrary-precision decimal text.
- A native no-op (all existing A/B values unchanged at 50 rows) refuses rather than producing a redundant candidate.
- Exact public template SHA-256 `ea50c9b97b063898f654a6189b30ca5d8be8b52ad4c9469b3934cd009185265a` only. Unknown bytes, graph configuration, bindings and all unrelated data remain unchanged. This is not a private-template sanitizer.

`declaration.json` has exactly three keys:

```json
{"schema":"custom-data-provenance-v1","declared_kind":"measured","statement":"Caller-supplied experiment data; measurement has not been independently verified."}
```

`declared_kind` may be `synthetic`, `measured` or `unspecified`. The declaration's original bytes are retained. Measured data is never relabelled synthetic. All declaration kinds remain caller-declared and independently unverified. The example measured declaration in `inputs/` exercises schema handling only; no measured experiment was collected in this research. Application research runs here use only known generated synthetic inputs.

## Commands

Use a new destination outside this package, or within its dedicated `runs/` directory, with existing stable parent directories. Linux only. Run in an isolated Python process:

```sh
python -I -B src/custom_data.py --accept-labplot-only-research generate \
  --template /absolute/path/to/exact-public-template.opj \
  --csv /absolute/path/to/input.csv \
  --provenance /absolute/path/to/declaration.json \
  --out /absolute/path/to/new-bundle
```

Capture SHA-256 of the original input CSV and declaration separately. Verification and recovery require those external anchors, not hashes copied from a possibly tampered bundle:

```sh
python -I -B src/custom_data.py --accept-labplot-only-research verify \
  --bundle /absolute/path/to/bundle \
  --expected-csv-sha256 ORIGINAL_CSV_SHA256 \
  --expected-declaration-sha256 ORIGINAL_DECLARATION_SHA256

python -I -B src/custom_data.py --accept-labplot-only-research recover \
  --bundle /absolute/path/to/bundle --out /absolute/path/to/new-recovery \
  --expected-csv-sha256 ORIGINAL_CSV_SHA256 \
  --expected-declaration-sha256 ORIGINAL_DECLARATION_SHA256
```

Recovery first verifies the entire bundle, then restores the exact public native original plus exact raw CSV and declaration into a new directory. It neither overwrites nor removes a candidate.

## API and evidence

Supported APIs in `src/custom_data.py`: `expected_artifacts`, `verify_artifacts`, `generate`, `verify`, `recover`. Each requires `research_opt_in=True` as a real Boolean. Verification/recovery require externally trusted CSV and declaration SHA-256 values. Supporting functions are implementation details.

The strict bundle contains exactly eight artifacts: `candidate.opj`, `rollback.opj`, `raw.csv`, `declaration.json`, `manifest.json`, `before.json`, `after.json`, `bundle.json`. Every byte is regenerated and compared. Extra/missing files refuse. Every JSON file is strict-parsed; duplicate keys and nonfinite constants refuse. The three vendored source files are exact unchanged copies of the frozen active-row implementation, and their hashes are checked before execution. Existing toy-only observer restrictions are neither altered nor bypassed; the new observer uses a separate declared-custom input gate.

See `CONTRACT.md`, `REPORT.md`, `evidence/`, and `application/verify_observation.py`. Raw native bundles, application profiles, screenshots, compiled observer and saved LML are local research artifacts, not source-distribution contents. `SOURCE-MANIFEST.json` and `audit_source.py` cover the current authored source and selected reports. The original reviewed manifest is retained unchanged at `review/HISTORICAL-SOURCE-MANIFEST.json`; it documents the pre-publication research snapshot, not the current distribution. An external trusted manifest digest is needed to detect coordinated source-and-manifest replacement.
