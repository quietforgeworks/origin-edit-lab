"""Independent bounded archive audit; writes only in this audit directory."""
from pathlib import Path
import sys, json, hashlib, tempfile, argparse
HERE=Path(__file__).resolve().parent
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--package',type=Path,default=HERE.parent/'package')
ap.add_argument('--research-root',type=Path,default=HERE.parents[2],help='Directory containing the prior research and approved source trees')
args=ap.parse_args()
PACKAGE=args.package.resolve()
WORK=args.research_root.resolve()
sys.path.insert(0,str(PACKAGE/'code'))
import run_codec_experiments as h

def need(c,m):
    if not c: raise RuntimeError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
expected={'code/experimental_exact_fpc.py':'982b2c9119e8a460bcd850e46db14268164dc28a78faf38fc4153123e2031e25','code/run_codec_experiments.py':'a0d2ea12255d8fdcecc8ebf0234ad3868a145db27ffe6d0bd755a33e7371df7b'}
for p,d in expected.items():need(sha(PACKAGE/p)==d,'candidate hash')
prior=WORK/'origin-modern-fpc-encoder-research-20261108'
report=prior/'results/public-corpus-normal.json';provenance=prior/'evidence/public_sources.json'
need(sha(report)=='2bca1eeeac8b271be79eaf355924aa259dfe4789884cc9a71634f62229bdc271','report hash')
need(sha(provenance)=='9da30c7bc4f167290f53d0293083354e2e168614d8e372541115240c0f203e76','provenance hash')
m=json.loads((PACKAGE/'evidence/public-template-streams.json').read_text());r=json.loads(report.read_text());p=json.loads(provenance.read_text())
need(m['source_report_sha256']==sha(report),'report reference')
need(len(m['files'])==3 and len(m['streams'])==13,'manifest count')
allow={f['file'] for f in m['files']}
for f in m['files']:need(f in p['files'],'provenance field equality')
need(m['streams']==[s for s in r['streams'] if s['file'] in allow],'full ordered stream record equality')
for s in m['streams']:
    need(0<=s['start']<s['end'] and s['end']-s['start']==s['original_bytes'],'extent')
    need(s['source_sha256']==next(f['sha256'] for f in m['files'] if f['file']==s['file']),'source ref')
checks=0
def refuses(fn):
    global checks
    try:fn()
    except (ValueError,TypeError,FileNotFoundError):checks+=1;return
    raise RuntimeError('malformed accepted')
from experimental_exact_fpc import encode_bits_exact_budget as encode, analyze_exact_budgets as analyze
for bad in (True,False,-1,1.0,None,'0',8_500_001):refuses(lambda:encode(b'',bad))
for raw in (b'x',b'x'*9,bytearray(8),memoryview(bytes(8)),None):refuses(lambda:encode(raw,1))
for kwargs in ({'max_values':True},{'max_values':-1},{'max_output_bytes':8_500_001},{'max_output_bytes':0}):refuses(lambda:encode(bytes(8),1,**kwargs))
# Prove no trailing padding admitted by strict decoders, and each truncated nonempty prefix rejected.
raw=h.packed([0x7ff0000000000001,0xfff8123456789abc,h.SENTINEL,0,1<<63])
info=analyze(raw)
root=WORK/'origin-data-generation/native-workbook-v2/dependencies/quantized-431deeb7c8473503970ca56b78cc1678f57d373d/src/quantized'
with h.loader.external_decoder(root) as external:
    for lo,hi in info.reachable_intervals:
        for budget in range(lo,hi+1):
            wire=encode(raw,budget)
            need(h.validate(raw,wire,external)==1,'sentinel count')
            need(encode(raw,budget)==wire,'determinism')
            refuses(lambda:h.independent.decode_strict(wire+b'\0',5))
            refuses(lambda:h.baseline.decode_bits(wire+b'\0',5))
            for cut in range(len(wire)):refuses(lambda:h.independent.decode_strict(wire[:cut],5))
need(not any(k=='quantized' or k.startswith('quantized.') for k in sys.modules),'module cleanup')
with tempfile.TemporaryDirectory(dir=HERE) as td:
    td=Path(td); file=td/'data';file.write_bytes(b'x')
    refuses(lambda:h.read_guarded(file,'0'*64))
    link=td/'link';link.symlink_to(file)
    refuses(lambda:h.read_guarded(link,sha(file)))
    refuses(lambda:h.loader.load_verified(file,'untrusted','0'*64))
    refuses(lambda:h.loader.load_verified(link,'untrusted',sha(file)))
    root=td/'fake';(root/'io/origin_project').mkdir(parents=True)
    (root/'io/origin_project/container.py').write_text('raise RuntimeError("must not execute")')
    def reject_external():
        with h.loader.external_decoder(root):pass
    refuses(reject_external)
    # Exercise real public entrypoint, with malformed/symlink fixture and source.
    saved_root=h.ROOT
    try:
        h.ROOT=td/'fake-package';(h.ROOT/'evidence').mkdir(parents=True)
        manifest=h.ROOT/'evidence/public-template-streams.json'
        manifest.write_text('{}')
        refuses(lambda:h.run_public(td,None))
        manifest.unlink();manifest.symlink_to(PACKAGE/'evidence/public-template-streams.json')
        refuses(lambda:h.run_public(td,None))
        manifest.unlink();manifest.write_bytes((PACKAGE/'evidence/public-template-streams.json').read_bytes())
        first=td/m['files'][0]['file'];first.write_bytes(b'tampered')
        refuses(lambda:h.run_public(td,None))
        first.unlink();first.symlink_to(WORK/'origin-data-generation/routes/public-native-samples'/m['files'][0]['file'])
        refuses(lambda:h.run_public(td,None))
    finally:h.ROOT=saved_root
result={'reviewed_hashes':{str(p.relative_to(PACKAGE)):sha(p) for p in PACKAGE.rglob('*') if p.is_file() and (p.parent.name in ('reference','code','independent-review') and p.suffix=='.py' or p.name in ('test_exact_budget.py','test_revision_contract.py','public-template-streams.json'))},'exact_prior_stream_records':13,'exact_prior_provenance_records':3,'malformed_refusals':checks,'synthetic_sentinel_and_nan_all_budgets':True,'optimize':sys.flags.optimize,'normal_optimized_results_equal_except_optimize':None}
a=json.loads((HERE/'portable-public-normal.json').read_text());b=json.loads((HERE/'portable-public-optimized.json').read_text());a.pop('optimize');b.pop('optimize');need(a==b,'normal optimized unequal');result['normal_optimized_results_equal_except_optimize']=True
out=HERE/('audit-checks-optimized.json' if sys.flags.optimize else 'audit-checks-normal.json');out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
