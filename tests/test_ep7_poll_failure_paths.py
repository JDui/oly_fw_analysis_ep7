import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import unittest
from pathlib import Path
from unittest.mock import patch
import ep7_poll_failure_paths as p
class Paths(unittest.TestCase):
 def test_guard_restore(self):
  old=p.base.W
  with patch.object(p.base.subprocess,'check_output') as run:
   with self.assertRaises(ValueError):p.inspect(b'wrong',Path('/no/tool'))
   run.assert_not_called()
  self.assertIs(p.base.W,old)
 def test_witnesses(self):
  for a,(op,arg) in p.W.items():
   p.base.require_instruction(f'{a:08x}: 00 {op} {arg}',a,op,arg)
   with self.assertRaises(ValueError):p.base.require_instruction(f'{a:08x}: 00 {op} WRONG',a,op,arg)
 def test_coverage(self):
  for a in p.W:self.assertEqual(sum(lo<=a<hi for lo,hi in p.WINDOWS),1)
if __name__=='__main__':unittest.main()
