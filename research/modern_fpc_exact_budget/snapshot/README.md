# Exact-budget FPC research candidate, revision 2

This unpublished, source-only archive completes a bounded raw numeric codec and portable/public harness review. It is not a native Origin writer and has not been accepted by the Origin application. Publication or capability promotion requires parent review.

- Start with `package/README.md`, then `package/REPORT.md`.
- Codec/source tests and historical core proof are in `package/`.
- Newly independent public-harness review and evidence are in `audit/PORTABLE_PUBLIC_AUDIT.md` and adjacent files.
- `MANIFEST.json` records payload hashes; `SHA256SUMS` covers the payload and that manifest. Run `sha256sum -c SHA256SUMS` from this directory.
- Run tests from `package/` in a disposable extracted copy. The independent scripts emit generated result JSON; immutable frozen evidence remains in `package/results/`.
- The optional audit script uses `--package PACKAGE_DIRECTORY --research-root HISTORICAL_RESEARCH_ROOT`. The historical root must contain the prior research/provenance reports and already-approved dependency/public-source trees described in `package/SOURCES.md`. It does not retrieve missing inputs. Run in a disposable copy because it writes audit results beside itself.

Included: generic code, synthetic tests, public metadata, license, reports and hashes. Excluded: user files, native source files, raw public scientific values, third-party software, binaries, credentials and local absolute input mappings. Original paused evidence is unchanged in its original location.

Numeric exact-budget and raw-bit preservation checks passed. Native dataset/page/container serialization is not implemented here. True Origin cold-open/save/reopen/export and PowerPoint OLE lifecycle validation were not run. No Origin-produced image is included.
