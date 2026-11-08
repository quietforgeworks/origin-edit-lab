"""Assert exact observed application changes against the source field plan."""
from pathlib import Path
import json,math,sys
import native_style_patch as n
import compare_application as app
ROOT=Path(__file__).resolve().parent

def verify_source_candidate(original,candidate,manifest,key):
 """Recompute the pinned source edit; never trust preservation booleans."""
 expected,expected_manifest,before,after=n.patch(original,key,manifest.get('field'),manifest.get('requested_value'))
 n.need(candidate==expected,'candidate differs from exact bounded source edit')
 n.need(manifest==expected_manifest,'candidate manifest differs from recomputed evidence')
 n.need(n.restore(candidate,manifest)==original,'source restoration failed')
 return after

def verify():
 report=[]
 expected_counts={'xb_tick_font':2,'xb_axis_width':4,'curve_line_width':1,'layer_rect':6}
 endings={'xb_tick_font':("/axis[@name='x']/labels[1]/@fontPointSize","/axis[@name='x']/textLabel[@name='x']/geometry[1]/@y"),
 'xb_axis_width':("/axis[@name='x']/line[1]/@width","/axis[@name='x']/majorTicks[1]/@width","/axis[@name='x']/minorTicks[1]/@width","/axis[@name='x']/textLabel[@name='x']/geometry[1]/@y"),
 'curve_line_width':('/lines[1]/@width',),
 'layer_rect':('/coordinateSystems[1]/@bottomPadding','/coordinateSystems[1]/@horizontalPadding','/coordinateSystems[1]/@rightPadding','/coordinateSystems[1]/@verticalPadding',"/axis[@name='x']/textLabel[@name='x']/geometry[1]/@y","/axis[@name='y']/textLabel[@name='y']/geometry[1]/@x")}
 for key in n.PROFILES:
  baseline=key+'-baseline';bdir=app.ROOT/baseline
  for field in expected_counts:
   case=key+'-'+field;folder=app.ROOT/case
   result=app.compare(baseline,case);ds=result['complete_project_differences_excluding_ui_metadata']
   n.need(result['all_numeric_bits_equal'],'native values changed')
   n.need(result['native_numeric_cells']==(128 if key=='two_graphs' else 64),'unexpected readback coverage')
   n.need(len(ds)==expected_counts[field],'unexpected application delta count')
   for d in ds:n.need("/worksheet[@name='Graph1']/" in d['path'] and d['path'].endswith(endings[field]),'unexplained application delta '+d['path'])
   n.need((folder/'input.before.sha256').read_bytes()==(folder/'input.after.sha256').read_bytes(),'input mutated during import')
   source=(ROOT/'candidates'/case/'candidate.opj').read_bytes();n.need(source==(folder/'source-evidence.opj').read_bytes(),'wrong application input')
   m=json.loads((ROOT/'candidates'/case/'manifest.json').read_text());n.need(n.sha(source)==m['candidate_sha256'],'candidate hash')
   original=(ROOT/'fixtures'/n.PROFILES[key]['source_name']).read_bytes()
   n.need((bdir/'source-evidence.opj').read_bytes()==original,'wrong baseline source')
   a=verify_source_candidate(original,source,m,key)
   for directory,expected_input in ((bdir,original),(folder,source)):
    before_hash=(directory/'input.before.sha256').read_text()
    n.need(before_hash==(directory/'input.after.sha256').read_text(),'input changed during observation')
    n.need(before_hash.split()[0]==n.sha(expected_input),'recorded input hash does not match source')
   height=a['page_pixels'][1];dpi=600 if key=='two_graphs' else 300
   element=29.5/(height*2.54/dpi);text=(1+element)/2
   if field=='xb_tick_font':
    d=next(d for d in ds if d['path'].endswith('@fontPointSize'));n.need(int(d['before'])==int(18*text*254/72),'old tick conversion');n.need(int(d['after'])==int(26*text*254/72),'new tick conversion')
   if field in ('xb_axis_width','curve_line_width'):
    target=1250/500*element*254/72
    for d in ds:
     if d['path'].endswith('@width'):n.need(math.isclose(float(d['after']),target,abs_tol=0.0001),'line conversion')
   if field=='layer_rect':
    left,top,right,bottom=a['layer_client_rect_i16'];w,h=a['page_pixels'];values={'horizontalPadding':left,'verticalPadding':top,'rightPadding':w-right,'bottomPadding':h-bottom}
    for d in ds:
     k=d['path'].split('@')[-1]
     if k in values:n.need(math.isclose(float(d['after']),values[k]/h*2950,abs_tol=0.0006),'native rect mapping')
   n.need((folder/'exit-status.txt').read_text().strip()=='124','unexpected GUI termination')
   n.need('OBSERVER_LAYER_MODE coordinate, actual=1' in (folder/'application.log').read_text(),'coordinate mode not set')
   report.append({'case':case,'target_and_expected_dependent_changes_only':True,'unchanged_native_double_cells':result['native_numeric_cells'],'changed_bytes':len(m['changed_offsets']),'source_and_numeric_and_cache_preservation':True,'application_property_conversion_matches_source':True,'visual_review':'NOT PERFORMED by this verifier; see separately recorded visual evidence','Origin_reopen':'NOT RUN'})
 (ROOT/'verified-results.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--evidence-root',type=Path,default=ROOT,help='Local directory containing fixtures/, candidates/ and application/results/; outputs summaries here')
 args=parser.parse_args();ROOT=args.evidence_root.resolve();app.ROOT=ROOT/'application/results'
 print(json.dumps(verify(),indent=2))
