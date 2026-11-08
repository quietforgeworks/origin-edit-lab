"""Read-only EMF pen metadata layout regressions; no rendering or writes.

EMREXTCREATEPEN: EMR(8), five DWORD fields(20), EXTLOGPEN starts at 28.
EXTLOGPEN COLORREF is its fourth DWORD, record-relative offset 40.
https://learn.microsoft.com/en-us/windows/win32/api/wingdi/ns-wingdi-emrextcreatepen
https://learn.microsoft.com/en-us/windows/win32/api/wingdi/ns-wingdi-extlogpen
"""
import hashlib
import struct
import unittest
import wmf_emf_extract as emf


def pen_fixture(kind, color=b'\x12\x34\x56\x00', hatch=0x00abcdef,
                size=None, entries=()):
    length = (28 if kind == 38 else 52 + 4 * len(entries)) if size is None else size
    record = bytearray(length)
    struct.pack_into('<III', record, 0, kind, length, 7)
    if kind == 38:
        struct.pack_into('<Iii', record, 12, 0, 3, 0)
        record[24:28] = color
    elif length >= 52:
        struct.pack_into('<III', record, 28, 0x10000, 3, 2)
        record[40:44] = color
        struct.pack_into('<II', record, 44, hatch, len(entries))
        for i, item in enumerate(entries):
            struct.pack_into('<I', record, 52 + 4 * i, item)
    header = bytearray(88)
    struct.pack_into('<II', header, 0, 1, 88)
    header[40:44] = b' EMF'
    struct.pack_into('<II', header, 48, 88 + len(record) + 20, 3)
    return bytes(header + record + struct.pack('<5I', 14, 20, 0, 0, 20))


class PenMetadataTests(unittest.TestCase):
    def test_extended_color_not_hatch(self):
        report = emf.inspect_emf(pen_fixture(95))
        pen = report['records'][1]
        self.assertEqual(pen['color_rgb_hex'], '123456')
        self.assertEqual(pen['color_offset'], 88 + 40)
        self.assertEqual(pen['pen_handle'], 7)

    def test_standard_createpen_unchanged(self):
        pen = emf.inspect_emf(pen_fixture(38))['records'][1]
        self.assertEqual(pen['color_rgb_hex'], '123456')
        self.assertEqual(pen['color_offset'], 88 + 24)

    def test_color_channel_order(self):
        for color, expected in [(b'\xff\0\0\0', 'ff0000'),
                                (b'\0\xff\0\0', '00ff00'),
                                (b'\0\0\xff\0', '0000ff')]:
            with self.subTest(color=expected):
                self.assertEqual(emf.inspect_emf(pen_fixture(95, color))['records'][1]['color_rgb_hex'], expected)

    def test_hatch_does_not_change_color(self):
        for hatch in (0, 1, 0xffffff, 0xffffffff):
            with self.subTest(hatch=hatch):
                self.assertEqual(emf.inspect_emf(pen_fixture(95, hatch=hatch))['records'][1]['color_rgb_hex'], '123456')

    def test_style_entries_do_not_change_color(self):
        pen = emf.inspect_emf(pen_fixture(95, entries=(0x111111, 0x222222)))['records'][1]
        self.assertEqual(pen['size'], 60)
        self.assertEqual(pen['color_rgb_hex'], '123456')

    def test_exact_minimum_and_truncated_extpen(self):
        self.assertEqual(emf.inspect_emf(pen_fixture(95))['record_count'], 3)
        for size in (12, 28, 40, 44, 48):
            with self.subTest(size=size), self.assertRaises(emf.FormatError):
                emf.inspect_emf(pen_fixture(95, size=size))

    def test_read_only_bytes_and_hash(self):
        original = pen_fixture(95)
        before = bytes(original)
        report = emf.inspect_emf(original)
        self.assertEqual(original, before)
        self.assertEqual(report['sha256'], hashlib.sha256(before).hexdigest())

    def test_strict_envelope_guards_still_apply(self):
        for offset, value in ((48, 999), (52, 4), (88 + 4, 56), (88 + 52, 33)):
            candidate = bytearray(pen_fixture(95))
            struct.pack_into('<I', candidate, offset, value)
            with self.subTest(offset=offset), self.assertRaises(emf.FormatError):
                emf.inspect_emf(bytes(candidate))


if __name__ == '__main__':
    unittest.main()
