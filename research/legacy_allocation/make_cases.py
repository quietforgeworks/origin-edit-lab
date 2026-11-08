"""Create only toy CSV and explicit LabPlot-only experimental candidates."""
# A refused CLI invocation must not leave import bytecode behind either.
if __name__ == '__main__':
    import sys
    sys.dont_write_bytecode = True

import argparse, math, os
from decimal import Decimal, localcontext
from pathlib import Path
from native_allocation import COUNTS, TEMPLATE_HASH, generate, require, sha, checked_path, Rejected, BLOCKER
ROOT=Path(__file__).resolve().parent
TOY_HASHES={51:'633717e0ae55bdf1ec6da02885a631f78caacf23f8a53f4e8426b4232bb65b71',
    257:'e6943baf066d99883de149c94a7d5740b1bae958275901f2dcf913c29881ddfc',
    1024:'b2905be142dcef078f7d6c8f0fc6c220fef9298f0d4cadc2872236eb21dbfabc'}

def toy_csv(n):
    require(type(n) is int and n in COUNTS,'unsupported toy count')
    lines=['A,B']
    with localcontext() as c:
        c.prec=45
        for i in range(n):
            x='-0' if i==0 else str(Decimal(50)*i/(n-1))
            y=format(.5+.35*math.sin(4*math.pi*i/(n-1)),'.17g')
            if i in (0,50,256,1023):y='-0'
            elif i==1:y='0.123456789012345678901234567890123456789'
            lines.append(x+','+y)
    raw=('\n'.join(lines)+'\n').encode('ascii')
    require(sha(raw)==TOY_HASHES[n],'toy generator differs on this runtime; use the retained hash-pinned CSV instead')
    return raw

def main(*, research_only=False):
    require(research_only is True,BLOCKER)
    path=checked_path(os.environ['ORIGIN_PUBLIC_FIXTURE'])
    require(sha(path.read_bytes())==TEMPLATE_HASH,'wrong fixture')
    folder=checked_path(ROOT/'candidates');folder.mkdir(exist_ok=True)
    targets=[checked_path(folder/f'generated{n}') for n in COUNTS]
    require(all(not p.exists() and not p.is_symlink() for p in targets),'candidate output already exists')
    for n in COUNTS:
        csvpath=checked_path(folder/f'raw{n}.csv')
        raw=csvpath.read_bytes() if csvpath.is_file() and not csvpath.is_symlink() else toy_csv(n)
        require(sha(raw)==TOY_HASHES[n],'wrong retained toy CSV')
        require(not csvpath.is_symlink() and (not csvpath.exists() or csvpath.read_bytes()==raw),'existing toy CSV differs')
        if not csvpath.exists():
            try:
                with csvpath.open('xb') as stream:stream.write(raw)
            except FileExistsError as exc:raise Rejected('toy CSV raced into place; no overwrite') from exc
        m=generate(path,csvpath,folder/f'generated{n}',research_only=research_only)
        print(n,m['candidate_bytes'],m['candidate_sha256'])
def cli(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--labplot-only-research',action='store_true',
        help='Explicitly allow unsafe-for-Origin research candidates; required before reading inputs or creating outputs')
    args=parser.parse_args(argv)
    main(research_only=args.labplot_only_research)

if __name__=='__main__':cli()
