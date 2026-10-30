import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import ep7_stage_admission as probe

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
    def test_all_witness_operand_mutations_rejected(self):
        for address,(mnemonic,operand) in probe.WITNESSES.items():
            with self.subTest(address=hex(address)):
                with self.assertRaises(ValueError):
                    probe.require_instruction(f'{address:x}: 00 {mnemonic} WRONG',address,mnemonic,operand)
    def test_key_admission_qualifiers_have_exact_witnesses(self):
        expected={
            0x60353855:('mov','192,d1'),
            0x60368f53:('mov','1614186573,d0'),
            0x60368f59:('mov','d0,(24,a2)'),
            0x6036763a:('mov','0,a1'),
            0x6036770d:('mov','0,a1'),
            0x60367f4a:('mov','0,a1'),
            0x6036780a:('mov','(36,sp),a1'),
            0x60367935:('mov','a2,a1'),
            0x60355347:('mov','712,d1'),
            0x60355362:('mov','3,d0'),
            0x60355364:('movbu','d0,(16,a2)'),
            0x60354c27:('movbu','d0,(17,a0)'),
        }
        for address,instruction in expected.items():
            self.assertEqual(probe.WITNESSES[address],instruction)
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
                    self.assertFalse(report['admission_hook_implemented'])
                    self.assertEqual(report['instruction_witness_count'],len(probe.WITNESSES))
        self.assertTrue(visited)
        self.assertTrue(all(not p.exists() and not p.parent.exists() for p in visited))
    def test_temp_cleanup_on_success(self): self.run_mock_inspect()
    def test_temp_cleanup_on_tool_failure(self): self.run_mock_inspect(fail=True)
    @staticmethod
    def synthetic_main():
        main=bytearray(0x603ed87c-probe.BASE)
        for a,t in [(0x60368f55,0x6036884d)]:
            main[a-probe.BASE:a-probe.BASE+4]=t.to_bytes(4,'little')
        return bytes(main)
    def test_stage_literal_mutation_fails_before_subprocess(self):
        with patch.object(probe,'audit',return_value={'source_sha256':'synthetic'}),patch.object(probe,'parse',return_value=[SimpleNamespace(payload=b'bad callback literal')]),patch.object(probe.subprocess,'check_output') as run:
            with self.assertRaises(ValueError): probe.inspect(b'synthetic',Path('/no-tool'))
            run.assert_not_called()
if __name__=='__main__': unittest.main()
