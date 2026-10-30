import unittest
from unittest.mock import patch
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import ep7_viewer_data as p
class Viewer(unittest.TestCase):
 def test_bad_build_before_tool(self):
  with patch.object(p.subprocess,'check_output',side_effect=AssertionError('launched')) as tool:
   with self.assertRaises(ValueError):p.inspect(b'bad',Path('/not/tool'))
   tool.assert_not_called()
 def test_unique_windows(self):
  for a in p.WITNESSES:self.assertEqual(sum(s<=a<e for s,e in p.WINDOWS.values()),1)
 def test_scalar_property_not_12array(self):
  self.assertEqual(p.WITNESSES[0x60e272e0],('mov','1091,d0'))
  self.assertEqual(p.WITNESSES[0x60e2741b],('movhu','(d0,a1),d0'))
  self.assertEqual(p.WITNESSES[0x60e2741d],('mov','(8,a2),a2'))
 def test_native_value_only_11keys(self):
  self.assertEqual(p.WITNESSES[0x60e27494],('mov','11,d1'))
  self.assertEqual(p.WITNESSES[0x60e274ad],('mov','11,d1'))
 def test_lookup_is_byte_output_not_draw(self):
  self.assertEqual(p.WITNESSES[0x60df24fc],('mov','(4,a1),d0'))
  self.assertEqual(p.WITNESSES[0x60df24ff],('movbu','d0,(a0)'))
  self.assertEqual(p.WITNESSES[0x60df2504],('add','8,a1'))
 def test_native_buffers(self):
  self.assertEqual(p.WITNESSES[0x60e26ac9],('mov','334,d1'))
  self.assertEqual(p.WITNESSES[0x60e26adb],('mov','44,d1'))
  self.assertEqual(p.WITNESSES[0x60e2729a],('mov','6,d0'))
 def test_copy_not_drawing_api(self):
  self.assertEqual(p.WITNESSES[0x60ea4c22],('mov','-11,d1'))
  self.assertEqual(p.WITNESSES[0x60ea4c27],('mov','d0,(a1)'))
  self.assertEqual(p.WITNESSES[0x60d7adbb],('call','0x60ea4c2e,[],0'))
 def test_publishes_native_display_service(self):
  self.assertEqual(p.WITNESSES[0x60e26bdd],('mov','229,d0'))
  self.assertEqual(p.WITNESSES[0x60e26be0],('mov','334,d1'))
  self.assertEqual(p.WITNESSES[0x60d7adc8],('mov','65508,d0'))
if __name__=='__main__':unittest.main()
