#!/usr/bin/env python3
"""Exercise local CLIs on generated synthetic sources only; never accepts a user deck.

By default validates package operations without a renderer. --render uses an
already installed Inkscape for real SVG rasterization, never Office or Origin.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from lxml import etree as E
from PIL import Image, ImageChops
import pptx_origin as p
import svg_edit
from synthetic_fixtures import SVG, png_bytes
from test_extractors import cfb_fixture, emf_fixture, wmf_fixture
from test_pptx_origin import build_ole_fixture, write_parts
from test_paired_vml import paired


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def run_smoke(folder, render=False):
    folder = Path(folder).absolute()
    need(not folder.exists() and not folder.is_symlink(), 'Use a new output directory')
    renderer = shutil.which('inkscape') if render else None
    need(not render or renderer, '--render requires already installed Inkscape')
    folder.mkdir(parents=False)
    script_dir = Path(__file__).resolve().parent
    commands = []

    def cli(script, *args, report=None):
        command = [sys.executable] + (['-O'] if sys.flags.optimize else []) + [str(script_dir / script), *map(str, args)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        need(result.returncode == 0, f'{script} failed: {result.stderr}')
        value = json.loads(result.stdout)
        commands.append([script, *[str(a).replace(str(folder) + '/', '') for a in args]])
        if report:
            with (folder / report).open('x', encoding='utf-8') as stream: json.dump(value, stream, indent=2)
        return value

    plain, legacy, source = [folder / n for n in ('plain.pptx', 'paired.pptx', 'source.pptx')]
    build_ole_fixture(plain); paired(plain, legacy)
    pkg = p.Package(legacy); part, root = pkg.slide(1)
    blip = root.find('.//p:pic/p:blipFill/a:blip', p.NS)
    ext = E.SubElement(E.SubElement(blip, p.q('a', 'extLst')), p.q('a', 'ext'), uri=p.SVG_EXT)
    E.SubElement(ext, p.q('asvg', 'svgBlip'), {p.q('r', 'embed'): 'rIdSyntheticSvg'})
    rp = p.rels_part(part); rels = p.xml(pkg.parts[rp])
    E.SubElement(rels, p.q('pr', 'Relationship'), Id='rIdSyntheticSvg', Type=p.IMAGE_REL, Target='../media/synthetic.svg')
    ct = p.xml(pkg.parts['[Content_Types].xml'])
    E.SubElement(ct, p.q('ct', 'Default'), Extension='svg', ContentType='image/svg+xml')
    write_parts(legacy, source, {part: p.serialize(root), rp: p.serialize(rels), '[Content_Types].xml': p.serialize(ct),
                                'ppt/embeddings/syntheticOrigin.bin': cfb_fixture()}, {'ppt/media/synthetic.svg': SVG.encode()})
    original = source.read_bytes()
    inventory = cli('pptx_origin.py', 'inspect', source, report='inventory.json')
    row = inventory['slides'][0]['objects'][0]
    need(row['key'] == 'ole:0' and row['safe_replace_supported'], 'Unexpected fixture inventory')
    for asset, name in [(row['previews'][0]['svg'][0], 'original.svg'),
                        (row['previews'][0]['raster_or_original'], 'original.png'), (row['ole'], 'original.bin')]:
        result = cli('pptx_origin.py', 'extract', source, '--part', asset['part'], '--output', folder / name)
        need(result['sha256'] == asset['sha256'], 'Extracted part hash mismatch')
    cli('cfb_extract.py', folder / 'original.bin', '--stream', 'Contents', '--output', folder / 'contents.payload',
        '--expected-sha256', row['ole']['sha256'], '--report', folder / 'streams.json')
    metadata = cli('compat.py', folder / 'contents.payload', report='payload-metadata.json')
    need(not metadata['parsed'] and not metadata['compatibility_complete'], 'Metadata mistaken for native compatibility')
    wrapped = folder / 'wrapped.wmf'; wrapped.write_bytes(wmf_fixture(parts=2))
    cli('wmf_emf_extract.py', wrapped, folder / 'original.emf', '--report', folder / 'emf-report.json',
        '--expected-sha256', hashlib.sha256(wrapped.read_bytes()).hexdigest())
    need((folder / 'original.emf').read_bytes() == emf_fixture(), 'EMF extraction changed bytes')

    inspected = cli('svg_edit.py', 'inspect', folder / 'original.svg', report='svg-inventory.json')
    plan = {'source_sha256': inspected['sha256'], 'edits': [{'selector': {'id': 'curve'}, 'set': {'stroke': '#dd3322', 'stroke-width': '6'}}]}
    plan_file = folder / 'style-plan.json'; plan_file.write_text(json.dumps(plan), encoding='utf-8')
    cli('svg_edit.py', 'edit', folder / 'original.svg', folder / 'changed.svg', '--plan', plan_file, report='svg-edit-report.json')
    before = svg_edit.load_svg(folder / 'original.svg')[1]
    after = svg_edit.load_svg(folder / 'changed.svg')[1]
    changed_curve = svg_edit.resolve(after, {'id': 'curve'})
    need(changed_curve.get('style') == 'stroke:#dd3322;stroke-width:6', 'Requested style did not apply')
    changed_curve.attrib.pop('style')
    need(E.tostring(before, method='c14n') == E.tostring(after, method='c14n'), 'Unexpected SVG content or geometry change')

    before_png, after_png = folder / 'before-render.png', folder / 'changed.png'
    if render:
        for svg, png in [('original.svg', before_png), ('changed.svg', after_png)]:
            result = subprocess.run([renderer, str(folder / svg), '--export-type=png', '--export-background=white',
                                     '--export-background-opacity=1', '--export-filename=' + str(png)], capture_output=True, text=True, timeout=60)
            need(result.returncode == 0 and png.is_file(), 'Inkscape rasterization failed: ' + result.stderr)
        with Image.open(before_png) as old, Image.open(after_png) as new:
            need(old.size == new.size == (640, 360), 'Raster canvas changed')
            bbox = ImageChops.difference(old.convert('RGB'), new.convert('RGB')).getbbox()
            need(bbox is not None, 'Rendered edit was a no-op')
            need(bbox[0] >= 35 and bbox[1] >= 55 and bbox[2] <= 605 and bbox[3] <= 285, 'Rendered change escaped synthetic curve bounds')
    else:
        # Known primitive fixture fallbacks test ZIP plumbing, not SVG rendering.
        before_png.write_bytes(png_bytes()); after_png.write_bytes(png_bytes('#dd3322', 6))
    cli('pixel_overlay.py', before_png, after_png, folder / 'overlay.png',
        '--old-sha256', p.digest(before_png.read_bytes()), '--new-sha256', p.digest(after_png.read_bytes()), report='overlay-report.json')
    output = folder / 'edited.pptx'
    replacement = cli('pptx_origin.py', 'replace', source, output, '--slide', '1', '--object', row['key'],
                      '--png', after_png, '--svg', folder / 'changed.svg', '--acknowledge-stale-ole', report='replacement.json')
    verified = cli('pptx_origin.py', 'verify', source, output, report='preservation.json')
    allowed = {part, rp, 'ppt/drawings/vmlDrawing1.vml', 'ppt/drawings/_rels/vmlDrawing1.vml.rels'}
    need(set(verified['changed_existing_parts']) == allowed, 'Unexpected package change set')
    need(not verified['removed_parts'] and not verified['relationship_errors'], 'Removed parts or broken relationships')
    need(verified['embedded_payloads_unchanged'] and replacement['existing_relationships_preserved'], 'OLE payload or prior relationship changed')
    need(verified['unchanged_slides'] == [2] and source.read_bytes() == original, 'Source or untouched slide changed')
    baseline, final = p.Package(source), p.Package(output)
    need(baseline.inspect()['slides'][0]['objects'][1] == final.inspect()['slides'][0]['objects'][1], 'Shared ordinary picture changed')
    new_row = final.inspect()['slides'][0]['objects'][0]
    need(new_row['vml_preview']['part'] == new_row['previews'][0]['raster_or_original']['part'], 'Paired PNG previews disagree')
    need(new_row['previews'][0]['raster_or_original']['sha256'] == p.digest(after_png.read_bytes()), 'Fallback bytes differ')
    need(new_row['previews'][0]['svg'][0]['sha256'] == p.digest((folder / 'changed.svg').read_bytes()), 'SVG bytes differ')
    old_root, new_root = baseline.slide(1)[1], final.slide(1)[1]
    for expression in ('.//p:sp', './/a:xfrm', './/p:xfrm'):
        need([E.tostring(n, method='c14n') for n in old_root.findall(expression, p.NS)] ==
             [E.tostring(n, method='c14n') for n in new_root.findall(expression, p.NS)], 'Native text or geometry changed')
    report = {'status': 'passed', 'synthetic_only': True, 'source_sha256': p.digest(original), 'output_sha256': p.digest(output.read_bytes()),
              'commands': commands, 'source_unchanged': True, 'embedded_payloads_unchanged': True,
              'paired_vml_png_and_svg_verified': True, 'native_text_and_geometry_unchanged': True,
              'svg_rasterization': 'Inkscape executed; changed pixels bounded to synthetic curve' if render else 'not run; known synthetic primitive PNGs used for package plumbing',
              'powerpoint_open': 'not run', 'origin_open_save_refresh': 'not run',
              'note': 'Synthetic package/OLE envelopes are not real editable Origin graphs or app compatibility evidence.'}
    with (folder / 'smoke-report.json').open('x', encoding='utf-8') as stream: json.dump(report, stream, indent=2)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True, type=Path, help='New directory for synthetic evidence')
    parser.add_argument('--render', action='store_true', help='Rasterize synthetic SVGs with installed Inkscape')
    args = parser.parse_args()
    report = run_smoke(args.output_dir, args.render)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
