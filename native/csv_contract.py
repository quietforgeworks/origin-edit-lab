"""Shared strict CSV/binary64 contract, used by generation and verification."""
import csv
from decimal import Decimal
import io
import math
from pathlib import Path
import re
import struct

MAX_CSV_BYTES = 16384
ORIGIN_MISSING_BITS = 0x81AA74FE1C132C0E
NUMBER = re.compile(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z')


class InputRefused(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise InputRefused(message)


def numeric_bits(value):
    need(not isinstance(value, bool) and isinstance(value, (int, float)), 'Expected finite numeric value')
    try:
        converted = float(value)
    except (OverflowError, ValueError) as exc:
        raise InputRefused('Value is not representable as finite float64') from exc
    need(math.isfinite(converted), 'Expected finite numeric value')
    need(not isinstance(value, int) or converted == value, 'Integer is not exactly representable as float64')
    bits = int.from_bytes(struct.pack('<d', converted), 'little')
    need(bits != ORIGIN_MISSING_BITS, 'Origin missing sentinel is not a finite measurement')
    need(converted == 0.0 or 1e-290 <= abs(converted) <= 1e290, 'Outside pinned independent decoder magnitude contract')
    return bits


def read_limited(path, limit):
    """Bound the actual read, not only an accepted-input length check afterward."""
    with Path(path).open('rb') as file:
        data = file.read(limit + 1)
    need(len(data) <= limit, f'Input exceeds {limit} bytes')
    return data


def parse_csv(data):
    need(type(data) is bytes and len(data) <= MAX_CSV_BYTES, 'CSV must be bytes within 16 KiB')
    try:
        rows = list(csv.reader(io.StringIO(data.decode('utf-8-sig')), strict=True))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise InputRefused('Invalid UTF-8 CSV') from exc
    need(len(rows) == 10 and rows[0] == ['x', 'y'], 'CSV requires exact x,y header and nine data rows')
    columns = [[], []]
    for row in rows[1:]:
        need(len(row) == 2, 'Exactly two CSV fields required')
        for column, token in zip(columns, row):
            token = token.strip()
            need(len(token) <= 128 and NUMBER.fullmatch(token), 'Blank, missing or non-numeric CSV cell')
            value = float(token)
            numeric_bits(value)
            if value == 0:
                need(Decimal(token) == 0, 'Underflow would turn nonzero data into zero')
            column.append(value)
    return columns
