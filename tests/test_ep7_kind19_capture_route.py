import unittest
from unittest.mock import patch
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import ep7_kind19_capture_route as p
class Kind19Route(unittest.TestCase):
 def test_bad_stock_before_tools(self):
  with patch.object(p.subprocess,'check_output',side_effect=AssertionError('launched')) as child:
   with self.assertRaises(ValueError):p.inspect(b'wrong stock',Path('/not/tool'))
   child.assert_not_called()
 def test_window_coverage(self):
  for a in p.WITNESSES:self.assertEqual(sum(s<=a<e for s,e in p.WINDOWS.values()),1)
 def test_same_id_two_destinations(self):
  self.assertEqual(p.WITNESSES[0x602a316f],('mov','d2,(a2)'))
  self.assertEqual(p.WITNESSES[0x602a3196],('mov','d2,(a0)'))
  self.assertEqual(p.WITNESSES[0x602a319b],('mov','a0,(8,a2)'))
 def test_dereference_before_metadata(self):
  self.assertEqual(p.WITNESSES[0x602ac3d9],('call','0x602ac8d0,[],0'))
  self.assertEqual(p.WITNESSES[0x602ac8dc],('mov','(a0),d0'))
  self.assertEqual(p.WITNESSES[0x602ac754],('mov','d2,(8,a3)'))
 def test_kind19_not_kind16(self):
  self.assertEqual(p.WITNESSES[0x602ac84f],('mov','19,d0'))
  self.assertEqual(p.WITNESSES[0x602ac757],('mov','8193,d0'))
  self.assertEqual(p.WITNESSES[0x603ef930],('movhu','(0x60040e32),d0'))
 def test_new_ctor_existing_family(self):
  self.assertEqual(p.WITNESSES[0x603f283e],('call','0x603537eb,[d2,d3,a2,a3],44'))
  self.assertEqual(p.WITNESSES[0x603f2850],('call','0x603e62d1,[d2,d3,a2,a3],72'))
  self.assertEqual(p.WITNESSES[0x603f2890],('call','0x603e61b8,[d2,a2,a3],24'))
  self.assertEqual(p.WITNESSES[0x603f28c0],('call','0x603e6c8d,[a2,a3],24'))
 def test_constructor_error_guard(self):
  self.assertEqual(p.WITNESSES[0x603f284d],('bne','0x603f285c'))
  self.assertEqual(p.WITNESSES[0x603f2882],('bne','0x603f28b0'))
 def test_exact_operands(self):
  p.require_instruction('603f283e: dd ad 0f f6 ff f0 2c call 0x603537eb,[d2,d3,a2,a3],44',0x603f283e,'call','0x603537eb,[d2,d3,a2,a3],44')
  with self.assertRaises(ValueError):p.require_instruction('603f283e: dd ad 0f f6 ff f0 2c call 0x603537eb,[],0',0x603f283e,'call','0x603537eb,[d2,d3,a2,a3],44')
if __name__=='__main__':unittest.main()
