# Revision 2 changes

The original paused checkpoint and its reports remain untouched outside this new revision subtree.

- Numeric implementation unchanged: `982b2c9119e8a460bcd850e46db14268164dc28a78faf38fc4153123e2031e25`.
- The previously paused path-only portability edits in the two independent scripts were preserved and rerun, under ordinary Python and `-O`.
- `code/run_codec_experiments.py` now validates the complete fixed public-fixture manifest hash before parsing it and records implementation, runner and manifest hashes in each result. This addresses an integrity qualification identified by the new independent auditor. It does not introduce a general manifest API.
- Six added tests in `tests/test_revision_contract.py` cover opaque type/subclass rejection, bounds rejected before predictor scanning, hand-derived nonminimal encodings, every reachable size for floating-point edge bits, truncation and trailer rejection, and the explicit lack of count/checksum authentication.
- The external/public experiment and its provenance were independently reproduced, not merely copied from author logs. The unchanged external decoder's sentinel normalization remains disclosed.
- README, source/license notes, consolidated report, current audit and deterministic source-only package were added. Historical core review and proof remain separately labeled.
- No native container code, stable installed skill, repository release, user file or application was modified. No publication was performed.
