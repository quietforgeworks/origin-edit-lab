# Reproduce the bounded reader experiments

Use a disposable Linux directory. No step requires or uses an Origin installation, user project, Mac or VM. These commands intentionally refuse existing candidate directories and existing application case/profile names. They do not download dependencies or fixtures.

## Prerequisites

1. Obtain the official LabPlot 2.12.1 runtime separately. Verify the AppImage SHA-256 `1b700d60b3297a987022cfc532e413b8211ef917059a21155d8b5604f3012a82` and the extracted executable/library hashes in `evidence/source-provenance.json`. This ABI observer is not suitable for another version.
2. Set `LABPLOT_EXTERNAL_VIEWER_ROOT` to your explicitly chosen runtime directory containing `squashfs-root/` and matching Qt6 development headers under `debian-runtime/usr/include/x86_64-linux-gnu/qt6`. A Linux C++ compiler is required. Runtime/header acquisition and installation are deliberately outside these scripts.
3. Obtain the three pinned public KDE fixtures linked in README into a local `fixtures/` directory. Check their SHA-256 values. Native files are not distributed with this source package, and this documentation does not grant fixture redistribution rights.
4. Run both test modes. With all three fixtures, both should pass 47 test methods without skips:

```sh
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -v
bash application/build.sh
```

## Eight style candidates and ten application observations

Run from this source directory. Candidate generation accepts only the exact original fixture hash, never a previously modified candidate.

```sh
mkdir -p candidates
for profile in two_graphs single_axes; do
  if [ "$profile" = two_graphs ]; then
    input=fixtures/2graphs.opj
    rect='[1351,721,5337,3955]'
  else
    input=fixtures/single_layer_two_axes.opj
    rect='[790,446,2641,1976]'
  fi
  bash application/run.sh "$profile-baseline" "$input" coordinate
  for field in xb_tick_font xb_axis_width curve_line_width layer_rect; do
    case "$field" in
      xb_tick_font) value=26 ;;
      layer_rect) value="$rect" ;;
      *) value=1250 ;;
    esac
    python native_style_patch.py patch --profile "$profile" --input "$input" \
      --field "$field" --value "$value" --out "candidates/$profile-$field"
    bash application/run.sh "$profile-$field" "candidates/$profile-$field/candidate.opj" coordinate
  done
done
python verify_results.py --evidence-root .
python -O verify_results.py --evidence-root .
```

The validator re-generates each candidate from its pinned original, compares the full manifest, verifies restoration, verifies import-input hashes, then checks app-owned serialization and direct native Column double readback. The two projects have 128 and 64 allocated numerical cells respectively; this count includes allocated empty cells. The source masks and binary64 bits are separately preserved byte-for-byte. App readback equality is baseline-versus-candidate equality, not a claim that the importer preserves every original missing-value encoding.

XML acceptance compares all tags, attributes, text and tails exactly except `uuid` and `creation_time` attributes, plus the root project's `dockWidgetState`, `modificationTime` and `thumbnail` attributes. The latter three are hashed before exclusion. This is serialized app-state comparison, not proof of complete undocumented Origin semantics.

## Separate title font22-to30 diagnostic

This third fixture is [strings_testing.opj at the pinned KDE commit](https://github.com/KDE/labplot/blob/0bd2e4094e92e74052ec161022d4e60aeb7605cd/tests/import_export/Project/data/strings_testing.opj): 344,049 bytes, SHA-256 `8d1e26543e77942faef097a3cdc05ba4a78d2b0d667c9edb9003074b4e0443ed`.

The guarded helper verifies that exact source and its YL title framing, then changes only absolute byte offset 147865 from 22 to 30. The resulting candidate must hash to `07185039711b4b3e1eedeec31c91e6b7a8707720d1698d9a639312719667d35d`. Every other byte is identical and restoration returns the exact source hash. It rejects arbitrary projects and repatching. This is a one-case reader diagnostic, not additional supported title-editing functionality.

```sh
python font_boundary_candidate.py --input fixtures/strings_testing.opj \
  --out candidates/title-font30
bash application/run.sh strings-probe-baseline fixtures/strings_testing.opj coordinate
bash application/run.sh strings-probe-font30 candidates/title-font30/candidate.opj coordinate
```

The two `application/results/strings-probe-*/font-boundaries.jsonl` logs should show `plain: "Log of x"` passing through `QTextEdit::setFontPointSize` at 26 and 36 points respectively, followed by `QTextEdit::setCurrentFont` with `Sans Serif,9,...`. Before the latter call the HTML contains the requested 26pt/36pt span; after it, the HTML font size is 9pt. The pinned executable's caller image-relative return offset is `7657e0` (load base `400000`, return virtual address `b657e0`). `TextLabel::setText` interposition has zero observations in this build; no symbolic TextLabel stack is claimed.

The two app-owned saved projects should retain the same 9pt YL title. The observer calls the real Qt functions with unchanged arguments and obtains the output through normal GUI import/save. It never constructs replacement plots or overrides import properties.

## Interpretation limits

The runner deliberately ends its offscreen event loop after eleven seconds; successful runs contain a completed app-owned save and record timeout status 124. Slow environments may fail this observation schedule and require manual timing adjustment; a missing output is not a pass.

Screenshots show parameter sensitivity, not good typography. Enlarged ticks and reduced plotting areas can overlap labels. Neither these runs nor tests validate Origin reopen/save/recalculate, modern OPJU/OGGU, arbitrary documents, font-family mapping, exact Origin UI units or native algorithm execution.
