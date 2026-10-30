import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import ep7_static_paths as paths


class EP7StaticPathTests(unittest.TestCase):
    def test_extract_only_target_operands(self):
        text = '100: 24 9f 03\tmov\t927,a0\n103: 80 01\tmov\t1,d0\n'
        self.assertEqual(paths.property_reads(text), [927])

    def test_direct_calls_exclude_indirect_calls(self):
        text = 'call\t0x602b2237,[d2],8\ncalls\t(a2)\n'
        self.assertEqual(paths.direct_calls(text), [0x602b2237])

    def test_bad_input_never_invokes_external_tool(self):
        with patch.object(paths.subprocess, 'check_output') as run:
            with self.assertRaisesRegex(ValueError, 'exact E-P7 1100'):
                paths.inspect(b'wrong firmware', Path('/not/executed'))
            run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
