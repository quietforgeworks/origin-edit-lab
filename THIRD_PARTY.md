# Third-party software and provenance

## quantized

Six unchanged Python modules under `native/dependencies/quantized/io/origin_project/` are from [pquarterman17/quantized](https://github.com/pquarterman17/quantized), revision `431deeb7c8473503970ca56b78cc1678f57d373d`, Copyright 2026 Paige Quarterman. They retain [Apache-2.0](native/dependencies/quantized/LICENSE) and the original [NOTICE](native/dependencies/quantized/NOTICE). The root MIT license does not replace these terms.

The copied modules are `container.py`, `opju_codec.py`, `opju_figure_curves.py`, `curve_style_color.py`, `tree.py` and `tree_opju.py`. Their original bytes and SHA-256 values are retained in `native/dependencies/PROVENANCE.json`. Bootstrap checks every listed file before import. No upstream application is launched or optional GUI registry imported.

The helpers in `native/dependencies/helpers/` are project-authored research code under the root MIT license. The FPC encoder/decoder is independently authored from the published algorithm, with framing checked against the pinned Apache-2.0 implementation. They do not include a copied GPL implementation.

## Runtime dependencies

NumPy, lxml and Pillow are installed separately, not vendored. Consult each distribution's license and bundled-component notices. Inkscape is optional and used only when already available for rendering tests/conversion. No Origin or Microsoft software, binaries, SDKs, license keys or fonts are redistributed.

## Test data

The committed CSV is synthetic. Preview fixtures are generated from code; the repository includes no original PPT/OLE/OPJ/OPJU binaries or research measurements. The optional exact-template tests refer to an external CC BY 4.0 research source, documented in `native/README.md`. Its license is separate from the code license.
