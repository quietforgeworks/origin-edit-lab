# Copied from this project's authored v2 code. No downloaded code is executed.
from __future__ import annotations
import argparse
import csv
import ctypes
import errno
import os
import platform
import sys
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import io
import json
import math
from pathlib import Path
import re
import shutil
import struct
import tempfile


NUMBER = re.compile(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z')
MISSING = struct.unpack('<d', bytes.fromhex('0e2c131cfe74aa81'))[0]

class Rejected(ValueError):
    pass

def require(ok, why):
    if not ok:
        raise Rejected(why)

def sha(blob):
    return hashlib.sha256(blob).hexdigest()

def convert_number(token, book, row, col):
    """IEEE-754 binary64 conversion, with an exact per-cell audit record."""
    require(sys.float_info.radix == 2 and sys.float_info.mant_dig == 53
            and sys.float_info.max_exp == 1024 and struct.calcsize('d') == 8,
            'runtime is not IEEE-754 binary64')
    require(isinstance(token, str) and len(token) <= 128 and NUMBER.fullmatch(token),
            f'{book}: invalid numeric token row {row}, col {col}')
    try:
        dec, value = Decimal(token), float(token)
    except (InvalidOperation, ValueError, OverflowError) as e:
        raise Rejected('invalid number') from e
    require(math.isfinite(value), 'NaN, infinity or binary64 overflow refused')
    require(value != MISSING, 'Origin missing-value sentinel refused')
    require(not (dec != 0 and value == 0), 'nonzero value underflows to zero')
    require(value == 0 or abs(value) >= sys.float_info.min,
            'subnormal binary64 values refused under this conservative underflow policy')
    represented = Decimal.from_float(value)
    if dec == dec.to_integral_value():
        require(represented == dec, 'integer changes during binary64 conversion; lossy integer refused')
    if value == 0:
        require(math.copysign(1, value) == (-1 if dec.is_signed() else 1), 'signed zero changed')
    # This precision covers every normal binary64 exact decimal expansion plus
    # the bounded 128-character input. No rounding error is silently omitted.
    with localcontext() as context:
        context.prec = 1200
        error = represented - dec
    return value, {'book': book, 'row_one_based': row, 'column': col,
        'raw_numeric_lexeme': token, 'input_exact_decimal': str(dec),
        'binary64_value': value, 'binary64_little_endian_hex': struct.pack('<d', value).hex(),
        'binary64_hex_float': value.hex(), 'binary64_exact_decimal': str(represented),
        'conversion': 'exact' if represented == dec else 'rounded_to_nearest_ties_even',
        'signed_decimal_error_binary64_minus_input': str(error),
        'negative_zero': value == 0 and math.copysign(1, value) < 0}

def publish_noreplace(staging, outdir):
    """One kernel operation: destination creation and no-overwrite are atomic.

    Fail closed on platforms/filesystems lacking renameat2(RENAME_NOREPLACE).
    Both paths share the same opened parent directory descriptor. No existing
    file, symlink, or directory, even an empty one raced into place, is replaced.
    """
    staging, outdir = Path(staging), Path(outdir)
    require(platform.system() == 'Linux', 'atomic no-overwrite publication requires Linux renameat2')
    require(staging.parent == outdir.parent, 'staging and output must share parent')
    libc = ctypes.CDLL(None, use_errno=True)
    call = getattr(libc, 'renameat2', None)
    require(call is not None, 'renameat2 unavailable; no unsafe publication fallback')
    call.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    call.restype = ctypes.c_int
    descriptor = os.open(staging.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        result = call(descriptor, os.fsencode(staging.name), descriptor, os.fsencode(outdir.name), 1)
        if result != 0:
            error = ctypes.get_errno()
            if error == errno.EEXIST:
                raise Rejected('output already exists (including concurrent creation); no overwrite')
            raise OSError(error, os.strerror(error))
    finally:
        os.close(descriptor)
