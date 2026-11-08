#!/usr/bin/env python3
"""Exercise the target gamma observer and native builder with explicit kind19 job fixtures."""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from ep7_candidate_startup_sim import CALLER, SP, STACK, Machine, Region, require, returned
from ep7_offline_candidate import symbols as read_symbols
from ep7_single_dr_gamma import BASE, GAMMA, gamma_table, target_table_source


BUILDER, HOOK, RESUME = 0x603AE80D, 0x603AE830, 0x603AE835
VENEER, CONTEXT, JOBS, OUTPUTS, CACHE = 0x19110000, 0x19200000, 0x19300000, 0x19400000, 0x19500000
JOB_STRIDE, OUTPUT_STRIDE = 16384, 8192
JOB_BYTES, JOB_LEVEL = 15516, 15512
PREIMAGE = bytes.fromhex('f8923c5c24')
CONFIG, CONFIG_RESUME, CONFIG_CLEANUP = 0x603396DD, 0x60334DF2, 0x60334E57
BYPASS, CONFIG_ENTER, STAGE_RESUME = 0x60334DE2, 0x60334DEC, 0x60354295
OUTPUT_RESUME, OUTPUT_SUCCESS, OUTPUT_FAILURE = 0x603F28B5, 0x603F28B7, 0x603F28BF
APPLIED = 0x80000000
HOOKS = (
    (HOOK, PREIMAGE, 'ep7dr_gamma_bridge'),
    (0x60334DED, bytes.fromhex('cdf048a048'), 'ep7dr_gamma_config_bridge'),
    (0x60334DDA, bytes.fromhex('58c0faec0080'), 'ep7dr_gamma_bypass_bridge'),
    (0x60354290, bytes.fromhex('5c08f0701c'), 'ep7dr_gamma_stage_bridge'),
    (0x603F28B0, bytes.fromhex('f8bc0ca000'), 'ep7dr_gamma_output_bridge'),
)
STOCK = dict(ep7dr_stock_gamma_resume_unresolved=RESUME,
             ep7dr_stock_gamma_config=CONFIG,
             ep7dr_stock_gamma_config_resume=CONFIG_RESUME,
             ep7dr_stock_gamma_config_cleanup=CONFIG_CLEANUP,
             ep7dr_stock_gamma_bypass=BYPASS,
             ep7dr_stock_gamma_config_enter=CONFIG_ENTER,
             ep7dr_stock_gamma_stage_resume=STAGE_RESUME,
             ep7dr_stock_gamma_output_resume=OUTPUT_RESUME)


def compile_fixture(stock, prefix):
    source = ROOT / 'prototypes/ep7_volatile_hl/native_single_dr'
    with tempfile.TemporaryDirectory(prefix='ep7-gamma-target-') as directory:
        temp = Path(directory)
        (temp / 'single_dr_gamma_tables.inc').write_text(target_table_source(stock), encoding='ascii')
        # Isolate the actual gamma observer while the integrated owner is unavailable.
        (temp / 'owner.c').write_text(
            '#include "single_dr.h"\n'
            'static volatile uint32_t *trailer(uint32_t job) {\n'
            '    return (volatile uint32_t *)(uintptr_t)(job + EP7DR_JOB_TRAILER);\n'
            '}\n'
            'uint32_t ep7dr_job_level(uint32_t job) {\n'
            '    return *trailer(job) & 3u;\n'
            '}\n'
            'void ep7dr_job_gamma_applied(uint32_t job) {\n'
            '    *trailer(job) |= EP7DR_JOB_GAMMA_APPLIED;\n'
            '}\n'
            'void ep7dr_job_gamma_clear(uint32_t job) {\n'
            '    *trailer(job) &= ~EP7DR_JOB_GAMMA_APPLIED;\n'
            '}\n'
            'uint32_t ep7dr_job_gamma_missing(uint32_t job) {\n'
            '    return ep7dr_job_level(job) && !(*trailer(job) & EP7DR_JOB_GAMMA_APPLIED);\n'
            '}\n', encoding='ascii')
        flags = ['-std=c11', '-Os', '-Wall', '-Wextra', '-Werror', '-ffreestanding', '-fno-builtin',
                 '-mno-setlb', '-mno-liw', '-I', str(temp), '-I', str(source)]
        subprocess.run([prefix + 'gcc', *flags, '-c', source / 'gamma.c', '-o', temp / 'gamma.o'], check=True)
        subprocess.run([prefix + 'gcc', *flags, '-c', temp / 'owner.c', '-o', temp / 'owner.o'], check=True)
        subprocess.run([prefix + 'as', '-o', temp / 'bridge.o', source / 'gamma.s'], check=True)
        subprocess.run([prefix + 'ld', f'-Ttext={VENEER:#x}', '-e', 'ep7dr_gamma_bridge',
                        *(f'--defsym={key}={address:#x}' for key, address in STOCK.items()),
                        '-o', temp / 'probe.elf', temp / 'bridge.o', temp / 'gamma.o', temp / 'owner.o'], check=True)
        subprocess.run([prefix + 'objcopy', '-O', 'binary', temp / 'probe.elf', temp / 'probe.bin'], check=True)
        return (temp / 'probe.bin').read_bytes(), read_symbols(prefix, temp / 'probe.elf')


