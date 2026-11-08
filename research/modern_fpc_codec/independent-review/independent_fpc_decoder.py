"""Independent implementation of the supplied FPC specification, not an Origin oracle.

No floating-point conversions, I/O, container parsing, or external dependencies.
"""

UINT64_MASK = (1 << 64) - 1
WIDTHS = (0, 1, 2, 3, 5, 6, 7, 8)
MAX_VALUES = 1_000_000
MAX_INPUT_BYTES = 16_000_000


class DecodeError(ValueError):
    """Invalid size, truncated payload, or trailing data in strict mode."""


def decode_prefix(data: bytes, count: int) -> tuple[list[int], int]:
    """Decode exactly count uint64 bit patterns and return bytes consumed.

    Each call starts fresh state. An unused high nibble is ignored. Trailing
    bytes are permitted (but the entire supplied input must respect the cap).
    Resource caps are deliberate policy limits, not format limits.
    """
    if type(data) is not bytes:
        raise TypeError("data must be immutable bytes")
    if type(count) is not int:
        raise TypeError("count must be an integer, excluding bool")
    if not 0 <= count <= MAX_VALUES:
        raise DecodeError("count exceeds allowed range")
    if len(data) > MAX_INPUT_BYTES:
        raise DecodeError("input exceeds byte limit")
    if (count + 1) // 2 > len(data):
        raise DecodeError("insufficient control bytes")

    values = []
    fcm = [0] * 4096
    dfcm = [0] * 4096
    fhash = dhash = last = offset = 0
    while len(values) < count:
        if offset >= len(data):
            raise DecodeError("missing control byte")
        control = data[offset]
        offset += 1
        for shift in (0, 4):
            if len(values) == count:
                break
            nibble = (control >> shift) & 15
            width = WIDTHS[nibble & 7]
            end = offset + width
            if end > len(data):
                raise DecodeError("truncated residual")
            residual = int.from_bytes(data[offset:end], "little")
            offset = end
            predictor = ((last + dfcm[dhash]) & UINT64_MASK
                         if nibble & 8 else fcm[fhash])
            value = predictor ^ residual
            stride = (value - last) & UINT64_MASK
            fcm[fhash] = value
            dfcm[dhash] = stride
            fhash = ((fhash << 6) ^ (value >> 48)) & 4095
            dhash = ((dhash << 2) ^ (stride >> 40)) & 4095
            last = value
            values.append(value)
    return values, offset


def decode_strict(data: bytes, count: int) -> list[int]:
    """Decode with the prefix rules and reject every trailing byte."""
    values, consumed = decode_prefix(data, count)
    if consumed != len(data):
        raise DecodeError("trailing bytes")
    return values
