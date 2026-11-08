# Independent review of separate custom-data research

Scope: Linux-only fixed50 single-curve active7/49/50 adapter. Read-only review of the source package, temp-copy adversarial checks, and revalidation of existing actual application observations. No fresh application or Origin run was performed by this reviewer. No stable-workbench or reviewed-package source was modified.

## Findings

- Native generation writes the converted binary64 values into the pinned OPJ dataset cell slots, retaining existing graph bindings and serialization. It is not a preview substitution. Every bundle artifact is regenerated from the pinned original, raw CSV and declaration and compared byte-for-byte.
- Raw CSV and declaration remain byte-exact; the per-cell conversion ledger distinguishes exact source decimal text, native binary64 representation, signed zero and rounding. Caller-declared measured data is not relabelled synthetic or authenticated.
- Verification and recovery require separate input hashes. Coordinated replacement cannot pass against unchanged external anchors. Recovery verifies the whole bundle before creating a no-overwrite directory with the exact original, raw CSV and declaration.
- Supported native input/output paths have bounded regular-file checks, symlink and lexical traversal rejection, read identity checks and explicit Linux no-overwrite publication. Trusted stable ancestors and no crash durability are appropriately stated limitations.
- All three vendored modules are byte-identical to the existing reviewed frozen active-row copies and match the pinned hashes.
- Observer code reads real application column APIs and passively records real XYCurve point signals. Independent expected values come from original CSV conversion. Saved LML values and graph bindings/configuration are cross-checked; native snapshots are exact. Numerical checks do not rely on screenshots.
- Existing application observations for 7, 49 and 50 rows all revalidated PASS against the separate input CSV/declaration files. This establishes those recorded LabPlot importer observations, not Origin lifecycle behavior.

## Review finding requiring correction

The initial source auditor rejected symlink directories for src/tests/inputs/evidence but failed to check the application directory itself. A temp source copy with application symlinked to the unchanged original application directory passed the externally anchored manifest audit. This does not defeat native bundle regeneration or change native values, but weakens the advertised source path guard. Reported immediately to the parent; final resolution and digest are recorded below when verified.

## Scope limits

Origin open/edit/update/recalculate/native save/close/reopen remain NOT_RUN. Unknown native range-like fields are retained, not interpreted. Native inactive template cells remain in 7/49 cases; unrelated template contents remain in every case. Binary64 conversion is not arbitrary-precision native storage. Only the exact public template, row counts and axes are supported.

Runtime pinning covers the executable, importer library, launcher and authored observer, not all transitive runtime dependencies. Local reports are not cryptographic execution attestations; a coordinated fabricated observation set is outside this trust model. No generic Origin compatibility, native-safe export, new sheet creation, OPJU, sanitization, Mac write support or stable integration is approved by this review.

## Final resolution and verdict

The application-directory symlink hole was fixed by the author and regression-tested. Independently repeated the temp-copy symlink attack after the fix: rejected. The author also hardened both strict JSON parsers against exponent overflow (1e999), plus source-directory FIFO handling. Independently checked both parsers reject positive/negative exponent overflow and NaN/Infinity literals. Updated documentation now explicitly states the incomplete runtime dependency pinning, non-attestation boundary and native no-op refusal.

Final source manifest externally supplied by parent and verified by this reviewer: SHA-256 `3b56217e1b537a61bcc6726b7110114bde0ecfe40d83fc0acb48000b6ef94645`, 45 files, 145428 bytes. Independent source-audit suites pass 3/3 normally and under -O. Independent native suites passed 14/14 normally and under -O; application suites passed 5/5 normally and under -O during review. These longer suites began before the final small JSON/source-audit hardening; final changes were separately inspected and targeted regressions repeated. The author reports full normal/-O suites also passed after the final hardening. All three actual application observations were independently revalidated again against the final source and external input files.

Verdict: PASS for this narrowly scoped local source-integrity adapter and recorded LabPlot importer evidence, with no unresolved blocker found. This is not approval for Origin compatibility or dependable native-safe export. Origin lifecycle remains NOT_RUN and actual Origin testing is still required before those claims.

Evidence: `final-source-audit.json`, `independent-app-revalidation.json`, and six normal/optimized test logs in this review directory.