def job_fixture(machine, index, key, variant, level):
    job = JOBS + JOB_STRIDE * index
    body = bytearray(JOB_BYTES)
    struct.pack_into('<I', body, 4, 0x603E7B83)
    stages = (0x603687D4, 0x603687ED, 0x6036884D, 0x60356116)
    for slot, callback in enumerate(stages):
        struct.pack_into('<I', body, 10984 + slot * 12, callback)
    struct.pack_into('<HH', body, 11312, 2, len(stages))
    request = job + 11364
    operation = job + 14576
    struct.pack_into('<2I4H', body, 11364, 0x60355FD4, operation, 0, key, 0, 2)
    struct.pack_into('<H', body, 11364 + 28, 0x0105)
    body[11364 + 48] = variant
    struct.pack_into('<3I', body, 14576, job, 0, request)
    struct.pack_into('<I', body, 11364 + 1484, CACHE)
    struct.pack_into('<I', body, JOB_LEVEL, level)
    name = f'job_{index}'
    machine.regions[name] = Region(name, job, bytes(body), 'rw', True)


def run_builder(machine, stock, index, key, expected_stock, level, reuse=False):
    job = JOBS + JOB_STRIDE * index
    output = OUTPUTS + OUTPUT_STRIDE * index
    machine.mutate('context', 4, struct.pack('<III', job + 11364, 0, output))
    machine.mutate('context', 52, struct.pack('<I', key))
    machine.mutate('context', 108, struct.pack('<I', 1))
    result = machine.run(CALLER, CALLER + 7, overrides={'a0': CONTEXT}, full_trace=True, limit=3000)
    returned(result, CALLER + 7)
    trace = {step['pc']: step for step in result['trace']}
    entry, resume = trace[HOOK], trace[RESUME]
    require(entry['d0'] == 1 and resume['a0'] == output, 'selector result or displaced output load changed')
    registers = ('d0', 'd1', 'd2', 'd3', 'a1', 'a2', 'a3', 'sp', 'mdr', 'psw')
    require(all(entry[reg] == resume[reg] for reg in registers), 'observer changed native resume state')
    require((0x603AE995 in trace, 0x603AE9CF in trace) == (not reuse, reuse), 'wrong native cache path')
    require(machine.read(CONTEXT + 108, 4) == struct.pack('<I', int(not reuse)), 'wrong native dirty bit')
    pointers = machine.read(output + 2596, 12)
    lut, green, blue = struct.unpack('<3I', pointers)
    require(lut == green == blue, 'wrong RGB tuple shape')
    require(machine.read(CACHE + 5736, 12) == pointers, 'wrong native cache pointer tuple')
    require(machine.read(lut, GAMMA.size) == gamma_table(stock, expected_stock, level), 'wrong selected RGB data')
    return dict(steps=result['completed'], lut=hex(lut), registers=result['registers'])


def hook_patch(site, before, target):
    return b'\xdc' + struct.pack('<i', target - site) + b'\xcb' * (len(before) - 5)


