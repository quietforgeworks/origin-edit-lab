"""Synthetic read-only extractor tests; no external corpus is bundled or loaded."""
import struct
import unittest

import cfb_extract as cfb
import wmf_emf_extract as wmf


def changed(data, offset, fmt, *values):
    result = bytearray(data)
    struct.pack_into(fmt, result, offset, *values)
    return bytes(result)


def emf_fixture():
    data = bytearray(108)
    struct.pack_into('<II', data, 0, 1, 88)
    data[40:44] = b' EMF'
    struct.pack_into('<II', data, 48, 108, 2)
    struct.pack_into('<IIIII', data, 88, 14, 20, 0, 0, 20)
    return bytes(data)


def wmf_fixture(parts=1, placeable=False):
    emf = emf_fixture()
    pieces = [emf] if parts == 1 else [emf[:52], emf[52:]]
    records, remaining = [], len(emf)
    for piece in pieces:
        remaining -= len(piece)
        meta = struct.pack('<IIIHIIIII', 0x43464d57, 1, 0x10000, 0, 0,
                           len(pieces), len(piece), remaining, len(emf))
        record = struct.pack('<IHHH', (44 + len(piece))//2, 0x626, 15,
                             34 + len(piece)) + meta + piece
        records.append(record)
    records.append(struct.pack('<IH', 3, 0))
    body = b''.join(records)
    result = struct.pack('<HHHIHIH', 1, 9, 0x300, (18+len(body))//2, 1,
                         max(len(r)//2 for r in records), 0) + body
    if placeable:
        prefix = bytearray(22)
        struct.pack_into('<I', prefix, 0, 0x9ac6cdd7)
        checksum = 0
        for word in struct.unpack('<10H', prefix[:20]): checksum ^= word
        struct.pack_into('<H', prefix, 20, checksum)
        result = bytes(prefix) + result
    return result


def cfb_fixture():
    header = bytearray(512)
    header[:8] = bytes.fromhex('d0cf11e0a1b11ae1')
    struct.pack_into('<HHHHH', header, 24, 0x3e, 3, 0xfffe, 9, 6)
    struct.pack_into('<9I', header, 40, 0, 1, 1, 0, 4096, 2, 1, cfb.END, 0)
    struct.pack_into('<109I', header, 76, 0, *([cfb.FREE]*108))
    fat = struct.pack('<128I', cfb.FAT, cfb.END, cfb.END, cfb.END, *([cfb.FREE]*124))
    def entry(name, kind, start, size, child=cfb.FREE, right=cfb.FREE):
        data = bytearray(128)
        name_bytes = (name + '\0').encode('utf-16le')
        data[:len(name_bytes)] = name_bytes
        struct.pack_into('<HBBIII', data, 64, len(name_bytes), kind, 1,
                         cfb.FREE, right, child)
        struct.pack_into('<IQ', data, 116, start, size)
        return bytes(data)
    directory = entry('Root Entry', 5, 3, 128, child=1)
    directory += entry('Contents', 2, 0, 11, right=2)
    directory += entry('\x01Ole', 2, 1, 20) + bytes(128)
    mini_fat = struct.pack('<128I', cfb.END, cfb.END, *([cfb.FREE]*126))
    mini_stream = b'CPYUA test\n' + bytes(64-11) + b'O'*20 + bytes(512-84)
    return bytes(header) + fat + directory + mini_fat + mini_stream


class EmfTests(unittest.TestCase):
    def test_valid_envelope(self):
        self.assertEqual(wmf.inspect_emf(emf_fixture())['record_count'], 2)
    def test_wrong_signature(self):
        with self.assertRaises(wmf.FormatError): wmf.inspect_emf(changed(emf_fixture(), 40, '<I', 0))
    def test_wrong_byte_count(self):
        with self.assertRaises(wmf.FormatError): wmf.inspect_emf(changed(emf_fixture(), 48, '<I', 999))
    def test_wrong_record_count(self):
        with self.assertRaises(wmf.FormatError): wmf.inspect_emf(changed(emf_fixture(), 52, '<I', 3))
    def test_record_overrun(self):
        with self.assertRaises(wmf.FormatError): wmf.inspect_emf(changed(emf_fixture(), 92, '<I', 24))
    def test_record_unaligned(self):
        with self.assertRaises(wmf.FormatError): wmf.inspect_emf(changed(emf_fixture(), 92, '<I', 19))
    def test_eof_missing(self):
        with self.assertRaises(wmf.FormatError): wmf.inspect_emf(changed(emf_fixture(), 88, '<I', 33))
    def test_limit(self):
        with self.assertRaises(wmf.FormatError): wmf.inspect_emf(emf_fixture(), max_bytes=100)


class WmfTests(unittest.TestCase):
    def test_single(self):
        self.assertEqual(wmf.extract_embedded_emf(wmf_fixture())[0], emf_fixture())
    def test_split(self):
        data, report = wmf.extract_embedded_emf(wmf_fixture(parts=2))
        self.assertEqual(data, emf_fixture()); self.assertEqual(len(report['chunks']), 2)
    def test_placeable(self):
        self.assertTrue(wmf.extract_embedded_emf(wmf_fixture(placeable=True))[1]['placeable_header'])
    def test_placeable_checksum(self):
        with self.assertRaises(wmf.FormatError): wmf.extract_embedded_emf(changed(wmf_fixture(placeable=True), 20, '<H', 0))
    def test_source_hash(self):
        with self.assertRaises(wmf.FormatError): wmf.extract_embedded_emf(wmf_fixture(), expected_sha256='0'*64)
    def test_size_header(self):
        with self.assertRaises(wmf.FormatError): wmf.extract_embedded_emf(changed(wmf_fixture(), 6, '<I', 999))
    def test_chunk_byte_count(self):
        with self.assertRaises(wmf.FormatError): wmf.extract_embedded_emf(changed(wmf_fixture(), 26, '<H', 5))
    def test_chunk_count(self):
        with self.assertRaises(wmf.FormatError): wmf.extract_embedded_emf(changed(wmf_fixture(), 46, '<I', 2))
    def test_chunk_remaining(self):
        with self.assertRaises(wmf.FormatError): wmf.extract_embedded_emf(changed(wmf_fixture(parts=2), 54, '<I', 55))
    def test_chunk_total(self):
        with self.assertRaises(wmf.FormatError): wmf.extract_embedded_emf(changed(wmf_fixture(), 58, '<I', 109))
    def test_flags(self):
        with self.assertRaises(wmf.FormatError): wmf.extract_embedded_emf(changed(wmf_fixture(), 42, '<I', 1))
    def test_truncated(self):
        with self.assertRaises(wmf.FormatError): wmf.extract_embedded_emf(wmf_fixture()[:-1])
    def test_max_record(self):
        with self.assertRaises(wmf.FormatError): wmf.extract_embedded_emf(changed(wmf_fixture(), 12, '<I', 1))
    def test_eof_missing(self):
        data = wmf_fixture()
        with self.assertRaises(wmf.FormatError): wmf.extract_embedded_emf(changed(data, len(data)-2, '<H', 33))


class CfbTests(unittest.TestCase):
    def test_contents(self):
        obj = cfb.CompoundFile(cfb_fixture())
        self.assertEqual(obj.read_stream('Contents'), b'CPYUA test\n')
        self.assertEqual(obj.read_stream(('\x01Ole',)), b'O'*20)
        self.assertEqual(len(obj.inventory()['streams']), 2)
    def test_missing_stream(self):
        with self.assertRaises(cfb.FormatError): cfb.CompoundFile(cfb_fixture()).read_stream('Missing')
    def test_signature(self):
        with self.assertRaises(cfb.FormatError): cfb.CompoundFile(changed(cfb_fixture(), 0, '<I', 0))
    def test_alignment(self):
        with self.assertRaises(cfb.FormatError): cfb.CompoundFile(cfb_fixture()[:-1])
    def test_byte_order(self):
        with self.assertRaises(cfb.FormatError): cfb.CompoundFile(changed(cfb_fixture(), 28, '<H', 0))
    def test_bad_fat_id(self):
        with self.assertRaises(cfb.FormatError): cfb.CompoundFile(changed(cfb_fixture(), 76, '<I', 99))
    def test_bad_fat_count(self):
        with self.assertRaises(cfb.FormatError): cfb.CompoundFile(changed(cfb_fixture(), 44, '<I', 2))
    def test_directory_cycle(self):
        with self.assertRaises(cfb.FormatError): cfb.CompoundFile(changed(cfb_fixture(), 1024+128+72, '<I', 1))
    def test_minifat_cycle(self):
        obj = cfb.CompoundFile(changed(cfb_fixture(), 1536, '<I', 0))
        with self.assertRaises(cfb.FormatError): obj.read_stream('Contents')
    def test_fat_cycle(self):
        with self.assertRaises(cfb.FormatError): cfb.CompoundFile(changed(cfb_fixture(), 512+4, '<I', 1))
    def test_stream_oversize(self):
        with self.assertRaises(cfb.FormatError): cfb.CompoundFile(changed(cfb_fixture(), 1024+128+120, '<Q', 999999))
    def test_bad_minifat_count(self):
        with self.assertRaises(cfb.FormatError): cfb.CompoundFile(changed(cfb_fixture(), 64, '<I', 2))
    def test_source_hash(self):
        with self.assertRaises(cfb.FormatError): cfb.CompoundFile(cfb_fixture(), expected_sha256='0'*64)
    def test_limit(self):
        with self.assertRaises(cfb.FormatError): cfb.CompoundFile(cfb_fixture(), max_bytes=512)


if __name__ == '__main__':
    unittest.main()
