"""Patch one reviewed CPYUA root Contents stream in a guarded PPTX member.

Only fixed-length ordinary-FAT Contents is supported. No allocation, previews,
application calls, transforms, or inferred semantic edits. ZIP member payloads
are preserved; ZIP rewriting may normalize flags and compressed representation.
"""
from __future__ import annotations
import argparse
import copy
import io
import json
from pathlib import Path
import struct
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from source_edit.cfb_extract import CompoundFile, FREE, END
try:
    from .reviewed_patch import bounded_read, check_hash, load_plan, need, patch_native, sha, write_new, MAX_BYTES
except ImportError:
    from reviewed_patch import bounded_read, check_hash, load_plan, need, patch_native, sha, write_new, MAX_BYTES

MAX_PPT_BYTES = 256 * 1024 * 1024
MAX_MEMBERS = 10000

def patch_contents(data, expected_sha256, plan):
    need(sha(data) == check_hash(expected_sha256), 'CFB SHA-256 mismatch')
    cfb = CompoundFile(data)
    need(not any('signature' in part.casefold() for path in cfb.streams for part in path),
         'Signed CFB streams are unsupported')
    owned = set()
    def claim(ids):
        need(len(set(ids)) == len(ids) and not owned.intersection(ids), 'CFB allocation overlap')
        owned.update(ids)
    def chain(start, count=None):
        result, seen, sid = [], set(), start
        if count == 0 and sid == FREE:
            return result
        while sid != END:
            need(0 <= sid < cfb.nsectors and sid not in seen, 'Invalid allocation chain')
            seen.add(sid)
            result.append(sid)
            need(count is None or len(result) <= count, 'Chain exceeds length')
            sid = cfb.fat[sid]
        need(count is None or len(result) == count, 'Chain length mismatch')
        return result
    # Claim all actual FAT/DIFAT metadata, including reserved markers. The
    # extractor has already verified referenced FAT/DIFAT sector identities.
    claim([i for i in range(cfb.nsectors) if cfb.fat[i] in (0xfffffffd, 0xfffffffc)])
    claim(chain(struct.unpack_from('<I', data, 48)[0]))
    firstmini, nmini = struct.unpack_from('<II', data, 60)
    claim(chain(firstmini, nmini))
    unit = cfb.sector_size
    root = cfb.entries[0]
    claim(chain(root['start'], (root['size'] + unit - 1) // unit))
    mini_owned, selected = set(), None
    for path, entry in cfb.streams.items():
        size = entry['size']
        if size >= 4096:
            ids = chain(entry['start'], (size + unit - 1) // unit)
            claim(ids)
            if path == ('Contents',):
                selected = ids
        else:
            # Audit every mini allocation too, although none is modified.
            sid, ids = entry['start'], set()
            for _ in range((size + 63) // 64):
                need(0 <= sid < len(cfb.mini_fat) and sid * 64 + 64 <= len(cfb.mini_stream), 'Mini allocation outside bounds')
                need(sid not in ids and sid not in mini_owned, 'Mini allocation overlap')
                ids.add(sid)
                sid = cfb.mini_fat[sid]
            need(sid == END or (not ids and sid == FREE), 'Mini chain length mismatch')
            mini_owned.update(ids)
    need(selected is not None, 'Exactly named root Contents must use ordinary FAT')
    source = cfb.read_stream('Contents')
    candidate, report = patch_native(source, plan)
    result = bytearray(data)
    allowed_offsets = set()
    for offset, (old, new) in enumerate(zip(source, candidate)):
        if old != new:
            physical = (selected[offset // unit] + 1) * unit + offset % unit
            allowed_offsets.add(physical)
            result[physical] = new
    result = bytes(result)
    need(sum(a != b for a, b in zip(data, result)) == len(allowed_offsets), 'CFB preservation failed')
    after = CompoundFile(result)
    need(after.read_stream('Contents') == candidate, 'CFB candidate readback failed')
    # Full-container equality outside changed bytes preserves all other streams,
    # their slack, directory entries, and every allocation/header byte.
    report.update({'cfb_source_sha256': sha(data), 'cfb_candidate_sha256': sha(result),
                   'unselected_cfb_bytes_preserved': True})
    return result, report

def patch_ppt(data, member, ppt_sha256, cfb_sha256, plan):
    need(len(data) <= MAX_PPT_BYTES and sha(data) == check_hash(ppt_sha256), 'PPT size/hash mismatch')
    need(member.startswith('ppt/embeddings/') and member.endswith('.bin'), 'Select a PPT embedding .bin member')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        infos = archive.infolist()
        need(len(infos) <= MAX_MEMBERS, 'ZIP member limit exceeded')
        need(len({i.filename for i in infos}) == len(infos), 'Duplicate ZIP members')
        need(sum(i.file_size for i in infos) <= MAX_PPT_BYTES, 'ZIP expansion exceeds limit')
        need(all(not i.flag_bits & 1 and i.compress_type in (0, 8) for i in infos), 'Unsupported ZIP encryption/compression')
        need(not any(i.filename.casefold().startswith('_xmlsignatures/')
                     or 'vbaprojectsignature' in i.filename.casefold() for i in infos),
             'Signed packages are unsupported')
        for item in infos:
            if item.filename == '[Content_Types].xml' or item.filename.endswith('.rels'):
                metadata = archive.read(item).lower()
                need(b'digital-signature' not in metadata and b'xmldsig' not in metadata,
                     'Package signature metadata is unsupported')
        need(member in archive.namelist(), 'Selected member missing')
        info = archive.getinfo(member)
        need(info.file_size <= MAX_BYTES, 'CFB member too large')
        candidate, report = patch_contents(archive.read(info), cfb_sha256, plan)
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w') as dest:
            dest.comment = archive.comment
            for item in infos:
                dest.writestr(copy.copy(item), candidate if item.filename == member else archive.read(item))
                need(output.tell() <= MAX_PPT_BYTES, 'Output exceeds limit')
        result = output.getvalue()
        need(len(result) <= MAX_PPT_BYTES, 'Output exceeds limit')
        with zipfile.ZipFile(io.BytesIO(result)) as verify:
            need(verify.namelist() == archive.namelist(), 'ZIP membership changed')
            for item in infos:
                expected = candidate if item.filename == member else archive.read(item)
                need(verify.read(item.filename) == expected, 'ZIP member verification failed')
    report.update({'ppt_source_sha256': sha(data), 'ppt_candidate_sha256': sha(result),
                   'member': member, 'unselected_ppt_member_payloads_preserved': True,
                   'zip_representation_preserved': False})
    return result, report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--member', required=True)
    parser.add_argument('--ppt-sha256', required=True)
    parser.add_argument('--cfb-sha256', required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    need(args.apply == bool(args.output), '--apply and --output must be used together')
    candidate, report = patch_ppt(bounded_read(args.input, MAX_PPT_BYTES), args.member,
                                  args.ppt_sha256, args.cfb_sha256, load_plan(args.plan))
    if args.apply:
        write_new(args.output, candidate)
    report['mode'] = 'applied' if args.apply else 'dry-run'
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
