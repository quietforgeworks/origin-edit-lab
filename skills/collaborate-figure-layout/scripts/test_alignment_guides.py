#!/usr/bin/env python3
"""Synthetic package-envelope tests only, not PowerPoint/Origin app validation."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import warnings
import zipfile

from lxml import etree as E
import alignment_guides as g

q, NS = g.q, g.NS


def write_parts(path, parts):
    with zipfile.ZipFile(path, 'x', zipfile.ZIP_DEFLATED) as archive:
        archive.comment = b'Synthetic alignment guide fixture'
        for name, data in parts.items():
            archive.writestr(name, data)


def fixture(path):
    """A small transitional package, including opaque synthetic embedded bytes."""
    p = E.Element(q('p', 'presentation'), nsmap={'p': NS['p'], 'r': NS['r']})
    ids = E.SubElement(p, q('p', 'sldIdLst'))
    E.SubElement(p, q('p', 'sldSz'), cx='9144000', cy='5143500')
    prs = E.Element(q('pr', 'Relationships'), nsmap={None: NS['pr']})
    types = E.Element(q('ct', 'Types'), nsmap={None: NS['ct']})
    for ext, mime in [('rels', 'application/vnd.openxmlformats-package.relationships+xml'),
                      ('xml', 'application/xml'), ('bin', 'application/octet-stream')]:
        E.SubElement(types, q('ct', 'Default'), Extension=ext, ContentType=mime)
    E.SubElement(types, q('ct', 'Override'), PartName='/ppt/presentation.xml',
                 ContentType='application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml')
    rootrels = E.Element(q('pr', 'Relationships'), nsmap={None: NS['pr']})
    E.SubElement(rootrels, q('pr', 'Relationship'), Id='rIdOffice',
                 Type=NS['r'] + '/officeDocument', Target='ppt/presentation.xml')
    parts = {'_rels/.rels': g.pp.serialize(rootrels),
             'ppt/embeddings/synthetic.bin': b'SYNTHETIC OPAQUE PAYLOAD\x00\xff\x01',
             'docProps/synthetic.xml': b'<synthetic>Untouched metadata</synthetic>'}
    # Presentation order deliberately differs from file-number order.
    for number, filename in enumerate(('slide8.xml', 'slide3.xml'), 1):
        E.SubElement(ids, q('p', 'sldId'), {'id': str(255 + number), q('r', 'id'): 'r' + str(number)})
        E.SubElement(prs, q('pr', 'Relationship'), Id='r' + str(number),
                     Type=NS['r'] + '/slide', Target='slides/' + filename)
        E.SubElement(types, q('ct', 'Override'), PartName='/ppt/slides/' + filename,
                     ContentType='application/vnd.openxmlformats-officedocument.presentationml.slide+xml')
        slide = E.Element(q('p', 'sld'), nsmap={'p': NS['p'], 'a': NS['a'], 'r': NS['r']})
        tree = E.SubElement(E.SubElement(slide, q('p', 'cSld')), q('p', 'spTree'))
        nv = E.SubElement(tree, q('p', 'nvGrpSpPr'))
        E.SubElement(nv, q('p', 'cNvPr'), id='1', name='')
        E.SubElement(nv, q('p', 'cNvGrpSpPr')); E.SubElement(nv, q('p', 'nvPr'))
        E.SubElement(tree, q('p', 'grpSpPr'))
        for sid, name, text in [(2, 'Synthetic scientific label', 'H₂O  Ω  unchanged'),
                                (3, 'Existing scientific annotation', 'Source label')]:
            shape = E.SubElement(tree, q('p', 'sp'))
            nv = E.SubElement(shape, q('p', 'nvSpPr'))
            E.SubElement(nv, q('p', 'cNvPr'), id=str(sid), name=name)
            E.SubElement(nv, q('p', 'cNvSpPr')); E.SubElement(nv, q('p', 'nvPr'))
            props = E.SubElement(shape, q('p', 'spPr'))
            xf = E.SubElement(props, q('a', 'xfrm'))
            E.SubElement(xf, q('a', 'off'), x='1111', y='2222')
            E.SubElement(xf, q('a', 'ext'), cx='3333', cy='4444')
            E.SubElement(E.SubElement(props, q('a', 'prstGeom'), prst='rect'), q('a', 'avLst'))
            tx = E.SubElement(shape, q('p', 'txBody'))
            E.SubElement(tx, q('a', 'bodyPr')); E.SubElement(tx, q('a', 'lstStyle'))
            run = E.SubElement(E.SubElement(tx, q('a', 'p')), q('a', 'r'))
            E.SubElement(run, q('a', 'rPr'), b='1', baseline='-25000')
            E.SubElement(run, q('a', 't')).text = text
        # Keep an existing connector/annotation untouched; do not classify its meaning.
        connector = E.SubElement(tree, q('p', 'cxnSp'))
        nv = E.SubElement(connector, q('p', 'nvCxnSpPr'))
        E.SubElement(nv, q('p', 'cNvPr'), id='4', name='Existing connector')
        E.SubElement(nv, q('p', 'cNvCxnSpPr')); E.SubElement(nv, q('p', 'nvPr'))
        E.SubElement(connector, q('p', 'spPr'))
        E.SubElement(E.SubElement(slide, q('p', 'clrMapOvr')), q('a', 'masterClrMapping'))
        parts['ppt/slides/' + filename] = g.pp.serialize(slide)
    parts.update({'[Content_Types].xml': g.pp.serialize(types),
                  'ppt/presentation.xml': g.pp.serialize(p),
                  'ppt/_rels/presentation.xml.rels': g.pp.serialize(prs)})
    write_parts(path, parts)
    return parts


class GuideTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-guide-tests-')
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.source = self.dir / 'clean-final.pptx'
        self.parts = fixture(self.source)
        self.source_bytes = self.source.read_bytes()
        self.plan = {'schema': g.SCHEMA, 'source_sha256': g.pp.digest(self.source_bytes),
                     'slide': 2, 'unit': 'EMU', 'group_id': 100,
                     'lines': [{'id': 101, 'key': 'top_axis', 'x1': 0, 'y1': 720000,
                                'x2': 9144000, 'y2': 720000},
                               {'id': 102, 'key': 'left_axis', 'x1': 360000, 'y1': 0,
                                'x2': 360000, 'y2': 5143500}]}
        self.output = self.dir / 'guided-final.pptx'

    def altered(self, mutate, parts=None, name='changed.pptx'):
        parts = dict(self.parts if parts is None else parts)
        mutate(parts)
        path = self.dir / name
        write_parts(path, parts)
        return path

    def candidate(self):
        g.add(self.source, self.plan, self.output)
        return dict(g.load_package(self.output).parts)

    def test_add_verify_restore_exact_original(self):
        result = g.add(self.source, self.plan, self.output)
        self.assertEqual(result['slide_part'], 'ppt/slides/slide3.xml')
        self.assertEqual(result['guide_group_count'], 1)
        self.assertFalse(result['powerpoint_reopen_verified'])
        self.assertEqual(self.source.read_bytes(), self.source_bytes)
        source, candidate = g.load_package(self.source), g.load_package(self.output)
        for part in source.parts:
            if part != result['slide_part']:
                self.assertEqual(source.parts[part], candidate.parts[part], part)
        _, root = candidate.slide(2)
        group = root.find('p:cSld/p:spTree', NS)[2]
        self.assertEqual(group.tag, q('p', 'grpSp'))
        self.assertNotIn(self.plan['source_sha256'], g.pp.serialize(group).decode())
        self.assertNotIn('sha256', g.pp.serialize(group).decode())
        self.assertEqual(len(group.findall('p:sp', NS)), 2)
        self.assertEqual([n.get('type') for n in group.findall('.//a:headEnd', NS)], ['none', 'none'])
        self.assertTrue(g.verify(self.source, self.plan, self.output)['source_slide_xml_equivalent_after_group_removal'])
        restored = self.dir / 'restored-clean-final.pptx'
        report = g.restore(self.source, self.plan, self.output, restored)
        self.assertTrue(report['exact_original_file_bytes_restored'])
        self.assertEqual(restored.read_bytes(), self.source_bytes)
        self.assertEqual(self.source.read_bytes(), self.source_bytes)

    def test_repeated_ole_preview_zero_ids_are_not_structural(self):
        def mutate(parts):
            root = g.pp.xml(parts['ppt/slides/slide3.xml'])
            tree = root.find('p:cSld/p:spTree', NS)
            relationships = E.Element(q('pr', 'Relationships'), nsmap={None: NS['pr']})
            for structural_id in (5, 6):
                frame = E.SubElement(tree, q('p', 'graphicFrame'))
                nv = E.SubElement(frame, q('p', 'nvGraphicFramePr'))
                E.SubElement(nv, q('p', 'cNvPr'), id=str(structural_id), name='Synthetic OLE')
                E.SubElement(nv, q('p', 'cNvGraphicFramePr')); E.SubElement(nv, q('p', 'nvPr'))
                xf = E.SubElement(frame, q('p', 'xfrm'))
                E.SubElement(xf, q('a', 'off'), x='1000', y='2000')
                E.SubElement(xf, q('a', 'ext'), cx='3000', cy='4000')
                data = E.SubElement(E.SubElement(frame, q('a', 'graphic')), q('a', 'graphicData'), uri=NS['p'] + '/ole')
                ole = E.SubElement(data, q('p', 'oleObj'), {q('r', 'id'): 'rOle', 'progId': 'Synthetic.Inert'})
                E.SubElement(ole, q('p', 'embed'))
                pic = E.SubElement(ole, q('p', 'pic'))
                pnv = E.SubElement(pic, q('p', 'nvPicPr'))
                E.SubElement(pnv, q('p', 'cNvPr'), id='0', name='Repeated cached representation')
                E.SubElement(pnv, q('p', 'cNvPicPr')); E.SubElement(pnv, q('p', 'nvPr'))
            E.SubElement(relationships, q('pr', 'Relationship'), Id='rOle', Type=NS['r'] + '/oleObject', Target='../embeddings/synthetic.bin')
            parts['ppt/slides/_rels/slide3.xml.rels'] = g.pp.serialize(relationships)
            parts['ppt/slides/slide3.xml'] = g.pp.serialize(root)
        source = self.altered(mutate, name='ole-previews.pptx')
        plan = copy.deepcopy(self.plan); plan['source_sha256'] = g.pp.digest(source.read_bytes())
        g.add(source, plan, self.output)
        self.assertTrue(g.verify(source, plan, self.output)['other_parts_and_embedded_payloads_byte_identical'])
        restored = self.dir / 'ole-restored.pptx'
        g.restore(source, plan, self.output, restored)
        self.assertEqual(restored.read_bytes(), source.read_bytes())

    def test_plan_id_and_schema_rejections(self):
        changes = [('source_sha256', '0' * 64), ('slide', 3), ('slide', True),
                   ('group_id', 1), ('group_id', True), ('group_id', 101),
                   ('group_id', 2**32), ('unit', 'mm'), ('schema', 'unknown'), ('lines', [])]
        for key, value in changes:
            with self.subTest(key=key, value=value):
                plan = copy.deepcopy(self.plan); plan[key] = value
                with self.assertRaises(ValueError):
                    g.add(self.source, plan, self.output)
                self.assertFalse(self.output.exists())
        plan = copy.deepcopy(self.plan); plan['lines'][1]['id'] = 101
        with self.assertRaises(ValueError): g.add(self.source, plan, self.output)
        plan = copy.deepcopy(self.plan); plan['lines'][1]['key'] = 'top_axis'
        with self.assertRaises(ValueError): g.add(self.source, plan, self.output)
        plan = copy.deepcopy(self.plan); plan['approval'] = True
        with self.assertRaises(ValueError): g.add(self.source, plan, self.output)

    def test_invalid_line_geometry(self):
        for updates in ({'x1': 4, 'x2': 3}, {'x1': -1}, {'x2': 9144001},
                        {'y2': 5143501}, {'x1': 0.5}, {'x1': float('nan')},
                        {'x1': float('inf')}, {'x1': True}, {'x1': '0'},
                        {'x2': 0}, {'y2': 720001}, {'key': '<xml>'}):
            with self.subTest(updates=updates):
                plan = copy.deepcopy(self.plan); plan['lines'][0].update(updates)
                with self.assertRaises(ValueError): g.add(self.source, plan, self.output)
                self.assertFalse(self.output.exists())
        plan = copy.deepcopy(self.plan)
        plan['lines'][1].update(y1=400, y2=300)
        with self.assertRaises(ValueError): g.add(self.source, plan, self.output)

    def test_stale_and_mismatched_source(self):
        changed = self.altered(lambda parts: parts.update({'docProps/synthetic.xml': b'<changed/>'}))
        with self.assertRaises(ValueError): g.add(changed, self.plan, self.output)
        self.candidate()
        with self.assertRaises(ValueError): g.verify(changed, self.plan, self.output)
        with self.assertRaises(ValueError): g.restore(changed, self.plan, self.output, self.dir / 'restore.pptx')
        wrong_plan = copy.deepcopy(self.plan); wrong_plan['lines'][0]['x1'] = 1
        with self.assertRaises(ValueError): g.verify(self.source, wrong_plan, self.output)

    def test_source_and_candidate_changes_during_verification_fail(self):
        self.candidate()
        old_canonical = g.canonical
        for path in (self.source, self.output):
            with self.subTest(changed_file=path.name):
                original = path.read_bytes()
                changed = False
                def mutate_during_comparison(root):
                    nonlocal changed
                    if not changed:
                        changed = True
                        # Appending a ZIP comment-like suffix changes whole-file
                        # bytes after loading without altering parsed part data.
                        path.write_bytes(original + b'changed during verification')
                    return old_canonical(root)
                try:
                    with mock.patch.object(g, 'canonical', side_effect=mutate_during_comparison):
                        with self.assertRaisesRegex(ValueError, 'changed during verification'):
                            g.verify(self.source, self.plan, self.output)
                finally:
                    path.write_bytes(original)
                self.assertTrue(changed)

    def test_existing_output_and_guides_rejected(self):
        self.candidate()
        before = self.output.read_bytes()
        with self.assertRaises(ValueError): g.add(self.source, self.plan, self.output)
        with self.assertRaises(ValueError): g.restore(self.source, self.plan, self.output, self.output)
        with self.assertRaises(ValueError): g.restore(self.source, self.plan, self.output, self.source)
        self.assertEqual(self.output.read_bytes(), before)
        plan = copy.deepcopy(self.plan); plan['source_sha256'] = g.pp.digest(before)
        with self.assertRaises(ValueError): g.add(self.output, plan, self.dir / 'twice.pptx')
        link = self.dir / 'dangling.pptx'; link.symlink_to(self.dir / 'absent')
        with self.assertRaises(ValueError): g.add(self.source, self.plan, link)

    def test_tampered_science_or_other_parts_rejected(self):
        base = self.candidate()
        for key, value in [('ppt/embeddings/synthetic.bin', b'changed data'),
                           ('docProps/synthetic.xml', b'<changed/>'),
                           ('ppt/slides/slide8.xml', b'<changed/>')]:
            with self.subTest(key=key):
                changed = self.altered(lambda parts: parts.update({key: value}), base, key.split('/')[-1] + '.pptx')
                with self.assertRaises(ValueError): g.verify(self.source, self.plan, changed)
        for index, tag, attribute in [(1, 'a:t', None), (2, 'a:xfrm/a:off', 'x'),
                                       (3, 'a:rPr', 'baseline')]:
            def mutate(parts):
                root = g.pp.xml(parts['ppt/slides/slide3.xml'])
                shape = root.find('p:cSld/p:spTree', NS)[3]
                node = shape.find('.//' + tag, NS)
                if attribute: node.set(attribute, '99')
                else: node.text = 'tampered science'
                parts['ppt/slides/slide3.xml'] = g.pp.serialize(root)
            changed = self.altered(mutate, base, 'science' + str(index) + '.pptx')
            with self.assertRaises(ValueError): g.verify(self.source, self.plan, changed)
            with self.assertRaises(ValueError): g.restore(self.source, self.plan, changed, self.dir / 'forbidden.pptx')
            self.assertFalse((self.dir / 'forbidden.pptx').exists())

    def test_malicious_or_modified_group_rejected(self):
        base = self.candidate()
        def text_member(group): E.SubElement(group, q('p', 'pic'))
        def arrow(group): group.find('.//a:headEnd', NS).set('type', 'triangle')
        def move(group): group.find('p:sp/p:spPr/a:xfrm/a:off', NS).set('x', '1')
        def id_duplicate(group): group.find('p:sp/p:nvSpPr/p:cNvPr', NS).set('id', '2')
        def unlabeled(group): group.find('p:nvGrpSpPr/p:cNvPr', NS).set('name', 'unmarked')
        def nested(group): group.append(E.Element(q('p', 'grpSp')))
        def escaped_member(group): group.getparent().append(group[-1])
        def duplicate_group(group): group.getparent().append(copy.deepcopy(group))
        def front(group): group.getparent().append(group)
        for index, action in enumerate((text_member, arrow, move, id_duplicate, unlabeled,
                                         nested, escaped_member, duplicate_group, front)):
            with self.subTest(action=action.__name__):
                def mutate(parts):
                    root = g.pp.xml(parts['ppt/slides/slide3.xml'])
                    action(root.find('p:cSld/p:spTree/p:grpSp', NS))
                    parts['ppt/slides/slide3.xml'] = g.pp.serialize(root)
                changed = self.altered(mutate, base, 'malicious' + str(index) + '.pptx')
                with self.assertRaises(ValueError): g.verify(self.source, self.plan, changed)

    def test_source_duplicates_and_unsupported_structures(self):
        def duplicate(root):
            root.find('.//p:nvSpPr/p:cNvPr', NS).set('id', '1')
        def source_group(root):
            E.SubElement(root.find('p:cSld/p:spTree', NS), q('p', 'grpSp'))
        def alternate(root):
            E.SubElement(root.find('p:cSld/p:spTree', NS), q('mc', 'AlternateContent'))
        def timing(root): E.SubElement(root, q('p', 'timing'))
        def marker(root):
            root.find('.//p:nvSpPr/p:cNvPr', NS).set('descr', 'figure-alignment-guides/v0')
        for index, action in enumerate((duplicate, source_group, alternate, timing, marker)):
            def mutate(parts):
                root = g.pp.xml(parts['ppt/slides/slide3.xml']); action(root)
                parts['ppt/slides/slide3.xml'] = g.pp.serialize(root)
            changed = self.altered(mutate, name='unsupported' + str(index) + '.pptx')
            plan = copy.deepcopy(self.plan); plan['source_sha256'] = g.pp.digest(changed.read_bytes())
            with self.assertRaises(ValueError): g.add(changed, plan, self.output)
            self.assertFalse(self.output.exists())

    def test_unsafe_package_rejections(self):
        external = b'<Relationships xmlns="' + NS['pr'].encode() + b'"><Relationship Id="r" Type="hyperlink" TargetMode="External" Target="https://example.invalid"/></Relationships>'
        mutations = [lambda parts: parts.update({'_xmlsignatures/signature.xml': b'<x/>'}),
                     lambda parts: parts.update({'ppt/activeX/item.xml': b'<x/>'}),
                     lambda parts: parts.update({'ppt/_rels/unsafe.xml.rels': external}),
                     lambda parts: parts.update({'docProps/synthetic.xml': b'<!DOCTYPE x [<!ENTITY e "bad">]><x>&e;</x>'}),
                     lambda parts: parts.update({'../escape.xml': b'<x/>'}),
                     lambda parts: parts.update({'ppt/./ambiguous.xml': b'<x/>'})]
        for index, mutate in enumerate(mutations):
            changed = self.altered(mutate, name='unsafe' + str(index) + '.pptx')
            with self.assertRaises(ValueError): g.load_package(changed)
        duplicate = self.dir / 'duplicate.pptx'
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(duplicate, 'x') as archive:
                for name, data in self.parts.items(): archive.writestr(name, data)
                archive.writestr('ppt/presentation.xml', self.parts['ppt/presentation.xml'])
        with self.assertRaises(ValueError): g.load_package(duplicate)

    def test_strict_json_and_cli_lifecycle(self):
        plan_file = self.dir / 'plan.json'
        plan_file.write_text('{"schema":1,"schema":2}')
        with self.assertRaises(ValueError): g.read_plan(plan_file)
        plan_file.write_text('{"x":NaN}')
        with self.assertRaises(ValueError): g.read_plan(plan_file)
        plan_file.write_text(json.dumps(self.plan))
        base = [sys.executable, str(Path(g.__file__))]
        if sys.flags.optimize:
            base.insert(1, '-O')
        common = ['--source', str(self.source), '--plan', str(plan_file)]
        for command, args in [('add', ['--output', str(self.output)]),
                              ('verify', ['--guided', str(self.output)]),
                              ('restore', ['--guided', str(self.output), '--output', str(self.dir / 'restored.pptx')])]:
            run = subprocess.run(base + [command] + common + args, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)['guide_group_count'], 1)
        self.assertEqual((self.dir / 'restored.pptx').read_bytes(), self.source_bytes)
        run = subprocess.run(base + ['add'] + common + ['--output', str(self.output)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertIn('overwrite', run.stderr)


if __name__ == '__main__':
    unittest.main()
