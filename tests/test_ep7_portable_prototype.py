"""Compile/run only the repository's self-authored host C demonstrator."""
import importlib.util
from pathlib import Path
import shutil
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('ep7_host_check', ROOT / 'prototypes/ep7_volatile_hl/check_host.py')
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)

class HostIntegration(unittest.TestCase):
    @unittest.skipUnless(shutil.which('cc'), 'trusted host C compiler not available')
    def test_strict_core_and_ui_integration(self):
        report = CHECK.check('cc')
        self.assertEqual([r['test'] for r in report['tests']], ['core', 'normalized_ui_to_output', 'bounded_native_decode', 'raw_logical_ui_to_output', 'direct_observer', 'raw_ui_fresh_job_lifecycle'])
        self.assertTrue(all(r['passed'] for r in report['tests']))
        self.assertTrue(report['host_prototype_executed'])
        self.assertFalse(report['firmware_executed'])
        self.assertFalse(report['native_adapter_installed'])
        self.assertFalse(report['flash_ready'])

if __name__ == '__main__': unittest.main()
