#!/usr/bin/env python3
"""Strict replay of the proposed exposure bridges and stock gain arithmetic."""

import argparse
from pathlib import Path
import struct
import subprocess
import tempfile

from ep7_sim_probe import capture, run
from penf_emulator import Region


BASE = 0x60020020
VENEER = 0x19100000
STACK = 0x19200000
COMMAND = 0x19201000
LOWER = 0x19202000
WORK = 0x19203000
CONTEXT = 0x19204000
PACKET = 0x19205000
COPY = 0x19206000
GATE = 0x19207000
CALIBRATION = 0x62270000
ENGINE = 0x6223D8A0
METADATA = 0x6223E450
STILL = 0x601CA690
CALL = 0x601429CC
STOP = 0x60142A11
GAIN = 0x6012E6EF
FREEZE = 0x6029D68E

SOURCE = Path(__file__).resolve().parents[2] / 'prototypes' / 'ep7_volatile_hl' / 'native_single_dr'
STOCK = {'ep7dr_stock_engine_dispatch': 0x601E77D8, 'ep7dr_stock_gain_table': 0x6012F788,
         'ep7dr_stock_gain_resume': 0x6012E6F5, 'ep7dr_stock_exp2': 0x6011C5E9,
         'fixture_type0_call': 0x6012E38E, 'fixture_load_nominal': 0x6012E698}

# Test-only outer shell. It skips native allocation and unrelated timing
# preparation. Both original nested CALL frames and the full gain slice run.
FIXTURE = f'''
.text
.global ep7dr_stock_exposure_calculate,fixture_enter_e654
ep7dr_stock_exposure_calculate:
 mov {WORK:#x},a1
 jmp fixture_type0_call
fixture_enter_e654:
 mov a0,a3
 mov a1,a2
 jmp fixture_load_nominal

.global _ep7dr_freeze_plan,_ep7dr_plan_for_metadata,_ep7dr_record_applied,_ep7dr_reject_plan
_ep7dr_freeze_plan:
 mov d0,({GATE + 16:#x})
 mov d1,({GATE + 20:#x})
 clr d0
 ret [],0
_ep7dr_plan_for_metadata:
 cmp {METADATA:#x},d0
 bne .Lreject
 mov ({GATE:#x}),d0
 ret [],0
_ep7dr_record_applied:
 cmp {METADATA:#x},d0
 bne .Lreject
 mov ({GATE + 4:#x}),d0
 cmp 1,d0
 bne .Lreject
 mov d1,({GATE + 8:#x})
 ret [],0
.Lreject:
 clr d0
 ret [],0
_ep7dr_reject_plan:
 mov d1,({GATE + 12:#x})
 ret [],0
'''


def compile_bridge(prefix):
    with tempfile.TemporaryDirectory(prefix='ep7-exposure-bridge-') as tmp:
        tmp = Path(tmp)
        fixture = tmp / 'fixture.s'
        fixture.write_text(FIXTURE)
        code, bridge, shell, elf, binary = [tmp / name for name in ('code.o', 'bridge.o', 'shell.o', 'test.elf', 'test.bin')]
        subprocess.run([prefix + 'gcc', '-O2', '-std=c11', '-ffreestanding', '-fno-builtin', '-mno-setlb', '-mno-liw',
                        '-Wall', '-Wextra', '-Werror', '-c', SOURCE / 'exposure.c', '-o', code], check=True)
        subprocess.run([prefix + 'as', '-o', bridge, SOURCE / 'exposure.s'], check=True)
        subprocess.run([prefix + 'as', '-o', shell, fixture], check=True)
        args = [f'--defsym={name}={address:#x}' for name, address in STOCK.items()]
        subprocess.run([prefix + 'ld', f'-Ttext={VENEER:#x}', '-e', 'ep7dr_exposure_scope_bridge', *args,
                        '-o', elf, code, bridge, shell], check=True)
        subprocess.run([prefix + 'objcopy', '-O', 'binary', '-j', '.text', elf, binary], check=True)
        symbols = {}
        for row in subprocess.check_output([prefix + 'nm', elf], text=True).splitlines():
            address, _, name = row.split()
            symbols[name] = int(address, 16)
        return binary.read_bytes(), symbols


