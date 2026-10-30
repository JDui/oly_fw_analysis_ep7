import unittest
from unittest.mock import patch
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import ep7_text_creation as p
class Creation(unittest.TestCase):
 def test_bad_stock_first(self):
  with patch.object(p.subprocess,'check_output',side_effect=AssertionError) as run:
   with self.assertRaises(ValueError):p.inspect(b'bad',Path('/bad'))
   run.assert_not_called()
 def test_unique_coverage(self):
  for a in p.WITNESSES:self.assertEqual(sum(s<=a<e for s,e in p.WINDOWS.values()),1)
 def test_factory_size(self):self.assertEqual(p.WITNESSES[0x60d33b02],('mov','180,d0'))
 def test_resource_extent(self):self.assertEqual(p.WITNESSES[0x60d4c043],('movhu','(92,a2),d0'))
 def test_parent_pointer(self):self.assertEqual(p.WITNESSES[0x60cfdfe0],('mov','a1,(20,a0)'))
 def test_attach_failure(self):
  self.assertEqual(p.WITNESSES[0x60cfef8d],('clr','d0'))
  self.assertEqual(p.WITNESSES[0x60cfef9e],('mov','a3,(8,a0)'))
 def test_cleanup_reachable(self):self.assertEqual(p.WITNESSES[0x60d42dc3],('call','0x60d02c03,[d2,d3,a2,a3],32'))
 def test_destructor_then_deallocator(self):
  self.assertEqual(p.WITNESSES[0x60d02ca6],('calls','(a1)'))
  self.assertEqual(p.WITNESSES[0x60d02ca8],('mov','a0,a1'))
  self.assertEqual(p.WITNESSES[0x60d02caa],('calls','(a1)'))
if __name__=='__main__':unittest.main()
