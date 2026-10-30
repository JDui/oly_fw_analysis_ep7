import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import ep7_editor_contracts as contracts


class EP7EditorContractTests(unittest.TestCase):
    def test_bad_input_rejected_before_table_decode(self):
        with patch.object(contracts, 'parse') as parse:
            with self.assertRaisesRegex(ValueError, 'exact E-P7 1100'):
                contracts.inspect(b'wrong firmware')
            parse.assert_not_called()

    def test_noncontiguous_profile_four(self):
        self.assertEqual(contracts.EDITOR_KEYS, (0x13b3,0x13b4,0x13b5,0x140c))
        self.assertEqual(contracts.CURSOR_IDS, (1091,1096,1097,1686))

    def test_key_pairs_have_distinct_application_events(self):
        self.assertEqual(len({row[3] for row in contracts.KEY_ROWS}), 6)
        for i in (0,2,4):
            self.assertEqual(contracts.KEY_ROWS[i+1][2]-contracts.KEY_ROWS[i][2], 0x10000)
            self.assertEqual(contracts.KEY_ROWS[i+1][3]-contracts.KEY_ROWS[i][3], 1)


if __name__ == '__main__':
    unittest.main()
