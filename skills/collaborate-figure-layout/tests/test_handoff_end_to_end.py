"""Exercise the packaged HTTP service and assistant CLI with synthetic source only."""
import base64, copy, json, subprocess, sys, time, unittest, urllib.request
from pathlib import Path
from PIL import Image
import test_local_handoff as fixtures

class EndToEnd(unittest.TestCase):
 def test_user_signal_read_lock_propose_refresh_confirm(self):
  fixture=fixtures.HandoffTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
  root=fixture.p/'out'
  proc=subprocess.Popen([sys.executable,'-B',str(root/'server.py'),'--port','0'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  def stop():
   proc.terminate();proc.wait(timeout=5);proc.stdout.close();proc.stderr.close()
  self.addCleanup(stop)
  for _ in range(100):
   if (root/'session.json').exists():break
   time.sleep(.02)
  url=json.loads((root/'session.json').read_text())['url'].rstrip('/')
  def post(path,obj):
   req=urllib.request.Request(url+path,data=json.dumps(obj).encode(),headers={'Content-Type':'application/json','Origin':url})
   with urllib.request.urlopen(req) as res:return json.load(res)
  def cli(*args,ok=True):
   q=subprocess.run([sys.executable,'-B',str(root/'assistant_layout.py'),*args],capture_output=True,text=True)
   self.assertEqual(q.returncode,0 if ok else 1,q.stderr+q.stdout)
   return json.loads(q.stdout)
  # Actual user save -> assistant reads same revision, no screenshot/export.
  state=cli('read');layout=state['layout'];layout['guideWorkflow']={'mode':'constrained','proposalReady':False}
  layout['guides']=[{'id':'user1','axis':'x','pos':30,'color':'#189db7','kind':'frame','owner':'user','label':'frame','targets':['p1']}]
  post('/api/state',{'author':'user','revision':0,'layout':layout})
  state=cli('read');self.assertEqual(state['revision'],1);cli('read-confirmed',ok=False)
  lock=cli('lock','--revision','1')['lock']['id']
  proposal=copy.deepcopy(state['layout']);proposal['guideWorkflow']['proposalReady']=True
  proposal['guides'].append({'id':'assistant1','axis':'y','pos':50,'color':'#bc892d','kind':'center','owner':'assistant','label':'center','targets':['p1']})
  path=root/'proposal.json';path.write_text(json.dumps(proposal))
  out=cli('apply','--layout',str(path),'--revision','1','--lock-id',lock);self.assertEqual(out['revision'],2)
  cli('unlock','--lock-id',lock)
  # Refresh-equivalent GET sees new revision; confirmation is separately required.
  refreshed=cli('read');self.assertEqual(refreshed['layout']['guides'][0],layout['guides'][0]);cli('read-confirmed',ok=False)
  cli('confirm','--revision','1',ok=False)
  confirmed=cli('confirm','--revision','2');self.assertEqual(confirmed['confirmation']['revision'],2)
  confirmed=cli('read-confirmed');self.assertEqual(len(confirmed['refinementInput']['selectedPanels']),2)
  self.assertNotIn('guides',confirmed['refinementInput']);self.assertEqual(confirmed['refinementInput']['guidePositionPolicy'],'display-only')
  self.assertNotIn('pos',confirmed['refinementInput']['alignmentRelations'][0])
  # Refined PNG refresh goes through a separate guarded action, preserving geometry.
  lock=cli('lock','--revision','2')['lock']['id']
  source=json.loads((root/'source.json').read_text());Image.new('RGB',(12,12),'blue').save(root/'render.png');png=(root/'render.png').read_bytes()
  preview_file=root/'preview-update.json';preview_file.write_text(json.dumps({'projectId':source['projectId'],'mapHash':source['mapHash'],'previews':{'p1':'render.png'}}))
  update=cli('update-previews','--previews',str(preview_file),'--revision','2','--lock-id',lock)
  self.assertEqual(update['revision'],3);cli('unlock','--lock-id',lock)
  refreshed=cli('read');self.assertEqual(refreshed['layout'],confirmed['layout']);self.assertNotIn('dataUrl',refreshed['displayPreviews']['p1'])
  complete=cli('read','--include-previews');self.assertEqual(base64.b64decode(complete['displayPreviews']['p1']['dataUrl'].split(',')[1]),png)
  with urllib.request.urlopen(url+'/api/state?view=summary') as res:summary=json.load(res)
  self.assertEqual(summary,refreshed)
  with urllib.request.urlopen(url+'/api/state') as res:full=json.load(res)
  self.assertIn('dataUrl',full['displayPreviews']['p1'])
  # A foreign preview manifest must fail before the local identity is added to the request.
  key=cli('lock','--revision','3')['lock']['id'];bad=source.copy();bad['projectId']='wrong';bad['previews']={'p1':'render.png'}
  preview_file.write_text(json.dumps(bad));cli('update-previews','--previews',str(preview_file),'--revision','3','--lock-id',key,ok=False)
  self.assertEqual(cli('read')['revision'],3);cli('unlock','--lock-id',key)
  cli('read-confirmed',ok=False)
  with urllib.request.urlopen(url+'/') as res:html=res.read().decode()
  self.assertIn('doc.displayPreviews',html)
  # Later edits invalidate approval rather than using an old frozen snapshot.
  post('/api/state',{'author':'user','revision':3,'layout':proposal});cli('read-confirmed',ok=False)
  # A stale/rebound session must not acquire a lock against another project.
  wrong=copy.deepcopy(source);wrong['projectId']='another-project';(root/'source.json').write_text(json.dumps(wrong))
  failed=cli('lock','--revision','4',ok=False);self.assertIn('error',failed)
  with urllib.request.urlopen(url+'/api/lock') as res:self.assertIsNone(json.load(res)['lock'])

if __name__=='__main__':unittest.main()
