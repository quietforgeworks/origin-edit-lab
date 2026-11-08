"""Regenerate exact research splices and verify full provenance artifacts."""
import json, os, re, sys
from pathlib import Path
from native_allocation import COUNTS,TEMPLATE_HASH,patch_bytes,restore_bytes,require,sha,inspect,checked_path
from make_cases import TOY_HASHES
ROOT=Path(__file__).resolve().parent

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)

def verify_original_source(root):
    root=Path(root);data=Path(os.environ['ORIGIN_PUBLIC_FIXTURE']).read_bytes()
    require(sha(data)==TEMPLATE_HASH,'original fixture differs');inspect(data,50)
    run=root/'application/results/original'
    require((run/'source-evidence.opj').read_bytes()==data,'original app snapshot differs')
    before=(run/'input.before.sha256').read_text()
    require(before==(run/'input.after.sha256').read_text() and before.split()[0]==TEMPLATE_HASH,'original app input hash differs')
    require('OBSERVER_INPUT='+str(run.resolve()/'source-evidence.opj') in (run/'application.log').read_text(),'original app import path differs')
    require((run/'exit-status.txt').read_text().strip()=='124','original app did not finish expected capture cycle')
    return {'source_snapshot_and_hash_exact':True,'template_sha256':TEMPLATE_HASH}

def verify_case_source(root,n,*,app=False):
    root=Path(root);base=Path(os.environ['ORIGIN_PUBLIC_FIXTURE']);template=base.read_bytes()
    require(sha(template)==TEMPLATE_HASH,'source fixture differs')
    folder=root/'candidates'/f'generated{n}';raw=(root/'candidates'/f'raw{n}.csv').read_bytes()
    require(sha(raw)==TOY_HASHES[n],'input differs from published synthetic case')
    candidate,m,b,a=patch_bytes(template,raw,research_only=True)
    require((folder/'candidate.opj').read_bytes()==candidate,'candidate differs from exact regenerated edit')
    require((folder/'raw.csv').read_bytes()==raw,'raw copy differs')
    for file,obj in (('manifest.json',m),('before.json',b),('after.json',a)):
        require(canonical(json.loads((folder/file).read_text()))==canonical(obj),'full artifact differs: '+file)
    require((folder/'rollback.opj').read_bytes()==template and restore_bytes(candidate,m)==template,'rollback differs')
    if app:
        run=root/'application/results'/f'expanded{n}'
        require((run/'source-evidence.opj').read_bytes()==candidate,'application source snapshot differs')
        before=(run/'input.before.sha256').read_text();after=(run/'input.after.sha256').read_text()
        require(before==after and before.split()[0]==sha(candidate),'app input hash not linked to actual candidate')
        require('OBSERVER_INPUT='+str(run.resolve()/'source-evidence.opj') in (run/'application.log').read_text(),'app imported wrong source path')
    return {'regenerated_source_and_all_artifacts_exact':True,'rollback_sha256':sha(template),
        'candidate_sha256':sha(candidate),'application_source_link_verified':app,
        'preserved_graph_sha256':a['graph_sha256'],'framed_end':a['framed_end'],'allocation':n}

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--check-paths':
        require(len(sys.argv)>2,'paths required')
        for path in sys.argv[2:]:checked_path(path)
        print('path components checked');sys.exit(0)
    require(len(sys.argv)==3,'require case and file')
    name,input_path=sys.argv[1:];data=Path(input_path).read_bytes()
    if name=='original':
        require(sha(data)==TEMPLATE_HASH,'wrong original');inspect(data,50)
    else:
        match=re.fullmatch(r'expanded(51|257|1024)',name);require(match is not None,'unsupported case')
        n=int(match[1]);verify_case_source(ROOT,n)
        require(data==(ROOT/'candidates'/f'generated{n}'/'candidate.opj').read_bytes(),'run input differs')
    print('exact public/synthetic input verified:',name)
