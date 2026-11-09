"""Strict, source-bound edits of root-level native PowerPoint text shapes.

No Office automation, embedded-object access, or text replacement. See references/native-ppt-text.md.
"""
import argparse
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import posixpath
import re
import zipfile
from lxml import etree as E

NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
MAX_BYTES = 256 * 1024 * 1024
SPACING = {'line_pt': 'lnSpc', 'before_pt': 'spcBef', 'after_pt': 'spcAft'}

def check_spacing_order(props):
    last=-1;other=False
    for node in props if props is not None else []:
        tag=E.QName(node).localname
        if tag in SPACING.values():
            rank=list(SPACING.values()).index(tag)
            if other or rank<=last:fail('Invalid paragraph spacing child order')
            last=rank
        else:other=True

def spacing_xml(props):
    return {tag: E.tostring(props.find('a:'+tag, NS), method='c14n').decode() if props is not None and props.find('a:'+tag, NS) is not None else None for tag in SPACING.values()}

MAX_DELTA = 9144000  # ten inches, in integer EMU


def fail(message):
    raise ValueError(message)


def keys(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or not set(required) <= set(value):
        fail('Missing or unknown plan fields')


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        fail('Expected bounded integer')
    return value


def xml(data):
    parser = E.XMLParser(resolve_entities=False, no_network=True, remove_blank_text=False)
    root = E.fromstring(data, parser)
    if root.getroottree().docinfo.doctype or any(isinstance(x, E._Entity) for x in root.iter()):
        fail('DTD/entities not supported')
    return root


def package(data):
    if len(data) > MAX_BYTES:
        fail('Package too large')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        infos = z.infolist()
        names = [x.filename for x in infos]
        if len(names) != len(set(names)) or sum(x.file_size for x in infos) > MAX_BYTES:
            fail('Duplicate members or expanded size limit exceeded')
        if any(n.startswith('/') or '\\' in n or '..' in n.split('/') for n in names):
            fail('Unsafe package path')
        if any(n.startswith('_xmlsignatures/') for n in names):
            fail('Signed packages not supported')
        return {n: z.read(n) for n in names}, infos, z.comment


def slides(parts):
    presentation = xml(parts['ppt/presentation.xml'])
    relationships = xml(parts['ppt/_rels/presentation.xml.rels'])
    rels = {}
    for rel in relationships:
        rid = rel.get('Id')
        if rid in rels:
            fail('Duplicate relationship ID')
        rels[rid] = rel
    result = []
    for sid in presentation.findall('p:sldIdLst/p:sldId', NS):
        rel = rels.get(sid.get('{%s}id' % NS['r']))
        if rel is None or rel.get('TargetMode', 'Internal') != 'Internal' or rel.get('Type') != NS['r'] + '/slide':
            fail('Invalid slide relationship')
        target = rel.get('Target', '')
        if '\\' in target or ':' in target or '?' in target or '#' in target:
            fail('Unsupported slide target')
        name = posixpath.normpath(target.lstrip('/') if target.startswith('/') else 'ppt/' + target)
        if not name.startswith('ppt/slides/') or not name.endswith('.xml') or name not in parts:
            fail('Invalid slide target')
        result.append(name)
    if len(result) != len(set(result)):
        fail('Duplicate displayed slide target')
    return result


def resolve(parts, plan):
    keys(plan, ('version', 'source_sha256', 'operations'))
    if type(plan['version']) is not int or plan['version'] != 1 or not isinstance(plan['operations'], list) or not 1 <= len(plan['operations']) <= 1000:
        fail('Invalid plan version or operation count')
    order = slides(parts)
    roots, changes, seen = {}, [], set()
    for op in plan['operations']:
        if not isinstance(op, dict):
            fail('Operation must be an object')
        base = ('op', 'slide', 'shape_id', 'old_text')
        if op.get('op') == 'font':
            keys(op, base + ('run', 'old_run_text'), ('size_pt', 'fonts', 'tracking_pt', 'kerning_min_pt', 'old_character_spacing'))
            if not {'size_pt','fonts','tracking_pt','kerning_min_pt'}.intersection(op):
                fail('Empty font operation')
        elif op.get('op') == 'paragraph_spacing':
            keys(op, base + ('paragraph', 'old_spacing_xml'), tuple(SPACING))
            if not set(SPACING).intersection(op):fail('Empty spacing operation')
        elif op.get('op') == 'translate':
            keys(op, base + ('old_xfrm', 'dx_emu', 'dy_emu'))
        else:
            fail('Unknown operation')
        name = order[integer(op['slide'], 1, len(order)) - 1]
        if name not in roots:roots[name]=xml(parts[name])
        root = roots[name]
        sid = op['shape_id']
        if not isinstance(sid, str) or not re.fullmatch(r'[1-9][0-9]*', sid):
            fail('Shape ID must be a decimal string')
        matches = root.xpath('.//p:cNvPr[@id=$sid]', namespaces=NS, sid=sid)
        if len(matches) != 1:
            fail('Shape ID is missing or ambiguous')
        shape = matches[0].getparent().getparent()
        if shape.tag != '{%s}sp' % NS['p'] or shape.getparent() != root.find('p:cSld/p:spTree', NS):
            fail('Only root native text shapes are supported')
        if len(shape.findall('p:txBody', NS)) != 1 or len(shape.findall('p:spPr', NS)) != 1:
            fail('Exactly one text body and shape properties element required')
        shape_props = shape.find('p:spPr', NS)
        transforms = shape_props.findall('a:xfrm', NS)
        if len(transforms) > 1:
            fail('Duplicate shape transforms')
        for transform in transforms:
            if len(transform.findall('a:off', NS)) != 1 or len(transform.findall('a:ext', NS)) != 1:
                fail('Exactly one explicit offset and extent required')
        body = shape.find('p:txBody', NS)
        if body is None or shape.xpath('.//mc:AlternateContent', namespaces={'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006'}):
            fail('Native text body required; alternate content is unsupported')
        for candidate in body.findall('a:p/a:r', NS):
            texts = candidate.findall('a:t', NS)
            if len(texts) != 1 or len(texts[0]):
                fail('Exactly one plain text element per run required')
            properties = candidate.findall('a:rPr', NS)
            if len(properties) > 1:
                fail('Duplicate run properties')
            if properties:
                tags = [child.tag for child in properties[0] if isinstance(child.tag, str)]
                if len(tags) != len(set(tags)):
                    fail('Duplicate run property children')
        text = '\n'.join(''.join(p.xpath('.//a:t/text()', namespaces=NS)) for p in body.findall('a:p', NS))
        if op['old_text'] != text:
            fail('Shape text precondition failed')
        if op['op'] == 'font':
            runs = body.findall('a:p/a:r', NS)
            run = runs[integer(op['run'], 0, len(runs) - 1)]
            if op['old_run_text'] != run.findtext('a:t', namespaces=NS):
                fail('Run text precondition failed')
            if len(run.findall('a:rPr', NS)) > 1:
                fail('Duplicate run properties')
            props = run.find('a:rPr', NS)
            if props is not None and any(len(props.findall('a:' + script, NS)) > 1 for script in ('latin', 'ea', 'cs')):
                fail('Duplicate font script properties')
            target = run
            char_fields={'tracking_pt':('spc',-20,100),'kerning_min_pt':('kern',0,400)}
            if set(char_fields).intersection(op):
                keys(op.get('old_character_spacing'),('spc','kern'))
                actual={k:props.get(k) if props is not None else None for k in ('spc','kern')}
                if op['old_character_spacing']!=actual:fail('Character spacing precondition failed')
                for key,(_,low,high) in char_fields.items():
                    if key in op:
                        value=op[key]
                        if type(value) not in (int,float) or not low<=value<=high or abs(value*100-round(value*100))>1e-7:fail('Character spacing must be bounded points in hundredths')
            elif 'old_character_spacing' in op:fail('Character spacing guard without a spacing change')
            if 'size_pt' in op:
                size = op['size_pt']
                if type(size) not in (int, float) or not 1 <= size <= 400 or abs(size * 100 - round(size * 100)) > 1e-7:
                    fail('Font size must be 1..400 pt in hundredths')
            if 'fonts' in op:
                fonts = op['fonts']
                if not isinstance(fonts, dict) or not fonts or set(fonts) - {'latin', 'ea', 'cs'}:
                    fail('Only latin, ea, cs font scripts supported')
                for font in fonts.values():
                    if not isinstance(font, str) or not 1 <= len(font) <= 128 or any(ord(c) < 32 for c in font) or font != font.strip() or font.startswith('+'):
                        fail('Invalid literal typeface')
        elif op['op'] == 'paragraph_spacing':
            paragraphs=body.findall('a:p', NS)
            target=paragraphs[integer(op['paragraph'],0,len(paragraphs)-1)]
            if len(target.findall('a:pPr',NS))>1:fail('Duplicate paragraph properties')
            props=target.find('a:pPr',NS)
            if props is not None and any(len(props.findall('a:'+tag,NS))>1 for tag in SPACING.values()):fail('Duplicate spacing properties')
            check_spacing_order(props)
            if op['old_spacing_xml']!=spacing_xml(props):fail('Paragraph spacing precondition failed')
            for key in SPACING:
                if key in op:
                    value=op[key]
                    if type(value) not in (int,float) or not (1 if key=='line_pt' else 0)<=value<=400 or abs(value*100-round(value*100))>1e-7:fail('Spacing must be bounded points in hundredths')
        else:
            target = shape.find('p:spPr/a:xfrm', NS)
            if target is None:
                fail('Explicit shape transform required')
            keys(op['old_xfrm'], ('x', 'y', 'cx', 'cy', 'rot', 'flipH', 'flipV'))
            off, ext = target.find('a:off', NS), target.find('a:ext', NS)
            if off is None or ext is None:
                fail('Explicit offset and extent required')
            actual = dict(x=off.get('x'), y=off.get('y'), cx=ext.get('cx'), cy=ext.get('cy'), rot=target.get('rot'), flipH=target.get('flipH'), flipV=target.get('flipV'))
            if actual != op['old_xfrm']:
                fail('Transform precondition failed')
            for axis, delta in [('x', 'dx_emu'), ('y', 'dy_emu')]:
                integer(op[delta], -MAX_DELTA, MAX_DELTA)
                integer(int(actual[axis]) + op[delta], -2147483648, 2147483647)
        path = root.getroottree().getpath(target)
        key = (name, path)
        if key in seen:
            fail('Duplicate operation target; combine font changes in one operation')
        seen.add(key)
        changes.append((name, path, op))
    return roots, changes


def edit(roots, changes):
    for name, path, op in changes:
        node = roots[name].xpath(path, namespaces={k: v for k, v in roots[name].nsmap.items() if k})[0]
        if op['op'] == 'translate':
            off = node.find('a:off', NS)
            for axis, delta in [('x', 'dx_emu'), ('y', 'dy_emu')]:
                off.set(axis, str(int(off.get(axis)) + op[delta]))
        elif op['op']=='paragraph_spacing':
            props=node.find('a:pPr',NS)
            if props is None:
                props=E.Element('{%s}pPr'%NS['a']);node.insert(0,props)
            for key,tag in SPACING.items():
                if key not in op:continue
                old=props.find('a:'+tag,NS)
                if old is not None:props.remove(old)
                child=E.Element('{%s}%s'%(NS['a'],tag));E.SubElement(child,'{%s}spcPts'%NS['a'],val=str(round(op[key]*100)))
                order=list(SPACING.values());rank=order.index(tag)
                index=next((i for i,c in enumerate(props) if E.QName(c).localname not in order or order.index(E.QName(c).localname)>rank),len(props));props.insert(index,child)
        else:
            props = node.find('a:rPr', NS)
            if props is None:
                props = E.Element('{%s}rPr' % NS['a'])
                node.insert(0, props)
            if 'size_pt' in op:
                props.set('sz', str(round(op['size_pt'] * 100)))
            for key,attr in [('tracking_pt','spc'),('kerning_min_pt','kern')]:
                if key in op:props.set(attr,str(round(op[key]*100)))
            for script, font in op.get('fonts', {}).items():
                child = props.find('a:' + script, NS)
                if child is None:
                    child = E.Element('{%s}%s' % (NS['a'], script))
                    # OOXML rPr child order: fonts precede hyperlink and extension nodes.
                    ranks = {'latin': 0, 'ea': 1, 'cs': 2, 'sym': 3, 'hlinkClick': 4, 'hlinkMouseOver': 5, 'rtl': 6, 'extLst': 7}
                    index = next((i for i, c in enumerate(props) if ranks.get(E.QName(c).localname, -1) > ranks[script]), len(props))
                    props.insert(index, child)
                child.set('typeface', font)


def validate(original, output, plan):
    """Independent allowed-diff check: undo only precisely authorized output fields."""
    keys(plan, ('version', 'source_sha256', 'operations'))
    if hashlib.sha256(original).hexdigest() != plan['source_sha256']:
        fail('Source SHA-256 mismatch')
    before, _, _ = package(original)
    after, _, _ = package(output)
    if before.keys() != after.keys():
        fail('Package membership changed')
    _, changes = resolve(before, plan)
    modified = {name for name, _, _ in changes}
    for name in before.keys() - modified:
        if before[name] != after[name]:
            fail('Untouched package member changed: ' + name)
    restored = {name: xml(after[name]) for name in modified}
    originals = {name: xml(before[name]) for name in modified}
    for name, path, op in changes:
        old = originals[name].xpath(path, namespaces={k: v for k, v in originals[name].nsmap.items() if k})[0]
        found = restored[name].xpath(path, namespaces={k: v for k, v in restored[name].nsmap.items() if k})
        if len(found) != 1:
            fail('Changed node identity')
        new = found[0]
        if op['op'] == 'translate':
            oldoff, newoff = old.find('a:off', NS), new.find('a:off', NS)
            for axis, delta in [('x', 'dx_emu'), ('y', 'dy_emu')]:
                if newoff.get(axis) != str(int(oldoff.get(axis)) + op[delta]):
                    fail('Translation mismatch')
                newoff.set(axis, oldoff.get(axis))
        elif op['op']=='paragraph_spacing':
            oldprops,newprops=old.find('a:pPr',NS),new.find('a:pPr',NS)
            if newprops is None:fail('Missing paragraph properties')
            check_spacing_order(newprops)
            for key,tag in SPACING.items():
                if key not in op:continue
                matches=newprops.findall('a:'+tag,NS)
                if len(matches)!=1:fail('Spacing node missing or duplicate')
                current=matches[0]
                if current.attrib or current.text or current.tail or len(current)!=1:fail('Unexpected spacing content')
                value=current[0]
                if value.tag!='{%s}spcPts'%NS['a'] or dict(value.attrib)!={'val':str(round(op[key]*100))} or len(value) or value.text or value.tail:fail('Spacing mismatch')
                newprops.remove(current)
            if oldprops is not None:
                for i,child in enumerate(oldprops):
                    if any(child.tag=='{%s}%s'%(NS['a'],tag) and key in op for key,tag in SPACING.items()):newprops.insert(i,copy.deepcopy(child))
            elif len(newprops) or newprops.attrib or newprops.text or newprops.tail:fail('Unexpected paragraph properties')
            else:new.remove(newprops)
        else:
            oldprops, newprops = old.find('a:rPr', NS), new.find('a:rPr', NS)
            if newprops is None:
                fail('Missing explicit run properties')
            if 'size_pt' in op:
                if newprops.get('sz') != str(round(op['size_pt'] * 100)):
                    fail('Size mismatch')
                previous = oldprops.get('sz') if oldprops is not None else None
                if previous is None:
                    del newprops.attrib['sz']
                else:
                    newprops.set('sz', previous)
            for key,attr in [('tracking_pt','spc'),('kerning_min_pt','kern')]:
                if key not in op:continue
                if newprops.get(attr)!=str(round(op[key]*100)):fail('Character spacing mismatch')
                previous=oldprops.get(attr) if oldprops is not None else None
                if previous is None:del newprops.attrib[attr]
                else:newprops.set(attr,previous)
            for script, font in op.get('fonts', {}).items():
                prev = oldprops.find('a:' + script, NS) if oldprops is not None else None
                current = newprops.find('a:' + script, NS)
                if current is None or current.get('typeface') != font:
                    fail('Typeface mismatch')
                if prev is None:
                    if dict(current.attrib) != {'typeface': font} or len(current) or current.text or current.tail:
                        fail('Unexpected added font content')
                    newprops.remove(current)
                elif prev.get('typeface') is None:
                    del current.attrib['typeface']
                else:
                    current.set('typeface', prev.get('typeface'))
            if oldprops is None:
                if len(newprops) or newprops.attrib or newprops.text or newprops.tail:
                    fail('Unexpected added run properties')
                new.remove(newprops)
    for name in modified:
        if E.tostring(originals[name], method='c14n') != E.tostring(restored[name], method='c14n'):
            fail('Unauthorized slide XML change: ' + name)


def execute(source, plan, output=None, apply=False):
    keys(plan, ('version', 'source_sha256', 'operations'))
    source = Path(source)
    original = source.read_bytes()
    if hashlib.sha256(original).hexdigest() != plan.get('source_sha256'):
        fail('Source SHA-256 mismatch')
    parts, infos, comment = package(original)
    roots, changes = resolve(parts, plan)
    edit(roots, changes)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as z:
        z.comment = comment
        for info in infos:
            value = E.tostring(roots[info.filename], xml_declaration=True, encoding='UTF-8') if info.filename in roots else parts[info.filename]
            z.writestr(copy.copy(info), value)
    result = buffer.getvalue()
    validate(original, result, plan)
    if apply:
        if output is None or Path(output).resolve() == source.resolve():
            fail('A distinct new output path is required')
        if source.read_bytes() != original:
            fail('Source changed during operation')
        # Exclusive creation never overwrites an existing output, including symlinks.
        with open(output, 'xb') as stream:
            stream.write(result)
            stream.flush()
            os.fsync(stream.fileno())
    return {'applied': apply, 'operations': len(changes), 'changed_members': sorted({n for n, _, _ in changes}), 'output_sha256': hashlib.sha256(result).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('plan')
    parser.add_argument('--output')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        plan = json.loads(Path(args.plan).read_text(encoding='utf-8'))
        print(json.dumps(execute(args.source, plan, args.output, args.apply), indent=2))
    except (ValueError, KeyError, IndexError, OSError, zipfile.BadZipFile, E.XMLSyntaxError) as exc:
        parser.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    main()
