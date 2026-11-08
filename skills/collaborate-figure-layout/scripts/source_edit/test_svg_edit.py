#!/usr/bin/env python3
"""Offline safety/regression tests; run: python -m unittest -v test_svg_edit.

Security regressions test known attack forms rather than certify arbitrary SVG safety.
Optional render smoke test uses an already installed Inkscape only.
"""
import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from lxml import etree
import svg_edit as editor

FIXTURE = '''<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">
<style>.curve {stroke:blue;stroke-width:2}</style>
<!-- retained comment -->
<rect id="background" width="640" height="360" fill="white"/>
<g id="plot" transform="translate(40,20)">
<path id="curve" class="curve" d="M 0,240 L 100,200 L 200,110 L 300,130 L 400,20" style="fill:none;stroke:green;opacity:0.8"/>
<text id="label" x="200" y="300" font-size="18">Time (s)</text>
<text id="mixed" x="20" y="20">A<tspan id="span">B</tspan>C</text>
<path id="outline" d="M 0,0 L 10,10"/>
</g></svg>'''

class SvgEditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.source = self.dir / 'source.svg'
        self.source.write_text(FIXTURE, encoding='utf-8')
        self.output = self.dir / 'output.svg'

    def plan(self, *edits):
        return {'source_sha256': hashlib.sha256(self.source.read_bytes()).hexdigest(), 'edits': list(edits)}

    def edit(self, ident='curve', **kwargs):
        return {'selector': {'id': ident}, **kwargs}

    def patch(self, *edits):
        return editor.patch_svg(self.source, self.output, self.plan(*edits))

    def test_inspection_and_selectors(self):
        result = editor.inspect_svg(self.source)
        self.assertEqual(result['sha256'], self.plan()['source_sha256'])
        self.assertEqual((result['width'], result['height'], result['viewBox']), ('640','360','0 0 640 360'))
        root = editor.load_svg(self.source)[1]
        for item in result['elements']:
            self.assertIs(editor.resolve(root, {'id': item['id']}), editor.resolve(root, {'path':item['path']}))
        mixed = next(i for i in result['elements'] if i['id'] == 'mixed')
        self.assertEqual(mixed['text'], 'ABC')

    def test_exact_hash_guard(self):
        plan = self.plan(self.edit(set={'stroke':'red'}))
        self.source.write_text(FIXTURE + '\n')
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            editor.patch_svg(self.source, self.output, plan)
        self.assertFalse(self.output.exists())

    def test_missing_duplicate_and_invalid_selectors(self):
        root = editor.load_svg(self.source)[1]
        for selector in ({'id':'absent'}, {'path':[-1]}, {'path':[True]}, {'path':[999]}, {'path':[1]}, {}, {'id':'curve','path':[]}, {'foo':'curve'}):
            with self.subTest(selector=selector), self.assertRaises(ValueError):
                editor.resolve(root, selector)
        root.append(etree.Element('{'+editor.SVG+'}path', id='curve'))
        with self.assertRaisesRegex(ValueError, 'uniquely'):
            editor.resolve(root, {'id':'curve'})

    def test_numeric_css_validation(self):
        valid = {'opacity':['0','0.5','1'], 'stroke-width':['0','.5','12px','9pt'], 'font-size':['16','12pt'], 'stroke-dasharray':['none','2 4','2,4,6']}
        invalid = {'opacity':['nan','inf','-0.1','1.1'], 'stroke-width':['-1','1e3','1001','NaN','2em'], 'font-size':['-2','1001pt'], 'stroke-dasharray':['-1 2','2;fill:red','url(http://x)']}
        for prop, values in valid.items():
            for value in values:
                with self.subTest(prop=prop,value=value): self.assertEqual(editor.validate_property(prop,value),value)
        for prop, values in invalid.items():
            for value in values:
                with self.subTest(prop=prop,value=value), self.assertRaises(ValueError): editor.validate_property(prop,value)

    def test_text_guards(self):
        for kwargs in ({'text':'new'}, {'text':'new','expected_text':'wrong'}, {'text':7,'expected_text':'Time (s)'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError): self.patch(self.edit('label', **kwargs))
        for ident, old in [('outline',''), ('mixed','ABC')]:
            with self.subTest(ident=ident), self.assertRaisesRegex(ValueError,'leaf text'):
                self.patch(self.edit(ident,text='new',expected_text=old))
        self.assertFalse(self.output.exists())

    def test_unicode_and_preservation_and_precedence(self):
        original = self.source.read_bytes()
        root_before = editor.load_svg(self.source)[1]
        result = self.patch(self.edit(set={'stroke':'#ff0000','stroke-width':'4'}),self.edit('label',text='时间 Δμ (秒)',expected_text='Time (s)'))
        root_after = editor.load_svg(self.output)[1]
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(root_before.attrib, root_after.attrib)
        for ident in ['background','mixed','outline']:
            self.assertEqual(etree.tostring(editor.resolve(root_before,{'id':ident})),etree.tostring(editor.resolve(root_after,{'id':ident})))
        before_curve = editor.resolve(root_before,{'id':'curve'})
        after_curve = editor.resolve(root_after,{'id':'curve'})
        self.assertEqual(before_curve.get('d'),after_curve.get('d'))
        self.assertEqual(after_curve.get('style'),'fill:none;opacity:0.8;stroke:#ff0000;stroke-width:4')
        self.assertEqual(editor.resolve(root_after,{'id':'label'}).text,'时间 Δμ (秒)')
        self.assertTrue(result['source_unchanged'])
        self.assertFalse(result['rendering_verified'])

    def test_output_protection(self):
        plan = self.plan(self.edit(set={'stroke':'red'}))
        self.output.write_text('keep')
        link = self.dir / 'link.svg'; link.symlink_to(self.source)
        dangling = self.dir / 'dangling.svg'; dangling.symlink_to(self.dir/'missing.svg')
        for dest in [self.source,self.output,link,dangling,self.dir/'bad.png',self.dir/'missing'/'out.svg']:
            with self.subTest(dest=dest), self.assertRaises(ValueError): editor.patch_svg(self.source,dest,plan)
        self.assertEqual(self.output.read_text(),'keep')
        self.assertEqual(self.source.read_text(),FIXTURE)

    def test_duplicate_targets_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'Merge edits'):
            self.patch(self.edit(set={'stroke':'red'}),self.edit(set={'stroke-width':'3'}))
        self.assertFalse(self.output.exists())

    def test_security_rejections(self):
        payloads = ['<script>alert(1)</script>','<rect onclick="foo()"/>','<foreignObject/>','<animate/>','<image href="https://example.test/x.png"/>','<image href="data:image/png;base64,AAAA"/>','<path fill="url(https://example.test/x)"/>','<style>@import "https://example.test/x";</style>','<style>path {stroke:red !important}</style>']
        for payload in payloads:
            self.source.write_text('<svg xmlns="'+editor.SVG+'">'+payload+'</svg>')
            with self.subTest(payload=payload), self.assertRaises(ValueError): editor.load_svg(self.source)
        for prefix in ['<!DOCTYPE svg>','<!DOCTYPE svg [<!ENTITY x SYSTEM "file:///etc/passwd">]>']:
            self.source.write_text(prefix+FIXTURE)
            with self.assertRaisesRegex(ValueError,'DTD/entities'): editor.load_svg(self.source)

    def test_inline_important_rejected(self):
        self.source.write_text(FIXTURE.replace('stroke:green','stroke:green !important'))
        with self.assertRaisesRegex(ValueError,'important'): self.patch(self.edit(set={'stroke':'red'}))

    def test_invalid_hex_colors_rejected(self):
        # CSS permits only 3, 4, 6, or 8 hex digits.
        for value in ['#12345','#1234567']:
            with self.assertRaises(ValueError): editor.validate_property('stroke',value)

    def test_external_stylesheet_processing_instruction_rejected(self):
        self.source.write_text('<?xml-stylesheet type="text/css" href="https://example.test/style.css"?>'+FIXTURE)
        with self.assertRaises(ValueError): editor.load_svg(self.source)

    def test_css_escaped_external_resource_rejected(self):
        self.source.write_text(FIXTURE.replace('fill:none',r'fill:u\72l(https://example.test/x.svg#paint)'))
        with self.assertRaises(ValueError): editor.load_svg(self.source)

    def test_external_xml_base_rejected(self):
        self.source.write_text(FIXTURE.replace('width="640" height="360" viewBox=', 'xml:base="https://example.test/external.svg" width="640" height="360" viewBox=', 1))
        with self.assertRaises(ValueError): editor.load_svg(self.source)

    @unittest.skipUnless(shutil.which('inkscape'), 'Inkscape is not installed')
    def test_render_inline_style_precedence(self):
        # Real rendering test: CSS class blue, old inline green, new inline red.
        self.patch(self.edit(set={'stroke':'#ff0000','stroke-width':'8','opacity':'1'}))
        png = self.dir/'preview.png'
        process = subprocess.run(['inkscape',str(self.output),'--export-type=png','--export-filename='+str(png)],capture_output=True,text=True,timeout=30)
        self.assertEqual(process.returncode,0,process.stderr)
        from PIL import Image
        im = Image.open(png).convert('RGB')
        self.assertEqual(im.size,(640,360))
        pixels = list(im.get_flattened_data()) if hasattr(im, 'get_flattened_data') else list(im.getdata())
        self.assertGreater(sum(r>220 and g<40 and b<40 for r,g,b in pixels),1000)
        self.assertEqual(sum(b>220 and r<40 and g<40 for r,g,b in pixels),0)

    def test_utf16_dtd_rejected(self):
        document = '<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE svg [<!ENTITY x "unsafe">]>' + FIXTURE
        self.source.write_bytes(document.encode('utf-16'))
        with self.assertRaises(ValueError): editor.load_svg(self.source)

    def test_utf16_external_stylesheet_rejected(self):
        document = '<?xml version="1.0" encoding="UTF-16"?><?xml-stylesheet href="https://example.test/x.css" type="text/css"?>' + FIXTURE
        self.source.write_bytes(document.encode('utf-16'))
        with self.assertRaises(ValueError): editor.load_svg(self.source)

if __name__ == '__main__': unittest.main(verbosity=2)
