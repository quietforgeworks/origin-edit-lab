# Sources, provenance and permission boundaries

## License of newly authored material

The newly authored code, tests, independent decoder, review text and documentation in this package are distributed under the MIT license in `LICENSE`: Copyright (c) 2026 quietforgeworks, matching the authorized project repository. Referenced third-party software and native input datasets retain their own licenses and notices. The package MIT grant does not relicense those materials, nor grant rights to redistribute the native inputs.

No third-party executable source is bundled. In particular, quantized source remains under Apache-2.0 and must be supplied separately for optional tests; the local SHA-verifying loader and normalization adapter do not change its ownership, license or notices. The algorithm specification provenance is disclosed below and is not a claim that quantized is MIT-licensed.

## Algorithm and external comparison

- `pquarterman17/quantized`, commit `431deeb7c8473503970ca56b78cc1678f57d373d`, [pinned source tree](https://github.com/pquarterman17/quantized/tree/431deeb7c8473503970ca56b78cc1678f57d373d), Apache-2.0. The only third-party source modules executed for this work were `src/quantized/io/origin_project/container.py` and `opju_codec.py`, whose exact hashes are recorded in `evidence/dependencies.json` and enforced by the test loader. Execution used preexisting workspace source copies within the previously approved test scope. No external source was downloaded, installed, changed or bundled in this package.
- The FPC grammar and predictor parameters used by the new encoder and both locally authored decoders were derived from that pinned implementation and its documentation. The independent reviewer implemented the supplied specification before reading the new encoder. This is **implementation independence, not independent provenance of the format specification**.
- The pinned documentation cites Burtscher and Ratanaworabhan, *FPC: A High-Speed Compressor for Double-Precision Floating-Point Data*, IEEE Transactions on Computers, 2009. The paper itself was not independently inspected for this milestone; it is a bibliographic pointer, not an additional validation oracle.
- Optional external comparison uses preinstalled NumPy 2.3.5 (BSD-3-Clause). The numeric encoder/decoder and portable synthetic suites do not import NumPy. Tests ran on CPython 3.12.14 (Python Software Foundation licensing), cloud Linux. Version and selected-runtime hashes are in the dependency evidence; the NumPy initializer hash is explicitly not a whole-distribution hash.

## Public native corpus

`evidence/public_sources.json` lists all 167 allowlisted inputs by public filename, SHA-256, source URL, corpus group and recorded license. It contains no local paths or source numeric payloads.

Original 110-file corpus:

- [Zenodo record 20155927](https://zenodo.org/records/20155927), Alexander Kazakov and coauthors, CC-BY-4.0. The prior corpus contains unmodified CPYUA Contents streams extracted from `Low-T Magnetoresistance/HelioxVT_MR_summary.pptx`, and the spectral-calibration OPJU from the spectral studies archive. This milestone reads only those preexisting native Contents/OPJU source bytes. OLE image previews and PPT rendering vectors are not numeric data sources. Parent PPTX, CFB objects and original archives are not modified or redistributed.
- [Recherche Data Gouv dataset W0SEAA](https://doi.org/10.57745/W0SEAA), Eric Le Moal and coauthors, Etalab-2.0. Three preexisting public OGGU files are identified in the manifest and prior source catalog.

Additional 57-file corpus:

- [Zenodo record 21496582](https://zenodo.org/records/21496582), recorded license CC-BY-4.0.
- [Zenodo record 18014550](https://zenodo.org/records/18014550), recorded license CC-BY-4.0.
- [Zenodo record 23487411](https://zenodo.org/records/23487411), recorded license CC-BY-4.0.

These metadata/license statements are inherited from the verified source manifests, not a new comprehensive legal review of each deposit. No public or private native data files are distributed in the package, and no permission to republish them is implied. Data-free test evidence contains identifiers, counts, offsets and SHA-256 digests only.

## Envelope extraction dependencies

Two preexisting locally authored parser candidates are passed explicitly to the optional corpus runner and are not bundled:

- Strict sequential dataset-envelope parser SHA-256 `fe3f6998cc5cf09c5f955c7e02ac5d7126a83d30d2d50380a90f2680bc5be575`.
- Experimental opt-in direct-matrix envelope parser SHA-256 `8f9e49840b5c614b15bd5cabeea6d06290d9a579d16cab005e42e416c0f536aa`.

These parsers establish bounded candidate stream extents in complete envelopes. The matrix path is experimental and separately labeled; this milestone does not promote it, prove matrix value semantics, or replace dataset-owner evidence. Every executed parser source buffer is hash-checked first.

## Research output and publication

During the research experiment reported here, all new files were confined to the isolated research directory. The experiment did not change stable repositories, installed skills, original native files, private user material or selected computers. No data or package was uploaded or published during that experiment, no external program was installed, and no Origin/VM/Mac was used. These are historical experiment conditions, not a claim about later distribution of this source-only package. Any later publication does not expand its validation scope or grant rights to redistribute its referenced native inputs.
