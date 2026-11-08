from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"code"))
import ctypes,ctypes.util,random,unittest
from lz4_block import decode_block,DecodeRefused
class BlockTests(unittest.TestCase):
 def test_literal_only(self):self.assertEqual(decode_block(b'\x50hello',5),b'hello')
 def test_empty_refused(self):
  with self.assertRaises(DecodeRefused):decode_block(b'',1)
 def test_mismatched_size(self):
  with self.assertRaises(DecodeRefused):decode_block(b'\x50hello',6)
 def test_literal_bounds(self):
  with self.assertRaises(DecodeRefused):decode_block(b'\x60hello',6)
 def test_zero_offset(self):
  with self.assertRaises(DecodeRefused):decode_block(b'\x10a\0\0',5)
 def test_offset_before_start(self):
  with self.assertRaises(DecodeRefused):decode_block(b'\x10a\x02\0',5)
 def test_extension_truncation(self):
  with self.assertRaises(DecodeRefused):decode_block(b'\xf0\xff',30)
 def test_match_overrun(self):
  with self.assertRaises(DecodeRefused):decode_block(b'\x1fa\x01\x00\xff',30)
 def test_declared_bound(self):
  with self.assertRaises(DecodeRefused):decode_block(b'\x50hello',1<<30)
 def test_types(self):
  with self.assertRaises(DecodeRefused):decode_block(bytearray(b'\x50hello'),5)
 def test_bool_not_int(self):
  with self.assertRaises(DecodeRefused):decode_block(b'\x10a',True)
 def test_terminal_sequence_required(self):
  with self.assertRaises(DecodeRefused):decode_block(b'\x10a\x01\x00',5)
 def test_terminal_five_literals_required(self):
  with self.assertRaises(DecodeRefused):decode_block(b'\x10a\x01\x00\x10z',6)
 def test_too_near_final_match(self):
  with self.assertRaises(DecodeRefused):decode_block(b'\x10a\x01\x00\x50hello',10)
 def test_existing_liblz4_synthetic_1000_cases(self):
  path=ctypes.util.find_library('lz4')
  if path is None:self.skipTest('Installed independent liblz4 unavailable')
  lib=ctypes.CDLL(path);lib.LZ4_compressBound.argtypes=[ctypes.c_int];lib.LZ4_compressBound.restype=ctypes.c_int
  lib.LZ4_compress_default.argtypes=[ctypes.c_char_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int];lib.LZ4_compress_default.restype=ctypes.c_int
  rng=random.Random(20261108)
  for i in range(1000):
   n=rng.randint(1,8192);alphabet=rng.choice((1,2,3,8,16,256));raw=bytes(rng.randrange(alphabet) for _ in range(n));capacity=lib.LZ4_compressBound(n);dest=ctypes.create_string_buffer(capacity);count=lib.LZ4_compress_default(raw,dest,n,capacity)
   self.assertGreater(count,0);packed=dest.raw[:count];self.assertEqual(decode_block(packed,n),raw)
   with self.assertRaises(DecodeRefused):decode_block(packed,n+1)
if __name__=='__main__':unittest.main(verbosity=2)
