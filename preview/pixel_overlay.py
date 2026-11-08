#!/usr/bin/env python3
"""Identity-coordinate PNG comparison; preserves new nonwhite RGB pixels exactly."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys

from PIL import Image, ImageChops

MAX_BYTES = 100 * 1024 * 1024
MAX_PIXELS = 40_000_000


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_opaque_png(path, expected_hash):
    if not isinstance(expected_hash, str) or not re.fullmatch(r'[0-9a-f]{64}', expected_hash):
        raise ValueError('An inspected lowercase SHA-256 is required for each input')
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('PNG exceeds 100 MiB input limit')
    data = path.read_bytes()
    if digest(data) != expected_hash:
        raise ValueError('Source SHA-256 does not match inspected input')
    with Image.open(io.BytesIO(data)) as image:
        if image.format != 'PNG' or getattr(image, 'n_frames', 1) != 1:
            raise ValueError('Expected a single-frame PNG')
        if image.width * image.height > MAX_PIXELS:
            raise ValueError('PNG exceeds 40 million pixel limit')
        if image.mode not in {'1', 'L', 'LA', 'P', 'RGB', 'RGBA'}:
            raise ValueError('Use an 8-bit opaque PNG')
        rgba = image.convert('RGBA')
        if rgba.getchannel('A').getextrema() != (255, 255):
            raise ValueError('Render transparency onto white before comparison')
        rgb = rgba.convert('RGB')
    return data, rgb


def make_overlay(old, new, output, old_sha256, new_sha256, old_opacity=0.35):
    if isinstance(old_opacity, bool) or not isinstance(old_opacity, (int, float)) or not math.isfinite(old_opacity) or not 0 <= old_opacity <= 1:
        raise ValueError('Old opacity must be finite and between 0 and 1')
    old = Path(old).resolve(strict=True)
    new = Path(new).resolve(strict=True)
    target = Path(output).absolute()
    if target.is_symlink() or target.exists() or target.resolve() in {old, new}:
        raise ValueError('Refusing existing output, symlink or source overwrite')
    if target.suffix.lower() != '.png' or not target.parent.is_dir():
        raise ValueError('Output must be a new .png in an existing directory')
    old_bytes, old_rgb = read_opaque_png(old, old_sha256)
    new_bytes, new_rgb = read_opaque_png(new, new_sha256)
    if old_rgb.size != new_rgb.size:
        raise ValueError('Canvas dimensions must match; registration and resizing are forbidden')

    # Exact, deterministic grayscale opacity on white; no geometric operation.
    lut = [int(255 * (1 - old_opacity) + value * old_opacity + 0.5) for value in range(256)]
    background = old_rgb.convert('L').point(lut).convert('RGB')
    minimum_channel = ImageChops.darker(ImageChops.darker(*new_rgb.split()[:2]), new_rgb.getchannel('B'))
    new_ink = minimum_channel.point([255] * 255 + [0])
    result = Image.composite(new_rgb, background, new_ink)
    difference = ImageChops.difference(old_rgb, new_rgb)
    difference_bbox = difference.getbbox()
    ink_pixels = new_ink.histogram()[255]
    encoded = io.BytesIO()
    result.save(encoded, format='PNG')
    output_bytes = encoded.getvalue()
    if digest(old.read_bytes()) != digest(old_bytes) or digest(new.read_bytes()) != digest(new_bytes):
        raise ValueError('An input changed during comparison; no output written')
    with target.open('xb') as stream:
        stream.write(output_bytes)
    return {
        'old_sha256': digest(old_bytes), 'new_sha256': digest(new_bytes),
        'output_sha256': digest(output_bytes), 'width': result.width, 'height': result.height,
        'old_grayscale_opacity': old_opacity, 'new_nonwhite_pixels': ink_pixels,
        'old_new_difference_bbox': list(difference_bbox) if difference_bbox else None,
        'coordinates': 'identity', 'registration_applied': False,
        'new_nonwhite_rgb_preserved': True, 'sources_unchanged': True,
        'note': 'Exact-white mask only. Visual review and allowed-region checks remain separate.'
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('old', type=Path)
    parser.add_argument('new', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--old-sha256', required=True)
    parser.add_argument('--new-sha256', required=True)
    parser.add_argument('--old-opacity', type=float, default=0.35)
    args = parser.parse_args()
    try:
        report = make_overlay(args.old, args.new, args.output, args.old_sha256, args.new_sha256, args.old_opacity)
        print(json.dumps(report, indent=2))
        return 0
    except Exception as error:
        print(json.dumps({'status': 'blocked_or_failed', 'error': str(error)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
