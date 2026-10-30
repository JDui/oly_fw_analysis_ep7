import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import unittest
from unittest.mock import patch
import ep7_profile_writer as p
class Tests(unittest.TestCase):
    def test_guard_before_disassembler(self):
        with patch.object(p.subprocess,'check_output') as run:
            with self.assertRaises((ValueError,AssertionError)):p.inspect(b'bad',Path('/not-a-tool'))
            run.assert_not_called()
    def test_every_witness_covered_once(self):
        for a in p.WITNESSES:self.assertEqual(sum(lo<=a<hi for lo,hi in p.WINDOWS.values()),1)
    def test_public64_reverse_row(self):
        self.assertEqual(p.PUBLIC.index(64),16)
        self.assertEqual(0x604ba8fc+16*64,0x604bacfc)
        self.assertEqual(p.WITNESSES[0x602b0bee],('call','0x602b9deb,[d2,d3,a2],16'))
        self.assertEqual(p.WITNESSES[0x602b9e22],('udf00','d1,d0'))
        self.assertEqual(p.WITNESSES[0x602b1469],('call','0x602b0d64,[d2,d3,a2,a3],24'))
    def test_unpack_calls_raw_pair_not_public_enum(self):
        calls=[arg for a,(mn,arg) in p.WITNESSES.items() if 0x602b0d64<=a<0x602b0d9b and mn=='call']
        self.assertEqual(calls,['0x602b15f2,[d2,d3],8','0x602b0b20,[d2,d3],12'])
        self.assertEqual(p.WITNESSES[0x602b0d83],('mov','(d1,a0),d1'))
    def test_raw_pair_stages_then_typed(self):
        calls=[arg for a,(mn,arg) in p.WITNESSES.items() if 0x602b0b20<=a<0x602b0b38 and mn=='call']
        self.assertEqual(calls,['0x602cc122,[],4','0x602cbc5d,[d2,d3],12'])
    def test_inhibit_and_direct_inner_write(self):
        self.assertEqual(p.WITNESSES[0x602cbc5f],('call','0x602cc6cf,[],0'))
        self.assertEqual(p.WITNESSES[0x602cbc65],('cmp','1,d0'))
        self.assertEqual(p.WITNESSES[0x602cbc67],('beq','0x602cbc71'))
        self.assertEqual(p.WITNESSES[0x602cbcb5],('call','0x6005ea22,[d2,d3,a2,a3],40'))
    def test_changed_raw_edge_rejected(self):
        a=0x602b0d86;s='602b0d86:\t00 00\tcall\t0x602b0b20,[d2,d3],12\n'
        p.require_instruction(s,a,*p.WITNESSES[a])
        with self.assertRaises(ValueError):p.require_instruction(s.replace('0b20','0bc4'),a,*p.WITNESSES[a])
if __name__=='__main__':unittest.main()
