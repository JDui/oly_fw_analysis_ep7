import unittest
from unittest.mock import patch
import check as c
class ABI(unittest.TestCase):
 def altered(self,old,new,flag='-dr'):
  original=c.subprocess.check_output
  def change(args,**kw):
   text=original(args,**kw)
   return text.replace(old,new) if flag in args else text
  with patch.object(c.subprocess,'check_output',side_effect=change):
   with self.assertRaises(ValueError):c.check()
 def test_actual(self):
  r=c.check();self.assertEqual(r['bridge_text_bytes'],52);self.assertTrue(r['relocations_verified'])
 def test_tools_fail_before_execution(self):
  with patch.object(c,'sha',return_value='bad'),patch.object(c.subprocess,'run') as run:
   with self.assertRaises(ValueError):c.check()
   run.assert_not_called()
 def test_wrong_router_relocation(self):self.altered('_ep7_gcc_ui_route+0x1','_wrong_route+0x1')
 def test_wrong_delegate_target(self):self.altered('ep7_stock_ui_event_unresolved','ep7_wrong_parent_unresolved')
 def test_wrong_branch_target(self):self.altered('.Ldone+0x1','.Lwrong+0x1')
 def test_wrong_return_offset(self):self.altered('00000031 <.Ldone>','00000029 <.Ldone>')
 def test_wrong_frame(self):self.altered('[d2,d3,a2,a3],48','[d2,d3,a2,a3],44')
 def test_wrong_text_size(self):self.altered('00000034','00000035','-h')
 def test_stack_register_order(self):self.assertTrue(c.stack_model())
if __name__=='__main__':unittest.main()
