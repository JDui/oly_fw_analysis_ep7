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
if __name__ == '__main__': unittest.main()
