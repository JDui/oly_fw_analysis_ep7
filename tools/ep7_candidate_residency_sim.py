#!/usr/bin/env python3
"""Audit final E-P7 placement and execute load -> cold clear with actual bytes.

The boot prefix is an explicit resident input. Only lower storage transfers are
modeled; code banks begin as poison and are not supplied as resident firmware.
No new CPU model, firmware build, package output, SHA or camera operation.
"""
import argparse
from collections import Counter
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_package import check_candidate, check_components
from ep7_candidate_startup_sim import CLEAR_SITE, CLEAR_RESUME, require
from ep7_early_load_probe import BEGIN, END, LOW, HIGH, UNCACHED, READS, EXPECTED_READS
from ep7_installation_manifest import BASE, load_region
from ep7_load_regions import EARLY, SECTIONS
from ep7_offline_candidate import RAM_START, RAM_BYTES
from ep7_ram_ownership import FENCES, KERNEL
from ep7_sim_probe import brief
from oly_container import parse
from penf_emulator import Region, execute


STACK, SP = 0x47000000, 0x470007ec
MAIN_FLASH_PAYLOAD = 0x406a0020
LITERAL_KEYS = (0x406a0000, 0x406a0020, 0x60020020, 0x600200f9,
                0x60026f38, 0x61bd6d40, 0xdeb10000, 0xdeb30000)


def cached(address):
    return address - 0x40000000 if 0xa0000000 <= address < 0xb0000000 else address


def overlap(a, b):
    return a[0] < b[1] and b[0] < a[1]


def placement(data, stock, build):
    spans = []
    for row in build['patches']:
        start, size = int(row['site'], 16), row['bytes']
        load = load_region(start, size)
        require(load['stage'] == row['load_stage'], 'recorded load stage changed')
        spans.append(dict(start=hex(start), end_exclusive=hex(start+size), bytes=size,
                          kind=row['kind'], load=load))
    for row in build['layout']:
        if row['section'].startswith('.ep7_code'):
            start, end = int(row['start'], 16), int(row['end'], 16)
            spans.append(dict(start=hex(start), end_exclusive=hex(end), bytes=end-start,
                kind=row['section'], load=load_region(start, end-start)))
    require(len(spans) == 103, 'final write-span inventory changed')
    prefixes = [r for r in spans if not r['load']['loader_path_identified']]
    require([r['start'] for r in prefixes] == ['0x600201fe', '0x600229b9', '0x60022c28'],
            'boot-prefix dependency changed')
    require(data[0x600229b9-BASE:0x600229bb-BASE] == bytes.fromhex('801f') and
            data[0x60022c28-BASE:0x60022c2a-BASE] == bytes.fromhex('8f1f'),
            'actual final pool reservation operands changed')

    # These are the established finite original write recipes, not an inventory
    # of every indirect/DMA write in the firmware. Count an arena as owned too.
    writes = [('primary_BSS_clear', 0x62038100, 0x6203c934),
              ('shared_BSS_clear', 0x621caf00, 0x62796888),
              ('initialized_data', 0x61b20fe0, 0x61b218a8),
              ('helper_staging', 0xa143ca00, 0xa143e200),
              ('per_core_helper', 0x47000800, 0x47002000),
              ('version_tail', 0x6191ffe0, 0x61920000)]
    writes += [(f'early_data_{i}', row[8], row[8]+row[6]-row[5])
               for i, row in enumerate(EARLY[1:], 1)]
    writes += [(f'section_{i}', lo, hi) for i, lo, hi, _ in SECTIONS]
    writes += [(f'kernel_arena_{i}', lo, lo+size) for i, (_, lo, size) in enumerate(KERNEL)]
    protected = [(r['section'], cached(int(r['start'], 16)), cached(int(r['end'], 16)))
                 for r in build['layout'] if r['section'].startswith('.ep7_code')]
    protected.append(('reserved_pool_payload', cached(RAM_START), cached(RAM_START)+RAM_BYTES))
    checked = []
    for name, lo, hi in writes:
        normalized = (cached(lo), cached(hi))
        collisions = [n for n, a, b in protected if overlap(normalized, (a, b))]
        require(not collisions, 'known original write collides: '+name+' '+str(collisions))
        checked.append(dict(name=name, start=hex(lo), end_exclusive=hex(hi),
                            normalized_start=hex(normalized[0]), protected_collisions=collisions))
    guard_table = 0x60026f38
    require(data[guard_table-BASE:guard_table-BASE+112] ==
            stock[guard_table-BASE:guard_table-BASE+112], 'guard table was modified')
    fence = FENCES[3]
    require(struct.unpack_from('<4I', data, guard_table-BASE+48) == fence,
            'big-pool guard recipe differs')
    last_payload = fence[0]+127*(fence[1]+64)
    require(last_payload == cached(RAM_START), 'reserved payload is not global slot127')
    bss = next(r for r in build['layout'] if r['section'] == '.bss')
    return dict(write_spans=spans, span_counts_by_stage=dict(Counter(r['load']['stage'] for r in spans)),
        identified_loader_spans=len(spans)-len(prefixes), external_prefix_spans=len(prefixes),
        known_original_write_ranges=checked, known_recipe_collision_count=0,
        private_ram=dict(start=hex(RAM_START), bytes=RAM_BYTES, linked_bss_bytes=bss['bytes'],
            unused_reserved_bytes=RAM_BYTES-bss['bytes'], original_domain=2, original_slot=31,
            original_global_slot=127, candidate_native_slot_count=31,
            preserved_guard_start=hex(last_payload+fence[1]), preserved_guard_bytes=64,
            expected_guard_word=hex(fence[3] | 127), guard_table_unchanged=True,
            guard_initialization_identified=False, late_reservation_is_invalid=True),
        all_indirect_or_DMA_writers_excluded=False, ownership_qualified=False)


