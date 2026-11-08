from pathlib import Path
import copy
import tempfile
import unittest
from lxml import etree as E
import pptx_origin as m
from test_pptx_origin import build_ole_fixture,write_parts,FIX


def paired(source,out):
    p=m.Package(source);part,root=p.slide(1);ole=root.find('.//p:oleObj',m.NS);parent=ole.getparent();parent.remove(ole)
    ac=E.SubElement(parent,m.q('mc','AlternateContent'),nsmap={'mc':m.NS['mc']})
    choice=E.SubElement(ac,m.q('mc','Choice'),Requires='v',nsmap={'v':m.NS['v']})
    co=copy.deepcopy(ole);co.set('spid','_testShape');co.remove(co.find('p:pic',m.NS));choice.append(co)
    fallback=E.SubElement(ac,m.q('mc','Fallback'));fallback.append(ole)
    old=p.inspect()['slides'][0]['objects'][0]['previews'][0]['raster_or_original']['part']
    vp='ppt/drawings/vmlDrawing1.vml';rp=m.rels_part(part);rr=m.xml(p.parts[rp])
    E.SubElement(rr,m.q('pr','Relationship'),Id='rIdVml',Type=m.NS['r']+'/vmlDrawing',Target='../drawings/vmlDrawing1.vml')
    vr=E.Element('xml',nsmap={'v':m.NS['v'],'o':m.NS['o']});shape=E.SubElement(vr,m.q('v','shape'),id='_testShape')
    E.SubElement(shape,m.q('v','imagedata'),{m.q('o','relid'):'rId1'})
    vrr=E.Element(m.q('pr','Relationships'),nsmap={None:m.NS['pr']})
    E.SubElement(vrr,m.q('pr','Relationship'),Id='rId1',Type=m.IMAGE_REL,Target='../media/'+Path(old).name)
    ct=m.xml(p.parts['[Content_Types].xml']);E.SubElement(ct,m.q('ct','Default'),Extension='vml',ContentType='application/vnd.openxmlformats-officedocument.vmlDrawing')
    write_parts(source,out,{part:m.serialize(root),rp:m.serialize(rr),'[Content_Types].xml':m.serialize(ct)},
                {vp:m.serialize(vr),m.rels_part(vp):m.serialize(vrr)})

class PairedVmlTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.d=Path(self.tmp.name)
        source=self.d/'base.pptx';build_ole_fixture(source)
        self.src=self.d/'paired.pptx';paired(source,self.src);self.out=self.d/'out.pptx'
    def tearDown(self):self.tmp.cleanup()
    def test_logical_dedup_and_synchronized_update(self):
        p=m.Package(self.src);rows=p.inspect()['slides'][0]['objects'];self.assertEqual(len(rows),2)
        self.assertTrue(rows[0]['safe_replace_supported']);self.assertTrue(rows[0]['paired_preview_supported'])
        r=m.replace(self.src,self.out,1,'ole:0',FIX/'after.png',svg=FIX/'after.svg',acknowledge_stale_ole=True)
        self.assertTrue(r['paired_vml_preview_updated']);self.assertTrue(r['existing_relationships_preserved'])
        self.assertTrue(r['embedded_payloads_unchanged']);self.assertEqual(r['unchanged_slides'],[2])
        a=m.Package(self.out).inspect()['slides'][0]['objects'][0]
        self.assertEqual(a['vml_preview']['part'],a['previews'][0]['raster_or_original']['part'])
        self.assertEqual(len(a['previews'][0]['svg']),1)
        self.assertEqual(m.Package(self.out).inspect()['slides'][0]['objects'][1],rows[1])
    def test_mismatched_ole_branch_refused(self):
        p=m.Package(self.src);part,root=p.slide(1);root.find('.//mc:Choice/p:oleObj',m.NS).set('progId','Different.Graph')
        bad=self.d/'mismatch.pptx';write_parts(self.src,bad,{part:m.serialize(root)})
        with self.assertRaisesRegex(ValueError,'Inconsistent'):m.replace(bad,self.out,1,'ole:0',FIX/'after.png',acknowledge_stale_ole=True)
    def test_shared_vml_drawing_refused(self):
        p=m.Package(self.src);part=p.slides[1];rp=m.rels_part(part);rr=m.xml(p.parts[rp])
        E.SubElement(rr,m.q('pr','Relationship'),Id='rIdShared',Type=m.NS['r']+'/vmlDrawing',Target='../drawings/vmlDrawing1.vml')
        bad=self.d/'shared.pptx';write_parts(self.src,bad,{rp:m.serialize(rr)})
        with self.assertRaisesRegex(ValueError,'Shared VML'):m.replace(bad,self.out,1,'ole:0',FIX/'after.png',acknowledge_stale_ole=True)
    def test_vml_drawing_only_target_shape_changes(self):
        p=m.Package(self.src);vp='ppt/drawings/vmlDrawing1.vml';vr=m.xml(p.parts[vp]);other=copy.deepcopy(vr[0]);other.set('id','other');vr.append(other)
        src=self.d/'two.pptx';write_parts(self.src,src,{vp:m.serialize(vr)})
        m.replace(src,self.out,1,'ole:0',FIX/'after.png',acknowledge_stale_ole=True)
        after=m.xml(m.Package(self.out).parts[vp]);self.assertEqual(E.tostring(other),E.tostring(after[1]))
    def test_old_vml_image_preserved_for_other_shapes(self):
        p=m.Package(self.src);vp='ppt/drawings/vmlDrawing1.vml';old=p.relationships(vp)['rId1']
        m.replace(self.src,self.out,1,'ole:0',FIX/'after.png',acknowledge_stale_ole=True)
        a=m.Package(self.out);self.assertEqual(old,a.relationships(vp)['rId1']);self.assertEqual(p.parts[old['part']],a.parts[old['part']])
    def test_svg_resource_in_presentation_attribute_refused(self):
        f=self.d/'external.svg';f.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect fill="url(https://example.com/x)"/></svg>')
        with self.assertRaises(ValueError):m.validate_svg(f)

if __name__=='__main__':unittest.main(verbosity=2)
