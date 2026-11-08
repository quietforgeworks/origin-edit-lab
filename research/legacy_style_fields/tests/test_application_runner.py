"""Runner input rejection needs no runtime and never launches LabPlot."""
from pathlib import Path
import os,subprocess,tempfile,shutil,unittest
SCRIPT=Path(__file__).resolve().parents[1]/'application/run.sh'
class RunnerGuardTests(unittest.TestCase):
 def reject(self,args,expected=2,setup=None):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);script=root/'run.sh';shutil.copyfile(SCRIPT,script)
   if setup:setup(root)
   env=os.environ.copy();env['LABPLOT_EXTERNAL_VIEWER_ROOT']=str(root/'no-runtime')
   result=subprocess.run(['bash',str(script),*args],env=env,capture_output=True,text=True)
   self.assertEqual(result.returncode,expected,result.stderr)
   return result.stderr
 def test_argument_count(self):
  for args in ([],['case'],['case','input','plot','extra']):self.reject(args)
 def test_case_identifiers(self):
  for name in ('../outside','/tmp/out','a/b','.','..','-case','a b','a\nb',''):
   self.assertIn('Unsafe case identifier',self.reject([name,'missing']))
 def test_unknown_mode(self):self.assertIn('Unsupported layer mode',self.reject(['safe','missing','bad']))
 def test_missing_input(self):self.reject(['safe','missing'])
 def test_existing_profile_rejected(self):
  self.assertIn('Refusing existing case or profile',self.reject(['safe',str(SCRIPT)],3,lambda root:(root/'profiles/safe').mkdir(parents=True)))
if __name__=='__main__':unittest.main()
