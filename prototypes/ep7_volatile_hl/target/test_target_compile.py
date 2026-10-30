import unittest
from unittest.mock import patch
import check_target_compile as candidate
class Guard(unittest.TestCase):
 def test_changed_tool_never_executes(self):
  with patch.object(candidate,'digest',return_value='wrong'),patch.object(candidate.subprocess,'run') as run,patch.object(candidate.subprocess,'check_output') as output:
   with self.assertRaises(ValueError):candidate.check()
   run.assert_not_called();output.assert_not_called()
 def test_actual_compile_only(self):
  result=candidate.check()
  self.assertEqual(set(result['results']),{'probe','ep7p','ep7p_ui','ep7p_decode','memory','ep7p_ui_raw'})
  for key in ['target_linked','target_executed','firmware_input_used','native_ABI_compatible','flash_ready']:self.assertFalse(result[key])
if __name__=='__main__':unittest.main()
