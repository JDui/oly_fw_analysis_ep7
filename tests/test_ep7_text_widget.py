import unittest
from unittest.mock import patch
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import ep7_text_widget as p
class TextWidget(unittest.TestCase):
 def test_bad_stock_before_tools(self):
  with patch.object(p.subprocess,'check_output',side_effect=AssertionError('launched')) as child:
   with self.assertRaises(ValueError):p.inspect(b'wrong',Path('/not/tool'))
   child.assert_not_called()
 def test_unique_coverage(self):
  for a in p.WITNESSES:self.assertEqual(sum(s<=a<e for s,e in p.WINDOWS.values()),1)
 def test_type5_inline_string(self):
  self.assertEqual(p.WITNESSES[0x60e8518c],('add','8,a1'))
  self.assertEqual(p.WITNESSES[0x60e8528b],('call','0x60d4c9df,[d2,d3,a2,a3],24'))
 def test_halfword_nul_length(self):
  self.assertEqual(p.WITNESSES[0x60d178ae],('movhu','(a1),d1'))
  self.assertEqual(p.WITNESSES[0x60d178ba],('add','2,a0'))
 def test_release_before_allocate(self):
  self.assertEqual(p.WITNESSES[0x60d4ca0d],('call','0x60d109db,[],4'))
  self.assertEqual(p.WITNESSES[0x60d4ca29],('call','0x60d109d1,[],4'))
 def test_owned_copy_not_borrow(self):
  self.assertEqual(p.WITNESSES[0x60d4ca25],('inc','d2'))
  self.assertEqual(p.WITNESSES[0x60d4ca26],('add','d2,d2'))
  self.assertEqual(p.WITNESSES[0x60d4ca4c],('call','0x47001052,[d2,d3,a2,a3],28'))
 def test_destructor_frees_owned_string(self):
  self.assertEqual(p.WITNESSES[0x60d4be49],('mov','d0,(156,a2)'))
  self.assertEqual(p.WITNESSES[0x60d4be82],('call','0x60d109db,[],4'))
 def test_paint_reaches_text_primitive(self):
  self.assertEqual(p.WITNESSES[0x60d4c510],('add','156,a0'))
  self.assertEqual(p.WITNESSES[0x60d4c61c],('mov','(16,sp),d1'))
  self.assertEqual(p.WITNESSES[0x60d4c61e],('call','0x60d075a7,[d2,d3,a2,a3],252'))
if __name__=='__main__':unittest.main()
