"""Focused offline checks for version pinning and optional hash recording."""
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import om_firmware_catalog as catalog


class CatalogInputPolicy(unittest.TestCase):
    def run_catalog(self, folder, version='1100', payload=b'abcd', size=4):
        response = folder / 'response.xml'
        response.write_text(f'''<firmware_result><firmwares><firmware_info>
<model_id>1420</model_id><model_name>E-P7</model_name><version>{version}</version>
<file_name>OLY_E_142_{version}_0000_0000.BIN</file_name><file_size>{size}</file_size>
<url>https://dl01.om-digitalsolutions.net/OMDS/FIRMWARES/0001/1420/OLY_E_142_{version}_0000_0000.BIN</url>
</firmware_info></firmwares></firmware_result>''')
        args = ['catalog', '--response', str(response), '--model-id', '1420',
                '--model-name', 'E-P7', '--expect-version', '1100', '--no-hash',
                '--download', '--out', str(folder / 'out')]
        with patch.object(sys, 'argv', args), patch.object(catalog.hashlib, 'sha256', side_effect=AssertionError('unexpected hash')), \
                patch.object(catalog.urllib.request, 'urlopen', return_value=io.BytesIO(payload)) as network, \
                patch('sys.stdout', new_callable=io.StringIO):
            catalog.main()
        return network

    def test_no_hash_still_downloads_and_records_length(self):
        import json
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            self.run_catalog(folder).assert_called_once()
            report = json.loads((folder / 'out/catalog-summary.json').read_text())
            self.assertEqual(report['download'], {'bytes': 4, 'hash_recorded': False})
            self.assertEqual((folder / 'out/OLY_E_142_1100_0000_0000.BIN').read_bytes(), b'abcd')

    def test_other_version_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            with self.assertRaisesRegex(ValueError, 'catalog version'):
                self.run_catalog(folder, version='1200')
            self.assertFalse((folder / 'out').exists())

    def test_short_download_still_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, 'download size'):
                self.run_catalog(Path(td), size=5)


if __name__ == '__main__':
    unittest.main()
