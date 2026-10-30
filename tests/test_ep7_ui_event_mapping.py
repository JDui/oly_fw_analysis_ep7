import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import ep7_ui_event_mapping as p
class Tests(unittest.TestCase):
 def test_guard_before_tool(self):
  with patch.object(p.subprocess,'check_output') as run:
   with self.assertRaises(ValueError):p.inspect(b'wrong',Path('/bad'))
   run.assert_not_called()
 def test_windows_cover_once(self):
  for a in p.WITNESSES:self.assertEqual(sum(lo<=a<hi for lo,hi in p.WINDOWS.values()),1)
 def test_full_delta_not_d1(self):
  self.assertEqual(p.WITNESSES[0x60ea3b35],('movhu','(0x61fc4fb8),d0'))
  for a in (0x60e21cb6,0x60e21f01):self.assertEqual(p.WITNESSES[a],('call','0x60ea3b35,[],0'))
  for a in (0x60e21cd5,0x60e21cef,0x60e21f1c,0x60e21f38):self.assertEqual(p.WITNESSES[a],('clr','d1'))
 def test_producer_before_packet_compression(self):
  for a in (0x60ea0d70,0x60ea0deb,0x60ea0e66):self.assertEqual(p.WITNESSES[a],('call','0x60ea3b2c,[],0'))
  self.assertEqual(p.WITNESSES[0x60ea0e82],('mov','36914,d0'))
  self.assertEqual(p.WITNESSES[0x60ea0d94],('mov','36913,d0'))
 def test_operand_mutations_rejected(self):
  for a,(mn,op) in p.WITNESSES.items():
   with self.assertRaises(ValueError):p.require_instruction(f'{a:x}: 00 {mn} WRONG',a,mn,op)
if __name__=='__main__':unittest.main()
