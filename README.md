# Origin Edit Lab

Tools for inspecting and editing Origin graphs embedded in PowerPoint, refining scientific figure layouts, and researching native Origin data and styles.

The project has two editing paths: **preview editing** changes how a graph appears in PowerPoint, while **native editing experiments** change selected data or style fields in the embedded Origin object.

## Features

### PowerPoint inspection and preview editing

- Inspect PPTX and Origin OLE containers.
- Extract CFB streams and EMF content embedded in WMF.
- Edit selected SVG appearance properties and replace previews in supported PPTX layouts.
- Compare original and edited figures with same-canvas pixel overlays.

See the [preview tools](docs/preview.md) and [capability map](docs/capabilities.md).

### Scientific figure layout

The [collaborate-figure-layout V1 skill](skills/collaborate-figure-layout/README.md) combines interactive rough layout and light refinement of an existing composition. It includes a local drag-layout page, typography and color options, alignment-guide proposals, selected preview-editing tools, and removable PowerPoint guides for a simple graph page.

The workflow also includes checks for overlap, panel-label ownership, data fidelity, marker proportions, and text spacing. Guide proposals are confirmed before alignment changes are applied.

- [Visual-layout workflow](docs/visual-layout.md)
- [Alignment plans](docs/alignment-plan.md)
- [Typography and color options](docs/style-options.md)
- [Skill changelog](skills/collaborate-figure-layout/CHANGELOG.md)

### Native data and style experiments

The repository contains separate modules with different format and template coverage:

| Module | Implemented work | Current scope |
| --- | --- | --- |
| [Original native experiment](native/README.md) | Replaces two columns of nine numeric values in an existing compressed record | One exact Origin OLE template |
| [Ropj readback](research/ropj_readback/README.md) | Reads workbook values and column metadata | Four synthetic legacy OPJ files; 1,761 values and 12 metadata groups checked |
| [Legacy style fields](research/legacy_style_fields/README.md) | Changes tick font size, axis width, curve width, and layer rectangles | Two hash-identified templates; eight changes reproduced through LabPlot import |
| [Legacy active rows](research/legacy_active_rows/README.md) | Changes the active prefix of an allocated dataset | 7, 49, or 50 active rows within a 50-row template |
| [Legacy allocation](research/legacy_allocation/README.md) | Reallocates data records for 51, 257, or 1,024 rows | One legacy OPJ template; LabPlot readback and curve-point checks |
| [Legacy multicurve](research/legacy_multicurve/README.md) | Adds independent X/Y curve pairs in Book1 | 2, 5, or 10 curves, each with 50 rows, in one template |
| [Custom data](research/legacy_custom_data/README.md) | Loads CSV data with a separate provenance declaration | One curve and 7, 49, or 50 active rows in a fixed 50-row template |
| [Modern binding diagnostics](research/modern_binding_diagnostics/README.md) | Examines worksheet and graph-reference mismatches | Read-only diagnostics on a fixed 110-input corpus |
| [Modern owner walk](research/modern_owner_walk/README.md) | Tracks layers, titles, curves, and axes in record order | 105 graph pages, 120 layers, and 2,717 curves parsed in the recorded corpus |
| [Modern native binding](research/modern_native_binding/README.md) | Reads sequential dataset roots, page chains, and column references | Restricted dataset/page sections completed in 101/110 and 24/57 recorded inputs |
| [Modern native scalar](research/modern_native_scalar/README.md) | Edits stored-integer curve width, named axis-title font, tick font, and axis-width fields | Equal-length literal changes in recognized records; 385 recorded single-field experiments |
| [Modern FPC codec](research/modern_fpc_codec/README.md) | Encodes and decodes raw binary64 numeric streams | In-memory codec; 7,843 streams and 9,949,997 value occurrences checked |
| [Exact-budget FPC](research/modern_fpc_exact_budget/README.md) | Finds same-count encodings at a requested byte length when reachable | Bounded numeric-stream encoding, separate from container writeback |

Module documentation records exact input coverage, dependencies, checks, and restoration procedures. The [native-data packaging guide](docs/native-data-packaging.md) distinguishes current portable tests from recorded application runs. The [FPC integration guide](research/modern_fpc_codec/INTEGRATION.md) describes the codec's included files and corpus accounting.

## Current limitations

- Preview edits do not change the underlying Origin graph. Opening and updating the object in Origin can replace those previews.
- Native writers are limited to identified templates, recognized structures, and specific fields. Arbitrary OPJU writing, general native style editing, and creating complete Origin graphs from scratch are not implemented.
- The published native experiments have not completed the full Origin open/edit/recalculate/save/reopen and PowerPoint activation cycle. LabPlot and parser results cover their own readback paths.
- Native data and scalar experiments retain the existing display cache; that cache does not render the new values.
- Modern scalar fields are stored integers whose mapping to Origin UI units remains incomplete. The FPC modules process numeric streams rather than writing OPJU, CFB, or PPT containers.
- Legacy row expansion and multicurve experiments use LabPlot-only research paths. Some template ranges, legends, unused cells, and unknown dependencies remain unchanged.
- Automated figure recognition and general automatic layout are not implemented by the layout helpers.
- Native atomic-output support currently depends on Linux `renameat2(RENAME_NOREPLACE)`. Native macOS writeback is not supported or validated.
- Ropj and LabPlot share a liborigin ancestry; their results are not independent parser-design evidence.
- Default tests use synthetic fixtures. External corpus checks require separately supplied samples and runtimes.

See [validation details](docs/validation.md).

## Quick start

Requires **Python 3.10+**. The recorded test environment is Linux with Python 3.12.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -B run_tests.py
```

Inspect a presentation, embedded object, or project signature:

```sh
python preview/pptx_origin.py inspect presentation.pptx
python preview/cfb_extract.py object.bin --report streams.json
python preview/compat.py project.opju
```

`compat.py` reports file size, signature hints, and hashes. Detailed editing commands and supported selectors are documented with each module.

## Development directions

1. Complete repeatable Origin and PowerPoint open/edit/save/reopen tests.
2. Extend native style-field coverage and map stored values to Origin UI units.
3. Add dataset/container writeback around the numeric codecs, including record lengths and dependent references.
4. Expand template-based graph generation, curve counts, and data ranges.
5. Improve scientific-layout refinement and cross-platform editing.

## License

Project code is licensed under [MIT](LICENSE). Third-party code in `native/dependencies/quantized/` retains Apache-2.0 licensing, LICENSE, and NOTICE files. See [THIRD_PARTY.md](THIRD_PARTY.md) for attribution and file hashes.

Origin, OriginLab, and PowerPoint are trademarks of their respective owners. This project is independent of those products.

