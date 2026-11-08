#!/usr/bin/env python3
"""Exercise the linked settings codec, actual bank copy and one bank epoch frame."""

import argparse
from dataclasses import replace
import json
from pathlib import Path
from struct import pack, unpack
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))

from ep7_candidate_startup_sim import BASE, CALLER, Machine, Region, SP, STACK, require, returned

ACTIVE = 0x6250BA00
BANK = 0x624EA8DC
PART = 1769
BANK_BYTES = 8 * PART
PUBLIC = 0x19200000


def probe(candidate, engine, prefix):
    report = json.loads((candidate / 'report.json').read_text(encoding='utf-8'))
    image = (candidate / report['image']).read_bytes()
    symbols = json.loads((candidate / 'symbols.json').read_text(encoding='utf-8'))
    entry = {name: int(row['address'], 16) for name, row in symbols.items()}
    machine = Machine(image, engine)

    def add(name, address, data, *, alias_of=None, permissions='rw'):
        machine.regions[name] = Region(name, address, data, permissions,
                                       'w' in permissions, alias_of=alias_of)

    def native(address, mask=0, frame=0, **registers):
        call = b'\xdd' + pack('<i', address - CALLER) + bytes((mask, frame))
        add('caller', CALLER, call, permissions='rx')
        result = machine.run(CALLER, CALLER + 7, overrides=registers, limit=100000)
        executed = result['completed']
        while result['status'] == 'instruction_limit' and executed < 500000:
            result = machine.resume(result['registers'], CALLER + 7, limit=100000)
            executed += result['completed']
        returned(result, CALLER + 7)
        return result['registers']['d0'], executed

    def stock(address, size):
        return image[address - BASE:address - BASE + size]

    def section(address, data, name):
        add(name, address, data)
        add(name + '_alias', address + 0x40000000, data, alias_of=name)

    def mutate_shared(name, offset, data):
        # The native runner shares the backing store while executing. Host
        # fixture edits must keep both serialized aliases equal as well.
        machine.mutate(name, offset, data)
        machine.mutate(name + '_alias', offset, data)

    def value(mode):
        return native(entry['_ep7dr_selected_level'], d0=mode)[0]

    def stage(mode, level):
        machine.mutate('public', 0, pack('<I', mode))
        return native(entry['_ep7dr_stage_level'], d0=mode, d1=level)[0]

    def cell(property_id):
        return unpack('<I', machine.read(ACTIVE + 4 * (PART + property_id), 4))[0]

    stock_active = stock(0x600B90CC, 3560 * 4)
    section(ACTIVE, stock_active, 'active')
    section(BANK, stock(0x60097DA4, 32040 * 4), 'bank')
    add('roots', 0x62253590, pack('<2I', BANK, ACTIVE))
    add('readonly_bank_root', 0xA2711A88, pack('<I', 0x60078E2C))
    add('typed_ring', 0xA2715C8C, bytes(4))
    add('typed_payload', 0xA2715ACC, bytes(448))
    add('inhibit', 0x62257B04, bytes(1))
    # Persistent native session state must allow normal reads and writes.
    add('native_session_latch', 0x622484FA, b'\x01')
    add('hfw_busy', 0x61FA7538, bytes(4))
    add('public', PUBLIC, pack('<I', 54))
    mutate_shared('active', 4 * (PART + 927), pack('<I', 0x4831BC43))

    with tempfile.TemporaryDirectory(prefix='ep7dr-settings-fixture-') as temporary:
        tmp = Path(temporary)
        (tmp / 'public.s').write_text(f"""
.text
.global fixture
fixture:
 mov ({PUBLIC:#x}),d0
 ret [],4
""", encoding='ascii')
        (tmp / 'mode.s').write_text("""
.text
.global fixture
fixture:
 mov (32,sp),d0
 cmp 0x1234,d0
 bne .Lwrong
 movbu (5,sp),d0
 cmp 0x5a,d0
 bne .Lwrong
 mov 54,d0
 call selected_level,[],0
 cmp -1,d0
 bne .Lwrong
 mov 7,d0
 ret [d2,d3,a2,a3],28
.Lwrong:
 mov 255,d0
 ret [d2,d3,a2,a3],28
""", encoding='ascii')
        for name, address in [('public', 0x602AFA81), ('mode', 0x602B3368)]:
            obj, elf, raw = (tmp / f'{name}.{suffix}' for suffix in ('o', 'elf', 'bin'))
            subprocess.run([prefix + 'as', '-o', obj, tmp / (name + '.s')], check=True)
            subprocess.run([prefix + 'ld', f'-Ttext={address:#x}', '-e', 'fixture',
                            f'--defsym=selected_level={entry["_ep7dr_selected_level"]:#x}',
                            '-o', elf, obj], check=True)
            subprocess.run([prefix + 'objcopy', '-O', 'binary', '-j', '.text', elf, raw],
                           check=True)
            machine.mutate('candidate', address - BASE, raw.read_bytes())

    # Before the original image-loaded flag, no observer may even read the
    # extension. Remove that mapping rather than initialize a convenient zero.
    resident = machine.regions.pop('private')
    machine.regions['load_flags'] = replace(machine.regions['load_flags'], data=bytes(8))
    native(entry['_ep7dr_bank_begin'])
    native(entry['_ep7dr_bank_end'])
    machine.regions['private'] = resident
    machine.regions['load_flags'] = replace(machine.regions['load_flags'], data=pack('<2I', 15, 15))

    require(value(54) == value(55) == 0, 'legacy settings did not default OFF')
    require(stage(54, 1) == 1 and stage(55, 2) == 1 and
            cell(963) == 0x445201FE and cell(966) == 0x445202FD,
            'linked setter did not write independently tagged native cells')
    require(value(54) == 1 and value(55) == 2 and cell(927) == 0x4831BC43,
            'linked getter or neighboring H1 differs')
    machine.mutate('typed_ring', 0, pack('<2H', 1, 0))
    require(value(54) == 0xFFFFFFFF and stage(54, 2) == 0 and cell(963) == 0x445201FE,
            'pending native typed write did not inhibit settings access')
    machine.mutate('typed_ring', 0, pack('<2H', 1, 1))
    require(value(54) == 1, 'settings did not resume after native ring drained')

    machine.mutate('typed_payload', 0,
                   pack('<4H5I', 1, 0x8B64, PART + 963, 0, ACTIVE, 0x445202FD, 0, 0, 0))
    machine.mutate('typed_ring', 0, pack('<2H', 1, 0))
    _, drained = native(0x6005E676, a0=0xA2715ACC)
    require(machine.read(0xA2715C8C, 4) == pack('<2H', 1, 1) and value(54) == 2,
            'native consumer did not publish the tagged value before advancing tail')
    require(stage(54, 1) == 1, 'could not edit after the actual native consumer returned')

    # Native cross-core dispatch admits domains 0, 1 and 2. An in-progress
    # bank transaction on either other domain must inhibit the GUI writer.
    for core in (1, 2):
        machine.regions['cpu_id'] = replace(machine.regions['cpu_id'], data=pack('<I', core))
        native(entry['_ep7dr_bank_begin'])
        machine.regions['cpu_id'] = replace(machine.regions['cpu_id'], data=bytes(4))
        require(value(54) == 0xFFFFFFFF and stage(54, 2) == 0 and cell(963) == 0x445201FE,
                f'domain {core} bank transaction did not inhibit access')
        machine.regions['cpu_id'] = replace(machine.regions['cpu_id'], data=pack('<I', core))
        native(entry['_ep7dr_bank_end'])
        machine.regions['cpu_id'] = replace(machine.regions['cpu_id'], data=bytes(4))
        require(value(54) == 1, 'settings did not resume after other-core transaction')

    machine.mutate('stack', SP - STACK + 4, pack('<I', 0x1234))
    observer, observed = native(0x602B3363, 0xF0, 28, a0=0x5A)
    require(observer == 7 and value(54) == 1,
            'mode observer frame or transient busy decision differs')

    active = machine.read(ACTIVE, BANK_BYTES)
    _, saved = native(0x602CC03A, 0xC0, 12, d0=2)
    require(machine.read(BANK + 2 * BANK_BYTES, BANK_BYTES) == active,
            'wrapped native bank save differs from ACTIVE')
    mutate_shared('active', 0, stock_active)
    require(value(54) == value(55) == 0, 'old ACTIVE fixture no longer defaults OFF')
    _, restored = native(0x602CBFFE, 0xC0, 12, d0=2)
    require(machine.read(ACTIVE, BANK_BYTES) == active and
            value(54) == 1 and value(55) == 2 and cell(927) == 0x4831BC43,
            'native bank recall did not preserve tagged levels and H1')

    return dict(status='passed', native_stage_and_active_get=True,
                persistent_native_session_latch=1,
                initial_legacy_levels=[0, 0], recalled_color_levels=[1, 2],
                adjacent_h1_preserved=True, pending_typed_ring_rejected=True, bank_bytes=BANK_BYTES,
                early_observer_without_private_mapping=True,
                bank_domains_covered=[0, 1, 2],
                native_typed_consumer_instructions=drained,
                mode_epoch_fixture_instructions=observed,
                wrapped_native_save_instructions=saved, native_recall_instructions=restored,
                fixture_replacements=['public Picture Mode getter', 'mode bank body after veneer'],
                physical_save_verified=False, hash_checks_performed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--prefix', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = probe(args.candidate, args.engine, args.prefix)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='ascii')
    print(result['status'])


if __name__ == '__main__':
    main()
