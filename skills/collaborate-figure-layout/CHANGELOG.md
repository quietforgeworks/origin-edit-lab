# Changelog

## 0.1.0 - 2026-11-08

First public release of the scientific-figure collaboration skill.

- Integrates interactive rough layout and existing-layout refinement with shared aesthetic, source-preservation, alignment and delivery gates.
- Includes offline interaction templates, bounded preview-edit helpers, generic optional online templates and native PPT guide add/inspect/restore support.
- Adds measured quality specifications and explicit communication guidance for unsupported source edits and application validation.
- Portable release validation: 180 Python tests in normal mode and 180 in optimized mode, plus nine Node interaction tests. Separate Inkscape smoke checks and LibreOffice guide-render checks were completed; guide removal restored exact PPT bytes and matched the clean render.

Guide support is limited to one selected simple figure slide without source groups or AlternateContent; no multi-figure guide chaining is claimed. Browser file-protocol behavior, actual PowerPoint activation and Origin edit/save/reopen were not validated by this release. Optional online deployment and its identity/storage bindings are not included.
