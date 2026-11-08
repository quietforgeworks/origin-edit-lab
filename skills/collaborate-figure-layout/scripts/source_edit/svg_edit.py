#!/usr/bin/env python3
"""Conservative SVG appearance editor. Does not edit embedded Origin data."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

from lxml import etree

MAX_BYTES = 25 * 1024 * 1024
SVG = 'http://www.w3.org/2000/svg'
ALLOWED = {'fill', 'stroke', 'stroke-width', 'stroke-dasharray', 'opacity',
           'fill-opacity', 'stroke-opacity', 'font-size', 'font-family',
           'font-weight', 'font-style', 'text-anchor'}
FORBIDDEN = {'script', 'foreignObject', 'animate', 'animateMotion',
             'animateTransform', 'set'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def local_name(node):
    return etree.QName(node).localname if isinstance(node.tag, str) else '#comment'


def load_svg(path):
    data = Path(path).read_bytes()
    if len(data) > MAX_BYTES:
        raise ValueError('SVG exceeds 25 MiB limit')
    if re.search(br'<!\s*(?:DOCTYPE|ENTITY)', data, re.I):
        raise ValueError('DTD/entities are not allowed')
    if re.search(br'<\?xml-stylesheet\b', data, re.I):
        raise ValueError('External XML stylesheets are not allowed')
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True,
                             remove_blank_text=False, strip_cdata=False)
    root = etree.fromstring(data, parser)
    tree = root.getroottree()
    if tree.docinfo.doctype or any(isinstance(n, etree._Entity) for n in root.iter()):
        raise ValueError('DTD/entities are not allowed')
    if tree.xpath('//processing-instruction("xml-stylesheet")'):
        raise ValueError('External XML stylesheets are not allowed')
    if root.tag != '{' + SVG + '}svg':
        raise ValueError('Expected an SVG namespace root')
    for node in root.iter():
        if not isinstance(node.tag, str):
            continue
        if local_name(node) in FORBIDDEN:
            raise ValueError('Active SVG content is not allowed')
        for key, value in node.attrib.items():
            name = etree.QName(key).localname
            if key == '{http://www.w3.org/XML/1998/namespace}base':
                raise ValueError('xml:base resource redirection is not supported')
            if name.lower().startswith('on'):
                raise ValueError('SVG event handlers are not allowed')
            if name == 'style' and ('\\' in value or '@import' in value.lower()):
                raise ValueError('Escaped or imported CSS is not supported')
            if name == 'href' and not value.startswith('#'):
                raise ValueError('External or embedded image references are not supported')
            if re.search(r'url\s*\(\s*["\']?\s*(?!#)', value, re.I):
                # Match URL tokens explicitly; a lookahead alone can backtrack whitespace.
                for match in re.finditer(r'url\s*\((.*?)\)', value, re.I):
                    target = match.group(1).strip().strip('"\'')
                    if not target.startswith('#'):
                        raise ValueError('External SVG resource URL is not allowed')
        if local_name(node) == 'style' and node.text:
            if re.search(r'@import|!important|url\s*\(|\\', node.text, re.I):
                raise ValueError('Stylesheet imports, resources or important rules are not supported')
    return data, root


def node_path(node):
    path = []
    while node.getparent() is not None:
        parent = node.getparent()
        path.append(parent.index(node))
        node = parent
    return list(reversed(path))


def inspect_svg(path):
    data, root = load_svg(path)
    items = []
    for node in root.iter():
        if not isinstance(node.tag, str):
            continue
        if local_name(node) not in {'text', 'tspan', 'path', 'line', 'polyline', 'polygon', 'rect', 'circle', 'ellipse', 'g', 'use'}:
            continue
        items.append({'id': node.get('id'), 'path': node_path(node),
                      'tag': local_name(node), 'text': ''.join(node.itertext()) if local_name(node) in {'text', 'tspan'} else None,
                      'attributes': {k: v for k, v in node.attrib.items()
                                     if etree.QName(k).localname in ALLOWED | {'style'}}})
    return {'sha256': digest(data), 'width': root.get('width'), 'height': root.get('height'),
            'viewBox': root.get('viewBox'), 'elements': items,
            'origin_payload_modified': False,
            'note': 'Text converted to outlines cannot be edited as text.'}


def resolve(root, selector):
    if not isinstance(selector, dict) or len(selector) != 1:
        raise ValueError('Selector must contain exactly id or path')
    if 'id' in selector:
        value = selector['id']
        matches = [n for n in root.iter() if isinstance(n.tag, str) and n.get('id') == value]
        if len(matches) != 1:
            raise ValueError('Element id must resolve uniquely')
        return matches[0]
    if 'path' in selector and isinstance(selector['path'], list):
        node = root
        for i in selector['path']:
            if type(i) is not int or i < 0 or i >= len(node):
                raise ValueError('Invalid element path')
            node = node[i]
        if not isinstance(node.tag, str):
            raise ValueError('Cannot edit a comment')
        return node
    raise ValueError('Unknown selector')


def validate_property(name, value):
    if name not in ALLOWED or not isinstance(value, str):
        raise ValueError('Unsupported property or non-string value')
    value = value.strip()
    if not value or any(c in value for c in ';{}<>\n\r') or re.search(r'url\s*\(|!important', value, re.I):
        raise ValueError('Unsafe or empty property value')
    if name in {'fill', 'stroke'}:
        names = {'none', 'black', 'white', 'red', 'green', 'blue', 'cyan',
                 'magenta', 'yellow', 'gray', 'grey', 'orange', 'purple',
                 'transparent', 'currentcolor'}
        if not re.fullmatch(r'#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})', value) and value.lower() not in names:
            raise ValueError('Use a named color or hexadecimal color')
    elif name in {'opacity', 'fill-opacity', 'stroke-opacity'}:
        n = float(value)
        if not math.isfinite(n) or not 0 <= n <= 1:
            raise ValueError('Opacity must be between 0 and 1')
    elif name in {'font-size', 'stroke-width'}:
        if not re.fullmatch(r'(?:\d+(?:\.\d*)?|\.\d+)(?:px|pt)?', value):
            raise ValueError('Use a non-negative numeric px/pt value')
        if float(re.sub(r'(px|pt)$', '', value)) > 1000:
            raise ValueError('Size exceeds supported range')
    elif name == 'stroke-dasharray':
        if value != 'none' and not re.fullmatch(r'\d+(?:\.\d+)?(?:[ ,]+\d+(?:\.\d+)?)*', value):
            raise ValueError('Invalid dash array')
    elif name == 'font-family':
        if not re.fullmatch(r'[\w\s,\-"\']+', value, flags=re.UNICODE):
            raise ValueError('Invalid font family')
    elif name == 'font-weight':
        if value not in {'normal','bold','bolder','lighter',*[str(i) for i in range(100,1000,100)]}:
            raise ValueError('Invalid font weight')
    elif name == 'font-style' and value not in {'normal','italic','oblique'}:
        raise ValueError('Invalid font style')
    elif name == 'text-anchor' and value not in {'start','middle','end'}:
        raise ValueError('Invalid text anchor')
    return value


def set_style(node, properties):
    original = node.get('style', '')
    if '!important' in original.lower():
        raise ValueError('Inline !important styles require manual inspection')
    # Preserve unrelated declarations. Requested properties receive inline precedence.
    declarations = []
    for piece in original.split(';'):
        if not piece.strip():
            continue
        if ':' not in piece:
            raise ValueError('Malformed inline style')
        key = piece.split(':', 1)[0].strip().lower()
        if key not in properties:
            declarations.append(piece.strip())
    declarations.extend(f'{k}:{v}' for k, v in properties.items())
    node.set('style', ';'.join(declarations))


def patch_svg(source, output, plan):
    source = Path(source).resolve(strict=True)
    raw_output = Path(output).absolute()
    if raw_output.is_symlink() or raw_output.exists() or raw_output.resolve() == source:
        raise ValueError('Refusing existing output, symlink or source overwrite')
    output = raw_output.resolve()
    if not output.parent.is_dir() or output.suffix.lower() != '.svg':
        raise ValueError('Output must be a new .svg in an existing directory')
    data, root = load_svg(source)
    if not isinstance(plan, dict) or set(plan) != {'source_sha256', 'edits'}:
        raise ValueError('Plan requires source_sha256 and edits only')
    if plan['source_sha256'] != digest(data):
        raise ValueError('Source SHA-256 does not match inspected input')
    if not isinstance(plan['edits'], list) or not plan['edits']:
        raise ValueError('At least one explicit edit is required')
    targets = set()
    changes = []
    for edit in plan['edits']:
        if not isinstance(edit, dict) or set(edit) - {'selector', 'set', 'text', 'expected_text'}:
            raise ValueError('Invalid edit schema')
        node = resolve(root, edit.get('selector'))
        identity = tuple(node_path(node))
        if identity in targets:
            raise ValueError('Merge edits targeting the same element')
        targets.add(identity)
        if 'set' not in edit and 'text' not in edit:
            raise ValueError('An edit must change properties or text')
        if 'set' in edit:
            if not isinstance(edit['set'], dict) or not edit['set']:
                raise ValueError('Properties must be a nonempty object')
            properties = {k: validate_property(k, v) for k, v in edit['set'].items()}
            set_style(node, properties)
        if 'text' in edit:
            if local_name(node) not in {'text','tspan'} or len(node):
                raise ValueError('Text edits require a leaf text/tspan, not outlines or mixed content')
            if 'expected_text' not in edit or (node.text or '') != edit['expected_text']:
                raise ValueError('Expected old text does not match')
            if not isinstance(edit['text'], str) or len(edit['text']) > 10000:
                raise ValueError('Invalid replacement text')
            node.text = edit['text']
        changes.append({'path': list(identity), 'id': node.get('id'), 'properties': list(edit.get('set',{})),
                        'text_changed': 'text' in edit})
    result = etree.tostring(root.getroottree(), encoding='utf-8', xml_declaration=True)
    if digest(source.read_bytes()) != digest(data):
        raise ValueError('Source changed during editing; no output written')
    with output.open('xb') as stream:
        stream.write(result)
    # Reparse and security-check the saved document; does not certify rendering.
    load_svg(output)
    return {'source_sha256': digest(data), 'output_sha256': digest(result),
            'changes': changes, 'source_unchanged': True,
            'origin_payload_modified': False, 'rendering_verified': False,
            'note': 'Only SVG appearance changed; review a rendered preview before PPT replacement.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    i = sub.add_parser('inspect');i.add_argument('source',type=Path)
    e = sub.add_parser('edit');e.add_argument('source',type=Path);e.add_argument('output',type=Path);e.add_argument('--plan',required=True,type=Path)
    a = p.parse_args()
    try:
        result = inspect_svg(a.source) if a.action == 'inspect' else patch_svg(a.source,a.output,json.loads(a.plan.read_text(encoding='utf-8')))
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except Exception as error:
        print(json.dumps({'status':'blocked_or_failed','error':str(error)},ensure_ascii=False),file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