def loaded_clear(data, engine):
    diagnostic_source = 0x6002e020 + (0x61b213a4-0x61b20fe0)
    diagnostic = data[diagnostic_source-BASE:diagnostic_source-BASE+4]
    require(diagnostic == bytes(4), 'original initialized diagnostic switch changed')
    regions = [
        Region('resident_prefix_assumption', BASE, data[:LOW-BASE], 'rx'),
        Region('loaded', LOW, b'\xa5'*(HIGH-LOW), 'rx', True),
        Region('uncached_load_alias', UNCACHED, b'\xa5'*(HIGH-LOW), 'rw', False, 'loaded'),
        Region('stack', STACK, b'\xcc'*2048, 'rw', True),
        Region('private', RAM_START, b'\xa5'*RAM_BYTES, 'rw', True),
        Region('private_before', RAM_START-64, b'\x5a'*64),
        Region('private_after', RAM_START+RAM_BYTES, b'\x5a'*64),
        Region('load_end', 0x6218d980, bytes(4), 'rw', True),
        Region('next_copy_end', 0x6218d984, struct.pack('<I', 0x6025eb50)),
        Region('cold_ready_flags', 0x8ff00058, bytes(3)),
        Region('initialized_diagnostic_switch', 0x61b213a4, diagnostic),
        Region('saturated_log_count', 0xa26ff938, struct.pack('<I', 100)),
        Region('stationary_timer', 0x9890014c, struct.pack('<I', 0x3fffffff))]
    memory = {r.name: r for r in regions}
    registers = dict(pc=BEGIN, sp=SP, psw=0, d2=1, d3=0x33445566,
                     a2=0x44556677, a3=0x55667788)
    reads, chunks = [], []

    def run(stop, limit, hooks=()):
        # Region aliases share storage inside the engine; their input snapshots
        # must also agree after a modeled read or a prior engine invocation.
        memory['uncached_load_alias'] = replace(memory['uncached_load_alias'],
                                               data=memory['loaded'].data)
        result = execute(list(memory.values()), registers, stop, limit=limit,
            trace_limit=limit, engine=engine, record_hashes=False, timeout=20,
            breakpoints=hooks)
        require(result.get('hash_checks_performed') is False, 'unexpected hash mode')
        require(len(result['trace']) == result['completed'], 'trace incomplete')
        for row in result['memory']:
            name = row['name']
            memory[name] = replace(memory[name], data=bytes.fromhex(row['hex']))
        chunks.append(brief(result))
        return result

    for _ in range(4):
        result = run(END, 500, tuple(READS))
        registers = result['registers']
        require(result['status'] in ('breakpoint', 'returned'), 'loader frontier: '+str(brief(result)))
        if result['status'] == 'returned':
            break
        pc = registers['pc']
        request = (pc, registers['d1'], registers['d0'], registers['a0'])
        require(len(reads) < 3 and request == EXPECTED_READS[len(reads)], 'storage request changed')
        _, source, dest, size = request
        source_offset, dest_offset = source-MAIN_FLASH_PAYLOAD, dest-UNCACHED
        payload = data[source_offset:source_offset+size]
        require(len(payload) == size, 'storage request outside candidate payload')
        current = memory['loaded'].data
        memory['loaded'] = replace(memory['loaded'],
            data=current[:dest_offset]+payload+current[dest_offset+size:])
        operation, native_return = READS[pc]
        reads.append(dict(operation=operation, source=hex(source), destination=hex(dest),
                          bytes=size, modeled_lower_storage_result=0,
                          actual_return_instruction=hex(native_return)))
        registers = dict(registers, pc=native_return, d0=0)
    require(result['status'] == 'returned' and registers['pc'] == CLEAR_SITE and len(reads) == 3,
            'load did not reach actual clear hook')
    require(memory['loaded'].data == data[LOW-BASE:HIGH-BASE], 'loaded bytes differ from final candidate')
    require(registers['sp'] == SP and memory['load_end'].data == struct.pack('<I', HIGH),
            'original load return/frame changed')
    require(memory['private'].data == b'\xa5'*RAM_BYTES, 'private RAM changed before clear hook')
    before, old_stack = dict(registers), memory['stack'].data
    result = run(CLEAR_RESUME, 20000)
    require(result['status'] == 'returned' and result['fault'] is None, 'loaded clear failed: '+str(brief(result)))
    require(result['registers'] == dict(before, pc=CLEAR_RESUME, d0=0x6025eb50),
            'loaded clear did not preserve original MOV semantics and registers')
    require(memory['private'].data == bytes(RAM_BYTES), 'loaded clear missed private bytes')
    require(memory['loaded'].data == data[LOW-BASE:HIGH-BASE], 'clear changed loaded code')
    stack = memory['stack'].data
    require(stack[:SP-STACK-16] == old_stack[:SP-STACK-16] and stack[SP-STACK:] == old_stack[SP-STACK:],
            'clear changed stack outside its 16-byte frame')
    return dict(reads=reads, engine_chunks=chunks,
        instructions=sum(r['completed'] for r in chunks),
        original_load_executed=True, exact_final_loaded_bytes=True,
        loaded_bytes=HIGH-LOW, candidate_code_banks_preloaded_by_harness=False,
        execution_regions=['resident_prefix_assumption', 'loaded'],
        actual_clear_hook=hex(CLEAR_SITE), actual_resume=hex(CLEAR_RESUME),
        private_poison_untouched_before_hook=True, cleared_bytes=RAM_BYTES,
        original_next_copy_end=hex(0x6025eb50), all_other_registers_restored=True,
        clear_frame_bytes=16, stack_pointer=hex(SP),
        canaries_readonly_and_unchanged=True,
        storage_transfer_is_model=True, prefix_loader_executed=False,
        hardware_cache_or_MPU_executed=False)


