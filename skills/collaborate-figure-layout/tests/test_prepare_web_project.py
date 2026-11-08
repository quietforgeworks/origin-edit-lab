import base64,hashlib,importlib.util,json,re,sys,tempfile,unittest,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import prepare_web_project as prepare
import layout_boxes as lb
spec=importlib.util.spec_from_file_location('offline_builder',ROOT/'assets/web-layout/build-offline.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jCXkAAAAASUVORK5CYII=')
class PrepTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name)
  self.core={'schema':lb.FMT,'projectId':'synthetic-test-project','canvas':{'width':200,'height':150,'unit':'mm'},'refinement':{'mode':'existing-aesthetics','references':[]},'panels':[{'id':f'p{i}','name':f'Plot {i}','parentPanelId':'pair','initialBounds':{'x':i*50,'y':20,'w':40,'h':50},'sourceAssetIds':[f'source{i}'],'sourceBindings':[{'privatePath':'PRIVATE_SOURCE_SENTINEL'}]} for i in (1,2)]}
  (self.p/'thumbnail.png').write_bytes(PNG);self.images={'p1':str(self.p/'thumbnail.png'),'p2':str(self.p/'thumbnail.png')};(self.p/'previews.json').write_text(json.dumps(self.images));self.write_binding()
 def write_binding(self):
  (self.p/'binding.json').write_text(json.dumps({**self.core,'mapHash':lb.jhash(self.core)}))
 def run_prepare(self,mode='offline',title='拖动图片编排'):
  return prepare.prepare(self.p/'binding.json',self.p/'previews.json',self.p/'out',self.p/'audit.json',title,mode)
 def test_offline_is_single_self_contained_html_with_semantic_groups(self):
  r=self.run_prepare();h=Path(r['outputFile']).read_text();project=json.loads((self.p/'out/project.json').read_text())
  self.assertEqual(r['panelCount'],2);self.assertFalse(r['hostingPerformed']);self.assertIn("connect-src 'none'",h);self.assertEqual(h.count('<script>'),1);self.assertNotIn('fetch(',h);self.assertNotIn('PRIVATE_SOURCE_SENTINEL',h);self.assertNotIn('sourceBindings',h);self.assertEqual(project['panels'][0]['parentPanelId'],'pair');self.assertIn('data:image/png;base64,',h)
 def test_screenshot_first_ui_remains_offline_with_optional_backup(self):
  r=self.run_prepare();h=Path(r['outputFile']).read_text()
  self.assertIn('完成后截图发回对话',h);self.assertIn('导出备份（可选）',h);self.assertNotIn('完成，导出布局',h)
  self.assertIn('Shift 点击添加 / 取消多选',h);self.assertIn('方向键微调 1 mm',h)
  script=re.search(r'<script>(.*?)</script>',h,re.S).group(1)
  digest='sha256-'+base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
  self.assertIn("script-src '"+digest+"'",h)
  for operation in ['fetch(', 'XMLHttpRequest', 'WebSocket', 'sendBeacon']:
   self.assertNotIn(operation,script)
 @unittest.skipUnless(shutil.which('node'),'Node is needed for offline interaction tests')
 def test_offline_selection_and_keyboard_behavior(self):
  result=subprocess.run(['node','--test',str(ROOT/'tests/offline_layout_controls.test.cjs')],text=True,capture_output=True)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
 def test_malicious_labels_are_inert_json_data(self):
  self.core['panels'][0]['name']='</script><img src=x onerror=alert(1)>\u2028\u2029';self.write_binding();r=self.run_prepare(title='</script><script>alert(2)</script>');h=Path(r['outputFile']).read_text()
  self.assertEqual(h.count('<script>'),1);self.assertEqual(h.count('</script>'),1);self.assertNotIn('<img src=x',h);self.assertIn('\\u003c/script>',h);self.assertIn('\\u2028',h);self.assertIn('\\u2029',h)
 def test_online_has_no_real_site_registration_or_source_objects(self):
  r=self.run_prepare('online');self.assertTrue(r['requiresPrivateSiteSetup']);self.assertFalse((self.p/'out/.openai/hosting.json').exists());self.assertTrue((self.p/'out/.openai/hosting.example.json').exists());project=json.loads((self.p/'out/dist/project.json').read_text());self.assertNotIn('sourceBindings',json.dumps(project));self.assertTrue((self.p/'out/worker/index.js').exists())
 def test_binding_tamper_is_rejected(self):
  p=json.loads((self.p/'binding.json').read_text());p['mapHash']='0'*64;(self.p/'binding.json').write_text(json.dumps(p));self.assertRaises(ValueError,self.run_prepare)
 def test_output_overwrite_is_rejected(self):
  self.run_prepare();self.assertRaises(ValueError,self.run_prepare)
 def test_png_type_is_enforced(self):
  (self.p/'thumbnail.png').write_text('<svg onload="alert(1)"></svg>');self.assertRaises(ValueError,self.run_prepare)
 def test_offline_preview_escape_is_rejected(self):
  self.run_prepare();p=json.loads((self.p/'out/project.json').read_text());p['panels'][0]['preview']='../thumbnail.png';self.assertRaises(ValueError,builder.normalize,p,(self.p/'out').resolve())
 @unittest.skipUnless(shutil.which('node'),'Node is needed for JS validation tests')
 def test_frontend_rejects_wrong_project_map_schema_and_malformed_geometry(self):
  self.run_prepare();project=json.loads((self.p/'out/project.json').read_text());js=(ROOT/'assets/web-layout/app.js').read_text();functions=js[js.index('function migrate('):js.index('function output(')]
  script="const vm=require('vm'),assert=require('assert');const input=JSON.parse(require('fs').readFileSync(0,'utf8'));const c={source:input.source};vm.createContext(c);vm.runInContext(input.functions,c);const good={schema:input.source.schema,projectId:input.source.projectId,mapHash:input.source.mapHash,canvas:structuredClone(input.source.canvas),selectedPanels:input.source.panels.map(p=>({id:p.id,bounds:p.initialBounds})),omittedPanelIds:[]};assert.equal(c.validate(good).panels.length,2);for(const change of [x=>x.schema='old',x=>x.projectId='other',x=>x.mapHash='wrong',x=>x.canvas.width++,x=>delete x.canvas,x=>x.canvas.unit='px',x=>x.selectedPanels[0].bounds.x=Infinity,x=>x.selectedPanels[0].bounds.w=-1,x=>x.selectedPanels.push(x.selectedPanels[0])]){const x=structuredClone(good);change(x);assert.throws(()=>c.validate(x));}const old=structuredClone(good);old.mapHash='a'.repeat(64);old.selectedPanels=[{id:'pair',bounds:{x:50,y:20,w:100,h:50}}];old.omittedPanelIds=[];input.source.layoutMigration={fromMapHash:old.mapHash,splitPanels:{pair:['p1','p2']}};c.source=input.source;const migrated=c.validate(old);assert.equal(migrated.panels.length,2);assert.equal(migrated.panels[1].bounds.x,100);old.selectedPanels=[];old.omittedPanelIds=['pair'];assert.equal(c.validate(old).panels.length,0);console.log('9 invalid imports rejected; split selection and omission migrated');"
  result=subprocess.run(['node','-e',script],input=json.dumps({'source':project,'functions':functions}),text=True,capture_output=True);self.assertEqual(result.returncode,0,result.stderr)
 def test_explicit_migration_file_retains_known_split_mapping(self):
  migration={'fromMapHash':'a'*64,'splitPanels':{'pair':['p1','p2']}};path=self.p/'migration.json';path.write_text(json.dumps(migration))
  prepare.prepare(self.p/'binding.json',self.p/'previews.json',self.p/'out',self.p/'audit.json','布局','offline',path)
  self.assertEqual(json.loads((self.p/'out/project.json').read_text())['layoutMigration'],migration)
 def test_duplicate_or_unknown_migration_children_rejected(self):
  for children in [['p1','p1'],['p1','missing']]:
   path=self.p/'migration.json';path.write_text(json.dumps({'fromMapHash':'a'*64,'splitPanels':{'pair':children}}))
   self.assertRaises(ValueError,prepare.prepare,self.p/'binding.json',self.p/'previews.json',self.p/'out',self.p/'audit.json','布局','offline',path)
 def test_old_schema_is_rejected(self):
  self.core['schema']='figure-layout-roundtrip/v0';self.write_binding();self.assertRaises(ValueError,self.run_prepare)
if __name__=='__main__':unittest.main()
