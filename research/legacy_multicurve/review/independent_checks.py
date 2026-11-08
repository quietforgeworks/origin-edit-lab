"""Reviewer-authored, exact-public-fixture checks, no author parser imports.

Only inspects local evidence. Does not launch applications or write native files.
The original frame indices are fixed by the pinned fixture's SHA-256. Insertion
boundaries are the dataset/Book1-column/Graph2-curve zero sentinels; all remaining
bytes, including unknown fields, must survive verbatim. This is not an Origin
validator and cannot establish Origin acceptance.
"""
from pathlib import Path
import argparse,base64,copy,csv,hashlib,json,lzma,struct,xml.etree.ElementTree as ET

def need(ok,why):
    if not ok:raise RuntimeError(why)
def sha(b):return hashlib.sha256(b).hexdigest()
def bits(s):return struct.pack('>d',float(s)).hex()
def framed(p):return len(p).to_bytes(4,'little')+b'\n'+p+(b'\n' if p else b'')
def records(blob,count):
    need(blob[:17]==b'CPYA 4,2878 724#\n','legacy signature');p=17;out=[]
    for i in range(count):
        need(p+5<=len(blob),'truncated frame');n=int.from_bytes(blob[p:p+4],'little');end=p+5+n+bool(n)
        need(end<=len(blob) and n<16777216 and blob[p+4]==10,'frame extent/prefix')
        need(not n or blob[end-1]==10,'frame suffix');out.append(blob[p+5:p+5+n]);p=end
    return out,p

def native(source,fixture,n):
    original=fixture.read_bytes();need(sha(original)=='ea50c9b97b063898f654a6189b30ca5d8be8b52ad4c9469b3934cd009185265a','fixture hash')
    a,stop=records(original,478);need(stop==228955,'pinned tail offset')
    need(a[77]==a[265]==a[453]==b'','insertion anchors are zero sentinels')
    need(a[246][2:27].split(b'\0')[0]==b'Book1' and a[412][2:27].split(b'\0')[0]==b'Graph2','pinned window identity')
    folder=source/f'candidates/curves{n}';raw=(folder/'raw.json').read_bytes();series=json.loads(raw)['series'];need(len(series)==n,'series count')
    candidate=(folder/'candidate.opj').read_bytes();actual,end=records(candidate,478+12*(n-1));expected=list(a);inserts={77:[],265:[],453:[]}
    expected[3]=b''.join(b'\0\0'+struct.pack('<d',float(v)) for v in series[0]['x']);expected[6]=b''.join(b'\0\0'+struct.pack('<d',float(v)) for v in series[0]['y'])
    for i,s in enumerate(series):
        need(s['series_id']==f'S{i+1:02d}' and s['sheet']=='Book1' and s['x_column']==chr(65+2*i) and s['y_column']==chr(66+2*i),'raw identities')
        need(len(s['x'])==len(s['y'])==50,'equal 50-row raw arrays')
        if not i:continue
        ids=(24+2*i,25+2*i)
        for c,key in enumerate(('x','y')):
            h=bytearray(a[2+3*c]);h[88:113]=('Book1_'+s[key+'_column']).encode().ljust(25,b'\0');data=b''.join(b'\0\0'+struct.pack('<d',float(v)) for v in s[key])
            inserts[77].extend([bytes(h),data,a[4+3*c]])
            h=bytearray(a[261+2*c]);h[4:6]=ids[c].to_bytes(2,'little');h[18:30]=s[key+'_column'].encode().ljust(12,b'\0')
            if c:h[35:37]=ids[0].to_bytes(2,'little')
            inserts[265].extend([bytes(h),a[262+2*c]])
        h=bytearray(a[451]);h[4:6]=ids[1].to_bytes(2,'little');h[35:37]=ids[0].to_bytes(2,'little');inserts[453].extend([bytes(h),a[452]])
    stitched=[]
    for i,p in enumerate(expected):stitched.extend(inserts.get(i,[]));stitched.append(p)
    need(actual==stitched,'unapproved original or inserted frame difference')
    need(candidate==original[:17]+b''.join(framed(p) for p in stitched)+original[stop:],'full binary complement')
    need(candidate[end:]==original[stop:],'opaque tail preserved')
    need((folder/'rollback.opj').read_bytes()==original,'exact rollback')
    cells=0
    for i,s in enumerate(series):
        ids=(1,2) if not i else (24+2*i,25+2*i)
        for j,key in enumerate(('x','y')):
            h,d,m=actual[2+3*(ids[j]-1):5+3*(ids[j]-1)]
            need(len(h)==140 and len(d)==500 and not m,'dataset header/data/mask extent')
            need(struct.unpack_from('<III',h,25)==(50,0,50),'dataset row bounds')
            need(h[61]==10 and h[88:113].split(b'\0')[0]==('Book1_'+s[key+'_column']).encode(),'dataset name and cell width')
            for r,v in enumerate(s[key]):need(d[10*r:10*r+2]==b'\0\0' and d[10*r+2:10*r+10][::-1].hex()==bits(v),'tagged native value');cells+=1
        sheetidx=(261 if not i else 265+4*(i-1))+6*(n-1)
        for j in range(2):
            h=actual[sheetidx+2*j];need(len(h)==489 and int.from_bytes(h[4:6],'little')==ids[j],'worksheet selector/extent')
            need(h[18:30].split(b'\0')[0]==chr(65+2*i+j).encode() and h[17]==(3,0)[j],'worksheet name/type')
            need(int.from_bytes(h[35:37],'little')==(0,ids[0])[j] and struct.unpack_from('<II',h,7)==(0,50),'worksheet X and opaque bounds')
        graphidx=(451 if not i else 453+2*(i-1))+10*(n-1);h=actual[graphidx]
        need(len(h)==489 and (int.from_bytes(h[35:37],'little'),int.from_bytes(h[4:6],'little'))==ids,'graph explicit selectors')
        need(struct.unpack_from('<II',h,7)==(0,50),'graph opaque bounds')
    manifest=json.loads((folder/'manifest.json').read_bytes());need(manifest['safe_native_export_supported'] is False and manifest['Origin_reopen_update_recalculate_save']=='NOT_RUN','native limitation report')
    need(manifest['candidate_sha256']==sha(candidate) and manifest['raw_sha256']==sha(raw),'manifest hashes')
    ledger=manifest['binary64_conversion_ledger'];need(len(ledger)==cells,'ledger coverage')
    rows={(r['series_id'],r['column'],r['row_one_based']):r for r in ledger};need(len(rows)==cells,'unique ledger identities')
    for s in series:
        for key in ('x','y'):
            for r,v in enumerate(s[key],1):
                entry=rows[(s['series_id'],s[key+'_column'],r)];need(entry['raw_numeric_lexeme']==v and entry['binary64_little_endian_hex']==struct.pack('<d',float(v)).hex(),'ledger bits and lexical preservation')
    return {'case':n,'bytes':len(candidate),'sha256':sha(candidate),'source_cells_bit_exact':cells,'frames':len(actual),'original_dataset_slots_preserved':25,'added_dataset_slots':2*(n-1),'all_other_bytes_and_opaque_tail_exact':True,'rollback_exact':True}

