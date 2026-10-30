#!/usr/bin/env python3
"""Prepare a local E-P7 research input using container structure, without SHA.

This does not establish byte identity with historical hash-pinned reports.
It decodes stock only, never modifies firmware or produces an install image.
"""
import argparse
import json
from pathlib import Path
import struct

from oly_container import encode, parse

ROOT = Path(__file__).resolve().parents[1]
FILENAME = 'OLY_E_142_1100_0000_0000.BIN'
BASE = 0x60020020


def prepare(stock, out, main_component_only=False):
    if out.exists():
        raise ValueError('output directory must be new')
    rows = json.loads((ROOT / 'provenance/firmware-inventory.json').read_text())
    reference = next(row for row in rows if row['model'] == 'E-P7' and FILENAME in row['filenames'])
    expected_components = reference['components'][:1] if main_component_only else reference['components']
    expected_bytes = expected_components[0]['payload_bytes'] + 64 if main_component_only else reference['bytes']
    with stock.open('rb') as stream:
        raw = stream.read(expected_bytes) if main_component_only else stream.read()
    if len(raw) != expected_bytes:
        raise ValueError('unsupported input length')
    # parse checks every header/trailer pair, component bound and additive sum.
    blocks = parse(raw)
    if len(blocks) != len(expected_components):
        raise ValueError('component count mismatch')
    components = []
    for block, expected in zip(blocks, expected_components):
        actual = dict(offset=block.offset, payload_bytes=len(block.payload),
                      kind=hex(block.kind), header_build=f'{struct.unpack_from("<H", block.header, 16)[0]:04x}',
                      model_bytes=block.header[2:4].hex(), container_address=hex(block.address))
        if actual != {key: expected[key] for key in actual}:
            raise ValueError(f'component structure mismatch at {block.offset:#x}')
        encoded = block.header + encode(block.payload) + block.trailer
        if encoded != raw[block.offset:block.offset + len(encoded)]:
            raise ValueError('unchanged container roundtrip differs')
        components.append(actual)
    main = blocks[0].payload
    if (main[0xb6:0xb8] != b'\xfc\xdc' or main[0xbc:0xbe] != b'\xf0\xf4'
            or struct.unpack_from('<I', main, 0xb8)[0] - 0xd9 != BASE or main[0xd9] != 0xcf):
        raise ValueError('main entry/runtime mapping witnesses mismatch')
    report = dict(scope=__doc__.strip(), bytes=len(raw), model='E-P7', build='1100',
                  whole_container_checked=not main_component_only,
                  components=components, component_sums_valid=True, unchanged_roundtrip_equal=True,
                  runtime_base=hex(BASE), entry_witnesses_match=True, hash_checks_performed=False,
                  historical_exact_byte_identity_proven=False, firmware_modified=False,
                  firmware_executed=False, camera_accessed=False, flash_ready=False)
    out.mkdir(parents=True)
    (out / 'main.decoded.bin').write_bytes(main)
    (out / 'input-report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True, help='new private/ignored output directory')
    parser.add_argument('--main-component-only', action='store_true', help='check only the complete first component; does not validate whole download')
    args = parser.parse_args()
    print(json.dumps(prepare(args.stock, args.out, args.main_component_only), indent=2))
