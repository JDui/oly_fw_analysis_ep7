import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import ep7_packaging_recovery as m
STOCK=m.ROOT/'firmware_files/OLY_E_142_1100_0000_0000.BIN';TOOL=m.ROOT/'toolchains/binutils-2.45-build/binutils/objdump'
class Tests(unittest.TestCase):
 def test_wrong_input(self):
  with self.assertRaisesRegex(ValueError,'wrong exact'):m.inspect(b'',Path('/absent'))
 @unittest.skipUnless(STOCK.is_file() and TOOL.is_file(),'private exact stock and trusted tool required')
 def test_exact_stock_static(self):
  r=m.inspect(STOCK.read_bytes(),TOOL)
  self.assertEqual(len(r['components']),5);self.assertTrue(r['exact_unchanged_byte_roundtrip'])
  self.assertEqual(r['checked_instructions'],len(m.W));self.assertFalse(r['firmware_image_output_created']);self.assertFalse(r['ep7_physical_recovery_entry_proven'])
if __name__=='__main__':unittest.main()
