"""Opt-in codec-only tests. No native writes, source edits, downloads or installs."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
# Fixed reviewed public fixture; this runner does not accept arbitrary manifests.
PUBLIC_TEMPLATE_MANIFEST_SHA256 = '4f59150060fd427f97fea59829c8cd7b070010287b6f030097b61c28b89810ec'
sys.path.insert(0, str(ROOT / 'tests'))
from test_exact_budget import (pinned, baseline, independent, packed,
                              seeded_sequences, SENTINEL)
from experimental_exact_fpc import analyze_exact_budgets, encode_bits_exact_budget, UnreachableBudgetError

loader = pinned('verified_oracle', '2e6281e200590d83c063fd1e633caa09988f511ba34fe925c2807871a105b98d')

def need(condition, message):
    if not condition: raise ValueError(message)

def sha(data): return hashlib.sha256(data).hexdigest()

def validate(raw, wire, external):
    import numpy as np
    count = len(raw)//8
    need(baseline.decode_bits(wire, count) == (raw, len(wire)), 'baseline raw decoder mismatch')
    words, used = independent.decode_prefix(wire+b'TRAILER', count)
    need((packed(words),used) == (raw,len(wire)), 'independent raw decoder mismatch')
    observed, used = external._decode(wire+b'TRAILER',count)
    expected = bytearray(raw)
    missing = 0
    for index,word in enumerate(words):
        if word == SENTINEL:
            expected[index*8:(index+1)*8] = np.asarray([np.nan], dtype='<f8').tobytes()
            missing += 1
    need(observed.view('<u8').tobytes()==bytes(expected), 'unchanged external mismatch beyond sentinel mapping')
    need(used==len(wire), 'external consumed length mismatch')
    return missing

def run_synthetic(external):
    rng = random.Random(1282026)
    totals = {'input_sequences':0,'exact_budget_encodings':0,'decoded_words':0,
              'nonminimal_encodings':0,'missing_sentinel_occurrences':0}
    digest = hashlib.sha256()
    for words in seeded_sequences():
        raw=packed(words)
        info=analyze_exact_budgets(raw)
        budgets=set()
        for low,high in info.reachable_intervals:
            budgets.update((low,high,rng.randint(low,high)))
        for budget in sorted(budgets):
            wire=encode_bits_exact_budget(raw,budget)
            missing=validate(raw,wire,external)
            need(wire==encode_bits_exact_budget(raw,budget),'nondeterminism')
            digest.update(raw);digest.update(wire)
            totals['exact_budget_encodings']+=1
            totals['decoded_words']+=len(words)
            totals['nonminimal_encodings']+=budget!=info.minimum_bytes
            totals['missing_sentinel_occurrences']+=missing
        totals['input_sequences']+=1
    return {**totals,'aggregate_raw_and_encoded_sha256':digest.hexdigest()}

def read_guarded(path, expected):
    need(not path.is_symlink() and path.is_file(),'public source must be a regular non-symlink file')
    need(path.stat().st_size<=1_000_000,'public source exceeds experiment size cap')
    data=path.read_bytes()
    need(sha(data)==expected,'public source SHA mismatch')
    return data

def run_public(source_dir,external):
    manifest=json.loads(read_guarded(ROOT/'evidence/public-template-streams.json',
                                     PUBLIC_TEMPLATE_MANIFEST_SHA256))
    results=[]
    originals={}
    for source in manifest['files']:
        need(source['public'] is True,'not a public source')
        path=source_dir/source['file']
        data=read_guarded(path,source['sha256'])
        originals[source['file']]=data
    for item in manifest['streams']:
        source=originals[item['file']]
        wire=source[item['start']:item['end']]
        need(sha(wire)==item['original_stream_sha256'],'recorded stream interval digest mismatch')
        words=independent.decode_strict(wire,item['count'])
        original_raw=packed(words)
        need(sha(original_raw)==item['raw_bits_sha256'],'recorded raw words digest mismatch')
        validate(original_raw,wire,external)
        replay=encode_bits_exact_budget(original_raw,len(wire))
        validate(original_raw,replay,external)

        # Deliberately different, disclosed toy values; not a scientific curve,
        # replacement recommendation, source-data mutation, graph or fitted data.
        toy_raw=b''.join(struct.pack('<d',float(i)) for i in range(item['count']))
        toy_info=analyze_exact_budgets(toy_raw)
        record={'file':item['file'],'source_sha256':item['source_sha256'],
                'source_stream_interval':[item['start'],item['end']],
                'count':item['count'],'target_bytes':len(wire),
                'source_stream_sha256':sha(wire),'source_raw_sha256':sha(original_raw),
                'source_reencoded_sha256':sha(replay),
                'toy_definition':'binary64 values float(i) for i in range(count), synthetic only',
                'toy_raw_sha256':sha(toy_raw),'toy_analysis':asdict(toy_info)}
        try:
            candidate=encode_bits_exact_budget(toy_raw,len(wire))
        except UnreachableBudgetError:
            record['toy_status']='refused_unreachable'
        else:
            validate(toy_raw,candidate,external)
            record.update(toy_status='exact_budget_codec_success',toy_stream_sha256=sha(candidate),
                          toy_stream_bytes=len(candidate),
                          extra_bytes_above_toy_minimum=len(candidate)-toy_info.minimum_bytes)
        rng=random.Random(item['count'])
        random_raw=packed([rng.getrandbits(64) for _ in range(item['count'])])
        random_info=analyze_exact_budgets(random_raw)
        record['random_bit_analysis']=asdict(random_info)
        try:
            random_wire=encode_bits_exact_budget(random_raw,len(wire))
        except UnreachableBudgetError: record['random_bit_status']='refused_unreachable'
        else:
            validate(random_raw,random_wire,external)
            record['random_bit_status']='exact_budget_codec_success'
        results.append(record)
    for source in manifest['files']:
        need(read_guarded(source_dir/source['file'],source['sha256'])==originals[source['file']],
             'public source changed')
    return {'files':len(originals),'streams':len(results),
            'toy_exact_budget_successes':sum(x['toy_status']=='exact_budget_codec_success' for x in results),
            'random_bit_refusals':sum(x['random_bit_status']=='refused_unreachable' for x in results),
            'all_source_hashes_unchanged':True,'records':results}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--quantized-root',required=True,type=Path)
    ap.add_argument('--public-source-dir',type=Path)
    ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args()
    import numpy as np
    with loader.external_decoder(args.quantized_root) as external:
        result={'synthetic':run_synthetic(external)}
        if args.public_source_dir: result['public_template_lengths']=run_public(args.public_source_dir,external)
    result.update(python=platform.python_version(),numpy=np.__version__,optimize=sys.flags.optimize,
                  external_revision=loader.REVISION,external_source_pins=loader.PINS,
                  implementation_sha256=sha((ROOT/'code/experimental_exact_fpc.py').read_bytes()),
                  harness_sha256=sha(Path(__file__).read_bytes()),
                  public_template_manifest_sha256=PUBLIC_TEMPLATE_MANIFEST_SHA256,
                  unchanged_external_qualification='Origin finite missing sentinel normalized to NaN; all other raw bits checked exactly',
                  both_integer_decoders_bit_exact=True,native_origin_acceptance=False,
                  native_containers_written=False,source_values_modified=False)
    with args.out.open('x') as handle:json.dump(result,handle,indent=2);handle.write('\n')
    print(json.dumps({key:value for key,value in result.items() if key!='public_template_lengths'},sort_keys=True))
    if 'public_template_lengths' in result:
        print(json.dumps({k:v for k,v in result['public_template_lengths'].items() if k!='records'},sort_keys=True))

if __name__=='__main__': main()
