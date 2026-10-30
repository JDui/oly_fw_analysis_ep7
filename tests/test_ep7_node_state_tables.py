import unittest, hashlib
from unittest.mock import patch
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import ep7_node_state_tables as m
class Tests(unittest.TestCase):
 def test_wrong_input_before_tool(self):
  with self.assertRaisesRegex(ValueError,'wrong exact'):m.inspect(b'',Path('/not-a-tool'))
 def test_finite_tables(self):
  for rows,n in [(m.TABLE33,18),(m.TABLE34,22)]:
   self.assertEqual(len(rows)-1,n);self.assertEqual(rows[-1],(0xffff,0));self.assertEqual(len(set(e for e,h in rows)),n+1)
 @unittest.skipUnless((m.ROOT/'generated/ep7/main.decoded.bin').is_file() and (m.ROOT/'toolchains/binutils-2.45-build/binutils/objdump').is_file(), 'exact proprietary stock and trusted objdump required')
 def test_real_stock_static(self):
  r=m.inspect((m.ROOT/'generated/ep7/main.decoded.bin').read_bytes(),m.ROOT/'toolchains/binutils-2.45-build/binutils/objdump')
  self.assertEqual(r['checked_instructions'],len(m.W));self.assertFalse(r['lifecycle_closure']);self.assertFalse(r['firmware_execution'])
if __name__=='__main__':unittest.main()
