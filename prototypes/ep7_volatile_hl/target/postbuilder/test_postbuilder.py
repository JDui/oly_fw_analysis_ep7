import unittest
from pathlib import Path
from unittest.mock import patch
import check_bridge as bridge
import seam_probe as seam
import check_loopstate as loop
import check_native_observer as observer
class Postbuilder(unittest.TestCase):
 def test_actual_native_observer_compile_only(self):
  r=observer.check();self.assertFalse(r['target_executed']);self.assertTrue(r['host_64bit_compile_rejected']);self.assertEqual(r['undefined_symbols'],['_ep7_native_runtime_unresolved','_ep7p_direct_apply'])
 def test_observer_tool_mismatch(self):
  with patch.object(observer,'sha',return_value='bad'),patch.object(observer.subprocess,'run') as run:
   with self.assertRaises(ValueError):observer.check()
   run.assert_not_called()
 def test_actual_loopstate_objects(self):
  result=loop.check();self.assertEqual(len(result['objects']),5)
 def test_loop_opcode_rejected(self):
  original=loop.subprocess.check_output
  def altered(args,**kw):
   value=original(args,**kw)
   return value+'\n 0: 00 setlb \n' if '-dr' in args else value
  with patch.object(loop.subprocess,'check_output',side_effect=altered):
   with self.assertRaises(ValueError):loop.check()
 def test_compile_and_host_stack(self):self.assertTrue(bridge.check()['stack_arithmetic_model_passed'])
 def test_bad_tool_noexec(self):
  with patch.object(bridge,'sha',return_value='bad'),patch.object(bridge.subprocess,'run') as run:
   with self.assertRaises(ValueError):bridge.check()
   run.assert_not_called()
 def test_bad_frame_rejected(self):
  original=bridge.subprocess.check_output
  def wrong(args,**kw):
   val=original(args,**kw)
   return val.replace('[d2,d3,a2,a3],96','[d2,d3,a2,a3],92') if '-dr' in args else val
  with patch.object(bridge.subprocess,'check_output',side_effect=wrong):
   with self.assertRaises(ValueError):bridge.check()
 def test_wrong_stock_noexec(self):
  with patch.object(seam.subprocess,'check_output') as run:
   with self.assertRaises(ValueError):seam.inspect(b'wrong',Path('/no/tool'))
   run.assert_not_called()
 def test_every_stock_operand_mutation(self):
  for addr,(op,args) in seam.W.items():
   with self.assertRaises(ValueError):seam.require_instruction(f'{addr:08x}: 00 {op} WRONG',addr,op,args)
if __name__=='__main__':unittest.main()
