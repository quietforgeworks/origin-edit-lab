"""Toy data only. Exact decimal construction, no libm dependence."""
from pathlib import Path
from decimal import Decimal
import argparse,json,os,stat
from native_multicurve import generate,checked_path,read_regular,patch_bytes,SERIES_COUNTS,BLOCKER
from numeric_support import require

def raw_for(n):
    out={'schema':'explicit-xy-v1','data_kind':'synthetic','series':[]}
    for i in range(n):
        x=[];y=[]
        for r in range(50):
            x.append(str(Decimal(r)*Decimal('0.91')+Decimal(i)*Decimal('0.037')+Decimal((r*r+3*i)%7)*Decimal('0.00013')))
            y.append(str(Decimal((r*7+i*11)%47)*Decimal('0.019')+Decimal(i)*Decimal('0.0011')))
        if i==0:x[0]='-0.0';y[3]='0.1234567890123456789012345'
        if i==1:x[25]='-0.0';y[17]='-0.0'
        out['series'].append({'series_id':f'S{i+1:02d}','sheet':'Book1','x_column':chr(65+2*i),'y_column':chr(66+2*i),'x':x,'y':y})
    return (json.dumps(out,indent=2)+'\n').encode()
def make_case(template_path,n,root=None,*,research_only=False):
    require(research_only is True,BLOCKER)
    require(type(n) is int and n in SERIES_COUNTS,'unsupported count')
    root=checked_path(root or Path(__file__).resolve().parent);require(root.is_dir(),'root must exist')
    d=checked_path(root/'candidates');raw=checked_path(d/f'synthetic{n}.json');out=checked_path(d/f'curves{n}')
    require(not raw.exists() and not out.exists(),'raw or candidate destination exists')
    require(not d.exists() or d.is_dir(),'candidates must be a directory')
    # Validate all input bytes and destinations before creating a directory/file.
    template=read_regular(template_path,262144);data=raw_for(n)
    patch_bytes(template,data,research_only=True)
    made_dir=False;raw_inode=None
    try:
        if not d.exists():d.mkdir();made_dir=True
        with raw.open('xb') as f:
            raw_inode=os.fstat(f.fileno()).st_ino;f.write(data)
        result=generate(template_path,raw,out,research_only=True)
        return result
    except BaseException:
        # Remove only this attempt's own unchanged raw inode, never a replacement.
        if raw_inode is not None and not raw.is_symlink() and raw.exists():
            current=raw.stat()
            if current.st_ino==raw_inode and stat.S_ISREG(current.st_mode) and raw.read_bytes()==data:raw.unlink()
        if made_dir:
            try:d.rmdir()
            except OSError:pass
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--template',type=Path,required=True);p.add_argument('--count',type=int,choices=(2,5,10),required=True);p.add_argument('--labplot-only-research',action='store_true');a=p.parse_args()
    print(make_case(a.template,a.count,research_only=a.labplot_only_research)['candidate_sha256'])
