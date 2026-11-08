# Exact-budget FPC numeric-stream research

Research revision **2**, published separately from the unchanged `collaborate-figure-layout` skill **0.2.0**.

This isolated, integer-only codec can preserve opaque binary64 bits while selecting an exact reachable FPC stream length. It refuses impossible budgets and does not pad, truncate, resize native records or change word counts. It is **not a native Origin/OPJU writer**. Origin acceptance of nonminimal encodings remains **NOT_RUN**.

The [44-file audited snapshot](snapshot/README.md) is retained byte-for-byte. Its mentions of an unpublished candidate describe the historical freeze, not this repository publication. They have not been rewritten, so its original hashes remain verifiable. See the [integration record](INTEGRATION.md), [codec contract](snapshot/package/README.md), [results and limits](snapshot/package/REPORT.md), and [independent audit](snapshot/audit/PORTABLE_PUBLIC_AUDIT.md).

## Tests

Python 3.10+ standard library suffices. From the repository root:

```sh
python -B -m unittest discover -s research/modern_fpc_exact_budget/snapshot/package/tests -v
python -B -O -m unittest discover -s research/modern_fpc_exact_budget/snapshot/package/tests -v
python -B -m unittest discover -s research/modern_fpc_exact_budget/repository-tests -v
python -B -O -m unittest discover -s research/modern_fpc_exact_budget/repository-tests -v
```

The root `run_tests.py` includes these isolated suites in both modes. The snapshot has 14 author/contract tests; six additional packaging tests verify the frozen inventory, review pins, public metadata and recorded evidence. They do not rerun public files or native applications. Run the larger independent oracle and adversarial scripts in a disposable copy using the snapshot instructions because those scripts create result files beside themselves.

## Scope and licensing

Bundled implementation, reference codec, separate grammar decoder and verification loader retain the project's MIT license. The decoder is not an independently sourced native Origin oracle. Optional quantized code is Apache-2.0 and is not bundled in this module. Public native inputs are excluded; their recorded Etalab-2.0 provenance remains in the [source notes](snapshot/package/SOURCES.md).

No user files, native binaries, measured arrays, private hashes, local absolute paths or credentials are included. Sanitized synthetic test logs and public-source metadata are historical evidence. No native dataset/page/container serializer, ownership proof, row-metadata update, cache refresh, graph export, or Origin cold-open/save/reopen acceptance is provided. All earlier repository APIs and Skill 0.2.0 remain unchanged.
