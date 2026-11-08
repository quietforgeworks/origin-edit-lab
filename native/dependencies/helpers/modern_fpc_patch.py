"""RESEARCH ONLY: exact-width mutation of observed CPYUA FPC segments.

Preserves every original control nibble, residual width, segment frame and byte
outside the selected FPC segment. Recomputes all predictor-dependent residuals
and refuses the edit if even one needs more bytes. Coordinates are STORED VALUE
ORDINALS, not verified worksheet rows or plot X/Y bindings. Unknown metadata and
cached graphics remain unchanged. This is NOT Origin-tested OPJU compatibility.

Authored implementation of the published FPC algorithm; framing/parameters are
corroborated against Apache-2.0 quantized revision 431deeb7c8473503970ca56b78cc1678f57d373d.
The record locator is the research modern_embedded_reader adapter and therefore
requires that pinned quantized project and NumPy. This module's decoder/encoder
are stdlib and do not import or copy the upstream decoder implementation.
"""
from __future__ import annotations
import hashlib
import math
import struct

MASK = (1 << 64) - 1
MAX_ROWS = 1_000_000
MAX_BYTES = 64 * 1024 * 1024
SUPPORTED_SOURCE_SHA256 = {
    'c586c88034ecfb2d9ad1157ff3b87b055414610ed8bd4a22959ba0f27ff998db': 'modern-oleObject106-Contents.opju',
    'b6b673b7d930bb72a028f59c61fe3d6a04c89632489ff6cedb86445791304712': 'modern-oleObject35-Contents.opju',
    '71bc52236036014c740f42453a44aa495a39a123616a9e92e386071dc5ac42a3': 'modern-oleObject52-Contents.opju',
    '25c752c2c2ad373211040a4d70d4ee278cebbf868a0fbdd09c5a21a10282fd66': 'modern-oleObject66-Contents.opju',
    '73d800c56814c8870e30bcebc20d931aa6f222480d7e42a7b3401def81fa323f': 'modern-oleObject90-Contents.opju',
}

class PatchRefused(ValueError):
    pass

def sha(b):
    return hashlib.sha256(b).hexdigest()

def varint(b, p):
    start = p
    n = 0
    for k in range(10):
        if p >= len(b): raise PatchRefused('Truncated varint')
        byte = b[p]; p += 1
        n |= (byte & 127) << (7 * k)
        if not byte & 128:
            if k and byte == 0: raise PatchRefused('Noncanonical varint')
            return n, p
    raise PatchRefused('Oversized varint')