def inspect_guards(machine):
    _, config_hook, bypass_hook, stage_hook, output_hook = (row[0] for row in HOOKS)
    frame = SP - 256

    def run(site, stop, **registers):
        result = machine.run(site, stop, overrides=dict(sp=frame, **registers), limit=3000)
        require(result['status'] == 'returned' and result['fault'] is None and
                result['registers']['pc'] == stop and result['registers']['sp'] == frame,
                f'guard {site:#x} failed to reach {stop:#x}: {result["fault"]}')
        return result['registers']

    def config_stub(run_gamma):
        # Isolate the actual guard from ISP allocator/MMIO dependencies. The
        # accepted branch invokes the real stock gamma builder in this body.
        setup = b'\xdd' + struct.pack('<i', BUILDER - CONFIG) + b'\xf0\x10' if run_gamma else b''
        machine.mutate('candidate', CONFIG - BASE, setup + b'\x00\xdf\xa0\x48')

    job = JOBS
    request = job + 11364
    machine.mutate('context', 4, struct.pack('<III', request, 0, OUTPUTS))
    machine.mutate('context', 52, struct.pack('<I', 2))
    config_stub(True)
    passed = run(config_hook, CONFIG_RESUME, a0=CONTEXT, a2=CONTEXT, a3=request)
    require(passed['d0'] == 0 and machine.read(job + JOB_LEVEL, 4) == struct.pack('<I', APPLIED | 1),
            'fresh gamma proof failed to release native config')
    config_stub(False)
    rejected = run(config_hook, CONFIG_CLEANUP, a0=CONTEXT, a2=CONTEXT, a3=request)
    require(rejected['d2'] == 0x9E02 and machine.read(job + JOB_LEVEL, 4) == struct.pack('<I', 1),
            'old marker released a missed native gamma configuration')

    off_job = JOBS + 2 * JOB_STRIDE
    off_request = off_job + 11364
    reference = machine.clone()
    reference.mutate('candidate', config_hook - BASE, HOOKS[1][1])
    off = run(config_hook, CONFIG_RESUME, a0=CONTEXT, a2=CONTEXT, a3=off_request)
    reference_result = reference.run(config_hook, CONFIG_RESUME,
                                     overrides=dict(sp=frame, a0=CONTEXT, a2=CONTEXT, a3=off_request))
    require(off['d0'] == 0 and machine.read(off_job + JOB_LEVEL, 4) == bytes(4),
            'OFF was altered by the config guard')
    require(reference_result['status'] == 'returned' and off == reference_result['registers'],
            'OFF changed native config resume registers')
    external = CACHE + 8192
    machine.regions['external_request'] = Region('external_request', external,
                                                 struct.pack('<II', 0x60355FD4, 0), 'r')
    run(config_hook, CONFIG_RESUME, a0=CONTEXT, a2=CONTEXT, a3=external)

    machine.mutate('stack', frame - STACK + 192, struct.pack('<I', 0x8000))
    rejected = run(bypass_hook, CONFIG_CLEANUP, a3=request)
    require(rejected['d2'] == 0x9E02, 'guarded job could enter native bypass')
    run(bypass_hook, BYPASS, a3=off_request)
    machine.mutate('stack', frame - STACK + 192, bytes(4))
    run(bypass_hook, CONFIG_ENTER, a3=request)

    for index, status in ((0, 0x9E02), (1, 0), (2, 0)):
        stage_job = JOBS + index * JOB_STRIDE
        machine.mutate('stack', frame - STACK + 8, struct.pack('<I', stage_job + 11316))
        result = run(stage_hook, STAGE_RESUME, d0=0, d2=stage_job)
        require(result['d0'] == status and machine.read(stage_job + 11316, 2) == struct.pack('<H', status),
                'scheduler guard failed to replay native status store')
    descriptor = CACHE + 12288
    machine.regions['descriptor'] = Region('descriptor', descriptor, bytes(300), 'r')
    machine.mutate('descriptor', 194, struct.pack('<H', 0x2001))
    output_cases = ((0, 0, 0x9E02, OUTPUT_FAILURE),
                    (1, 0, 0, OUTPUT_SUCCESS),
                    (2, 0, 0, OUTPUT_SUCCESS),
                    (0, 0x9E05, 0x9E05, OUTPUT_FAILURE))
    for index, native, status, target in output_cases:
        machine.mutate('descriptor', 36, struct.pack('<I', JOBS + index * JOB_STRIDE))
        machine.mutate('stack', frame - STACK + 12, struct.pack('<H', native))
        result = run(output_hook, target, a3=descriptor)
        require(result['d0'] == status and machine.read(frame + 12, 2) == struct.pack('<H', status),
                'descriptor guard changed the wrong status or branch')
    return dict(config_accepts_fresh_marker=True, config_rejects_stale_marker=True,
                guarded_bypass_rejected=True, scheduler_rejects_missing=True,
                off_passes=True, external_request_untouched=True,
                descriptor_checks_original_success_branch=True,
                config_fixture='stock RGB builder with isolated native setup stub',
                cleanup_fixture='stopped on entry to stock cleanup')


