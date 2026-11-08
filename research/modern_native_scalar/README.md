# Restricted modern Origin scalar source-edit research

This is a research module, not a generic OPJU writer and not an Origin-validated editor. It makes equal-length edits to selected native CPYUA scalar fields, then verifies and reverses every changed byte. No previews are edited, no numeric data are fitted or regenerated, and no application is launched. Visible PowerPoint previews remain unchanged and stale until an Origin refresh, which has not been tested.

## Exposed write interfaces

Only `code/native_scalar_writer.py` and `code/native_container.py` expose supported write/restore command-line interfaces. Both use externally supplied SHA-256 anchors, bounded regular-file reads, strict JSON with duplicate keys and all floating-point forms rejected, no-follow directory-component traversal, and exclusive atomic creation of new outputs. Inputs may not be FIFO devices, directories, symlinks or oversized files. Original files are never overwritten.

- Native API: `prepare(source, selector, new_value, expected_source_sha256=...)`; `apply(source, plan, expected_source_sha256=..., expected_plan_sha256=...)`; `restore(result, manifest, expected_source_sha256=..., expected_result_sha256=..., expected_manifest_sha256=...)`.
- Container API: `native_container.patch(source, plans, kind='cfb'|'pptx', part=..., expected_source_sha256=..., expected_cfb_sha256=..., expected_native_sha256=..., expected_bundle_sha256=...)`; matching `restore` requires independent source, result and manifest hashes.
- Canonical JSON bytes are `native_scalar_writer.canonical(object)`. A bundle is a list of 1–4 plans. Each serial plan must be freshly prepared from the actual preceding result, with its new source hash. A stale first-step plan cannot be reused on a later source.
- Native CLI: `plan`, `apply`, `restore`; inspect `--help` for required options. Container CLI: `patch`, `restore`. Manifests from apply/patch are printed on stdout; the new artifact is atomically created at `--out` only after full checks. Capture stdout in a new separate file, then retain its canonical SHA outside that file.
- External anchors must come from a trusted original inventory or independently retained caller record. A manifest’s own hashes do not authenticate the manifest. Recomputing both an untrusted manifest and its supposed external anchor is not independent validation. SHA-256 here provides byte identity, not a cryptographic signature or application acceptance.

`cfb_read.py` and `writeback.py` are internal byte-only dependencies. Their former extraction/patch/restore CLIs are disabled and fail explicitly. Their CFB allocation/ZIP algorithms remain unchanged. `native_binding.py`, `walk_dataset_envelope.py`, and `owner_walk.py` retain separate read-only inventory/diagnostic CLIs; these do not expose native editing or container restoration. Their diagnostic JSON I/O is not the hardened writer interface. `sparse_transport.py`, `independent_cursor.py`, and `verify_native_delta.py` are import-only read/verification helpers.

## Selection and accepted structure

Every write starts at the CPYUA prolog and requires a complete recognized dataset-envelope list, its terminator, every sequential page chain and its post-page opaque block, and the page-list terminator. The writer calls the frozen strict-root reader directly. It never calls the old scan-based inventory to authorize an edit. A matching-looking graph in an unknown prefix, opaque payload, incomplete root or unvalidated tail cannot be selected.

The selector supplies a unique root page name and a 1-based graph-layer ordinal. Names are looked up only within the complete rooted list; duplicate names reject. Curve selectors additionally specify curve ordinal, original X/Y selector integers and native plot type200. Both selectors must resolve to slots in the complete dataset list. This does not claim every descriptor's scientific type or every row's meaning is understood. Axis selectors specify X/Y/Z and near/far; title selectors require a unique named XB/XT/YL/YR/ZF/ZB annotation with a bounded raw text body. Mixed worksheet/graph pages are not accepted for writing.

The complete project tail remains unknown and is preserved byte-for-byte. Unsupported dataset codecs, root structures, page/layer/curve types, nonempty axis breaks, opaque target encodings, ambiguous owners, unknown version profiles, unknown unit systems and unsupported field classes reject. Known opaque non-target blocks remain opaque.

## Field classes, version profiles and evidence

All edit values are **stored integers**, never inferred Origin UI points or font sizes.

