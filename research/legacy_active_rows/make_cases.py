"""Recreate only public-fixture/toy cases, with no overwrite or symlink following."""
from pathlib import Path
import json,os
from native_active_rows import generate, Rejected, TEMPLATE_HASH, sha
from numeric_support import require

def read_regular(path):
    descriptor=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        import stat
        require(stat.S_ISREG(os.fstat(descriptor).st_mode),'CSV prerequisite is not a regular file')
        with os.fdopen(descriptor,'rb',closefd=False) as stream:return stream.read()
    finally:os.close(descriptor)

def main():
    root=Path(__file__).resolve().parent
    source=Path(os.environ.get('ORIGIN_PUBLIC_FIXTURE',''))
    require(bool(os.environ.get('ORIGIN_PUBLIC_FIXTURE')),'Set ORIGIN_PUBLIC_FIXTURE to the separately obtained exact public fixture')
    require(sha(source.read_bytes())==TEMPLATE_HASH,'wrong public fixture')
    candidates=root/'candidates'
    require(candidates.is_dir() and not candidates.is_symlink(),'candidates must be a real directory')
    rows=[]
    for i in range(50):
        x='-0' if i==0 else str(i)+'.1'
        y='-0.0' if i==0 else ('0.12345678901234567' if i==1 else '0.'+str(1+i%8))
        rows.append(f'{x},{y}\n')
    raws={n:('A,B\n'+''.join(rows[i%50] for i in range(n))).encode() for n in (7,49,50,51,257)}
    for n,raw in raws.items():
        path=candidates/f'raw{n}.csv'
        require(not path.is_symlink(),'refusing CSV symlink')
        if path.exists():require(read_regular(path)==raw,'existing CSV differs; no overwrite')
        output=candidates/(f'generated{n}' if n<=50 else f'refused{n}')
        require(not output.exists() and not output.is_symlink(),'case output already exists; no overwrite')
    report=root/'refusal-evidence.json'
    require(not report.exists() and not report.is_symlink(),'refusal report already exists; no overwrite')
    for n,raw in raws.items():
        path=candidates/f'raw{n}.csv'
        if not path.exists():
            with path.open('xb') as stream:stream.write(raw)
        require(read_regular(path)==raw,'CSV changed after preflight')
    for n in (7,49,50):generate(source,candidates/f'raw{n}.csv',candidates/f'generated{n}')
    refused=[]
    for n in (51,257):
        out=candidates/f'refused{n}'
        try:generate(source,candidates/f'raw{n}.csv',out)
        except Rejected as exc:
            require(not out.exists() and not out.is_symlink(),'refused case created an output')
            refused.append({'requested_active_rows':n,'result':'REFUSED before output creation','reason':str(exc),'output_exists':False})
        else:raise RuntimeError('unsafe expansion unexpectedly accepted')
    with report.open('x') as stream:stream.write(json.dumps(refused,indent=2)+'\n')

if __name__=='__main__':main()
