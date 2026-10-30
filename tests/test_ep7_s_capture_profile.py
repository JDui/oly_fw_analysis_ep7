import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import unittest
from unittest.mock import patch
import ep7_s_capture_profile as p
class Tests(unittest.TestCase):
    def test_four_bindings(self):
        for selector,mode in enumerate((54,55,56,64),1):self.assertEqual(p.bind_capture_color(11,selector),mode)
    def test_selector_zero_and_outside_fail_closed(self):
        for selector in (-1,0,5,255,True,1.0,None):self.assertIsNone(p.bind_capture_color(11,selector))
    def test_other_modes_fail_closed(self):
        for mode in (0,6,12,54,55,56,64,True,11.0):self.assertIsNone(p.bind_capture_color(mode,1))
    def test_stock_guard_precedes_disassembly(self):
        with patch.object(p.subprocess,'check_output') as run:
            with self.assertRaises((ValueError,AssertionError)):p.inspect(b'not firmware',Path('/bad'))
            run.assert_not_called()
    def test_each_witness_covered_once(self):
        for addr in p.WITNESSES:self.assertEqual(sum(lo<=addr<hi for lo,hi in p.WINDOWS.values()),1)
    def test_composite_getter_branch(self):
        self.assertEqual(p.WITNESSES[0x602b0b79],('call','0x602b0d9b,[d2,d3,a2,a3],88'))
        self.assertEqual(p.WITNESSES[0x602b0b83],('call','0x602b9dc4,[d2,d3,a2],16'))
        self.assertEqual(p.WITNESSES[0x602b0dc7],('call','0x602cbc0a,[],4'))
    def test_native_fallback_is_not_color1(self):
        self.assertEqual(p.PUBLIC[32],63)
        self.assertNotIn(63,(54,55,56,64))
        self.assertEqual(p.WITNESSES[0x602b9ea1],('add','-1,d3'))
        self.assertEqual(p.WITNESSES[0x602b9ec3],('blt','0x602b9ea6'))
        self.assertEqual(p.WITNESSES[0x602b9f1f],('blt','0x602b9f22'))
    def test_corrupt_match_call_rejected(self):
        a=0x602b9ead;s='602b9ead:\t00 00\tcall\t0x60022f89,[d2,d3],8\n'
        p.require_instruction(s,a,*p.WITNESSES[a])
        with self.assertRaises(ValueError):p.require_instruction(s.replace('2f89','2f88'),a,*p.WITNESSES[a])
if __name__=='__main__':unittest.main()
