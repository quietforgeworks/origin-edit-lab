"""Build tiny synthetic OOXML/PNG/SVG test inputs. Contains no Origin data.

The minimal OOXML envelope tests package logic, not Office interoperability.
All files are generated locally; nothing is downloaded.
"""
from pathlib import Path
import io
import zipfile
from PIL import Image

HERE = Path(__file__).resolve().parent / 'fixtures'

def build():
    HERE.mkdir(exist_ok=True)
    png = io.BytesIO()
    Image.new('RGB', (640, 360), '#f0f0ff').save(png, format='PNG')
    p = 'http://schemas.openxmlformats.org/presentationml/2006/main'
    a = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    r = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    pr = 'http://schemas.openxmlformats.org/package/2006/relationships'
    ct = 'http://schemas.openxmlformats.org/package/2006/content-types'
    presentation = f'<p:presentation xmlns:p="{p}" xmlns:r="{r}"><p:sldIdLst><p:sldId id="256" r:id="s1"/><p:sldId id="257" r:id="s2"/></p:sldIdLst><p:sldSz cx="12192000" cy="6858000"/></p:presentation>'
    slide = f'''<p:sld xmlns:p="{p}" xmlns:a="{a}" xmlns:r="{r}"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/><p:pic><p:nvPicPr><p:cNvPr id="2" name="Synthetic image"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed="img"/><a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr><a:xfrm><a:off x="1524000" y="1428750"/><a:ext cx="9144000" cy="5143500"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic></p:spTree></p:cSld></p:sld>'''
    parts = {
        '[Content_Types].xml': f'<Types xmlns="{ct}"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>' + ''.join(f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>' for i in [1,2]) + '</Types>',
        '_rels/.rels': f'<Relationships xmlns="{pr}"><Relationship Id="main" Type="{r}/officeDocument" Target="ppt/presentation.xml"/></Relationships>',
        'ppt/presentation.xml': presentation,
        'ppt/_rels/presentation.xml.rels': f'<Relationships xmlns="{pr}"><Relationship Id="s1" Type="{r}/slide" Target="slides/slide1.xml"/><Relationship Id="s2" Type="{r}/slide" Target="slides/slide2.xml"/></Relationships>',
        'ppt/media/image1.png': png.getvalue(),
        'ppt/media/image2.png': png.getvalue(),
    }
    for i in [1,2]:
        parts[f'ppt/slides/slide{i}.xml'] = slide
        parts[f'ppt/slides/_rels/slide{i}.xml.rels'] = f'<Relationships xmlns="{pr}"><Relationship Id="img" Type="{r}/image" Target="../media/image{i}.png"/></Relationships>'
    with zipfile.ZipFile(HERE/'baseline.pptx', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, value in parts.items():
            info = zipfile.ZipInfo(name, (2020,1,1,0,0,0)); info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, value)
    Image.new('RGB',(640,360),'#fff0f0').save(HERE/'after.png')
    (HERE/'after.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360"><rect width="640" height="360" fill="#fff0f0"/><path d="M 20,320 L 300,40 L 620,200" fill="none" stroke="red"/></svg>\n')

if __name__ == '__main__':
    build()
