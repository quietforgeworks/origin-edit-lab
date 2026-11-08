#!/usr/bin/env python3
"""Generate synthetic-only PPTX fixtures and test extraction/validation invariants."""
import base64
import copy
import hashlib
import importlib.util
import json
import subprocess
import tempfile
import sys
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('extractor', ROOT / 'scripts/inspect_pptx.py')
extractor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extractor)
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl6kxkAAAAASUVORK5CYII=')
P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
REL='http://schemas.openxmlformats.org/package/2006/relationships'
MC='http://schemas.openxmlformats.org/markup-compatibility/2006'


def synthetic_pic(ident):
    return f'<p:pic><p:nvPicPr><p:cNvPr id="{ident}" name="Synthetic preview"/></p:nvPicPr><p:blipFill><a:blip r:embed="rImg"/></p:blipFill></p:pic>'


def synthetic_ole(host_id, preview_id):
    # Same host/payload in two compatibility branches, like a cached OLE object.
    ole = '<p:oleObj r:id="rOle" progId="Origin50.Graph"><p:embed/>{}</p:oleObj>'
    return (f'<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="{host_id}" name="Synthetic OLE"/></p:nvGraphicFramePr>'
        '<a:graphic><a:graphicData><mc:AlternateContent><mc:Choice Requires="p">' + ole.format('') +
        '</mc:Choice><mc:Fallback>' + ole.format(synthetic_pic(preview_id)) +
        '</mc:Fallback></mc:AlternateContent></a:graphicData></a:graphic></p:graphicFrame>')


def synthetic_alternatives(content):
    return '<mc:AlternateContent><mc:Choice Requires="p">'+content+'</mc:Choice><mc:Fallback>'+content+'</mc:Fallback></mc:AlternateContent>'


def fixture(path, slide1_extra='', slide2_extra=''):
    head=f'<p:sld xmlns:p="{P}" xmlns:a="{A}" xmlns:r="{R}" xmlns:mc="{MC}"><p:cSld><p:spTree>'
    tail='</p:spTree></p:cSld></p:sld>'
    pic='<p:pic><p:nvPicPr><p:cNvPr id="2" name="Synthetic PNG"/></p:nvPicPr><p:blipFill><a:blip r:embed="rImg"/></p:blipFill><p:spPr><a:xfrm><a:off x="36000" y="72000"/><a:ext cx="360000" cy="180000"/></a:xfrm></p:spPr></p:pic>'
    group='<p:grpSp><p:nvGrpSpPr><p:cNvPr id="8" name="Synthetic group"/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="360000" cy="360000"/></a:xfrm></p:grpSpPr>'+pic.replace('id="2"','id="9"')+'</p:grpSp>'
    ole='<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="12" name="Synthetic Origin candidate"/></p:nvGraphicFramePr><p:xfrm><a:off x="0" y="0"/><a:ext cx="360000" cy="360000"/></p:xfrm><a:graphic><a:graphicData><p:oleObj r:id="rOle" progId="Origin50.Graph"/></a:graphicData></a:graphic></p:graphicFrame>'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('ppt/presentation.xml',f'<p:presentation xmlns:p="{P}" xmlns:r="{R}"><p:sldIdLst><p:sldId id="256" r:id="rSecond"/><p:sldId id="257" r:id="rFirst"/></p:sldIdLst><p:sldSz cx="7200000" cy="5400000"/></p:presentation>')
        z.writestr('ppt/_rels/presentation.xml.rels',f'<Relationships xmlns="{REL}"><Relationship Id="rSecond" Type="{R}/slide" Target="slides/slide2.xml"/><Relationship Id="rFirst" Type="{R}/slide" Target="slides/slide1.xml"/></Relationships>')
        z.writestr('ppt/slides/slide2.xml',head+pic+group+slide2_extra+tail)
        z.writestr('ppt/slides/slide1.xml',head+ole+slide1_extra+tail)
        z.writestr('ppt/slides/_rels/slide2.xml.rels',f'<Relationships xmlns="{REL}"><Relationship Id="rImg" Type="{R}/image" Target="../media/image1.png"/><Relationship Id="external" Type="{R}/hyperlink" Target="https://example.invalid/" TargetMode="External"/></Relationships>')
        z.writestr('ppt/slides/_rels/slide1.xml.rels',f'<Relationships xmlns="{REL}"><Relationship Id="rOle" Type="{R}/oleObject" Target="../embeddings/oleObject1.bin"/><Relationship Id="rImg" Type="{R}/image" Target="../media/image1.png"/></Relationships>')
        z.writestr('ppt/media/image1.png', PNG)
        z.writestr('ppt/embeddings/oleObject1.bin', b'SYNTHETIC TEST BYTES; NOT AN ORIGIN PROJECT')

class InventoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.dir=Path(self.tmp.name);self.pptx=self.dir/'synthetic.pptx';fixture(self.pptx)
        self.before=self.pptx.read_bytes();self.project,self.report=extractor.extract(self.pptx)

    def test_source_order_and_preservation(self):
        self.assertEqual([a['source']['slidePart'] for a in self.project['assets']], ['ppt/slides/slide2.xml','ppt/slides/slide2.xml','ppt/slides/slide1.xml'])
        self.assertEqual(self.project['assets'][0]['source']['slideNumber'],1)
        self.assertEqual(self.before,self.pptx.read_bytes())
        self.assertNotIn('complete_inventory', self.report)
        self.assertTrue(self.report['candidate_inventory_complete'])
        for field in ('scientific_segmentation_complete', 'scientific_grouping_complete',
                      'internal_ole_stream_inspection_complete', 'anchor_measurements_complete'):
            self.assertFalse(self.report[field])
        self.assertEqual(self.project['schema'],'figure-layout-inventory/v1')

    def test_group_and_origin_binding(self):
        image,group,origin=self.project['assets']
        self.assertEqual(image['source']['previewHash'],hashlib.sha256(PNG).hexdigest())
        self.assertIsNone(group['source']['previewPart'])
        self.assertEqual(group['source']['memberShapeIds'],['8','9'])
        self.assertEqual(origin['source']['progId'],'Origin50.Graph')
        self.assertEqual(origin['source']['embeddedHash'],hashlib.sha256(b'SYNTHETIC TEST BYTES; NOT AN ORIGIN PROJECT').hexdigest())
        self.assertNotIn('preview',image)

    def test_nested_preview_ids_are_not_structural_members(self):
        # Repeated 0 IDs and a nonzero cached ID must all be excluded structurally.
        extra = ''.join(synthetic_ole(host, cached) for host, cached in
                        [('21', '0'), ('22', '0'), ('23', '77')])
        extra += synthetic_pic('0') + synthetic_pic('77')
        fixture(self.pptx, slide1_extra=extra)
        before = self.pptx.read_bytes()
        project, report = extractor.extract(self.pptx)
        sources = {a['source']['shapeId']: a['source'] for a in project['assets']}
        all_preview_paths = []
        with zipfile.ZipFile(self.pptx) as z:
            root = ET.fromstring(z.read('ppt/slides/slide1.xml'))
            def resolve(path):
                prefix = '/p:sld[1]/'
                self.assertTrue(path.startswith(prefix))
                node = root.find(path[len(prefix):], extractor.NS)
                self.assertIsNotNone(node)
                return node
            for host, cached in [('21', '0'), ('22', '0'), ('23', '77')]:
                source = sources[host]
                self.assertEqual(source['memberShapeIds'], [host])
                self.assertEqual([m['shapeId'] for m in source['structuralMembers']], [host])
                self.assertEqual(source['kind'], 'pptx-ole')
                self.assertEqual(source['embeddedPart'], 'ppt/embeddings/oleObject1.bin')
                self.assertEqual(source['progId'], 'Origin50.Graph')
                self.assertEqual(source['previewHash'], hashlib.sha256(PNG).hexdigest())
                self.assertEqual(len(source['oleBindings']), 2)
                preview, = source['nestedPreviewShapes']
                self.assertEqual(preview['shapeId'], cached)
                self.assertEqual(preview['hostShapeId'], host)
                self.assertEqual(preview['hostXmlPath'], source['xmlPath'])
                self.assertEqual(preview['oleRelationshipId'], 'rOle')
                self.assertEqual(preview['relationshipIds'], ['rImg'])
                self.assertEqual(extractor.own_identity(resolve(preview['xmlPath'])).get('id'), cached)
                self.assertEqual(extractor.own_identity(resolve(preview['hostXmlPath'])).get('id'), host)
                self.assertEqual(resolve(preview['oleXmlPath']).get('{' + R + '}id'), 'rOle')
                image_link = next(r for r in source['relationships'] if r['relationshipId'] == 'rImg')
                self.assertEqual(image_link['sha256'], hashlib.sha256(PNG).hexdigest())
                ref, = image_link['references']
                self.assertTrue(ref['xmlPath'].startswith(preview['xmlPath'] + '/'))
                self.assertEqual(resolve(ref['xmlPath']).get(ref['attribute']), 'rImg')
                all_preview_paths.append(preview['xmlPath'])
        self.assertEqual(len(set(all_preview_paths)), 3)
        # The identical values remain valid IDs for independent ordinary pictures.
        for ident in ('0', '77'):
            self.assertEqual(sources[ident]['memberShapeIds'], [ident])
            self.assertEqual(sources[ident]['nestedPreviewShapes'], [])
        self.assertTrue(report['candidate_inventory_complete'])
        self.assertEqual(before, self.pptx.read_bytes())

    def test_group_and_alternate_branches_do_not_guess_membership(self):
        alternatives = synthetic_alternatives(synthetic_pic('42'))
        group = ('<p:grpSp><p:nvGrpSpPr><p:cNvPr id="30" name="Synthetic composite"/>'
                 '</p:nvGrpSpPr>' + synthetic_pic('0') + synthetic_ole('32', '81') +
                 alternatives + '</p:grpSp>')
        fixture(self.pptx, slide1_extra=group+alternatives)
        project, _ = extractor.extract(self.pptx)
        source, alternate = [a['source'] for a in project['assets'][-2:]]
        self.assertEqual(source['kind'], 'pptx-group')
        self.assertEqual(source['memberShapeIds'], ['30', '0', '32'])
        self.assertIsNone(source['embeddedPart'])
        self.assertIsNone(source['progId'])
        self.assertIsNone(source['bounds'])  # No borrowing a descendant transform.
        self.assertIsNone(source['previewPart'])
        self.assertEqual([m['shapeId'] for m in source['structuralMembers']], ['30', '0', '32', '42', '42'])
        self.assertEqual([p['shapeId'] for p in source['nestedPreviewShapes']], ['81'])
        self.assertEqual(source['nestedPreviewShapes'][0]['hostShapeId'], '32')
        for member in source['structuralMembers'][1:]:
            self.assertEqual(member['parentGroupXmlPath'], source['xmlPath'])
        self.assertEqual(alternate['kind'], 'pptx-alternate-content')
        self.assertIsNone(alternate['shapeId'])
        self.assertIsNone(alternate['bounds'])
        self.assertEqual(alternate['memberShapeIds'], [])
        self.assertEqual(alternate['compatibilityBranchSelection'], 'unresolved')
        self.assertEqual([m['shapeId'] for m in alternate['structuralMembers']], ['42', '42'])
        self.assertEqual(len({m['xmlPath'] for m in alternate['structuralMembers']}), 2)
        for member in alternate['structuralMembers']:
            self.assertEqual(len(member['compatibilityBranchPaths']), 1)
            self.assertIsNone(member['parentGroupXmlPath'])

    def test_host_identity_cannot_be_borrowed_from_preview(self):
        malformed = synthetic_ole('21', '77').replace('<p:cNvPr id="21" name="Synthetic OLE"/>', '')
        fixture(self.pptx, slide1_extra=malformed)
        with self.assertRaisesRegex(ValueError, 'stable shape ID'):
            extractor.extract(self.pptx)

    def test_distinct_ole_branches_have_no_scalar_payload_guess(self):
        alternatives = synthetic_ole('21', '77').replace('progId="Origin50.Graph"', 'progId="Other.Object"', 1)
        fixture(self.pptx, slide1_extra=alternatives)
        project, _ = extractor.extract(self.pptx)
        source = project['assets'][-1]['source']
        self.assertEqual(source['kind'], 'pptx-ole')
        self.assertIsNone(source['progId'])
        self.assertIsNone(source['embeddedPart'])
        self.assertEqual(len(source['oleBindings']), 2)
        self.assertEqual(source['memberShapeIds'], ['21'])

    def test_unsupported_candidates_are_reported_incomplete(self):
        fixture(self.pptx, slide1_extra='<p:contentPart r:id="rOle"/>')
        _, report = extractor.extract(self.pptx)
        self.assertFalse(report['candidate_inventory_complete'])
        self.assertTrue(any('Unsupported top-level element' in warning for warning in report['warnings']))
        unknown = '<p:contentPart r:id="rOle"/>'
        group = '<p:grpSp><p:nvGrpSpPr><p:cNvPr id="30"/></p:nvGrpSpPr>'+unknown+'</p:grpSp>'
        for candidate in (group, synthetic_alternatives(unknown)):
            fixture(self.pptx, slide1_extra=candidate)
            _, report = extractor.extract(self.pptx)
            self.assertFalse(report['candidate_inventory_complete'])
            self.assertTrue(any('Unsupported structural member' in warning for warning in report['warnings']))

    def test_unsafe_zip_refused(self):
        bad=self.dir/'unsafe.pptx'
        with zipfile.ZipFile(bad,'w') as z:z.writestr('../unsafe',b'x')
        with self.assertRaises(ValueError):extractor.extract(bad)

    def test_overwrite_refused(self):
        output=self.dir/'existing.json';output.write_text('keep')
        result=subprocess.run([sys.executable,*(['-O'] if sys.flags.optimize else []),str(ROOT/'scripts/inspect_pptx.py'),str(self.pptx),'--output',str(output)],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0);self.assertEqual(output.read_text(),'keep')

    def test_create_and_read_from_inspection(self):
        spec=importlib.util.spec_from_file_location('boxes',ROOT/'scripts/layout_boxes.py')
        boxes=importlib.util.module_from_spec(spec);spec.loader.exec_module(boxes)
        inventory=self.dir/'inventory.json';inventory.write_text(json.dumps(self.project))
        panels=self.dir/'panels.json';panels.write_text(json.dumps({'panels':[{'id':'F01','name':'Synthetic panel','sourceAssetIds':[self.project['assets'][0]['id'],self.project['assets'][1]['id']]},{'id':'F02','name':'Synthetic Origin candidate','sourceAssetIds':[self.project['assets'][2]['id']]}]}))
        draft=self.dir/'boxes.pptx';binding=self.dir/'binding.json';report=self.dir/'intent.json'
        boxes.create(inventory,draft,binding,panels)
        boxes.read_layout(draft,binding,report,[self.pptx])
        got=json.loads(report.read_text());self.assertTrue(got['originalSourceVerified']);self.assertEqual(len(got['selectedPanels']),2)
        self.assertEqual(len(got['selectedPanels'][0]['sourceBindings']),2)
        self.assertFalse(got['scientificSourceEdited']);self.assertEqual(self.before,self.pptx.read_bytes())

if __name__=='__main__':unittest.main(verbosity=2)
