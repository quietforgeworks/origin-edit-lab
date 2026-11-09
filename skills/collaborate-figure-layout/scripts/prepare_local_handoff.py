#!/usr/bin/env python3
"""Build a task-private local handoff directory; does not start a server."""
import argparse, base64, hashlib, importlib.util, json, re, shutil, tempfile
from pathlib import Path
from prepare_web_project import prepare

ROOT=Path(__file__).resolve().parent.parent

def build(binding, previews, output, record):
    output,record=Path(output),Path(record)
    if output.exists() or record.exists(): raise ValueError('Choose new output and record paths')
    if output.resolve()==record.resolve() or output.resolve() in record.resolve().parents: raise ValueError('Keep private binding record outside page directory')
    assets=ROOT/'assets/local-handoff'
    with tempfile.TemporaryDirectory(prefix='figure-handoff-') as tmp:
        tmp=Path(tmp)
        prepare(binding,previews,tmp/'prepared',tmp/'record.json')
        spec=importlib.util.spec_from_file_location('offline_builder',ROOT/'assets/web-layout/build-offline.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        source=module.normalize(json.loads((tmp/'prepared/project.json').read_text()),(tmp/'prepared').resolve())
        html=(assets/'workbench.template.html').read_text()
        if html.count('__SOURCE_JSON__')!=1:raise ValueError('Invalid handoff template')
        data=json.dumps(source,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
        html=html.replace('__SOURCE_JSON__',data)
        scripts=re.findall(r'<script>(.*?)</script>',html,re.S)
        if len(scripts)!=1:raise ValueError('Expected one inline script')
        digest=base64.b64encode(hashlib.sha256(scripts[0].encode()).digest()).decode()
        html,n=re.subn(r"script-src 'sha256-[A-Za-z0-9+/=]+'", "script-src 'sha256-"+digest+"'",html)
        if n!=1:raise ValueError('Missing script CSP hash')
        output.mkdir(parents=True,exist_ok=False)
        for name in ('server.py','assistant_layout.py','guide_relations.py'):shutil.copyfile(assets/name,output/name)
        (output/'index.html').write_text(html)
        (output/'source.json').write_text(json.dumps(source,ensure_ascii=False,indent=2))
        record.parent.mkdir(parents=True,exist_ok=True)
        with record.open('x') as f:f.write((tmp/'record.json').read_text())
    return {'output':str(output),'panelCount':len(source['panels']),'serverStarted':False,'uploaded':False,'sourceEdited':False,'browserVerified':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('binding');p.add_argument('previews');p.add_argument('--output-dir',required=True);p.add_argument('--thumbnail-record',required=True);a=p.parse_args()
    try:print(json.dumps(build(a.binding,a.previews,a.output_dir,a.thumbnail_record),ensure_ascii=False,indent=2))
    except (OSError,ValueError,TypeError,KeyError) as e:p.exit(2,str(e)+'\n')
if __name__=='__main__':main()
