"""Independent numeric checks of actual official app observations and app saves.

No Origin parser/writer is imported. Expectations derive only from untouched raw
synthetic JSON. Separate source audits are run by verify_source.py.
"""
from pathlib import Path
import argparse,base64,collections,copy,csv,hashlib,io,json,lzma,struct,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parent
APP=ROOT/'application/results'
def need(ok,msg):
    if not ok:raise RuntimeError(msg)
def bits(v):return struct.pack('>d',float(v)).hex()
def sha(b):return hashlib.sha256(b).hexdigest()
def load(name):
    raw=(APP/name/'imported-application.lml').read_bytes()
    return E.fromstring(lzma.decompress(raw) if raw.startswith(b'\xfd7zXZ\x00') else raw)
def normalized(e):
    a=copy.deepcopy(e)
    for v in a.iter():
        for k in ('uuid','creation_time'):v.attrib.pop(k,None)
    return a
def diff(a,b,path='/project'):
    out=[]
    if a.tag!=b.tag:out.append(path+':tag')
    if a.attrib!=b.attrib:out.append(path+':attributes '+repr((a.attrib,b.attrib)))
    if a.text!=b.text:out.append(path+':text')
    if a.tail!=b.tail:out.append(path+':tail')
    if len(a)!=len(b):out.append(path+':children '+repr((len(a),len(b))))
    for i in range(min(len(a),len(b))):out+=diff(a[i],b[i],path+'/'+a[i].tag+'['+str(i)+']')
    return out

