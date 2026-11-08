"""Independent black-box checks. Checks stay active with python -O."""
import hashlib, types, sys, random, json, time
from pathlib import Path
from itertools import product
from reachability_oracle import W, choices, reachable_widths
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
BASE=ROOT/'reference'

def load(name,path,digest=None):
    source=path.read_bytes()
    if digest:require(hashlib.sha256(source).hexdigest()==digest,'source hash mismatch')
    mod=types.ModuleType(name);sys.modules[name]=mod
    exec(compile(source,str(path),'exec'),mod.__dict__)
    return mod

def require(condition,message):
    if not condition:raise RuntimeError(message)

impl=load('target_exact_fpc',ROOT/'code/experimental_exact_fpc.py')
baseline=load('pinned_baseline',BASE/'fpc_numeric.py','43c3415066ed12f1f158e8406f6d62d1dc767daea537e31441865934e6c70dbc')
dec=load('pinned_decoder',BASE/'independent_fpc_decoder.py','0ad34fbaedf86655085e6302d864a3456af6377f7d00e641a2879dbf79734d89')
counts={'streams':0,'accepted_budgets':0,'rejected_budgets':0,'invalid_calls':0}

def refusal(call,kind=impl.ExperimentalFPCError):
    try:call()
    except kind:counts['invalid_calls']+=1;return
    raise RuntimeError('invalid call accepted')

def widths(payload,n):
    result=[];off=0
    for i in range(0,n,2):
        control=payload[off];off+=1
        if i+1==n:require(control>>4==0,'odd high nibble must be zero')
        for j in range(min(2,n-i)):
            w=W[(control>>(4*j))&7];result.append(w);off+=w
    require(off==len(payload),'payload bounds')
    return tuple(result)

def check(words,all_budgets=True):
    raw=b''.join(v.to_bytes(8,'little') for v in words)
    minima=tuple(min(o[0] for o in c) for c in choices(words))
    sums=reachable_widths(minima);control=(len(words)+1)//2
    wanted={control+s for s in sums}
    info=impl.analyze_exact_budgets(raw)
    actual={i for lo,hi in info.reachable_intervals for i in range(lo,hi+1)}
    require(actual==wanted,('analysis mismatch',words,actual,wanted))
    require(info.count==len(words) and info.minimum_bytes==min(wanted) and info.maximum_bytes==max(wanted),'metadata')
    require(impl.encode_bits_exact_budget(raw,min(wanted))==baseline.encode_bits(raw),'baseline bytes')
    budgets=range(max(wanted)+2) if all_budgets else sorted(set((0,min(wanted),max(wanted),rng.choice(sorted(wanted)),max(wanted)+1)))
    schedules=None
    if len(words)<=2:
        schedules={}
        for schedule in product(*[tuple(w for w in W if w>=m) for m in minima]):
            b=control+sum(schedule)
            schedules[b]=min(schedules.get(b,schedule),schedule)
    for budget in budgets:
        if budget not in wanted:
            try:impl.encode_bits_exact_budget(raw,budget)
            except impl.UnreachableBudgetError:counts['rejected_budgets']+=1;continue
            raise RuntimeError(('unreachable accepted',words,budget))
        payload=impl.encode_bits_exact_budget(raw,budget)
        require(type(payload) is bytes and len(payload)==budget,'size/type')
        require(dec.decode_strict(payload,len(words))==list(words),'roundtrip')
        require(payload==impl.encode_bits_exact_budget(raw,budget),'determinism/reset')
        ws=widths(payload,len(words))
        if schedules is not None:require(ws==schedules[budget],'lexicographic widths')
        counts['accepted_budgets']+=1
    counts['streams']+=1

start=time.monotonic();rng=random.Random(20261108)
alphabet=(0,1,256,65536,1<<24,1<<32,1<<40,1<<48,1<<56,(1<<64)-1)
for n in range(4):
    for words in product(alphabet,repeat=n):check(words)
# Raw IEEE categories, integer strides, long prefixes, wraparound and hash collision pressure.
special=[0,1<<63,0x7ff0000000000000,0xfff0000000000000,0x7ff8000000000001,0x7ff0000000000001,0xfff8000012345678,1,0x000fffffffffffff,0x0010000000000000,0x7fefffffffffffff,(1<<64)-1]
for _ in range(240):
    n=rng.randrange(1,100)
    category=rng.randrange(5)
    if category==0:words=[rng.getrandbits(64) for _ in range(n)]
    elif category==1:words=[rng.choice(special) for _ in range(n)]
    elif category==2:words=[rng.getrandbits(rng.randrange(65)) for _ in range(n)]
    elif category==3:words=[(rng.getrandbits(64) if i%11==0 else 0) for i in range(n)]
    else:
        a=rng.getrandbits(64);step=rng.getrandbits(64);words=[(a+i*step)%2**64 for i in range(n)]
    check(words,False)
for bad in (None,False,0,[],bytearray(8),memoryview(bytes(8)),b'x',b'x'*9):
    refusal(lambda bad=bad:impl.analyze_exact_budgets(bad))
    refusal(lambda bad=bad:impl.encode_bits_exact_budget(bad,0))
for bad in (-1,True,False,None,1.0,'1',10**100):
    refusal(lambda bad=bad:impl.encode_bits_exact_budget(b'',bad))
    refusal(lambda bad=bad:impl.encode_bits_exact_budget(b'',0,max_output_bytes=bad))
    refusal(lambda bad=bad:impl.analyze_exact_budgets(b'',max_values=bad))
for call in (
    lambda:impl.analyze_exact_budgets(bytes(8),max_values=0),
    lambda:impl.analyze_exact_budgets(b'',max_values=1_000_001),
    lambda:impl.encode_bits_exact_budget(b'',0,max_output_bytes=8_500_001),
    lambda:impl.encode_bits_exact_budget(bytes(8),1,max_output_bytes=0),
    lambda:impl.analyze_exact_budgets(bytes(8_000_008)),
    lambda:impl.encode_bits_exact_budget(bytes(8_000_008),0),
):refusal(call)
# Exact hard count boundary. A full-width output exercises preallocation and final bounds.
raw=bytes(8_000_000)
info=impl.analyze_exact_budgets(raw)
require((info.count,info.minimum_bytes,info.maximum_bytes)==(1_000_000,500_000,8_500_000),'hard boundary analysis')
for budget in (500_000,8_500_000):
    payload=impl.encode_bits_exact_budget(raw,budget)
    require(len(payload)==budget,'hard boundary length')
    decoded=dec.decode_strict(payload,1_000_000)
    require(len(decoded)==1_000_000 and not any(decoded),'hard boundary decode')
    widths(payload,1_000_000)
counts['hard_boundary_streams']=2
counts['optimized']=not __debug__
counts['seconds']=round(time.monotonic()-start,3)
counts['implementation_sha256']=hashlib.sha256((ROOT/'code/experimental_exact_fpc.py').read_bytes()).hexdigest()
path=HERE/('review_results_optimized.json' if not __debug__ else 'review_results.json')
path.write_text(json.dumps(counts,indent=2)+'\n');print(json.dumps(counts))
