import unittest
from unittest.mock import patch
import check_dependency_closure as c
class Closure(unittest.TestCase):
 def test_actual_compile(self):
  r=c.check();self.assertEqual(r['selected_object_count'],9);self.assertEqual(set(r['remaining_external_symbols']),c.EXPECTED_EXTERNAL);self.assertFalse(r['target_linked'])
 def test_untrusted_tool(self):
  with patch.object(c,'sha',return_value='bad'),patch.object(c.subprocess,'run') as run:
   with self.assertRaises(ValueError):c.check()
   run.assert_not_called()
 def test_local_definition_not_global(self):
  d,u=c.symbols('00000000 l F .text 00000000 _local\n00000000 g F .text 00000000 _public\n00000000 *UND* 00000000 _needed')
  self.assertEqual(d,{'_public'});self.assertEqual(u,{'_needed'})
 def test_missing_internal_definition(self):
  o={'x':dict(global_definitions=[],undefined_symbols=sorted(c.EXPECTED_EXTERNAL|{'_missing'}))}
  with self.assertRaises(ValueError):c.resolve(o)
 def test_duplicate_definition(self):
  o={n:dict(global_definitions=['_duplicate'],undefined_symbols=[]) for n in ['a','b']}
  with self.assertRaises(ValueError):c.resolve(o)
 def test_unexpected_atomic_dependency(self):
  o={'x':dict(global_definitions=[],undefined_symbols=sorted(c.EXPECTED_EXTERNAL|{'___atomic_compare_exchange_4'}))}
  with self.assertRaises(ValueError):c.resolve(o)
if __name__=='__main__':unittest.main()
