"""Adversarial verification checks, including normal and optimized Python."""
from pathlib import Path
import copy,csv,io,json,os,shutil,subprocess,sys,tempfile,unittest
import xml.etree.ElementTree as E
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import native_active_rows as native
import verify_application as application
import verify_source_artifacts as source
import verify_synthetic_observations as observations

class XMLTests(unittest.TestCase):
    def test_exact_leading_and_trailing_text(self):
        for before,after in [('<a> x</a>','<a>x</a>'),('<a>x </a>','<a>x</a>'),('<a>\nx\n</a>','<a>x</a>')]:
            self.assertTrue(application.diff(E.fromstring(before),E.fromstring(after)))
    def test_exact_leading_and_trailing_tail(self):
        for before,after in [('<a><b/> x</a>','<a><b/>x</a>'),('<a><b/>x </a>','<a><b/>x</a>')]:
            self.assertTrue(application.diff(E.fromstring(before),E.fromstring(after)))
    def test_none_and_empty_distinct_in_text_and_tail(self):
        for attr in ('text','tail'):
            a,b=E.Element('a'),E.Element('a');setattr(b,attr,'')
            self.assertTrue(application.diff(a,b))
    def test_indentation_is_not_ignored(self):
        self.assertTrue(application.diff(E.fromstring('<a>\n<b/>\n</a>'),E.fromstring('<a><b/></a>')))
    def test_substantive_attributes_checked(self):
        self.assertTrue(application.diff(E.fromstring('<a width="1"/>'),E.fromstring('<a width="2"/>')))
    def test_only_documented_volatile_attributes_ignored(self):
        self.assertEqual(application.diff(E.fromstring('<a uuid="1" creation_time="x"/>'),E.fromstring('<a uuid="2" creation_time="y"/>')),[])

FIXTURE=Path(os.environ.get('ORIGIN_PUBLIC_FIXTURE','/not-materialized'))
@unittest.skipUnless(FIXTURE.is_file(),'Exact separately obtained public fixture required')
class SourceTests(unittest.TestCase):
    def setUp(self):
        self.original=FIXTURE.read_bytes();self.raw=(ROOT/'candidates/raw7.csv').read_bytes()
        self.candidate,self.manifest,self.before,self.after=native.patch_bytes(self.original,self.raw)
    def check(self,candidate=None,manifest=None,before=source._ABSENT,after=source._ABSENT):
        return source.verify_candidate(self.original,self.raw,self.candidate if candidate is None else candidate,self.manifest if manifest is None else manifest,before,after)
    def test_exact_candidate_and_manifest_accepted(self):self.check(before=self.before,after=self.after)
    def test_opaque_tail_tamper_even_with_new_hash_rejected(self):
        b=bytearray(self.candidate);b[-1]^=1;m=copy.deepcopy(self.manifest);m['candidate_sha256']=native.sha(b)
        with self.assertRaises(RuntimeError):self.check(bytes(b),m)
    def test_false_preservation_flags_rejected(self):
        for key in ('native_graph_source_bytes_unchanged','source_inactive_cells_retained','unknown_curve_range_fields_untouched'):
            m=copy.deepcopy(self.manifest);m[key]=False
            with self.assertRaises(RuntimeError):self.check(manifest=m)
    def test_boolean_number_substitution_rejected(self):
        m=copy.deepcopy(self.manifest);m['native_graph_source_bytes_unchanged']=1
        with self.assertRaises(RuntimeError):self.check(manifest=m)
    def test_signed_zero_ledger_substitution_rejected(self):
        m=copy.deepcopy(self.manifest);m['binary64_conversion_ledger'][0]['binary64_value']=0.0
        with self.assertRaises(RuntimeError):self.check(manifest=m)
    def test_before_after_inspection_tamper_rejected(self):
        for keyword in ('before','after'):
            for bad in (None,{},dict(self.before,sha256='0'*64)):
                with self.assertRaises(RuntimeError):self.check(**{keyword:bad})
    def test_same_forged_hash_logs_do_not_prove_source(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'source-evidence.opj').write_bytes(self.candidate)
            for f in ('input.before.sha256','input.after.sha256'):(p/f).write_text('0'*64+'  candidate.opj\n')
            with self.assertRaises(RuntimeError):source.verify_hash_records(p,self.candidate)
    def test_snapshot_must_match_hash_records(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'source-evidence.opj').write_bytes(self.original)
            for f in ('input.before.sha256','input.after.sha256'):(p/f).write_text(native.sha(self.candidate)+'  candidate.opj\n')
            with self.assertRaises(RuntimeError):source.verify_hash_records(p,self.candidate)

class ObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'candidates').mkdir();shutil.copyfile(ROOT/'candidates/raw7.csv',self.root/'candidates/raw7.csv')
        self.data=self.root/'evidence/synthetic-observations/active7'
        shutil.copytree(ROOT/'evidence/synthetic-observations/active7',self.data)
    def tearDown(self):self.temp.cleanup()
    def check(self):
        with patch.object(observations,'ROOT',self.root):return observations.check(7)
    def modify_curve(self,edit):
        p=self.data/'curve-observation.json';c=json.loads(p.read_text());edit(c);p.write_text(json.dumps(c))
        with self.assertRaises((ValueError,KeyError)):self.check()
    def test_retained_actual_evidence_accepted(self):self.assertEqual(self.check()['bit_exact_active_values'],14)
    def test_mask_change_rejected(self):self.modify_curve(lambda c:c['rows'][0].update(x_masked=True))
    def test_validity_change_rejected(self):self.modify_curve(lambda c:c['rows'][7].update(y_valid=True))
    def test_signed_zero_signal_change_rejected(self):self.modify_curve(lambda c:c['point_signal_emissions'][0]['logical_points_binary64'][0].__setitem__(0,'0000000000000000'))
    def test_wrong_point_count_rejected(self):self.modify_curve(lambda c:c['point_signal_emissions'][0].update(logical_point_count=6))
    def test_wrong_range_rejected(self):self.modify_curve(lambda c:c['point_signal_emissions'][0].update(start_index=1))
    def test_no_signal_rejected(self):self.modify_curve(lambda c:c.update(point_signal_emissions=[]))
    def test_curve_source_bit_change_rejected(self):self.modify_curve(lambda c:c['rows'][0].update(x_bits='0000000000000000'))
    def test_signed_zero_API_change_rejected(self):
        p=self.data/'native-app-values.tsv';p.write_text(p.read_text().replace('8000000000000000','0000000000000000',1))
        with self.assertRaises(ValueError):self.check()
    def test_missing_cell_API_change_rejected(self):
        p=self.data/'native-app-values.tsv';p.write_text(p.read_text().replace('7ff8000000000000','0000000000000000',1))
        with self.assertRaises(ValueError):self.check()

@unittest.skipUnless(FIXTURE.is_file(),'Exact separately obtained public fixture required')
class MakeCasesTests(unittest.TestCase):
    def run_case(self,setup=None,success=False):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            for name in ('make_cases.py','native_active_rows.py','numeric_support.py'):shutil.copyfile(ROOT/name,p/name)
            (p/'candidates').mkdir()
            for n in (7,49,50):shutil.copyfile(ROOT/f'candidates/raw{n}.csv',p/f'candidates/raw{n}.csv')
            if setup:setup(p)
            env=os.environ.copy();env['ORIGIN_PUBLIC_FIXTURE']=str(FIXTURE.resolve());env['PYTHONDONTWRITEBYTECODE']='1'
            result=subprocess.run([sys.executable,str(p/'make_cases.py')],capture_output=True,text=True,env=env)
            if success:
                self.assertEqual(result.returncode,0,result.stderr)
                for n in (7,49,50):
                    candidate=p/f'candidates/generated{n}/candidate.opj'
                    self.assertTrue(candidate.is_file())
                    self.assertEqual((candidate.parent/'rollback.opj').read_bytes(),FIXTURE.read_bytes())
                for n in (51,257):self.assertFalse((p/f'candidates/refused{n}').exists())
            else:
                self.assertNotEqual(result.returncode,0,result.stderr)
                self.assertFalse((p/'candidates/generated7/manifest.json').exists())
                if (p/'victim').exists():self.assertEqual((p/'victim').read_bytes(),b'unchanged')
    def test_clean_generation_and_refusals(self):self.run_case(success=True)
    def test_existing_csv_is_not_overwritten(self):self.run_case(lambda p:(p/'candidates/raw7.csv').write_bytes(b'changed'))
    def test_csv_symlink_not_followed(self):
        def setup(p):
            (p/'victim').write_bytes(b'unchanged');(p/'candidates/raw7.csv').unlink();(p/'candidates/raw7.csv').symlink_to(p/'victim')
        self.run_case(setup)
    def test_existing_generated_directory_refused(self):self.run_case(lambda p:(p/'candidates/generated7').mkdir())
    def test_existing_report_refused(self):self.run_case(lambda p:(p/'refusal-evidence.json').write_text('old'))

class RunnerTests(unittest.TestCase):
    def reject(self,args,setup=None):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);shutil.copyfile(ROOT/'application/run.sh',p/'run.sh')
            input=p/'input.opj';input.write_bytes(b'not a fixture')
            if setup:setup(p)
            env=os.environ.copy();env['LABPLOT_RUNTIME_ROOT']=str(p/'no-runtime')
            args=[str(input) if a=='INPUT' else a for a in args]
            result=subprocess.run(['bash',str(p/'run.sh'),*args],env=env,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertFalse((p/'results/original/application.log').exists())
            return result.stderr
    def test_argument_count(self):
        for a in ([],['original'],['original','INPUT','plot','extra']):self.reject(a)
    def test_case_traversal_and_unvalidated_count(self):
        for name in ('../escape','/tmp/out','a/b','.','..','-case','a b','a\nb','','active51','active257'):
            self.assertIn('Unsafe or unsupported',self.reject([name,'INPUT']))
    def test_unknown_mode(self):self.assertIn('Unsupported layer mode',self.reject(['original','INPUT','coordinate']))
    def test_existing_result_and_profile(self):
        for kind in ('results','profiles'):
            self.assertIn('Refusing existing',self.reject(['original','INPUT'],lambda p:(p/kind/'original').mkdir(parents=True)))
    def test_dangling_result_symlink(self):
        def setup(p):
            (p/'results').mkdir();(p/'results/original').symlink_to(p/'absent')
        self.assertIn('Refusing existing',self.reject(['original','INPUT'],setup))
    def test_symlink_parent_rejected(self):
        for kind in ('results','profiles'):
            self.assertIn('Unsafe result/profile parent',self.reject(['original','INPUT'],lambda p:(p/kind).symlink_to(p/'absent')))
    def test_wrong_fixture_refused_without_app(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source.opj';p.write_bytes(b'not a public fixture')
            with self.assertRaises(RuntimeError):source.verify_run_input('original',p,ROOT)

if __name__=='__main__':unittest.main(verbosity=2)
