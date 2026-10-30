import unittest, hashlib
from unittest.mock import patch
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import ep7_node_state_guard as m
class Tests(unittest.TestCase):
 def test_input_guard(self):
  with self.assertRaisesRegex(ValueError,'wrong exact'):m.inspect(b'',Path('/nottool'))
 @unittest.skipUnless((m.ROOT/'generated/ep7/main.decoded.bin').is_file() and (m.ROOT/'toolchains/binutils-2.45-build/binutils/objdump').is_file(),'exact stock and trusted tool required')
 def test_real_stock_static(self):
  r=m.inspect((m.ROOT/'generated/ep7/main.decoded.bin').read_bytes(),m.ROOT/'toolchains/binutils-2.45-build/binutils/objdump')
  self.assertEqual(r['checked_instructions'],len(m.W));self.assertEqual(len(r['literal_hits']),21)
  self.assertEqual(len(r['service_wrapper_callsites']),2);self.assertFalse(r['global_mutex_proven'])
if __name__=='__main__':unittest.main()
