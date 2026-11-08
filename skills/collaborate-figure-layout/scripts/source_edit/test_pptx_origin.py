from pathlib import Path
import copy
import json
import tempfile
import unittest
import zipfile
from lxml import etree as E
import pptx_origin as m

# All fixtures are generated synthetic content; no deck or image assets are bundled.
from synthetic_fixtures import fixture_directory
FIX=fixture_directory()

def write_parts(source, output, changes=None, adds=None):
    changes=changes or {};adds=adds or {}
    with zipfile.ZipFile(source) as z, zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as o:
        for i in z.infolist():o.writestr(i,changes.get(i.filename,z.read(i)))
        for k,v in adds.items():o.writestr(k,v)

def build_ole_fixture(output, shared_picture=True):
    source=FIX/'baseline.pptx';pkg=m.Package(source);part,root=pkg.slide(1)
    pic=root.find('.//p:pic',m.NS);parent=pic.getparent();index=parent.index(pic)
    gf=E.Element(m.q('p','graphicFrame'))
    nv=E.SubElement(gf,m.q('p','nvGraphicFramePr'))
    E.SubElement(nv,m.q('p','cNvPr'),id='20',name='Synthetic Origin OLE fixture')
    E.SubElement(nv,m.q('p','cNvGraphicFramePr'));E.SubElement(nv,m.q('p','nvPr'))
    xf=copy.deepcopy(pic.find('p:spPr/a:xfrm',m.NS));xf.tag=m.q('p','xfrm');gf.append(xf)
    graphic=E.SubElement(gf,m.q('a','graphic'));gd=E.SubElement(graphic,m.q('a','graphicData'),uri=m.NS['p']+'/ole')
    ole=E.SubElement(gd,m.q('p','oleObj'),{m.q('r','id'):'rIdSyntheticOle','name':'Synthetic graph','progId':'Origin95.Graph','imgW':'9144000','imgH':'5143500','showAsIcon':'0'})
    E.SubElement(ole,m.q('p','embed'))
    parent.remove(pic);ole.append(pic);parent.insert(index,gf)
    if shared_picture:
        other=copy.deepcopy(pic)
        other.find('p:nvPicPr/p:cNvPr',m.NS).set('id','99')
        other.find('p:spPr/a:xfrm/a:off',m.NS).set('x','100000')
        other.find('p:spPr/a:xfrm/a:off',m.NS).set('y','100000')
        other.find('p:spPr/a:xfrm/a:ext',m.NS).set('cx','914400')
        other.find('p:spPr/a:xfrm/a:ext',m.NS).set('cy','514350')
        parent.append(other)
    rp=m.rels_part(part);rels=m.xml(pkg.parts[rp]);E.SubElement(rels,m.q('pr','Relationship'),Id='rIdSyntheticOle',Type=m.NS['r']+'/oleObject',Target='../embeddings/syntheticOrigin.bin')
    ct=m.xml(pkg.parts['[Content_Types].xml']);E.SubElement(ct,m.q('ct','Default'),Extension='bin',ContentType='application/vnd.openxmlformats-officedocument.oleObject')
    payload=b'SYNTHETIC NON-EXECUTABLE FIXTURE; NOT A VALID ORIGIN OLE OBJECT\x00'+bytes(range(256))*16
    write_parts(source,output,{part:m.serialize(root),rp:m.serialize(rels),'[Content_Types].xml':m.serialize(ct)},
                {'ppt/embeddings/syntheticOrigin.bin':payload})

class SafePptxTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.d=Path(self.temp.name);self.src=self.d/'source.pptx'
        build_ole_fixture(self.src);self.out=self.d/'output.pptx';self.png=FIX/'after.png';self.svg=FIX/'after.svg'
    def tearDown(self):self.temp.cleanup()
    def run_replace(self,**kw):
        return m.replace(self.src,self.out,1,'ole:0',self.png,acknowledge_stale_ole=True,**kw)
    def test_inventory_distinguishes_ole_and_picture(self):
        r=m.Package(self.src).inspect();o=r['slides'][0]['objects']
        self.assertEqual(len(o),2);self.assertTrue(o[0]['origin_hint']);self.assertFalse(o[0]['origin_verified'])
        self.assertEqual(o[0]['ole']['part'],'ppt/embeddings/syntheticOrigin.bin');self.assertEqual(o[1]['kind'],'picture')
    def test_stale_ack_required(self):
        with self.assertRaisesRegex(ValueError,'Explicit acknowledgment'):m.replace(self.src,self.out,1,'ole:0',self.png)
        self.assertFalse(self.out.exists())
    def test_shared_asset_source_payload_and_slides_preserved(self):
        before=m.Package(self.src);r=self.run_replace();after=m.Package(self.out)
        self.assertTrue(r['source_unchanged']);self.assertTrue(r['embedded_payloads_unchanged']);self.assertTrue(r['existing_relationships_preserved'])
        self.assertEqual(r['unchanged_slides'],[2]);self.assertFalse(r['relationship_errors']);self.assertFalse(r['native_origin_object_edited'])
        a,b=before.inspect()['slides'][0]['objects'],after.inspect()['slides'][0]['objects']
        self.assertNotEqual(a[0]['previews'][0]['raster_or_original']['part'],b[0]['previews'][0]['raster_or_original']['part'])
        self.assertEqual(a[1],b[1]);self.assertFalse(r['removed_parts'])
        for k,v in before.parts.items():
            if k not in r['changed_existing_parts']:self.assertEqual(v,after.parts[k],k)
    def test_svg_plus_png_and_then_png_removes_stale_svg(self):
        r=self.run_replace(svg=self.svg);self.assertTrue(r['vector_svg_included'])
        p=m.Package(self.out);row=p.inspect()['slides'][0]['objects'][0]
        self.assertEqual(len(row['previews'][0]['svg']),1)
        out2=self.d/'output2.pptx';m.replace(self.out,out2,1,'ole:0',self.png,acknowledge_stale_ole=True)
        self.assertEqual(m.Package(out2).inspect()['slides'][0]['objects'][0]['previews'][0]['svg'],[])
    def test_ordinary_picture_requires_no_stale_ack(self):
        r=m.replace(self.src,self.out,2,'picture:0',self.png,svg=self.svg)
        self.assertEqual(r['operation'],'replace_picture');self.assertEqual(r['unchanged_slides'],[1])
    def test_source_and_existing_output_refused(self):
        with self.assertRaises(ValueError):m.replace(self.src,self.src,1,'ole:0',self.png,acknowledge_stale_ole=True)
        self.out.write_bytes(b'untouched')
        with self.assertRaises(ValueError):self.run_replace()
        self.assertEqual(self.out.read_bytes(),b'untouched')
    def test_dangling_symlink_refused(self):
        self.out.symlink_to(self.d/'nonexistent')
        with self.assertRaises(ValueError):self.run_replace()
    def test_wrong_selector_and_slide(self):
        for slide,key in [(0,'ole:0'),(3,'ole:0'),(1,'ole:9')]:
            with self.assertRaises(ValueError):m.replace(self.src,self.out,slide,key,self.png,acknowledge_stale_ole=True)
    def test_external_image_refused(self):
        p=m.Package(self.src);part=p.slides[0];rp=m.rels_part(part);rr=m.xml(p.parts[rp]);rid=p.inspect()['slides'][0]['objects'][0]['previews'][0]['raster_or_original']['id']
        for r in rr:
            if r.get('Id')==rid:r.set('TargetMode','External');r.set('Target','https://example.com/x.png')
        external=self.d/'external.pptx';write_parts(self.src,external,{rp:m.serialize(rr)})
        with self.assertRaisesRegex(ValueError,'embedded image'):m.replace(external,self.out,1,'ole:0',self.png,acknowledge_stale_ole=True)
    def test_alternate_content_refused(self):
        p=m.Package(self.src);part,root=p.slide(1);gf=root.find('.//p:graphicFrame',m.NS);parent=gf.getparent();parent.remove(gf)
        ac=E.SubElement(parent,m.q('mc','AlternateContent'));choice=E.SubElement(ac,m.q('mc','Choice'),Requires='p');choice.append(gf)
        other=self.d/'ac.pptx';write_parts(self.src,other,{part:m.serialize(root)})
        with self.assertRaisesRegex(ValueError,'AlternateContent'):m.replace(other,self.out,1,'ole:0',self.png,acknowledge_stale_ole=True)
    def test_slide_order_not_filename_order(self):
        p=m.Package(self.src);r=m.xml(p.parts['ppt/presentation.xml']);ls=r.find('p:sldIdLst',m.NS);ls[:]=list(ls)[::-1]
        other=self.d/'reordered.pptx';write_parts(self.src,other,{'ppt/presentation.xml':m.serialize(r)})
        self.assertEqual(m.Package(other).inspect()['slides'][0]['objects'][0]['kind'],'picture')
    def test_extract_is_exact_and_exclusive(self):
        out=self.d/'raw.bin';r=m.extract(self.src,'ppt/embeddings/syntheticOrigin.bin',out)
        self.assertEqual(r['sha256'],m.digest(out.read_bytes()))
        with self.assertRaises(FileExistsError):m.extract(self.src,'ppt/embeddings/syntheticOrigin.bin',out)
    def test_signed_presentation_refused(self):
        other=self.d/'signed.pptx';write_parts(self.src,other,adds={'_xmlsignatures/sig1.xml':b'<Signature />'})
        with self.assertRaisesRegex(ValueError,'Signed'):m.replace(other,self.out,1,'ole:0',self.png,acknowledge_stale_ole=True)
    def test_dtd_and_external_svg_refused(self):
        for s in ['<!DOCTYPE svg [<!ENTITY x SYSTEM "file:///etc/passwd">]><svg xmlns="http://www.w3.org/2000/svg">&x;</svg>',
                  '<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
                  '<svg xmlns="http://www.w3.org/2000/svg"><image href="https://example.com/x.png"/></svg>']:
            f=self.d/'bad.svg';f.write_text(s)
            with self.assertRaises(ValueError):m.validate_svg(f)
    def test_bad_png_and_mismatched_aspect_refused(self):
        f=self.d/'bad.png';f.write_bytes(b'not png')
        with self.assertRaises(OSError):m.validate_png(f)
        s=self.d/'bad.svg';s.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 5"/>')
        with self.assertRaisesRegex(ValueError,'aspect ratios'):self.run_replace(svg=s)
    def test_duplicate_zip_name_refused(self):
        other=self.d/'duplicate.pptx';write_parts(self.src,other)
        with zipfile.ZipFile(other,'a') as z:z.writestr('ppt/presentation.xml',b'bad')
        with self.assertRaisesRegex(ValueError,'Duplicate'):m.Package(other)
    def test_missing_internal_relationship_target_refused(self):
        p=m.Package(self.src);part=p.slides[0];rp=m.rels_part(part);root=m.xml(p.parts[rp]);root[0].set('Target','missing.png')
        other=self.d/'broken.pptx';write_parts(self.src,other,{rp:m.serialize(root)})
        with self.assertRaisesRegex(ValueError,'broken internal'):m.replace(other,self.out,1,'ole:0',self.png,acknowledge_stale_ole=True)

if __name__=='__main__':unittest.main(verbosity=2)
