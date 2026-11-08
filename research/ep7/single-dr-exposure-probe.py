#!/usr/bin/env python3
"""Replay stock STILL exposure arithmetic and the native TG_GAIN handoff."""

import argparse
from pathlib import Path
from struct import pack, pack_into, unpack_from

from ep7_sim_probe import capture, run
from penf_emulator import Region


BASE = 0x60020020
STACK = 0x19010000
SP = STACK + 512
COMMAND = 0x19020000
WORK = 0x19021000
EXPOSURE = 0x19022000
CONTEXT = 0x19023000
PACKET = 0x19024000
CONFIG = 0x19025000
TG_GAIN = 0x19026000
JOB = 0x19027000
SLOT = 0x19028000
SLOT_GAIN = 0x19029000
SLOT_MODE = 0x1902A000
CALLBACK = 0x1902C000
TG_STATE = 0x1902D000
SERIAL_DATA = 0x621F5570
STILL = 0x601CA690
DB_GAIN = 0x60091A88
OPTICAL_BLACK = 0x60091638


def record(size, fields):
    data = bytearray(size)
    for offset, fmt, value in fields:
        pack_into(fmt, data, offset, value)
    return bytes(data)


def replay_tg_gain(execute, command):
    """Feed the supplied type-0 result through the original TG and serial writes."""
    flag, _, control_a, control_b = unpack_from('<4I', command, 48)
    handoff = execute(0x6013CD94, 0x6013CD99, dict(a0=CONTEXT),
                      [Region('context', CONTEXT, pack('<6I', PACKET, COMMAND, 0, EXPOSURE, 0, STILL)),
                       Region('packet', PACKET, record(32, ((2, '<H', 7), (28, '<I', CONFIG)))),
                       Region('command', COMMAND, command),
                       Region('config', CONFIG, record(476, ((472, '<I', TG_GAIN),)), 'rw', True),
                       Region('tg_gain', TG_GAIN, bytes(24), 'rw', True)])
    payload = capture(handoff, 'tg_gain')
    if (unpack_from('<3I', payload) != (flag, control_a, control_b)
            or unpack_from('<I', capture(handoff, 'config')) != (1 << 25,)):
        raise RuntimeError('native TG_GAIN payload or enable bit differs')

    make_job = execute(0x601503F3, 0x60150406,
                       dict(a0=CONFIG, a2=JOB - 1800, a3=CALLBACK),
                       [Region('config', CONFIG, capture(handoff, 'config')),
                        Region('callback', CALLBACK, bytes(4)),
                        Region('job', JOB, bytes(72), 'rw', True)])
    job = capture(make_job, 'job')
    if unpack_from('<H', job) != (7,) or unpack_from('<I', job, 20) != (TG_GAIN,):
        raise RuntimeError('native TG_GAIN job setup differs')

    accept = execute(0x60138125, 0x6013812A, dict(a0=JOB),
                     [Region('root', 0x621F52D8, pack('<I', SLOT)),
                      Region('job', JOB, job),
                      Region('tg_gain', TG_GAIN, payload),
                      Region('slot', SLOT, record(116, ((24, '<I', SLOT_MODE),
                                                      (40, '<I', SLOT_GAIN))), 'rw', True),
                      Region('slot_gain', SLOT_GAIN, bytes(24), 'rw', True)])
    slot = capture(accept, 'slot')
    accepted_gain = capture(accept, 'slot_gain')
    if (accept['registers']['d0'] != 0 or unpack_from('<I', slot, 12) != (16,)
            or accepted_gain != payload):
        raise RuntimeError('native TG_GAIN slot copy or pending bit differs')

    # The serial command addresses come from the native TG template. The
    # active timing state and mode word are fixture inputs for this slice.
    serial_before = record(0x144, tuple((4 + 8 * i, '<I', 0x5A001234) for i in range(6)))
    packed = execute(0x60138C8B, 0x60138CC2, dict(a2=SLOT + 12),
                     [Region('tg_state_ptr', 0x621F555C, pack('<I', TG_STATE)),
                      Region('tg_state', TG_STATE, bytes(16), 'rw'),
                      Region('slot', SLOT, slot, 'rw', True),
                      Region('slot_mode', SLOT_MODE, pack('<I', 10 << 20)),
                      Region('slot_gain', SLOT_GAIN, accepted_gain),
                      Region('serial', SERIAL_DATA, serial_before, 'rw', True)])
    serial = capture(packed, 'serial')
    encoded = tuple(unpack_from('<I', serial, offset)[0] for offset in range(12, 48, 8))
    expected_bytes = (flag, control_a & 255, control_a >> 8, control_b & 255, control_b >> 8)
    if (encoded != tuple(0x5A001234 | value << 16 for value in expected_bytes)
            or unpack_from('<2I', serial, 0x621F56A4 - SERIAL_DATA) != (control_a, control_b)
            or unpack_from('<I', capture(packed, 'slot'), 12) != (0,)):
        raise RuntimeError('native TG_GAIN serial encoding or slot acknowledgment differs')

    return expected_bytes, handoff['completed'], packed['completed']


