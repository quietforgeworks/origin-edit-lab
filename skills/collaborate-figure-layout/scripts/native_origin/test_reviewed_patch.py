"""Synthetic-only tests: no user sample bytes, identities, or field offsets."""
import copy
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile

from reviewed_patch import PatchError, patch_native, sha, write_new, load_plan
from ppt_contents_patch import patch_contents, patch_ppt


def plan_for(source):
    candidate = bytearray(source)
    candidate[17] ^= 1
    return {'source_sha256': sha(source), 'candidate_sha256': sha(candidate),
            'source_bytes': len(source), 'candidate_bytes': len(source),
            'changed_byte_count': 1, 'changes': [[17, source[17], candidate[17]]]}


def synthetic_cfb():
    """Small CFB v3, two ordinary streams, no mini sectors or DIFAT sectors."""
    free, end, fatmark = 0xffffffff, 0xfffffffe, 0xfffffffd
    header = bytearray(512)
    header[:8] = bytes.fromhex('d0cf11e0a1b11ae1')
    struct.pack_into('<HHHHH', header, 24, 0x3e, 3, 0xfffe, 9, 6)
    struct.pack_into('<9I', header, 40, 0, 1, 0, 0, 4096, end, 0, end, 0)
    struct.pack_into('<109I', header, 76, 1, *([free] * 108))
    def entry(name, kind, start, size, child=free, right=free):
        data = bytearray(128)
        encoded = (name + '\0').encode('utf-16le')
        data[:len(encoded)] = encoded
        struct.pack_into('<HBBIII', data, 64, len(encoded), kind, 1, free, right, child)
        struct.pack_into('<IQ', data, 116, start, size)
        return bytes(data)
    directory = entry('Root Entry', 5, end, 0, child=1)
    directory += entry('Contents', 2, 2, 4096, right=2)
    directory += entry('Other', 2, 10, 4096) + bytes(128)
    fat = [end, fatmark] + list(range(3, 10)) + [end] + list(range(11, 18)) + [end]
    fat += [free] * (128 - len(fat))
    source = b'CPYUA' + bytes((i % 251 for i in range(4091)))
    return bytes(header) + directory + struct.pack('<128I', *fat) + source + b'Z' * 4096, source


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.source = b'CPYUA' + bytes(range(100))
        self.plan = plan_for(self.source)

    def test_valid_list_and_dict(self):
        for change in ([17, self.source[17], self.source[17] ^ 1],
                       {'offset': 17, 'old': self.source[17], 'new': self.source[17] ^ 1}):
            self.plan['changes'] = [change]
            candidate, report = patch_native(self.source, self.plan)
            self.assertEqual(sha(candidate), self.plan['candidate_sha256'])
            self.assertEqual(report['scientific_semantics'], 'NOT VERIFIED')

    def test_refusals(self):
        updates = [
            {'source_sha256': '0' * 64}, {'candidate_sha256': '0' * 64},
            {'source_bytes': 1}, {'candidate_bytes': len(self.source) + 1},
            {'candidate_bytes': None}, {'length': len(self.source)},
            {'changed_byte_count': True}, {'changed_byte_count': 2},
            {'changes': self.plan['changes'] * 2},
            {'changes': [[17, 222, 223]]}, {'changes': [[999, 0, 1]]},
            {'changes': [[1, 80, 1]]}, {'changes': [[True, 0, 1]]},
            {'changes': [[17, self.source[17], 256]]}, {'changes': []},
        ]
        for update in updates:
            with self.subTest(update=update), self.assertRaises(PatchError):
                patch_native(self.source, dict(self.plan, **update))
        with self.assertRaises(PatchError):
            patch_native(b'WRONG' + self.source[5:], self.plan)

    def test_exclusive_output_and_duplicate_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'out'
            write_new(path, b'original')
            with self.assertRaises(FileExistsError):
                write_new(path, b'replacement')
            self.assertEqual(path.read_bytes(), b'original')
            path.write_text('{"changes": [], "changes": []}')
            with self.assertRaises(PatchError):
                load_plan(path)

    def test_cli_dry_run_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, plan, output = (Path(tmp) / name for name in ('source', 'plan', 'out'))
            source.write_bytes(self.source)
            plan.write_text(json.dumps(self.plan))
            cmd = [sys.executable, str(Path(__file__).with_name('reviewed_patch.py')), str(source), '--plan', str(plan)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(result.stdout)['mode'], 'dry-run')
            self.assertFalse(output.exists())
            subprocess.run(cmd + ['--apply', '--output', str(output)], capture_output=True, check=True)
            self.assertEqual(sha(output.read_bytes()), self.plan['candidate_sha256'])
            result = subprocess.run(cmd + ['--apply', '--output', str(output)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            result = subprocess.run(cmd + ['--output', str(output)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)


class CfbTests(unittest.TestCase):
    def test_cfb_and_ppt_preservation(self):
        cfb, source = synthetic_cfb()
        plan = plan_for(source)
        candidate, _ = patch_contents(cfb, sha(cfb), plan)
        differences = [i for i, (a, b) in enumerate(zip(cfb, candidate)) if a != b]
        self.assertEqual(differences, [3 * 512 + 17])
        stream = io.BytesIO()
        member = 'ppt/embeddings/oleObject1.bin'
        with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.comment = b'synthetic archive'
            z.writestr('[Content_Types].xml', b'<Types/>')
            z.writestr(member, cfb)
            z.writestr('ppt/media/image.png', b'synthetic preview unchanged')
            z.writestr('ppt/slides/slide1.xml', b'<synthetic/>')
        ppt = stream.getvalue()
        result, report = patch_ppt(ppt, member, sha(ppt), sha(cfb), plan)
        with zipfile.ZipFile(io.BytesIO(ppt)) as before, zipfile.ZipFile(io.BytesIO(result)) as after:
            self.assertEqual(before.comment, after.comment)
            for name in before.namelist():
                self.assertEqual(after.read(name), candidate if name == member else before.read(name))
        self.assertFalse(report['zip_representation_preserved'])
        with self.assertRaises(PatchError):
            patch_ppt(ppt, member, '0' * 64, sha(cfb), plan)
        with self.assertRaises(PatchError):
            patch_ppt(ppt, member, sha(ppt), '0' * 64, plan)

    def test_refuse_signed_package(self):
        cfb, source = synthetic_cfb()
        member = 'ppt/embeddings/oleObject1.bin'
        for signature_name, signature_data in (
                ('_xmlsignatures/sig1.xml', b'<Signature/>'),
                ('[Content_Types].xml', b'application/vnd.openxmlformats-package.digital-signature-xmlsignature+xml'),
                ('ppt/vbaProjectSignature.bin', b'signature')):
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, 'w') as z:
                z.writestr(member, cfb)
                z.writestr(signature_name, signature_data)
            ppt = stream.getvalue()
            with self.subTest(signature_name=signature_name), self.assertRaises(PatchError):
                patch_ppt(ppt, member, sha(ppt), sha(cfb), plan_for(source))

    def test_refuse_overlapping_stream_allocations(self):
        cfb, source = synthetic_cfb()
        bad = bytearray(cfb)
        struct.pack_into('<I', bad, 512 + 2 * 128 + 116, 2)
        with self.assertRaisesRegex(PatchError, 'overlap'):
            patch_contents(bytes(bad), sha(bad), plan_for(source))

    def test_refuse_reserved_metadata_allocation(self):
        cfb, source = synthetic_cfb()
        bad = bytearray(cfb)
        # Make the directory chain also a full-sized Contents stream. The
        # extractor can read the directory; the allocation audit must reject.
        struct.pack_into('<I', bad, 512 + 128 + 116, 0)
        with self.assertRaises(PatchError):
            patch_contents(bytes(bad), sha(bad), plan_for(source))

    def test_refuse_mini_contents(self):
        cfb, source = synthetic_cfb()
        bad = bytearray(cfb)
        struct.pack_into('<Q', bad, 512 + 128 + 120, 0)
        struct.pack_into('<I', bad, 512 + 128 + 116, 0xfffffffe)
        with self.assertRaisesRegex(PatchError, 'ordinary FAT'):
            patch_contents(bytes(bad), sha(bad), plan_for(source))

if __name__ == '__main__':
    unittest.main()
