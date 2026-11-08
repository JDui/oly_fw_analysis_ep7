#!/usr/bin/env python3
"""Run the stock 1100 settings primitives with isolated single-frame DR cells."""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))

from ep7_candidate_startup_sim import BASE, CALLER, Machine, require, returned
from ep7_hl_storage_design import encode as encode_h1
from penf_emulator import Region

PART = 1769
STRIDE = 2 * PART
BANK = 0x624ea8dc
ACTIVE = 0x6250ba00
NATIVE_STAGE1 = 0x6225359c
NATIVE_STAGE2 = 0x62255850
LEVEL_CELLS = (894, 963, 966, 969, 1672, 998, 1001, 1004, 1675)

# Probe-only encoding. Stock/default words and all unknown encodings are OFF.
ENCODED = (0, 0x445201fe, 0x445202fd)


def selected(word):
    if word == ENCODED[1]:
        return 1
    if word == ENCODED[2]:
        return 2
    return 0


def inspect(image, engine):
    def stock(address, size):
        offset = address - BASE
        return image[offset:offset + size]

    require(len(image) == 26214336 and stock(BASE + 0xb6, 2) == b'\xfc\xdc'
            and struct.unpack('<I', stock(BASE + 0xb8, 4))[0] == BASE + 0xd9,
            'unexpected decoded-main size or entry mapping')
    require(stock(0x600b90c8, 4) == struct.pack('<HH', 0x8b64, 3560)
            and stock(0x60097da0, 4) == struct.pack('<HH', 0x85d4, 32040),
            'settings record headers differ')
    machine = Machine(image, engine)

    def add(name, address, data, *, alias_of=None):
        machine.regions[name] = Region(name, address, data, 'rw', True, alias_of=alias_of)

    def alias_region(name, address, data):
        add(name, address, data)
        add(name + '_alias', address + 0x40000000, data, alias_of=name)

    active_stock = stock(0x600b90cc, 3560 * 4)
    alias_region('active', ACTIVE, active_stock)
    alias_region('bank', BANK, stock(0x60097da4, 32040 * 4))
    add('settings_roots', 0x62253590, struct.pack('<3I', BANK, ACTIVE, 0))
    add('readonly_bank_root', 0xa2711a88, struct.pack('<I', 0x60078e2c))
    # Include the sparse 3000/4000/4500/10000/15000 bands that the native
    # 626-item list can visit, through the 274 words starting at stage2+7788.
    stage_size = NATIVE_STAGE2 - NATIVE_STAGE1
    add('reset_stage1', NATIVE_STAGE1, bytes(stage_size))
    add('reset_stage2', NATIVE_STAGE2, bytes(stage_size))
    # The real default accessor checks property 4508 for model overrides.
    # Use the stock-initialized cache mode and its single typed data pointer.
    require(stock(0x604d8810 + 8 * 2, 2) == struct.pack('<H', 0x0aa2)
            and stock(0x60090fac, 4) == struct.pack('<HH', 0x0aa2, 1),
            'default-override selector binding changed')
    selector = 0x624ba400 + (0x60090fb0 - 0x60090e98)
    add('stock_override_selector', selector, stock(0x60090fb0, 2))
    add('stock_override_selector_cache', 0xa269b92c, struct.pack('<I', selector))
    add('stock_cache_mode', 0xa269bf68, stock(0x60090fd8, 1))

    instructions = {}

    def native(entry, mask, frame, *, limit=10000, **registers):
        call = b'\xdd' + struct.pack('<i', entry - CALLER) + bytes((mask, frame))
        machine.regions['caller'] = Region('caller', CALLER, call, 'rx')
        budget = min(limit, 100000)
        result = machine.run(CALLER, CALLER + 7, overrides=registers, limit=budget)
        completed = result['completed']
        while result['status'] == 'instruction_limit' and completed < limit:
            result = machine.resume(result['registers'], CALLER + 7,
                                    limit=min(limit - completed, 100000))
            completed += result['completed']
        returned(result, CALLER + 7)
        key = f'{entry:#x}'
        instructions[key] = instructions.get(key, 0) + completed
        return result['registers']['d0']

    def write(property_id, value):
        native(0x602cc0d0, 0x80, 8, d0=property_id, d1=1, a0=value)

    def read(property_id, part=1):
        return native(0x602cc0a7, 0x80, 8, d0=property_id, d1=part)

    def active_word(property_id, part=1):
        address = ACTIVE + 4 * (part * PART + property_id)
        word = machine.read(address, 4)
        require(machine.read(address + 0x40000000, 4) == word,
                'settings aliases diverged')
        return struct.unpack('<I', word)[0]

    require(all(selected(active_word(key)) == 0 for key in LEVEL_CELLS),
            'stock ACTIVE profile did not decode OFF')
    require(all(selected(value) == 0 for value in (0x445203fc, 0xffffffff, encode_h1(2, -2))),
            'unknown or legacy H1 encoding was admitted as a DR level')

    # Model existing 015 H1 words in two profile scopes using its public codec.
    h1 = {927: encode_h1(3, -2), 939: encode_h1(-5, 4)}
    for key, word in h1.items():
        write(key, word)

    levels = (1, 1, 2, 0, 2, 1, 0, 2, 1)
    for key, level in zip(LEVEL_CELLS, levels):
        write(key, ENCODED[level])
    require(tuple(selected(read(key)) for key in LEVEL_CELLS) == levels,
            'profile-specific native getter did not return the requested level')
    require(machine.read(ACTIVE, PART * 4) == active_stock[:PART * 4],
            'HDR writes changed part 0')
    require(all(active_word(key) == word for key, word in h1.items()),
            'HDR writes changed neighboring H1 words')

    expected = machine.read(ACTIVE, STRIDE * 4)
    native(0x602cc03a, 0xc0, 12, d0=2, limit=800000)
    require(machine.read(BANK + 2 * STRIDE * 4, STRIDE * 4) == expected,
            'native bank save differs from ACTIVE')
    # Load an untouched stock bank first so stale ACTIVE data cannot pass recall.
    native(0x602cbffe, 0xc0, 12, d0=0, limit=800000)
    require(all(selected(active_word(key)) == 0 for key in LEVEL_CELLS),
            'untouched bank did not decode OFF on native recall')
    native(0x602cbffe, 0xc0, 12, d0=2, limit=800000)
    require(machine.read(ACTIVE, STRIDE * 4) == expected,
            'native bank recall did not restore the same two-part words')

    # Run the full stock 626-property partial-reset wrapper. It includes the
    # ordinary scope and leaves the COLOR profile curves and H1 words alone.
    native(0x602b960d, 0, 4, limit=400000)
    require(active_word(894) == active_word(894, 0) == 3200 and selected(active_word(894)) == 0,
            'stock ordinary reset did not restore the non-tagged default')
    require(tuple(selected(active_word(key)) for key in LEVEL_CELLS[1:]) == levels[1:]
            and all(active_word(key) == word for key, word in h1.items()),
            'ordinary reset touched independent profile levels or H1 words')

    # Call the same stock reset loop for exactly the COLOR2 HL entry from the
    # native full-reset list. The caller's count and start pointer are fixtures.
    full_list = struct.unpack('<1785H', stock(0x604aa952, 2 * 1785))
    color2_row = 0x604aa952 + 2 * full_list.index(966)
    native(0x602b9778, 0xf0, 28, d0=1, a0=color2_row)
    require(active_word(966) == active_word(966, 0) == 3 and selected(active_word(966)) == 0,
            'COLOR2 reset did not restore the non-tagged default')
    require(selected(active_word(963)) == 1 and all(active_word(key) == word for key, word in h1.items()),
            'single stock reset-loop entry changed COLOR1 or H1')

    return dict(status='passed', level_cells=list(LEVEL_CELLS),
                color1_level_before_reset=levels[1], color2_level_before_reset=levels[2],
                bank2_bytes_round_tripped=STRIDE * 4,
                ordinary_reset_default=3200, color2_reset_default=3,
                neighbor_h1_ids=list(h1), native_instruction_totals=instructions,
                hash_checks_performed=False, hardware_executed=False,
                limits=['Probe-only tags, explicit stock-initialized settings RAM and CPU0 aliases.',
                        'Whole native bank copies and the 626-item ordinary reset run.',
                        'COLOR2 is one actual reset-list row executed by the native loop.',
                        'No full GUI lifecycle, scheduling, power-cycle or group-7 backend write.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main', type=Path, required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.main.read_bytes(), args.engine), indent=2))
