#!/usr/bin/env python3
"""Audit E-P7 placement and original load -> image-initialized private state.

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
from ep7_offline_candidate import RAM_IMAGE_START, RAM_START, RAM_BYTES, PRIVATE_SECTION
from ep7_ram_ownership import KERNEL
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
        elif row['section'] == PRIVATE_SECTION:
            spans.append(dict(start=hex(RAM_IMAGE_START), end_exclusive=hex(RAM_IMAGE_START+RAM_BYTES),
                bytes=RAM_BYTES, kind=PRIVATE_SECTION, load=load_region(RAM_IMAGE_START,RAM_BYTES)))
    require(len(spans) == 101, 'final write-span inventory changed')
    prefixes = [r for r in spans if not r['load']['loader_path_identified']]
    require(not prefixes and data[:LOW-BASE] == stock[:LOW-BASE], 'boot prefix must remain original')
    require(data[0x600229b9-BASE:0x600229bb-BASE] == bytes.fromhex('8020') and
            data[0x60022c28-BASE:0x60022c2a-BASE] == bytes.fromhex('8f20'),
            'original pool capacity changed')

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
    protected.append(('image_initialized_state', RAM_IMAGE_START, RAM_IMAGE_START+RAM_BYTES))
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
    private = next(r for r in build['layout'] if r['section'] == PRIVATE_SECTION)
    return dict(write_spans=spans, span_counts_by_stage=dict(Counter(r['load']['stage'] for r in spans)),
        identified_loader_spans=len(spans)-len(prefixes), external_prefix_spans=len(prefixes),
        known_original_write_ranges=checked, known_recipe_collision_count=0,
        private_ram=dict(start=hex(RAM_START),image_address=hex(RAM_IMAGE_START),bytes=RAM_BYTES,
            linked_bss_bytes=private['bss_bytes'],unused_reserved_bytes=private['remaining'],
            initialized_by_original_early_copy=True, cpu2_pool_slots=32,
            pool_reservation_required=False, guard_table_unchanged=True),
        all_indirect_or_DMA_writers_excluded=False, ownership_qualified=False)


def loaded_state(data, engine):
    diagnostic_source = 0x6002e020 + (0x61b213a4-0x61b20fe0)
    diagnostic = data[diagnostic_source-BASE:diagnostic_source-BASE+4]
    require(diagnostic == bytes(4), 'original initialized diagnostic switch changed')
    regions = [
        Region('resident_prefix_assumption', BASE, data[:LOW-BASE], 'rx'),
        Region('loaded', LOW, b'\xa5'*(HIGH-LOW), 'rx', True),
        Region('uncached_load_alias', UNCACHED, b'\xa5'*(HIGH-LOW), 'rw', False, 'loaded'),
        Region('stack', STACK, b'\xcc'*2048, 'rw', True),
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
            'load did not reach original prefix continuation')
    require(memory['loaded'].data == data[LOW-BASE:HIGH-BASE], 'loaded bytes differ from final candidate')
    require(registers['sp'] == SP and memory['load_end'].data == struct.pack('<I', HIGH),
            'original load return/frame changed')
    state_offset = RAM_IMAGE_START-LOW
    require(memory['loaded'].data[state_offset:state_offset+RAM_BYTES] == bytes(RAM_BYTES),
            'original loader did not initialize the complete private state')
    before, old_stack = dict(registers), memory['stack'].data
    result = run(CLEAR_RESUME, 20)
    require(result['status'] == 'returned' and result['fault'] is None, 'original continuation failed: '+str(brief(result)))
    require(result['registers'] == dict(before, pc=CLEAR_RESUME, d0=0x6025eb50),
            'original MOV semantics and registers changed')
    require(memory['loaded'].data == data[LOW-BASE:HIGH-BASE], 'original MOV changed loaded bytes')
    stack = memory['stack'].data
    require(stack == old_stack, 'original MOV changed stack')
    return dict(reads=reads, engine_chunks=chunks,
        instructions=sum(r['completed'] for r in chunks),
        original_load_executed=True, exact_final_loaded_bytes=True,
        loaded_bytes=HIGH-LOW, candidate_code_banks_preloaded_by_harness=False,
        execution_regions=['resident_prefix_assumption', 'loaded'],
        original_mov=hex(CLEAR_SITE), actual_resume=hex(CLEAR_RESUME),
        private_state_started_poisoned=True, image_initialized_bytes=RAM_BYTES,
        original_next_copy_end=hex(0x6025eb50), all_other_registers_restored=True,
        new_clear_hook_required=False, stack_pointer=hex(SP),
        state_shares_original_load_alias=True, continuation_stack_unchanged=True,
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
    require(count == 101, 'candidate package span inventory changed')
    stock_data = decoded.read_bytes()
    layout = placement(data, stock_data, build)
    execution = loaded_state(data, engine)
    return dict(scope=__doc__, status='passed',
        candidate_build_revision=build['source_revision'], layout=layout,
        actual_load_and_initialize=execution,
        historical_component_survey='research/ep7/candidate-residency-sim.json',
        hash_checks_performed=False, firmware_rebuilt=False, firmware_written=False,
        hardware_executed=False, installable=False, installation_authorized=False,
        remaining_conditions=[
            'The entire boot prefix remains original. It is resident input here; physical reset is not emulated.',
            'The two code-bank interiors have finite reference and load evidence, not exhaustive ownership or physical execute/cache qualification.',
            'CPU2 pool capacity and prefix instructions remain original; no private pool reservation or cold-clear hook remains.',
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
