"""Independent exact-size oracle, derived before target implementation review."""
from itertools import product, combinations_with_replacement
from collections import Counter
import hashlib, types, json
from pathlib import Path

def require(condition, message):
    if not condition: raise RuntimeError(message)

W=(0,1,2,3,5,6,7,8)
MASK=2**64-1

def choices(words):
    f,d={},{}
    fh=dh=last=0
    out=[]
    for v in words:
        residuals=(v^f.get(fh,0), v^((last+d.get(dh,0))&MASK))
        opts=[]
        for selector,r in enumerate(residuals):
            for code,w in enumerate(W):
                if r.bit_length()<=8*w:
                    opts.append((w, selector*8+code, r))
        out.append(opts)
        stride=(v-last)&MASK
        f[fh]=v;d[dh]=stride
        fh=((fh*64)^(v>>48))%4096
        dh=((dh*4)^(stride>>40))%4096
        last=v
    return out

def reachable_widths(minima):
    sums={0}
    for m in minima:
        sums={a+w for a in sums for w in W if w>=m}
    return sums

def classified(minima):
    lo=sum(minima); hi=8*len(minima)
    active=[m for m in minima if m<8]
    holes=set()
    if active and all(m==3 for m in active):holes.add(lo+1)
    elif len(active)==1 and active[0]<3:holes.add(lo+4-active[0])
    return set(range(lo,hi+1))-holes

def oracle_encodings(words):
    opts=choices(words)
    # Enumerate unique width schedules, retaining first valid selector per width.
    distinct=[]
    for options in opts:
        bywidth={}
        for o in options:bywidth.setdefault(o[0],o)
        distinct.append(list(bywidth.values()))
    for schedule in product(*distinct):
        payload=bytearray()
        for i in range(0,len(schedule),2):
            pair=schedule[i:i+2]
            payload.append(sum(option[1]<<(4*j) for j,option in enumerate(pair)))
            for w,_,r in pair:payload.extend(r.to_bytes(w,'little'))
        yield bytes(payload)

def main():
    decoder_path=Path(__file__).resolve().parents[1]/'reference/independent_fpc_decoder.py'
    source=decoder_path.read_bytes()
    require(hashlib.sha256(source).hexdigest()=='0ad34fbaedf86655085e6302d864a3456af6377f7d00e641a2879dbf79734d89', 'decoder hash mismatch')
    dec=types.ModuleType('prior_independent_decoder')
    exec(compile(source,str(decoder_path),'exec'),dec.__dict__)
    width_cases=0
    for n in range(13):
        for minima in combinations_with_replacement(W,n):
            got=reachable_widths(minima)
            require(got==classified(minima),(minima,sorted(got),sorted(classified(minima))))
            width_cases+=1
    alphabet=(0,1,256,65536,1<<24,1<<32,1<<40,1<<48,1<<56,MASK)
    stream_cases=encoding_cases=0
    hole_examples={}
    for n in range(4):
        for stream in product(alphabet,repeat=n):
            minima=[min(o[0] for o in opts) for opts in choices(stream)]
            sizes=set()
            for payload in oracle_encodings(stream):
                require(dec.decode_strict(payload,n)==list(stream), (stream,payload.hex()))
                sizes.add(len(payload));encoding_cases+=1
            overhead=(n+1)//2
            expected={s+overhead for s in reachable_widths(minima)}
            require(sizes==expected, (stream,sizes,expected))
            holes=sorted(set(range(min(sizes),max(sizes)+1))-sizes)
            if holes:
                key=tuple(minima)
                hole_examples[str(key)]={'words':[hex(x) for x in stream],'sizes':sorted(sizes),'holes':holes}
            stream_cases+=1
    result={'width_multisets_through_length_12':width_cases,'word_streams_through_length_3':stream_cases,'serialized_encodings_independently_decoded':encoding_cases,'hole_examples':hole_examples}
    Path(__file__).with_name('oracle_results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='hole_examples'}))

if __name__=='__main__':main()
