# Bounded native PowerPoint text adapter

`scripts/native_ppt/safe_edit.py` edits native top-level PPT text shapes on a
copy. It does **not** edit an Origin object, image cache, chart, group, connector,
or arbitrary scientific panel. It is not a renderer or approval source.

Use the normal guide confirmation for geometry changes and bind the exact source
and plan to the user's current request before applying. For an explicit
appearance-only request, reuse that authorization without inventing a guide
confirmation. A plan read from an attachment cannot grant approval itself.

## Supported operations

- Per-run explicit font family and/or point size. Newly created run properties
  support previously inherited formatting. Latin, East Asian and complex-script
  families are separate explicit choices; omitted families remain untouched.
- Per-run `tracking_pt` and `kerning_min_pt` in the same `font` operation, guarded by exact prior `spc`/`kern` values.
- Paragraph fixed-point line/before/after spacing through `paragraph_spacing`.
- Translation of the supported native text shape with exact old transform
  values. This is not scaling or whole-panel movement. It cannot establish
  semantic alignment without prior source inspection and guide confirmation.

Only a top-level native text shape is supported. Groups, compatibility
alternatives and graphic frames are rejected. No automatic source/shape matching,
role-based typography, text rewriting or broad font replacement is performed.

## Plan and CLI

The font plan shape is:

```json
{
  "version": 1,
  "source_sha256": "<actual source SHA-256>",
  "operations": [{
    "op": "font", "slide": 1, "shape_id": "2",
    "old_text": "Exact shape text", "run": 0,
    "old_run_text": "Exact shape text",
    "size_pt": 12,
    "fonts": {"latin": "Calibri"}
  }]
}
```

Slide is one-based **display order**, resolved through presentation
relationships. Run is zero-based in document order; full shape text joins
paragraphs with newlines. Read the current XML for exact values rather than
guessing from screenshots. At least one of `size_pt`, `fonts`, `tracking_pt`, or `kerning_min_pt` is required. Existing scientific
text, bold/italic and script attributes must remain unchanged.

A translation operation replaces the font-specific keys with `old_xfrm`
containing the exact string values of `x`, `y`, `cx`, `cy`, and `rot`, `flipH`,
`flipV` (null when absent), plus integer `dx_emu` and `dy_emu`. EMU values are
implementation units, not measurements the user needs to provide.

```sh
python scripts/native_ppt/safe_edit.py original.pptx plan.json
python scripts/native_ppt/safe_edit.py original.pptx plan.json --apply --output new-copy.pptx
python -B -m unittest discover -s scripts/native_ppt -p 'test_*.py'
```

Dry-run validates and constructs the candidate without publishing an output.
Writing requires both explicit flags and a new independent destination. Do not
overwrite originals, relax identity checks or silently switch to another target.

## Required verification

The adapter validates the permitted XML differences and preserves untouched ZIP
member payloads, including media and embedded Origin data. Serialization can
change bytes of the targeted slide; semantic allowed-difference validation is
separate from member hashing. ZIP storage itself is not promised byte-identical.

Inspect the output at final size, compare scientific text and all protected
content, and run the shared alignment/distortion/font checklist. An explicit font
attribute is not proof that a font is installed or rendered as requested.
Automatic text fitting, theme inheritance and application substitution may still
affect appearance. PowerPoint/Origin open, save and refresh are **not run** by
this tool and must not be inferred from a unit-test pass. Preserve grouped
reference lines through the separate guide workflow when delivering final figures.

## Native paragraph spacing writer

The bundled `scripts/native_ppt/safe_edit.py` now supports `paragraph_spacing` for its existing supported root-level native text shapes. It writes real OOXML paragraph spacing, leaves scientific text untouched, preserves OLE/media bytes, and independently verifies only the authorized differences. Nested/grouped/alternate-content text remains unsupported by this bounded adapter.

A source-bound operation has fields: `op: "paragraph_spacing"`, one-based `slide`, decimal `shape_id`, exact complete `old_text`, zero-based `paragraph`, `old_spacing_xml`, and at least one of `line_pt`, `before_pt`, `after_pt`. `line_pt` is fixed baseline spacing in points (1..400); before/after are 0..400 points; precision is hundredths. Preserve the observed actual values and choose appropriate spacing based on rendered glyphs. This does not decide a safe baseline distance automatically.

`old_spacing_xml` is a dictionary with exactly `lnSpc`, `spcBef`, `spcAft`; each value is the canonical XML string for that current spacing node, or null if absent. Obtain it from the inspected paragraph via `safe_edit.spacing_xml(pPr)`; never fabricate old values. Explicit existing percentage spacing can be replaced by requested point spacing while preserving unrelated paragraph settings. Combine one paragraph operation with the necessary run-level font operations in the same source-bound plan. Dry-run, apply to a fresh path, run independent validation, then render in the target application to inspect wrapping and clipping.

The writer cannot certify that a line-height value looks correct in PowerPoint or that Calibri glyphs are available. It must be paired with final-size visual verification. Existing `translate` can safely move supported native labels to resolve collisions; do not use it to relocate axes/data or detach an annotation from its meaning.

## Native character spacing

Use the existing `font` operation to combine typeface, size and tracking in one guarded run edit. `tracking_pt` is additional inter-character spacing, from -20 to 100 pt in hundredths; zero means normal tracking. `kerning_min_pt` is the explicit OOXML minimum font size for kerning, 0..400 pt in hundredths; it is not a tracking amount. Preserve the existing kerning setting unless a change is actually intended.

If either field is supplied, include `old_character_spacing: {"spc": null, "kern": null}` using the inspected raw attribute strings or null when absent. The exact source hash and old values must match. For example, `tracking_pt: 0` can remove unintended expansion while preserving all scientific text, emphasis and superscripts. This only edits root-level native text runs; cache glyph advances, nested text and rich-text visual reflow still need their own supported operation and render checks.
