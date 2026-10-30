import unittest
from pathlib import Path
from unittest.mock import patch
import sys,importlib.util
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import ep7_semaphore_bootstrap as p
spec=importlib.util.spec_from_file_location('bootstrap_check',ROOT/'prototypes/ep7_volatile_hl/poll_lock_provider/bootstrap/check_bootstrap.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
class Checks(unittest.TestCase):
 def test_actual(self):
  r=c.check();self.assertEqual(r['selected_objects'],12);self.assertEqual(len(r['remaining_external_symbols']),7);self.assertFalse(r['native_api_invoked'])
 def test_tool_guard(self):
  with patch.object(c.closure,'sha',return_value='bad'),patch.object(c.subprocess,'run') as run:
   with self.assertRaises(ValueError):c.check()
   run.assert_not_called()
 def test_create_pointer_translation(self):
  old=c.subprocess.check_output
  def altered(args,**kw):
   value=old(args,**kw)
   return value.replace('d0,a0','d1,a0') if '-dr' in args else value
  with patch.object(c.subprocess,'check_output',side_effect=altered):
   with self.assertRaises(ValueError):c.check()
 def test_delete_frame(self):
  old=c.subprocess.check_output
  def altered(args,**kw):
   value=old(args,**kw)
   return value.replace('[d2,d3,a2,a3],20','[d2,d3,a2,a3],16') if '-dr' in args else value
  with patch.object(c.subprocess,'check_output',side_effect=altered):
   with self.assertRaises(ValueError):c.check()
 def test_stockguard(self):
  old=p.base.W
  with patch.object(p.base.subprocess,'check_output') as run:
   with self.assertRaises(ValueError):p.inspect(b'bad',Path('/no/tool'))
   run.assert_not_called()
  self.assertIs(p.base.W,old)
 def test_all_operands(self):
  for a,(op,arg) in p.W.items():
   p.base.require_instruction(f'{a:08x}: 00 {op} {arg}',a,op,arg)
   with self.assertRaises(ValueError):p.base.require_instruction(f'{a:08x}: 00 {op} WRONG',a,op,arg)
 def test_windowcoverage(self):
  for a in p.W:self.assertEqual(sum(lo<=a<hi for lo,hi in p.WINDOWS),1)
if __name__=='__main__':unittest.main()
