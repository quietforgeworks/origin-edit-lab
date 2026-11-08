"""Experimental exact-size raw FPC encoder, NOT a native Origin file writer.

Fresh predictor state per call. Bit-exact immutable uint64 words, no floats.
Valid nonminimal residual widths supply size flexibility; no trailing padding,
fake values, altered count, or residual truncation is permitted.
"""
from __future__ import annotations

from dataclasses import dataclass

MAX_VALUES = 1_000_000
MAX_RAW_BYTES = 8 * MAX_VALUES
MAX_STREAM_BYTES = 8 * MAX_VALUES + (MAX_VALUES + 1) // 2
WIDTHS = (0, 1, 2, 3, 5, 6, 7, 8)
_MASK = (1 << 64) - 1


class ExperimentalFPCError(ValueError):
    """Invalid argument, hard/resource limit, or unreachable exact budget."""


class UnreachableBudgetError(ExperimentalFPCError):
    """No valid stream with this exact count and byte budget exists."""


class ResourceLimitError(ExperimentalFPCError):
    """The requested operation exceeds an explicit resource limit."""


@dataclass(frozen=True)
class BudgetAnalysis:
    """Exact reachable full-stream byte intervals, inclusive, at most two."""
    count: int
    control_bytes: int
    minimum_bytes: int
    maximum_bytes: int
    reachable_intervals: tuple[tuple[int, int], ...]


def _limit(value: int, name: str, ceiling: int) -> None:
    if type(value) is not int or not 0 <= value <= ceiling:
        raise ExperimentalFPCError(f"{name} must be an integer in [0, {ceiling}]")


def _count(raw_le: bytes, max_values: int) -> int:
    _limit(max_values, "max_values", MAX_VALUES)
    if type(raw_le) is not bytes:
        raise ExperimentalFPCError("raw_le must be immutable bytes")
    if len(raw_le) > MAX_RAW_BYTES:
        raise ResourceLimitError("raw_le exceeds hard byte limit")
    if len(raw_le) % 8:
        raise ExperimentalFPCError("raw_le length must be a multiple of eight")
    count = len(raw_le) // 8
    if count > max_values:
        raise ResourceLimitError("value count exceeds max_values")
    return count


def _minimum_width(residual: int) -> int:
    width = (residual.bit_length() + 7) // 8
    return 5 if width == 4 else width


def _scan(raw_le: bytes, count: int) -> tuple[bytearray, int, int, int]:
    """Return per-word minima, their sum, flexible count and width-3 count."""
    minima = bytearray(count)
    fcm = [0] * 4096
    dfcm = [0] * 4096
    fh = dh = last = total = flexible = threes = 0
    for index in range(count):
        offset = index * 8
        word = int.from_bytes(raw_le[offset:offset + 8], "little")
        residual = min(word ^ fcm[fh], word ^ ((last + dfcm[dh]) & _MASK))
        width = _minimum_width(residual)
        minima[index] = width
        total += width
        flexible += width < 8
        threes += width == 3
        stride = (word - last) & _MASK
        fcm[fh] = word
        dfcm[dh] = stride
        fh = ((fh << 6) ^ (word >> 48)) & 4095
        dh = ((dh << 2) ^ (stride >> 40)) & 4095
        last = word
    return minima, total, flexible, threes


def _hole(total: int, count: int, flexible: int, threes: int) -> int | None:
    """Unique missing payload sum, or None; see exact sumset proof in README."""
    if flexible == 0:
        return None
    if threes == flexible:
        return total + 1
    if flexible == 1:
        single_minimum = total - 8 * (count - 1)
        if single_minimum < 3:
            return total + 4 - single_minimum
    return None


def _reachable(target: int, total: int, count: int,
               flexible: int, threes: int) -> bool:
    return total <= target <= count * 8 and target != _hole(total, count, flexible, threes)


