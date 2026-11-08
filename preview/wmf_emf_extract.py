"""Read-only extraction of one EMF carried in WMFC comments in a WMF.

No rendering, OLE activation, external fetch, or Origin parsing is performed.
Supported: standard 18-byte WMF header, optionally preceded by an Aldus
placeable header. One consecutive WMFC sequence. All fields are bounded.

The Microsoft ByteCount description names total EMF size, but the 12 real
Origin WMFs tested use 34 + current chunk size. This implementation uses the
latter, also consistent with the actual record boundary. These specimens
have a zero additive 16-bit checksum over the whole non-placeable WMF;
the documented XOR checksum over the EMF does not match. Both are reported,
not silently conflated. Neither checksum establishes semantic correctness.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from pathlib import Path

MAX_BYTES = 128 * 1024 * 1024
MAX_RECORDS = 250000

class FormatError(ValueError):
    """Unsupported or inconsistent metafile. No output should be written."""


def _need(condition, message):
    if not condition:
        raise FormatError(message)


def inspect_emf(data: bytes, *, max_bytes: int = MAX_BYTES) -> dict:
    """Validate the record envelope, not drawing semantics or renderer safety."""
    _need(isinstance(data, bytes), 'EMF must be bytes')
    _need(88 <= len(data) <= max_bytes, 'EMF size outside supported bounds')
    typ, header_size = struct.unpack_from('<II', data)
    _need(typ == 1 and 88 <= header_size <= len(data), 'Invalid EMR_HEADER')
    _need(data[40:44] == b' EMF', 'EMF signature missing')
    nbytes, nrecords = struct.unpack_from('<II', data, 48)
    _need(nbytes == len(data), 'EMF nBytes does not match payload')
    _need(2 <= nrecords <= min(len(data) // 8, MAX_RECORDS), 'Invalid EMF record count')
    records, pos = [], 0
    while pos < len(data):
        _need(len(records) < MAX_RECORDS, 'EMF record limit exceeded')
        _need(pos + 8 <= len(data), 'Truncated EMF record header')
        kind, size = struct.unpack_from('<II', data, pos)
        _need(size >= 8 and size % 4 == 0 and pos + size <= len(data),
              'Invalid EMF record size')
        _need(not records or kind != 1, 'Unexpected second EMR_HEADER')
        _need(kind != 14 or pos + size == len(data), 'Premature EMR_EOF')
        record = {'index': len(records), 'offset': pos, 'type': kind, 'size': size}
        if kind in (38, 95):
            _need(size >= (28 if kind == 38 else 52), 'Truncated pen record')
            color_offset = pos + (24 if kind == 38 else 40)
            record.update(pen_handle=struct.unpack_from('<I', data, pos + 8)[0],
                          color_offset=color_offset,
                          color_rgb_hex=data[color_offset:color_offset + 3].hex())
        records.append(record)
        pos += size
    _need(len(records) == nrecords and records[-1]['type'] == 14,
          'EMF nRecords/EOF mismatch')
    _need(records[-1]['size'] >= 20, 'Truncated EMR_EOF')
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'record_count': nrecords, 'records': records,
            'validation_scope': 'Record boundaries only; drawing semantics and application rendering unverified.'}


def extract_embedded_emf(data: bytes, *, expected_sha256: str | None = None,
                         max_bytes: int = MAX_BYTES) -> tuple[bytes, dict]:
    """Extract exact stored EMF bytes; reject ambiguous or malformed wrappers."""
    _need(isinstance(data, bytes), 'WMF must be bytes')
    _need(18 <= len(data) <= max_bytes, 'WMF size outside supported bounds')
    sha = hashlib.sha256(data).hexdigest()
    if expected_sha256 is not None:
        _need(sha == expected_sha256.lower(), 'Source SHA-256 mismatch')
    base = 22 if data[:4] == b'\xd7\xcd\xc6\x9a' else 0
    if base:
        _need(len(data) >= 40, 'Truncated placeable WMF')
        words = struct.unpack_from('<11H', data)
        check = 0
        for word in words[:10]: check ^= word
        _need(check == words[10], 'Placeable header checksum mismatch')
    kind, header_words, version, file_words, objects, max_record, params = struct.unpack_from('<HHHIHIH', data, base)
    _need(kind in (1, 2) and header_words == 9 and version in (0x100, 0x300),
          'Unsupported WMF header')
    _need(params == 0 and file_words * 2 == len(data) - base, 'WMF file size mismatch')
    pos, count, max_seen, chunks, details = base + 18, 0, 0, [], []
    sequence_end = None
    last_function = None
    while pos < len(data):
        _need(count < MAX_RECORDS, 'WMF record limit exceeded')
        _need(pos + 6 <= len(data), 'Truncated WMF record')
        words, function = struct.unpack_from('<IH', data, pos)
        size = words * 2
        _need(size >= 6 and pos + size <= len(data), 'Invalid WMF record size')
        _need(function != 0 or pos + size == len(data), 'Premature WMF EOF')
        max_seen = max(max_seen, words)
        if function == 0x626:
            _need(size >= 10, 'Truncated WMF escape')
            escape, byte_count = struct.unpack_from('<HH', data, pos + 6)
            _need(10 + byte_count <= size, 'Escape ByteCount exceeds record')
            if escape == 15:
                _need(size >= 44, 'Truncated WMFC header')
                magic, comment_type, version, checksum, flags, total_count, current, remaining, total = struct.unpack_from('<IIIHIIIII', data, pos + 10)
                _need(magic == 0x43464d57 and comment_type == 1 and flags == 0,
                      'Unsupported WMFC comment')
                _need(0 < current <= 8192 and 0 < total <= max_bytes,
                      'WMFC chunk/payload exceeds limits')
                _need(0 < total_count <= max_bytes // 44 and total_count <= total,
                      'Invalid WMFC chunk count')
                _need(byte_count == 34 + current and size == 44 + current + (current % 2),
                      'WMFC current size does not match record')
                _need(current + remaining <= total, 'WMFC remaining exceeds total')
                _need(sequence_end is None or sequence_end == pos,
                      'Non-consecutive or multiple WMFC sequences')
                if details:
                    _need(total_count == details[0]['count'] and total == details[0]['total'],
                          'Inconsistent WMFC totals')
                    _need(details[-1]['remaining'] == current + remaining,
                          'Broken WMFC remaining-byte chain')
                else:
                    _need(current + remaining == total, 'First WMFC chunk lacks prefix')
                chunks.append(data[pos + 44:pos + 44 + current])
                details.append({'offset': pos, 'count': total_count, 'current': current,
                                'remaining': remaining, 'total': total, 'checksum': checksum})
                sequence_end = pos + size
        last_function = function
        pos += size
        count += 1
    _need(last_function == 0, 'WMF EOF missing')
    _need(max_seen <= max_record, 'WMF maximum record field too small')
    _need(bool(chunks), 'No embedded EMF found')
    _need(len(chunks) == details[0]['count'] and details[-1]['remaining'] == 0,
          'WMFC sequence incomplete')
    emf = b''.join(chunks)
    _need(len(emf) == details[0]['total'], 'Reassembled size mismatch')
    report = inspect_emf(emf, max_bytes=max_bytes)
    xor = 0
    for (word,) in struct.iter_unpack('<H', emf): xor ^= word
    additive = sum(word for (word,) in struct.iter_unpack('<H', data[base:])) & 0xffff
    report.update(source_sha256=sha, wmf_record_count=count, chunks=details,
                  placeable_header=bool(base),
                  source_wmf_additive_word_checksum=additive,
                  documented_emf_xor_checksum=(~xor) & 0xffff,
                  stored_first_checksum=details[0]['checksum'],
                  checksum_note='Source checksum conventions differ. No assertion of general checksum equivalence.')
    return emf, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--expected-sha256')
    args = parser.parse_args()
    targets = [args.output] + ([args.report] if args.report else [])
    _need(len({p.resolve() for p in targets}) == len(targets), 'Output paths overlap')
    _need(all(not p.exists() for p in targets), 'Refusing to overwrite output')
    _need(args.input.stat().st_size <= MAX_BYTES, 'Input exceeds limit')
    emf, report = extract_embedded_emf(args.input.read_bytes(), expected_sha256=args.expected_sha256)
    with args.output.open('xb') as output: output.write(emf)
    if args.report:
        with args.report.open('x', encoding='utf8') as output:
            json.dump(report, output, indent=2)
    print(json.dumps({k: v for k, v in report.items() if k not in ('records', 'chunks')}))

if __name__ == '__main__':
    main()
