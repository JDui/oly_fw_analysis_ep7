import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import unittest
from pathlib import Path
from unittest.mock import patch
import ep7_private_semaphore as probe
import ep7_semaphore_transport as t
class Transport(unittest.TestCase):
 def test_wrong_stock_restores_probe(self):
  old=probe.W
  with patch.object(probe.subprocess,'check_output') as run:
   with self.assertRaises(ValueError):t.inspect(b'wrong',Path('/no/tool'))
   run.assert_not_called()
  self.assertIs(probe.W,old)
 def test_witness_mutations(self):
  for addr,(op,args) in t.W.items():
   probe.require_instruction(f'{addr:08x}: 00 {op} {args}',addr,op,args)
   with self.assertRaises(ValueError):probe.require_instruction(f'{addr:08x}: 00 {op} WRONG',addr,op,args)
 def test_window_coverage(self):
  for addr in t.W:self.assertEqual(sum(lo<=addr<hi for lo,hi in t.WINDOWS),1)
if __name__=='__main__':unittest.main()
