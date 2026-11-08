#!/usr/bin/env python3
"""Replay the linked DR owners and native gain/gamma windows in one strict machine."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import runpy
import struct
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'tools'))
from ep7_candidate_startup_sim import CALLER, Machine, Region, SP, STACK, require, returned
from ep7_sim_probe import run
from ep7_single_dr_gamma import BASE

EXPOSURE = runpy.run_path(str(HERE / 'single-dr-exposure-bridge-probe.py'))
GAMMA = runpy.run_path(str(HERE / 'single-dr-gamma-target-probe.py'))
SERIAL = runpy.run_path(str(HERE / 'single-dr-exposure-probe.py'))['replay_tg_gain']
record, branch, patch = (EXPOSURE[n] for n in ('record', 'branch', 'patch'))
LOWER, WORK, CONTEXT, PACKET, COPY = (EXPOSURE[n] for n in ('LOWER', 'WORK', 'CONTEXT', 'PACKET', 'COPY'))
CONTROLLER, CURRENT, ENGINE, MODE = 0x6223D134, 0x6223D414, 0x6223D8A0, 0x6223D488
REGISTRY, METADATA = 0x6223D178, 0x6223E450
COMMAND, NODE, DESCRIPTOR, PROPS = 0x19201000, 0x19208000, 0x1920A000, 0x19600000
CAPTURE, CLONE, SHELL, CAL = 0xAF6037C0, 0xAF900000, 0x19180000, 0x62270000
DESTROYED = 0x1920B000
ACTIVE = 0x6250BA00
DEFERRED = 0xA2715C8C
ISO = 2048


def fixture_code(prefix):
    source = f'''
.text
.global typed,public,still,selected,convert,pointer,copy,release,destroy,enter_calc,enter_load
typed:
 cmp 0,a0
 beq .Lfixture_property
 mov d1,d3
 mov d0,d2
 jmp fixture_typed_explicit
.Lfixture_property:
 asl2 d0
 mov {PROPS:#x},a0
 mov (d0,a0),d0
 ret [d2,d3],12
public:
 mov ({PROPS:#x}),d0
 ret [],4
still:
 clr d0
 ret [d2,d3,a2],32
selected:
 ret [d2,d3,a2,a3],64
convert:
 clr d0
 ret [d2,d3,a2,a3],72
pointer:
 mov {CAPTURE:#x},d0
 ret [d2,d3,a2,a3],44
copy:
 ret [d2,d3,a2,a3],28
release:
 ret [],4
destroy:
 mov d0,({DESTROYED:#x})
 clr d0
 ret [d2,a2],12
enter_calc:
 mov {WORK:#x},a1
 jmp fixture_calculate
enter_load:
 mov a0,a3
 mov a1,a2
 jmp fixture_load_nominal
'''
    with tempfile.TemporaryDirectory(prefix='ep7dr-owner-fixture-') as temp:
        asm, obj, elf, raw = (Path(temp) / name for name in ('shell.s', 'shell.o', 'shell.elf', 'shell.bin'))
        asm.write_text(source, encoding='ascii')
        subprocess.run([prefix + 'as', '-o', obj, asm], check=True)
        subprocess.run([prefix + 'ld', f'-Ttext={SHELL:#x}', '-e', 'typed',
                        '--defsym=fixture_calculate=0x6012e38e', '--defsym=fixture_load_nominal=0x6012e698',
                        '--defsym=fixture_typed_explicit=0x6005e987',
                        '-o', elf, obj], check=True)
        subprocess.run([prefix + 'objcopy', '-O', 'binary', '-j', '.text', elf, raw], check=True)
        syms = {name: int(address, 16) for address, _, name in
                map(str.split, subprocess.check_output([prefix + 'nm', '-g', elf], text=True).splitlines())}
        return raw.read_bytes(), syms


def memory(machine, name, address, data, permissions='rw'):
    machine.regions[name] = Region(name, address, data, permissions, 'w' in permissions)


def put(machine, region, address, fmt, value):
    machine.mutate(region, address - machine.regions[region].address, struct.pack(fmt, value))


def window(machine, address, end, **registers):
    result = machine.run(address, end, overrides=registers, limit=4000)
    returned(result, end)
    return result['registers']


def call(machine, target, mask=0, frame=0, **registers):
    memory(machine, 'caller', CALLER, branch(0xdd, CALLER, target) + bytes((mask, frame)), 'rx')
    return window(machine, CALLER, CALLER + 7, **registers)


def setup(image, engine, code, fixture):
    image = bytearray(image)
    # Only native service bodies are replaced. Installed call sites, bridges
    # and owner code are unchanged. Real nested gain and gamma windows run.
    for address, name in [(0x6005E971, 'typed'), (0x602AFA81, 'public'),
                          (0x601E77D8, 'still'), (0x602A91EE, 'selected'),
                          (0x603E62D1, 'convert'), (0x603DBA87, 'pointer'),
                          (0x603DB89E, 'release'), (0x60353CB7, 'destroy'),
                          (0x6012E2FC, 'enter_calc')]:
        image[address - BASE:address - BASE + 5] = branch(0xdc, address, fixture[name])
    patch(image, 0x6012E654, '93f8231496', branch(0xdc, 0x6012E654, fixture['enter_load']))
    patch(image, 0x6012E393, 'cc9b02f0', bytes.fromhex('00dff038'))
    patch(image, 0x6012E76D, '9ccd29', bytes.fromhex('dfb010'))
    machine = Machine(bytes(image), engine)
    active_data = bytes(image[0x600b90cc - BASE:0x600b90cc - BASE + 3560 * 4])
    del machine.regions['stack_after']
    memory(machine, 'stack', STACK, bytes(4096))
    memory(machine, 'shell', SHELL, code, 'rx')
    memory(machine, 'memcpy', 0x47001052, branch(0xdc, 0x47001052, fixture['copy']), 'rx')
    for name, address, data in (
        ('controller', CONTROLLER, bytes(0x1500)), ('settings', 0x62253594, struct.pack('<I', ACTIVE)),
        ('active', ACTIVE, active_data), ('readonly_bank', 0xA2711A88, struct.pack('<I', 0x60078E2C)),
        ('typed_deferred', DEFERRED, bytes(4)),
        ('mode_busy', 0x62257B04, bytes(4)), ('bank_busy', 0x622484FA, bytes(1)),
        ('alternate_busy', 0x61FA7538, bytes(4)), ('properties', PROPS, bytes(0x40000)),
        ('command', COMMAND, record(64, (0, '<I', 1))), ('node', NODE, record(56, (0, '<I', 1))),
        ('lower', LOWER, bytes(168)), ('work', WORK, bytes(152)), ('copy', COPY, bytes(96)),
        ('lower_context', CONTEXT, record(64, (0, '<I', PACKET), (4, '<I', LOWER), (12, '<I', COPY))),
        ('packet', PACKET, record(36, (0, '<H', 8), (2, '<H', 7), (12, '<I', ENGINE + 4))),
        ('gain_roots', 0x621F3FF4, struct.pack('<II', CAL, 0x6009163C)),
        ('calibration', CAL, struct.pack('<6h', -1541, 0, 1541, 3082, 4623, 6165)),
        ('descriptor', DESCRIPTOR, bytes(300)), ('clone_owner', 0x622933DC, struct.pack('<I', CLONE)),
        ('capture', CAPTURE, bytes(41984)), ('destroyed', DESTROYED, bytes(4)),
    ):
        memory(machine, name, address, data)
    machine.regions['active_alias'] = Region('active_alias', ACTIVE + 0x40000000,
                                             active_data, 'rw', True, alias_of='active')
    for i in range(4):
        put(machine, 'controller', METADATA + 96 * i + 93, '<B', i)
    for address, fmt, value in ((CURRENT, '<I', COMMAND), (ENGINE, '<H', 7),
                                (ENGINE + 12, '<I', MODE), (MODE, '<H', 10)):
        put(machine, 'controller', address, fmt, value)
    put(machine, 'properties', PROPS + 4 * 0x810a, '<I', ISO)
    put(machine, 'properties', PROPS + 4 * 0x8141, '<I', 1)
    return machine


def submit(machine, syms, mode, level, nominal=ISO):
    put(machine, 'properties', PROPS + 4 * 0x810a, '<I', nominal)
    put(machine, 'properties', PROPS, '<I', mode)
    put(machine, 'properties', PROPS + 4 * 0x9481, '<I', 2 if mode == 1 else 11)
    put(machine, 'properties', PROPS + 4 * 0xf6b1, '<I', 1)
    require(call(machine, syms['_ep7dr_stage_level'], d0=mode, d1=level)['d0'] == 1,
            'setter rejected supported mode')
    window(machine, 0x6029BE17, 0x6029BE1E)
    for address, fmt, value in ((REGISTRY + 24, '<H', 4), (REGISTRY + 36, '<I', CAPTURE),
                                (0x6223e5d0, '<B', 0), (METADATA + 92, '<B', 0),
                                (ENGINE + 4, '<I', METADATA)):
        put(machine, 'controller', address, fmt, value)
    require(call(machine, 0x602A7556, 0x20, 20)['a0'] == METADATA, 'stock metadata claim failed')
    put(machine, 'command', COMMAND + 60, '<I', METADATA)
    exposure = record(92, (0, '<I', 0x100), (4, '<H', 1), (6, '<h', 2304),
                      (8, '<h', nominal), (10, '<h', 768))
    machine.mutate('controller', METADATA - CONTROLLER, exposure)
    machine.mutate('copy', 0, exposure)
    window(machine, 0x6029D68E, 0x6029D695, a0=ENGINE)
    return call(machine, syms['_ep7dr_plan_for_metadata'], d0=METADATA)['d0']


def gain(machine, nominal=ISO):
    machine.mutate('lower', 0, record(168, (4, '<I', 10), (20, '<I', COPY)))
    machine.mutate('work', 0, record(152, (0, '<I', EXPOSURE['STILL'])))
    for offset, address in [(28, 0x6013CCE5), (36, 0x601420AD), (72, 0x6014E5F8),
                            (108, 0x6014E783), (124, 0x6014DE09)]:
        put(machine, 'stack', SP + offset, '<I', address)
    registers = window(machine, 0x601429CC, 0x60142A11, a0=LOWER, a3=CONTEXT, d3=CONTEXT + 12)
    require(registers['d0'] == 0, 'stock exposure calculator failed')
    require(machine.read(METADATA + 48, 6) == struct.pack('<3h', 2304, nominal, 768),
            'work gain changed native Tv/Sv/Av echo')
    return struct.unpack('<5I', machine.read(LOWER + 44, 20))


def serial_gain(machine):
    image = machine.regions['candidate']
    stack = Region('stack', STACK, bytes(4096), 'rw')

    def execute(start, stop, registers, regions):
        result = run(machine.engine, [image, stack, *regions],
                     dict(pc=start, sp=SP, **registers), stop=stop, limit=700)
        returned(result, stop)
        return result

    return SERIAL(execute, machine.read(LOWER, 168))[0]


def convert(machine, index, key, variant, source, failure_path=False):
    job = GAMMA['JOBS'] + GAMMA['JOB_STRIDE'] * index
    GAMMA['job_fixture'](machine, index, key, variant, 0)
    name = f'job_{index}'
    machine.regions[name] = replace(machine.regions[name], permissions='rw', capture=True)
    put(machine, name, job + 11312, '<H', 0)
    machine.mutate('descriptor', 0, record(300, (28, '<I', source), (36, '<I', job),
                                           (194, '<H', 0x2001)))
    stop = 0x603F28D4 if failure_path else 0x603F2857
    result = machine.run(0x603F2850, stop, overrides={'a0': DESCRIPTOR, 'a3': DESCRIPTOR},
                         limit=4000, full_trace=failure_path)
    returned(result, stop)
    if failure_path:
        trace = {step['pc'] for step in result['trace']}
        require(0x603F28C0 in trace and 0x603E6CCE in trace and
                not {0x603F2890, 0x603F28B8} & trace,
                'native failure did not skip development and success postprocess')
        require(machine.read(DESTROYED, 4) == struct.pack('<I', job) and
                machine.read(DESCRIPTOR + 192, 2) == struct.pack('<H', 0x9e02),
                'native cleanup did not retire the job and report the exact error')
    put(machine, name, job + 11312, '<H', 2)
    return result['registers']['d0'] & 0xffff, struct.unpack('<I', machine.read(job + 15512, 4))[0]


def select(machine):
    window(machine, 0x602A283C, 0x602A2841, d2=NODE, a2=COMMAND)


def inspect(directory, baseline, engine, prefix):
    image = (directory / 'EP7DR-NONINSTALLABLE.decoded-main.bin').read_bytes()
    stock = baseline.read_bytes()
    syms = {name: int(row['address'], 16) for name, row in
            json.loads((directory / 'symbols.json').read_text(encoding='utf-8')).items()}
    machine = setup(image, engine, *fixture_code(prefix))
    h1 = ACTIVE + 4 * (1769 + 927)
    h1_original = machine.read(h1, 4)
    require(call(machine, syms['_ep7dr_selected_level'], d0=1)['d0'] == 0,
            'old ACTIVE defaults must decode OFF')
    ticket_a = submit(machine, syms, 1, 1)
    require(ticket_a & 3 == 1, 'A did not freeze Natural/200 at submission')
    require(machine.read(ACTIVE + 4 * (1769 + 894), 4) == struct.pack('<I', 0x445201fe),
            'Natural level did not reach its native ACTIVE cell')
    call(machine, syms['_ep7dr_stage_level'], d0=1, d1=2)
    put(machine, 'properties', PROPS + 4 * 0x8141, '<I', 4)
    frozen = window(machine, 0x602A7EF0, 0x602A7EF7, d0=0x8141, d3=CAPTURE, a0=0, d1=0)
    require(frozen['d0'] == 1, 'capture could switch to RAW after submission')
    put(machine, 'properties', PROPS + 4 * 0x8141, '<I', 1)
    a_gain = gain(machine)
    require(a_gain[:2] == (65536, 1) and a_gain[-2:] == (3070, 3070), 'wrong A gain')
    a_serial = serial_gain(machine)
    window(machine, 0x6029E966, 0x6029E96D, a1=COMMAND)
    window(machine, 0x603EDBCE, 0x603EDBD5, a0=CLONE, a1=CAPTURE, d0=27332)
    require(call(machine, syms['_ep7dr_stage_level'], d0=1, d1=0)['d0'] == 1,
            'ordinary scope reset failed')
    window(machine, 0x6029BE5D, 0x6029BE64, a2=REGISTRY + 24)

    ticket_b = submit(machine, syms, 54, 2)
    require(ticket_b & 3 == 2 and ticket_a != ticket_b, 'B reused A ticket')
    require(machine.read(ACTIVE + 4 * (1769 + 963), 4) == struct.pack('<I', 0x445202fd) and
            machine.read(ACTIVE + 4 * (1769 + 894), 4) == bytes(4),
            'COLOR changed the separate ordinary scope')
    b_gain = gain(machine)
    require(b_gain[:2] == (65536, 1) and b_gain[-2:] == (2046, 2046), 'wrong B gain')
    b_serial = serial_gain(machine)
    select(machine)
    require(convert(machine, 0, 2, 0, CLONE) == (0, 1), 'A lost its level after mode and pool reuse')
    require(convert(machine, 1, 11, 4, CAPTURE) == (0, 2), 'B did not publish')
    window(machine, 0x6029BE5D, 0x6029BE64, a2=REGISTRY + 24)

    require(submit(machine, syms, 54, 0) == 0, 'OFF has a ticket')
    off_gain = gain(machine)
    require(off_gain[:2] == (65536, 1) and off_gain[-2:] == (3583, 3583), 'OFF changed gain')
    off_serial = serial_gain(machine)
    require(convert(machine, 2, 11, 4, CAPTURE) == (0, 0), 'OFF inherited a previous capture')
    memory(machine, 'context', GAMMA['CONTEXT'], bytes(128))
    memory(machine, 'cache', GAMMA['CACHE'], bytes(6000))
    memory(machine, 'outputs', GAMMA['OUTPUTS'], bytes(3 * GAMMA['OUTPUT_STRIDE']))
    memory(machine, 'caller', CALLER, branch(0xdd, CALLER, GAMMA['BUILDER']) + bytes((0xf0, 16)), 'rx')
    a = GAMMA['run_builder'](machine, stock, 0, 2, 0x604EDE78, 1)
    b = GAMMA['run_builder'](machine, stock, 1, 11, 0x604F3E78, 2)
    off = GAMMA['run_builder'](machine, stock, 2, 11, 0x604F3E78, 0)

    require(submit(machine, syms, 1, 1) & 3 == 1, 'fault case did not arm')
    require(gain(machine)[-2:] == (3070, 3070), 'fault case did not lower gain')
    # Deliberately skip selected-event binding after the gain was accepted.
    failure, trailer = convert(machine, 2, 2, 0, CAPTURE, failure_path=True)
    require(failure == 0x9e02 and trailer == 0x40000001,
            'lost selected binding became a successful OFF development')
    require(machine.read(h1, 4) == h1_original, 'DR changed an original 015 H/L setting cell')
    # Fractional menu stops need actual stock gain/serial execution, not just
    # a UI eligibility flag. Compare each with its own OFF reference.
    fractional = []
    for nominal in (1877, 1962):
        submit(machine, syms, 1, 0, nominal)
        reference = gain(machine, nominal)
        reference_serial = serial_gain(machine)
        require(submit(machine, syms, 1, 1, nominal) & 3 == 1,
                'fractional ISO did not acquire a capture ticket')
        actual = gain(machine, nominal)
        actual_serial = serial_gain(machine)
        require(actual[:3] == reference[:3] and actual[0] == 65536 and
                actual[1] == 1 and actual[-2] == actual[-1] and
                abs((4095 - actual[-1]) - 2 * (4095 - reference[-1])) <= 8 and
                actual[-1] < reference[-1] and actual_serial != reference_serial,
                'fractional ISO did not halve the analog gain in the native serial payload')
        window(machine, 0x6029E966, 0x6029E96D, a1=COMMAND)
        require(convert(machine, 2, 2, 0, CAPTURE) == (0, 1),
                'fractional ISO lost its compensation binding')
        memory(machine, 'caller', CALLER, branch(0xdd, CALLER, GAMMA['BUILDER']) + bytes((0xf0, 16)), 'rx')
        mapped = GAMMA['run_builder'](machine, stock, 2, 2, 0x604EDE78, 1,
                                      reuse=bool(fractional))
        fractional.append(dict(nominal_sv=nominal, stock_gain=reference[-2:],
                               hdr200_gain=actual[-2:], serial=actual_serial, lut=mapped['lut']))
        require(submit(machine, syms, 1, 2, nominal) == 0,
                'HDR400 admitted a fractional ISO below its floor')
        require(gain(machine, nominal) == reference,
                'unavailable HDR400 changed the native exposure')
    return dict(status='passed', A=dict(ticket=hex(ticket_a), gain=a_gain[-2:], lut=a['lut'], serial=a_serial),
                B=dict(ticket=hex(ticket_b), gain=b_gain[-2:], lut=b['lut'], serial=b_serial),
                off=dict(gain=off_gain[-2:], lut=off['lut'], serial=off_serial),
                frozen_format=dict(live=4, capture=frozen['d0']),
                fractional_iso_hdr200=fractional,
                native_active_scopes=True, legacy_active_defaults_off=True, native_h1_cell_unchanged=True,
                lost_selected_binding=dict(error=hex(failure), trailer=hex(trailer),
                                           native_cleanup=True, success_path_skipped=True),
                boundaries=['Stock service shells cover RTOS dispatch, property/allocator responses,',
                            'selected metadata body, clone memcpy, converter and allocator destruction.',
                            'Job geometry and stage ownership are explicit native-shaped inputs.',
                            'The overlay executes the actual bridges, owners, gain and gamma math.'],
                isp_pixels_executed=False, hash_checks_performed=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--tool-prefix', required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.candidate, args.baseline, args.engine, args.tool_prefix), indent=2))
