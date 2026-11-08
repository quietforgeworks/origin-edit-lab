# FPC numeric stream encoder milestone, 2026-11-08

## Result

A deterministic, bounded, integer-only FPC encoder now accepts arbitrary exact binary64 representations and produces streams consumed by the verified external decoder. A separate reviewer independently wrote a raw decoder before inspecting the encoder, reviewed the final implementation, and found no codec correctness or resource-check defect within the stated scope.

Final core SHA-256: `43c3415066ed12f1f158e8406f6d62d1dc767daea537e31441865934e6c70dbc`.

Independent decoder SHA-256: `0ad34fbaedf86655085e6302d864a3456af6377f7d00e641a2879dbf79734d89`.

This result is an in-memory numeric-stream codec milestone only. It is not an OPJU writer, dataset rewrite, native graph generator, CFB/PPT editor, or Origin application acceptance test.

## Synthetic bitwise verification

The same 6,004 seeded/manual exact-bit cases (767,387 word occurrences) passed unchanged external-API compatibility, adapted external raw-bit comparison, independent integer decoding, and own integer decoding under both normal and optimized Python. Reports agree exactly after removing only the optimization-mode field.

The verified synthetic inputs include:

- 36,034 positive-zero and 36,895 negative-zero occurrences.
- 199,901 subnormal occurrences.
- 3,256 positive-infinity and 3,237 negative-infinity occurrences.
- 39,604 signaling-NaN and 45,802 quiet-NaN occurrences, representing 65,627 distinct NaN bit patterns across both signs.
- 3,308 exact Origin finite-missing-sentinel occurrences.

No conversion to float is used to generate, encode, independently decode, or compare source words. The independent and own raw codecs preserve all these bits. The external `_decode` implementation contains an application-level conversion of the finite sentinel to NaN. That is explicitly expected, not misreported as a numeric codec error. Its unchanged API is raw-bit exact on the 5,545 synthetic cases without that sentinel, while the other 459 cases match its documented normalization exactly. The separately labeled adapter disables only that mapping and retains every raw bit; it is not described as the unchanged API.

Portable author tests include 6,000 deterministic sequences spanning full uint64 randomness, special values, modular ramps/strides, repetition, collisions, one-bit changes, subnormals and NaN payloads. Separate reviewer tests include 3,000 arbitrary byte-stream differential cases and additional edge/random words. Eleven author test methods and 17 independent-review methods pass normally and with `-O`. Manual fixtures cover all residual widths and selectors, low/high ordering, FCM table/hash reuse, DFCM modular strides, wraparound, odd/even/empty counts and reset boundaries. Truncation, mutation, type checks, every undersized output budget for representative inputs, and the real one-million-word hard boundary also pass. These suites overlap in intended semantic coverage and are not summed into a larger unique-dataset claim.

## Genuine public native stream verification

All 167 allowlisted public input hashes were verified before and after both corpus runs. No source bytes changed.

- Original 110-source corpus: 4,496 FPC stream occurrences and 8,401,325 word occurrences, from all 110 files.
- Additional 57-source corpus: 3,347 stream occurrences and 1,548,672 word occurrences, from 49 files.
- Combined: **7,843 stream occurrences, 9,949,997 words, 159 source files with tested streams**. Counts describe occurrences, not a claim of that many statistically independent datasets.
- The 167 input entries represent 166 distinct source-file hashes. The 7,843 stream occurrences represent 6,245 distinct raw-bit/count pairs and 6,245 distinct encoded stream hashes.
- Largest tested public stream: 72,195 words. Source signatures span six CPYUA revision strings, listed in the detailed evidence.
- All 16 control nibbles occur in actual source streams, including zero-width FCM and DFCM codes.
- 5,439 streams / 8,885,112 words come from the strict parser's complete envelopes.
- 2,404 streams / 1,064,885 words are additional complete-envelope intervals reached through the opt-in matrix parser. Of these, 2,050 streams / 795,422 words are directly labeled experimental matrix framing; 354 others become reachable after traversing those records. These are not silently combined with strict-only parser support.

For every tested interval, the audit independently decoded the original native FPC bytes, packed the exact uint64 words, re-encoded them, and checked the re-encoded stream with both decoders and the external implementation. Original and re-encoded streams were also fed to the unchanged external API, with a deliberate appended trailer: their consumption ended exactly at the corresponding encoded extent and their outputs agreed. Sixty finite missing sentinels occur in 36 public streams; raw independent/adapted comparisons retain them, while unchanged-API comparisons explicitly allow only its documented missing-cell mapping.

**Observed byte identity is bounded:** all 7,843 re-encoded stream hashes match their corresponding original stream hashes in this corpus. Both total 48,918,617 encoded bytes. This is not a canonical-encoding guarantee, proof of matching Origin's policy on future inputs, a requirement for semantic interoperability, or evidence of full modern-file support. Synthetic and hand-written noncanonical streams demonstrate that the decoder accepts multiple valid representations.

Normal and `-O` public reports match exactly except for their optimization-mode field. `evidence/final-reconciliation.json` records report hashes and the agreement. Detailed result files retain public filenames, verified source hashes, exact offsets/counts, raw-word hashes, encoded hashes, sentinel counts, parser provenance and before/after hashes. They include no native data payloads.

## Bounded exclusions

The strict parser completed dataset lists for 149/167 inputs; the experimental matrix parser completed 159/167. These counts differ from “files with tested streams”: a file may have safely parsed earlier streams before a later outer-framing blocker, and a fully parsed file may contain no FPC stream.

The experimental parser stopped on one ambiguous raw-ULEB/encoded81 property transport, six unsupported repeat-tag forms, and one unsupported row-group type. The audit never guessed branches or searched for substitute byte patterns. Only streams within complete dataset envelopes were tested; pending/incomplete envelopes were excluded. Numeric repeat segments, string/index cells, virtual data and unknown codecs are not written or semantically generalized by this work. Nothing was recovered from images, render vectors or curve fitting.

## Independence and remaining risks

The two newly authored raw decoders and the encoder share a pinned-codec-derived specification. Independent implementation review catches coding errors but is not an independent vendor-format oracle. The external decoder is from previously approved source and is unmodified, with a separately disclosed raw adapter needed for sentinel normalization. Public specimen round trips are stronger than parser-self-consistency but still do not establish Origin's acceptance of newly generated data or modified native containers.

A strict stream decode does not validate its externally supplied count. Zero-width residuals can make smaller counts consume the same byte extent. Prefix offsets are not resume checkpoints. There is no checksum, so mutations may validly decode into different words. Boundaries, ownership, semantic row counts and integrity require outer-format validation.

Remaining native-write blockers include complete descriptor/property/segment framing, correct active/stored row metadata, safe variable-length section reconstruction and pointer relocation, preserved unknown bytes and object bindings, CFB allocation, graph/analysis dependencies, failure/recovery behavior, and real Origin open/edit/save validation. Native computations/models must be preserved or recomputed by an explicitly supported native route, never silently reimplemented or refit externally.

## Isolation and next gate

During the research experiment reported here, no Mac, VM, Origin application, external installation, private source dataset, stable repository change, native-container mutation, upload or publication was used. That statement records the experiment stage and is not a claim about later distribution of the package. The source-only candidate includes new code, tests, data-free evidence, scope documentation, references, the project MIT license for newly authored material, and hashes. It excludes local absolute-path mappings, native public/private files and third-party executable source. `CHANGESET.md` describes the net-new additions. Dataset/container writeback still requires a separate independent integration review and authorization; later source-package publication does not establish native acceptance.
