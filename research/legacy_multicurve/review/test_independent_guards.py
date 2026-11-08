"""Independent adversarial checks of the source API. No private user files."""
import copy,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,os.environ['MULTICURVE_SOURCE'])
import native_multicurve as n
import make_cases as m
from numeric_support import Rejected,publish_noreplace
FIXTURE=Path(os.environ['ORIGIN_PUBLIC_FIXTURE'])
class IndependentGuards(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name);self.raw=self.p/'raw.json';self.raw.write_bytes(m.raw_for(2))
    def tearDown(self):self.tmp.cleanup()
    def check_clean(self):self.assertFalse((self.p/'out').exists());self.assertEqual(list(self.p.glob('.multicurve-*')),[])
    def test_default_all_entrypoints_no_io(self):
        with patch.object(n,'read_regular',side_effect=AssertionError('unexpected I/O')):
            for flag in (False,None,0,1,'yes'):
                with self.assertRaisesRegex(Rejected,'Origin-safe export refused'):n.generate(None,None,self.p/'out',research_only=flag)
                with self.assertRaisesRegex(Rejected,'Origin-safe export refused'):n.patch_bytes(None,None,research_only=flag)
        with self.assertRaisesRegex(Rejected,'Origin-safe export refused'):m.make_case('/does/not/exist',2,self.p)
        self.assertFalse((self.p/'candidates').exists());self.check_clean()
    def test_nested_symlinks_all_path_roles(self):
        target=self.p/'target';target.mkdir();(target/'child').mkdir();alias=self.p/'alias';alias.symlink_to(target,target_is_directory=True)
        for template,raw,out in ((FIXTURE,self.raw,alias/'child/out'),(alias/'child/input',self.raw,self.p/'out'),(FIXTURE,alias/'child/input',self.p/'out')):
            with self.assertRaisesRegex(Rejected,'symlink'):n.generate(template,raw,out,research_only=True)
        self.assertEqual(list((target/'child').iterdir()),[]);self.check_clean()
    def test_symlink_leaf_existing_and_dangling(self):
        for target in (self.raw,self.p/'absent'):
            out=self.p/'out';out.symlink_to(target)
            with self.assertRaises(Rejected):n.generate(FIXTURE,self.raw,out,research_only=True)
            self.assertTrue(out.is_symlink());out.unlink()
    def test_fifo_inputs_refuse_without_blocking(self):
        f=self.p/'fifo';os.mkfifo(f)
        for template,raw in ((f,self.raw),(FIXTURE,f)):
            with self.assertRaisesRegex(Rejected,'regular file'):n.generate(template,raw,self.p/'out',research_only=True)
        self.check_clean()
    def test_injected_publish_failure_cleans_stage(self):
        with patch.object(n,'publish_noreplace',side_effect=RuntimeError('injected')):
            with self.assertRaisesRegex(RuntimeError,'injected'):n.generate(FIXTURE,self.raw,self.p/'out',research_only=True)
        self.check_clean()
    def test_raced_directory_destination_preserved(self):
        def raced(stage,out):
            out.mkdir();(out/'winner').write_bytes(b'concurrent winner');publish_noreplace(stage,out)
        with patch.object(n,'publish_noreplace',side_effect=raced):
            with self.assertRaisesRegex(Rejected,'already exists'):n.generate(FIXTURE,self.raw,self.p/'out',research_only=True)
        self.assertEqual((self.p/'out/winner').read_bytes(),b'concurrent winner');self.assertEqual(list(self.p.glob('.multicurve-*')),[])
    def test_raced_symlink_destination_preserved(self):
        def raced(stage,out):out.symlink_to(self.raw);publish_noreplace(stage,out)
        with patch.object(n,'publish_noreplace',side_effect=raced):
            with self.assertRaisesRegex(Rejected,'already exists'):n.generate(FIXTURE,self.raw,self.p/'out',research_only=True)
        self.assertTrue((self.p/'out').is_symlink());self.assertEqual(self.raw.read_bytes(),m.raw_for(2));self.assertEqual(list(self.p.glob('.multicurve-*')),[])
    def test_input_changed_before_publication_refuses(self):
        real=n.read_regular;counts={}
        def changed(path,limit):
            key=str(path);counts[key]=counts.get(key,0)+1;data=real(path,limit)
            return data+b' ' if Path(path)==self.raw and counts[key]>1 else data
        with patch.object(n,'read_regular',side_effect=changed):
            with self.assertRaisesRegex(Rejected,'source changed'):n.generate(FIXTURE,self.raw,self.p/'out',research_only=True)
        self.check_clean()
    def test_wrapper_prewrite_and_rollback(self):
        root=self.p/'wrapper';root.mkdir();candidate=root/'candidates';candidate.mkdir();(candidate/'curves2').mkdir()
        with self.assertRaises(Rejected):m.make_case(FIXTURE,2,root,research_only=True)
        self.assertFalse((candidate/'synthetic2.json').exists());(candidate/'curves2').rmdir()
        with patch.object(m,'generate',side_effect=RuntimeError('injected')):
            with self.assertRaisesRegex(RuntimeError,'injected'):m.make_case(FIXTURE,2,root,research_only=True)
        self.assertEqual(list(candidate.iterdir()),[])
    def test_wrapper_candidates_ancestor_symlink_prewrite(self):
        root=self.p/'wrapper';root.mkdir();target=self.p/'target';target.mkdir();(root/'candidates').symlink_to(target,target_is_directory=True)
        with self.assertRaisesRegex(Rejected,'symlink'):m.make_case(FIXTURE,2,root,research_only=True)
        self.assertEqual(list(target.iterdir()),[])
    def test_numeric_rejections_and_arrays(self):
        base=json.loads(m.raw_for(2))
        values=[None,True,False,0,0.1,'',' ','NaN','nan','Inf','Infinity','-Infinity','1e309','1e-999','5e-324','1e-308','9007199254740993','0x1','1_0','1,2','1\n','1'*129,'1.7976931348623157e308','-1.23456789e-300']
        # The last arbitrary tiny normal is allowed in X; do not confuse conservatism with validity.
        values=values[:-1]
        from numeric_support import MISSING
        values.append(repr(MISSING))
        for v in values:
            o=copy.deepcopy(base);o['series'][1]['x'][4]=v
            with self.subTest(token=repr(v)):
                with self.assertRaises((ValueError,Rejected)):n.parse_raw(json.dumps(o).encode())
        for key in ('x','y'):
            for count in (0,1,49,51):
                o=copy.deepcopy(base);o['series'][1][key]=['0']*count
                with self.assertRaises(Rejected):n.parse_raw(json.dumps(o).encode())
    def test_identity_missing_fields_and_count_refusals(self):
        base=json.loads(m.raw_for(2))
        for key in ('sheet','series_id','x_column','y_column','x','y'):
            o=copy.deepcopy(base);del o['series'][1][key]
            with self.assertRaises(Rejected):n.parse_raw(json.dumps(o).encode())
        for key,value in (('sheet','Book2'),('series_id','S01'),('x_column','A'),('y_column','B')):
            o=copy.deepcopy(base);o['series'][1][key]=value
            with self.assertRaises(Rejected):n.parse_raw(json.dumps(o).encode())
        for count in (0,1,3,4,6,11):
            o=copy.deepcopy(base);o['series']=[base['series'][0]]*count
            with self.assertRaises(Rejected):n.parse_raw(json.dumps(o).encode())
    def test_wrapper_failed_attempt_keeps_replaced_raw(self):
        root=self.p/'wrapper';root.mkdir()
        def replace_and_fail(template,raw,out,**kw):
            raw.unlink();raw.write_bytes(b'new concurrent owner');raise RuntimeError('injected replacement')
        with patch.object(m,'generate',side_effect=replace_and_fail):
            with self.assertRaisesRegex(RuntimeError,'injected replacement'):m.make_case(FIXTURE,2,root,research_only=True)
        self.assertEqual((root/'candidates/synthetic2.json').read_bytes(),b'new concurrent owner')
if __name__=='__main__':unittest.main()
