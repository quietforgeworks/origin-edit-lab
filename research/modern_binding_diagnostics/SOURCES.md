# Public sources and scope

## Input provenance

- Alexander Kazakov and coauthors, [Zenodo record 20155927](https://zenodo.org/records/20155927), CC-BY-4.0. The source archive `Low-T Magnetoresistance.zip` contains `Low-T Magnetoresistance/HelioxVT_MR_summary.pptx`. Only its 106 named OLE `Contents` streams are audited. The separate archive `Spectral studies.zip` contains `Spectral studies/Spectral_studies_calibration/intensitites.opju`, locally identified as `spectral-calibration.opju`. Archive member identities are retained for reproducibility; no native bytes are redistributed.
- Eric Le Moal and coauthors, [dataset DOI 10.57745/W0SEAA](https://doi.org/10.57745/W0SEAA), “Dataset supporting the publication: Sub-diffraction-resolved spatial distribution of emitting excitons in STM-induced luminescence of 2D semiconductors via Richardson-Lucy deconvolution,” Etalab-2.0. Public file IDs 667553, 667559 and 667566. Individual file DOIs, original names and SHA-256 hashes are in `public_sources.json`.

All reported per-file hashes refer to public inputs from those records, not user files. The only retained measurements are counts. Filenames in the manifest identify acquisition targets and are not raw decoded worksheet/graph names.

## Exact external parser

[quantized revision 431deeb7c8473503970ca56b78cc1678f57d373d](https://github.com/pquarterman17/quantized/tree/431deeb7c8473503970ca56b78cc1678f57d373d), Apache-2.0. All six imported files are pinned by SHA-256 in `quantized_sources.json`. They are external prerequisites, not redistributed here.

The relevant implementation is [opju_figure_curves.py](https://github.com/pquarterman17/quantized/blob/431deeb7c8473503970ca56b78cc1678f57d373d/src/quantized/io/origin_project/opju_figure_curves.py):

- Lines 18–28 distinguish stored IDs from current worksheet column order.
- Lines 93–95 describe counting decoders retained as a fallback when no table is found. This package does not invoke that fallback.
- Lines 121 and 195–204 restrict recognized property designations.
- Lines 250–286 select X from a worksheet partner/first-X/A and deduplicate book/short-Y pairs. The portable proof invokes this actual function without editing it.

The proof is independent of the earlier audit's file layout. It still depends on the pinned parser for page candidates and actual extraction; it is not an independent complete modern file reader.

## Official reader context, not modern acceptance

Official release: [LabPlot 2.12.1 source archive](https://download.kde.org/stable/labplot/labplot-2.12.1.tar.xz).

- Archive SHA-256: `e28155bfddf40e5b6f7c4791313556d1e48138044f216f210d515b9f6d6c106a`.
- `src/3rdparty/liborigin/OriginAnyParser.cpp`: `b43d1fbf3b70fd135188dcd12838c83b0886dc3444dbc63b086183e09f53d611`.
- `src/3rdparty/liborigin/OriginParser.cpp`: `e1aa776c931f24c081c33ff8ee67cbe65ae29d9b74009cc5daa10e19703e1c7d`.

These hashes identify official public source reviewed in the underlying audit; the portable proof does not execute or require LabPlot. Source observations:

- `OriginAnyParser.cpp` traverses datasets before windows, assigns stream indexes across dataset types, increments the object index per dataset, and reads graph X/Y selectors independently. Worksheet columns, matrices and functions share the identity namespace.
- `OriginParser.cpp` searches those types by assigned index and retains sheet suffix information when grouping columns.
- Recognizing a CPYUA signature does not demonstrate successful parsing of all modern sparse-compressed forms. The official source observations establish legacy reader semantics, not a universal modern serialization grammar.

No source implementation from LabPlot, liborigin or quantized is copied into this package. Native source offsets, decoded property payloads and captured application files are deliberately absent.
