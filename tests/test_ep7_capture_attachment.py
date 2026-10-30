import unittest
from unittest.mock import patch
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import ep7_capture_attachment as p
class CaptureAttachment(unittest.TestCase):
 def test_wrong_stock_before_subprocess(self):
  with patch.object(p.subprocess,'check_output',side_effect=AssertionError('launched')) as child:
   with self.assertRaises(ValueError): p.inspect(b'not stock',Path('/no/tool'))
   child.assert_not_called()
 def test_one_window_per_witness(self):
  for a in p.WITNESSES:self.assertEqual(sum(s<=a<e for s,e in p.WINDOWS.values()),1)
 def test_retire_order(self):
  self.assertEqual(p.WITNESSES[0x6029be5d],('call','0x603db89e,[],4'))
  self.assertEqual(p.WITNESSES[0x6029be6a],('movhu','d0,(a2)'))
  self.assertLess(0x6029be5d,0x6029be6a)
 def test_node_free_branch(self):
  self.assertEqual(p.WITNESSES[0x602a4456],('ble','0x602a4460'))
  self.assertEqual(p.WITNESSES[0x602a4459],('call','0x6029b686,[d2],28'))
  self.assertEqual(p.WITNESSES[0x602a4461],('call','0x60022732,[],4'))
 def test_clone_order(self):
  self.assertEqual(p.WITNESSES[0x603edbc5],('mov','d0,(28,a2)'))
  self.assertEqual(p.WITNESSES[0x603edbce],('call','0x47001052,[d2,d3,a2,a3],28'))
  self.assertEqual(p.WITNESSES[0x603edbd5],('ret','[a2,a3],12'))
 def test_prepopulation_queue(self):
  self.assertEqual(p.WITNESSES[0x602a323d],('call','0x6020b98b,[],8'))
  self.assertEqual(p.WITNESSES[0x602a31d1],('call','0x602a3204,[d2,a2],16'))
  self.assertLess(0x602a31d1,0x602a31ea)
 def test_exact_instruction(self):
  p.require_instruction('6029be6a: f0 72 movhu d0,(a2)',0x6029be6a,'movhu','d0,(a2)')
  with self.assertRaises(ValueError):p.require_instruction('6029be6a: f0 72 movhu d1,(a2)',0x6029be6a,'movhu','d0,(a2)')
 def test_allocation_and_population(self):
  self.assertEqual(p.WITNESSES[0x602a316f],('mov','d2,(a2)'))
  self.assertEqual(p.WITNESSES[0x602a31a4],('mov','d2,(a0)'))
  self.assertEqual(p.WITNESSES[0x602a31ea],('call','0x602a7ea0,[d2,d3,a2,a3],20'))
if __name__=='__main__':unittest.main()
