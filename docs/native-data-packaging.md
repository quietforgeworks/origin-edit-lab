# Public source-only native-data supplements

This repository adds two separate experiments. It does not combine their native
algorithms or integrate them into a stable workbench:

- `research/legacy_multicurve`: independent X/Y bindings for 2, 5 or 10 curves,
  exactly 50 rows per curve, in the existing Book1 worksheet. All added curves
  clone the black style; the original single-entry B legend is retained.
- `research/legacy_custom_data`: one custom-declared X/Y series with 7, 49 or 50
  active rows inside a fixed 50-row allocation. CSV and provenance declarations
  are retained exactly; verification and recovery require separate original
  CSV/declaration SHA-256 anchors. Native cells store converted binary64, while
  the full ledger preserves original decimal lexemes and disclosed rounding.

Both use only the same exact public KDE fixture, identified in
[`NATIVE-DATA-PROVENANCE.json`](../research/NATIVE-DATA-PROVENANCE.json). Unknown
native metadata is retained. Origin open/edit/refresh/recalculate/native save,
close and reopen are **NOT_RUN**. Linux no-overwrite output is required; macOS
writes are unsupported. There is no generic template writer, OPJU writer,
new-sheet generator, private-template sanitizer or native-safe export.
For custom 7/49 rows, 86/2 inactive native cells remain. Unrelated template
content remains for all cases, including 50 rows.

## Public provenance and historical evidence

Every supplied CSV and every generated multicurve JSON contains project-authored
synthetic demonstration numbers, not user measurements. The custom CSV generator
uses written numerical stress literals plus modular arithmetic; the multicurve
generator uses Decimal arithmetic. `measured-declaration-example.json` is only a
schema example. It does not describe an experiment performed here.

The provenance matrix links each compact report/test transcript to its relevant
case IDs, the one public fixture, exact synthetic input hash and exact generated
candidate hash. All six synthetic inputs and native candidate hashes were
regenerated during packaging and matched the recorded cases. No native output
was added to the source distribution. Hashes of app-owned thumbnail/UI metadata
are historical public-case comparison evidence, not image pixels or private
user-file hashes. No raw application log, profile, native sample, full LML save,
screenshot, compiled observer or downloaded third-party implementation is added.

Earlier actual LabPlot 2.12.1 runs observed all claimed worksheet values, curve
bindings, passive XY point signals and saved LML arrays. Multicurve had a fresh
independent application rerun. The custom reviewer revalidated existing actual
observations but did not rerun the application. **Packaging tests did not rerun
LabPlot or Origin.** Historical `evidence/` and `review/` logs retain their original
pass counts; they must not be presented as clean-checkout results or as execution
attestations. LabPlot's own LML save does not verify native OPJ/OPJU save.

## Integrity inventories and packaging changes

All reviewed `.py`, `.cpp`, `.inc` and `.sh` files, including tests, remain
byte-exact. The three custom vendor files retain their original hard-pinned
hashes. Changes are only distribution documentation, three relative output-path
redactions and separate repository integration helpers.

- Multicurve `PACKAGE-INVENTORY.json` is the unchanged historical reviewed
  inventory, SHA-256 `f6548e6f35769fd9884bf2a86020ee1de5c8f51b5bf694a2c64e3e3dd64e08f1`.
  `CURRENT-INVENTORY.json` describes this distribution instead. The README adds
  current scope and fixes an unsupported flag in a verifier example; no verifier
  code changes.
- Custom `review/HISTORICAL-SOURCE-MANIFEST.json` is the unchanged 45-file research
  manifest, SHA-256 `3b56217e1b537a61bcc6726b7110114bde0ecfe40d83fc0acb48000b6ef94645`.
  The new `SOURCE-MANIFEST.json` describes current authored sources/reports and
  is verified by the unchanged `audit_source.py`. Its companion SHA-256 file is
  a convenience checksum; obtain the trusted digest from the publication record
  or a separately verified outer manifest for an external integrity anchor.
