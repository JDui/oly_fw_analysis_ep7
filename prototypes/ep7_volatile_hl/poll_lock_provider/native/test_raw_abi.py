import unittest
from unittest.mock import patch
import check_raw_abi as c
class ABI(unittest.TestCase):
 def test_actual_compile(self):
  r=c.check();self.assertEqual(r['objects']['bridge']['text_bytes'],31);self.assertFalse(r['target_executed'])
 def test_stack(self):self.assertTrue(c.stack_model())
 def test_untrusted_tool(self):
  with patch.object(c,'sha',return_value='bad'),patch.object(c.subprocess,'run') as run:
   with self.assertRaises(ValueError):c.check()
   run.assert_not_called()
 def test_bad_native_frame(self):
  old=c.subprocess.check_output
  def altered(args,**kw):
   text=old(args,**kw)
   return text.replace('[d2,d3,a2,a3],24','[d2,d3,a2,a3],20') if '-dr' in args else text
  with patch.object(c.subprocess,'check_output',side_effect=altered):
   with self.assertRaises(ValueError):c.check()
 def test_poll_zero_enforced(self):
  old=c.subprocess.check_output
  def altered(args,**kw):
   text=old(args,**kw)
   return text.replace('clr\td1','clr\td0') if '-dr' in args else text
  with patch.object(c.subprocess,'check_output',side_effect=altered):
   with self.assertRaises(ValueError):c.check()
 def test_bad_return(self):
  old=c.subprocess.check_output
  def altered(args,**kw):
   text=old(args,**kw)
   return text.replace('ret\t','retf\t') if '-dr' in args else text
  with patch.object(c.subprocess,'check_output',side_effect=altered):
   with self.assertRaises(ValueError):c.check()
if __name__=='__main__':unittest.main()
