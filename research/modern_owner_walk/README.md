# Bounded modern Origin ownership research

This source-only package inventories a limited subset of CPYUA graph structure. It is not an OPJU editor, complete project parser, dataset resolver, or Origin replacement. It never updates source data, renders graphs, or refreshes cached previews.

## Run

Python 3.10+ standard library is sufficient for the owner walker:

```sh
python code/owner_walk.py /path/to/source.Contents.bin --out /path/to/new-inventory.json
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -v
```

Provide the native CPYUA Contents stream or standalone supported CPYUA file, not a PPTX or CFB container. The output parent must already exist. Output must be a new file: existing files, source aliases, symlinks, hardlinks and symlink-parent destinations are refused. A temporary file and atomic no-clobber publication prevent an output race from replacing a file. Input size is checked before bounded reads.

The helper beside the walker is self-contained. No workspace, private sample directory, user account, environment-specific path, NumPy or quantized installation is required. A relocation test copies the two modules to a fresh directory and exercises the actual CLI.

## What is established

Initial page discovery identifies complete sparse window-header candidates. Within a recognized graph page, ownership is then followed sequentially: post-header properties, layers, annotation lists, full curve/DataPlot entries, axis-break termination, three axis-parameter lists and layer/page termination. The six axis roles and X/Y/Z ordering are corroborated by the pinned liborigin source listed in the provenance file.

Already bounded outer-owned intervals suppress nested page candidates even if later outer parsing fails. Unknown transport, unsupported records and ambiguous raw-ULEB versus encoded81 framing stop the affected chain. Source size, page anchors, object lists and total owned-span counts have explicit budgets.

The public corpus evidence records 110 sources: 121 candidate pages, 105 complete graph-page chains, 120 complete graph layers and 2,717 sequentially walked curve records. Remaining categories are 10 workbook/table grammars, four unknown sparse style opcodes and two unsupported uncompressed style forms. No sample binaries or measurement values are included.

## What remains unknown

- Root page discovery is still candidate-based, not a complete top-level project traversal.
- Workbook sheet ownership, complete typed dataset lists and global dataset binding are not implemented. Explicit X/Y selectors are exposed without A-column or worksheet-X fallbacks. Zero selectors remain zero.
- Encoded81 and other property payloads are bounded and hashed, not semantically decoded by the owner walker.
- Nonempty axis-break lists, additional style encodings, matrices/functions and other versions may stop a chain.
- A complete transport chain does not prove all opaque semantics, visual correctness, font scaling, Origin reopening, saving or later regeneration.

## Separate LZ4 experiment

`code/lz4_block.py` is a standalone, bounded LZ4 block decoder. It is intentionally **not called by the owner walker**. Its caller must provide an independently justified block boundary and declared output size.

A separate public experiment compared 259 identified encoded81 payloads with installed liblz4 1.10.0. All 182 smaller packed blocks decoded byte-identically to their declared size. The 77 equal-length payloads were refused by both decoders and remain opaque; an uncompressed-fallback interpretation is unproved. This does not establish the meanings of decoded fields.

The 15 decoder tests include 1,000 deterministic synthetic cases compressed by installed liblz4. That one test explicitly skips if the optional existing library is unavailable. No library binary, upstream implementation, hardcoded proof runner, or native application is bundled.

## Scope and licensing

Only original code, synthetic tests and public provenance/counts are included. The code uses the existing repository MIT license. Public research samples retain their separate licenses and are not redistributed. No dataset-envelope prototype, file writer, application binary, screenshot, private source file, private field inventory or stable-skill modification is included.