def verify(n):
    case=f'curves{n}';root=APP/case;raw=json.loads((ROOT/'candidates'/case/'raw.json').read_text());series=raw['series']
    need(len(series)==n,'wrong raw series count');original=load('original');actual=load(case)
    sheet=actual.find(".//folder[@name='Folder1']/child_aspect/spreadsheet[@name='Book1']")
    original_sheet=original.find(".//folder[@name='Folder1']/child_aspect/spreadsheet[@name='Book1']")
    original_curve=original.find('.//xyCurve')
    need(sheet is not None,'sheet missing');columns=sheet.findall('column');need(len(columns)==2*n,'app columns missing/extra')
    observed=json.loads((root/'curve-observation.json').read_text());need(observed['curve_count']==n and len(observed['curves'])==n,'app curve count differs')
    curves={c['y_path']:c for c in observed['curves']};need(len(curves)==n,'duplicate curve Y source identity')
    xmlcurves=actual.findall('.//xyCurve');need(len(xmlcurves)==n,'saved curve count differs')
    saved_curves={c.find('general').get('yColumn'):c for c in xmlcurves};need(len(saved_curves)==n,'duplicate saved curve binding')
    cells=list(csv.DictReader(io.StringIO((root/'Book1/native-app-values.tsv').read_text()),delimiter='\t'))
    need(len(cells)==100*n,'visible spreadsheet API cell count');api={(int(c['column']),int(c['row'])):c['hex_binary64'] for c in cells};need(len(api)==100*n,'duplicate API cells')
    paths=[];emissions=0
    for i,s in enumerate(series):
        need(len(s['x'])==len(s['y'])==50,'raw row count mismatch')
        xp='test_tree_import/Folder1/Book1/'+s['x_column'];yp='test_tree_import/Folder1/Book1/'+s['y_column'];paths.append({'series_id':s['series_id'],'x':xp,'y':yp})
        need(yp in curves and yp in saved_curves,'expected bound curve missing');c=curves[yp]
        need(c['x_bound'] and c['y_bound'] and c['signal_spy_valid'],'unbound curve or no passive signal spy')
        need(c['x_path']==xp and c['y_path']==yp,'actual bound object identities differ')
        need(c['curve_path']=='test_tree_import/Folder1/Graph2/Plot1/'+s['y_column'],'wrong parent graph/layer')
        need(c['x_allocated_rows']==c['y_allocated_rows']==50,'curve unequal/missing bound rows')
        need(saved_curves[yp].find('general').get('xColumn')==xp,'saved X identity differs')
        expected_curve=copy.deepcopy(original_curve);expected_curve.set('name',s['y_column'])
        expected_curve.find('general').set('xColumn',xp);expected_curve.find('general').set('yColumn',yp)
        expected_curve.find('general').set('legendVisible','1' if i==0 else '0')
        need(not diff(normalized(expected_curve),normalized(saved_curves[yp])),'new curve configuration differs from declared cloned style')
        expected=[[bits(s['x'][r]),bits(s['y'][r])] for r in range(50)]
        for j,key in enumerate(('x','y')):
            vv=c[key+'_values'];need(len(vv)==50,'bound column observation count')
            column=columns[2*i+j];need(column.get('name')==s[key+'_column'] and column.get('rows')=='50' and column.get('mode')=='0','saved column identity/type/rows')
            payload=base64.b64decode(column.find('output_filter').tail,validate=True);need(len(payload)==400,'saved payload length')
            expected_column=copy.deepcopy(original_sheet.findall('column')[j]);expected_column.set('name',s[key+'_column'])
            # Exact XML inter-element tail: a nonfinal column gets the original
            # A sibling indent; only the final column gets the original B indent.
            expected_column.tail=original_sheet.findall('column')[0 if 2*i+j<2*n-1 else 1].tail
            expected_column.find('output_filter').tail=column.find('output_filter').tail
            need(not diff(normalized(expected_column),normalized(column)),'new column metadata differs from declared clone')
            for r in range(50):
                cell=vv[r];need(cell['row']==r and cell['valid'] is True and cell['masked'] is False,'bound row invalid/masked')
                need(cell['bits']==expected[r][j]==api[(2*i+j,r)]==payload[r*8:r*8+8][::-1].hex(),'raw/bound/worksheet/save bits disagree')
        ee=c['point_signal_emissions'];need(len(ee)>0,'no independently rendered curve point signal');emissions+=len(ee)
        for e in ee:need(e['start_index']==0 and e['end_index']==49 and e['logical_point_count']==50 and e['logical_points_binary64']==expected,'rendered curve points differ')
    # Check independently different X, not inferred A or a visually similar data alias.
    need(len({tuple(bits(v) for v in s['x']) for s in series})==n,'test lost pairwise distinct X challenge')
    # Remove only intended insertions and restore only intended A/B data, then
    # compare all remaining app-owned content including every unrelated value.
    original_sheet=original.find(".//folder[@name='Folder1']/child_aspect/spreadsheet[@name='Book1']")
    for c in list(sheet.findall('column'))[2:]:sheet.remove(c)
    sheet.find("column[@name='B']").tail=original_sheet.find("column[@name='B']").tail
    for label in ('A','B'):
        sheet.find(f"column[@name='{label}']/output_filter").tail=original_sheet.find(f"column[@name='{label}']/output_filter").tail
    for parent in actual.iter():
        for child in list(parent):
            if child.tag=='xyCurve' and child.find('general').get('yColumn')!='test_tree_import/Folder1/Book1/B':parent.remove(child)
    exclusions={}
    for k in ('dockWidgetState','modificationTime','thumbnail'):
        exclusions[k]={'original_sha256':sha(original.get(k,'').encode()),'candidate_sha256':sha(actual.get(k,'').encode())};original.attrib.pop(k,None);actual.attrib.pop(k,None)
    dd=diff(normalized(original),normalized(actual));need(not dd,'unexpected unrelated project changes: '+repr(dd[:8]))
    need((root/'input.before.sha256').read_bytes()==(root/'input.after.sha256').read_bytes(),'source modified by app')
    need((root/'source-evidence.opj').read_bytes()==(ROOT/'candidates'/case/'candidate.opj').read_bytes(),'observed snapshot differs')
    return {'case':case,'curve_count':n,'source_cells_bit_exact':100*n,'rendered_pairs_bit_exact':50*n,'point_signal_emissions':emissions,
            'actual_and_saved_source_bindings':paths,'all_unrelated_app_content_unchanged':True,'all_expected_column_values_saved_bit_exact':True,
            'all_X_vectors_pairwise_distinct':True,'excluded_application_ui_metadata':exclusions,'origin_validation':'NOT_RUN',
            'native_safe_export_supported':False,'legend_limitation':'Only original B is included in the unchanged template legend; new curves have legendVisible=0.'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--count',type=int,choices=(2,5,10),required=True);p.add_argument('--output',type=Path);a=p.parse_args();r=verify(a.count)
    if a.output:
        with a.output.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
    print(json.dumps(r,indent=2))
