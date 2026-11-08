# Native numeric writeback experiment

This is a narrow source-object experiment, not a preview edit. It changes two existing numeric columns in one exact embedded Origin95.Graph template. Only FPC residual bytes may change. Original residual widths, controls, counts, graph records, X/Y selectors and all other native bytes stay intact. Some ordinary finite datasets cannot fit and are refused.

## Scope

- Exactly two columns (`x,y`), each containing nine stored values.
- Strict UTF-8 CSV, optional BOM, at most 16 KiB. Finite binary64 values only; missing values, NaN, infinity, underflow and the Origin missing sentinel are refused.
- Existing outputs are never replaced. Complete output is staged and atomically published on supported Linux systems.
- A custom decoder and the pinned quantized decoder check the stored numeric bits. Reversible manifests can reconstruct the original native stream and OLE bytes.
- **Origin open/recalculate/save/reopen and PowerPoint activation have not been tested.** Worksheet UI row alignment and unknown metadata/checksum dependencies remain unverified. The original caches are stale and unchanged.
- Output is an embedded native Contents payload and CFB object, not a standalone `.opju`, not a complete edited PPTX and not a newly serialized graph.

## External fixture

No original binary is distributed. To reproduce the exact-template experiment, obtain the public source independently from Alexander Kazakov and coauthors, [Zenodo 20155927](https://doi.org/10.5281/zenodo.20155927), under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The source is `Low-T Magnetoresistance/HelioxVT_MR_summary.pptx`, SHA-256 `207de07f76806d1059f4b6829203c2e3a4a74823df8b457cf03497cf9262a250`.

Extract `ppt/embeddings/oleObject90.bin` without activating it. Its SHA-256 must be `25536b607581c5161af6e859b69c09d21be4ba3df3a51ab620829ad46e9bfa7c`. Put your local copy at `native/inputs/original-object90.ole.bin`. That path is ignored by Git. Do not substitute an arbitrary Origin object: the generator refuses it.

The CSV included here is entirely synthetic demonstration data, not a measurement or proposed scientific correction. If you share an adaptation of the external template, follow its license, credit its authors and indicate changes. This project's MIT license does not relicense that template.

```sh
python -B native/generate_native.py native/inputs/original-object90.ole.bin native/inputs/synthetic-demo.csv candidate
python -B native/verify_native.py native/inputs/original-object90.ole.bin candidate
python -B -O native/verify_native.py native/inputs/original-object90.ole.bin candidate
python -B run_tests.py
```

Use a new output directory. A `PublicationError` can indicate that complete output was published before a later durability error. Inspect `published`, `final_path` and `staging_path` before retrying. A crash may leave a hidden staging directory. Hardware power-loss durability and adversarial filesystem races have not been audited.

The 58 exact-template regression tests are skipped unless you supply that fixture. Synthetic CSV, codec, restoration and output-failure tests run without it. Native/PPTX container patch primitives in `dependencies/helpers/writeback.py` remain research utilities and do not synchronize display caches.
