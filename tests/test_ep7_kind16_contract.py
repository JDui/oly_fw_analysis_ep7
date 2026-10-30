import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from ep7_kind16_contract import ContractError,Selection,MetadataWindow,capture_id,identity_slot,select_kind16

class Tests(unittest.TestCase):
    def words(self,a=1,b=2): return [a,b]+[0]*13
    def test_qualification_flags_cannot_be_constructor_overridden(self):
        for kwargs in ({'permits_firmware_use':True},{'requires_generation_qualification':False}):
            with self.assertRaises(TypeError):Selection(0,1,(0,1),**kwargs)
    def test_default_first(self):
        result=select_kind16(self.words(),0x100d)
        self.assertEqual((result.index,result.capture_id,result.identity),(0,1,(0,1)))
        self.assertTrue(result.requires_generation_qualification)
        self.assertFalse(result.permits_firmware_use)
    def test_two_dispatches_select_second(self):
        for d in (0x1002,0x1005):
            with self.subTest(d=d):self.assertEqual(select_kind16(self.words(),d).capture_id,2)
    def test_100c_marker11_selects_second(self):
        self.assertEqual(select_kind16(self.words(),0x100c,initial_capture_marker=11).index,1)
    def test_100c_other_marker_keeps_first(self):
        for marker in (0,10,12,255):
            self.assertEqual(select_kind16(self.words(),0x100c,initial_capture_marker=marker).index,0)
    def test_100c_requires_marker(self):
        with self.assertRaises(ContractError):select_kind16(self.words(),0x100c)
    def test_100c_validates_initial_capture_even_if_second_selected(self):
        with self.assertRaises(ContractError):select_kind16(self.words(26,2),0x100c,initial_capture_marker=11)
    def test_domain_difference(self):
        for value in (26,27):
            self.assertEqual(identity_slot(0,value),(0,value))
            with self.assertRaises(ContractError):capture_id(value)
            with self.assertRaises(ContractError):select_kind16(self.words(value),0x100d)
    def test_selected_capture_bounds(self):
        for value in (0,26,27,0xffffffff):
            with self.assertRaises(ContractError):select_kind16(self.words(1,value),0x1002)
        self.assertEqual(select_kind16(self.words(25),0x100d).capture_id,25)
    def test_unused_zero_slots_allowed(self):
        self.assertEqual(select_kind16([1]+[0]*14,0x100d).capture_id,1)
    def test_exact_width_and_length(self):
        for words in ([1]*14,[1]*16,self.words(True),self.words(-1),self.words(1<<32)):
            with self.assertRaises(ContractError):select_kind16(words,0x100d)
        for dispatch in (-1,1<<16,True):
            with self.assertRaises(ContractError):select_kind16(self.words(),dispatch)
    def test_identity_class_bounds(self):
        for cls,value in [(3,1),(-1,1),(True,1),(0,0),(0,28)]:
            with self.assertRaises(ContractError):identity_slot(cls,value)
    def test_ack_revokes_metadata_access(self):
        window=MetadataWindow();before=window.snapshot(self.words(),0x100d)
        window.acknowledge()
        with self.assertRaises(ContractError):window.snapshot(self.words(),0x100d)
        self.assertFalse(before.permits_firmware_use)
    def test_id_reuse_does_not_establish_generation(self):
        old=select_kind16(self.words(),0x100d);new=select_kind16(self.words(),0x100d)
        self.assertEqual(old.capture_id,new.capture_id)
        self.assertTrue(old.requires_generation_qualification and new.requires_generation_qualification)
        self.assertFalse(old.permits_firmware_use or new.permits_firmware_use)
if __name__=='__main__':unittest.main()
