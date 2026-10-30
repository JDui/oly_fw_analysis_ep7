import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import unittest
import ep7_hl_storage_design as m
class Tests(unittest.TestCase):
    def test_all_valid_pairs_roundtrip(self):
        for h in range(-7,8):
            for l in range(-7,8):self.assertEqual(m.decode(m.encode(h,l)),(h,l))
    def test_all_256_packed_values(self):
        for p in range(256):
            got=m.decode((m.TAG<<16)|((p^255)<<8)|p)
            if p&15==8 or p>>4==8:self.assertEqual(got,(0,0))
            else:self.assertEqual(m.encode(*got)&255,p)
    def test_invalid_format_and_reset_neutral(self):
        for v in (None,0,-1,0xffffffff,0x48310000,0x4830ff00,1<<32,True):
            self.assertEqual(m.decode(v),(0,0))
    def test_complement_bit_corruption(self):
        cell=m.encode(3,-4)
        for bit in range(32):self.assertEqual(m.decode(cell^(1<<bit)),(0,0))
    def test_exact_four_profiles(self):
        ids=[m.property_id(mode,s) for mode in m.PROFILE_BASES for s in range(12)]
        self.assertEqual(len(set(ids)),48)
        self.assertEqual(ids,list(range(927,963))+list(range(1655,1667)))
        for mode in m.PROFILE_BASES:
            for s in range(12):self.assertEqual(m.profile_sector(m.property_id(mode,s)),(mode,s))
    def test_color4_not_contiguous(self):
        self.assertEqual(m.property_id(64,0),1655)
        self.assertEqual(m.property_id(64,11),1666)
        for i in (926,963,1654,1667):
            with self.assertRaises(ValueError):m.profile_sector(i)
    def test_invalid_mode_sector(self):
        for mode,sector in ((57,0),(54,-1),(54,12),(54,True),(True,0),(64,1.0)):
            with self.assertRaises(ValueError):m.property_id(mode,sector)
    def test_axis_preservation(self):
        self.assertEqual(m.decode(m.edit_axis(m.encode(2,-3),1655,'hue',7)),(7,-3))
        self.assertEqual(m.decode(m.edit_axis(m.encode(2,-3),1666,'luminance',-7)),(2,-7))
    def test_reset_then_edit_neutral_other_axis(self):
        self.assertEqual(m.decode(m.edit_axis(0,927,'hue',1)),(1,0))
    def test_invalid_edit_rejected(self):
        for pid,axis,value in ((963,'hue',0),(927,'saturation',0),(927,'hue',8),(927,'hue',-8),(927,'hue',True)):
            with self.assertRaises(ValueError):m.edit_axis(0,pid,axis,value)
    def test_candidate_indices_separate_from_typed_s(self):
        self.assertEqual(m.candidate_index(54,0),2696)
        self.assertEqual(m.candidate_index(64,11),3435)
        for bank in range(9):self.assertEqual(m.candidate_index(64,11,bank),bank*3538+3435)
        for bank in (-1,9,True):
            with self.assertRaises(ValueError):m.candidate_index(54,0,bank)
if __name__=='__main__':unittest.main()
