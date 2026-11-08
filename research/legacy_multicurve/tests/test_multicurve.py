import copy,json,os,struct,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from native_multicurve import *
from make_cases import raw_for,make_case
from unittest.mock import patch
from numeric_support import Rejected
FIXTURE=os.environ.get('ORIGIN_PUBLIC_FIXTURE')
class Inputs(unittest.TestCase):
    def raw(self):return json.loads(raw_for(2))
    def reject(self,obj):
        with self.assertRaises((ValueError,Rejected)):parse_raw(json.dumps(obj).encode())
    def test_explicit_bindings(self):
        for n in SERIES_COUNTS:
            _,s,l=parse_raw(raw_for(n));self.assertEqual(len(s),n);self.assertEqual(len(l),100*n)
            self.assertEqual(len({v for a in s for v in (a['x_dataset_id'],a['y_dataset_id'])}),2*n)
            for a in s[1:]:self.assertNotEqual(a['x'],s[0]['x'])
    def test_unequal(self):
        for key in ('x','y'):
            o=self.raw();o['series'][1][key].pop();self.reject(o)
    def test_missing_pair(self):
        for value in (None,'','NaN','Infinity','--','1e309','1e-999','1e-320','9007199254740993'):
            o=self.raw();o['series'][1]['x'][3]=value;self.reject(o)
    def test_missing_x(self):
        o=self.raw();del o['series'][1]['x'];self.reject(o)
    def test_duplicate_ids(self):
        for key in ('series_id','x_column','y_column'):
            o=self.raw();o['series'][1][key]=o['series'][0][key];self.reject(o)
    def test_wrong_sheet(self):
        o=self.raw();o['series'][1]['sheet']='Book2';self.reject(o)
    def test_boolean(self):
        o=self.raw();o['series'][1]['x'][0]=True;self.reject(o)
    def test_nonnumeric_json(self):
        with self.assertRaises((ValueError,Rejected)):parse_raw(b'{bad')
    def test_duplicate_key(self):
        with self.assertRaises((ValueError,Rejected)):parse_raw(b'{"schema":1,"schema":2}')
    def test_measurement_claim(self):
        o=self.raw();o['data_kind']='measured';self.reject(o)
    def test_no_extra_input(self):
        o=self.raw();o['series'][1]['guess_x_from']='A';self.reject(o)
    def test_native_safe_default(self):
        with self.assertRaisesRegex(Rejected,'Origin-safe export refused'):patch_bytes(None,None)
        with self.assertRaisesRegex(Rejected,'Origin-safe export refused'):generate('/does/not/exist','/does/not/exist','/does/not/exist')
    def test_wrapper_native_safe_default(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(Rejected,'Origin-safe export refused'):make_case('/does/not/exist',2,Path(d))
            self.assertEqual(list(Path(d).iterdir()),[])
    def test_signed_zero_and_raw_rounding(self):
        o,s,l=parse_raw(raw_for(2));self.assertEqual(struct.pack('>d',s[1]['x'][25]).hex(),'8000000000000000')
        self.assertEqual([r for r in l if r['raw_numeric_lexeme']=='0.1234567890123456789012345'][0]['conversion'],'rounded_to_nearest_ties_even')
    def test_symlink_and_fifo(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'link').symlink_to('/tmp')
            with self.assertRaises(Rejected):checked_path(p/'link'/'anything')
            os.mkfifo(p/'fifo')
            with self.assertRaises(Rejected):read_regular(p/'fifo',100)
    def test_parent_traversal(self):
        with self.assertRaises(Rejected):checked_path('/tmp/../tmp')
@unittest.skipUnless(FIXTURE,'set ORIGIN_PUBLIC_FIXTURE for exact external fixture')
class Native(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.template=Path(FIXTURE).read_bytes()
    def test_grammar(self):
        w=inspect(self.template,1);self.assertEqual(len(w.frames),478);self.assertEqual(w.tail_start,228955)
    def test_patch_all(self):
        for n in SERIES_COUNTS:
            b,m=patch_bytes(self.template,raw_for(n),research_only=True);w=inspect(b,n)
            self.assertEqual(len(w.datasets),25+2*(n-1));self.assertEqual(b[w.tail_start:],self.template[228955:]);self.assertFalse(m['safe_native_export_supported'])
            _,s,_=parse_raw(raw_for(n))
            for a in s:
                for key in ('x','y'):
                    payload=w.datasets[a[key+'_dataset_id']-1][1].payload
                    self.assertEqual(payload,column_payload(a[key]))
    def test_hash_guard(self):
        b=bytearray(self.template);b[-1]^=1
        with self.assertRaises(Rejected):patch_bytes(bytes(b),raw_for(2),research_only=True)
    def test_export_and_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);raw=p/'toy.json';raw.write_bytes(raw_for(2));out=p/'generated'
            generate(FIXTURE,raw,out,research_only=True)
            self.assertEqual((out/'raw.json').read_bytes(),raw_for(2));self.assertEqual((out/'rollback.opj').read_bytes(),self.template)
            with self.assertRaises(Rejected):generate(FIXTURE,raw,out,research_only=True)
    def test_defaults_do_not_touch_disk(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'out'
            with self.assertRaises(Rejected):generate(FIXTURE,FIXTURE,p)
            self.assertFalse(p.exists())
    def test_truncated_frame(self):
        for cut in (0,16,18,500,228954):
            with self.assertRaises((Rejected,UnicodeError)):inspect(self.template[:cut],1)
    def test_wrapper_bad_template_prewrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);bad=p/'bad.opj';bad.write_bytes(b'bad')
            with self.assertRaises(Rejected):make_case(bad,2,p,research_only=True)
            self.assertFalse((p/'candidates').exists())
    def test_wrapper_existing_destination_prewrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);c=p/'candidates';c.mkdir();(c/'curves2').mkdir()
            with self.assertRaises(Rejected):make_case(FIXTURE,2,p,research_only=True)
            self.assertFalse((c/'synthetic2.json').exists())
    def test_wrapper_symlink_destination_prewrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);c=p/'candidates';c.mkdir();(c/'curves2').symlink_to('/tmp')
            with self.assertRaises(Rejected):make_case(FIXTURE,2,p,research_only=True)
            self.assertFalse((c/'synthetic2.json').exists())
    def test_wrapper_failed_generate_rolls_back(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            with patch('make_cases.generate',side_effect=Rejected('simulated generation failure')):
                with self.assertRaises(Rejected):make_case(FIXTURE,2,p,research_only=True)
            self.assertFalse((p/'candidates').exists())
    def test_wrapper_exclusive_raw_race(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);target=p/'candidates/synthetic2.json';op=Path.open
            def raced(path,mode='r',*args,**kwargs):
                if path==target and mode=='xb':
                    with op(path,'wb') as f:f.write(b'raced')
                return op(path,mode,*args,**kwargs)
            with patch.object(Path,'open',raced):
                with self.assertRaises(FileExistsError):make_case(FIXTURE,2,p,research_only=True)
            self.assertEqual(target.read_bytes(),b'raced');self.assertFalse((p/'candidates/curves2').exists())
    def test_wrapper_output_race(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);target=p/'candidates/curves2'
            def raced(*args,**kwargs):target.mkdir();return generate(*args,**kwargs)
            with patch('make_cases.generate',raced):
                with self.assertRaises(Rejected):make_case(FIXTURE,2,p,research_only=True)
            self.assertTrue(target.is_dir());self.assertFalse((p/'candidates/synthetic2.json').exists())
    def test_wrong_curve_ids(self):
        b,m=patch_bytes(self.template,raw_for(2),research_only=True);w=inspect(b,2);p=w.windows[6]['layers'][0]['curves'][1][0].offset+5+35
        bad=bytearray(b);struct.pack_into('<H',bad,p,1)
        with self.assertRaisesRegex(Rejected,'explicit graph XY'):inspect(bytes(bad),2)
if __name__=='__main__':unittest.main()
