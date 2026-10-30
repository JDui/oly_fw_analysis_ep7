import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import ep7_metadata_allocation as m
class Tests(unittest.TestCase):
 def test_input_guard(self):
  with self.assertRaisesRegex(ValueError,'wrong exact'):m.inspect(b'',Path('/nottool'))
 def test_static_frame_arithmetic(self):
  # Arithmetic against documented CALL semantics, NOT native branch execution.
  p=0x1000;producer_entry=p-32;wrapper_entry=producer_entry-4
  self.assertEqual(producer_entry-wrapper_entry,4);self.assertEqual(p-wrapper_entry,36)
 @unittest.skipUnless(all((m.ROOT/x).is_file() for x in ['generated/ep7/main.decoded.bin','toolchains/binutils-2.45-build/binutils/objdump','generated/ep7/gcc_abi/mn10300.igen']),'private stock and trusted tool/source fixtures required')
 def test_real_stock_static(self):
  r=m.inspect((m.ROOT/'generated/ep7/main.decoded.bin').read_bytes(),m.ROOT/'toolchains/binutils-2.45-build/binutils/objdump')
  self.assertEqual(r['checked_instructions'],34);self.assertEqual(len(r['direct_relative_call_candidates']),2)
  self.assertFalse(r['native_lifetime_proven']);self.assertFalse(r['firmware_execution'])
if __name__=='__main__':unittest.main()
