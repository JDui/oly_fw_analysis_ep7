import unittest
from unittest.mock import patch
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import ep7_ui_native_status as p
class Status(unittest.TestCase):
 def test_wrong_build_before_tools(self):
  with patch.object(p.subprocess,'check_output',side_effect=AssertionError('launched')) as tool:
   with self.assertRaises(ValueError):p.inspect(b'wrong',Path('/not/tool'))
   tool.assert_not_called()
 def test_window_coverage(self):
  for a in p.WITNESSES:self.assertEqual(sum(s<=a<e for s,e in p.WINDOWS.values()),1)
 def test_sector_native_one(self):self.assertEqual(p.WITNESSES[0x60e21f43],('mov','1,d0'))
 def test_value_returns_child_result(self):self.assertEqual(p.WITNESSES[0x60e21cfc],('mov','a2,d0'))
 def test_info_wrapper_timer_on_one(self):
  self.assertEqual(p.WITNESSES[0x60e20d25],('cmp','1,d0'))
  self.assertEqual(p.WITNESSES[0x60e20d2c],('mov','500,d0'))
 def test_four_not_generic_handled(self):
  self.assertEqual(p.WITNESSES[0x60dd545d],('cmp','4,d0'))
  self.assertEqual(p.WITNESSES[0x60dd5857],('mov','535,d0'))
 def test_one_viewer_and_other_results(self):
  self.assertEqual(p.WITNESSES[0x60e4d115],('cmp','1,d0'))
  self.assertEqual(p.WITNESSES[0x60e4d123],('calls','(a1)'))
  for a,b in [(0x60e4d12b,1),(0x60e4d133,2),(0x60e4d13b,3)]:self.assertEqual(p.WITNESSES[a],('mov',f'{b},d0'))
 def test_handler137_distinct_state_result(self):
  self.assertEqual(p.WITNESSES[0x60e5da9f],('cmp','1,d0'))
  self.assertEqual(p.WITNESSES[0x60e5dada],('mov','1,d3'))
  self.assertEqual(p.WITNESSES[0x60e5dadc],('mov','4,d2'))
if __name__=='__main__':unittest.main()
