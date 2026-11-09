"""Only generated synthetic ZIP/XML fixtures; no private scientific files."""
import copy
import hashlib
import io
import tempfile
import subprocess
import sys
import json
import unittest
from pathlib import Path
import zipfile
import safe_edit as s


def zipbytes(parts):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as z:
        for name, data in parts.items():
            z.writestr(name, data)
    return out.getvalue()


def fixture(inherited=False, wrapper='', tag='sp'):
    props = '' if inherited else '<a:rPr baseline="30000" b="1" i="1"><a:latin typeface="Old"/><a:ea typeface="OldEA"/><a:cs typeface="OldCS"/></a:rPr>'
    shape = f'<p:{tag}><p:nvSpPr><p:cNvPr id="2" name="scientific label"/></p:nvSpPr><p:spPr><a:xfrm rot="0"><a:off x="100" y="200"/><a:ext cx="300" cy="400"/></a:xfrm></p:spPr><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz="1000"/></a:pPr><a:r>{props}<a:t>α² 中文</a:t></a:r></a:p></p:txBody></p:{tag}>'
    if wrapper:
        shape = f'<{wrapper}>{shape}</{wrapper}>'
    slide = f'<p:sld xmlns:p="{s.NS["p"]}" xmlns:a="{s.NS["a"]}" xmlns:r="{s.NS["r"]}" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"><p:cSld><p:spTree>{shape}</p:spTree></p:cSld></p:sld>'
    return zipbytes({'ppt/presentation.xml': f'<p:presentation xmlns:p="{s.NS["p"]}" xmlns:r="{s.NS["r"]}"><p:sldIdLst><p:sldId id="256" r:id="second"/><p:sldId id="257" r:id="first"/></p:sldIdLst></p:presentation>', 'ppt/_rels/presentation.xml.rels': f'<Relationships xmlns="{s.REL}"><Relationship Id="first" Type="{s.NS["r"]}/slide" Target="slides/slide1.xml"/><Relationship Id="second" Type="{s.NS["r"]}/slide" Target="slides/slide9.xml"/></Relationships>', 'ppt/slides/slide9.xml': slide, 'ppt/slides/slide1.xml': slide, 'ppt/embeddings/oleObject1.bin': b'OPAQUE\x00\xff payload', 'ppt/media/image1.png': b'opaque image', '[Content_Types].xml': '<Types/>'})


class SafeEditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name) / 'source.pptx'
        self.output = Path(self.tmp.name) / 'output.pptx'
        self.data = fixture()
        self.source.write_bytes(self.data)
        self.op = {'op': 'font', 'slide': 1, 'shape_id': '2', 'old_text': 'α² 中文', 'run': 0, 'old_run_text': 'α² 中文', 'size_pt': 12.5, 'fonts': {'latin': 'Arial', 'ea': 'Noto Sans CJK SC', 'cs': 'Arial'}}

    def plan(self, op=None):
        return {'version': 1, 'source_sha256': hashlib.sha256(self.data).hexdigest(), 'operations': [copy.deepcopy(op or self.op)]}

    def apply(self, plan=None):
        return s.execute(self.source, plan or self.plan(), self.output, True)

    def test_dry_run(self):
        self.assertFalse(s.execute(self.source, self.plan(), self.output)['applied'])
        self.assertFalse(self.output.exists())
        self.assertEqual(self.source.read_bytes(), self.data)

    def test_reordered_slide_scientific_style_scripts_and_payload(self):
        self.apply()
        before, _, _ = s.package(self.data)
        after, _, _ = s.package(self.output.read_bytes())
        self.assertEqual([n for n in before if before[n] != after[n]], ['ppt/slides/slide9.xml'])
        root = s.xml(after['ppt/slides/slide9.xml'])
        props = root.find('.//a:rPr', s.NS)
        self.assertEqual(dict(props.attrib), {'baseline': '30000', 'b': '1', 'i': '1', 'sz': '1250'})
        self.assertEqual(props.find('a:ea', s.NS).get('typeface'), 'Noto Sans CJK SC')
        self.assertEqual(root.findtext('.//a:t', namespaces=s.NS), 'α² 中文')
        self.assertEqual(self.source.read_bytes(), self.data)

    def test_missing_run_properties(self):
        self.data = fixture(inherited=True)
        self.source.write_bytes(self.data)
        self.apply()
        after, _, _ = s.package(self.output.read_bytes())
        root = s.xml(after['ppt/slides/slide9.xml'])
        self.assertEqual(root.find('.//a:rPr', s.NS).get('sz'), '1250')
        self.assertEqual(root.find('.//a:defRPr', s.NS).get('sz'), '1000')

    def test_stale_hash(self):
        plan = self.plan(); plan['source_sha256'] = '0' * 64
        with self.assertRaises(ValueError): self.apply(plan)

    def test_unknown_operation_or_field(self):
        for field, value in [('op', 'ole'), ('extra', True), ('fonts', {'unknown': 'A'}), ('fonts', {'latin': 1}), ('size_pt', float('inf')), ('size_pt', float('nan')), ('size_pt', True), ('size_pt', 1.001)]:
            plan = self.plan(); plan['operations'][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError): self.apply(plan)

    def test_collision_and_source_as_output(self):
        self.output.write_bytes(b'KEEP')
        with self.assertRaises(FileExistsError): self.apply()
        self.assertEqual(self.output.read_bytes(), b'KEEP')
        with self.assertRaises(ValueError): s.execute(self.source, self.plan(), self.source, True)
        self.assertEqual(self.source.read_bytes(), self.data)

    def test_nested_shapes_and_non_native_targets(self):
        for wrapper, tag in [('p:grpSp', 'sp'), ('mc:AlternateContent', 'sp'), ('', 'graphicFrame'), ('', 'cxnSp')]:
            self.data = fixture(wrapper=wrapper, tag=tag); self.source.write_bytes(self.data)
            with self.subTest(wrapper=wrapper, tag=tag), self.assertRaises(ValueError): self.apply()

    def test_text_preconditions(self):
        for field in ('old_text', 'old_run_text', 'shape_id'):
            plan = self.plan(); plan['operations'][0][field] = 'wrong'
            with self.assertRaises(ValueError): self.apply(plan)

    def test_translate(self):
        op = {k: self.op[k] for k in ('slide', 'shape_id', 'old_text')}
        op.update(op='translate', old_xfrm=dict(x='100', y='200', cx='300', cy='400', rot='0', flipH=None, flipV=None), dx_emu=10, dy_emu=-20)
        self.apply(self.plan(op))
        after, _, _ = s.package(self.output.read_bytes())
        self.assertEqual(dict(s.xml(after['ppt/slides/slide9.xml']).find('.//a:off', s.NS).attrib), {'x': '110', 'y': '180'})
        for value in (float('inf'), float('nan'), True, 1.5, s.MAX_DELTA+1):
            bad = copy.deepcopy(op); bad['dx_emu'] = value
            with self.assertRaises(ValueError): s.execute(self.source, self.plan(bad))
        op['old_xfrm']['cx'] = '301'
        with self.assertRaises(ValueError): s.execute(self.source, self.plan(op))

    def test_validator_rejects_unplanned_payload_and_text_edits(self):
        self.apply()
        valid = self.output.read_bytes()
        for name in ('ppt/embeddings/oleObject1.bin', 'ppt/slides/slide9.xml', 'ppt/slides/slide1.xml'):
            parts, _, _ = s.package(valid)
            parts[name] = parts[name].replace('α²'.encode(), 'β³'.encode()) if name.endswith('.xml') else b'changed'
            with self.subTest(name=name), self.assertRaises(ValueError): s.validate(self.data, zipbytes(parts), self.plan())

    def test_duplicate_relevant_elements_fail_closed(self):
        for path in ('.//p:txBody', './/p:spPr', './/a:xfrm', './/a:off', './/a:ext', './/a:t', './/a:rPr', './/a:latin'):
            for kind in ('font', 'translate'):
                with self.subTest(path=path, kind=kind):
                    parts, _, _ = s.package(fixture())
                    root = s.xml(parts['ppt/slides/slide9.xml'])
                    node = root.find(path, s.NS)
                    node.getparent().append(copy.deepcopy(node))
                    parts['ppt/slides/slide9.xml'] = s.E.tostring(root)
                    self.data = zipbytes(parts)
                    self.source.write_bytes(self.data)
                    op = copy.deepcopy(self.op)
                    if path == './/a:t':
                        op['old_text'] *= 2
                    if kind == 'translate':
                        op = {key: op[key] for key in ('slide', 'shape_id', 'old_text')}
                        op.update(op='translate', old_xfrm=dict(x='100', y='200', cx='300', cy='400', rot='0', flipH=None, flipV=None), dx_emu=1, dy_emu=2)
                    with self.assertRaises(ValueError):
                        s.execute(self.source, self.plan(op))

    def test_cli_dry_run_and_apply(self):
        path = Path(self.tmp.name) / 'plan.json'
        path.write_text(json.dumps(self.plan()), encoding='utf-8')
        command = [sys.executable, '-B', str(Path(s.__file__)), str(self.source), str(path), '--output', str(self.output)]
        dry = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertFalse(json.loads(dry.stdout)['applied'])
        self.assertFalse(self.output.exists())
        applied = subprocess.run(command + ['--apply'], capture_output=True, text=True)
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertTrue(json.loads(applied.stdout)['applied'])
        self.assertTrue(self.output.exists())

    def test_validator_rejects_unplanned_style_changes(self):
        self.apply()
        parts, _, _ = s.package(self.output.read_bytes())
        parts['ppt/slides/slide9.xml'] = parts['ppt/slides/slide9.xml'].replace(b'baseline="30000"', b'baseline="0"')
        with self.assertRaises(ValueError): s.validate(self.data, zipbytes(parts), self.plan())

    def test_duplicate_targets(self):
        plan = self.plan(); plan['operations'].append(copy.deepcopy(self.op))
        with self.assertRaises(ValueError): self.apply(plan)


if __name__ == '__main__':
    unittest.main()
