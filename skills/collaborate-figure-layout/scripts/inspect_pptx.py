#!/usr/bin/env python3
"""Read-only bounded inventory of scientific-PPT source objects; no source mutation."""
import argparse
import hashlib
import io
import json
import math
import posixpath
import re
import struct
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

SCHEMA = 'figure-layout-inventory/v1'
MAX_FILE = 250 * 1024 * 1024
MAX_ENTRY = 30 * 1024 * 1024
NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
      'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006'}
R = '{' + NS['r'] + '}'
P = '{' + NS['p'] + '}'
MC = '{' + NS['mc'] + '}'
SHAPE_PROPERTIES = {P + tag: 'p:' + props + '/p:cNvPr' for tag, props in (
    ('pic', 'nvPicPr'), ('sp', 'nvSpPr'), ('grpSp', 'nvGrpSpPr'),
    ('graphicFrame', 'nvGraphicFramePr'), ('cxnSp', 'nvCxnSpPr'))}


def xml_paths(root):
    """Namespace-qualified, sibling-indexed paths bind repeated IDs unambiguously."""
    def qname(tag):
        for prefix, uri in NS.items():
            if tag.startswith('{' + uri + '}'):
                return prefix + ':' + local(tag)
        return tag
    result = {}
    def visit(node, path):
        result[node] = path
        counts = {}
        for child in node:
            counts[child.tag] = counts.get(child.tag, 0) + 1
            visit(child, path + '/' + qname(child.tag) + '[' + str(counts[child.tag]) + ']')
    visit(root, '/' + qname(root.tag) + '[1]')
    return result


def own_identity(obj):
    query = SHAPE_PROPERTIES.get(obj.tag)
    return obj.find(query, NS) if query else None


def structural_members(obj, paths, unsupported):
    """Follow only slide/group membership edges, never graphic/OLE payload edges.

    Choice/Fallback members remain separate, branch-qualified candidates. They
    are not asserted to coexist, correspond, or form one scientific panel.
    """
    members = []
    def visit(node, parent_path=None, branches=()):
        if node.tag in SHAPE_PROPERTIES:
            identity = own_identity(node)
            if identity is None or not identity.get('id'):
                raise ValueError('Object without stable shape ID at ' + paths[node])
            members.append((node, {'shapeId': identity.get('id'),
                'shapeName': identity.get('name', local(node.tag)), 'shapeType': local(node.tag),
                'xmlPath': paths[node], 'parentGroupXmlPath': parent_path,
                'compatibilityBranchPaths': list(branches)}))
            if node.tag != P + 'grpSp':
                return
            parent_path = paths[node]
        elif node.tag == MC + 'AlternateContent':
            for branch in node:
                if branch.tag in (MC + 'Choice', MC + 'Fallback'):
                    for child in branch:
                        visit(child, parent_path, branches + (paths[branch],))
                else:
                    unsupported.append(paths[branch])
            return
        else:
            if node.tag not in (P + 'nvGrpSpPr', P + 'grpSpPr', P + 'extLst'):
                unsupported.append(paths[node])
            return
        for child in node:
            visit(child, parent_path, branches)
    visit(obj)
    return members


def own_transform(obj):
    query = 'p:xfrm' if obj.tag == P + 'graphicFrame' else 'p:grpSpPr/a:xfrm' if obj.tag == P + 'grpSp' else 'p:spPr/a:xfrm'
    return obj.find(query, NS)


def sha(data):
    return hashlib.sha256(data).hexdigest()

def local(tag):
    return tag.rsplit('}', 1)[-1]

def xml(data):
    if data is None:
        return None
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('DTD/entity declarations are not supported')
    return ET.fromstring(data)

def relative(base, target):
    if '\\' in target or '?' in target or '#' in target:
        raise ValueError('Unsupported package relationship path')
    target = posixpath.normpath(target.lstrip('/') if target.startswith('/') else posixpath.join(posixpath.dirname(base), target))
    if target == '..' or target.startswith('../'):
        raise ValueError('Package relationship escapes container')
    return target

