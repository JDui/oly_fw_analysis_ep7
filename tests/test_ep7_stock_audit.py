"""Input-free guards, not a substitute for the exact proprietary stock audit."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import ep7_stock_audit as audit


class EP7StockAuditTests(unittest.TestCase):
    def test_unknown_inputs_rejected_before_decode(self):
        for data in (b'', b'OE\x14\x20'+bytes(60), b'PEN-F 3101', bytes(1024)):
            with self.subTest(size=len(data)), patch.object(audit, 'parse') as parse:
                with self.assertRaisesRegex(ValueError, 'exact E-P7 1100'):
                    audit.audit(data)
                parse.assert_not_called()

    def test_four_profiles_noncontiguous(self):
        self.assertEqual(audit.SAT_IDS, (927, 939, 951, 1655))
        self.assertEqual(len(audit.SAT_DEFAULTS), 4)
        self.assertTrue(all(len(row) == 12 for row in audit.SAT_DEFAULTS))
        self.assertEqual(len({i for start in audit.SAT_IDS for i in range(start, start+12)}), 48)

    def test_manifest_identity_consistent(self):
        import json
        rows = json.loads((ROOT/'provenance/firmware-inventory.json').read_text())
        entry = next(row for row in rows if row['sha256'] == audit.SOURCE_SHA)
        self.assertEqual(entry['model'], 'E-P7')
        self.assertEqual(entry['bytes'], 111017984)
        self.assertEqual([x['model_bytes'] for x in entry['components']], ['1420']*5)


if __name__ == '__main__':
    unittest.main()
