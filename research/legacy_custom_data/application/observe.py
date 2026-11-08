"""New custom-data observation gate; does not modify the published toy-only runner."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('custom',ROOT/'src/custom_data.py')
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
RUNTIME_HASHES={
 'squashfs-root/usr/bin/labplot':'c11d801f47329fcd69b03c8f6acf5a5f8f74a9dc6a2f3bbdaa32293804e17554',
 'squashfs-root/usr/lib/liblabplot.so.2.12.1':'81d571e53b9dfb793f07cbbb9307d418391103ae7c8679a36284d12422e10fbf',
 'squashfs-root/AppRun':'ce1d68255d5cd2a27c13471a22f504d35f3e0374ed90763d24f6830b781af30d'}
OBSERVER_HASH='3c4df197b6c6c960a44d31bf3f1a704580d63ba119ea927881c02925f2b7aa2a'

def run(runtime,bundle,output,expected_csv_sha256,expected_declaration_sha256,research_opt_in=False):
 c.opt_in(research_opt_in)
 data=c.read_bundle(bundle)
 verified=c.verify_artifacts(data,expected_csv_sha256=expected_csv_sha256,expected_declaration_sha256=expected_declaration_sha256,research_opt_in=True)
 c.need(verified['input_provenance']['caller_declaration']['declared_kind']=='synthetic','this application research run accepts only explicitly declared synthetic input')
 runtime=c.checked_path(runtime)
 for path,digest in RUNTIME_HASHES.items():
  c.need(c.sha(c.read_file(runtime/path,100000000))==digest,'official runtime component hash mismatch: '+path)
 observer=c.checked_path(ROOT/'application/application_observer.so')
 c.need(c.sha(c.read_file(observer,10000000))==OBSERVER_HASH,'authored observer build hash mismatch')
 output=c.new_output(output);output.mkdir()
 before={name:c.sha(content) for name,content in data.items()}
 for name,source in [('original',data['rollback.opj']),('custom',data['candidate.opj'])]:
  dest=output/name;dest.mkdir();profile=output/(name+'-profile');profile.mkdir()
  for d in ('home','config','cache','state','data','runtime','tmp'):(profile/d).mkdir(mode=0o700)
  snapshot=dest/'source-evidence.opj';snapshot.write_bytes(source);snapshot.chmod(0o400)
  env=os.environ.copy()
  for key in ('LD_PRELOAD','LD_LIBRARY_PATH','QT_PLUGIN_PATH','QML2_IMPORT_PATH','OBSERVER_SELECT_NAME'):env.pop(key,None)
  env.update(HOME=str(profile/'home'),XDG_CONFIG_HOME=str(profile/'config'),XDG_CACHE_HOME=str(profile/'cache'),XDG_STATE_HOME=str(profile/'state'),XDG_DATA_HOME=str(profile/'data'),XDG_RUNTIME_DIR=str(profile/'runtime'),TMPDIR=str(profile/'tmp'),OBSERVER_BUNDLED_LIB=str(runtime/'squashfs-root/usr/lib/liblabplot.so.2.12.1'),OBSERVER_RAW_NUMERIC='1',OBSERVER_OUT=str(dest),OBSERVER_INPUT=str(snapshot),OBSERVER_LAYER_MODE='plot',LD_PRELOAD=str(observer))
  (dest/'input.before.sha256').write_text(c.sha(source)+'\n')
  with (dest/'application.log').open('wb') as log:
   process=subprocess.run(['timeout','11s',str(runtime/'squashfs-root/AppRun'),'-platform','offscreen','--no-splash'],cwd=dest,env=env,stdout=log,stderr=subprocess.STDOUT)
  (dest/'exit-status.txt').write_text(str(process.returncode)+'\n')
  c.need(process.returncode==124,'unexpected observer runtime exit')
  c.need(c.read_file(snapshot,231494)==source,'source snapshot changed')
  (dest/'input.after.sha256').write_text(c.sha(c.read_file(snapshot,231494))+'\n')
  c.need((dest/'imported-application.lml').is_file(),'no real application save')
 after=c.read_bundle(bundle)
 c.need(all(after[name]==data[name] for name in data),'bundle changed during observation')
 receipt={'schema':'custom-labplot-observation-v1','native_bundle_before_after_identical':True,
  'native_bundle_artifacts_sha256':before,'runtime_sha256':RUNTIME_HASHES,'observer_sha256':OBSERVER_HASH,
  'expected_csv_sha256':expected_csv_sha256,'expected_declaration_sha256':expected_declaration_sha256,
  'origin_lifecycle':'NOT_RUN','application_results_validation':'PENDING independent validator'}
 (output/'run-receipt.json').write_bytes(c.json_bytes(receipt))
 print(json.dumps(receipt,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for f in ('runtime','bundle','output','expected-csv-sha256','expected-declaration-sha256'):p.add_argument('--'+f,required=True)
 p.add_argument('--accept-labplot-only-research',action='store_true')
 a=vars(p.parse_args());a['research_opt_in']=a.pop('accept_labplot_only_research');run(**a)