def inspect(stock, image, addresses, engine, *, probe_code=None):
    offset = HOOK - BASE
    for site, before, name in HOOKS:
        start, stop = site - BASE, site - BASE + len(before)
        require(stock[start:stop] == before, f'stock hook preimage changed at {site:#x}')
        require(image[start:stop] == hook_patch(site, before, addresses[name]),
                f'target image is missing {name}')
    machine = Machine(image, engine)
    if probe_code is not None:
        machine.regions['linked_gamma'] = Region('linked_gamma', VENEER, probe_code, 'rx')
    machine.regions['context'] = Region('context', CONTEXT, bytes(128), 'rw', True)
    machine.regions['cache'] = Region('cache', CACHE, bytes(6000), 'rw', True)
    machine.regions['outputs'] = Region('outputs', OUTPUTS, bytes(3 * OUTPUT_STRIDE), 'rw', True)
    call = b'\xdd' + struct.pack('<i', BUILDER - CALLER) + bytes([0xf0, 16])
    machine.regions['caller'] = Region('caller', CALLER, call, 'rx')
    job_fixture(machine, 0, 2, 0, 1)
    job_fixture(machine, 1, 11, 4, 2)
    job_fixture(machine, 2, 11, 4, 0)

    a = run_builder(machine, stock, 0, 2, 0x604EDE78, 1)
    a_again = run_builder(machine, stock, 0, 2, 0x604EDE78, 1, reuse=True)
    a_output = machine.read(OUTPUTS, OUTPUT_STRIDE)
    a_lut = machine.read(int(a['lut'], 16), GAMMA.size)
    b = run_builder(machine, stock, 1, 11, 0x604F3E78, 2)
    reference = machine.clone()
    reference.regions['candidate'] = replace(reference.regions['candidate'],
                                               data=image[:offset] + PREIMAGE + image[offset + 5:])
    off_reference = run_builder(reference, stock, 2, 11, 0x604F3E78, 0)
    off = run_builder(machine, stock, 2, 11, 0x604F3E78, 0)
    require(off['registers'] == off_reference['registers'], 'OFF changed native builder return registers')
    for region in ('context', 'outputs', 'cache'):
        require(machine.regions[region].data == reference.regions[region].data, f'OFF changed {region} bytes')
    require(machine.read(OUTPUTS, OUTPUT_STRIDE) == a_output, 'request A output changed')
    require(machine.read(int(a['lut'], 16), GAMMA.size) == a_lut, 'request A table changed')
    results = dict(A_Natural_200=a, A_cache_reuse=a_again, B_COLOR_400=b, OFF=off, OFF_unhooked=off_reference)
    for row in results.values():
        del row['registers']
    guards = inspect_guards(machine)
    return dict(status='passed', owner='explicit bounded job fixture' if probe_code is not None else 'candidate',
                native_calls=results, job_inputs='kind19-shaped fixtures',
                guards=guards,
                a_unchanged=True, off_stock_equivalent=True, isp_pixels_executed=False,
                hash_checks_performed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stock_main', type=Path)
    parser.add_argument('--engine', required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--tool-prefix', help='cross-link isolated target objects with an explicit owner fixture')
    mode.add_argument('--candidate', type=Path, help='directory containing integrated decoded image and symbols.json')
    args = parser.parse_args()
    stock = args.stock_main.read_bytes()
    if args.candidate:
        symbols = json.loads((args.candidate / 'symbols.json').read_text(encoding='utf-8'))
        image = (args.candidate / 'EP7DR-NONINSTALLABLE.decoded-main.bin').read_bytes()
        addresses = {key: int(row['address'], 16) for key, row in symbols.items()}
        report = inspect(stock, image, addresses, args.engine)
    else:
        code, symbols = compile_fixture(stock, args.tool_prefix)
        addresses = {key: row['address'] for key, row in symbols.items()}
        image = bytearray(stock)
        for site, before, name in HOOKS:
            offset = site - BASE
            image[offset:offset + len(before)] = hook_patch(site, before, addresses[name])
        report = inspect(stock, bytes(image), addresses, args.engine, probe_code=code)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
