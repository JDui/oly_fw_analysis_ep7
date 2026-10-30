import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import ep7_capture_clone as probe

class Tests(unittest.TestCase):
    def test_wrong_stock_never_executes_tool(self):
        with patch.object(probe.subprocess,'check_output') as run:
            with self.assertRaises(ValueError): probe.inspect(b'wrong build',Path('/no-tool'))
            run.assert_not_called()
    def test_windows_cover_each_witness_once(self):
        for address in probe.WITNESSES:
            self.assertEqual(sum(lo <= address < hi for lo,hi in probe.WINDOWS.values()),1)
    def test_reject_wrong_operand(self):
        with self.assertRaises(ValueError):
            probe.require_instruction('603edbca: 00 mov 41984,d0',0x603edbca,'mov','27332,d0')
    def test_allocator_source_and_copy_source_are_distinct_witnesses(self):
        self.assertEqual(probe.WITNESSES[0x603ed63d],('mov','(28,a0),a2'))
        self.assertEqual(probe.WITNESSES[0x603edbcd],('mov','a3,a1'))
    def run_mock_inspect(self, fail=False):
        visited=[]
        def run(args,**kwargs):
            if args[-1]=='--version': return 'synthetic objdump\n'
            image=Path(args[-1]);visited.append(image)
            self.assertTrue(image.is_file())
            if fail: raise RuntimeError('synthetic disassembler failure')
            return '\n'.join(f'{a:x}: 00 {mn} {op}' for a,(mn,op) in probe.WITNESSES.items())
        with tempfile.TemporaryDirectory() as temp:
            tool=Path(temp)/'not-executed';tool.write_bytes(b'synthetic tool')
            with patch.object(probe,'audit',return_value={'source_sha256':'synthetic'}),patch.object(probe,'parse',return_value=[SimpleNamespace(payload=b'synthetic')]),patch.object(probe.subprocess,'check_output',side_effect=run):
                if fail:
                    with self.assertRaises(RuntimeError): probe.inspect(b'synthetic',tool)
                else:
                    report=probe.inspect(b'synthetic',tool)
                    self.assertFalse(report['flash_ready'])
                    self.assertEqual(report['instruction_witness_count'],48)
        self.assertTrue(visited)
        self.assertTrue(all(not p.exists() and not p.parent.exists() for p in visited))
    def test_temp_cleanup_on_success(self): self.run_mock_inspect()
    def test_temp_cleanup_on_tool_failure(self): self.run_mock_inspect(fail=True)
    def test_clone_extent_arithmetic_only(self):
        # Host arithmetic assertion, not an execution of the firmware copy routine.
        self.assertLessEqual(24058+12*2,27332)
        self.assertLess(27332,41984)
if __name__=='__main__': unittest.main()
