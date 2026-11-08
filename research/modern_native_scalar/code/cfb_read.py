"""Bounded, read-only Compound File Binary extraction for Origin OLE samples.

This is not a general Office parser or CFB writer. It walks directory sibling
and storage trees, FAT and miniFAT chains; rejects cycles, ambiguous names,
invalid boundaries and unsupported headers. It never activates embedded data.
Validation covers allocation and directory envelopes, not application semantics,
all CFB conformance rules or overlapping allocation across different streams.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from pathlib import Path

FREE = 0xffffffff
END = 0xfffffffe
FAT = 0xfffffffd
DIF = 0xfffffffc
MAX_BYTES = 128 * 1024 * 1024
MAX_DIRECTORY_ENTRIES = 65536

class FormatError(ValueError):
    pass


def _need(condition, message):
    if not condition:
        raise FormatError(message)


class CompoundFile:
    def __init__(self, data: bytes, *, expected_sha256: str | None = None,
                 max_bytes: int = MAX_BYTES):
        _need(isinstance(data, bytes) and 512 <= len(data) <= max_bytes,
              'CFB size outside supported bounds')
        self.data = data
        self.max_bytes = max_bytes
        self.sha256 = hashlib.sha256(data).hexdigest()
        if expected_sha256 is not None:
            _need(self.sha256 == expected_sha256.lower(), 'Source SHA-256 mismatch')
        _need(data[:8] == bytes.fromhex('d0cf11e0a1b11ae1'), 'CFB signature missing')
        self.major = struct.unpack_from('<H', data, 26)[0]
        order, shift, mini_shift = struct.unpack_from('<HHH', data, 28)
        _need(order == 0xfffe and ((self.major, shift) in ((3, 9), (4, 12)))
              and mini_shift == 6, 'Unsupported CFB header')
        self.sector_size = 1 << shift
        _need(len(data) % self.sector_size == 0, 'CFB file is not sector aligned')
        self.nsectors = len(data) // self.sector_size - 1
        ndir, nfat, firstdir, transaction, cutoff, firstmini, nmini, firstdif, ndif = struct.unpack_from('<9I', data, 40)
        _need(cutoff == 4096 and 0 < nfat <= self.nsectors and ndif <= self.nsectors,
              'Invalid CFB allocation counts/cutoff')
        _need(self.major != 3 or ndir == 0, 'Version 3 directory count is nonzero')
        _need(nmini <= self.nsectors, 'MiniFAT count exceeds file')
        fat_ids, fat_set = [], set()
        def append_fat(values):
            for sid in values:
                if sid != FREE:
                    _need(sid < self.nsectors and sid not in fat_set,
                          'Invalid or repeated FAT sector ID')
                    fat_ids.append(sid)
                    fat_set.add(sid)
        append_fat(struct.unpack_from('<109I', data, 76))
        dif_ids, sid = set(), firstdif
        for _ in range(ndif):
            _need(sid < self.nsectors and sid not in dif_ids, 'Invalid/cyclic DIFAT chain')
            dif_ids.add(sid)
            values = struct.unpack('<' + 'I' * (self.sector_size // 4), self._sector(sid))
            append_fat(values[:-1])
            sid = values[-1]
        _need(sid in (END, FREE) and len(fat_ids) == nfat, 'DIFAT length/FAT count mismatch')
        _need(not (dif_ids & set(fat_ids)), 'FAT/DIFAT allocations overlap')
        self.fat = []
        for sid in fat_ids:
            self.fat.extend(struct.unpack('<' + 'I' * (self.sector_size // 4), self._sector(sid)))
        _need(len(self.fat) >= self.nsectors, 'FAT does not cover file')
        _need(all(self.fat[s] == FAT for s in fat_ids), 'FAT sectors not marked FAT')
        _need(all(self.fat[s] == DIF for s in dif_ids), 'DIFAT sectors not marked DIFAT')
        directory = self._read_chain(firstdir, self.fat, self.sector_size, self.nsectors,
                                     expected_count=ndir if self.major == 4 else None)
        _need(bool(directory), 'Empty CFB directory')
        _need(len(directory) // 128 <= MAX_DIRECTORY_ENTRIES, 'Directory entry limit exceeded')
        self.entries = []
        for offset in range(0, len(directory), 128):
            item = directory[offset:offset + 128]
            kind, name_len = item[66], struct.unpack_from('<H', item, 64)[0]
            if kind == 0:
                self.entries.append(None)
                continue
            _need(kind in (1, 2, 5) and 2 <= name_len <= 64 and name_len % 2 == 0,
                  'Invalid CFB directory type/name length')
            _need(item[name_len-2:name_len] == b'\0\0', 'Directory name missing terminator')
            try:
                name = item[:name_len-2].decode('utf-16le', 'strict')
            except UnicodeDecodeError as error:
                raise FormatError('Invalid UTF-16 directory name') from error
            _need(name and '\0' not in name and '/' not in name and '\\' not in name,
                  'Unsupported directory name')
            left, right, child = struct.unpack_from('<III', item, 68)
            start, size = struct.unpack_from('<IQ', item, 116)
            _need(self.major != 3 or size <= 0xffffffff, 'Version 3 stream exceeds 32-bit size')
            _need(size <= len(data), 'Stream size exceeds container')
            self.entries.append({'name': name, 'kind': kind, 'left': left, 'right': right,
                                 'child': child, 'start': start, 'size': size})
        _need(self.entries[0] and self.entries[0]['kind'] == 5, 'CFB root entry missing')
        _need(all(e is None or e['kind'] != 5 for e in self.entries[1:]), 'Multiple CFB roots')
        root = self.entries[0]
        _need(root['left'] == FREE and root['right'] == FREE, 'Root has sibling links')
        self.mini_stream = self._read_stream(root, mini=False)
        mini_fat_bytes = self._read_chain(firstmini, self.fat, self.sector_size,
                                         self.nsectors, expected_count=nmini)
        self.mini_fat = list(struct.unpack('<' + 'I' * (len(mini_fat_bytes)//4), mini_fat_bytes))
        self.streams = {}
        self._walk_directory(root['child'])

    def _sector(self, sid):
        _need(0 <= sid < self.nsectors, 'Sector ID outside file')
        off = (sid + 1) * self.sector_size
        return self.data[off:off + self.sector_size]

    def _read_chain(self, start, table, unit, count_limit, *, expected_count=None, mini=False):
        _need(expected_count is None or 0 <= expected_count <= count_limit,
              'Expected chain count outside bounds')
        chunks, seen, sid = [], set(), start
        while sid != END:
            # An empty chain sometimes uses FREE in existing files.
            if sid == FREE and not chunks and expected_count == 0:
                break
            _need(0 <= sid < count_limit and sid < len(table) and sid not in seen,
                  'Invalid or cyclic allocation chain')
            _need(expected_count is None or len(chunks) < expected_count,
                  'Allocation chain is longer than declared size')
            seen.add(sid)
            if mini:
                off = sid * unit
                _need(off + unit <= len(self.mini_stream), 'Mini-sector exceeds root mini-stream')
                chunks.append(self.mini_stream[off:off + unit])
            else:
                chunks.append(self._sector(sid))
            sid = table[sid]
        _need(expected_count is None or len(chunks) == expected_count,
              'Allocation chain shorter than declared size')
        return b''.join(chunks)

    def _read_stream(self, entry, *, mini):
        size, unit = entry['size'], 64 if mini else self.sector_size
        count = (size + unit - 1) // unit
        table = self.mini_fat if mini else self.fat
        limit = len(self.mini_stream) // 64 if mini else self.nsectors
        return self._read_chain(entry['start'], table, unit, limit,
                                expected_count=count, mini=mini)[:size]

    def _walk_directory(self, first):
        visited = {0}
        pending = [(first, ())]
        names = set()
        while pending:
            index, parent = pending.pop()
            if index == FREE:
                continue
            _need(0 <= index < len(self.entries) and index not in visited,
                  'Invalid/cyclic directory tree')
            visited.add(index)
            entry = self.entries[index]
            _need(entry is not None, 'Directory tree points to unused entry')
            key = (parent, entry['name'].casefold())
            _need(key not in names, 'Ambiguous sibling directory names')
            names.add(key)
            path = parent + (entry['name'],)
            pending.extend(((entry['left'], parent), (entry['right'], parent)))
            if entry['kind'] == 1:
                pending.append((entry['child'], path))
            else:
                _need(entry['kind'] == 2 and entry['child'] == FREE,
                      'Stream entry has a child')
                self.streams[path] = entry
        _need(all(e is None or i in visited for i, e in enumerate(self.entries)),
              'Unreachable active directory entries')

    def read_stream(self, path: str | tuple[str, ...]) -> bytes:
        """Read one exact stream. A string names a root-level stream only."""
        path = (path,) if isinstance(path, str) else path
        _need(isinstance(path, tuple) and path in self.streams, 'Stream not found')
        entry = self.streams[path]
        return self._read_stream(entry, mini=entry['size'] < 4096)

    def inventory(self) -> dict:
        records = []
        total = 0
        for path, entry in sorted(self.streams.items()):
            total += entry['size']
            _need(total <= self.max_bytes, 'Total extracted stream bytes exceed limit')
            data = self.read_stream(path)
            records.append({'path': list(path), 'size': len(data),
                            'sha256': hashlib.sha256(data).hexdigest(),
                            'header_hex': data[:48].hex()})
        return {'source_sha256': self.sha256, 'major_version': self.major,
                'sector_size': self.sector_size, 'streams': records,
                'validation_scope': 'Bounded read-only allocation and directory envelopes; not application semantics or complete CFB conformance.'}



if __name__ == '__main__':
    raise SystemExit('Internal byte-only CFB helper. Use native_container.py for anchored file operations.')
