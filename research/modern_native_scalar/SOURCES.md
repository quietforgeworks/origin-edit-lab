# Code and third-party evidence sources

The authored research modules and synthetic tests are provided under the existing project's MIT License, copied unchanged in LICENSE (Copyright2026 quietforgeworks). This package does not contain a third-party Origin runtime, Office runtime, codec binary, native dataset sample, PPT/CFB binary or copied third-party parser source. It requires Python's standard library only.

## Static semantic references, not runtime acceptance

LabPlot2.12.1 liborigin was consulted for legacy native field roles and the page/layer/annotation/curve/axis record order. Source: https://download.kde.org/stable/labplot/labplot-2.12.1.tar.xz . Reviewed file: src/3rdparty/liborigin/OriginAnyParser.cpp, SHA256b43d1fbf3b70fd135188dcd12838c83b0886dc3444dbc63b086183e09f53d611. It is not bundled. README gives the exact relevant field locations and source lines. Its legacy scaling is not represented as verified modern Origin UI scaling.

The quantized CPYUA style reader, by Paige Quarterman, was consulted as additional static corroboration of the native curve width field: revision431deeb7c8473503970ca56b78cc1678f57d373d, src/quantized/io/origin_project/curve_style_color.py SHA256d156c51f603a144d7a01f41cad7137afc323c3b51cffa0d20f0e9425920aec4d. Neither its implementation nor binaries are bundled. The current writer does not depend on it and does not treat its output as an independent Origin application oracle.

The byte cursor in independent_cursor.py is a separately authored read-only implementation of the same restricted transport grammar. Its agreement strengthens internal record/delta checks; it does not independently establish the full modern Origin format.

## Public source evidence and attribution

The included JSON evidence describes only previously public samples. No source PPT, CFB, native file or numerical array is included.

- Alexander Kazakov and coauthors, Low-T Magnetoresistance and Spectral studies, https://zenodo.org/records/20155927 , Creative Commons Attribution4.0. The Heliox PPT and standalone calibration provenance are in evidence/*.json.
- Dataset supporting “Sub-diffraction-resolved spatial distribution of emitting excitons in STM-induced luminescence of2D semiconductors via Richardson-Lucy deconvolution”, https://doi.org/10.57745/W0SEAA , Licence Ouverte/Etalab2.0, https://spdx.org/licenses/etalab-2.0.html . Public OGGU provenance and citation metadata are in evidence/public-oggu-provenance.json.

License attribution does not imply endorsement, scientific correctness of an edited result, or Origin reopen/refresh/save acceptance. All application lifecycle checks remain NOT_RUN.
