import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('custom', ROOT / 'src/custom_data.py')
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
TEMPLATE = Path(os.environ.get('CUSTOM_TEMPLATE', str(ROOT.parent / 'origin-data-generation/row-range-v3/research/kde-fixtures/origin8_test_tree_import.opj')))

def csv_bytes(n):
    initial = [('-0','-0.0'), ('-5','-0.1'), ('55','1.1'),
        ('1.00000000000000011102230246251565404236316680908203125','0.1'),
        ('2.2250738585072014e-308','-2.2250738585072014e-308'),
        ('+01.2500e+1','0.3333333333333333333333333333333333333'), ('54.99999999999999','1.0999999999999999')]
    pairs = initial + [(str((i * 7 % 50) + .125), str(((i * 13) % 80 + 5) / 100)) for i in range(7,n)]
    return ('A,B\r\n' + ''.join('"'+a+'",'+b+'\r\n' for a,b in pairs[:n])).encode()

def provenance(kind='synthetic'):
    return json.dumps({'schema':'custom-data-provenance-v1','declared_kind':kind,
        'statement':'Known generated non-toy numerical stress input; not a measurement.' if kind == 'synthetic' else 'Caller-supplied declaration only; not independently verified.'}, indent=1).encode()

class CustomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = TEMPLATE.read_bytes()
        cls.cases = {n:c.expected_artifacts(cls.original,csv_bytes(n),provenance(),research_opt_in=True) for n in (7,49,50)}
    def verify(self, files, raw=None, decl=None):
        return c.verify_artifacts(files, expected_csv_sha256=c.sha(raw or files['raw.csv']),
             expected_declaration_sha256=c.sha(decl or files['declaration.json']),research_opt_in=True)
    def test_all_shapes_and_full_ledger(self):
        for n,files in self.cases.items():
            with self.subTest(n=n):
                report=self.verify(files);self.assertEqual(report['active_rows'],n)
                self.assertEqual(files['raw.csv'],csv_bytes(n));self.assertEqual(files['rollback.opj'],self.original)
                m=c.strict_json(files['manifest.json']);self.assertEqual(len(m['binary64_conversion_ledger']),2*n)
                self.assertTrue(m['binary64_conversion_ledger'][0]['negative_zero'])
                self.assertEqual(m['binary64_conversion_ledger'][0]['binary64_little_endian_hex'],'0000000000000080')
                self.assertEqual(m['binary64_conversion_ledger'][6]['binary64_value'],1.)
                self.assertEqual(m['binary64_conversion_ledger'][6]['conversion'],'rounded_to_nearest_ties_even')
                env=c.strict_json(files['bundle.json'])
                self.assertEqual(sum(len(x['retained_binary64_little_endian_hex']) for x in env['inactive_template_cells_retained']),2*(50-n))
                self.assertFalse(env['native_safe_export_supported']);self.assertEqual(env['origin_lifecycle'],'NOT_RUN')
    def test_each_artifact_tamper_all_shapes(self):
        for n,files in self.cases.items():
            for name in c.FILES:
                with self.subTest(n=n,name=name):
                    bad=dict(files);b=bytearray(bad[name]);b[len(b)//2]^=1;bad[name]=bytes(b)
                    with self.assertRaises(Exception):self.verify(bad,files['raw.csv'],files['declaration.json'])
    def test_every_active_cell_tamper_all_shapes(self):
        backend,_=c.load_backend()
        for n,files in self.cases.items():
            for offset,size,kind in backend.ranges(n):
                with self.subTest(n=n,offset=offset):
                    bad=dict(files);b=bytearray(bad['candidate.opj']);b[offset]^=1;bad['candidate.opj']=bytes(b)
                    with self.assertRaises(Exception):self.verify(bad)
    def test_unknown_graph_inactive_and_source_tamper(self):
        for name in ('candidate.opj','rollback.opj'):
            for offset in (0,31,745,180000,219422,231493):
                bad=dict(self.cases[7]);b=bytearray(bad[name]);b[offset]^=1;bad[name]=bytes(b)
                with self.assertRaises(Exception):self.verify(bad)
    def test_semantic_json_tamper(self):
        for name in ('manifest.json','before.json','after.json','bundle.json'):
            for field,value in [('unknown',1),('unknown',True),('unknown',-0.0)]:
                bad=dict(self.cases[50]);obj=c.strict_json(bad[name]);obj[field]=value;bad[name]=c.json_bytes(obj)
                with self.assertRaises(Exception):self.verify(bad)
        for name in (n for n in c.FILES if n.endswith('.json')):
            for value in (b'{"x":1,"x":1}',b'{"x":NaN}',b'{"x":Infinity}',b'{"x":1e999}'):
                bad=dict(self.cases[50]);bad[name]=value
                with self.assertRaises(Exception):self.verify(bad)
    def test_numeric_invalid_missing_and_unsupported_shapes(self):
        for token in ('','NaN','Infinity','1e999','1e-999','5e-324','9007199254740993',' 1','1 ','--1','1_0','56'):
            raw=csv_bytes(7).replace(b'"-0"',token.encode(),1)
            with self.subTest(token=token),self.assertRaises(Exception):c.expected_artifacts(self.original,raw,provenance(),research_opt_in=True)
        for n in (0,1,6,8,48,51,257,1024):
            raw=('A,B\n'+'1,0.5\n'*n).encode()
            with self.subTest(n=n),self.assertRaises(Exception):c.expected_artifacts(self.original,raw,provenance(),research_opt_in=True)
        for raw in (b'A,C\n'+b'1,0.5\n'*7,b'A,B\n'+b'1,0.5,1\n'*7,b'A,B\n'+b'1\n'*7,b'\xff', b'A,B\n'+b'"1,0.5\n'*7):
            with self.assertRaises(Exception):c.expected_artifacts(self.original,raw,provenance(),research_opt_in=True)
    def test_missing_sentinel(self):
        backend,_=c.load_backend();token=repr(backend.MISSING).encode()
        with self.assertRaises(Exception):c.expected_artifacts(self.original,csv_bytes(7).replace(b'"-0"',token,1),provenance(),research_opt_in=True)
    def test_measured_and_unspecified_never_relabelled(self):
        for kind in ('measured','unspecified'):
            files=c.expected_artifacts(self.original,csv_bytes(50),provenance(kind),research_opt_in=True)
            report=self.verify(files)
            self.assertEqual(report['input_provenance']['caller_declaration']['declared_kind'],kind)
            self.assertFalse(report['input_provenance']['independently_verified'])
            self.assertEqual(files['declaration.json'],provenance(kind))
    def test_opt_in_exact_type(self):
        for value in (False,None,1,'yes'):
            with self.assertRaises(Exception):c.expected_artifacts(self.original,csv_bytes(50),provenance(),research_opt_in=value)
            with self.assertRaises(Exception):c.verify_artifacts(self.cases[50],expected_csv_sha256='0'*64,expected_declaration_sha256='0'*64,research_opt_in=value)
    def test_anchors_and_coordinated_source_substitution(self):
        base=self.cases[50]
        changed=c.expected_artifacts(self.original,csv_bytes(50).replace(b'+01.2500e+1',b'+01.3750e+1'),provenance('measured'),research_opt_in=True)
        with self.assertRaises(Exception):self.verify(changed,base['raw.csv'],base['declaration.json'])
        for anchor in ('',None,True,'g'*64):
            with self.assertRaises(Exception):c.verify_artifacts(base,expected_csv_sha256=anchor,expected_declaration_sha256=c.sha(base['declaration.json']),research_opt_in=True)
    def test_declaration_strict_schema(self):
        for obj in ({}, {'schema':'custom-data-provenance-v1','declared_kind':True,'statement':'x'},
          {'schema':'custom-data-provenance-v1','declared_kind':'measured','statement':'x','extra':1},
          {'schema':'wrong','declared_kind':'synthetic','statement':'x'}):
            with self.assertRaises(Exception):c.expected_artifacts(self.original,csv_bytes(50),c.json_bytes(obj),research_opt_in=True)
    def test_vendor_source_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);shutil.copytree(ROOT/'src/vendor',root/'vendor')
            with patch.object(c,'ROOT',root):
                for name in c.PINNED:
                    path=root/'vendor'/name;original=path.read_bytes();path.write_bytes(original+b'\n# tamper\n')
                    with self.assertRaises(Exception):c.load_backend()
                    path.write_bytes(original)
                (root/'vendor/extra.py').write_text('x=1')
                with self.assertRaises(Exception):c.load_backend()
    def test_generate_verify_recover_filesystem(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'raw.csv').write_bytes(csv_bytes(50));(p/'declaration.json').write_bytes(provenance())
            args=dict(research_opt_in=True,expected_csv_sha256=c.sha(csv_bytes(50)),expected_declaration_sha256=c.sha(provenance()))
            c.generate(TEMPLATE,p/'raw.csv',p/'declaration.json',p/'bundle',research_opt_in=True)
            c.verify(p/'bundle',**args);c.recover(p/'bundle',p/'recovered',**args)
            self.assertEqual((p/'recovered/restored-original.opj').read_bytes(),self.original)
            self.assertEqual((p/'recovered/raw.csv').read_bytes(),csv_bytes(50))
            for output in (p/'bundle',p/'recovered'):
                with self.assertRaises(Exception):c.generate(TEMPLATE,p/'raw.csv',p/'declaration.json',output,research_opt_in=True)
            (p/'alias').symlink_to(p/'raw.csv')
            with self.assertRaises(Exception):c.read_file(p/'alias',32768)
            (p/'diralias').symlink_to(p, target_is_directory=True)
            with self.assertRaises(Exception):c.read_file(p/'diralias/raw.csv',32768)
            with self.assertRaises(Exception):c.read_file(p/'../raw.csv',32768)
            os.mkfifo(p/'fifo')
            with self.assertRaises(Exception):c.read_file(p/'fifo',32768)
            for forbidden in ('src/not-allowed','tests/not-allowed','application/not-allowed','evidence/not-allowed','inputs/not-allowed','unexpected'):
                with self.assertRaises(Exception):c.new_output(ROOT/forbidden)
            with patch.object(c.platform,'system',return_value='Darwin'):
                with self.assertRaises(Exception):c.generate(TEMPLATE,p/'raw.csv',p/'declaration.json',p/'mac',research_opt_in=True)
            for name in c.FILES:
                path=p/'bundle'/name;original=path.read_bytes();path.unlink();path.symlink_to(p/'raw.csv')
                with self.assertRaises(Exception):c.verify(p/'bundle',**args)
                path.unlink();path.write_bytes(original)
            (p/'bundle/extra').write_text('unexpected')
            with self.assertRaises(Exception):c.verify(p/'bundle',**args)
    def test_atomic_publish_race_and_interruption(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            original_load=c.load_backend
            def race():
                backend,verifier=original_load();real=backend.publish_noreplace
                def racing(stage,out):
                    Path(out).mkdir();(Path(out)/'keep').write_bytes(b'racer')
                    real(stage,out)
                backend.publish_noreplace=racing
                return backend,verifier
            with patch.object(c,'load_backend',race),self.assertRaises(Exception):c.publish({'x':b'x'},p/'raced')
            self.assertEqual((p/'raced/keep').read_bytes(),b'racer')
            self.assertFalse(list(p.glob('.custom-data-*')))
            def fail():
                backend,verifier=original_load()
                def interrupted(*args):raise KeyboardInterrupt()
                backend.publish_noreplace=interrupted
                return backend,verifier
            with patch.object(c,'load_backend',fail),self.assertRaises(KeyboardInterrupt):c.publish({'x':b'x'},p/'interrupted')
            self.assertFalse((p/'interrupted').exists());self.assertFalse(list(p.glob('.custom-data-*')))
            def late_failure():
                backend,verifier=original_load();real=backend.publish_noreplace
                def late(stage,out):
                    real(stage,out);raise OSError('injected post-publication failure')
                backend.publish_noreplace=late
                return backend,verifier
            with patch.object(c,'load_backend',late_failure),self.assertRaises(OSError):c.publish({'x':b'x'},p/'published')
            self.assertEqual((p/'published/x').read_bytes(),b'x')

if __name__=='__main__':
    unittest.main(verbosity=2)
