#!/usr/bin/env python3
"""Read-only E-P7 1.1/1100 identity and COLOR landmark audit; JSON only.

No firmware output, disassembler, executable firmware, network or camera access.
Addresses are stock research landmarks, NEVER patch placements.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from oly_container import encode, parse, sha256

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = '9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb'
BASE = 0x60020020
TABLE = 0x6051de2c
TABLE_SHA = 'a33d64bdb78ac41ba24ccbff820380f563211a095ac08a12a7c37a51b5c00531'
SAT_IDS = (927, 939, 951, 1655)  # COLOR4 is NOT contiguous with COLOR1–3.
SAT_DEFAULTS = ([0]*12, [1,1,0,0,0,0,1,1,0,0,1,1],
                [4,4,4,4,4,3,4,4,4,4,4,4], [-4,0,0,0,-1,-1,-1,0,0,0,0,-4])


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(raw):
    # Reject wrong model/build BEFORE decoding or interpreting address operands.
    require(sha256(raw) == SOURCE_SHA, 'unsupported input: exact E-P7 1100 SHA-256 required')
    inventory = json.loads((ROOT/'provenance/firmware-inventory.json').read_text())
    reference = next(row for row in inventory if row['sha256'] == SOURCE_SHA)
    require(len(raw) == reference['bytes'], 'stock size mismatch')
    blocks = parse(raw)
    require(len(blocks) == len(reference['components']), 'component count mismatch')
    roundtrip = hashlib.sha256()
    component_report = []
    for block, expected in zip(blocks, reference['components']):
        require(block.header[2:4].hex() == '1420', 'wrong model')
        require(block.kind == int(expected['kind'], 16), 'component kind mismatch')
        require(block.offset == expected['offset'], 'component offset mismatch')
        require(block.address == int(expected['container_address'], 16), 'container address mismatch')
        require(len(block.payload) == expected['payload_bytes'], 'component size mismatch')
        require(struct.unpack_from('<H', block.header, 16)[0] == int(expected['header_build'], 16), 'component build mismatch')
        require(sha256(block.payload) == expected['decoded_sha256'], 'decoded component mismatch')
        roundtrip.update(block.header)
        roundtrip.update(encode(block.payload))
        roundtrip.update(block.trailer)
        # Deliberately omit raw headers, payloads, strings and disassembly.
        component_report.append(dict(kind=hex(block.kind), payload_bytes=len(block.payload),
                                     decoded_sha256=sha256(block.payload)))
    require(roundtrip.hexdigest() == SOURCE_SHA, 'roundtrip mismatch')
    main = blocks[0].payload
    require(main[0xb6:0xb8] == b'\xfc\xdc' and main[0xbc:0xbe] == b'\xf0\xf4', 'entry jump mismatch')
    require(struct.unpack_from('<I', main, 0xb8)[0] - 0xd9 == BASE and main[0xd9] == 0xcf,
            'runtime base witness mismatch')
    table = main[TABLE-BASE:TABLE-BASE+3028]
    require(sha256(table) == TABLE_SHA, 'COLOR table mismatch')
    require([b.payload.count(table) for b in blocks] == [1,0,0,0,0], 'table uniqueness mismatch')
    literal, call = 0x603b02d3-BASE, 0x603b02d9-BASE
    require(main[literal:literal+6] == b'\xfc\xdc'+struct.pack('<I', TABLE), 'table load mismatch')
    require(main[call] == 0xcd and BASE+call+struct.unpack_from('<h', main, call+1)[0] == 0x603b0068,
            'builder call mismatch')
    profiles = []
    for profile, (first, expected) in enumerate(zip(SAT_IDS, SAT_DEFAULTS), 1):
        values = list(struct.unpack_from('<12i', main, 0x604a8774-BASE+first*4))
        require(values == expected, f'COLOR{profile} defaults mismatch')
        profiles.append(dict(profile=profile, saturation_ids=list(range(first, first+12)),
                             default_saturation_matches=True))
    return dict(scope='Offline stock integrity and static landmarks only; NOT HSL execution or patch qualification',
                model='E-P7', public_version='1.1', build='1100', source_sha256=SOURCE_SHA,
                source_bytes=len(raw), exact_roundtrip=True, components=component_report,
                main_analysis_base=hex(BASE), color_table_sha256=TABLE_SHA,
                entry_mapping_checked=True, selector_builder_call_checked=True, profiles=profiles,
                firmware_output_created=False, camera_accessed=False, flash_ready=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    args = parser.parse_args()
    # stdout only: this program does not itself write files.
    print(json.dumps(audit(args.stock.read_bytes()), indent=2))


if __name__ == '__main__':
    main()
