# Collaborate Figure Layout

Version **0.2.0**. A reusable scientific-figure collaboration skill with two entry modes: interactive rough composition and light refinement of an existing arrangement. Start with [SKILL.md](SKILL.md).

## Included

- Source-aware PPT inspection, panel grouping and layout exchange.
- A self-contained offline draggable HTML template; optional online source templates require a separate authorized deployment.
- Shared aesthetics, alignment proposals, measurable final-size quality checks and practical collaboration guidance.
- Bounded Python preview-edit utilities and a removable native PPT guide group for a single selected simple figure slide.
- A bounded checker of verified figure observations, synthetic quality-case generators, explicit ownership/occlusion/fidelity gates and composite-marker/ink-spacing regressions.
- Reviewed external-method references with explicit license and reuse boundaries.
- Synthetic regression tests. No scientific input files, measurements, runtime databases, user bindings, credentials or application binaries are distributed.

## Boundaries

The observation checker validates supplied source-verified measurements; it does not automatically recognize figures. In the original 12-case synthetic evaluation, the corrected result is four clean controls and eight flawed cases. A source-existing opaque inset was initially missed and then corrected; preserved bytes do not prove visibility. The checker's text-collision scope does not cover all non-text occlusions.


A composition preview is not an edited scientific source. The guide tool rejects source groups and AlternateContent and does not chain guides across a multi-figure deck. The included code is not a general Origin/OPJU writer and does not establish an available Windows MCP or Mac VM bridge. Actual Origin and PowerPoint open/edit/save/reopen validation is still required for claims about those applications.

## Installation

Unzip the standalone skill package and place the complete `collaborate-figure-layout` folder in your assistant's supported skills directory, for example `$CODEX_HOME/skills/` or `~/.codex/skills/` for Codex. Keep its subfolders together and start with `SKILL.md`. Installation does not authorize uploads, deployment or changes to scientific source files.

For the Python helpers, separately install Python 3.10+ and `lxml>=4.9,<7`, `Pillow>=10,<14`, `numpy>=1.24,<3` in your chosen environment. Node.js is needed for offline interaction tests. Inkscape and Liberation Sans are needed only for the rendered synthetic corpus. No runtime is bundled.

## Portable tests

Use Python 3.10+ with the repository Python requirements installed and Node.js for the offline interaction tests. From this directory:

```sh
python -B -m unittest discover -s scripts -p 'test_*.py'
python -B -m unittest discover -s tests -p 'test_*.py'
python -B -m unittest discover -s scripts/source_edit -p 'test_*.py'
python -B -m unittest discover -s scripts/figure_quality -p 'test_*.py'
node --test tests/offline_layout_controls.test.cjs
```

Repeat the Python commands with `-O` after `-B` to test optimized execution. The optional online backend is not configured by these commands; its [README](assets/web-layout/online/README.md) documents separate synthetic setup and checks. For the separately generated 22-test rendered corpus, follow [fixture instructions](references/figure-quality-fixtures.md) and keep output outside this skill. Rendering/application checks require their actual tools and are not implied by a unit-test pass.

## License and dependencies

The authored source and documentation are [MIT licensed](LICENSE). Python, Node.js and optional renderers are installed separately. The online template lockfile records separately installed MIT/Apache/BSD dependencies; it does not bundle their code or relicense them. No proprietary Origin/Office runtime or fonts are included. See the repository [third-party notices](https://github.com/quietforgeworks/origin-edit-lab/blob/main/THIRD_PARTY.md).

[Release notes](CHANGELOG.md) describe the versioned scope. `MANIFEST.json` records the exact SHA-256 of each packaged file except the manifest itself.
