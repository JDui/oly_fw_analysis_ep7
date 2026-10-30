import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import unittest,struct
from unittest.mock import patch
import ep7_s_capture_snapshot as p

def fixture():
    b=bytearray(0x4d9000)
    for pid,key in ((111,0x9481),(211,0x9d11),(908,0xf6b1),(973,0xf731)):
        struct.pack_into('<HH',b,0x604d6c14-p.BASE+4*pid,key,0)
    struct.pack_into('<3I',b,0x60078968-p.BASE,0x6005c8cc,0x60067100,0x60067100)
    return b
class Tests(unittest.TestCase):
    def test_fixture_maps(self):
        r=p.tables(fixture());self.assertEqual(r['mode_profile_map']['908'],['0xf6b1',0])
        self.assertFalse(r['atomicity_proven']);self.assertFalse(r['actual_race_demonstrated'])
    def test_changed_mode_map_rejected(self):
        b=fixture();b[0x604d6c14-p.BASE+111*4]=0
        with self.assertRaises(ValueError):p.tables(b)
    def test_changed_dispatch_rejected(self):
        b=fixture();b[0x60078968-p.BASE]=0
        with self.assertRaises(ValueError):p.tables(b)
    def test_bad_stock_never_disassembles(self):
        with patch.object(p.subprocess,'check_output') as run:
            with self.assertRaises((ValueError,AssertionError)):p.inspect(b'bad stock',Path('/missing'))
            run.assert_not_called()
    def test_witnesses_covered_once(self):
        for addr in p.WITNESSES:self.assertEqual(sum(lo<=addr<hi for lo,hi in p.WINDOWS.values()),1)
    def test_twelve_independent_getter_store_pairs(self):
        seq=[(a,*op) for a,op in sorted(p.WITNESSES.items()) if 0x602a85c4<=a<0x602a86b7]
        starts=[i for i,(_,mn,arg) in enumerate(seq) if (mn,arg)==('mov','63210,d0')]
        self.assertEqual(len(starts),12)
        for sector,start in enumerate(starts):
            block=[(mn,arg) for _,mn,arg in seq[start:starts[sector+1] if sector<11 else len(seq)]]
            self.assertIn(('mov','0,a0'),block)
            self.assertIn(('clr','d1') if sector==0 else ('mov',f'{sector},d1'),block)
            self.assertEqual(sum(mn=='call' for mn,_ in block),1)
            self.assertIn(('call','0x6005e971,[d2,d3],12'),block)
            self.assertEqual(block[-1],('movhu','d0,(a2)' if sector==0 else f'd0,({2*sector},a2)'))
    def test_mode_and_profile_guards(self):
        for addr,want in {0x602a8586:('cmp','6,d0'),0x602a859e:('cmp','11,d0'),0x602a85aa:('cmp','12,d0'),0x602a8583:('movbu','d0,(a2)'),0x602a85c0:('movbu','d0,(24083,a0)')}.items():
            self.assertEqual(p.WITNESSES[addr],want)
    def test_immediate_caller_guards_and_edge(self):
        for addr,want in {0x602a447e:('bne','0x602a44ba'),0x602a4488:('beq','0x602a44ba'),0x602a4492:('beq','0x602a449c'),0x602a44a3:('call','0x602a7ea0,[d2,d3,a2,a3],20')}.items():
            self.assertEqual(p.WITNESSES[addr],want)
    def test_corrupt_instruction_rejected(self):
        addr=0x602a44a3;asm='602a44a3:\t00 00\tcall\t0x602a7ea0,[d2,d3,a2,a3],20\n'
        p.require_instruction(asm,addr,*p.WITNESSES[addr])
        with self.assertRaises(ValueError):p.require_instruction(asm.replace('7ea0','7ea1'),addr,*p.WITNESSES[addr])
if __name__=='__main__':unittest.main()
