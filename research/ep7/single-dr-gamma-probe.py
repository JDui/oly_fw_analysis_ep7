#!/usr/bin/env python3
"""Research-only execution of the E-P7 native gamma cache seam in explicit fixtures."""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from ep7_candidate_startup_sim import CALLER, Machine, Region, require, returned
from ep7_single_dr_gamma import BASE, GAMMA, ROM_POINTERS, gamma_table


BUILDER, HOOK, RESUME = 0x603AE80D, 0x603AE830, 0x603AE835
VENEER, TABLES = 0x19110000, 0x19111000
CONTEXT, REQUESTS, OUTPUTS, CACHE = 0x19200000, 0x19300000, 0x19400000, 0x19500000
REQUEST_STRIDE, OUTPUT_STRIDE, FIXTURE_LEVEL = 2048, 8192, 1884
CACHE_OFFSET = 5736
STOCK_GAMMA = 0x604EDE78


def build_veneer(prefix):
    source = Path(__file__).with_name('single-dr-gamma-bridge.s')
    with tempfile.TemporaryDirectory(prefix='ep7-single-dr-gamma-') as tmp:
        obj, elf, raw = (Path(tmp) / name for name in ('bridge.o', 'bridge.elf', 'bridge.bin'))
        subprocess.run([prefix + 'as', '-o', obj, source], check=True)
        subprocess.run([prefix + 'ld', f'-Ttext={VENEER:#x}', '-e', 'single_dr_gamma_bridge',
                        f'--defsym=fixture_gamma_resume={RESUME:#x}',
                        f'--defsym=fixture_gamma_luts={TABLES:#x}', '-o', elf, obj], check=True)
        subprocess.run([prefix + 'objcopy', '-O', 'binary', '-j', '.text', elf, raw], check=True)
        code = raw.read_bytes()
    require(0 < len(code) < TABLES - VENEER, 'unexpected fixture veneer size')
    return code


def run_builder(machine, index, expected, reuse):
    request = REQUESTS + REQUEST_STRIDE * index
    output = OUTPUTS + OUTPUT_STRIDE * index
    machine.mutate('context', 4, struct.pack('<III', request, 0, output))
    machine.mutate('context', 108, struct.pack('<I', 1))
    result = machine.run(CALLER, CALLER + 7, overrides={'a0': CONTEXT}, full_trace=True, limit=2000)
    returned(result, CALLER + 7)
    trace = {step['pc']: step for step in result['trace']}
    entry, resume = trace[HOOK], trace[RESUME]
    require(entry['d0'] == 1 and resume['a0'] == output, 'selector result or displaced output load changed')
    require(all(entry[reg] == resume[reg] for reg in
                ('d0', 'd1', 'd2', 'd3', 'a1', 'a2', 'a3', 'sp', 'mdr', 'psw')),
            'gamma veneer changed the native resume state')
    require((0x603AE995 in trace, 0x603AE9CF in trace) == (not reuse, reuse), 'wrong native cache path')
    require(machine.read(CONTEXT + 108, 4) == struct.pack('<I', int(not reuse)), 'wrong native dirty bit')
    pointers = struct.pack('<3I', expected, expected, expected)
    require(machine.read(output + 2596, 12) == pointers, 'wrong output pointer tuple')
    require(machine.read(CACHE + CACHE_OFFSET, 12) == pointers, 'wrong native cache pointer tuple')
    return result


def inspect(stock, engine, veneer):
    offset = HOOK - BASE
    require(stock[offset:offset + 5] == bytes.fromhex('f8923c5c24'), 'stock gamma hook preimage changed')
    jump = b'\xdc' + struct.pack('<i', VENEER - HOOK)
    patched = stock[:offset] + jump + stock[offset + len(jump):]
    machine = Machine(patched, engine)
    lut_data = b''.join(gamma_table(stock, address, level)
                        for address in dict.fromkeys(ROM_POINTERS) for level in (1, 2))
    machine.regions['veneer'] = Region('veneer', VENEER, veneer, 'rx')
    machine.regions['luts'] = Region('luts', TABLES, lut_data, 'r')
    call = b'\xdd' + struct.pack('<i', BUILDER - CALLER) + bytes([0xf0, 16])
    machine.regions['caller'] = Region('caller', CALLER, call, 'rx')
    context = bytearray(128)
    struct.pack_into('<I', context, 52, 2)
    machine.regions['context'] = Region('context', CONTEXT, bytes(context), 'rw', True)
    machine.regions['cache'] = Region('cache', CACHE, bytes(6000), 'rw', True)
    machine.regions['outputs'] = Region('outputs', OUTPUTS, bytes(3 * OUTPUT_STRIDE), 'rw', True)
    for index, level in enumerate((1, 2, 0)):
        address = REQUESTS + REQUEST_STRIDE * index
        request = bytearray(FIXTURE_LEVEL + 1)
        struct.pack_into('<3H', request, 10, 2, 0x100d, 2)
        struct.pack_into('<H', request, 28, 0x0105)
        struct.pack_into('<I', request, 1484, CACHE)
        request[FIXTURE_LEVEL] = level
        name = f'request_{index}'
        machine.regions[name] = Region(name, address, bytes(request), 'r')

    a = run_builder(machine, 0, TABLES, reuse=False)
    same_a = run_builder(machine, 0, TABLES, reuse=True)
    a_output = machine.read(OUTPUTS, OUTPUT_STRIDE)
    a_lut = machine.read(TABLES, GAMMA.size)
    b = run_builder(machine, 1, TABLES + GAMMA.size, reuse=False)

    stock_reference = machine.clone()
    stock_reference.regions['candidate'] = replace(stock_reference.regions['candidate'], data=stock)
    off_stock = run_builder(stock_reference, 2, STOCK_GAMMA, reuse=False)
    off = run_builder(machine, 2, STOCK_GAMMA, reuse=False)
    for region in ('context', 'outputs', 'cache'):
        require(machine.regions[region].data == stock_reference.regions[region].data,
                f'OFF differs from the unmodified builder in {region}')
    require(off['registers'] == off_stock['registers'], 'OFF changed the native return registers')
    require(machine.read(OUTPUTS, OUTPUT_STRIDE) == a_output, 'request A output changed after B or OFF')
    require(machine.read(TABLES, GAMMA.size) == a_lut, 'request A table changed after B or OFF')
    return dict(status='research_only', veneer_bytes=len(veneer), hash_checks_performed=False,
                native_calls=[dict(request=name, steps=result['completed'], cache=cache)
                              for name, result, cache in (
                                  ('A_HDR200', a, 'rebuild'), ('A_HDR200_again', same_a, 'reuse'),
                                  ('B_HDR400', b, 'rebuild'), ('OFF', off, 'rebuild'),
                                  ('OFF_stock_reference', off_stock, 'rebuild'))],
                off_matches_stock=True, a_immutable_through_b_and_off=True,
                capture_preview_transport_qualified=False, isp_pixels_executed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stock_main', type=Path)
    parser.add_argument('--tool-prefix', required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.stock_main.read_bytes(), args.engine, build_veneer(args.tool_prefix)), indent=2))


if __name__ == '__main__':
    main()
