"""Generate tiny package-envelope fixtures, not Origin data or Office compatibility evidence.

No scientific/user images, downloaded decks or application processes are used.
The minimal PPTX exercises the package editor; its app-open validity is not claimed.
"""
from pathlib import Path
import atexit
import io
import tempfile
import zipfile

from lxml import etree as E
from PIL import Image, ImageDraw
import pptx_origin as m

SVG = '''<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">
<rect id="background" width="640" height="360" fill="white"/>
<path id="curve" d="M 40,280 L 160,220 L 300,240 L 460,100 L 600,60" fill="none" stroke="#1262aa" stroke-width="4"/>
<text id="label" x="80" y="325" font-family="sans-serif" font-size="18">Synthetic A</text>
</svg>'''


def png_bytes(color='#1262aa', width=4):
    """A known synthetic primitive fallback, not a general SVG rasterizer."""
    im = Image.new('RGB', (640, 360), 'white')
    draw = ImageDraw.Draw(im)
    draw.line([(40, 280), (160, 220), (300, 240), (460, 100), (600, 60)], fill=color, width=width)
    draw.text((80, 315), 'Synthetic A', fill='black')
    out = io.BytesIO(); im.save(out, format='PNG'); return out.getvalue()


def make_fixture_files(folder):
    folder = Path(folder)
    (folder / 'after.png').write_bytes(png_bytes('#dd3322', 6))
    (folder / 'after.svg').write_text(SVG.replace('#1262aa', '#dd3322').replace('stroke-width="4"', 'stroke-width="6"'), encoding='utf-8')
    ct = E.Element(m.q('ct', 'Types'), nsmap={None: m.NS['ct']})
    for ext, mime in [('rels', 'application/vnd.openxmlformats-package.relationships+xml'), ('xml', 'application/xml'), ('png', 'image/png')]:
        E.SubElement(ct, m.q('ct', 'Default'), Extension=ext, ContentType=mime)
    E.SubElement(ct, m.q('ct', 'Override'), PartName='/ppt/presentation.xml', ContentType='application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml')
    presentation = E.Element(m.q('p', 'presentation'), nsmap={'p': m.NS['p'], 'r': m.NS['r']})
    ids = E.SubElement(presentation, m.q('p', 'sldIdLst'))
    rels = E.Element(m.q('pr', 'Relationships'), nsmap={None: m.NS['pr']})
    parts = {'ppt/media/synthetic.png': png_bytes()}
    for number in (1, 2):
        part = f'ppt/slides/slide{number}.xml'
        E.SubElement(ids, m.q('p', 'sldId'), {'id': str(255 + number), m.q('r', 'id'): f'rId{number}'})
        E.SubElement(rels, m.q('pr', 'Relationship'), Id=f'rId{number}', Type=m.NS['r'] + '/slide', Target=f'slides/slide{number}.xml')
        E.SubElement(ct, m.q('ct', 'Override'), PartName='/' + part, ContentType='application/vnd.openxmlformats-officedocument.presentationml.slide+xml')
        slide = E.Element(m.q('p', 'sld'), nsmap={'p': m.NS['p'], 'a': m.NS['a'], 'r': m.NS['r']})
        tree = E.SubElement(E.SubElement(slide, m.q('p', 'cSld')), m.q('p', 'spTree'))
        pic = E.SubElement(tree, m.q('p', 'pic'))
        nv = E.SubElement(pic, m.q('p', 'nvPicPr'))
        E.SubElement(nv, m.q('p', 'cNvPr'), id='2', name='Synthetic preview')
        E.SubElement(nv, m.q('p', 'cNvPicPr')); E.SubElement(nv, m.q('p', 'nvPr'))
        fill = E.SubElement(pic, m.q('p', 'blipFill'))
        E.SubElement(fill, m.q('a', 'blip'), {m.q('r', 'embed'): 'rIdImage'})
        E.SubElement(E.SubElement(fill, m.q('a', 'stretch')), m.q('a', 'fillRect'))
        props = E.SubElement(pic, m.q('p', 'spPr'))
        xf = E.SubElement(props, m.q('a', 'xfrm'))
        E.SubElement(xf, m.q('a', 'off'), x='0', y='0')
        E.SubElement(xf, m.q('a', 'ext'), cx='9144000', cy='5143500')
        geom = E.SubElement(props, m.q('a', 'prstGeom'), prst='rect')
        E.SubElement(geom, m.q('a', 'avLst'))
        # A separate native text node is protected from a preview-only edit.
        shape = E.SubElement(tree, m.q('p', 'sp'))
        text = E.SubElement(E.SubElement(E.SubElement(shape, m.q('p', 'txBody')), m.q('a', 'p')), m.q('a', 'r'))
        E.SubElement(text, m.q('a', 'rPr'), b='1', baseline='-25000')
        E.SubElement(text, m.q('a', 't')).text = 'Unchanged synthetic H₂O  Ω'
        sr = E.Element(m.q('pr', 'Relationships'), nsmap={None: m.NS['pr']})
        E.SubElement(sr, m.q('pr', 'Relationship'), Id='rIdImage', Type=m.IMAGE_REL, Target='../media/synthetic.png')
        parts[part] = m.serialize(slide); parts[m.rels_part(part)] = m.serialize(sr)
    parts['[Content_Types].xml'] = m.serialize(ct)
    parts['ppt/presentation.xml'] = m.serialize(presentation)
    parts['ppt/_rels/presentation.xml.rels'] = m.serialize(rels)
    with zipfile.ZipFile(folder / 'baseline.pptx', 'x', zipfile.ZIP_DEFLATED) as archive:
        for name, data in parts.items(): archive.writestr(name, data)
    return folder


def fixture_directory():
    temporary = tempfile.TemporaryDirectory(prefix='synthetic-source-edit-')
    atexit.register(temporary.cleanup)
    return make_fixture_files(temporary.name)
