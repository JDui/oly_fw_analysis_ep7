import unittest
from unittest.mock import patch
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import ep7_text_rollback as p
class Rollback(unittest.TestCase):
 def test_wrong_stock_first(self):
  with patch.object(p.subprocess,'check_output',side_effect=AssertionError) as run:
   with self.assertRaises(ValueError):p.inspect(b'wrong',Path('/bad'))
   run.assert_not_called()
 def test_unique_windows(self):
  for a in p.WITNESSES:self.assertEqual(sum(s<=a<e for s,e in p.WINDOWS.values()),1)
 def test_base_destructor_not_cleanup(self):self.assertEqual(p.WITNESSES[0x60cfd791],('mov','1624237513,a0'))
 def test_layout_release(self):self.assertEqual(p.WITNESSES[0x60cfe1f7],('call','0x60d109db,[],4'))
 def test_guard_widths(self):
  self.assertEqual(p.WITNESSES[0x60d048d6],('movbu','(88,a3),d0'))
  self.assertEqual(p.WITNESSES[0x60d04c16],('movbu','(68,a0),d0'))
 def test_ctor_parent_zero(self):self.assertEqual(p.WITNESSES[0x60cfd767],('mov','d0,(20,a2)'))
 def test_noop(self):self.assertEqual(p.WITNESSES[0x60cfeafe],('retf','[],0'))
 def test_native_allocator_selection(self):self.assertEqual(p.WITNESSES[0x60d02c81],('mov','(244,a1),a1'))
if __name__=='__main__':unittest.main()