def literal_survey(stock_path, decoded_stock):
    blocks = parse(stock_path.read_bytes())
    check_components(blocks)
    require(blocks[0].payload == decoded_stock, 'survey package main differs from the reviewed stock')
    rows = []
    for block in blocks:
        found = {}
        for key in LITERAL_KEYS:
            needle, positions = struct.pack('<I', key), []
            at = block.payload.find(needle)
            while at >= 0:
                positions.append(hex(at))
                at = block.payload.find(needle, at+1)
            found[hex(key)] = positions
        rows.append(dict(kind=hex(block.kind), payload_bytes=len(block.payload), literal_offsets=found))
    return dict(components=rows, scope='Eight exact little-endian32 literals, at every byte offset',
        absent_literal_is_not_absent_computed_reference=True,
        startup_prefix_loader_identified=False, guard_initializer_identified=False,
        note='The three main406a0000 matches are range-end comparisons at6002071e/60020744/600208b2, not copies. Other components have no searched literals; this is not full disassembly.')


def inspect(stock_path, decoded, directory, prefix, engine):
    data, build, count = check_candidate(decoded, directory, prefix)
    require(count == 103, 'candidate package span inventory changed')
    stock_data = decoded.read_bytes()
    layout = placement(data, stock_data, build)
    execution = loaded_clear(data, engine)
    survey = literal_survey(stock_path, stock_data)
    return dict(scope=__doc__, status='passed',
        candidate_build_revision=build['source_revision'], layout=layout,
        actual_load_and_clear=execution, bounded_component_survey=survey,
        hash_checks_performed=False, firmware_rebuilt=False, firmware_written=False,
        hardware_executed=False, installable=False, installation_authorized=False,
        remaining_conditions=[
            'Reset/upstream loading of the three changed prefix spans is unproved; the prefix is explicitly resident in this test.',
            'The two code-bank interiors have finite reference and load evidence, not exhaustive ownership or physical execute/cache qualification.',
            'CPU2 last-slot reservation must precede all allocation. Real cold pool initialization, guard initialization, bypass writers and one-slot capacity remain unqualified.',
            'Known copy/clear/arena intervals do not collide. This does not exclude unknown or indirect later writes, resets or DMA.',
            'Lower storage success and coherent cached/uncached aliases are explicit models; the earlier failing-read evidence is unchanged.',
            'Whole task/IRQ stack bounds, physical startup/display/photo behavior and independent recovery remain unproved.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--decoded-stock', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--tool-prefix', required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.stock, args.decoded_stock, args.candidate,
                             args.tool_prefix, args.engine), indent=2))
