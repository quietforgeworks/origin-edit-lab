"""Hash-check public samples and reproduce structural counts, without source writes.

Supply original extracted public samples in --inputs, named as public_sources.json.
No sample bytes, private inputs, downloaded runtimes or application activation.
"""
import argparse,hashlib,json
from pathlib import Path
import native_binding as n

def need(ok,msg):
    if not ok:raise ValueError(msg)
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--inputs',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--corpus',choices=['all','original110','independent57'],default='all')
    args=ap.parse_args()
    source=Path(__file__).with_name('public_sources.json')
    records=json.loads(source.read_text())
    rows=[]
    for e in records:
        if args.corpus!='all' and e['corpus']!=args.corpus:continue
        path=args.inputs/e['file'];b=n.ds.read_bounded_source(path)
        need(len(b)==e['bytes'],'Input size mismatch: '+e['file'])
        need(hashlib.sha256(b).hexdigest()==e['sha256'],'Input SHA256 mismatch: '+e['file'])
        if 'md5' in e:need(hashlib.md5(b).hexdigest()==e['md5'],'Publisher MD5 mismatch: '+e['file'])
        report=n.walk(b)
        need(report['summary']==e['expected_summary'],'Structural summary differs: '+e['file'])
        need(hashlib.sha256(n.ds.read_bounded_source(path)).hexdigest()==e['sha256'],'Source changed: '+e['file'])
        rows.append({'file':e['file'],'sha256':e['sha256'],'corpus':e['corpus'],'summary':report['summary']})
    need(bool(rows),'No sources selected')
    n.ds.write_new_result(args.out,{'sources_verified':len(rows),'result':'all expected summaries reproduced',
                                  'origin_acceptance':False,'numeric_values_decoded':False,'project_tail_validated':False,'rows':rows})
    print(json.dumps({'sources_verified':len(rows),'result':'all expected summaries reproduced'}))
if __name__=='__main__':main()
