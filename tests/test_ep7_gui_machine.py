import unittest
import struct
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import ep7_gui_machine as probe

class Tests(unittest.TestCase):
    def test_invalid_input_never_launches_objdump(self):
        with patch.object(probe.subprocess, 'check_output') as run:
            with self.assertRaises((ValueError, AssertionError)):
                probe.inspect(b'not firmware', Path('/not-an-executable'))
            run.assert_not_called()
    def test_exact_instruction(self):
        probe.require_instruction('603537f0:\tfc 00\tmov\t15488,d0', 0x603537f0, 'mov', '15488,d0')
    def test_bad_instruction(self):
        for line in ['603537f1:\tfc 00\tmov\t15488,d0', '603537f0:\tfc 00\tmov\t15489,d0', '603537f0:\tfc 00\tadd\t15488,d0']:
            with self.subTest(line=line), self.assertRaises(ValueError):
                probe.require_instruction(line, 0x603537f0, 'mov', '15488,d0')
    def test_duplicate_instruction_rejected(self):
        line='603537f0:\tfc 00\tmov\t15488,d0\n'
        with self.assertRaises(ValueError):
            probe.require_instruction(line*2,0x603537f0,'mov','15488,d0')
    def test_witnesses_covered_once(self):
        for a in probe.WITNESSES:
            self.assertEqual(sum(start <= a < end for start,end in probe.WINDOWS.values()),1)
class TableTests(unittest.TestCase):
    def fixture(self):
        data=bytearray(0x611a3be8-probe.BASE)
        for _,address,values in probe.ROWS:
            struct.pack_into('<'+'I'*len(values),data,address-probe.BASE,*values)
        for index in range(112):
            event={6:0x900c,10:0x9014,11:0x9015}.get(index,0xa000+index)
            struct.pack_into('<II',data,0x611a2888+index*8-probe.BASE,event,index)
        for index in (6,10,11):data[0x611a2e30+index*29+28-probe.BASE]=137
        struct.pack_into('<I',data,0x611a2c08+137*4-probe.BASE,0x60e5da87)
        return data
    def test_synthetic_table_layout(self):
        _,paths=probe.inspect_tables(self.fixture())
        self.assertEqual(len(paths),3)
    def test_injected_Delete_event_rejected(self):
        data=self.fixture()
        struct.pack_into('<I',data,0x611a2888-probe.BASE,0x9016)
        with self.assertRaises(ValueError):probe.inspect_tables(data)
    def test_wrong_handler_rejected(self):
        data=self.fixture();data[0x611a2e30+6*29+28-probe.BASE]=1
        with self.assertRaises(ValueError):probe.inspect_tables(data)
    def test_duplicate_event_rejected(self):
        data=self.fixture()
        struct.pack_into('<I',data,0x611a2888-probe.BASE,0x900c)
        with self.assertRaises(ValueError):probe.inspect_tables(data)
class PreprocessorTests(unittest.TestCase):
    def fixture(self):
        data=bytearray(0x611ecd60-probe.BASE)
        for i in range(128):
            struct.pack_into('<II',data,0x611ec960+i*8-probe.BASE,i+1000,0x60e9fb74)
        struct.pack_into('<II',data,0x611ec960+38*8-probe.BASE,0,0x60e9fd41)
        struct.pack_into('<41H',data,0x611ec38c-probe.BASE,*range(41))
        return data
    def test_bounded_probe(self):
        result=probe.inspect_preprocessor(self.fixture())
        self.assertEqual(len(result['probe_path']),21)
    def test_Delete_preprocessor_injection_rejected(self):
        data=self.fixture()
        struct.pack_into('<I',data,0x611ec960-probe.BASE,0x12)
        with self.assertRaises(ValueError):probe.inspect_preprocessor(data)
    def test_bad_target_rejected(self):
        data=self.fixture()
        struct.pack_into('<I',data,0x611ec960+18*8+4-probe.BASE,0)
        with self.assertRaises(ValueError):probe.inspect_preprocessor(data)
    def test_unterminated_probe_rejected(self):
        data=self.fixture()
        struct.pack_into('<I',data,0x611ec960+38*8-probe.BASE,999)
        with self.assertRaises(ValueError):probe.inspect_preprocessor(data)
    def test_Delete_tracking_injection_rejected(self):
        data=self.fixture()
        struct.pack_into('<H',data,0x611ec38c-probe.BASE,0x9016)
        with self.assertRaises(ValueError):probe.inspect_preprocessor(data)
if __name__ == '__main__': unittest.main()
