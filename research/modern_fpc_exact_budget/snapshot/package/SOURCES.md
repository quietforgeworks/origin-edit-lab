# Sources and scope

## Exact-budget implementation

The unchanged implementation is `code/experimental_exact_fpc.py`, SHA-256 `982b2c9119e8a460bcd850e46db14268164dc28a78faf38fc4153123e2031e25`. It and the original test/proof harness were authored for this project under the included MIT license. The independent decoder is a separately authored implementation of the supplied grammar, not an independently sourced Origin format oracle.

The baseline research project is https://github.com/quietforgeworks/origin-edit-lab/commit/f43e31cb2c18c5fc2906f2a0235a48214a4b27a0 . This revision has not been published there.

Inherited, byte-identical reference copies:

- `reference/fpc_numeric.py`: `43c3415066ed12f1f158e8406f6d62d1dc767daea537e31441865934e6c70dbc`.
- `reference/independent_fpc_decoder.py`: `0ad34fbaedf86655085e6302d864a3456af6377f7d00e641a2879dbf79734d89`.
- `reference/verified_oracle.py`: `2e6281e200590d83c063fd1e633caa09988f511ba34fe925c2807871a105b98d`.

## External implementation, not bundled

Previously approved quantized revision `431deeb7c8473503970ca56b78cc1678f57d373d`, Apache-2.0: https://github.com/pquarterman17/quantized/tree/431deeb7c8473503970ca56b78cc1678f57d373d .

- `src/quantized/io/origin_project/container.py`: `e80996b8955d46b446bdc4761a55b19b6d760619edb0b94b98f16ebe47cb4115`.
- `src/quantized/io/origin_project/opju_codec.py`: `5a2c6f000ff8fef0a71ba8aab0876f7de785d5bb4dfa8d07dd612f052b737be9`.

Only those two exact verified source buffers execute. NumPy 2.3.5 was already available for this optional test. No code was downloaded or installed. External API sentinel normalization is documented in README and REPORT; the unchanged API is not fully bit-exact on that sentinel.

## Public provenance, native bytes not bundled

Three previously acquired public Dataverse native files, record https://doi.org/10.57745/W0SEAA , under Etalab-2.0 according to the pinned provenance manifest. Exact filenames, source hashes, complete stream extents and word counts are in `evidence/public-template-streams.json` (SHA-256 `4f59150060fd427f97fea59829c8cd7b070010287b6f030097b61c28b89810ec`). No source values or project bytes are included.

- Original reviewed public corpus report: SHA-256 `2bca1eeeac8b271be79eaf355924aa259dfe4789884cc9a71634f62229bdc271`.
- Original public source provenance manifest: SHA-256 `9da30c7bc4f167290f53d0293083354e2e168614d8e372541115240c0f203e76`.

Those large prior reports are not bundled. This revision's auditor independently verified both source hashes, exact equality of all 13 selected stream records and all three provenance records, and immutable source file hashes before/after reproduction. Portable codec tests need only this package and Python. Reproducing the external/public checks additionally requires NumPy, the two pinned approved quantized sources, and the three listed public files. Reproducing the historical lineage crosscheck also needs the prior reports with these exact hashes.