def xml(folder):
    b=(folder/'imported-application.lml').read_bytes();return ET.fromstring(lzma.decompress(b) if b.startswith(b'\xfd7zXZ\0') else b)
def norm(e,root=False):
    attrs={k:v for k,v in e.attrib.items() if k not in ('uuid','creation_time') and not(root and k in ('dockWidgetState','modificationTime','thumbnail'))}
    return e.tag,attrs,e.text,e.tail,[norm(c) for c in e]
def app(source,fixture,n):
    root=source/f'application/results/curves{n}';base=source/'application/results/original';a=xml(base);b=xml(root)
    series=json.loads((source/f'candidates/curves{n}/raw.json').read_bytes())['series'];prefix='test_tree_import/Folder1/Book1/'
    obs=json.loads((root/'curve-observation.json').read_bytes());need(obs['curve_count']==n and len(obs['curves'])==n,'actual XYCurve count')
    observed={c['y_path']:c for c in obs['curves']};saved={c.find('general').get('yColumn'):c for c in b.findall('.//xyCurve')};need(len(observed)==len(saved)==n,'unique curves in app and save')
    rows=list(csv.DictReader((root/'Book1/native-app-values.tsv').open(),delimiter='\t'));api={(int(c['column']),int(c['row'])):c['hex_binary64'] for c in rows};need(len(rows)==len(api)==100*n,'API cell identities/count')
    path=".//folder[@name='Folder1']/child_aspect/spreadsheet[@name='Book1']";asheet=a.find(path);bsheet=b.find(path);need(asheet is not None and bsheet is not None,'target worksheet');columns=bsheet.findall('column');need(len(columns)==2*n,'saved column count')
    acurve=a.find('.//xyCurve');emissions=[];binds=[]
    for i,s in enumerate(series):
        xp=prefix+s['x_column'];yp=prefix+s['y_column'];need(yp in observed and yp in saved,'curve target present');c=observed[yp];sc=saved[yp]
        need(c['curve_path']=='test_tree_import/Folder1/Graph2/Plot1/'+s['y_column'] and c['x_path']==xp and c['y_path']==yp,'actual bound object paths')
        need(c['x_bound'] is True and c['y_bound'] is True and c['signal_spy_valid'] is True,'actual curve bindings and signal spy')
        need(c['x_allocated_rows']==c['y_allocated_rows']==50,'bound allocation');binds.append([xp,yp]);expected=[[bits(x),bits(y)] for x,y in zip(s['x'],s['y'])]
        ec=copy.deepcopy(acurve);ec.set('name',s['y_column']);ec.find('general').set('xColumn',xp);ec.find('general').set('yColumn',yp);ec.find('general').set('legendVisible','1' if not i else '0');need(norm(ec)==norm(sc),'complete saved curve cloned style/bindings with exact text/tails')
        for j,key in enumerate(('x','y')):
            vv=c[key+'_values'];col=columns[2*i+j];need(len(vv)==50 and col.get('rows')=='50' and col.get('mode')=='0' and col.get('name')==s[key+'_column'],'saved/API column shape')
            data=base64.b64decode(col.find('output_filter').tail,validate=True);need(len(data)==400,'saved array length')
            ec=copy.deepcopy(asheet.findall('column')[j]);ec.set('name',s[key+'_column']);ec.tail=asheet.findall('column')[0 if 2*i+j<2*n-1 else 1].tail;ec.find('output_filter').tail=col.find('output_filter').tail;need(norm(ec)==norm(col),'complete saved column clone')
            for r,v in enumerate(vv):need(v['row']==r and v['valid'] is True and v['masked'] is False and v['bits']==expected[r][j]==api[(2*i+j,r)]==data[8*r:8*r+8][::-1].hex(),'raw/bound/API/saved bit equality')
        ee=c['point_signal_emissions'];need(len(ee)>0,'passive per-curve points emissions');emissions.append(len(ee))
        for e in ee:need(e['start_index']==0 and e['end_index']==49 and e['logical_point_count']==50 and e['logical_points_binary64']==expected,'each actual curve rendered logical points')
    need(len({tuple(bits(x) for x in s['x']) for s in series})==n,'all X columns distinct')
    for c in list(columns)[2:]:bsheet.remove(c)
    bsheet.findall('column')[1].tail=asheet.findall('column')[1].tail
    for j in range(2):bsheet.findall('column')[j].find('output_filter').tail=asheet.findall('column')[j].find('output_filter').tail
    for parent in b.iter():
        for child in list(parent):
            if child.tag=='xyCurve' and child.find('general').get('yColumn')!=prefix+'B':parent.remove(child)
    need(norm(a,True)==norm(b,True),'entire unrelated serialized project content including exact whitespace')
    for folder,src in ((base,fixture),(root,source/f'candidates/curves{n}/candidate.opj')):
        blob=src.read_bytes();need((folder/'source-evidence.opj').read_bytes()==blob,'app source snapshot');need((folder/'input.before.sha256').read_bytes()==(folder/'input.after.sha256').read_bytes(),'input hashes stable');need((folder/'input.before.sha256').read_text().split()[0]==sha(blob),'before hash evidence')
        need('OBSERVER_INPUT='+str(folder/'source-evidence.opj') in (folder/'application.log').read_text(),'actual import filename')
        need((folder/'exit-status.txt').read_text().strip()=='124','planned timeout after capture/save')
    # Baseline independently tied to original cells, not author expectations.
    original,_=records(fixture.read_bytes(),478);points=[[original[3][r*10+2:r*10+10][::-1].hex(),original[6][r*10+2:r*10+10][::-1].hex()] for r in range(50)]
    bo=json.loads((base/'curve-observation.json').read_bytes());need(bo['curve_count']==len(bo['curves'])==1,'baseline curve count')
    need(len(bo['curves'][0]['point_signal_emissions'])>0,'baseline signals')
    for e in bo['curves'][0]['point_signal_emissions']:need(e['logical_point_count']==50 and e['logical_points_binary64']==points,'baseline points')
    br=list(csv.DictReader((base/'Book1/native-app-values.tsv').open(),delimiter='\t'));need(len(br)==100 and len({(int(c['column']),int(c['row'])) for c in br})==100,'baseline API count')
    for c in br:need(c['hex_binary64']==points[int(c['row'])][int(c['column'])],'baseline API bits')
    return {'case':n,'actual_xycurve_objects':n,'api_cells_bit_exact':100*n,'logical_pairs_bit_exact':50*n,'passive_emissions_per_curve':emissions,'all_saved_arrays_bit_exact':True,'all_source_bindings':binds,'all_unrelated_app_project_content_exact':True,'xml_whitespace_preserved':True,'original_baseline_verified':True,'input_snapshot_and_hashes_verified':True,'exit_status':124,'Origin_acceptance':'NOT_RUN'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('fixture',type=Path);p.add_argument('--evidence-root',type=Path,required=True);p.add_argument('--output',type=Path);a=p.parse_args();source=a.evidence_root.absolute();fixture=a.fixture.absolute()
    result={'native':[native(source,fixture,n) for n in (2,5,10)],'application':[app(source,fixture,n) for n in (2,5,10)]}
    if a.output:
        with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))
