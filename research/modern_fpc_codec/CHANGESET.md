# Isolated change set

This package records net-new standalone research work. During that experiment there was no patch to a stable repository or skill and no native-file difference to apply.

Added:

- `code/fpc_numeric.py`: exact-bit FPC stream encoder and bounded companion decoder, no file I/O or dependencies.
- `code/verified_oracle.py`: test-only SHA-pinned external-source loader and explicitly labeled sentinel-normalization adapter.
- `code/run_external_synthetic.py`: deterministic external interoperability proof runner.
- `code/run_public_corpus.py`: read-only, allowlisted public-stream audit; externally supplied strict and opt-in matrix parsers.
- `tests/`: deterministic edge/synthetic, framing, mutation, truncation and resource-bound tests.
- `independent-review/`: separately authored integer decoder, hand-derived fixtures, adversarial tests and review findings.
- `evidence/`: public identifiers, source/dependency hashes, numerical test-category counts and final run reconciliation, without native data or private paths.
- `results/`: data-free validation logs and bounded corpus records.
- Documentation: interfaces, algebraic exactness argument, implementation ancestry, limits, reproducibility, source references and remaining native-write blockers.
- `LICENSE`: the authorized project's MIT license and copyright notice, applying only to newly authored material; third-party boundaries are stated in `SOURCES.md`.

During the research experiment, original files were opened read-only, and all 167 public input SHA-256 values were checked before and after each corpus run. No encoded stream was inserted into OPJU/CFB/PPT and no native file was produced. No source or package was uploaded, committed, pushed or published during that experiment. These historical conditions do not describe any later package distribution. Final file hashes and archive hash are supplied separately for integration review.

The license-packaging revision changes only license/documentation, related metadata and archive manifests. Core implementation, test code and original experimental result logs are unchanged.
