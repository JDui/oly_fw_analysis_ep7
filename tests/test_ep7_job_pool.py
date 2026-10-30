import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import unittest
from unittest.mock import patch
import ep7_job_pool as p


class PoolTests(unittest.TestCase):
    def test_branch_boundaries(self):
        for size, expected in ((1,0),(128,0),(129,1),(2048,1),(2049,2),
                               (15488,2),(15512,2),(16384,2),(16385,None)):
            self.assertEqual(p.proposed_size_class(size), expected)
    def test_invalid_model_size(self):
        for size in (0, -1, True, 1.0, '15512'):
            with self.assertRaises(ValueError): p.proposed_size_class(size)
    def test_wrong_stock_never_invokes_tool(self):
        with patch.object(p.subprocess, 'check_output') as call:
            with self.assertRaises((ValueError, AssertionError)):
                p.inspect(b'invalid', Path('/not-a-tool'))
            call.assert_not_called()
    def test_witness_coverage(self):
        for address in p.WITNESSES:
            self.assertEqual(sum(lo <= address < hi for lo,hi in p.WINDOWS.values()), 1)

if __name__ == '__main__': unittest.main()
