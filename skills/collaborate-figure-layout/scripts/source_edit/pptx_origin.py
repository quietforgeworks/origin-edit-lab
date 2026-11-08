#!/usr/bin/env python3
"""Conservative PPTX picture/Origin-OLE preview operations, never an OLE editor.

Dependencies: lxml; Pillow for replacement PNG validation. No Office/Origin process
is launched. Unmodified package parts retain identical *uncompressed* bytes.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import tempfile
from urllib.parse import unquote, urlsplit
import zipfile
from lxml import etree as E

NS = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'pr': 'http://schemas.openxmlformats.org/package/2006/relationships',
    'ct': 'http://schemas.openxmlformats.org/package/2006/content-types',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
    'v': 'urn:schemas-microsoft-com:vml',
    'o': 'urn:schemas-microsoft-com:office:office',
    'asvg': 'http://schemas.microsoft.com/office/drawing/2016/SVG/main',
}
IMAGE_REL = NS['r'] + '/image'
SVG_EXT = '{96DAC541-7B7A-43D3-8B79-37D633B846F1}'
VERSION = '0.2.0'
MAX_PART = 256 * 1024 * 1024
MAX_TOTAL = 1024 * 1024 * 1024
STALE_WARNING = ('Only the visible preview has changed. The embedded OLE object and its '
                 'Origin data/graph remain unchanged. Opening or refreshing it in Origin '
                 'may restore the old graph. Do not present this as an Origin data edit.')

def q(prefix, name): return '{' + NS[prefix] + '}' + name

def digest(data): return hashlib.sha256(data).hexdigest()

def xml(data):
    # Fail closed on entities/DTDs, including UTF-16 declarations after parsing.
    parser = E.XMLParser(resolve_entities=False, no_network=True, load_dtd=False,
                         remove_blank_text=False, huge_tree=False)
    root = E.fromstring(data, parser)
    if root.getroottree().docinfo.doctype or any(isinstance(n, E._Entity) for n in root.iter()):
        raise ValueError('DTD/entity content is not supported')
    return root

def serialize(root):
    return E.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)

def rels_part(part):
    parent, name = posixpath.split(part)
    return posixpath.join(parent, '_rels', name + '.rels')

def internal_target(part, target):
    # Relationship URLs may use percent escapes. Never fetch external targets.
    u = urlsplit(target)
    if u.scheme or u.netloc or u.query or u.fragment or '\\' in target:
        raise ValueError('Unsupported relationship target')
    value = unquote(u.path)
    result = posixpath.normpath(value.lstrip('/') if value.startswith('/') else
                               posixpath.join(posixpath.dirname(part), value))
    if result == '..' or result.startswith('../') or result.startswith('/'):
        raise ValueError('Relationship escapes package root')
    return result

class Package:
    def __init__(self, path):
        self.path = Path(path).resolve(strict=True)
        if self.path.suffix.lower() != '.pptx':
            raise ValueError('Only .pptx is supported; legacy .ppt and .pptm are not converted')
        self.source_hash = digest(self.path.read_bytes())
        self.parts, self.infos = {}, []
        self._relationship_cache = {}
        with zipfile.ZipFile(self.path) as z:
            infos = z.infolist()
            if len(infos) > 10000 or sum(i.file_size for i in infos) > MAX_TOTAL:
                raise ValueError('Package exceeds safety limits')
            for i in infos:
                name = i.filename
                if name in self.parts or '\\' in name or name.startswith('/') or '..' in PurePosixPath(name).parts:
                    raise ValueError('Duplicate or unsafe ZIP member name')
                if i.file_size > MAX_PART or i.flag_bits & 1:
                    raise ValueError('Oversized or encrypted ZIP part')
                if i.compress_size and i.file_size / i.compress_size > 2000:
                    raise ValueError('Suspicious ZIP expansion ratio')
                self.parts[name] = z.read(i)
                self.infos.append(i)
            self.comment = z.comment
        for required in ['[Content_Types].xml', 'ppt/presentation.xml', 'ppt/_rels/presentation.xml.rels']:
            if required not in self.parts:
                raise ValueError('Missing required presentation part: ' + required)
        self.presentation = xml(self.parts['ppt/presentation.xml'])
        if self.presentation.tag != q('p','presentation'):
            raise ValueError('Strict/unknown OOXML namespace is not supported')
        rels = self.relationships('ppt/presentation.xml')
        self.slides = []
        for s in self.presentation.findall('p:sldIdLst/p:sldId', NS):
            rid = s.get(q('r','id'))
            r = rels.get(rid)
            if not r or r['external'] or not r['type'].endswith('/slide') or r['part'] not in self.parts:
                raise ValueError('Invalid presentation slide relationship')
            self.slides.append(r['part'])
        if len(set(self.slides)) != len(self.slides):
            raise ValueError('Duplicate slide part references are unsupported')

    def relationships(self, part):
        if part in self._relationship_cache: return self._relationship_cache[part]
        rp = rels_part(part)
        if rp not in self.parts: return {}
        root = xml(self.parts[rp]); result = {}
        if root.tag != q('pr','Relationships'): raise ValueError('Invalid relationship namespace')
        for r in root:
            rid = r.get('Id')
            if not rid or rid in result: raise ValueError('Missing or duplicate relationship ID')
            external = r.get('TargetMode') == 'External'
            target = r.get('Target', '')
            result[rid] = {'id': rid, 'target': target, 'type': r.get('Type',''),
                           'external': external, 'part': None if external else internal_target(part, target)}
        self._relationship_cache[part]=result
        return result

    def slide(self, number):
        if type(number) is not int or not 1 <= number <= len(self.slides):
            raise ValueError('Slide number is 1-based and must exist')
        name = self.slides[number-1]
        return name, xml(self.parts[name])

    def asset(self, rel):
        if not rel: return None
        out = dict(rel)
        if not rel['external']:
            data = self.parts.get(rel['part'])
            out.update(exists=data is not None, sha256=None if data is None else digest(data),
                       bytes=None if data is None else len(data))
            if data is not None:
                out['container_hint'] = ('compound_file' if data.startswith(bytes.fromhex('D0CF11E0A1B11AE1'))
                                         else 'origin_header' if data.startswith((b'CPYA', b'CPYUA')) else 'unclassified')
        return out

    def nodes(self, root):
        rows = []; seen = set()
        for ole in root.findall('.//p:oleObj', NS):
            ac = next((a for a in ole.iterancestors() if a.tag == q('mc','AlternateContent')), None)
            if ac is not None:
                if ac in seen: continue
                seen.add(ac)
                # A single key represents the logical object, never discard its fallback.
                members=ac.findall('.//p:oleObj',NS)
                representative=next((n for n in members if n.findall('.//p:pic',NS)), ole)
                pics=ac.findall('.//p:pic',NS)
            else: representative=ole;pics=ole.findall('.//p:pic',NS)
            rows.append((f'ole:{len(rows)}', representative, pics))
        pics = [p for p in root.findall('.//p:pic', NS)
                if not any(a.tag == q('p','oleObj') for a in p.iterancestors())]
        rows += [(f'picture:{i}', p, [p]) for i,p in enumerate(pics)]
        return rows

    def paired_vml(self, part, node):
        """Resolve only the specific legacy VML-choice + DrawingML-fallback pattern.

        Keep the VML cache and DrawingML cache synchronized. A shared VML part is
        rejected instead of changing another slide implicitly.
        """
        ac=next((a for a in node.iterancestors() if a.tag==q('mc','AlternateContent')),None)
        if ac is None: return None
        choices=ac.findall('mc:Choice',NS);fallbacks=ac.findall('mc:Fallback',NS)
        if len(choices)!=1 or len(fallbacks)!=1 or len(ac)!=2:
            raise ValueError('Unsupported AlternateContent branches')
        choice,fallback=choices[0],fallbacks[0]
        req=choice.get('Requires','').split()
        if len(req)!=1 or choice.nsmap.get(req[0])!=NS['v']:
            raise ValueError('AlternateContent is not the supported VML choice')
        a=choice.findall('p:oleObj',NS);b=fallback.findall('p:oleObj',NS)
        if len(a)!=1 or len(b)!=1 or len(choice)!=1 or len(fallback)!=1:
            raise ValueError('AlternateContent must represent one OLE object')
        a,b=a[0],b[0]
        if (not a.get('spid') or a.get(q('r','id'))!=b.get(q('r','id')) or
            a.get('progId')!=b.get('progId') or a.find('p:embed',NS) is None or
            b.find('p:embed',NS) is None or a.findall('.//p:pic',NS) or len(b.findall('p:pic',NS))!=1):
            raise ValueError('Inconsistent VML and DrawingML OLE branches')
        candidates=[r for r in self.relationships(part).values() if r['type']==NS['r']+'/vmlDrawing']
        if len(candidates)!=1 or candidates[0]['external']:
            raise ValueError('Expected one internal VML drawing relationship')
        vp=candidates[0]['part']
        owners=[]
        for name in self.parts:
            if '/_rels/' in name and name.endswith('.rels'):
                parent,base=name.rsplit('/_rels/',1);owner=parent+'/'+base[:-5]
                for r in self.relationships(owner).values():
                    if not r['external'] and r['part']==vp: owners.append(owner)
        if owners!=[part]: raise ValueError('Shared VML drawing requires a separate clone operation')
        vr=xml(self.parts[vp]);shapes=vr.findall('.//v:shape',NS)
        shapes=[sh for sh in shapes if sh.get('id')==a.get('spid')]
        if len(shapes)!=1: raise ValueError('VML shape ID must resolve uniquely')
        images=shapes[0].findall('v:imagedata',NS)
        if len(images)!=1: raise ValueError('Expected one VML image data entry')
        image=images[0];attribute=q('o','relid') if image.get(q('o','relid')) else q('r','id')
        rid=image.get(attribute);rel=self.relationships(vp).get(rid)
        if not rel or rel['external'] or rel['type']!=IMAGE_REL:
            raise ValueError('VML image relationship must be internal')
        fallback_blips=b.findall('p:pic/p:blipFill/a:blip',NS)
        if len(fallback_blips)!=1: raise ValueError('Expected one DrawingML fallback blip')
        fallback_rel=self.relationships(part).get(fallback_blips[0].get(q('r','embed')))
        if not fallback_rel or fallback_rel['part']!=rel['part']:
            raise ValueError('VML and DrawingML already have different preview assets')
        return {'part':vp,'root':vr,'image':image,'attribute':attribute,'relationship':rel}

    def inspect(self):
        result = {'version': VERSION, 'file': self.path.name, 'sha256': self.source_hash,
                  'slide_count':len(self.slides), 'origin_native_edit_supported':False, 'slides':[]}
        for i, part in enumerate(self.slides, 1):
            _, root = self.slide(i); rels = self.relationships(part); objects = []
            for key, node, pics in self.nodes(root):
                ole = key.startswith('ole:')
                owner = next((a for a in node.iterancestors() if a.tag == q('p','graphicFrame')), node)
                props = owner.find('.//p:cNvPr', NS)
                origin = bool(re.match(r'^Origin(?:Lab)?(?:\d+)?[.\s]', node.get('progId',''), re.I)) if ole else False
                row = {'key':key,'kind':'ole' if ole else 'picture', 'name':None if props is None else props.get('name'),
                       'shape_id':None if props is None else props.get('id'), 'origin_hint':origin,
                       'origin_verified':False, 'prog_id':node.get('progId') if ole else None,
                       'alternate_content': any(a.tag == q('mc','AlternateContent') for a in node.iterancestors()),
                       'previews':[]}
                if ole: row['ole'] = self.asset(rels.get(node.get(q('r','id'))))
                for pic in pics:
                    for blip in pic.findall('p:blipFill/a:blip', NS):
                        row['previews'].append({'raster_or_original':self.asset(rels.get(blip.get(q('r','embed')) or blip.get(q('r','link')))),
                          'svg':[self.asset(rels.get(s.get(q('r','embed')) or s.get(q('r','link')))) for s in blip.findall('.//asvg:svgBlip',NS)]})
                try:
                    vml=self.paired_vml(part,node) if ole else None
                    row['vml_preview']=self.asset(vml['relationship']) if vml else None
                    row['paired_preview_supported']=vml is not None
                    ac_supported=not row['alternate_content'] or vml is not None
                except ValueError as exc:
                    row['paired_preview_supported']=False; row['unsupported_reason']=str(exc);ac_supported=False
                row['safe_replace_supported'] = (len(pics) == 1 and len(row['previews']) == 1
                    and ac_supported and row['previews'][0]['raster_or_original'] is not None
                    and not row['previews'][0]['raster_or_original']['external']
                    and row['previews'][0]['raster_or_original'].get('exists',False)
                    and row['previews'][0]['raster_or_original']['type']==IMAGE_REL)
                objects.append(row)
            result['slides'].append({'number':i,'part':part,'objects':objects,
                                     'native_chart_count':len(root.xpath('//*[local-name()="chart"]'))})
        return result

    def verify_relationships(self):
        issues=[]
        for part in self.parts:
            if not part.endswith('.rels'): continue
            if part == '_rels/.rels': owner = ''
            elif '/_rels/' in part:
                a,b=part.rsplit('/_rels/',1); owner=a+'/'+b[:-5]
            else: continue
            for r in self.relationships(owner).values():
                if not r['external'] and r['part'] not in self.parts:
                    issues.append({'part':part, 'id':r['id'], 'missing':r['part']})
        return issues

def validate_png(path):
    from PIL import Image
    data = Path(path).read_bytes()
    if len(data) > MAX_PART: raise ValueError('PNG too large')
    with Image.open(io.BytesIO(data)) as im:
        if im.format != 'PNG': raise ValueError('Replacement fallback must be a real PNG')
        size = im.size
        if max(size) > 32000 or size[0]*size[1] > 80000000: raise ValueError('PNG dimensions too large')
        im.verify()
    return data, size

def validate_svg(path):
    data = Path(path).read_bytes()
    if len(data) > 32*1024*1024: raise ValueError('SVG too large')
    root = xml(data)
    if root.tag != '{http://www.w3.org/2000/svg}svg': raise ValueError('Not an SVG document')
    for n in root.iter():
        if not isinstance(n.tag,str): continue
        if E.QName(n).localname in {'script','foreignObject','iframe','object','embed','audio','video','animate','animateMotion','animateTransform','set'}:
            raise ValueError('Active/animated SVG content is unsupported')
        for key,value in n.attrib.items():
            local = E.QName(key).localname.lower()
            if local=='base': raise ValueError('SVG xml:base is unsupported')
            if local.startswith('on'): raise ValueError('SVG event handlers are unsupported')
            if local in {'href','src'} and value and not value.startswith('#'):
                raise ValueError('External or embedded-resource SVG references are unsupported')
        css = ' '.join([*n.attrib.values(), n.text or '' if E.QName(n).localname=='style' else ''])
        if '\\' in css or '/*' in css or '@' in css:
            raise ValueError('Escaped, imported, or commented SVG CSS is unsupported')
        if '@import' in css.lower() or any(not u.strip(' \"\'').startswith('#') for u in re.findall(r'url\((.*?)\)',css,re.I)):
            raise ValueError('External CSS resources are unsupported')
    viewbox = root.get('viewBox')
    if viewbox:
        vals = [float(v) for v in re.split(r'[\s,]+',viewbox.strip())]
        if len(vals)!=4 or vals[2]<=0 or vals[3]<=0: raise ValueError('Invalid SVG viewBox')
        ratio=vals[2]/vals[3]
    else: ratio=None
    return data, ratio

def output_path(source, target):
    p = Path(target).absolute()
    if p.is_symlink() or p.exists(): raise ValueError('Refusing to overwrite an existing output or symlink')
    p = p.parent.resolve(strict=True) / p.name
    if p == source: raise ValueError('Refusing to overwrite the source')
    if p.suffix.lower() != '.pptx': raise ValueError('Output must have .pptx suffix')
    return p

def save_package(pkg, changes, additions, target):
    out = output_path(pkg.path, target)
    fd, tmp = tempfile.mkstemp(prefix='.pptx-origin-', suffix='.tmp', dir=out.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            with zipfile.ZipFile(stream,'w') as z:
                z.comment = pkg.comment
                for info in pkg.infos: z.writestr(info, changes.get(info.filename,pkg.parts[info.filename]))
                for name, data in additions.items(): z.writestr(name,data,compress_type=zipfile.ZIP_DEFLATED)
            stream.flush(); os.fsync(stream.fileno())
        if digest(pkg.path.read_bytes()) != pkg.source_hash:
            raise ValueError('Source changed during operation; refusing to publish output')
        os.link(tmp, out) # Atomic, fails if another process created the output.
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
    return out

def compare_packages(source, output):
    a,b=Package(source),Package(output)
    old,new=set(a.parts),set(b.parts)
    changed=sorted(k for k in old & new if a.parts[k] != b.parts[k])
    embedded=sorted(k for k in old if k.startswith('ppt/embeddings/'))
    return {'source_sha256':a.source_hash,'output_sha256':b.source_hash,
            'changed_existing_parts':changed,'added_parts':sorted(new-old),'removed_parts':sorted(old-new),
            'unchanged_existing_parts':len(old&new)-len(changed),
            'embedded_payloads_unchanged':all(k in b.parts and a.parts[k]==b.parts[k] for k in embedded),
            'embedded_payload_count':len(embedded),
            'unchanged_slides':[i for i,p in enumerate(a.slides,1) if p in b.parts and a.parts[p]==b.parts[p]],
            'relationship_errors':b.verify_relationships(),
            'powerpoint_reopen_verified':False,'origin_reopen_verified':False}

def replace(source, output, slide, key, png, *, svg=None, acknowledge_stale_ole=False):
    pkg=Package(source); part,root=pkg.slide(slide)
    if any(k.startswith('_xmlsignatures/') for k in pkg.parts):
        raise ValueError('Signed presentations are not edited because this invalidates signatures')
    if pkg.verify_relationships(): raise ValueError('Source package has broken internal relationships')
    matches=[x for x in pkg.nodes(root) if x[0]==key]
    if len(matches)!=1: raise ValueError('Object key must resolve uniquely; run inspect first')
    _,node,pics=matches[0]; isole=key.startswith('ole:')
    if isole and not acknowledge_stale_ole:
        raise ValueError(STALE_WARNING+' Explicit acknowledgment is required.')
    vml=pkg.paired_vml(part,node) if isole else None
    if not isole and any(a.tag==q('mc','AlternateContent') for a in node.iterancestors()):
        raise ValueError('AlternateContent pictures require a paired-branch editor')
    if len(pics)!=1: raise ValueError('Exactly one direct preview picture is required')
    blips=pics[0].findall('p:blipFill/a:blip',NS)
    if len(blips)!=1: raise ValueError('Exactly one image blip is required')
    blip=blips[0]; rels=pkg.relationships(part)
    oldrid=blip.get(q('r','embed'))
    if not oldrid or oldrid not in rels or rels[oldrid]['external'] or rels[oldrid]['type']!=IMAGE_REL:
        raise ValueError('Only embedded image relationships can be replaced')
    pngdata,size=validate_png(png)
    svgdata,svgratio=validate_svg(svg) if svg else (None,None)
    if svgratio and abs((size[0]/size[1])/svgratio-1)>0.01:
        raise ValueError('SVG and fallback PNG aspect ratios differ by over 1%')
    rp=rels_part(part); rroot=xml(pkg.parts[rp]); additions={}; changes={}
    # Clone both media parts and relationships: assets/RIDs can be shared by other shapes/slides.
    def add_asset(data,ext,owner=part,relroot=rroot,asset_name=None):
        n=1
        if asset_name: name=asset_name
        else:
            while (name:=f'ppt/media/origin_edit_{n}.{ext}') in pkg.parts or name in additions: n+=1
        ridn=1
        used={r.get('Id') for r in relroot}
        while (rid:=f'rIdOriginEdit{ridn}') in used: ridn+=1
        E.SubElement(relroot,q('pr','Relationship'),Id=rid,Type=IMAGE_REL,
                     Target=posixpath.relpath(name,posixpath.dirname(owner)))
        additions[name]=data
        return rid
    blip.set(q('r','embed'),add_asset(pngdata,'png'))
    png_part=next(iter(additions))
    if vml:
        vp=vml['part'];vrp=rels_part(vp);vrr=xml(pkg.parts[vrp])
        vrid=add_asset(pngdata,'png',owner=vp,relroot=vrr,asset_name=png_part)
        vml['image'].set(vml['attribute'],vrid)
        changes[vp]=serialize(vml['root']);changes[vrp]=serialize(vrr)
    # Remove only old SVG extension entries, not other image processing metadata.
    for oldsvg in list(blip.findall('.//asvg:svgBlip',NS)):
        parent=oldsvg.getparent(); parent.remove(oldsvg)
        if parent.tag==q('a','ext') and len(parent)==0: parent.getparent().remove(parent)
    if svgdata:
        extlst=blip.find('a:extLst',NS)
        if extlst is None: extlst=E.SubElement(blip,q('a','extLst'))
        ext=E.SubElement(extlst,q('a','ext'),uri=SVG_EXT)
        E.SubElement(ext,q('asvg','svgBlip'),{q('r','embed'):add_asset(svgdata,'svg')},nsmap={'asvg':NS['asvg']})
    changes[part]=serialize(root); changes[rp]=serialize(rroot)
    ct=xml(pkg.parts['[Content_Types].xml']); modified=False
    for ext,mime in [('png','image/png')]+([('svg','image/svg+xml')] if svgdata else []):
        existing=[x for x in ct if x.get('Extension','').lower()==ext]
        if existing and any(x.get('ContentType')!=mime for x in existing):
            raise ValueError('Conflicting content type for '+ext)
        if not existing:
            E.SubElement(ct,q('ct','Default'),Extension=ext,ContentType=mime); modified=True
    if modified: changes['[Content_Types].xml']=serialize(ct)
    out=save_package(pkg,changes,additions,output)
    report=compare_packages(pkg.path,out)
    allowed={part,rp,'[Content_Types].xml'} | ({vml['part'],rels_part(vml['part'])} if vml else set())
    if (set(report['changed_existing_parts'])-allowed or report['removed_parts'] or
        not report['embedded_payloads_unchanged'] or report['relationship_errors']):
        raise RuntimeError('Post-write verification failed; do not use output: '+str(out))
    report.update(operation='replace_ole_preview' if isole else 'replace_picture', slide=slide, object_key=key,
                  source_unchanged=digest(pkg.path.read_bytes())==pkg.source_hash,
                  native_origin_object_edited=False, visual_review_verified=False,
                  png_dimensions=list(size),vector_svg_included=bool(svgdata),
                  paired_vml_preview_updated=bool(vml),
                  warning=STALE_WARNING if isole else 'Picture pixels/vector changed; no underlying Origin data was edited.')
    # Prove all pre-existing relationship definitions remain unchanged, even shared assets.
    after=Package(out)
    report['existing_relationships_preserved']=all(
        pkg.relationships(p)=={k:v for k,v in after.relationships(p).items() if k in pkg.relationships(p)}
        for p in pkg.slides+([vml['part']] if vml else []))
    return report

def extract(source, part, output):
    pkg=Package(source)
    if not part.startswith(('ppt/media/','ppt/embeddings/')) or part not in pkg.parts:
        raise ValueError('Choose an existing ppt/media or ppt/embeddings part from inspection')
    target=Path(output)
    with target.open('xb') as f: f.write(pkg.parts[part])
    return {'part':part,'output':str(target),'sha256':digest(pkg.parts[part]),
            'note':'Raw package part only. OLE .bin is not automatically an OPJ/OPJU project.'}

def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='command',required=True)
    i=sub.add_parser('inspect'); i.add_argument('source')
    r=sub.add_parser('replace'); r.add_argument('source'); r.add_argument('output');r.add_argument('--slide',type=int,required=True)
    r.add_argument('--object',dest='key',required=True);r.add_argument('--png',required=True);r.add_argument('--svg')
    r.add_argument('--acknowledge-stale-ole',action='store_true')
    e=sub.add_parser('extract');e.add_argument('source');e.add_argument('--part',required=True);e.add_argument('--output',required=True)
    c=sub.add_parser('verify');c.add_argument('source');c.add_argument('output')
    args=vars(p.parse_args());cmd=args.pop('command')
    try:
        if cmd=='inspect': result=Package(args['source']).inspect()
        elif cmd=='replace': result=replace(**args)
        elif cmd=='extract': result=extract(**args)
        else: result=compare_packages(**args)
    except (ValueError, OSError, zipfile.BadZipFile, E.XMLSyntaxError) as exc:
        p.exit(2,'Error: '+str(exc)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
