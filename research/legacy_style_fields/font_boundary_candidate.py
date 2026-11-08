"""One hash-locked title-font diagnostic fixture, not a supported general edit.

This reproduces only the public strings_testing.opj YL font22-to30 probe.
It is separate from the four supported bounded style experiment fields.
"""
from pathlib import Path
import json
from native_style_patch import need,sha,frame,publish_directory

SOURCE_URL='https://github.com/KDE/labplot/blob/0bd2e4094e92e74052ec161022d4e60aeb7605cd/tests/import_export/Project/data/strings_testing.opj'
SOURCE_SHA256='8d1e26543e77942faef097a3cdc05ba4a78d2b0d667c9edb9003074b4e0443ed'
CANDIDATE_SHA256='07185039711b4b3e1eedeec31c91e6b7a8707720d1698d9a639312719667d35d'
SIZE=344049
OFFSET=147865

def prepare(source):
    need(type(source)is bytes and len(source)==SIZE and sha(source)==SOURCE_SHA256,'exact original strings fixture required')
    header=frame(source,147696,154)
    style=frame(source,147856,103)
    title=frame(source,147965,9)
    need(header[70:111].split(b'\0')[0]==b'YL' and title==b'Log of x\0' and style[4]==22,'pinned title structure differs')
    candidate=source[:OFFSET]+bytes([30])+source[OFFSET+1:]
    need(sha(candidate)==CANDIDATE_SHA256,'unexpected candidate hash')
    need(source[:OFFSET]+source[OFFSET+1:]==candidate[:OFFSET]+candidate[OFFSET+1:],'non-target source bytes changed')
    restored=candidate[:OFFSET]+bytes([22])+candidate[OFFSET+1:]
    need(restored==source,'title probe rollback differs')
    manifest={'purpose':'Diagnostic reader font-overwrite probe only; not supported general title editing','public_source':SOURCE_URL,'source_sha256':SOURCE_SHA256,'candidate_sha256':CANDIDATE_SHA256,'source_size':SIZE,'candidate_size':SIZE,'target':'Graph1.layer1.YL stored title font','offset':OFFSET,'before':22,'after':30,'changed_bytes':1,'all_other_source_bytes_identical':True,'restored_sha256':sha(restored),'Origin_reopen':'NOT RUN'}
    return candidate,manifest,restored

def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    candidate,manifest,restored=prepare(args.input.read_bytes())
    publish_directory(args.out,{'candidate.opj':candidate,'restored.opj':restored,'manifest.json':(json.dumps(manifest,indent=2)+'\n').encode()})
    print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
