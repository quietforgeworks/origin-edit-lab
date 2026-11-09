"""Normalize one reviewed slide's Origin OLE display branches, never its payload.

This is not a layout writer, cache image generator, or Origin activation test.
"""
from pathlib import Path
import argparse, copy, hashlib, io, json, posixpath, zipfile
from lxml import etree as ET

P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
MC='http://schemas.openxmlformats.org/markup-compatibility/2006'
NS={'p':P,'a':A,'r':R,'mc':MC}
PARSER=ET.XMLParser(resolve_entities=False,no_network=True)
def fail(message): raise ValueError(message)
def digest(data): return hashlib.sha256(data).hexdigest()
def signature(node):
    return (node.tag, tuple(sorted(node.attrib.items())), (node.text or '').strip(), tuple(signature(c) for c in node))
def common_signature(ole):
    clone=copy.deepcopy(ole)
    for pic in clone.findall('p:pic',NS): clone.remove(pic)
    return signature(clone)
def frames_match(frame,pic):
    host=frame.find('p:xfrm',NS); preview=pic.find('p:spPr/a:xfrm',NS)
    if host is None or preview is None or host.attrib!=preview.attrib:fail('OLE host and preview transform attributes differ')
    for name in ('off','ext'):
        a=frame.find('p:xfrm/a:'+name,NS); b=pic.find('p:spPr/a:xfrm/a:'+name,NS)
        if a is None or b is None or a.attrib!=b.attrib:fail('OLE host and preview frames differ; fix approved geometry before normalization')
def normalize(source, output, expected_sha256, slide_part):
    source,output=Path(source),Path(output)
    if source.resolve()==output.resolve():fail('Output must differ from source')
    if output.exists():fail('Output exists; use a new revision')
    data=source.read_bytes()
    if digest(data)!=expected_sha256:fail('Source hash mismatch; rebind the reviewed input')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if len(z.namelist())!=len(set(z.namelist())):fail('Duplicate ZIP members')
        infos=z.infolist(); parts={i.filename:z.read(i.filename) for i in infos}
    if not slide_part.startswith('ppt/slides/slide') or not slide_part.endswith('.xml') or slide_part not in parts:fail('Select an existing exact slide part')
    root=ET.fromstring(parts[slide_part],PARSER)
    relpart=posixpath.join(posixpath.dirname(slide_part),'_rels',posixpath.basename(slide_part)+'.rels')
    relroot=ET.fromstring(parts[relpart],PARSER)
    rels={x.get('Id'):x for x in relroot}
    if len(rels)!=len(relroot) or None in rels:fail('Duplicate or missing relationship IDs')
    def local_relationship(rid,kind):
        rel=rels.get(rid)
        if rel is None or rel.get('TargetMode')=='External' or not rel.get('Type','').endswith('/'+kind):fail('Missing or unexpected local '+kind+' relationship')
        target=posixpath.normpath(posixpath.join(posixpath.dirname(slide_part),rel.get('Target','')))
        if target not in parts:fail('Relationship target missing')
        return target
    normalized=0; checked=[]
    for frame in root.findall('.//p:graphicFrame',NS):
        gd=frame.find('a:graphic/a:graphicData',NS)
        if gd is None:continue
        oles=gd.findall('.//p:oleObj',NS)
        if not oles:continue
        if any(not x.get('progId','').startswith('Origin') for x in oles):continue
        alt=gd.find('mc:AlternateContent',NS)
        if alt is not None:
            if len(gd)!=1:fail('Unexpected graphicData siblings')
            if len(alt.findall('mc:Fallback',NS))!=1:fail('Exactly one fallback is required')
            fb=alt.find('mc:Fallback',NS)
            if fb is None or len(fb)!=1 or fb[0].tag!='{'+P+'}oleObj':fail('Unsupported fallback')
            chosen=fb[0]
            if len(chosen.findall('p:pic',NS))!=1:fail('Exactly one explicit fallback preview is required')
            if any(c.tag not in ('{'+MC+'}Choice','{'+MC+'}Fallback') for c in alt):fail('Unknown compatibility branch')
            common=common_signature(chosen)
            if not alt.findall('mc:Choice',NS):fail('Missing choice')
            if list(alt)[-1] is not fb:fail('Fallback must follow all choices')
            for choice in alt.findall('mc:Choice',NS):
                if len(choice)!=1 or choice[0].tag!=chosen.tag or common_signature(choice[0])!=common:fail('Divergent OLE branches; manual review required')
                if len(choice[0].findall('p:pic',NS))>1:fail('Multiple choice previews')
                cp=choice[0].find('p:pic',NS)
                if cp is not None and signature(cp)!=signature(chosen.find('p:pic',NS)):fail('Divergent branch previews; manual review required')
        else:
            if len(gd)!=1 or gd[0].tag!='{'+P+'}oleObj':fail('Unsupported direct OLE container')
            chosen=gd[0]
        if chosen.find('p:embed',NS) is None or chosen.find('p:link',NS) is not None:fail('Embedded objects only')
        pics=chosen.findall('p:pic',NS)
        if len(pics)!=1:fail('Exactly one explicit preview is required')
        pic=pics[0];frames_match(frame,pic)
        blip=pic.find('p:blipFill/a:blip',NS)
        if blip is None or blip.get('{'+R+'}link'):fail('Missing or linked preview')
        binary=local_relationship(chosen.get('{'+R+'}id'),'oleObject')
        preview=local_relationship(blip.get('{'+R+'}embed'),'image')
        checked.append({'shape_id':frame.find('p:nvGraphicFramePr/p:cNvPr',NS).get('id'),'binary_part':binary,'binary_sha256':digest(parts[binary]),'preview_part':preview})
        if alt is not None:
            gd.replace(alt,copy.deepcopy(chosen));normalized+=1
    if not checked:fail('No supported Origin objects selected')
    revised=ET.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True) if normalized else parts[slide_part]
    # All payload, media, relationships and unselected slides remain byte-identical.
    output.parent.mkdir(parents=True,exist_ok=True)
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w') as z:
        for info in infos:z.writestr(info,revised if info.filename==slide_part else parts[info.filename])
    with zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as z:
        if any(z.read(n)!=b for n,b in parts.items() if n!=slide_part):fail('Unexpected package modification')
    created=False
    try:
        with output.open('xb') as handle:
            created=True
            handle.write(buffer.getvalue())
    except BaseException:
        if created:output.unlink(missing_ok=True)
        raise
    return {'normalized_objects':normalized,'checked_objects':checked,'source_sha256':expected_sha256,'output_sha256':digest(output.read_bytes()),'changed_parts':[slide_part] if normalized else [],'payloads_and_relationships_unchanged':True,'host_display':'NOT_TESTED_BY_THIS_SCRIPT','origin_activation':'NOT_TESTED','origin_update_stability':'NOT_TESTED'}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source');p.add_argument('output');p.add_argument('--expected-sha256',required=True);p.add_argument('--slide-part',required=True);a=p.parse_args()
    print(json.dumps(normalize(a.source,a.output,a.expected_sha256,a.slide_part),indent=2))
if __name__=='__main__':main()
