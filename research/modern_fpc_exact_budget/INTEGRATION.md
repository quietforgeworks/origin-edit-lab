# Publication integration record

## Frozen source and audit

The original source-only archive `origin-exact-budget-fpc-r2.source-only.tar.gz` has 44 files, 44,068 bytes, SHA-256 `b72092fdabe68e80a3031b922163c5234fbe770ec5e0fd1d54384fb95c7f1991`. Its extracted contents are retained unchanged in `snapshot/`, including the original manifest and checksum inventory. Its historical unpublished/candidate labels describe the state at freeze; this integration publishes that reviewed research without promoting native support.

Independent review: [`PORTABLE_PUBLIC_AUDIT.md`](snapshot/audit/PORTABLE_PUBLIC_AUDIT.md), SHA-256 `63936bda1e969f285be36fd385c732ca242f435e55e87a579fa6c7ad8707c411`. This audit applies to the frozen snapshot, not the additional repository wrapper.

Integration baseline: public commit `67c3fd8d1f236c4470b4b58558f0d49037202d67`. Only this new research module, the root README, test index, validation document and current source-package inventory change. All existing skill and scientific source files retain their exact baseline bytes. Skill version and tag `skill0.2.0` are unchanged.

## Verification distinction

- Newly rerun after relocation: 14 codec/contract unittest groups in normal and optimized Python; six repository-packaging tests per mode.
- The standalone oracle was rerun in disposable relocated copies in both modes: 125,970 width multisets, 1,111 streams and 63,627 serialized schedules.
- The standalone adversarial review was rerun in those copies in both modes: 12,465 accepted budgets, 18,656 refused budgets, 43 invalid calls and two million-word boundary streams.
- Frozen independently reproduced historical evidence: 1,264 synthetic encodings and 13 public exact-budget successes, with 430 additional malformed/tampered-input refusals per mode. The repository suite validates those reports, not their external inputs or execution again.
- Current full-repository suite: 759 tests per mode, 556 pass and 203 explicitly skip with the optional system liblz4 available; without it one additional test skips. These counts do not include the separate skill/corpus suites, whose version 0.2.0 evidence remains unchanged.

The repository runner never fetches external sources or launches Origin, PowerPoint, a VM or bridge. Native Origin cold-open, edit, save, reopen and export remain **NOT_RUN**. No native artifact or Origin-generated image is produced.

## Reproduction

`sha256sum -c SHA256SUMS` from `snapshot/` verifies the frozen payload. The root source-package manifest includes the new module and wrapper files. Snapshot scripts that emit JSON should run in a disposable copy; generated outputs are not added to the published tree.

Optional public-source and external-decoder reproduction needs the already-approved pinned sources and files listed in `snapshot/package/SOURCES.md`, plus NumPy. These inputs are not bundled or downloaded by this integration. The historical lineage audit needs the prior reports with their documented public hashes and relative layout. Its directory name `native-workbook-v2` is a generic research fixture version, not private presentation data.

The archive and snapshot exclude native source bytes, private scientific content, raw public measured values, third-party implementation sources, local input mappings and runtime binaries. Included logs contain only generic synthetic test names/counts and test evidence, not private diagnostic logs. All bundled source retains MIT attribution; optional quantized/public-input licensing is unchanged.
