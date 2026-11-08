# Independent exact-budget reachability

This is a proof for the supplied raw FPC grammar, not evidence that Origin accepts such bytes.

For word i, both predictor residuals are fixed by the preceding words. The encoding selector/width never changes subsequent predictor state. Let m_i be the smallest member of W=(0,1,2,3,5,6,7,8) that contains either residual. The union of both predictors' allowed widths is exactly {w in W : w >= m_i}. A predictor achieving m_i also supports all those widths.

Thus the byte lengths are exactly C + S_1 + ... + S_n, where C=ceil(n/2). L=C+sum(m_i), U=C+8n. A correct encoder must reject holes inside [L,U], in addition to rejecting outside that interval.

## Exact closed-form holes

Ignore all m_i=8 (they are fixed-width). Call the remaining multiset A.

- A empty: only L=U is possible, including n=0 and length 0.
- A consists entirely of 3s: [L,U] except L+1.
- A has one element m in {0,1,2}: [L,U] except L+(4-m).
- Every other case: all integers in [L,U].

## Proof

Subtract each minimum. Individual slack sets are:

- m=0: {0,1,2,3,5,6,7,8}
- m=1: {0,1,2,4,5,6,7}
- m=2: {0,1,3,4,5,6}
- m=3: {0,2,3,4,5}
- m=5,6,7,8: integer intervals [0,3], [0,2], [0,1], [0,0], respectively.

A sum of k positive m=3 slack sets is {0} union [2,5k], by induction, so slack 1 is impossible and all others through its cap are possible.

Every pair of nontrivial slack sets, unless both are m=3, has a contiguous sum interval. For two m<=2 sets, the single missing value of each is supplied by splitting it across two available values. For m<=2 plus m=3, the latter supplies a split for the former's hole while the former supplies slack 1. For an interval with positive capacity plus any set, adjacent translates overlap or meet because no individual slack set has a gap exceeding one missing integer. The resulting interval has capacity at least 2. Adding any further slack set preserves contiguity: its successive available values differ by at most 2, and translated intervals of length at least 2 overlap or meet. Adding width-8 words has no effect on slack.

## Brute force design

The oracle is independent of the target implementation. It enumerates sums directly rather than using the formula, checks every minimum-width multiset through length 12 against the formula, and exhaustively enumerates width schedules of short actual word streams. It serializes those schedules and verifies with the existing separately implemented raw decoder, whose hash is pinned before import. This checks residual containment, little-endian bytes, nibble order, fresh state, count handling, and unused odd high nibble zero.
