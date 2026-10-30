import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import ep7_gui_bridge as probe

class Tests(unittest.TestCase):
    def test_invalid_input_never_launches_objdump(self):
        with patch.object(probe.subprocess, 'check_output') as run:
            with self.assertRaises((ValueError, AssertionError)):
                probe.inspect(b'not firmware', Path('/not-an-executable'))
            run.assert_not_called()
    def test_exact_instruction(self):
        probe.require_instruction('603537f0:\tfc 00\tmov\t15488,d0', 0x603537f0, 'mov', '15488,d0')
    def test_bad_instruction(self):
        for line in ['603537f1:\tfc 00\tmov\t15488,d0', '603537f0:\tfc 00\tmov\t15489,d0', '603537f0:\tfc 00\tadd\t15488,d0']:
            with self.subTest(line=line), self.assertRaises(ValueError):
                probe.require_instruction(line, 0x603537f0, 'mov', '15488,d0')
    def test_duplicate_instruction_rejected(self):
        line='603537f0:\tfc 00\tmov\t15488,d0\n'
        with self.assertRaises(ValueError):
            probe.require_instruction(line*2,0x603537f0,'mov','15488,d0')
    def test_witnesses_covered_once(self):
        for a in probe.WITNESSES:
            self.assertEqual(sum(start <= a < end for start,end in probe.WINDOWS.values()),1)
    def test_profile_state_rows(self):
        rows={label:values for label,address,values in probe.ROWS}
        self.assertEqual(rows['profile state descriptor'], (0x5704,0x60f5d06c,90))
        self.assertEqual(rows['profile Delete'], (0x1000026,39,1,0))
        self.assertNotEqual(rows['profile INFO'][-1],0)
        self.assertEqual(rows['GUI profile enum'],(0xb7,0x9715))
    def test_both_entry_arguments_witnessed(self):
        self.assertEqual(probe.WITNESSES[0x60cd4a2a],('mov','4,d0'))
        self.assertEqual(probe.WITNESSES[0x60cf08f5],('mov','5,d0'))
        self.assertEqual(probe.WITNESSES[0x60cf08fe],('mov','238,d0'))
if __name__ == '__main__': unittest.main()
