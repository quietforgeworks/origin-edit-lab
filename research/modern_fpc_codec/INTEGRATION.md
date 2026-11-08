# Source-only repository integration

This directory integrates the frozen, independently reviewed numeric-stream
research package into Origin Edit Lab. It does not connect the codec to any
native writer or change an existing CLI. Dataset/container writeback research
is separate and is not included. Origin and PowerPoint lifecycle validation
remain **NOT_RUN**.

## Exact source selection

- Repository baseline: `5cc89ef6f7bd4509a4f5ea80ef447008e98aba22`.
- Licensed upstream archive: `origin-modern-fpc-source-only-20261108-licensed.tar.gz`.
- Archive SHA-256: `cae754eb202181857b6e5294ae876697260cc16d3c73c8d5d33bff8e334dfb05`.
- Archive size: 1,553,840 bytes, containing 37 regular files.
- All 35 retained upstream files are byte-identical. `MANIFEST.json` from the
  archive is renamed to `UPSTREAM-MANIFEST.json`; the current directory has a
  separate current `MANIFEST.json`.
- The two excluded upstream members are a redundant source patch and the full
  optimized public-corpus JSON. Their exact original sizes, hashes and exclusion
  reasons are retained in `INTEGRATION.json` and the upstream manifest.
- The optimized report is losslessly reconstructable from the complete normal
  report by replacing its sole `"optimize": 0` with `"optimize": 1`. Only byte 735
  changes, from ASCII 0 to ASCII 1. The verifier checks the reconstructed bytes
  against the original optimized report SHA-256. This saves 5,991,732 duplicate
  bytes without losing either historical report's exact byte identity.
- The redundant patch is not needed to build or run the retained source. Its
  original archive hash and manifest entry remain available for audit.

Repository additions are this explanation, the selection audit,
`verify_package.py`, ten packaging tests, and a current inventory. Outside this
directory, only the root README, validation guide, test runner and source
manifest/checksum change. Existing native/preview/research files, dependencies,
root LICENSE and third-party notices remain unchanged.

## Checks and what they mean

Run from the repository root:

```sh
python -B run_tests.py
python -B research/modern_fpc_codec/verify_package.py
python -B -O research/modern_fpc_codec/verify_package.py
```

The root runner uses separate subprocesses for normal and optimized Python.
It runs 11 frozen author methods, 17 frozen independent-review methods and 10
repository packaging methods for this addition. These tests need no external
native source files, NumPy, external decoder, envelope parser or application.
The packaging checks reconcile the recorded 167 public input entries, 166
source hashes, 7,843 stream occurrences and 9,949,997 word occurrences. They also
check preserved source hashes, exact source selection, evidence schemas,
sentinel qualification, strict/experimental stream counts, duplicate-report
reconstruction, local-path exclusions and the complete root inventory. They
read recorded evidence; they do **not** rerun those public streams.

The root default run still marks existing external-fixture/application tests
as explicit skips. No external corpus, external executable source, LabPlot,
Origin, Office, Mac or VM was run during this integration. The optional corpus
and external synthetic commands in the frozen README require separately
supplied exact-hash dependencies and public source files. They never download
or install them. Providing the matrix parser explicitly selects an experimental
comparison; its additional coverage is separately labeled, not strict-parser
support.

## Provenance, privacy and interpretation

Newly authored material uses the project's MIT LICENSE. The pinned external
quantized source remains Apache-2.0 and is not newly bundled here. Public source
metadata retains recorded CC-BY-4.0 or Etalab-2.0 attribution; native bytes and
numeric measurements are excluded. The new public tree contains source,
synthetic test generation, documentation and count/offset/hash evidence only.
No local source-path map, runtime binary, native input, image, measured array or
third-party executable source is added. This statement concerns the new package,
not the repository's separately documented existing dependencies or historical
synthetic CSV examples.

The independent decoder is an independently implemented check of the same
pinned-codec-derived specification, not an independently sourced vendor-format
oracle. The unchanged external API normalizes a finite missing sentinel to NaN.
The separately labeled, synchronous test-only adapter disables just that
normalization and restores the external module global afterward. Neither route
establishes native Origin acceptance. Wire identity observed in the recorded
public corpus is not a universal encoding guarantee.

The codec preserves raw bits in memory. It does not establish dataset ownership,
active/stored row consistency, compressed-container resizing, preserved graph or
analysis dependencies, or native application open/recalculate/save/reopen
behavior. None of the source-package or evidence checks removes those limits.
