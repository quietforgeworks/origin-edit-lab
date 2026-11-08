"""Bounded, exact-bit FPC numeric streams. Not an OPJU/container writer.

Input/output binary64 representations are opaque eight-byte little-endian
words. No floating-point conversion or missing-cell normalization is performed.
Each call starts fresh predictor state. No external dependencies or file I/O.
"""
from __future__ import annotations

MAX_VALUES = 1_000_000
MAX_RAW_BYTES = MAX_VALUES * 8
MAX_STREAM_BYTES = MAX_VALUES * 8 + (MAX_VALUES + 1) // 2
_MASK64 = (1 << 64) - 1
_WIDTHS = (0, 1, 2, 3, 5, 6, 7, 8)


class FPCError(ValueError):
    """Invalid arguments, exhausted budget, or malformed/truncated stream."""


def _limit(value: int, name: str, ceiling: int) -> int:
    if type(value) is not int or not 0 <= value <= ceiling:
        raise FPCError(f"{name} must be an integer between 0 and {ceiling}")
    return value


def _bytes(value: bytes, name: str, maximum: int) -> None:
    # Exact bytes excludes mutable inputs, views and custom sequence callbacks.
    if type(value) is not bytes or len(value) > maximum:
        raise FPCError(f"{name} must be immutable bytes of at most {maximum} bytes")


def encode_bits(raw_le: bytes, *, max_values: int = MAX_VALUES,
                max_output_bytes: int = MAX_STREAM_BYTES) -> bytes:
    """Encode exact binary64 words; deterministic, fresh state per call.

    raw_le must be bytes with length divisible by eight. The count is external
    metadata, not part of the returned stream. Empty input produces b''.
    max_values and max_output_bytes may only tighten the hard limits. The
    unused high nibble for an odd word count is zero. Output is atomic to the
    caller: exceptions return no partial stream. All checks survive python -O.
    """
    _limit(max_values, "max_values", MAX_VALUES)
    _limit(max_output_bytes, "max_output_bytes", MAX_STREAM_BYTES)
    _bytes(raw_le, "raw_le", MAX_RAW_BYTES)
    if len(raw_le) % 8:
        raise FPCError("raw_le length must be a multiple of eight")
    count = len(raw_le) // 8
    if count > max_values:
        raise FPCError("value count exceeds max_values")
    # Even predictor-perfect streams need one control byte per pair.
    if (count + 1) // 2 > max_output_bytes:
        raise FPCError("control bytes exceed max_output_bytes")
    if not count:
        return b""
    fcm = [0] * 4096
    dfcm = [0] * 4096
    fh = dh = last = 0
    out = bytearray()
    for pair in range(0, count, 2):
        control_position = len(out)
        # The initial lower-bound check plus earlier payload checks guarantee
        # space only for earlier pairs, so guard every append independently.
        if len(out) >= max_output_bytes:
            raise FPCError("encoded stream exceeds max_output_bytes")
        out.append(0)
        for half in range(min(2, count - pair)):
            offset = (pair + half) * 8
            word = int.from_bytes(raw_le[offset:offset + 8], "little")
            a = word ^ fcm[fh]
            b = word ^ ((last + dfcm[dh]) & _MASK64)
            # Smaller unsigned XOR has at least as many leading zeros.
            # Equal residuals choose FCM. This is a deterministic policy,
            # not a claim to reproduce Origin's encoded bytes.
            selector = 8 if b < a else 0
            residual = b if selector else a
            width = (residual.bit_length() + 7) // 8
            if width == 4:
                width = 5
            code = width if width < 4 else width - 1
            if len(out) + width > max_output_bytes:
                raise FPCError("encoded stream exceeds max_output_bytes")
            out[control_position] |= (selector | code) << (half * 4)
            out.extend(residual.to_bytes(width, "little"))
            stride = (word - last) & _MASK64
            fcm[fh] = word
            dfcm[dh] = stride
            fh = ((fh << 6) ^ (word >> 48)) & 4095
            dh = ((dh << 2) ^ (stride >> 40)) & 4095
            last = word
    return bytes(out)


def decode_bits(stream: bytes, count: int, *, exact: bool = True,
                max_values: int = MAX_VALUES,
                max_input_bytes: int = MAX_STREAM_BYTES,
                max_output_bytes: int = MAX_RAW_BYTES) -> tuple[bytes, int]:
    """Return (exact little-endian words, bytes consumed), fresh state.

    exact=True rejects every trailing byte, including for count=0. exact=False
    decodes only the requested prefix; bytes consumed stops at its exact end.
    The caller must provide a trusted/bounded count. FPC has no checksum or
    intrinsic count, so valid-looking mutations and an incorrect smaller
    count can be undetectable. Prefix offsets are not resumable positions: the
    predictor state is not returned, and an odd prefix can stop inside a pair.
    All 16 nibbles are accepted, and an unused odd
    high nibble is ignored for compatibility; it never consumes a residual.
    """
    _limit(max_values, "max_values", MAX_VALUES)
    _limit(count, "count", max_values)
    _limit(max_input_bytes, "max_input_bytes", MAX_STREAM_BYTES)
    _limit(max_output_bytes, "max_output_bytes", MAX_RAW_BYTES)
    _bytes(stream, "stream", max_input_bytes)
    if type(exact) is not bool:
        raise FPCError("exact must be a bool")
    if count * 8 > max_output_bytes:
        raise FPCError("decoded words exceed max_output_bytes")
    if len(stream) < (count + 1) // 2:
        raise FPCError("stream shorter than minimum control bytes")
    if not count:
        if exact and stream:
            raise FPCError("trailing bytes after zero-value stream")
        return b"", 0
    fcm = [0] * 4096
    dfcm = [0] * 4096
    fh = dh = last = position = produced = 0
    out = bytearray(count * 8)
    while produced < count:
        if position == len(stream):
            raise FPCError("truncated control byte")
        control = stream[position]
        position += 1
        for shift in (0, 4):
            nibble = (control >> shift) & 15
            width = _WIDTHS[nibble & 7]
            if position + width > len(stream):
                raise FPCError("truncated residual")
            residual = int.from_bytes(stream[position:position + width], "little")
            position += width
            prediction = ((last + dfcm[dh]) & _MASK64) if nibble & 8 else fcm[fh]
            word = prediction ^ residual
            out[produced * 8:(produced + 1) * 8] = word.to_bytes(8, "little")
            stride = (word - last) & _MASK64
            fcm[fh] = word
            dfcm[dh] = stride
            fh = ((fh << 6) ^ (word >> 48)) & 4095
            dh = ((dh << 2) ^ (stride >> 40)) & 4095
            last = word
            produced += 1
            if produced == count:
                break
    if exact and position != len(stream):
        raise FPCError("trailing bytes after FPC stream")
    return bytes(out), position