def f64_bits(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise PatchRefused('Expected finite numeric value')
    try:
        converted = float(x)
    except (OverflowError, ValueError):
        raise PatchRefused('Value is not representable as finite float64') from None
    if not math.isfinite(converted):
        raise PatchRefused('Expected finite numeric value')
    if isinstance(x, int) and converted != x:
        raise PatchRefused('Integer is not exactly representable as float64')
    return int.from_bytes(struct.pack('<d', converted), 'little')

def bits_f64(x):
    return struct.unpack('<d', x.to_bytes(8, 'little'))[0]

def decode_fpc(blob, start, count):
    if type(count) is not int or type(start) is not int or not 0 < count <= MAX_ROWS or not 0 <= start < len(blob):
        raise PatchRefused('Invalid stream bounds')
    table_value = {}; table_delta = {}; hv = hd = prior = 0
    decoded = []; trace = []; p = start
    while len(decoded) < count:
        if p >= len(blob): raise PatchRefused('Missing control byte')
        controls = blob[p]; p += 1
        for code in (controls & 15, controls >> 4):
            width = (code & 7) + (1 if code & 7 >= 4 else 0)
            if p + width > len(blob): raise PatchRefused('Truncated residual')
            predicted = ((prior + table_delta.get(hd, 0)) & MASK) if code & 8 else table_value.get(hv, 0)
            bits = predicted ^ int.from_bytes(blob[p:p+width], 'little')
            trace.append({'code':code, 'offset':p, 'width':width})
            p += width
            decoded.append(bits)
            delta = (bits - prior) & MASK
            table_value[hv] = bits; table_delta[hd] = delta
            hv = ((hv << 6) ^ (bits >> 48)) & 4095
            hd = ((hd << 2) ^ (delta >> 40)) & 4095
            prior = bits
            if len(decoded) == count: break
    return decoded, trace, p

def parse_record(blob, ff):
    if not 0 <= ff < len(blob)-2 or blob[ff:ff+2] != b'\xff\xff':
        raise PatchRefused('Missing record marker')
    count, p = varint(blob, ff+2)
    if not 2 <= count <= MAX_ROWS: raise PatchRefused('Unsupported record size')
    if p >= len(blob) or blob[p] != 0: raise PatchRefused('Missing record delimiter')
    p += 1; values = []; segments = []
    while len(values) < count:
        raw, p = varint(blob, p)
        signed = (raw >> 1) ^ -(raw & 1)
        length = abs(signed)
        if not length or len(values)+length > count: raise PatchRefused('Segment row total mismatch')
        first = len(values)
        if signed < 0:
            if p >= len(blob) or blob[p] != 12: raise PatchRefused('Unsupported FPC segment tag')
            p += 1; start = p
            bits, trace, p = decode_fpc(blob, p, length)
            segments.append({'kind':'fpc', 'first':first, 'count':length, 'start':start, 'end':p, 'trace':trace})
            values.extend(bits)
        else:
            if p >= len(blob): raise PatchRefused('Missing repeated-value tag')
            widths = {0x50:8, 0x1a:2, 0x11:1, 0x64:0}
            width = widths.get(blob[p])
            if width is None or p+1+width > len(blob): raise PatchRefused('Unsupported repeated-value segment')
            p += 1
            value = int.from_bytes(b'\x00'*(8-width)+blob[p:p+width], 'little')
            segments.append({'kind':'repeat', 'first':first, 'count':length, 'start':p, 'end':p+width})
            values.extend([value]*length); p += width
    return values, segments, p

def rewrite_segment(blob, segment, values):
    """Keep original control nibbles and use their allocated widths exactly."""
    if len(values) != segment['count']: raise PatchRefused('Row count cannot change')
    if any(type(v) is not int or not 0 <= v <= MASK for v in values):
        raise PatchRefused('Values must be uint64 bit patterns')
    _, verified_trace, verified_end = decode_fpc(blob, segment['start'], segment['count'])
    if verified_trace != segment['trace'] or verified_end != segment['end']:
        raise PatchRefused('Segment trace does not match original byte allocation')
    out = bytearray(blob)
    table_value = {}; table_delta = {}; hv = hd = prior = 0
    for ordinal, (bits, entry) in enumerate(zip(values, segment['trace'])):
        code = entry['code']; width = entry['width']; p = entry['offset']
        predicted = ((prior + table_delta.get(hd,0)) & MASK) if code & 8 else table_value.get(hv,0)
        residual = predicted ^ bits
        if residual >= 1 << (width*8):
            raise PatchRefused(f'Changed predictor residual exceeds original width at segment ordinal {ordinal}')
        out[p:p+width] = residual.to_bytes(width, 'little')
        delta = (bits-prior) & MASK
        table_value[hv] = bits; table_delta[hd] = delta
        hv = ((hv << 6) ^ (bits >> 48)) & 4095
        hd = ((hd << 2) ^ (delta >> 40)) & 4095
        prior = bits
    check, _, end = decode_fpc(out, segment['start'], segment['count'])
    if check != values or end != segment['end']: raise AssertionError('FPC bitwise verification failed')
    return bytes(out)

def patch_stored_value(blob, *, expected_sha256, column, ordinal, expected_value, value, allow_unverified=False):
    """Single-column stored-value edit using current read-only locator.

    Allows only source header CPYUA 4.3268 195, no undecoded gap flags,
    finite replacement and exact full source SHA. No row or curve inference.
    """
    from modern_embedded_reader import read_modern_embedded_numeric
    if allow_unverified is not True: raise PatchRefused('Origin acceptance unknown; research opt-in required')
    if len(blob) > MAX_BYTES: raise PatchRefused('Resource limit')
    if not isinstance(expected_sha256, str) or len(expected_sha256)!=64 or sha(blob)!=expected_sha256:
        raise PatchRefused('Full source hash mismatch')
    if expected_sha256 not in SUPPORTED_SOURCE_SHA256:
        raise PatchRefused('Only five exact public research specimens are supported')
    scan = read_modern_embedded_numeric(blob)
    cols = [c for c in scan['columns'] if c['name']==column]
    if len(cols)!=1: raise PatchRefused('Dataset name not uniquely located')
    col = cols[0]
    if col['undecoded_gap_flags']: raise PatchRefused('Worksheet alignment flags are unresolved')
    bits, segments, end = parse_record(blob, col['ff_offset'])
    if end != col['end_offset'] or len(bits) != col['stored_count']:
        raise PatchRefused('Independent record framing disagrees')
    if any(not math.isfinite(bits_f64(v)) for v in bits): raise PatchRefused('Missing/non-finite values unsupported')
    # Require bit-level agreement with approved external decoder, not only this
    # implementation. Origin itself remains a separate, unperformed oracle.
    if [f64_bits(v) for v in col['stored_values']] != bits:
        raise PatchRefused('External numeric decoder disagrees')
    if type(ordinal) is not int or not 0 <= ordinal < len(bits): raise PatchRefused('Invalid stored ordinal')
    if bits[ordinal] != f64_bits(expected_value): raise PatchRefused('Expected value mismatch')
    new_bits = f64_bits(value)
    if new_bits == bits[ordinal]: raise PatchRefused('Edit is a no-op')
    selected = next(s for s in segments if s['first'] <= ordinal < s['first']+s['count'])
    if selected['kind'] != 'fpc': raise PatchRefused('Repeated-value mutation not supported')
    segment_values = bits[selected['first']:selected['first']+selected['count']]
    segment_values[ordinal-selected['first']] = new_bits
    out = rewrite_segment(blob, selected, segment_values)
    final_bits, _, final_end = parse_record(out, col['ff_offset'])
    wanted = list(bits); wanted[ordinal] = new_bits
    if final_bits != wanted or final_end != end: raise AssertionError('Record verification failed')
    external = read_modern_embedded_numeric(out)
    if len(external['columns']) != len(scan['columns']): raise PatchRefused('Modified output is outside the numeric locator/plausibility support')
    for old_col, new_col in zip(scan['columns'], external['columns']):
        for key in ('name','name_offset','record_offset','ff_offset','end_offset','prefix_hex','undecoded_gap_flags','stored_count'):
            if old_col[key]!=new_col[key]: raise PatchRefused('Modified output locator metadata disagrees')
        old_values = [f64_bits(v) for v in old_col['stored_values']]
        new_values = [f64_bits(v) for v in new_col['stored_values']]
        if old_col['name']==column: old_values[ordinal]=new_bits
        if old_values!=new_values: raise PatchRefused('External decoder found an unrequested numeric change')
    changes = [i for i,(a,b) in enumerate(zip(blob,out)) if a!=b]
    if len(blob)!=len(out) or any(not selected['start'] <= i < selected['end'] for i in changes):
        raise AssertionError('Bytes escaped selected segment')
    return out, {'source_sha256':sha(blob),'output_sha256':sha(out),'column':column,
                 'stored_ordinal':ordinal,'before':bits_f64(bits[ordinal]),'after':bits_f64(new_bits),
                 'segment_span':[selected['start'],selected['end']],
                 'changed_byte_offsets':changes,'changed_byte_count':len(changes),
                 'all_other_decoded_numeric_values_bit_identical':True,'bytes_outside_selected_fpc_segment_identical':True,
                 'row_alignment_verified':False,'curve_binding_verified':False,
                 'unknown_metadata_recalculated':False,'visible_cache_updated':False,
                 'origin_acceptance_verified':False}
