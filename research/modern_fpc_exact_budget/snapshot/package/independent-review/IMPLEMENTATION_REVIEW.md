# Independent implementation review

Reviewed target SHA-256: `982b2c9119e8a460bcd850e46db14268164dc28a78faf38fc4153123e2031e25`.

No correctness or fail-closed defect was found within this review scope. The target matches the independently derived reachable-size classification. The independent oracle and proof were authored before inspecting the implementation.

## Executed checks

Both independent harnesses passed in ordinary Python and `python -O`; all check conditions use explicit exceptions, not removable assert statements. Hash-pinned dependencies are compiled and executed from the exact source bytes whose hashes were checked.

- 125,970 minimum-width multisets, every multiset through length 12, compared direct sumset enumeration to the closed-form classification.
- 1,111 word streams over a 10-value boundary alphabet, lengths 0 through 3, totaling 63,627 directly serialized width schedules checked against the separately written decoder.
- Target checks on 1,351 streams: exhaustive short alphabet streams and 240 deterministic seeded streams covering arbitrary uint64s, signed zero, infinities, subnormals, signaling/quiet NaN payloads, wrapping strides, and repeated zeros/hash collisions.
- 12,465 accepted budgets checked for exact size, immutable-byte output, word-bit equality, no trailing data, reset/determinism and zero unused high nibble.
- 18,656 unreachable budgets rejected, including interior holes and count-bound failures.
- Lexicographically smallest width schedules compared with independent schedule enumeration for all tested streams of length 0 through 2.
- Minimum-budget output matched the SHA-pinned baseline encoder for every tested stream.
- 43 malformed or limit-exceeding calls rejected: wrong raw types, malformed byte lengths, boolean/noninteger/negative/oversized parameters, hard-cap inflation, and explicit reduced resource limits.
- Exact hard input cap: 1,000,000 zero words analyzed; both minimum (500,000 bytes) and maximum (8,500,000 bytes) output were encoded, completely independently decoded, and control positions inspected.

## Static resource and algorithm review

Input is restricted to exact immutable bytes, so arbitrary iterators/subclasses cannot alter scan behavior. Raw byte and count limits are checked before per-word allocation; output budget and caller cap are checked before output allocation. Caller limits cannot enlarge the hard caps. Invalid count-dependent ranges are rejected before scanning. Reachability holes are rejected after scanning, before output allocation.

The implementation makes two bounded passes and at most eight width candidates per word; no dynamic-programming table grows with the budget. Working storage is O(n), with a one-byte minimum-width array, two fixed 4,096-entry tables and a bounded output array. Returning immutable bytes temporarily duplicates the output buffer; the caps are not a whole-process memory quota, correctly disclosed in the API.

At each encoding step the chosen width leaves a reachable suffix. Since predictor state depends solely on the original words, choosing an enlarged residual cannot change later minima. The selected smaller numeric residual has the smallest required width and remains valid at every larger selected width. Each residual is little-endian and contained within its chosen width. Final position and residual budget are explicitly checked even under optimized Python. Empty input has exactly the empty output.

## Limits

This review validates only the supplied raw grammar and module. It does not demonstrate native Origin container compatibility, compressed-stream framing acceptance, cell semantics, graph/style preservation, or successful native application opening. No native Origin files, original decoder, or baseline encoder were modified. The hard-cap runtime tests use zero data; varied-bit behavior was tested on smaller streams.
