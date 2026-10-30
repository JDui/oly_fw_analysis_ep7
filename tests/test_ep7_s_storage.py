import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import unittest,struct
from unittest.mock import patch
import ep7_s_storage as p

def filter_fixture():
    b=bytearray(0x4b0000)
    ptr=0x60490020
    for i,pid in enumerate(p.IDS):struct.pack_into('<HBB',b,ptr-p.BASE+4*i,pid,0,0)
    for i in range(70):struct.pack_into('<HHIHH',b,0x604a8420-p.BASE+12*i,i+1,0,ptr,1338,0)
    return b,ptr
class Tests(unittest.TestCase):
    def test_filter_fixture(self):
        b,_=filter_fixture();r=p.filters(b)
        self.assertEqual(len(r),70);self.assertTrue(all(x['selected_S_count']==48 and x['selected_part']==0 for x in r))
    def test_part1_rejected(self):
        b,ptr=filter_fixture();b[ptr-p.BASE+2]=1
        with self.assertRaises(ValueError):p.filters(b)
    def test_missing_or_duplicate_id_rejected(self):
        for value in (0,927):
            b,ptr=filter_fixture();struct.pack_into('<H',b,ptr-p.BASE+4,value)
            with self.assertRaises(ValueError):p.filters(b)
    def test_sentinel_rejected(self):
        b,_=filter_fixture();struct.pack_into('<H',b,0x604a8768-p.BASE,1)
        with self.assertRaises(ValueError):p.filters(b)
    def test_bad_input_never_runs_objdump(self):
        with patch.object(p.subprocess,'check_output') as run:
            with self.assertRaises((ValueError,AssertionError)):p.inspect(b'no firmware',Path('/not-a-tool'))
            run.assert_not_called()
    def test_witness_coverage(self):
        for a in p.WITNESSES:self.assertEqual(sum(lo<=a<hi for lo,hi in p.WINDOWS.values()),1)
    def test_separate_widths(self):
        self.assertEqual(0xf6fa&3,2)
        self.assertEqual(0x8b64&7,4)
        self.assertEqual(0x85d4&7,4)
class LifecycleTests(unittest.TestCase):
    def test_bad_input_never_runs_disassembler(self):
        with patch.object(p.subprocess,'check_output') as run:
            with self.assertRaises((ValueError,AssertionError)):p.inspect(b'invalid',Path('/not-a-tool'))
            run.assert_not_called()
    def test_lifecycle_witness_unique_coverage(self):
        self.assertEqual(len(p.LIFECYCLE_WINDOWS),8)
        self.assertEqual(len(p.LIFECYCLE_WITNESSES),59)
        for addr in p.LIFECYCLE_WITNESSES:
            self.assertEqual(sum(lo<=addr<hi for lo,hi in p.LIFECYCLE_WINDOWS.values()),1)
    def test_inhibit_set_and_release_are_distinct(self):
        self.assertEqual(p.WITNESSES[0x602b3527],('mov','1,d0'))
        self.assertEqual(p.WITNESSES[0x602b3586],('clr','d0'))
        for addr in (0x602b3529,0x602b3587):
            self.assertEqual(p.WITNESSES[addr],('call','0x602cc6c6,[],0'))
    def test_commit_bypasses_ordinary_gate(self):
        self.assertEqual(p.WITNESSES[0x602cbc5f],('call','0x602cc6cf,[],0'))
        self.assertEqual(p.WITNESSES[0x602cc571],('call','0x602cbc74,[d2,d3,a2],20'))
        self.assertEqual(p.WITNESSES[0x602cc57a],('cmp','1769,d2'))
    def test_changed_instruction_rejected(self):
        asm='602b3529:\t00 00\tcall\t0x602cc6c6,[],0\n'
        p.require_instruction(asm,0x602b3529,*p.WITNESSES[0x602b3529])
        with self.assertRaises(ValueError):
            p.require_instruction(asm.replace('602cc6c6','602cc6cf'),0x602b3529,*p.WITNESSES[0x602b3529])
    def test_limits_remain_explicit(self):
        f=p.lifecycle_facts()
        self.assertTrue(f['conditional_path'])
        self.assertEqual(len(f['limitations']),6)
        self.assertTrue(any('runtime bank registration' in s for s in f['limitations']))
        self.assertEqual(f['ordered_call_sites'][-1],'0x602b3597')

if __name__=='__main__':unittest.main()