def relationships(z, base):
    name = posixpath.join(posixpath.dirname(base), '_rels', posixpath.basename(base) + '.rels')
    if name not in z.namelist():
        return {}
    result = {}
    for e in xml(z.read(name)):
        ident = e.get('Id')
        if ident in result:
            raise ValueError('Duplicate relationship ID')
        external = e.get('TargetMode') == 'External'
        result[ident] = {'target': None if external else relative(base, e.get('Target', '')),
                         'external': external, 'type': e.get('Type')}
    return result

def first(root, name):
    return next((e for e in root.iter() if local(e.tag) == name), None)

def number(value):
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    return n if math.isfinite(n) else None

def bounds(root):
    xfrm = own_transform(root)
    if xfrm is None:
        return None
    off = next((e for e in xfrm if local(e.tag) == 'off'), None)
    ext = next((e for e in xfrm if local(e.tag) == 'ext'), None)
    if off is None or ext is None:
        return None
    values = [number(off.get('x')), number(off.get('y')), number(ext.get('cx')), number(ext.get('cy'))]
    if any(v is None for v in values):
        return None
    return dict(zip(('x', 'y', 'w', 'h'), [v / 36000 for v in values]), unit='mm')

def image_info(data):
    if data.startswith(b'\x89PNG\r\n\x1a\n') and len(data) >= 24:
        width, height = struct.unpack('>II', data[16:24])
        return 'image/png', width, height
    if data.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg', 0, 0
    return None, 0, 0

