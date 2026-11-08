# Independent review: legacy native allocation expansion

The original findings below describe the pre-integration reviewed snapshot.
The post-review note at the end records current source-only packaging and
wrapper hardening; the historical author-freeze manifest is not a current inventory.

## Decision

Accepted as a **source-only, exact-fixture, LabPlot-only research supplement** after the path-safety corrections below. No blocking defect remains within that stated research scope. This is **not approval for native-safe Origin export**. The default export refusal is necessary and remains tested.

The final source manifest SHA-256 is `5fdea6c70275c3547e5b5aab88da9307938baee8b53cb2ff9a3e3c183848d7ab`. Its 30 authored/source/compact files were independently checked before copying. The reviewed package adds this review, an independent verifier and compact independent evidence; it does not add native samples or third-party implementation.

## Findings and severity

1. **Medium, fixed: nested symlink output redirection.** Initially `generate()` checked only the output and immediate parent. An ancestor alias such as `alias/child/out` was accepted and published under the symlink target. The final revision checks all lexical components for input/output paths, rejects `..`, repeats the preflight before publication, and checks runner input/profile/runtime paths. Independent reproduction now rejects without output. This is preflight hardening under a trusted, stable directory-tree assumption, not protection against a hostile process concurrently replacing ancestors.
2. **Medium, fixed: wrapper wrote before refusal.** Initially a symlinked `make_cases` candidates directory received `raw51.csv` before `generate()` rejected the path. The wrapper now validates its fixture, candidates directory, destinations and CSV paths before access. A new CSV uses exclusive `xb` creation; a raced-in file is preserved. Independent reproduction now leaves the symlink target empty. Added regression tests cover these cases.
3. **Native compatibility blocker, intentionally unresolved.** Worksheet A/B and curve payload fields at `+7/+11` remain `(0,50)`; opaque absolute pointers and other dependent metadata have not been ruled out. Byte preservation after relocation does not establish their semantic validity. Both API and CLI require an explicit LabPlot-only research opt-in, even for passing sizes. Origin reopen, redraw, update, recalculation, native save and saved-native-file reopen remain **NOT RUN**.

No claim is made for a filesystem sandbox, crash durability, arbitrary Origin projects, arbitrary row counts, multiple curves, OPJU/OGGU, or private-template sanitization. `renameat2(RENAME_NOREPLACE)` provides atomic no-overwrite directory publication on the supported Linux system. Injected pre-publication failure cleans staging; a concurrently created destination is retained unchanged. A killed process can still leave staging artifacts, and persistence across system failure was not tested.

## Independent scientific checks

The original public fixture was verified by exact SHA-256. All three candidates were regenerated from synthetic CSV and independently examined with a separate sequential-frame checker:

- 51 rows: 231,514 bytes; 102 X/Y cells checked bit-for-bit.
- 257 rows: 235,634 bytes; 514 X/Y cells checked bit-for-bit.
- 1024 rows: 250,974 bytes; 2,048 X/Y cells checked bit-for-bit.

Every payload tag and binary64 value matched the CSV conversion. The only permitted changes are the two dataset headers' total/end fields and their two self-framed data records. Every other frame and the entire original suffix from offset 1,412 are identical after relocation. All 478 frames, all dataset IDs/order and the opaque tail survive unchanged. Each rollback is byte-identical to the original. The graph's native byte hash is unchanged.

The conversion ledger explicitly records decimal rounding, exact represented value, sign and binary64 bits. Signed zero is checked before and beyond the former boundary. Nonfinite values, the Origin missing sentinel, zero-underflow, subnormals, lossy integer conversion, unsupported row counts, malformed CSV and values outside the unchanged axes are refused. These are deliberately narrow input rules, not a general numerical importer.

## Actual application evidence

The reviewer rebuilt the authored observer and used the official LabPlot 2.12.1 executable and importer library with their pinned hashes. The rebuilt observer SHA-256 is `3c4df197b6c6c960a44d31bf3f1a704580d63ba119ea927881c02925f2b7aa2a`.

Fresh original/51/257/1024 imports ran in separate reviewer-owned result directories and HOME/XDG/temp profiles. The review read the captured actual public Column API data and passive Qt signal arguments, not just author report flags. The separate checker found:

