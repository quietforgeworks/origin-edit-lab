# Modern binding counterexamples, read-only

Audited research supplement, **not a general Origin parser, binding resolver, or writer**. This source-only package reproduces a contradiction between explicit graph-selector candidates and the actual extraction result of a fixed quantized revision. It changes no native file and makes **no Origin open/recalculate/save/reopen or PowerPoint acceptance claim**.

## What was reproduced

The 110 SHA-256-pinned public inputs comprise 106 CPYUA `Contents` streams from the Heliox PowerPoint in [Zenodo record 20155927](https://zenodo.org/records/20155927), three OGGU files from [Recherche Data Gouv](https://doi.org/10.57745/W0SEAA), and one OPJU from the same Zenodo record.

- 4,738 named **descriptor candidates** and 2,824 recognized immediate-DataPlot **graph-anchor candidates**. All positive graph selectors are in candidate range and their X agrees with the Y descriptor's observed field82. This is a measured correlation, not a format definition.
- **313 explicit property-ID candidates: 295 in five files with complete candidate coverage, plus 18 in three partial maps.** Complete candidate coverage means exactly one matching property ID per scanned descriptor candidate. It does not prove the dataset-list grammar or sheet ownership.
- The pinned ID table returns only 279 of the 295 IDs in the five complete-candidate files. It returns none of the 18 IDs in the three partial-map files. An empty pinned table does not mean records are absent.
- Neither recognizer finds worksheet properties in the remaining 102 inputs. Unsupported encodings may still be present.
- Four other decoded-size descriptor-like candidates were rejected for empty/nontext names. Byte scanning is not a sequential dataset-list parser, even when a candidate looks valid.

The minimal case is public `oleObject105.Contents.bin`. Its 28 property IDs exactly cover 28 descriptor candidates. Its three explicit graph candidates preserve three different sheet-suffixed descriptor identities, but have one common book/short-Y key. All three explicit graph X selectors differ from worksheet X partners. Calling the **actual pinned `extract_curves_by_id`** returns one row, whose X/Y does not match any explicit graph candidate. This demonstrates worksheet-X substitution and loss of sheet-distinguished identities in that pinned extractor. It does not assert how Origin renders the file.

All source identities, licenses and hashes are in `public_sources.json`. `expected_counts.json` contains only measured counts. `evidence/observed_counts.json` is a fresh all-input run of this portable package, not a copied raw audit dump.

## Run the self-contained tests

Python 3.10+; the package's own code and synthetic tests use only the standard library. Tested on Python 3.12. No native fixtures, third-party source, binaries, downloads or installs are required:

```sh
python -B -m unittest discover -s tests -v
python -B -O -m unittest discover -s tests -v
```

The external proof test explicitly skips unless both external roots are provided. The tests cover bounded sparse decoding, malformed/truncated records, exact and partial candidate coverage, duplicate/out-of-range IDs, synthetic IDs above 255, preserved unknown slots and sheet suffixes, X=0, descriptor/X disagreements, source hash mismatch, runtime hash mismatch, output overwrite refusal and namespace cleanup. Passing tests under `-O` does not remove any safety check: production contracts use explicit exceptions rather than `assert`.

## Reproduce with public files you already have

Obtain the public inputs and the fixed quantized source separately, in an authorized environment. This package does not fetch or install them. Extract the named CFB `Contents` streams without changing their bytes; do not pass whole OLE containers. For the standalone files, use the manifest's public basename. The three Dataverse file IDs and original filenames are listed in the manifest.

Supply an existing directory containing `quantized/io/` from revision `431deeb7c8473503970ca56b78cc1678f57d373d`. `--quantized-root` points to the **quantized directory**, not its parent. Existing NumPy is required by the pinned modules. Python and NumPy are external runtime dependencies and are not bundled, installed or newly approved by these instructions.

```sh
python -B prove_public.py \
  --public-root /absolute/path/to/public-inputs \
  --quantized-root /absolute/path/to/src/quantized \
  --case minimal --out /absolute/path/to/new-minimal-counts.json

python -B -O prove_public.py \
  --public-root /absolute/path/to/public-inputs \
  --quantized-root /absolute/path/to/src/quantized \
  --case all --out /absolute/path/to/new-all-counts.json
```

`--public-root` may repeat for separately stored collections. Every requested basename must exist in exactly one root. There is no recursive search, private-file mode, guessed local directory or fallback runtime. `minimal` requires only the one public Contents file; `all` requires the 110 manifest entries. Other files in the directories are not read.

All source hashes are verified before processing, checked again when read, and rechecked after processing. Six exact source modules are verified from `quantized_sources.json` before any execute. The loader executes the already-verified bytes, does not run package initializers, refuses an already-imported quantized namespace and removes its own modules afterward. It does not alter the pinned code. Use a fresh Python process and trusted installed NumPy. Hash matching identifies code; it is not a security audit or authorization to execute otherwise untrusted software.

Output is an exclusively created JSON file. Existing output paths and symlinks are refused. No native file is opened for writing. Reports contain public source identities and counts only, with no decoded names, measurement values, native record dumps, source positions or local paths.

To opt the test suite into the minimal external proof, set both `MODERN_BINDING_PUBLIC_ROOT` and `MODERN_BINDING_QUANTIZED_ROOT` to those same explicit directories. The test invokes the CLI in a fresh process, with `-O` when the suite itself is optimized. It never downloads a missing prerequisite.

## Fail-closed boundary

- Descriptor/anchor scans remain **candidates**, including when a property map covers all candidates. The sparse recognizer is not a complete typed dataset-list parser. `require_supported_binding` always rejects promotion to supported binding status.
- A candidate's graph X and Y are checked independently. Worksheet designations never replace graph X. **X=0 stays absent**; it must not become column A or Python's last-element index. The public modern corpus contains no X=0 example; this package tests that rule synthetically, without claiming modern plot-mode validation.
- Keep full sheet-suffixed identities and every typed or unknown stream slot. Do not renumber after numeric decode failures, missing cells, unsupported designations, unknown records, matrix/function records or other occupants.
- Complete modern typed framing, real sheet/layer ownership, matrices, functions, placeholders/destroyed slots, deleted-dataset holes, cross-book X, arbitrary encodings/names, plot modes and high-ID modern fixtures remain unproved. Synthetic high-ID tests do not establish real-file coverage.
- The immediate-DataPlot recognizer misses anchors with intervening metadata. Its graph count is not exhaustive. A pinned row lacking a scanned match outside the minimal case is not, by that fact alone, proved erroneous.
- No numeric array is decoded by this package. Dataset capacity, active rows, plot-specific row limits, continuation runs, missing cells, masks and complete numeric envelopes remain outside scope. Do not infer row extent from the count of decoded values.
- No native mutation, fit, recalculation, cache update, Origin execution, PowerPoint activation or application acceptance occurs here.

## Source evidence and licensing

See `SOURCES.md` for official liborigin context and the exact pinned quantized source references. The official reader's legacy stream-index semantics support the distinction between stream identity and worksheet layout, but do not establish a complete modern compressed grammar.

Newly authored code/reporting uses the project's MIT license, included unchanged in `LICENSE`. The external Zenodo sources retain CC-BY-4.0; Dataverse retains Etalab-2.0; quantized retains Apache-2.0; LabPlot/liborigin retain their source licenses. No third-party source, native sample bytes, decoded raw records, runtime, binary, private input or local research path is included. Do not commit reproduction inputs or locally generated reports without reviewing their contents and rights.
