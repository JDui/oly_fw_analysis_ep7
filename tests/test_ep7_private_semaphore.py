import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import unittest
from pathlib import Path
from unittest.mock import patch
import ep7_private_semaphore as probe
class Probe(unittest.TestCase):
 def test_stock_guard_before_tool(self):
  with patch.object(probe.subprocess,'check_output') as run:
   with self.assertRaises(ValueError):probe.inspect(b'wrong',Path('/no/tool'))
   run.assert_not_called()
 def test_tool_guard(self):
  with patch.object(probe,'audit',return_value={}),patch.object(Path,'read_bytes',return_value=b'badtool'),patch.object(probe.subprocess,'check_output') as run:
   with self.assertRaises(ValueError):probe.inspect(b'',Path('/no/tool'))
   run.assert_not_called()
 def test_exact_witnesses(self):
  for addr,(op,args) in probe.W.items():probe.require_instruction(f'{addr:08x}: 00 {op} {args}',addr,op,args)
 def test_all_operand_changes_rejected(self):
  for addr,(op,args) in probe.W.items():
   with self.assertRaises(ValueError):probe.require_instruction(f'{addr:08x}: 00 {op} WRONG',addr,op,args)
 def test_all_opcode_changes_rejected(self):
  for addr,(op,args) in probe.W.items():
   with self.assertRaises(ValueError):probe.require_instruction(f'{addr:08x}: 00 BAD {args}',addr,op,args)
 def test_unique_window_membership(self):
  for addr in probe.W:self.assertEqual(sum(lo<=addr<hi for lo,hi in probe.WINDOWS),1)
if __name__=='__main__':unittest.main()
