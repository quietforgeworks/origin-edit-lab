"""Public synthetic checks. No original Origin file or measurement is loaded."""
from pathlib import Path
import errno
import struct
import tempfile
import unittest
from unittest import mock
import bootstrap
import atomic_output as atomic
import csv_contract as csv
from modern_fpc_patch import parse_record, rewrite_segment, f64_bits, PatchRefused
from writeback import make_delta, restore_delta

class SyntheticNativeTests(unittest.TestCase):
    def test_csv_demo(self):
        columns=csv.parse_csv((Path(__file__).parent/'inputs/synthetic-demo.csv').read_bytes())
        self.assertEqual(len(columns[0]),9)
        self.assertEqual(columns[1][-1],0)

    def test_csv_bom(self):
        data=b'x,y\n'+b'1,2\n'*9
        self.assertEqual(csv.parse_csv(data), csv.parse_csv(b'\xef\xbb\xbf'+data))

    def test_csv_signed_zero(self):
        data=b'x,y\n'+b'-0,0\n'*9
        self.assertEqual(csv.numeric_bits(csv.parse_csv(data)[0][0]),1<<63)

    def test_csv_invalid(self):
        for token in [b'NaN', b'inf', b'', b'1e-999', b'=2+2', b'1e300']:
            with self.subTest(token=token), self.assertRaises(csv.InputRefused):
                csv.parse_csv(b'x,y\n'+token+b',1\n'+b'2,3\n'*8)

    def test_csv_shape(self):
        for data in [b'x,y\n'+b'1,2\n'*8,b'x,y,z\n'+b'1,2,3\n'*9]:
            with self.assertRaises(csv.InputRefused):csv.parse_csv(data)

    def test_csv_read_limit(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'data';p.write_bytes(b'x'*20)
            with self.assertRaises(csv.InputRefused):csv.read_limited(p,10)

    def test_fpc_mutation_and_preservation(self):
        # Two full-width residuals for [1.0, 2.0], value predictor initially zero.
        record=b'\xff\xff\x02\x00\x03\x0c\x77'+struct.pack('<dd',1.,2.)
        blob=b'prefix'+record+b'suffix'
        values,segments,end=parse_record(blob,6)
        self.assertEqual(values,[f64_bits(1.),f64_bits(2.)])
        changed=rewrite_segment(blob,segments[0],[f64_bits(3.),f64_bits(4.)])
        self.assertEqual(parse_record(changed,6)[0],[f64_bits(3.),f64_bits(4.)])
        self.assertEqual(changed[:13],blob[:13]);self.assertEqual(changed[end:],blob[end:])

    def test_fpc_width_refusal(self):
        blob=b'\xff\xff\x02\x00\x03\x0c\x00'
        values,segments,_=parse_record(blob,0)
        self.assertEqual(values,[0,0])
        with self.assertRaises(PatchRefused):rewrite_segment(blob,segments[0],[f64_bits(1.),0])

    def test_fpc_malformed(self):
        for blob in [b'',b'\xff\xff',b'\xff\xff\x02\x00\x03\x0c\x77']:
            with self.assertRaises(PatchRefused):parse_record(blob,0)

    def test_delta_restoration(self):
        source=b'synthetic payload only'
        candidate,manifest=make_delta(source,[(0,b'synthetic',b'SYNTHETIC')],kind='synthetic-test',detail={})
        self.assertEqual(restore_delta(candidate,manifest),source)
        with self.assertRaises(ValueError):restore_delta(candidate+b'x',manifest)

    def test_publication_success_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'new'
            result=atomic.publish_new_directory(out,{'test.txt':b'synthetic'})
            self.assertTrue(result['published']);self.assertEqual((out/'test.txt').read_bytes(),b'synthetic')
            with self.assertRaises(ValueError):atomic.publish_new_directory(out,{'test.txt':b'other'})

    def test_publication_failure_cleans(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'new'
            with mock.patch.object(atomic,'rename_noreplace',side_effect=OSError(errno.ENOSPC,'synthetic fault')):
                with self.assertRaises(atomic.PublicationError) as caught:
                    atomic.publish_new_directory(out,{'test.txt':b'synthetic'})
            self.assertFalse(caught.exception.published)
            self.assertFalse(out.exists());self.assertEqual(list(Path(d).iterdir()),[])

    def test_publication_refuses_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'new';out.symlink_to(Path(d)/'missing')
            with self.assertRaises(ValueError):atomic.publish_new_directory(out,{'test.txt':b'synthetic'})

    def test_publication_traversal_refused(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):atomic.publish_new_directory(Path(d)/'new',{'../escape':b'x'})

if __name__=='__main__':unittest.main()
