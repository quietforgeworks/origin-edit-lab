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
    "fonts": {"latin": "Arial"}
  }]
}
```

Slide is one-based **display order**, resolved through presentation
relationships. Run is zero-based in document order; full shape text joins
paragraphs with newlines. Read the current XML for exact values rather than
guessing from screenshots. `size_pt` or `fonts` is required. Existing scientific
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