def analyze_exact_budgets(raw_le: bytes, *, max_values: int = MAX_VALUES) -> BudgetAnalysis:
    """Return every mathematically reachable size under this stream grammar.

    Limits are algorithmic hard caps, not whole-process memory/wall-clock
    quotas. No native framing, cell meaning or application acceptance inferred.
    """
    count = _count(raw_le, max_values)
    _, total, flexible, threes = _scan(raw_le, count)
    controls = (count + 1) // 2
    low, high = controls + total, controls + count * 8
    hole = _hole(total, count, flexible, threes)
    intervals = ((low, high),) if hole is None else (
        (low, controls + hole - 1), (controls + hole + 1, high))
    return BudgetAnalysis(count, controls, low, high, intervals)


def encode_bits_exact_budget(raw_le: bytes, budget_bytes: int, *,
                             max_values: int = MAX_VALUES,
                             max_output_bytes: int = MAX_STREAM_BYTES) -> bytes:
    """Encode exactly budget_bytes or raise without returning a partial stream.

    Deterministic choices: smaller unsigned residual (FCM on equality), then
    lexicographically smallest width sequence that admits a valid suffix.
    This retains the minimal baseline bytes at the minimum budget. Enlarged
    widths store zero high bytes *inside* each residual, never arbitrary padding.
    Each call resets state; count remains exactly len(raw_le)//8, external to
    the stream. Hard caps cannot be enlarged by caller-supplied limits.
    """
    count = _count(raw_le, max_values)
    _limit(budget_bytes, "budget_bytes", MAX_STREAM_BYTES)
    _limit(max_output_bytes, "max_output_bytes", MAX_STREAM_BYTES)
    if budget_bytes > max_output_bytes:
        raise ResourceLimitError("budget_bytes exceeds max_output_bytes")
    controls = (count + 1) // 2
    if not controls <= budget_bytes <= controls + count * 8:
        raise UnreachableBudgetError("budget is outside count-dependent bounds")
    minima, total, flexible, threes = _scan(raw_le, count)
    remaining = budget_bytes - controls
    if not _reachable(remaining, total, count, flexible, threes):
        raise UnreachableBudgetError("budget is not in this input's exact reachable set")
    if not count:
        return b""

    # Allocation is checked above. In-place filling avoids unbounded growth.
    out = bytearray(budget_bytes)
    fcm = [0] * 4096
    dfcm = [0] * 4096
    fh = dh = last = position = 0
    for index in range(count):
        if index % 2 == 0:
            control_position = position
            position += 1
        minimum = minima[index]
        total -= minimum
        flexible -= minimum < 8
        threes -= minimum == 3
        suffix_count = count - index - 1
        chosen = None
        for width in WIDTHS:
            if width >= minimum and _reachable(remaining - width, total,
                                               suffix_count, flexible, threes):
                chosen = width
                break
        if chosen is None:
            raise ExperimentalFPCError("internal reachability invariant failed")
        remaining -= chosen
        offset = index * 8
        word = int.from_bytes(raw_le[offset:offset + 8], "little")
        a = word ^ fcm[fh]
        b = word ^ ((last + dfcm[dh]) & _MASK)
        selector = 8 if b < a else 0
        residual = b if selector else a
        if residual.bit_length() > chosen * 8 or position + chosen > budget_bytes:
            raise ExperimentalFPCError("internal encoding bound failed")
        code = chosen if chosen < 4 else chosen - 1
        out[control_position] |= (selector | code) << (4 * (index % 2))
        out[position:position + chosen] = residual.to_bytes(chosen, "little")
        position += chosen
        stride = (word - last) & _MASK
        fcm[fh] = word
        dfcm[dh] = stride
        fh = ((fh << 6) ^ (word >> 48)) & 4095
        dh = ((dh << 2) ^ (stride >> 40)) & 4095
        last = word
    if position != budget_bytes or remaining:
        raise ExperimentalFPCError("internal final-size invariant failed")
    return bytes(out)
