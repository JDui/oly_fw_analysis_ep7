import unittest
from unittest.mock import patch
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import ep7_kind19_lifetime as p
class Lifetime(unittest.TestCase):
 def test_reject_before_tools(self):
  with patch.object(p.subprocess,'check_output',side_effect=AssertionError('launched')) as child:
   with self.assertRaises(ValueError):p.inspect(b'wrong',Path('/not/tool'))
   child.assert_not_called()
 def test_unique_window_coverage(self):
  for a in p.WITNESSES:self.assertEqual(sum(s<=a<e for s,e in p.WINDOWS.values()),1)
 def test_send_then_local_return(self):
  self.assertEqual(p.WITNESSES[0x602ac869],('call','0x6020beb4,[d2,d3],48'))
  self.assertEqual(p.WITNESSES[0x602ac870],('ret','[d2,a2,a3],32'))
 def test_ack_identity_and_free(self):
  self.assertEqual(p.WITNESSES[0x603df988],('mov','(48,a2),d0'))
  self.assertEqual(p.WITNESSES[0x602ac496],('mov','(8,a0),a2'))
  self.assertEqual(p.WITNESSES[0x602ac4d2],('call','0x60022732,[],4'))
 def test_alternate_free_path_not_qualified(self):
  self.assertEqual(p.WITNESSES[0x602ac489],('call','0x602acf50,[d2,d3,a2,a3],40'))
 def test_optional_early_notification(self):
  self.assertEqual(p.WITNESSES[0x603f2af2],('cmp','3,d0'))
  self.assertEqual(p.WITNESSES[0x603f2b01],('mov','(48,a2),d1'))
  self.assertEqual(p.WITNESSES[0x603f2b08],('calls','(a1)'))
  self.assertEqual(p.WITNESSES[0x602ac87e],('mov','92,d1'))
 def test_selected_id_not_assumed_equal(self):
  self.assertEqual(p.WITNESSES[0x602a9674],('mov','(a1),d0'))
  self.assertEqual(p.WITNESSES[0x602a9677],('mov','(a2),d0'))
 def test_profile_reads_not_selector_store(self):
  self.assertEqual(p.WITNESSES[0x603018d6],('add','3180,a2'))
  self.assertEqual(p.WITNESSES[0x6030195c],('add','24083,a0'))
  self.assertEqual(p.WITNESSES[0x60301960],('movbu','(a0),d0'))
  self.assertEqual(p.WITNESSES[0x60301988],('movhu','d0,(a2)'))
if __name__=='__main__':unittest.main()
