import unittest
from unittest.mock import patch
import check_get_tid_bridge as p
class Bridge(unittest.TestCase):
 def test_actual_compile_and_stack_model(self):
  r=p.check();self.assertTrue(r['stack_arithmetic_contract_passed']);self.assertFalse(r['target_executed']);self.assertEqual(r['text_bytes'],17)
 def test_tool_mismatch_no_execution(self):
  with patch.object(p,'sha',return_value='wrong'),patch.object(p.subprocess,'run') as run:
   with self.assertRaises(ValueError):p.check()
   run.assert_not_called()
 def test_wrong_final_return_rejected(self):
  original=p.subprocess.check_output
  def changed(args,**kw):
   value=original(args,**kw)
   return value.replace('[a2],16','[a2],4') if '-dr' in args else value
  with patch.object(p.subprocess,'check_output',side_effect=changed):
   with self.assertRaises(ValueError):p.check()
if __name__=='__main__':unittest.main()
