# Bounded native OPJ style experiments

Research code only. It edits explicit source-object fields in two exact, hash-locked legacy OPJ fixtures. It never edits images or reconstructs graph data. Eight candidates were independently imported/redrawn by LabPlot 2.12.1. Origin reopen/save and modern OPJU support remain **NOT RUN / unsupported**.

See [the report](evidence/REPORT.md) for exact results, the title-font overwrite diagnosis, and compatibility limits. No stable skill is changed by this directory.

## Run tests

`python -m unittest discover -s tests -v`

`python -O -m unittest discover -s tests -v`

The source-only checkout runs 33 synthetic/unit test methods and skips 14 optional real-fixture methods. All 47 pass in normal and optimized Python with the three exact public fixtures. The added regression tests cover exact XML text/tail whitespace, independently recomputed source/cache preservation, title-probe hash guards, and shell argument/path rejection. To enable those tests, separately acquire the exact KDE source fixtures and place them under `fixtures/`, or set `ORIGIN_RESEARCH_FIXTURE_ROOT` to their directory:

- [2graphs.opj](https://github.com/KDE/labplot/blob/0bd2e4094e92e74052ec161022d4e60aeb7605cd/tests/import_export/Project/data/2graphs.opj), SHA-256 `bd25404bf20d008918c6fa6ad2bd610bedd28dca43ce0e52ee9c0b9a490e58ef`.
- [single_layer_two_axes.opj](https://github.com/KDE/labplot/blob/0bd2e4094e92e74052ec161022d4e60aeb7605cd/tests/import_export/Project/data/single_layer_two_axes.opj), SHA-256 `907538ce3633a51cdde39c4f3dc729b569bfaffedd33274b1367e1f791e9e961`.
- [strings_testing.opj](https://github.com/KDE/labplot/blob/0bd2e4094e92e74052ec161022d4e60aeb7605cd/tests/import_export/Project/data/strings_testing.opj), SHA-256 `8d1e26543e77942faef097a3cdc05ba4a78d2b0d667c9edb9003074b4e0443ed`. This third fixture is only for the separate title-font reader diagnostic.

Fixtures are not bundled or automatically downloaded. Review the upstream provenance/licensing separately if redistributing them.

## Create and restore a candidate

`python native_style_patch.py patch --profile single_axes --input fixtures/single_layer_two_axes.opj --field xb_tick_font --value 26 --out tick26`

The output has `candidate.opj`, a reversible `manifest.json`, complete native before/after inventories, and `restored.opj`. The source is read-only. Output directories cannot already exist. Publication uses Linux `renameat2(RENAME_NOREPLACE)` and refuses platforms where it cannot provide that safety.

`python native_style_patch.py restore --candidate tick26/candidate.opj --manifest tick26/manifest.json --out restored`

Supported narrow fields: `xb_tick_font`, `xb_axis_width`, `curve_line_width`, `layer_rect`. Values are JSON exact integers, or `[left,top,right,bottom]`. These are native stored field values, not promises about Origin's physical UI units. Never use this hash-locked experimental profile as an arbitrary user-project editor.

These parameter probes are not publication-ready layouts. Increasing the tick font or shrinking the layer produces overlapping labels in the observed screenshots. Automatic layout constraints and collision repair are not implemented.

Only newly authored code/tests and compact result evidence are included. No private files, executable binaries, third-party source implementations, native fixtures, generated plots, or numerical research datasets are published.

## Independent reader instrumentation

`application/` holds the newly authored read-only observer source and runner. They require the separately verified official LabPlot 2.12.1 extracted runtime, matching Qt6 development headers, and a Linux compiler. Set `LABPLOT_EXTERNAL_VIEWER_ROOT` to the runtime directory whose `squashfs-root/` and `debian-runtime/` layout is expected by `build.sh`. No binaries or third-party source are bundled. The observer ABI is specific to that release; do not use it against arbitrary LabPlot versions.

`compare_application.py` and `verify_results.py` consume the resulting actual application saves/readback, plus local candidate manifests. They do not render replacement plots. Full local run artifacts and native candidates are intentionally excluded from the public commit.

[Reproduction instructions](REPRODUCING.md) cover the eight style cases and the separate one-byte title22-to30 probe. `font_boundary_candidate.py` is a hash-locked diagnostic helper, not an added supported title-editing API.

[Independent review](evidence/INDEPENDENT_REVIEW.md) records twelve fresh-profile LabPlot runs, exact text/tail comparisons, native bit/cache checks and representative screenshot inspection. The reviewed validator regenerates every candidate from the pinned original before reporting preservation. Only UUID and creation-time attributes, plus the three explicitly named project UI metadata attributes, are excluded from XML acceptance. No other whitespace is normalized.

Newly authored code is covered by [MIT](LICENSE). LabPlot, liborigin and Qt remain external dependencies under their own upstream licenses. No upstream implementation or fixture is redistributed here.
