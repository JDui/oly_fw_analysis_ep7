import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import unittest
from unittest.mock import patch
import ep7_output_layout as p
class TestLayout(unittest.TestCase):
 def test_wrong_stock_no_tool(self):
  with patch.object(p.subprocess,'check_output') as run:
   with self.assertRaises(ValueError):p.inspect(b'not stock',Path('/no/tool'))
   run.assert_not_called()
 def test_every_operand_mutation_rejected(self):
  for addr,(op,args) in p.W.items():
   line=f'{addr:08x}: 00  {op}\t{args}'
   p.require_instruction(line,addr,op,args)
   with self.assertRaises(ValueError):p.require_instruction(line.replace(args,'WRONG'),addr,op,args)
 def test_map_bounds_disjoint_and_permutation(self):
  inputs=[];lanes=set();sat=set()
  for parity in range(2):
   for k in range(6):
    j=6*parity+k;inputs.append(2*k+parity)
    lanes.update([706+24*j,707+24*j,710+24*j,711+24*j])
    sat.update([708+24*j,709+24*j])
  self.assertEqual(inputs,[0,2,4,6,8,10,1,3,5,7,9,11])
  self.assertEqual(len(lanes),48);self.assertFalse(lanes&sat)
  self.assertEqual(max(lanes),975)
if __name__=='__main__':unittest.main()