- Custom README/CONTRACT/REPORT now distinguish public source distribution from
  the earlier local research runs. The three `generation-custom*.json` reports
  change only `output` from a local absolute path to `runs/customN`.
- Custom independent-review text and compact logs are added under `review/`.
  They describe the historical source snapshot. They are covered by the outer
  package inventory, not by the narrower authored-source auditor.
- `research/run_native_data_tests.py` supplies explicit optional-fixture skips
  without changing frozen tests. A selected but missing fixture/evidence path
  is an error. Source audit failures never become skips.
- `research/verify_native_data_provenance.py` regenerates demonstration inputs
  and optionally checks the six candidate hashes against the exact public
  fixture entirely in memory. It writes no native files and launches no app.
- Root README, validation and third-party notes describe the supplements; the
  test runner preserves every previous suite and adds the new suites.

The repository-wide `SOURCE-PACKAGE-MANIFEST.json` records every distributed
file except itself and its companion checksum. Its companion `.sha256` contains
its digest. The inventory is an integrity record, not an Origin acceptance test.

## Reproduce source-only checks

From the repository root, with the dependencies in `requirements.txt` installed:

```sh
python -B run_tests.py
python -B research/verify_native_data_provenance.py
python -B research/legacy_custom_data/audit_source.py \
  --expected-manifest-sha256 TRUSTED_CURRENT_CUSTOM_MANIFEST_SHA256
```

The main runner exercises normal and optimized Python. It generates synthetic
preview fixtures locally, skips unavailable external native/application cases
explicitly, and never downloads a fixture or launches an application.

To enable only the exact-public-fixture tests and candidate provenance checks:

```sh
export ORIGIN_PUBLIC_FIXTURE=/absolute/path/to/exact-public-template.opj
export CUSTOM_TEMPLATE="$ORIGIN_PUBLIC_FIXTURE"
python -B run_tests.py
python -B research/verify_native_data_provenance.py --fixture "$ORIGIN_PUBLIC_FIXTURE"
python -O -B research/verify_native_data_provenance.py --fixture "$ORIGIN_PUBLIC_FIXTURE"
```

The frozen multicurve app-verifier tests expect separately generated actual
application evidence in that package's documented local paths. The custom
5-test observation suite can instead use `CUSTOM_EVIDENCE_ROOT`, a separate
research directory holding `application/results50` and `runs/custom50`. This
revalidates recorded app files and does not launch the app. Never copy that
research directory into a public commit. Direct custom `unittest discover`
remains the historical full-evidence command and intentionally requires its
original external files; use the bridge/main runner for a source-only checkout.

The unchanged custom auditor's result field `public_publication: false` means
that the read-only audit does not publish anything. It is not a claim that this
source distribution is private. Historical review receipts retain the field as
recorded; current distribution status is described here, not inferred from it.

## Exact CSV bytes in Git

The three `research/legacy_custom_data/inputs/custom7.csv`, `custom49.csv` and
`custom50.csv` files intentionally exercise quoted numeric lexemes and CRLF
serialization. Root `.gitattributes` names only those exact paths and sets
`-text`, so Git preserves their original bytes instead of normalizing line
endings. Their whitespace attribute retains `blank-at-eol`, `blank-at-eof` and
`space-before-tab`, adding only `cr-at-eol` to treat the CR in CRLF as a line
terminator. Other files do not receive this exemption. Synthetic input hashes,
frozen scientific modules and original source manifests are unchanged.

The packaging check used an isolated temporary Git repository and real index,
without global configuration changes. It checked cached attributes and indexed
CSV byte identity even with command-local `core.autocrlf=true`; staged
`git diff --check` passed. Negative controls still rejected trailing spaces,
blank lines at EOF and space-before-tab, and confirmed the CR exemption did not
apply to an unlisted CSV. The controls changed only temporary Git index objects.

The complete Git attribute, indexed-byte and negative-control receipt is
[`NATIVE-DATA-GIT-VALIDATION.json`](../research/NATIVE-DATA-GIT-VALIDATION.json).
