import unittest
from unittest.mock import patch
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import ep7_expanded_node as p
class ExpandedNode(unittest.TestCase):
 def test_reject_before_tool(self):
  with patch.object(p.subprocess,'check_output',side_effect=AssertionError('launched')) as tool:
   with self.assertRaises(ValueError):p.inspect(b'bad',Path('/not/tool'))
   tool.assert_not_called()
 def test_unique_windows(self):
  for a in p.WITNESSES:self.assertEqual(sum(s<=a<e for s,e in p.WINDOWS.values()),1)
 def test_request_thresholds_not_stride(self):
  for a,n in [(0x60022700,128),(0x60022709,2048),(0x60022713,16384)]:self.assertEqual(p.WITNESSES[a],('cmp',f'{n},d0'))
 def test_pointer_queue_not_node_copy(self):
  self.assertEqual(p.WITNESSES[0x6029c665],('mov','4,d0'))
  self.assertEqual(p.WITNESSES[0x6029c667],('mov','d0,d1'))
  self.assertEqual(p.WITNESSES[0x6020b94f],('movhu','d1,(6,a0)'))
  self.assertEqual(p.WITNESSES[0x6020b98b],('mov','d0,(4,sp)'))
 def test_five_frees(self):
  for a in (0x602a31b1,0x602a4461,0x6029f1c2,0x602a4220,0x6029f6ba):self.assertEqual(p.WITNESSES[a],('call','0x60022732,[],4'))
 def test_alternate_node_is_native_56(self):
  self.assertEqual(p.WITNESSES[0x6029ce67],('mov','56,d0'))
  self.assertEqual(p.WITNESSES[0x6029f51b],('mov','56,d0'))
 def test_deferred_metadata_has_other_record_register(self):
  self.assertEqual(p.WITNESSES[0x602ac5ef],('mov','d0,d2'))
  self.assertEqual(p.WITNESSES[0x602ac609],('call','0x602ac8d0,[],0'))
 def test_alternate_envelope_node_free(self):
  self.assertEqual(p.WITNESSES[0x6029f512],('mov','(8,a0),d2'))
  self.assertEqual(p.WITNESSES[0x6029f615],('mov','d2,d0'))
  self.assertEqual(p.WITNESSES[0x6029f617],('call','0x602a4d34,[d2,d3,a2,a3],36'))
  self.assertEqual(p.WITNESSES[0x6029f6ac],('mov','(8,a0),a2'))
  self.assertEqual(p.WITNESSES[0x6029f6b9],('mov','a2,a0'))
if __name__=='__main__':unittest.main()