- Exactly 102/514/2,048 actual API cell values matching every expected binary64 bit.
- Two actual `pointsUpdated` emissions per candidate, containing exactly 51/257/1,024 expected logical points and ranges 0–50/0–256/0–1023.
- The curve's own bound columns contain exactly the expected valid, unmasked source rows.
- The application-owned saved LML double arrays match the actual API values bit-for-bit.
- The complete Graph2 object, including A/B source bindings, axes and style configuration, is unchanged except generated UUID/creation timestamps.
- After replacing only A/B row attributes and numeric payloads with the original values, the entire parsed project matches. Only generated UUID/creation timestamps and root dock state/modification time/thumbnail are excluded. XML text and tails are compared exactly, without whitespace stripping.
- The original 100 API values and its 50-point curve emissions also match the original native cells.
- Original inputs, imported snapshots and before/after hashes are linked and unchanged.

The actual 257-row graph pixels were separately inspected: the synthetic two-cycle curve is visible, including the explicit zero dips, with native black square markers and axes. Pixel inspection is supplementary, not a point-count or bit-precision proof. Planned timeout status 124 follows capture and Save As; it is not represented as a natural application exit.

Official release source was read only to verify dataset field offsets, sequential record behavior, vector-based allocation, active-row copying, QObject model identity and the `pointsUpdated` signature/render location. The archive SHA-256 and inspected member hashes match the recorded provenance. The observer has no Origin parser, numerical replacement data or manual recalc. No Origin executable, Mac, user VM or private PPT was used.

## Tests and reproducibility

- Final author suite: **53 tests pass** with the external public fixture, normally and with `python -O`.
- Source-only suite: **24 pass, 29 explicitly skip**, normally and optimized.
- Separate independent native/application checker: passes normally and optimized.
- Author's complete application verifier: passes against independently generated application evidence, normally and optimized.
- Shell syntax checks pass.
- Independent static nested-alias tests reject after correction, raced destination remains untouched, and injected publication failure leaves no final output or staging leak.

The portable independent checker can be run after recreating the author's candidates and real application observations:

```sh
python review/independent_checks.py "$ORIGIN_PUBLIC_FIXTURE" --evidence-root .
python -O review/independent_checks.py "$ORIGIN_PUBLIC_FIXTURE" --evidence-root .
```

It prints a compact result and writes only if a new `--output` filename is supplied. The app runtime and exact fixture are external prerequisites, not bundled or downloaded by this package.

## License and package boundary

The existing MIT project license is unchanged and applies to authored material. The inspected LabPlot/liborigin implementations are GPL-licensed and remain external; none of their implementations, headers or source archives is copied into the package. The authored observer uses Qt headers and existing application APIs; no observer binary, linked runtime or claim to relicense third-party software is included. Any future binary distribution needs its own dependency/license review.

The allowlisted package contains authored source/tests/docs, synthetic CSV, compact reports, hashes and test logs. It excludes native fixture/candidate/rollback files, manifests containing original source bytes, full application saves, full source-bearing comparison reports, screenshots, compiled objects, runtimes, profiles, third-party source and private user data. No publication, remote checkout change or stable-skill edit was performed.


## Post-review integration hardening (2026-11-08)

The pending source-only package now requires an explicit
`make_cases.main(research_only=True)` or CLI `--labplot-only-research` before
reading the fixture environment variable, inspecting task inputs or creating
outputs. Refused CLI invocations also avoid import bytecode. Existing path,
prewrite and concurrent-CSV tests pass the flag so those guards remain exercised.

Six new tests cover default/nonliteral opt-in refusal, no environment/path
access, no output and actual API/CLI opt-in regeneration. All **59 tests pass**
normally and with `python -O`; without the fixture, **28 pass and 31 skip**.
All three opt-in candidate hashes match the previously reviewed 51/257/1024
outputs. Native generation, numeric support, observer, synthetic CSV and frozen
historical manifest bytes are unchanged. No Origin, Mac, VM or new application
run was needed, and no numerical capability or compatibility claim was added.

README and REPORT now describe the current source-only contents and excluded
local regeneration outputs. `PACKAGE-INVENTORY.json` is refreshed for current
files. `evidence/source-freeze-manifest.json` remains unchanged historical
pre-public-packaging evidence, with its old hashes preserved. Current checks
are in `review/evidence/post-integration-*.log` and
`review/evidence/post-integration-summary.json`. This work changed staging only;
no upload, publication or outer publication manifest update was performed.