def inspect(image, engine):
    if (len(image) != 26214336
            or unpack_from('<I', image, STILL - BASE) != (10,)
            or unpack_from('<2h', image, STILL + 68 - BASE) != (3033, 1024)
            or unpack_from('<HH', image, DB_GAIN - BASE) != (0x712A, 24)
            or unpack_from('<HH', image, OPTICAL_BLACK - BASE) != (0x703A, 550)
            or image[0x6013CD94 - BASE:0x6013CD99 - BASE] != bytes.fromhex('cd b1 30 20 08')):
        raise ValueError('unexpected E-P7 1100 mode, table or native call witness')

    common = [Region('stock_main', BASE, image, 'rx'),
              Region('gain_roots', 0x621F3FF4, pack('<II', DB_GAIN + 4, OPTICAL_BLACK + 4)),
              Region('stack', STACK, bytes(1024), 'rw')]

    def execute(start, stop, registers, regions):
        result = run(engine, common + regions, dict(pc=start, sp=SP, **registers), stop=stop, limit=700)
        if result['status'] != 'returned' or result['registers']['sp'] != SP:
            raise RuntimeError(f'{start:08x}: {result["status"]}, {result["fault"]}')
        return result

    nominal = 1792
    original_command = record(168, ((4, '<I', 10), (20, '<I', EXPOSURE)))
    original_exposure = record(92, ((0, '<I', 0x400), (6, '<h', 2304),
                                    (8, '<h', nominal), (10, '<h', 768)))
    work = record(152, ((0, '<I', STILL),))
    loaded = execute(0x6012E698, 0x6012E6EF, dict(a2=WORK, a3=COMMAND),
                     [Region('command', COMMAND, original_command),
                      Region('work', WORK, work, 'rw', True),
                      Region('exposure', EXPOSURE, original_exposure, 'rw', True)])
    work = capture(loaded, 'work')
    exposure = capture(loaded, 'exposure')
    if unpack_from('<h', work, 46) != (nominal,) or unpack_from('<3h', exposure, 48) != (2304, nominal, 768):
        raise RuntimeError('native loading or nominal Tv/Sv/Av echo differs')

    rows = []
    for requested in (1792, 1536, 1280, 1024, 2048):
        independent_work = bytearray(work)
        pack_into('<h', independent_work, 46, requested)
        gain = execute(0x6012E6EF, 0x6012E76D, dict(a1=WORK, a2=WORK, a3=COMMAND),
                       [Region('command', COMMAND, original_command, 'rw', True),
                        Region('work', WORK, bytes(independent_work), 'rw', True),
                        Region('exposure', EXPOSURE, exposure, 'r')])
        command = capture(gain, 'command')
        calibrated, = unpack_from('<i', capture(gain, 'work'), 52)
        multiplier, flag, _, control_a, control_b = unpack_from('<5I', command, 44)

        expected_bytes, handoff_steps, packing_steps = replay_tg_gain(execute, command)
        rows.append((nominal, requested, calibrated, multiplier, flag, control_a, control_b,
                     *expected_bytes, gain['completed'], handoff_steps, packing_steps))

    expected = [(3082 * 256, 65536, 1, 3070, 3070), (1541 * 256, 65536, 1, 2046, 2046),
                (0, 65536, 1, 0, 0), (-1541 * 256, 65536, 81, 0, 0),
                (4623 * 256, 65536, 1, 3583, 3583)]
    if [row[2:7] for row in rows] != expected:
        raise RuntimeError(f'native gain output differs: {rows}')
    print('nominalSvQ8 workSvQ8 dBcalQ16 multiplierQ16 tgFlags tgCodeA tgCodeB '
          'flagByte codeALow codeAHigh codeBLow codeBHigh gainInstructions transferInstructions packingInstructions')
    for row in rows:
        print(*row)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded', type=Path, required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    inspect(args.decoded.read_bytes(), args.engine)


if __name__ == '__main__':
    main()