def extract(path):
    if path.stat().st_size > MAX_FILE:
        raise ValueError('PPTX exceeds 250 MiB limit')
    raw = path.read_bytes()
    file_hash = sha(raw)
    warnings = []
    assets = []
    candidate_inventory_complete = True
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        if len(infos) > 10000 or len(set(names)) != len(names):
            raise ValueError('Too many or duplicate package entries')
        if sum(i.file_size for i in infos) > MAX_FILE or any(i.file_size > MAX_ENTRY or i.flag_bits & 1 for i in infos):
            raise ValueError('Encrypted or oversized package entry')
        for name in names:
            if name.startswith('/') or '\\' in name or '..' in name.split('/'):
                raise ValueError('Unsafe package entry path')
        if 'ppt/presentation.xml' not in names:
            raise ValueError('Missing presentation.xml')
        pres = xml(z.read('ppt/presentation.xml'))
        pres_rels = relationships(z, 'ppt/presentation.xml')
        slide_ids = pres.find('p:sldIdLst', NS)
        slide_parts = []
        if slide_ids is None:
            raise ValueError('Missing slide order')
        for sid in slide_ids:
            rel = pres_rels.get(sid.get(R + 'id'))
            if not rel or rel['external'] or rel['target'] not in names:
                raise ValueError('Unresolved presentation slide relationship')
            slide_parts.append(rel['target'])
        size = pres.find('p:sldSz', NS)
        original_canvas = {'width': number(size.get('cx')) / 36000, 'height': number(size.get('cy')) / 36000, 'unit': 'mm'} if size is not None else None
        for number_in_deck, slide in enumerate(slide_parts, 1):
            slide_root = xml(z.read(slide))
            paths = xml_paths(slide_root)
            tree = slide_root.find('p:cSld/p:spTree', NS)
            if tree is None:
                candidate_inventory_complete = False
                warnings.append('Missing slide shape tree: ' + slide)
                continue
            rels = relationships(z, slide)
            for obj in tree:
                typ = local(obj.tag)
                if obj.tag not in SHAPE_PROPERTIES and obj.tag != MC + 'AlternateContent':
                    if obj.tag not in (P + 'nvGrpSpPr', P + 'grpSpPr', P + 'extLst'):
                        candidate_inventory_complete = False
                        warnings.append('Unsupported top-level element: ' + paths[obj])
                    continue
                unsupported = []
                members = structural_members(obj, paths, unsupported)
                if unsupported:
                    candidate_inventory_complete = False
                    warnings.extend('Unsupported structural member: ' + path for path in unsupported)
                c = own_identity(obj)
                ident, name = (c.get('id'), c.get('name', typ)) if c is not None else (None, typ)
                composite = typ in ('grpSp', 'AlternateContent')
                ole_nodes = [e for e in obj.iter(P + 'oleObj')] if not composite else []
                # Scalar OLE binding is safe only when all compatibility branches agree.
                ole_signatures = {(e.get(R + 'id'), e.get('progId')) for e in ole_nodes}
                ole = ole_nodes[0] if len(ole_signatures) == 1 else None
                chart = first(obj, 'chart') if not composite else None
                kind = 'pptx-group' if typ == 'grpSp' else 'pptx-alternate-content' if typ == 'AlternateContent' else 'pptx-ole' if ole_nodes else 'pptx-chart' if chart is not None else 'pptx-picture' if typ == 'pic' else 'pptx-native'
                text = ' '.join(e.text or '' for e in obj.iter() if local(e.tag) == 't')[:200]
                member_ids = list(dict.fromkeys(m['shapeId'] for _, m in members if not m['compatibilityBranchPaths']))
                branches = [{'xmlPath': paths[e], 'type': local(e.tag), 'requires': e.get('Requires')}
                            for e in obj.iter() if e.tag in (MC + 'Choice', MC + 'Fallback')]
                nested_previews, ole_bindings = [], []
                for member, binding in members:
                    if member.tag != P + 'graphicFrame':
                        continue
                    for embedded_ole in member.iter(P + 'oleObj'):
                        rid = embedded_ole.get(R + 'id')
                        rel = rels.get(rid)
                        part = rel['target'] if rel and not rel['external'] and rel['target'] in names else None
                        ole_binding = {'hostShapeId': binding['shapeId'], 'hostXmlPath': paths[member],
                            'xmlPath': paths[embedded_ole], 'relationshipId': rid,
                            'progId': embedded_ole.get('progId'), 'embeddedPart': part,
                            'embeddedHash': sha(z.read(part)) if part else None}
                        ole_bindings.append(ole_binding)
                        for cached in embedded_ole.iter(P + 'pic'):
                            cached_identity = own_identity(cached)
                            nested_previews.append({'shapeId': cached_identity.get('id') if cached_identity is not None else None,
                                'xmlPath': paths[cached], 'hostShapeId': binding['shapeId'],
                                'hostXmlPath': paths[member], 'oleXmlPath': paths[embedded_ole],
                                'oleRelationshipId': rid, 'role': 'ole-cached-preview',
                                'relationshipIds': list(dict.fromkeys(v for e in cached.iter() for k, v in e.attrib.items() if k.startswith(R)))})
                links = []
                for e in obj.iter():
                    for key, value in e.attrib.items():
                        if key.startswith(R) or local(key) == 'relid':
                            rel = rels.get(value)
                            if rel and not rel['external'] and rel['target'] in names:
                                part = rel['target']
                                entry = {'relationshipId': value, 'part': part, 'sha256': sha(z.read(part)), 'type': rel['type']}
                                match = next((link for link in links if link['relationshipId'] == value), None)
                                if match is None:
                                    match = dict(entry, references=[])
                                    links.append(match)
                                match['references'].append({'xmlPath': paths[e], 'attribute': key})
                preview, preview_part, preview_hash, iw, ih = None, None, None, 0, 0
                if typ not in ('grpSp', 'AlternateContent'):
                    for link in links:
                        if not (link['type'] or '').endswith('/image'):
                            continue
                        data = z.read(link['part'])
                        mime, width, height = image_info(data)
                        if mime:
                            preview = True
                            preview_part, preview_hash, iw, ih = link['part'], link['sha256'], width, height
                            break
                embedded, embedded_hash = None, None
                if ole is not None:
                    rel = rels.get(ole.get(R + 'id'))
                    if rel and not rel['external'] and rel['target'] in names:
                        embedded, embedded_hash = rel['target'], sha(z.read(rel['target']))
                xfrm = own_transform(obj)
                source = {'kind': kind, 'fileName': path.name, 'fileHash': file_hash, 'slidePart': slide,
                          'slideNumber': number_in_deck, 'shapeId': ident, 'shapeName': name, 'shapeType': typ,
                          'bounds': bounds(obj), 'previewPart': preview_part, 'previewHash': preview_hash,
                          'embeddedPart': embedded, 'embeddedHash': embedded_hash,
                          'editableOriginalPreserved': True, 'representation': 'embedded-raster-preview' if preview else 'placeholder',
                          'xmlPath': paths[obj], 'memberShapeIds': member_ids,
                          'memberShapeIdsScope': 'unconditional-structural-members-only',
                          'structuralMembers': [m for _, m in members], 'compatibilityBranches': branches,
                          'compatibilityBranchSelection': 'unresolved' if branches else 'not-applicable',
                          'nestedPreviewShapes': nested_previews, 'oleBindings': ole_bindings, 'relationships': links,
                          'progId': ole.get('progId') if ole is not None else None,
                          'transformAttributes': dict(xfrm.attrib) if xfrm is not None else {},
                          'semanticGrouping': 'unreviewed',
                          'previewWarning': 'Composite preview required; do not represent the whole group with one descendant image.' if typ in ('grpSp', 'AlternateContent') else None}
                asset_ident = ident if ident is not None else 'alternate'
                assets.append({'id': f'pptx-{file_hash[:12]}-{number_in_deck}-{asset_ident}-{len(assets)}', 'name': f'S{number_in_deck} · {name}',
                               'note': text, 'category': 'unknown', 'priority': 'normal', 'preview': preview, 'width': iw, 'height': ih, 'source': source})
        warnings.append('Top-level objects are candidates, not classified scientific panels. Inspect group membership, native text and connector endpoints.')
        warnings.append('Candidate inventory only: scientific grouping, internal OLE stream inspection and visual/connector anchor measurements are incomplete.')
        if any(a['source']['compatibilityBranches'] for a in assets):
            warnings.append('Compatibility branches are recorded separately without choosing an active branch or equating alternative shape IDs; memberShapeIds includes unconditional structural members only.')
        if any(a['preview'] is None for a in assets):
            warnings.append('Some objects have no supported cached preview. Inspect a full-slide render and detail crops; do not infer their appearance from placeholders.')
        if any(a['source']['kind'] == 'pptx-ole' for a in assets):
            warnings.append('OLE does not automatically mean Origin. Check progId and payload type; no embedded object was executed.')
    project = {'schema': SCHEMA, 'source': {'fileName': path.name, 'fileHash': file_hash, 'slideCount': len(slide_parts), 'canvas': original_canvas, 'xmlPathNamespaces': NS},
               'assets': [{k: v for k, v in asset.items() if k not in ('preview', 'width', 'height')} for asset in assets]}
    report = {'source_sha256': file_hash, 'slide_count': len(slide_parts), 'candidate_count': len(assets), 'candidate_inventory_complete': candidate_inventory_complete,
              'candidate_inventory_scope': 'supported top-level slide objects and structural group/compatibility members; not a scientific object inventory',
              'scientific_segmentation_complete': False, 'scientific_grouping_complete': False,
              'internal_ole_stream_inspection_complete': False, 'anchor_measurements_complete': False, 'original_canvas': original_canvas, 'warnings': warnings}
    return project, report

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('pptx', type=Path)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        p.error('Output already exists; choose a new path')
    try:
        project, report = extract(args.pptx)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as out:
            json.dump(project, out, ensure_ascii=False, indent=2, allow_nan=False)
            out.write('\n')
        print(json.dumps(report, ensure_ascii=False, indent=2))
    except (ValueError, OSError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
