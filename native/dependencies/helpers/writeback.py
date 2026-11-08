"""RESEARCH ONLY: bounded CFB equal-length patching and reversible PPTX embedding.

Does not interpret Origin records, launch Office/Origin, sync previews, change
allocation, or promise application acceptance. Stdlib only; outputs are copies.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import re
import struct
import zipfile
import zlib
from pathlib import Path

from cfb_read import CompoundFile, FormatError, FREE, END, FAT, DIF, MAX_BYTES, _need

MAX_ARCHIVE = 256 * 1024 * 1024
MAX_EXPANDED = 512 * 1024 * 1024
SCHEMA = 'origin-writeback-research-delta-v1'
LIMITATION = ('Container-byte verification only. Origin has not opened or accepted this '
              'output. Cached previews and application recalculation are not synchronized.')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def guard(data, expected, label):
    _need(isinstance(expected, str) and re.fullmatch(r'[0-9a-f]{64}', expected),
          label + ': exact lowercase SHA-256 is required')
    _need(sha(data) == expected, label + ': SHA-256 mismatch')


class AllocatedCFB(CompoundFile):
    """Read-only parser plus exclusive physical and mini-sector ownership audit.

    Deliberately rejects allocated orphan sectors, malformed chains, overlapping
    ownership, non-64-aligned mini-stream sizes, and nonstandard storage fields.
    It is not a complete validator of every CFB red-black-tree or Origin rule.
    """
    def __init__(self, data, *, expected_sha256=None):
        super().__init__(data, expected_sha256=expected_sha256)
        _need(data[8:24] == bytes(16) and data[34:40] == bytes(6),
              'Unsupported reserved CFB header fields')
        _need(self.major != 4 or data[512:self.sector_size] == bytes(self.sector_size - 512),
              'Unsupported version 4 header padding')
        self.physical_owners = {}
        self.mini_owners = {}
        self.stream_chains = {}
        ndir, nfat, firstdir, _, _, firstmini, nmini, firstdif, ndif = struct.unpack_from('<9I', data, 40)
        fats = [s for s in struct.unpack_from('<109I', data, 76) if s != FREE]
        sid = firstdif
        for _ in range(ndif):
            self._claim(self.physical_owners, [sid], 'DIFAT')
            entries = struct.unpack('<' + 'I' * (self.sector_size // 4), self._sector(sid))
            fats.extend(s for s in entries[:-1] if s != FREE)
            sid = entries[-1]
        self._claim(self.physical_owners, fats, 'FAT')
        self.directory_chain = self._chain(firstdir, self.fat, self.nsectors,
                                          ndir if self.major == 4 else None)
        self._claim(self.physical_owners, self.directory_chain, 'directory')
        self._claim(self.physical_owners, self._chain(firstmini, self.fat, self.nsectors, nmini), 'miniFAT')
        root = self.entries[0]
        _need(root['size'] % 64 == 0, 'Unsupported unaligned root mini-stream size')
        self.root_chain = self._chain(root['start'], self.fat, self.nsectors,
                                     (root['size'] + self.sector_size - 1) // self.sector_size)
        self._claim(self.physical_owners, self.root_chain, 'root-mini-stream')
        for i, entry in enumerate(self.entries):
            if entry and entry['kind'] == 1:
                _need(entry['size'] == 0 and entry['start'] == 0,
                      'Unsupported storage entry allocation fields')
            if entry:
                directory_offset = i * 128
                sector, intra = divmod(directory_offset, self.sector_size)
                pos = (self.directory_chain[sector] + 1) * self.sector_size + intra
                _need(data[pos + 67] in (0, 1), 'Invalid directory color')
        total = 0
        for path, entry in self.streams.items():
            total += entry['size']
            _need(total <= MAX_BYTES, 'Total stream bytes exceed limit')
            mini = entry['size'] < 4096
            unit = 64 if mini else self.sector_size
            table = self.mini_fat if mini else self.fat
            limit = len(self.mini_stream) // 64 if mini else self.nsectors
            chain = self._chain(entry['start'], table, limit, (entry['size'] + unit - 1) // unit)
            self._claim(self.mini_owners if mini else self.physical_owners, chain, 'stream:' + repr(path))
            self.stream_chains[path] = (mini, chain)
        for sid, value in enumerate(self.fat):
            if sid >= self.nsectors:
                _need(value == FREE, 'Non-free FAT padding entry')
            elif sid not in self.physical_owners:
                _need(value == FREE, 'Allocated physical sector has no owner')
        for sid, value in enumerate(self.mini_fat):
            if sid not in self.mini_owners:
                _need(value == FREE, 'Allocated mini-sector has no owner')
        self.hashes = {path: sha(self.read_stream(path)) for path in self.streams}

    @staticmethod
    def _claim(owners, chain, owner):
        for sid in chain:
            _need(sid not in owners, 'Overlapping allocation: ' + owner + ' and ' + owners.get(sid, ''))
            owners[sid] = owner

    @staticmethod
    def _chain(start, table, limit, count):
        result, seen, sid = [], set(), start
        if count == 0:
            _need(start in (FREE, END), 'Empty stream/chain has allocation')
            return result
        while sid != END:
            _need(0 <= sid < limit and sid < len(table) and sid not in seen,
                  'Invalid/cyclic ownership chain')
            _need(count is None or len(result) < count, 'Ownership chain exceeds declared size')
            seen.add(sid)
            result.append(sid)
            sid = table[sid]
        _need(count is None or len(result) == count, 'Ownership chain shorter than declared size')
        return result

    def mapping(self, path, start, length):
        """Map only actual logical stream bytes, never sector padding, to file bytes."""
        path = (path,) if isinstance(path, str) else tuple(path)
        _need(path in self.streams, 'Exact stream path not found')
        _need(type(start) is int and type(length) is int and 0 <= start and 0 < length
              and start + length <= self.streams[path]['size'], 'Range outside stream content')
        mini, chain = self.stream_chains[path]
        unit = 64 if mini else self.sector_size
        spans, cursor = [], start
        while cursor < start + length:
            index, intra = divmod(cursor, unit)
            take = min(unit - intra, start + length - cursor)
            if mini:
                root_offset = chain[index] * 64 + intra
                root_index, root_intra = divmod(root_offset, self.sector_size)
                absolute = (self.root_chain[root_index] + 1) * self.sector_size + root_intra
            else:
                absolute = (chain[index] + 1) * self.sector_size + intra
            spans.append((cursor, absolute, take))
            cursor += take
        return spans

    def report(self):
        return {'source_sha256': sha(self.data), 'major_version': self.major,
                'sector_size': self.sector_size,
                'owned_physical_sectors': len(self.physical_owners),
                'owned_mini_sectors': len(self.mini_owners),
                'streams': [{'path': list(p), 'size': self.streams[p]['size'], 'sha256': h}
                            for p, h in sorted(self.hashes.items())]}


def _ranges(ranges, size):
    _need(isinstance(ranges, (tuple, list)) and len(ranges) <= 65536, 'Invalid allowlist')
    normalized = []
    for item in ranges:
        _need(isinstance(item, (tuple, list)) and len(item) == 2, 'Range must be [offset, length]')
        start, length = item
        _need(type(start) is int and type(length) is int and start >= 0 and length > 0
              and start + length <= size, 'Invalid allowlist range')
        normalized.append((start, length))
    normalized.sort()
    _need(all(a + n <= b for (a, n), (b, _) in zip(normalized, normalized[1:])),
          'Allowlist ranges overlap')
    return normalized


def make_delta(source, edits, *, kind, detail):
    """Splice only caller-specified original byte ranges; record reversible bytes."""
    edits = sorted(edits, key=lambda v: v[0])
    cursor = 0
    result_length = 0
    chunks, records = [], []
    for offset, before, after in edits:
        _need(type(offset) is int and offset >= cursor and len(before) > 0
              and offset + len(before) <= len(source), 'Invalid/overlapping byte splice')
        _need(source[offset:offset + len(before)] == before, 'Byte splice preimage mismatch')
        unchanged = source[cursor:offset]
        chunks.extend((unchanged, after))
        result_length += len(unchanged)
        if before != after:
            records.append({'source_offset': offset, 'result_offset': result_length,
                            'before_b64': base64.b64encode(before).decode(),
                            'after_b64': base64.b64encode(after).decode()})
        result_length += len(after)
        cursor = offset + len(before)
    chunks.append(source[cursor:])
    result = b''.join(chunks)
    manifest = {'schema': SCHEMA, 'kind': kind, 'source_sha256': sha(source),
                'result_sha256': sha(result), 'source_size': len(source),
                'result_size': len(result), 'edits': records, 'detail': detail,
                'limitation': LIMITATION}
    return result, manifest


def restore_delta(result, manifest):
    """Accept only the exact result; reconstruct and verify the exact original."""
    _need(isinstance(manifest, dict) and manifest.get('schema') == SCHEMA, 'Unknown restore schema')
    guard(result, manifest.get('result_sha256'), 'Restore input')
    _need(len(result) == manifest.get('result_size'), 'Restore input size mismatch')
    edits = manifest.get('edits')
    _need(isinstance(edits, list) and len(edits) <= 1000000, 'Invalid restore edits')
    chunks, cursor, source_cursor = [], 0, 0
    for entry in edits:
        try:
            before = base64.b64decode(entry['before_b64'], validate=True)
            after = base64.b64decode(entry['after_b64'], validate=True)
            offset, original_offset = entry['result_offset'], entry['source_offset']
        except (KeyError, TypeError, ValueError) as error:
            raise FormatError('Invalid restore record') from error
        _need(type(offset) is int and type(original_offset) is int and offset >= cursor
              and offset + len(after) <= len(result) and before and after,
              'Invalid restore bounds')
        _need(source_cursor + offset - cursor == original_offset, 'Inconsistent restore offsets')
        _need(result[offset:offset + len(after)] == after, 'Restore preimage mismatch')
        chunks.extend((result[cursor:offset], before))
        source_cursor = original_offset + len(before)
        cursor = offset + len(after)
    chunks.append(result[cursor:])
    source = b''.join(chunks)
    _need(len(source) == manifest.get('source_size'), 'Restored size mismatch')
    guard(source, manifest.get('source_sha256'), 'Restored source')
    return source


def patch_cfb(source, replacement, *, stream_path, expected_source_sha256,
              expected_stream_sha256, allowlist):
    guard(source, expected_source_sha256, 'CFB source')
    _need(isinstance(replacement, bytes), 'Replacement must be bytes')
    cfb = AllocatedCFB(source)
    path = (stream_path,) if isinstance(stream_path, str) else tuple(stream_path)
    original = cfb.read_stream(path)
    guard(original, expected_stream_sha256, 'CFB stream')
    _need(len(replacement) == len(original), 'Replacement changes stream length')
    ranges = _ranges(allowlist, len(original))
    cursor, edits, mappings = 0, [], []
    for offset, length in ranges:
        _need(original[cursor:offset] == replacement[cursor:offset], 'Change outside logical allowlist')
        for logical, absolute, amount in cfb.mapping(path, offset, length):
            before, after = original[logical:logical + amount], replacement[logical:logical + amount]
            edits.append((absolute, before, after))
            mappings.append({'stream_offset': logical, 'file_offset': absolute, 'length': amount})
        cursor = offset + length
    _need(original[cursor:] == replacement[cursor:], 'Change outside logical allowlist')
    detail = {'stream_path': list(path), 'stream_source_sha256': sha(original),
              'stream_result_sha256': sha(replacement), 'allowlist': ranges,
              'physical_allowlist': mappings, 'before': cfb.report()}
    result, manifest = make_delta(source, edits, kind='cfb-equal-length-stream', detail=detail)
    check = AllocatedCFB(result)
    _need(check.read_stream(path) == replacement, 'Patched stream verification failed')
    _need(cfb.streams == check.streams and cfb.physical_owners == check.physical_owners
          and cfb.mini_owners == check.mini_owners, 'Allocation or directory changed')
    _need(all(check.hashes[p] == h for p, h in cfb.hashes.items() if p != path),
          'Non-target stream changed')
    # Independently check all untouched spans, including header, allocation tables,
    # sector padding, directory, cached previews, and free sectors.
    physical = sorted((x['file_offset'], x['length']) for x in mappings)
    cursor = 0
    for offset, amount in physical:
        _need(source[cursor:offset] == result[cursor:offset], 'Bytes outside physical allowlist changed')
        cursor = offset + amount
    _need(source[cursor:] == result[cursor:], 'Bytes outside physical allowlist changed')
    _need(restore_delta(result, manifest) == source, 'Exact restoration verification failed')
    detail.update({'after': check.report(), 'non_target_streams_equal': True,
                   'outside_physical_allowlist_equal': True, 'exact_restore_verified': True})
    return result, manifest


class RawZip:
    """Narrow conventional ZIP profile, no ZIP64, encryption, descriptors, or gaps.

    Preserve the raw compressed data, names, attributes, comments, and extras of
    every untargeted member; only adjust offsets where target size changes.
    """
    def __init__(self, source):
        _need(isinstance(source, bytes) and 22 <= len(source) <= MAX_ARCHIVE, 'ZIP size outside limits')
        self.source = source
        pos = source.rfind(b'PK\x05\x06', max(0, len(source) - 65557))
        _need(pos >= 0 and pos + 22 <= len(source), 'ZIP end record missing')
        _, disk, cd_disk, n_disk, n, cd_size, cd_off, comment_len = struct.unpack_from('<4s4H2IH', source, pos)
        _need(disk == cd_disk == 0 and n_disk == n and 0 < n < 65535
              and cd_off != 0xffffffff and cd_size != 0xffffffff
              and pos + 22 + comment_len == len(source)
              and cd_off + cd_size == pos, 'Unsupported ZIP footer/ZIP64/multidisk')
        self.eocd, self.central_offset = pos, cd_off
        self.z = zipfile.ZipFile(io.BytesIO(source))
        infos = self.z.infolist()
        _need(len(infos) == n and len({i.filename for i in infos}) == n, 'Duplicate ZIP names/count mismatch')
        _need(sum(i.file_size for i in infos) <= MAX_EXPANDED, 'ZIP expanded size limit')
        self.parts, self.headers, self.hashes = {}, {}, {}
        central = cd_off
        local_segments = []
        for info in infos:
            _need(info.file_size <= MAX_BYTES and info.compress_size <= MAX_BYTES,
                  'ZIP member exceeds bound')
            _need(info.file_size <= max(1, info.compress_size) * 1000, 'Excessive ZIP compression ratio')
            _need(info.compress_type in (0, 8) and info.flag_bits & ~0x806 == 0,
                  'Unsupported ZIP flags/compression/encryption/data descriptor')
            _need('\x00' not in info.filename and '\\' not in info.filename
                  and not info.filename.startswith('/') and '..' not in info.filename.split('/'),
                  'Unsafe ZIP member name')
            _need(source[central:central + 4] == b'PK\x01\x02', 'Invalid ZIP central header')
            _need(central + 46 <= pos, 'Truncated ZIP central header')
            fields = struct.unpack_from('<6H3I5H2I', source, central + 4)
            made, needed, flags, method, mtime, mdate, crc, compressed, size, nl, el, cl, disk, ia, ea, local = fields
            _need(needed <= 20 and disk == 0 and local == info.header_offset
                  and (flags, method, crc, compressed, size) ==
                  (info.flag_bits, info.compress_type, info.CRC, info.compress_size, info.file_size),
                  'Unsupported or inconsistent ZIP central fields')
            central_end = central + 46 + nl + el + cl
            _need(central_end <= pos, 'Truncated ZIP central record')
            rawname = source[central + 46:central + 46 + nl]
            _need(b'\x00' not in rawname and rawname.decode('utf-8' if flags & 0x800 else 'cp437') == info.filename,
                  'ZIP name is not an exact unambiguous name')
            self._check_extra(source[central + 46 + nl:central + 46 + nl + el])
            _need(source[local:local + 4] == b'PK\x03\x04' and local + 30 <= cd_off,
                  'Invalid ZIP local header')
            ln, lf, lm, lt, ld, lc, lcs, ls, lnl, lel = struct.unpack_from('<5H3I2H', source, local + 4)
            _need((ln, lf, lm, lt, ld, lc, lcs, ls) == (needed, flags, method, mtime, mdate, crc, compressed, size),
                  'ZIP local/central fields differ')
            _need(source[local + 30:local + 30 + lnl] == rawname, 'ZIP local/central names differ')
            self._check_extra(source[local + 30 + lnl:local + 30 + lnl + lel])
            data_offset = local + 30 + lnl + lel
            end = data_offset + compressed
            _need(end <= cd_off, 'ZIP member crosses central directory')
            local_segments.append((local, end))
            raw = source[data_offset:end]
            if method == 0:
                data = raw
            else:
                try:
                    decompressor = zlib.decompressobj(-15)
                    data = decompressor.decompress(raw, size + 1)
                except zlib.error as error:
                    raise FormatError('Invalid raw ZIP deflate stream') from error
                _need(decompressor.eof and not decompressor.unused_data and not decompressor.unconsumed_tail,
                      'ZIP deflate stream is truncated, overlong or has trailing data')
            _need(len(data) == size and zlib.crc32(data) == crc, 'ZIP decompressed size/CRC mismatch')
            self.parts[info.filename] = info
            self.hashes[info.filename] = sha(data)
            self.headers[info.filename] = (central, local, data_offset)
            central = central_end
        _need(central == pos, 'Unexpected central directory records')
        cursor = 0
        for start, end in sorted(local_segments):
            _need(start == cursor, 'ZIP local records overlap or have unsupported gaps/preamble')
            cursor = end
        _need(cursor == cd_off, 'ZIP gap before central directory')

    @staticmethod
    def _check_extra(extra):
        cursor = 0
        while cursor < len(extra):
            _need(cursor + 4 <= len(extra), 'Malformed ZIP extra field')
            tag, size = struct.unpack_from('<HH', extra, cursor)
            _need(tag != 1, 'ZIP64 extra fields unsupported')
            cursor += 4 + size
            _need(cursor <= len(extra), 'Truncated ZIP extra field')


def reembed_pptx(source, replacement, *, part, expected_source_sha256,
                 expected_part_sha256, cfb_manifest):
    guard(source, expected_source_sha256, 'PPTX source')
    _need(isinstance(part, str) and re.fullmatch(r'ppt/embeddings/[A-Za-z0-9_-]+\.bin', part),
          'Target must be an exact PPTX embedded binary part')
    package = RawZip(source)
    _need('[Content_Types].xml' in package.parts and 'ppt/presentation.xml' in package.parts,
          'Not a conventional PPTX package')
    _need(part in package.parts, 'Exact binary part not found')
    original = package.z.read(part)
    guard(original, expected_part_sha256, 'PPTX embedded source')
    _need(cfb_manifest.get('kind') == 'cfb-equal-length-stream', 'CFB patch manifest required')
    _need(restore_delta(replacement, cfb_manifest) == original, 'Replacement/CFB manifest not tied to source part')
    # Re-run the CFB constrained patch, rather than trusting unverified manifest claims.
    detail = cfb_manifest['detail']
    _need(detail.get('stream_path') == ['Contents'],
          'PPTX source writeback permits only the exact root Contents stream')
    cf = AllocatedCFB(replacement)
    verified, _ = patch_cfb(original, cf.read_stream(tuple(detail['stream_path'])),
                            stream_path=detail['stream_path'], expected_source_sha256=sha(original),
                            expected_stream_sha256=detail['stream_source_sha256'],
                            allowlist=detail['allowlist'])
    _need(verified == replacement, 'Replacement has changes outside its verified CFB patch')
    info = package.parts[part]
    central, local, data_offset = package.headers[part]
    edits = []
    if original != replacement:
        if info.compress_type == zipfile.ZIP_STORED:
            compressed = replacement
        else:
            compressor = zlib.compressobj(level=9, wbits=-15)
            compressed = compressor.compress(replacement) + compressor.flush()
        delta = len(compressed) - info.compress_size
        crc = zlib.crc32(replacement)
        edits.extend([(local + 14, source[local + 14:local + 26], struct.pack('<III', crc, len(compressed), len(replacement))),
                      (data_offset, source[data_offset:data_offset + info.compress_size], compressed),
                      (central + 16, source[central + 16:central + 28], struct.pack('<III', crc, len(compressed), len(replacement)))])
        if delta:
            for name, (c, l, _) in package.headers.items():
                if l > local:
                    edits.append((c + 42, source[c + 42:c + 46], struct.pack('<I', l + delta)))
            edits.append((package.eocd + 16, source[package.eocd + 16:package.eocd + 20],
                          struct.pack('<I', package.central_offset + delta)))
    result, manifest = make_delta(source, edits, kind='pptx-one-binary-part',
                                 detail={'part': part, 'before_part_hashes': package.hashes,
                                         'embedded_cfb_manifest': cfb_manifest})
    check = RawZip(result)
    _need(package.parts.keys() == check.parts.keys(), 'PPTX part set changed')
    _need(check.z.read(part) == replacement, 'Embedded replacement does not match')
    _need(all(check.hashes[n] == h for n, h in package.hashes.items() if n != part),
          'Non-target PPTX part changed')
    _need(restore_delta(result, manifest) == source, 'Exact PPTX restoration failed')
    manifest['detail'].update({'after_part_hashes': check.hashes, 'non_target_parts_equal': True,
                               'exact_restore_verified': True, 'cached_previews_unchanged': True})
    return result, manifest


def write_new(path, data):
    path = Path(path)
    with path.open('xb') as f:
        f.write(data)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    audit = sub.add_parser('audit-cfb')
    audit.add_argument('source', type=Path)
    patch = sub.add_parser('patch-cfb')
    patch.add_argument('source', type=Path)
    patch.add_argument('replacement_stream', type=Path)
    patch.add_argument('plan', type=Path, help='JSON: source_sha256, stream_sha256, stream_path, allowlist')
    patch.add_argument('output', type=Path)
    patch.add_argument('manifest', type=Path)
    emb = sub.add_parser('reembed-pptx')
    emb.add_argument('source', type=Path)
    emb.add_argument('replacement_cfb', type=Path)
    emb.add_argument('cfb_manifest', type=Path)
    emb.add_argument('plan', type=Path, help='JSON: source_sha256, part_sha256, part')
    emb.add_argument('output', type=Path)
    emb.add_argument('manifest', type=Path)
    restore = sub.add_parser('restore')
    restore.add_argument('source', type=Path)
    restore.add_argument('restore_manifest', type=Path)
    restore.add_argument('output', type=Path)
    args = p.parse_args()
    inputs = [getattr(args, k) for k in ('source', 'replacement_stream', 'replacement_cfb', 'plan', 'cfb_manifest', 'restore_manifest') if hasattr(args, k)]
    outputs = [getattr(args, k) for k in ('output', 'manifest') if hasattr(args, k)]
    _need(len({v.resolve() for v in outputs}) == len(outputs)
          and not ({v.resolve() for v in outputs} & {v.resolve() for v in inputs}), 'Input/output paths overlap')
    _need(all(not v.exists() for v in outputs), 'Refusing to overwrite existing output')
    _need(all(v.stat().st_size <= MAX_ARCHIVE for v in inputs), 'Input file exceeds limit')
    source = args.source.read_bytes()
    if args.command == 'audit-cfb':
        print(json.dumps(AllocatedCFB(source).report(), indent=2))
        return
    if args.command == 'restore':
        result = restore_delta(source, json.loads(args.restore_manifest.read_text()))
        write_new(args.output, result)
        print(json.dumps({'restored_sha256': sha(result), 'limitation': LIMITATION}))
        return
    plan = json.loads(args.plan.read_text())
    if args.command == 'patch-cfb':
        result, manifest = patch_cfb(source, args.replacement_stream.read_bytes(),
                                    stream_path=plan['stream_path'],
                                    expected_source_sha256=plan['source_sha256'],
                                    expected_stream_sha256=plan['stream_sha256'], allowlist=plan['allowlist'])
    else:
        result, manifest = reembed_pptx(source, args.replacement_cfb.read_bytes(),
                                       part=plan['part'], expected_source_sha256=plan['source_sha256'],
                                       expected_part_sha256=plan['part_sha256'],
                                       cfb_manifest=json.loads(args.cfb_manifest.read_text()))
    # Validate completely before either write; exclusive creation prevents clobbering.
    write_new(args.manifest, (json.dumps(manifest, indent=2) + '\n').encode())
    write_new(args.output, result)
    print(json.dumps({'output_sha256': sha(result), 'exact_restore_verified': True, 'limitation': LIMITATION}))


if __name__ == '__main__':
    main()
