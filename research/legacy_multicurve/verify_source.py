from pathlib import Path
import argparse,json,os
from native_multicurve import checked_path,read_regular,patch_bytes,TEMPLATE_HASH
from numeric_support import require,sha
ROOT=Path(__file__).resolve().parent

def verify_case(name,path):
    b=read_regular(path,524288)
    if name=='original':require(sha(b)==TEMPLATE_HASH,'wrong original hash');return
    require(name in ('curves2','curves5','curves10'),'bad case')
    folder=ROOT/'candidates'/name
    raw=read_regular(folder/'raw.json',262144);template=read_regular(folder/'rollback.opj',262144)
    expected,m=patch_bytes(template,raw,research_only=True)
    require(b==expected,'candidate differs from exact authored transformation')
    require(json.loads(read_regular(folder/'manifest.json',2097152))==m,'manifest differs')
    return m
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',required=True);p.add_argument('--input',type=Path,required=True);p.add_argument('--check-path',nargs='*',default=[]);a=p.parse_args()
    for path in a.check_path:checked_path(path)
    verify_case(a.case,a.input);print('source verified:',a.case)
