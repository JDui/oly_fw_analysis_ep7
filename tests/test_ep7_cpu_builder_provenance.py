import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import ep7_cpu_builder_provenance as probe

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
            probe.require_instruction('6034ef51: 00 mov 9,d0',0x6034ef51,'mov','10,d0')
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
            with patch.object(probe,'audit',return_value={'source_sha256':'synthetic'}),patch.object(probe,'parse',return_value=[SimpleNamespace(payload=self.synthetic_main())]),patch.object(probe.subprocess,'check_output',side_effect=run):
                if fail:
                    with self.assertRaises(RuntimeError): probe.inspect(b'synthetic',tool)
                else:
                    report=probe.inspect(b'synthetic',tool)
                    self.assertFalse(report['flash_ready'])
                    self.assertEqual(report['instruction_witness_count'],len(probe.WITNESSES))
        self.assertTrue(visited)
        self.assertTrue(all(not p.exists() and not p.parent.exists() for p in visited))
    def test_temp_cleanup_on_success(self): self.run_mock_inspect()
    def test_temp_cleanup_on_tool_failure(self): self.run_mock_inspect(fail=True)
    @staticmethod
    def synthetic_main():
        main=bytearray(0x604e4f84-probe.BASE)
        for a,t in [(0x604e4f80,0x603397db)]:
            main[a-probe.BASE:a-probe.BASE+4]=t.to_bytes(4,'little')
        return bytes(main)
    def test_table_mutation_fails_before_subprocess(self):
        with patch.object(probe,'audit',return_value={'source_sha256':'synthetic'}),patch.object(probe,'parse',return_value=[SimpleNamespace(payload=b'bad tables')]),patch.object(probe.subprocess,'check_output') as run:
            with self.assertRaises(ValueError): probe.inspect(b'synthetic',Path('/no-tool'))
            run.assert_not_called()
if __name__=='__main__': unittest.main()
