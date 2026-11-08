#!/usr/bin/env python3
"""Bounded guide-only OOXML edit. Does not infer alignment or edit science.

Requires lxml and the bundled source_edit/pptx_origin.py. A plan is an explicit
coordinate specification, not evidence of user approval. No Office/Origin is run.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
import zipfile

from lxml import etree as E
from source_edit import pptx_origin as pp

SCHEMA = 'figure-alignment-guides/v1'
GROUP_NAME = 'FIGURE_ALIGNMENT_GUIDES::v1'
LINE_PREFIX = 'ALIGNMENT_GUIDE::v1::'
MAX_BYTES = 256 * 1024 * 1024
MAX_PART = 64 * 1024 * 1024
MAX_ID = 4294967295
NS, q = pp.NS, pp.q


def fail(message):
    raise ValueError(message)


def exact_keys(obj, keys, context):
    if not isinstance(obj, dict) or set(obj) != set(keys):
        fail(context + ' has missing or unsupported fields')


def integer(value, low, high, context):
    if type(value) is not int or not low <= value <= high:
        fail(context + ' must be an integer in the supported range')
    return value


def json_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            fail('Duplicate JSON field: ' + key)
        out[key] = value
    return out


def read_plan(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(65537)
    if len(raw) > 65536:
        fail('Plan exceeds 64 KiB')
    return json.loads(raw, object_pairs_hook=json_object,
                      parse_constant=lambda value: fail('Non-finite JSON number: ' + value))


def canonical(root):
    return E.tostring(root, method='c14n', exclusive=True, with_comments=True)


def load_package(path):
    """Additional narrow-envelope checks; opaque media/embeddings are not run."""
    if Path(path).stat().st_size > MAX_BYTES:
        fail('Compressed PPTX exceeds 256 MiB')
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if len(infos) > 4000 or sum(i.file_size for i in infos) > MAX_BYTES:
            fail('PPTX exceeds bounded package limits')
        seen = set()
        for info in infos:
            name = info.filename
            if (not name or name != str(PurePosixPath(name)) or name.endswith('/') or
                    name.casefold() in seen or info.file_size > MAX_PART or
                    '\\' in name or name.startswith('/') or '..' in PurePosixPath(name).parts or
                    '%' in name or info.flag_bits & 1 or info.compress_type not in (0, 8) or
                    (info.external_attr >> 16) & 0o170000 == 0o120000):
                fail('Unsafe, duplicate, encrypted, or unsupported ZIP member')
            seen.add(name.casefold())
    pkg = pp.Package(path)
    if pp.digest(pkg.path.read_bytes()) != pkg.source_hash:
        fail('Source changed while reading')
    roots = {}
    for name, data in pkg.parts.items():
        lower = name.lower()
        if (lower.startswith('_xmlsignatures/') or '/activex/' in lower or
                'vbaproject' in lower or '/ctrlprops/' in lower):
            fail('Signed, macro, or ActiveX packages are unsupported')
        if lower.endswith(('.xml', '.rels')):
            root = pp.xml(data)
            if root.getprevious() is not None or root.getnext() is not None:
                fail('Top-level XML comments/processing instructions are unsupported')
            roots[name] = root
        if lower.endswith('.rels'):
            if roots[name].tag != q('pr', 'Relationships'):
                fail('Invalid relationship part')
            for rel in roots[name]:
                if (rel.tag != q('pr', 'Relationship') or
                        rel.get('TargetMode', 'Internal') != 'Internal'):
                    fail('External or unsupported relationships are not supported')
    types = roots['[Content_Types].xml']
    if types.tag != q('ct', 'Types'):
        fail('Invalid content types')
    for node in types:
        content_type = node.get('ContentType', '').lower()
        if any(word in content_type for word in ('macroenabled', 'vbaproject', 'activex', 'digital-signature')):
            fail('Active or signed content types are unsupported')
    main_types = [n.get('ContentType') for n in types
                  if n.get('PartName') == '/ppt/presentation.xml']
    if main_types != ['application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml']:
        fail('Only a standard transitional .pptx presentation is supported')
    root_rels = pkg.relationships('')
    main = [r for r in root_rels.values() if r['type'] == NS['r'] + '/officeDocument']
    if len(main) != 1 or main[0]['part'] != 'ppt/presentation.xml':
        fail('Expected one package-root presentation relationship')
    if pkg.verify_relationships():
        fail('Broken internal package relationships')
    slide_lists = pkg.presentation.findall('p:sldIdLst', NS)
    if len(slide_lists) != 1 or not 1 <= len(pkg.slides) <= 200:
        fail('Expected one nonempty supported slide list')
    for attr in ('id', q('r', 'id')):
        values = [n.get(attr) for n in slide_lists[0]]
        if None in values or len(values) != len(set(values)):
            fail('Duplicate or missing presentation slide identifiers')
    pkg.guide_roots = roots
    return pkg


def reserved_markers(pkg):
    for part, root in pkg.guide_roots.items():
        for nv in root.iter(q('p', 'cNvPr')):
            text = ' '.join(nv.attrib.values())
            if any(marker in text for marker in
                   ('FIGURE_ALIGNMENT_GUIDES::', 'ALIGNMENT_GUIDE::', 'figure-alignment-guides/')):
                yield part, nv


def simple_tree(root, allow_group=False):
    if root.tag != q('p', 'sld'):
        fail('Selected part is not a standard slide')
    if any(n.tag not in (q('p', 'cSld'), q('p', 'clrMapOvr')) for n in root):
        fail('Slide timing, transitions, extensions, and other complex slide children are unsupported')
    commons = root.findall('p:cSld', NS)
    if len(commons) != 1 or len(root.findall('p:clrMapOvr', NS)) > 1:
        fail('Expected one common slide')
    common = commons[0]
    if any(n.tag not in (q('p', 'bg'), q('p', 'spTree')) for n in common):
        fail('Unsupported common-slide child')
    trees = common.findall('p:spTree', NS)
    if len(trees) != 1:
        fail('Expected one shape tree')
    tree = trees[0]
    if len(tree) < 2 or [n.tag for n in tree[:2]] != [q('p', 'nvGrpSpPr'), q('p', 'grpSpPr')]:
        fail('Shape tree must start with standard nonvisual/group properties')
    allowed = {q('p', s) for s in ('sp', 'pic', 'cxnSp', 'graphicFrame')}
    if allow_group:
        allowed.add(q('p', 'grpSp'))
    if any(n.tag not in allowed for n in tree[2:]):
        fail('Only direct shapes, pictures, connectors, and graphic frames are supported')
    if root.find('.//mc:AlternateContent', NS) is not None:
        fail('AlternateContent is unsupported on the selected slide')
    groups = root.findall('.//p:grpSp', NS)
    if (not allow_group and groups) or (allow_group and len(groups) != 1):
        fail('Source groups or multiple/nested guide groups are unsupported')
    # An ordinary slide has no root transform, or an identity/zero root transform.
    props = tree[1]
    if len(props):
        if len(props) != 1 or props[0].tag != q('a', 'xfrm') or props[0].attrib:
            fail('Unsupported slide-root transform')
        xf = props[0]
        if [n.tag for n in xf] != [q('a', x) for x in ('off', 'ext', 'chOff', 'chExt')]:
            fail('Unsupported slide-root transform children')
        if (dict(xf[0].attrib) != {'x': '0', 'y': '0'} or
                dict(xf[2].attrib) != {'x': '0', 'y': '0'} or
                dict(xf[1].attrib) != dict(xf[3].attrib) or
                set(xf[1].attrib) != {'cx', 'cy'} or
                any(not re.fullmatch(r'[0-9]+', v) for v in xf[1].attrib.values())):
            fail('Nonidentity slide-root transform is unsupported')
    ids, structural_ids = [], []
    for nv in root.iter(q('p', 'cNvPr')):
        value = nv.get('id', '')
        # Cached OLE preview pictures are representations, not slide members.
        # Office commonly repeats ID=0 there. Still reserve every such ID when
        # choosing new guide IDs; do not change or deduplicate preview XML.
        parent = nv.getparent()
        preview = (parent is not None and parent.tag == q('p', 'nvPicPr') and
                   parent.getparent() is not None and parent.getparent().tag == q('p', 'pic') and
                   any(a.tag == q('p', 'oleObj') for a in nv.iterancestors()))
        if not re.fullmatch(r'0|[1-9][0-9]*', value) or int(value) > MAX_ID:
            fail('Invalid source shape ID')
        number = int(value)
        if not preview:
            if number == 0:
                fail('Structural source shape ID must be positive')
            structural_ids.append(number)
        ids.append(number)
    if len(structural_ids) != len(set(structural_ids)):
        fail('Duplicate structural source/candidate shape ID')
    for shape in tree[2:]:
        nv_names = {'sp': 'nvSpPr', 'pic': 'nvPicPr', 'cxnSp': 'nvCxnSpPr',
                    'graphicFrame': 'nvGraphicFramePr', 'grpSp': 'nvGrpSpPr'}
        name = E.QName(shape).localname
        if len(shape.findall('p:' + nv_names[name] + '/p:cNvPr', NS)) != 1:
            fail('Each direct shape must have one stable nonvisual ID')
    if len(tree[0].findall('p:cNvPr', NS)) != 1:
        fail('Root group must have one stable nonvisual ID')
    return tree, set(ids)


def validate_plan(pkg, plan):
    exact_keys(plan, ('schema', 'source_sha256', 'slide', 'unit', 'group_id', 'lines'), 'Plan')
    if plan['schema'] != SCHEMA or plan['unit'] != 'EMU':
        fail('Unsupported plan schema or unit; use integer EMU coordinates')
    if plan['source_sha256'] != pkg.source_hash:
        fail('Stale or mismatched source SHA-256')
    part, root = pkg.slide(plan['slide'])
    tree, used = simple_tree(root)
    if list(reserved_markers(pkg)):
        fail('Source already contains a reserved alignment-guide marker')
    sizes = pkg.presentation.findall('p:sldSz', NS)
    if len(sizes) != 1:
        fail('Expected explicit slide dimensions')
    width, height = (int(sizes[0].get(k, '0')) for k in ('cx', 'cy'))
    for v in (width, height):
        integer(v, 1, 51206400, 'Slide dimension')
    all_ids = [integer(plan['group_id'], 1, MAX_ID, 'Group ID')]
    lines = plan['lines']
    if not isinstance(lines, list) or not 1 <= len(lines) <= 100:
        fail('Provide 1–100 explicit guide lines')
    keys = set()
    for line in lines:
        exact_keys(line, ('id', 'key', 'x1', 'y1', 'x2', 'y2'), 'Guide line')
        all_ids.append(integer(line['id'], 1, MAX_ID, 'Line ID'))
        key = line['key']
        if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,48}', key) or key in keys:
            fail('Guide keys must be distinct stable ASCII identifiers')
        keys.add(key)
        x1, x2 = (integer(line[k], 0, width, k) for k in ('x1', 'x2'))
        y1, y2 = (integer(line[k], 0, height, k) for k in ('y1', 'y2'))
        if not ((x1 < x2 and y1 == y2) or (y1 < y2 and x1 == x2)):
            fail('Guides must be nonzero horizontal/vertical lines with ascending endpoints')
    if len(all_ids) != len(set(all_ids)) or used.intersection(all_ids):
        fail('Guide IDs are duplicated or conflict with source shape IDs')
    return part, root, tree, width, height


def sub(parent, prefix, local_name, **attrs):
    return E.SubElement(parent, q(prefix, local_name), **{k: str(v) for k, v in attrs.items()})


def make_group(plan, width, height):
    group = E.Element(q('p', 'grpSp'))
    nv = sub(group, 'p', 'nvGrpSpPr')
    # Keep file/plan hashes in the external plan/report, not the deliverable.
    meta = {'schema': SCHEMA, 'group_id': plan['group_id']}
    sub(nv, 'p', 'cNvPr', id=plan['group_id'], name=GROUP_NAME,
        descr=json.dumps(meta, sort_keys=True, separators=(',', ':')))
    sub(nv, 'p', 'cNvGrpSpPr'); sub(nv, 'p', 'nvPr')
    xf = sub(sub(group, 'p', 'grpSpPr'), 'a', 'xfrm')
    for name, attrs in [('off', {'x': 0, 'y': 0}), ('ext', {'cx': width, 'cy': height}),
                        ('chOff', {'x': 0, 'y': 0}), ('chExt', {'cx': width, 'cy': height})]:
        sub(xf, 'a', name, **attrs)
    for line in plan['lines']:
        shape = sub(group, 'p', 'sp'); nv = sub(shape, 'p', 'nvSpPr')
        sub(nv, 'p', 'cNvPr', id=line['id'], name=LINE_PREFIX + line['key'],
            descr=SCHEMA + ': alignment reference only; not scientific data')
        sub(nv, 'p', 'cNvSpPr'); sub(nv, 'p', 'nvPr')
        props = sub(shape, 'p', 'spPr'); xf = sub(props, 'a', 'xfrm')
        sub(xf, 'a', 'off', x=line['x1'], y=line['y1'])
        sub(xf, 'a', 'ext', cx=line['x2'] - line['x1'], cy=line['y2'] - line['y1'])
        sub(sub(props, 'a', 'prstGeom', prst='line'), 'a', 'avLst')
        sub(props, 'a', 'noFill')
        stroke = sub(props, 'a', 'ln', w=6350, cap='flat')
        color = sub(sub(stroke, 'a', 'solidFill'), 'a', 'srgbClr', val='D000D0')
        sub(color, 'a', 'alpha', val=65000)
        sub(stroke, 'a', 'prstDash', val='dash')
        sub(stroke, 'a', 'headEnd', type='none'); sub(stroke, 'a', 'tailEnd', type='none')
    return group


def verify_loaded(source, candidate, plan):
    part, original, _, width, height = validate_plan(source, plan)
    if set(source.parts) != set(candidate.parts) or source.comment != candidate.comment:
        fail('Candidate added/removed package parts or changed ZIP comment')
    changed = [p for p in source.parts if source.parts[p] != candidate.parts[p]]
    if changed != [part]:
        fail('Candidate must change only the selected slide XML part')
    cpart, root = candidate.slide(plan['slide'])
    if cpart != part:
        fail('Candidate changed actual slide mapping')
    tree, _ = simple_tree(root, allow_group=True)
    if len(tree) < 3 or tree[2].tag != q('p', 'grpSp'):
        fail('Guide group must be behind every source shape')
    group = tree[2]
    expected = make_group(plan, width, height)
    # Compare within identical namespace context, including all geometry/style/IDs.
    reference = copy.deepcopy(original)
    reference.find('p:cSld/p:spTree', NS).insert(2, expected)
    if group.tail is not None or canonical(group) != canonical(expected):
        fail('Guide group, membership, markers, geometry, or line styling changed')
    markers = list(reserved_markers(candidate))
    if len(markers) != 1 + len(plan['lines']) or any(p != part for p, _ in markers):
        fail('Guide markers must occur only in the one expected guide group')
    if canonical(root) != canonical(reference):
        fail('Candidate slide contains changes beyond the exact planned guide group')
    tree.remove(group)
    if canonical(root) != canonical(original):
        fail('Source slide content changed after removal of the guide group')
    if (pp.digest(source.path.read_bytes()) != source.source_hash or
            pp.digest(candidate.path.read_bytes()) != candidate.source_hash):
        fail('Source or candidate changed during verification')
    return {'schema': SCHEMA, 'source_sha256': source.source_hash,
            'guided_sha256': candidate.source_hash, 'slide': plan['slide'], 'slide_part': part,
            'guide_group_count': 1, 'guide_line_count': len(plan['lines']),
            'source_slide_xml_equivalent_after_group_removal': True,
            'other_parts_and_embedded_payloads_byte_identical': True,
            'powerpoint_reopen_verified': False, 'origin_reopen_verified': False}


def add(source, plan, output):
    pkg = load_package(source)
    pp.output_path(pkg.path, output)
    part, root, tree, width, height = validate_plan(pkg, plan)
    tree.insert(2, make_group(plan, width, height))
    out = pp.save_package(pkg, {part: pp.serialize(root)}, {}, output)
    result = verify_loaded(pkg, load_package(out), plan)
    result['output'] = str(out)
    return result


def verify(source, plan, guided):
    return verify_loaded(load_package(source), load_package(guided), plan)


def restore(source, plan, guided, output):
    """Verify the candidate, then publish original ZIP bytes; never reconstruct it."""
    a, b = load_package(source), load_package(guided)
    result = verify_loaded(a, b, plan)
    out = pp.output_path(a.path, output)
    data = a.path.read_bytes()
    if pp.digest(data) != a.source_hash or pp.digest(b.path.read_bytes()) != b.source_hash:
        fail('Source or candidate changed during restore')
    fd, temporary = tempfile.mkstemp(prefix='.alignment-restore-', dir=out.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        if pp.digest(a.path.read_bytes()) != a.source_hash or pp.digest(b.path.read_bytes()) != b.source_hash:
            fail('Source or candidate changed before restore publication')
        os.link(temporary, out)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    result.update(output=str(out), restored_sha256=pp.digest(out.read_bytes()),
                  exact_original_file_bytes_restored=True)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for command in ('add', 'verify', 'restore'):
        item = commands.add_parser(command)
        item.add_argument('--source', required=True, help='Unmodified clean .pptx')
        item.add_argument('--plan', required=True, help='Explicit approved-coordinate JSON plan')
        if command in ('verify', 'restore'):
            item.add_argument('--guided', required=True)
        if command in ('add', 'restore'):
            item.add_argument('--output', required=True, help='New .pptx path, never overwritten')
    args = parser.parse_args(argv)
    try:
        plan = read_plan(args.plan)
        if args.command == 'add':
            result = add(args.source, plan, args.output)
        elif args.command == 'verify':
            result = verify(args.source, plan, args.guided)
        else:
            result = restore(args.source, plan, args.guided, args.output)
    except (ValueError, OSError, TypeError, KeyError, E.XMLSyntaxError, zipfile.BadZipFile) as exc:
        parser.exit(2, 'alignment_guides: ' + str(exc) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