- `curve.line_width`: uint16 little-endian at decoded curve-header byte21. Require complete owned DataPlot body identity, native line plot type200, matching X/Y selectors, and the expected full header size. Static semantic support: LabPlot2.12.1 `OriginAnyParser.cpp` lines2431–2437 reads the width from offset0x15. The independent quantized CPYUA style reader corroborates this field. Its legacy division by500 is not used as a modern UI conversion or an Origin oracle.
- `annotation.font`: uint8 at decoded annotation-style byte4. Require the complete named annotation chain, unique accepted axis title, raw title text, and a profile-specific style record size. Static support: `OriginAnyParser.cpp` lines1874–1880 and named axis-title branches1918–1953.
- `axis.tick_font`: uint16 little-endian at decoded axis-parameter byte21, only positional near/far tick-label members of complete sequential X/Y/Z six-record axis lists. Static support: `OriginAnyParser.cpp` lines2793–2801 and2882–2890.
- `axis.line_width`: uint16 little-endian at byte21, only positional near/far axis-line members of those lists. Static support: `OriginAnyParser.cpp` lines2858–2865 and2947–2954. Modern UI scaling remains unverified.

Exact experimental profiles:

- CPYUA4.3268 build195: 515-byte curve/axis parameter records, 103-byte title-style records; all four classes have real public-source trials.
- CPYUA4.3683 build132: 519-byte axis parameter records, 111-byte title-style records; title/tick/axis classes have real public-source trials. Curve width is explicitly disabled because the available public curves are type202, not supported type200.
- CPYUA4.3811 build222: 519-byte curve/axis records, 111-byte title-style records. The source-only package includes generic synthetic coverage for these shapes. Its public-source matrix makes no real-source claim for this profile.

Record length alone never determines a field class. Root ownership, graph/annotation/axis role, fixed native tags and neighboring envelopes are required. The semantic sources and cross-format structural correspondence justify an experimental stored-field interpretation, not proof of modern Origin’s UI or runtime behavior.

Primary static semantic source: https://download.kde.org/stable/labplot/labplot-2.12.1.tar.xz ; `OriginAnyParser.cpp` SHA256 `b43d1fbf3b70fd135188dcd12838c83b0886dc3444dbc63b086183e09f53d611`.

## Preservation and restoration contract

A changed decoded byte must have unique one-to-one literal provenance. Zero/nonzero byte patterns cannot change. Unknown sparse opcodes, changed implicit-zero/repeat-backed bytes, altered sparse controls, encoded-length changes and record resizing reject. Unchanged implicit zeros can remain in a field. Every byte outside the selected field literals is compared, including numeric storage, unknown records and caches. This is stronger byte preservation, not a claim that all numeric rows are interpreted.

For CFB, only equal-length root `Contents` replacement within the existing allocation is permitted. FAT/miniFAT, directory, padding, free sectors, every non-target stream and all cached presentations are preserved. For PPT, exactly one authorized embedding part is replaced. All other member contents and raw compressed member data are preserved; ZIP metadata/offset changes needed for the one compressed member are reversible. Restoring the native steps in reverse, the CFB and the full original PPT must reproduce the exact original bytes. Restoration is additionally re-generated through the forward writer and compared.

## Public reproduction evidence

The public matrix checks110 pinned sources.101 meet the complete-root restriction and support385 successful scalar experiments:82 native type200 curve-width trials and101 each title, tick and axis-line trial. Nine sources reject. Each trial has a separately implemented full-record cursor reread, an exactly one-leaf semantic-tree change, full native complement comparison, and exact reverse restoration. This cursor is independent code for the same restricted grammar, not an independent Origin runtime oracle.

Public container serial example: one graph in the Heliox source PPT; four stored-field edits.516 other ZIP members,319 other CFB streams,102 OlePres streams and152 media parts remain byte-identical. Exact full-PPT restoration passed. The source-only package contains only public JSON evidence and generic code/tests, not the public PPT binaries.

Public sources and attribution:
- Alexander Kazakov and coauthors, Low-T Magnetoresistance, HelioxVT_MR_summary.pptx, https://zenodo.org/records/20155927 , CC-BY4.0.
- Dataset supporting “Sub-diffraction-resolved spatial distribution of emitting excitons in STM-induced luminescence of2D semiconductors via Richardson-Lucy deconvolution”, https://doi.org/10.57745/W0SEAA , Etalab2.0.
- Additional standalone public provenance is recorded in the copied public provenance JSON.

Run generic tests from this directory: `python -m unittest discover -s tests -v` and `python -O -m unittest discover -s tests -v`. No real user file or installed Origin is needed. This module does not install or modify a stable skill and does not establish Origin application acceptance.