def record(size, *fields):
    result = bytearray(size)
    for offset, fmt, value in fields:
        struct.pack_into(fmt, result, offset, value)
    return bytes(result)


def branch(op, source, destination):
    return bytes([op]) + struct.pack('<i', destination - source)


def patch(image, address, expected, replacement):
    offset = address - BASE
    witness = bytes.fromhex(expected)
    if image[offset:offset + len(witness)] != witness:
        raise ValueError(f'{address:08x}: original bytes differ')
    image[offset:offset + len(replacement)] = replacement


def inspect(image, engine, veneer, symbols):
    candidate = bytearray(image)
    patch(candidate, CALL, 'dd30b9fefff038', branch(0xDD, CALL, symbols['ep7dr_exposure_scope_bridge']) + b'\xf0\x38')
    patch(candidate, GAIN, '9ccd9810300c', branch(0xDC, GAIN, symbols['ep7dr_exposure_gain_bridge']) + b'\x00')
    patch(candidate, FREEZE, 'dd4aa1f4ffe020', branch(0xDD, FREEZE, symbols['ep7dr_exposure_freeze_bridge']) + b'\xe0\x20')
    patch(candidate, 0x6012E654, '93f8231496', branch(0xDC, 0x6012E654, symbols['fixture_enter_e654']))
    patch(candidate, 0x6012E393, 'cc9b02f0', bytes.fromhex('00dff038'))
    patch(candidate, 0x6012E76D, '9ccd29', bytes.fromhex('dfb010'))
    original_gain = bytearray(candidate)
    original_gain[GAIN - BASE:GAIN - BASE + 6] = image[GAIN - BASE:GAIN - BASE + 6]
    original_gain[CALL - BASE:CALL - BASE + 7] = (
        branch(0xDD, CALL, symbols['ep7dr_stock_exposure_calculate']) + b'\xf0\x38')

    stack = STACK + 768
    freeze_regs = dict(pc=FREEZE, sp=stack, a0=ENGINE, a1=COMMAND, d0=0x12345678, d1=0x0ABCDEF0)
    freeze = run(engine, [
        Region('main', BASE, bytes(candidate), 'rx'),
        Region('bridge', VENEER, veneer, 'rx'),
        Region('stack', STACK, bytes(1024), 'rw'),
        Region('current', 0x6223D414, struct.pack('<I', COMMAND), 'r'),
        Region('gate', GATE, bytes(24), 'rw', True),
    ], freeze_regs, stop=STOCK['ep7dr_stock_engine_dispatch'], limit=64)
    if (freeze['status'] != 'returned' or
            struct.unpack_from('<II', capture(freeze, 'gate'), 16) != (COMMAND, ENGINE) or
            any(freeze['registers'][name] != value for name, value in freeze_regs.items()
                if name not in ('pc', 'sp')) or freeze['registers']['sp'] != stack - 32):
        raise RuntimeError(f'early freeze changed dispatch: {freeze["status"]}, {freeze["registers"]}')
    print('early freeze: active command and engine forwarded, stock dispatch arguments preserved')

    def shot(level, accepted=True, fixed_sv=2048, origin=ENGINE + 4, corrupt_cal=False,
             stock_gain=False, outer_return=0x6014DE09, native_adjustment=0):
        exposure = record(96, (0, '<I', 0x100), (4, '<H', 1), (6, '<h', 2304), (8, '<h', fixed_sv),
                          (10, '<h', 768), (92, '<B', 1))
        coefficients = (-1541, 0, 1541, 3082, 4623, 6165)
        if corrupt_cal:
            coefficients = (-1541, 0, 1500, 3082, 4623, 6165)
        # Seed the outer native caller records omitted by the bounded replay.
        # CALL at 601429cc provides the inner return PC itself.
        outer = ((28, 0x6013CCE5), (36, 0x601420AD), (72, 0x6014E5F8),
                 (108, 0x6014E783), (124, outer_return))
        regions = [
            Region('main', BASE, bytes(original_gain if stock_gain else candidate), 'rx'),
            Region('bridge', VENEER, veneer, 'rx'),
            Region('stack', STACK, record(1024, *((768 + off, '<I', pc) for off, pc in outer)), 'rw'),
            Region('command', COMMAND, record(64, (60, '<I', METADATA)), 'r'),
            Region('lower', LOWER, record(168, (4, '<I', 10), (20, '<I', COPY)), 'rw', True),
            Region('work', WORK, record(152, (0, '<I', STILL), (140, '<h', native_adjustment)), 'rw'),
            Region('context', CONTEXT, record(64, (0, '<I', PACKET), (4, '<I', LOWER), (12, '<I', COPY)), 'r'),
            Region('packet', PACKET, record(36, (0, '<H', 8), (2, '<H', 7), (12, '<I', origin)), 'r'),
            Region('copy', COPY, exposure[:92], 'rw', True),
            Region('metadata', METADATA, exposure, 'rw', True),
            Region('engine', ENGINE, record(16, (4, '<I', METADATA), (8, '<I', METADATA)), 'r'),
            Region('current', 0x6223D414, struct.pack('<I', COMMAND), 'r'),
            Region('gain_roots', 0x621F3FF4, struct.pack('<II', CALIBRATION, 0x6009163C), 'r'),
            Region('table', CALIBRATION, struct.pack('<6h', *coefficients), 'r'),
            Region('gate', GATE, struct.pack('<IIII', 0x100 + level if level else 0, accepted, 0, 0), 'rw', True),
        ]
        result = run(engine, regions, dict(pc=CALL, sp=stack, a0=LOWER, a3=CONTEXT, d3=CONTEXT + 12),
                     stop=STOP, limit=2200)
        if (result['status'] != 'returned' or result['registers']['sp'] != stack
                or result['registers']['d0'] != 0):
            raise RuntimeError(f'{level=}: {result["status"]}, {result["fault"]}, {result["registers"]}')
        for output in ('copy', 'metadata'):
            if struct.unpack_from('<3h', capture(result, output), 48) != (2304, fixed_sv, 768):
                raise RuntimeError(f'the native Tv/Sv/Av echo changed in {output}')
        controls = struct.unpack_from('<5I', capture(result, 'lower'), 44)
        published, rejected = struct.unpack_from('<II', capture(result, 'gate'), 8)
        return controls, published, rejected, result['completed']

    reference = shot(0, stock_gain=True)[0]
    corrupt_reference = shot(0, stock_gain=True, corrupt_cal=True)[0]
    low_reference = shot(0, stock_gain=True, fixed_sv=1792)[0]
    adjusted_reference = shot(0, stock_gain=True, native_adjustment=1)[0]
    for label, result, expected, ticket, reject in (
        ('OFF', shot(0), reference, 0, 0),
        ('HDR200', shot(1), (65536, 1, reference[2], 3070, 3070), 0x101, 0),
        ('HDR400', shot(2), (65536, 1, reference[2], 2046, 2046), 0x102, 0),
        ('publication rejected', shot(2, accepted=False), reference, 0, 0x102),
        ('foreign exposure owner', shot(2, origin=ENGINE + 8), reference, 0, 0),
        ('temporary selector 7', shot(2, outer_return=0x6014DDC2), reference, 0, 0),
        ('unsafe calibration', shot(2, corrupt_cal=True), corrupt_reference, 0, 0x102),
        ('below normal range', shot(2, fixed_sv=1792), low_reference, 0, 0x102),
        ('stock working Sv differs', shot(2, native_adjustment=1), adjusted_reference, 0, 0x102),
    ):
        controls, published, rejected, steps = result
        if controls != expected or published != ticket or rejected != reject:
            raise RuntimeError(f'{label}: {result}, expected {expected=}, {ticket=}, {reject=}')
        print(f'{label}: TG_GAIN={controls[3]}/{controls[4]}, ticket={published:#x}, '
              f'rejected={rejected:#x}, instructions={steps}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded', type=Path, required=True)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--tool-prefix', required=True)
    args = parser.parse_args()
    inspect(args.decoded.read_bytes(), args.engine, *compile_bridge(args.tool_prefix))


if __name__ == '__main__':
    main()
