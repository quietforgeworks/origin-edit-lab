# Collaborate Figure Layout — V1

Start with [SKILL.md](SKILL.md). The workflow supports interactive local arrangement and light refinement of existing scientific figures, with source preservation and shared final-scale aesthetic review.

## Workflow and capabilities

- Identify source panels and native objects; use a local saved-state workbench when interactive arrangement is requested.
- Interpret guides as alignment relationships. Derive positions, typography and whitespace from the source/reference aesthetics.
- Apply supported native PPT, per-object cache or explicitly selected native Origin operations. Preserve OLE data and native editability.
- Correct type size, tracking, line/paragraph gaps, collisions, and stretched plot/legend symbols. Use the [operation map](references/operation-map.md) and [quality matrix](references/quality-specification.md#review-matrix-and-correction-order).
- Use compact state reads, reuse compatible decisions and evidence, record explicit chat confirmation of a reviewed revision, and publish under short revision-checked locks.

## Installation and dependencies

Place the complete `collaborate-figure-layout` folder in the supported skills directory, such as `$CODEX_HOME/skills/` or `~/.codex/skills/`. Keep its subfolders together. No private figures, source profiles, project state, fonts or runtimes are bundled.

Python helpers require Python 3.10+ and `lxml>=4.9,<7`, `Pillow>=10,<14`, `numpy>=1.24,<3` as applicable. Node.js runs the interaction tests. Inkscape and Liberation Sans are needed only for the separately rendered synthetic corpus. Install dependencies in the chosen environment; availability is not implied by this package.

## Validation

From the skill directory, run the suites relevant to a changed operation; a release audit uses all of these:

```sh
python -B -m unittest discover -s tests -p 'test_*.py'
python -B -m unittest discover -s scripts -p 'test_*.py'
python -B -m unittest discover -s scripts/source_edit -p 'test_*.py'
python -B -m unittest discover -s scripts/native_ppt -p 'test_*.py'
python -B -m unittest discover -s scripts/native_origin -p 'test_*.py'
python -B -m unittest discover -s scripts/figure_quality -p 'test_*.py'
node --test tests/*.test.cjs
```

Repeat changed guard implementations with `-O` after `-B`. The local HTTP integration test binds a temporary loopback port. The optional [online backend](assets/web-layout/online/README.md) and [rendered corpus](references/figure-quality-fixtures.md) have separate synthetic setup. Do not deploy or upload to run a local audit.

Tests do not certify a new user figure's appearance or native application lifecycle. Real PowerPoint display, Origin reopen/refresh, conversion fidelity and final glyph/marker readability remain per-task checks. These are bounded editors and validators, not a universal Origin writer or automatic bridge launcher.

## License and release identity

Authored code and documentation use the [MIT license](LICENSE). Dependencies retain their own licenses; the online lockfile does not bundle or relicense them. See the repository [third-party notices](https://github.com/quietforgeworks/origin-edit-lab/blob/main/THIRD_PARTY.md).

[CHANGELOG.md](CHANGELOG.md) records versioned scope. `MANIFEST.json` records the exact SHA-256 of all packaged source files except itself.
