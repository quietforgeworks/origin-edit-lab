# Independent portable/public harness audit

Scope: fixed revision-2 research package only. Independent static inspection of the exact-budget encoder, author tests, portable independent-review scripts, pinned reference modules, external loader and public harness; independent rerun of public/external harness and bounded adversarial checks. The parent reruns the full focused author/oracle/adversarial suites. No whole repository tests, native writing, Origin, VM, bridge, downloads, installs or user files were used. All auditor writes are within revision-2/audit. Python 3.12.14, NumPy 2.3.5, Linux.

## Exact reviewed inputs

- code/experimental_exact_fpc.py: 982b2c9119e8a460bcd850e46db14268164dc28a78faf38fc4153123e2031e25
- code/run_codec_experiments.py, final reviewed revision: a0d2ea12255d8fdcecc8ebf0234ad3868a145db27ffe6d0bd755a33e7371df7b
- tests/test_revision_contract.py (additional static review): fe19bf10fc2487c5ed6ba2df74cfa5677067479f3840872f46f64e527f822b7b
- tests/test_exact_budget.py: 85a08e74a3e0546e0a27414eda04761761bcb6ec9484847f8f0e6932b0901c97
- independent-review/adversarial_review.py: 620f999722de6b9a4e788d74da6e11fdc4aaa82590d9fd430a5d0598d4800f90
- independent-review/reachability_oracle.py: 4bce21e420ed09ca2e956b16d0fdec285f15ba4640d03962cf61f1fff0cd734c
- reference/fpc_numeric.py: 43c3415066ed12f1f158e8406f6d62d1dc767daea537e31441865934e6c70dbc
- reference/independent_fpc_decoder.py: 0ad34fbaedf86655085e6302d864a3456af6377f7d00e641a2879dbf79734d89
- reference/verified_oracle.py: 2e6281e200590d83c063fd1e633caa09988f511ba34fe925c2807871a105b98d
- evidence/public-template-streams.json: 4f59150060fd427f97fea59829c8cd7b070010287b6f030097b61c28b89810ec
- Prior public-corpus-normal.json: 2bca1eeeac8b271be79eaf355924aa259dfe4789884cc9a71634f62229bdc271
- Prior evidence/public_sources.json: 9da30c7bc4f167290f53d0293083354e2e168614d8e372541115240c0f203e76

All 13 public stream records match the prior report exactly, including ordering, intervals, counts, raw/encoded hashes, sentinel counts and strict/experimental flags. All three full public provenance records match the prior provenance manifest exactly. The fixed source allowlist contains only dataverse-667553.oggu, dataverse-667559.oggu and dataverse-667566.oggu.

## Reproduction and adversarial results

portable-public-normal.json and portable-public-optimized.json independently reproduce the final runner and compare equal after removing only optimize. Each reports 483 synthetic sequences, 1,264 exact-budget encodings, 39,543 decoded words, 781 nonminimal encodings and 566 sentinel occurrences. Aggregate raw/encoded SHA256: 8d4c06043c8680b3e2139f7743426b27bbc133212529cb5fd21a832b4416e711. Each public run validates all 13 original and reencoded streams, achieves 13 toy exact-budget successes, refuses all 13 unreachable random-bit targets, and verifies all three sources unchanged.

The additional six contract tests were statically reviewed without defect, including the explicit example in which counts 1 and 2 consume identical extents. The independently written audit_public_harness.py accepts --package and --research-root path overrides and ran normally and under -O: each passed 430 expected refusals. Coverage includes malformed raw/budget/limit types, truncation and strict trailing-byte rejection, source/dependency hash mismatch, direct symlink refusal, real public entrypoint rejection of tampered or symlinked manifests and sources, external source mismatch before execution, external module cleanup, deterministic encoding and raw NaN/sentinel/signed-zero checks at every reachable budget for a special-value sequence. Checks use explicit exceptions, not assert.

The original runner c8d3c5288f62dcb374c3d71a09cbcf18a37df7a992c1ab57f34a15adf33595bb also reproduced successfully, retained as old-runner-normal.json and old-runner-optimized.json. Its manifest-trust qualification was reported before parent modification. It is superseded by the final pinned-manifest runner above.

## Findings and qualifications

No blocking codec or final fixed-fixture harness defect found. Initially the runner trusted unpinned manifest metadata; parent fixed this by checking the exact reviewed manifest digest on the same read buffer before JSON parsing. The fixed hash plus exact historical-record comparison adequately closes this gap for this archive; it is not a generalized arbitrary-manifest interface.

The external loader verifies both previously approved source files before executing either; only their verified in-memory buffers execute, with synthetic empty package namespaces rather than real package initializers. Pins are container e80996b8955d46b446bdc4761a55b19b6d760619edb0b94b98f16ebe47cb4115 and opju_codec 5a2c6f000ff8fef0a71ba8aab0876f7de785d5bb4dfa8d07dd612f052b737be9, revision 431deeb7c8473503970ca56b78cc1678f57d373d. Trust still includes the local Python/NumPy runtime and approved dependencies. Direct symlink checks are not an OS sandbox or protection from concurrently hostile parent-directory replacement; digests guard actual read source bytes. No adversarial filesystem threat is claimed.

Both integer decoders preserve all input words exactly. The unchanged external API intentionally maps the finite Origin missing sentinel to NumPy NaN; every other bit is compared exactly, including NaN payloads. The adapter helper is not called by this harness. Public selected streams contain no missing sentinels, so sentinel behavior is supported by synthetic coverage, not these 13 public cases.

Count remains external metadata. Strict decoders reject extra bytes, prefix checks require exact consumed extent, and nonminimal widths enlarge residuals rather than append padding. Independent decoders share the specified grammar and are not independent native Origin acceptance. A smaller count can legitimately describe a prefix, so this codec cannot authenticate dataset framing or semantic count by itself. Fresh predictor state applies per stream.

The source report provides prior envelope evidence; this harness checks recorded intervals, not new envelope recognition. Toy values are deliberately synthetic and never replace source data. Resource caps bound algorithmic sizes, not total process memory/time. Tests on Linux do not establish Mac/Windows behavior, Origin reopening, graph preservation, scientific suitability, whole-container writeback or serializer completeness. No such promotion is warranted.

## Verdict

Safe to freeze as a bounded codec-only research archive, conditional on the parent's final manifest/archive review and its focused suite results. Not approved for production/native serializer promotion or native Origin acceptance. Re-review changes to the pinned code, manifests or dependencies; this report does not approve later additions merely because they occupy the same directory.
