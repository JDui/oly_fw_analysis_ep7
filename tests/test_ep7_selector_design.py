import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from ep7_selector_design import SelectorDesign, normalize_index, navigate, enabled_categories

class DesignTests(unittest.TestCase):
    def test_stock_order_preserved(self):
        self.assertEqual(SelectorDesign(54).categories[:4],(0,1,2,3))
    def test_COLOR_enable_only_known_modes(self):
        for mode in (54,55,56,64):self.assertEqual(enabled_categories(mode)[4:],(True,True))
        for mode in (57,58,59,65,0,999):self.assertEqual(enabled_categories(mode)[4:],(False,False))
    def test_hue_to_mono_normalizes_focus(self):
        self.assertEqual(SelectorDesign(54,4).change_mode(57).focus,0)
    def test_luminance_to_unknown_normalizes_focus(self):
        self.assertEqual(SelectorDesign(64,5).change_mode(999).focus,0)
    def test_stock_focus_preserved(self):
        for focus in range(4):self.assertEqual(SelectorDesign(54,focus).change_mode(57).focus,focus)
    def test_COLOR_to_COLOR_preserves_axis_focus(self):
        self.assertEqual(SelectorDesign(54,5).change_mode(55).focus,5)
    def test_nonCOLOR_navigation_skips_proposed_entries(self):
        self.assertEqual(SelectorDesign(57,3).step(1).focus,0)
        self.assertEqual(SelectorDesign(57,0).step(-1).focus,3)
    def test_COLOR_navigation_includes_proposed_entries(self):
        self.assertEqual(SelectorDesign(54,3).step(1).focus,4)
        self.assertEqual(SelectorDesign(54,5).step(1).focus,0)
    def test_empty_and_all_disabled_fail_closed(self):
        for enabled in ((),(False,),(False,)*6):
            for remembered in (None,-1,0,5,999):
                self.assertIsNone(normalize_index(remembered,enabled))
                for direction in (-1,1):self.assertIsNone(navigate(remembered,enabled,direction))
    def test_single_enabled_is_bounded(self):
        for direction in (-1,1):self.assertEqual(navigate(2,(False,False,True),direction),2)
    def test_invalid_index_normalized(self):
        for focus in (None,-1,999):self.assertEqual(normalize_index(focus,(False,True,False)),1)
    def test_invalid_direction_rejected(self):
        for direction in (0,2,-2):
            with self.assertRaises(ValueError):navigate(0,(True,),direction)
    def test_proposed_views_explicitly_named(self):
        self.assertEqual(SelectorDesign(54,4).selected_view(),'proposed_hue')
        self.assertEqual(SelectorDesign(54,5).selected_view(),'proposed_luminance')
        self.assertEqual(SelectorDesign(57,4).selected_view(),'stock_category_0')
if __name__ == '__main__':unittest.main()
