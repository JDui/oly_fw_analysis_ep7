"""Check address-space isolation for the reused raw-reference scanner."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from penf_disasm import BASE, refs


class ReferenceBase(unittest.TestCase):
    def test_explicit_base_affects_relative_calls_and_result_addresses(self):
        base = 0x60020020
        target = base + 0x80
        data = bytearray(32)
        struct.pack_into('<I', data, 0, target)
        data[8] = 0xcd
        struct.pack_into('<h', data, 9, target - (base + 8))
        data[16] = 0xdd
        struct.pack_into('<i', data, 17, target - (base + 16))
        self.assertEqual(refs(data, target, base=base), ([base], [base + 8, base + 16]))
        self.assertEqual(refs(data, target, base=base + 0x1000), ([base + 0x1000], []))

    def test_existing_default_base_preserved(self):
        data = struct.pack('<I', BASE + 0x80)
        self.assertEqual(refs(data, BASE + 0x80), ([BASE], []))


if __name__ == '__main__':
    unittest.main()
