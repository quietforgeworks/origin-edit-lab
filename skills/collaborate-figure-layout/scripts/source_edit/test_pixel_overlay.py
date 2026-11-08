#!/usr/bin/env python3
"""Synthetic, offline behavioral tests; no user artifacts are included."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

from pixel_overlay import make_overlay


class PixelOverlayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.old = self.root / 'old.png'
        self.new = self.root / 'new.png'
        self.out = self.root / 'overlay.png'
        self.old_image = Image.new('RGB', (9, 7), 'white')
        self.old_image.putpixel((2, 3), (0, 0, 0))
        self.new_image = Image.new('RGB', (9, 7), 'white')
        self.new_image.putpixel((5, 4), (35, 90, 210))
        self.new_image.putpixel((6, 4), (254, 255, 255))
        self.save()

    def save(self):
        self.old_image.save(self.old)
        self.new_image.save(self.new)
        self.old_hash = hashlib.sha256(self.old.read_bytes()).hexdigest()
        self.new_hash = hashlib.sha256(self.new.read_bytes()).hexdigest()

    def overlay(self, **kwargs):
        return make_overlay(self.old, self.new, self.out, self.old_hash, self.new_hash, **kwargs)

    def test_identity_coordinates_keep_shift_visible(self):
        before = (self.old.read_bytes(), self.new.read_bytes())
        report = self.overlay()
        with Image.open(self.out) as result:
            self.assertEqual(result.size, (9, 7))
            self.assertEqual(result.getpixel((2, 3)), (166, 166, 166))
            self.assertEqual(result.getpixel((5, 4)), (35, 90, 210))
            self.assertEqual(result.getpixel((6, 4)), (254, 255, 255))
            self.assertEqual(result.getpixel((0, 0)), (255, 255, 255))
        self.assertEqual(before, (self.old.read_bytes(), self.new.read_bytes()))
        self.assertEqual(report['old_new_difference_bbox'], [2, 3, 7, 5])
        self.assertEqual(report['new_nonwhite_pixels'], 2)
        self.assertFalse(report['registration_applied'])

    def test_all_new_nonwhite_pixels_preserved(self):
        self.old_image = Image.new('RGB', (256, 3), (4, 90, 200))
        self.new_image = Image.new('RGB', (256, 3), 'white')
        for x in range(256):
            self.new_image.putpixel((x, 0), (x, 255, 255))
            self.new_image.putpixel((x, 1), (255, x, 255))
            self.new_image.putpixel((x, 2), (255, 255, x))
        self.save()
        self.overlay()
        with Image.open(self.out) as result:
            for y in range(3):
                for x in range(255):
                    self.assertEqual(result.getpixel((x, y)), self.new_image.getpixel((x, y)))

    def test_new_ink_covers_old_at_same_coordinate(self):
        self.new_image.putpixel((2, 3), (233, 12, 44))
        self.save()
        self.overlay()
        with Image.open(self.out) as result:
            self.assertEqual(result.getpixel((2, 3)), (233, 12, 44))

    def test_configurable_old_opacity(self):
        for opacity, expected in [(0, 255), (0.5, 128), (1, 0)]:
            with self.subTest(opacity=opacity):
                self.overlay(old_opacity=opacity)
                with Image.open(self.out) as result:
                    self.assertEqual(result.getpixel((2, 3)), (expected,) * 3)
                self.out.unlink()

    def test_opaque_rgba_accepted(self):
        self.new_image = self.new_image.convert('RGBA')
        self.save()
        self.overlay()

    def test_identical_inputs_have_no_difference(self):
        self.new_image = self.old_image.copy()
        self.save()
        self.assertIsNone(self.overlay()['old_new_difference_bbox'])

    def test_refuse_size_mismatch(self):
        self.new_image = Image.new('RGB', (10, 7), 'white')
        self.save()
        with self.assertRaisesRegex(ValueError, 'Canvas'):
            self.overlay()
        self.assertFalse(self.out.exists())

    def test_refuse_transparency(self):
        self.new_image = self.new_image.convert('RGBA')
        self.new_image.putpixel((0, 0), (255, 255, 255, 254))
        self.save()
        with self.assertRaisesRegex(ValueError, 'transparency'):
            self.overlay()
        self.assertFalse(self.out.exists())

    def test_refuse_wrong_hash(self):
        self.old_hash = '0' * 64
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            self.overlay()
        self.assertFalse(self.out.exists())

    def test_refuse_invalid_hash(self):
        self.new_hash = 'NOT A HASH'
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            self.overlay()

    def test_refuse_opacity(self):
        for opacity in [-0.1, 1.1, float('nan'), float('inf'), True, '0.35']:
            with self.subTest(opacity=opacity), self.assertRaises(ValueError):
                self.overlay(old_opacity=opacity)
        self.assertFalse(self.out.exists())

    def test_refuse_existing_output_and_source(self):
        self.out.write_bytes(b'keep')
        with self.assertRaisesRegex(ValueError, 'existing output'):
            self.overlay()
        self.assertEqual(self.out.read_bytes(), b'keep')
        self.out = self.old
        with self.assertRaisesRegex(ValueError, 'source overwrite'):
            self.overlay()

    def test_refuse_dangling_output_symlink(self):
        self.out.symlink_to(self.root / 'absent.png')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.overlay()
        self.assertFalse((self.root / 'absent.png').exists())

    def test_refuse_wrong_output_extension(self):
        self.out = self.root / 'comparison.jpg'
        with self.assertRaisesRegex(ValueError, 'new .png'):
            self.overlay()

    def test_refuse_non_png_and_animated_png(self):
        self.new_image.save(self.new, format='BMP')
        self.new_hash = hashlib.sha256(self.new.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, 'single-frame PNG'):
            self.overlay()
        self.new_image.save(self.new, format='PNG', save_all=True, append_images=[self.old_image], duration=100)
        self.new_hash = hashlib.sha256(self.new.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, 'single-frame PNG'):
            self.overlay()

    def test_cli(self):
        script = Path(__file__).with_name('pixel_overlay.py')
        process = subprocess.run([sys.executable, str(script), str(self.old), str(self.new), str(self.out),
                                  '--old-sha256', self.old_hash, '--new-sha256', self.new_hash],
                                 capture_output=True, text=True, timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)['coordinates'], 'identity')
        self.assertTrue(self.out.exists())


if __name__ == '__main__':
    unittest.main()
