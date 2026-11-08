"""Only exposed CFB/PPT native-edit/restore route; bounded external-anchor API.

New copies only. No preview/cache changes. Import-only writeback helper never
receives unanchored caller restoration data through this wrapper.
"""
from pathlib import Path
import io,json,zipfile
import native_scalar_writer as n
import writeback as core
from cfb_read import CompoundFile
CORE_SHA='9b971c9828cb6382ce1d21df6a21d5219424040a83e0438a1b33e8996ec21e93'
CFB_SHA='afbc1fdcfdeaf8ceafcee772380c8ef0e5c135b988565216e8f3d6dbf649d06a'
MAX_CONTAINER=128*1024*1024
MAX_MANIFEST=16*1024*1024

def pinned():
 for name,h in [('writeback.py',CORE_SHA),('cfb_read.py',CFB_SHA)]:n.anchor((Path(__file__).parent/name).read_bytes(),h,'container dependency '+name)

def apply_native_bundle(source,plans,*,expected_native_sha256,expected_bundle_sha256):
 n.anchor(source,expected_native_sha256,'native source');n.anchor(n.canonical(plans),expected_bundle_sha256,'plan bundle')
 n.need(type(plans)is list and 1<=len(plans)<=4,'bundle must contain 1 to 4 scalar plans')
 current=source;manifests=[]
 for plan in plans:
  current,m=n.apply(current,plan,expected_source_sha256=n.digest(current),expected_plan_sha256=n.digest(n.canonical(plan)));manifests.append(m)
 # Each next plan must have been independently prepared from the actual new source.
 allowed=sorted(set(i for m in manifests for i in m['changed_offsets']))
 n.need(all(a==b or i in allowed for i,(a,b) in enumerate(zip(source,current))),'bundle full native complement')
 restored=current
 for m in reversed(manifests):restored=n.restore(restored,m,expected_source_sha256=m['source_sha256'],expected_result_sha256=m['result_sha256'],expected_manifest_sha256=n.digest(n.canonical(m)))
 n.need(restored==source,'reverse-order exact native bundle restore')
 return current,manifests,allowed

def patch(source,plans,*,kind,part=None,expected_source_sha256,expected_cfb_sha256,expected_native_sha256,expected_bundle_sha256):
 pinned();n.need(type(source)is bytes and len(source)<=MAX_CONTAINER,'bounded container bytes required');n.anchor(source,expected_source_sha256,'container source')
 n.need(kind in ('cfb','pptx'),'unsupported container kind');n.need((kind=='cfb' and part is None) or (kind=='pptx' and type(part)is str and part.startswith('ppt/embeddings/') and part.endswith('.bin')),'exact PPT embedding part required')
 if kind=='pptx':
  package=core.RawZip(source);n.need(part in package.parts,'exact embedding part missing');cfb=package.z.read(part)
 else:cfb=source
 n.anchor(cfb,expected_cfb_sha256,'CFB source');original=CompoundFile(cfb).read_stream('Contents');n.anchor(original,expected_native_sha256,'native source')
 candidate,deltas,allowed=apply_native_bundle(original,plans,expected_native_sha256=expected_native_sha256,expected_bundle_sha256=expected_bundle_sha256)
 changed,cm=core.patch_cfb(cfb,candidate,stream_path='Contents',expected_source_sha256=expected_cfb_sha256,expected_stream_sha256=expected_native_sha256,allowlist=[(x,1) for x in allowed])
 if kind=='pptx':result,container_delta=core.reembed_pptx(source,changed,part=part,expected_source_sha256=expected_source_sha256,expected_part_sha256=expected_cfb_sha256,cfb_manifest=cm)
 else:result,container_delta=changed,cm
 manifest={'schema':'cpyua-native-container-v1','kind':kind,'part':part,'source_sha256':n.digest(source),'result_sha256':n.digest(result),'cfb_source_sha256':n.digest(cfb),'cfb_result_sha256':n.digest(changed),'native_source_sha256':n.digest(original),'native_result_sha256':n.digest(candidate),'bundle_sha256':expected_bundle_sha256,'plans':plans,'native_deltas':deltas,'cfb_delta':cm,'container_delta':container_delta,'native_allowed_offsets':allowed,'origin_acceptance':'NOT_RUN','cache_policy':'all caches unchanged; visible PPT is not updated until Origin refresh, unverified'}
 n.need(core.restore_delta(result,container_delta)==source,'exact whole container restore')
 return result,manifest

def restore(result,manifest,*,expected_source_sha256,expected_result_sha256,expected_manifest_sha256):
 pinned();n.need(type(result)is bytes and len(result)<=MAX_CONTAINER,'bounded container bytes required');n.anchor(n.canonical(manifest),expected_manifest_sha256,'container manifest');n.anchor(result,expected_result_sha256,'container result')
 n.need(type(manifest)is dict and manifest.get('schema')=='cpyua-native-container-v1','container manifest schema');n.need(manifest.get('source_sha256')==expected_source_sha256 and manifest.get('result_sha256')==expected_result_sha256,'container external source/result anchors')
 original=core.restore_delta(result,manifest['container_delta']);n.anchor(original,expected_source_sha256,'restored container source')
 reproduced,m=patch(original,manifest['plans'],kind=manifest['kind'],part=manifest['part'],expected_source_sha256=expected_source_sha256,expected_cfb_sha256=manifest['cfb_source_sha256'],expected_native_sha256=manifest['native_source_sha256'],expected_bundle_sha256=manifest['bundle_sha256'])
 n.need(reproduced==result and n.canonical(m)==n.canonical(manifest),'restored container fails full anchored regeneration')
 return original

def manifest_json(data):
 n.need(type(data)is bytes and len(data)<=MAX_MANIFEST,'manifest exceeds bound')
 # Same strict hooks as native plans; larger cap is only for compressed ZIP deltas.
 return n.strict_json(data,max_bytes=MAX_MANIFEST)

def main():
 import argparse
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=['patch','restore']);p.add_argument('source',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--source-sha256',required=True);p.add_argument('--result-sha256');p.add_argument('--manifest',type=Path);p.add_argument('--manifest-sha256');p.add_argument('--plans',type=Path);p.add_argument('--bundle-sha256');p.add_argument('--native-sha256');p.add_argument('--cfb-sha256');p.add_argument('--kind',choices=['cfb','pptx']);p.add_argument('--part');args=p.parse_args()
 n.w.validate_output(args.source,args.out);b=n.bounded_regular(args.source,MAX_CONTAINER)
 if args.operation=='patch':
  n.need(args.plans is not None,'plans file required');plans=n.strict_json(n.bounded_regular(args.plans,65536));out,m=patch(b,plans,kind=args.kind,part=args.part,expected_source_sha256=args.source_sha256,expected_cfb_sha256=args.cfb_sha256,expected_native_sha256=args.native_sha256,expected_bundle_sha256=args.bundle_sha256)
  print(n.canonical(m).decode(),end='')
 else:
  n.need(args.manifest is not None,'manifest file required');m=manifest_json(n.bounded_regular(args.manifest,MAX_MANIFEST));out=restore(b,m,expected_source_sha256=args.source_sha256,expected_result_sha256=args.result_sha256,expected_manifest_sha256=args.manifest_sha256)
 n.need(n.bounded_regular(args.source,MAX_CONTAINER)==b,'source changed during container operation');n.new_output(args.source,args.out,out)
if __name__=='__main__':main()
