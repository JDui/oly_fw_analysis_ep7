#!/usr/bin/env python3
"""010 terminal diagnostics using the existing native engine and AF-helper probe.

Runs real candidate assembly and stock AF helper; only PWM driver returns are
modeled. This identifies emitted configurations, not physical LED visibility.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_candidate_publish_sim import bootstrap_context
from ep7_candidate_startup_sim import CALLER, SP, require


def inspect(directory, prefix, engine):
    base, _, syms, build, _ = bootstrap_context(directory, prefix, engine)
    quarantine = syms['_ep7_gcc_quarantine']
    reason_address = syms['_ep7_terminal_reason']
    helper = 0x601e73e5
    require(base.read(0x601e73ce, 5) == bytes.fromhex('cd1700c01c'),
            'original AF helper call target/mask/frame changed')
    pwm = {0x6006c808: 'initialize', 0x6006c888: 'stop',
           0x6006c848: 'configure', 0x6006c868: 'start'}
    # One complete stock-helper execution for each supported mode. Additional
    # reasons cover each explicit assembly branch without repeating the driver.
    cases = []
    for reason, mode in ((0x701, 255), (0xc01, 100), (0x80a, 50), (0xf03, 250),
                         (0x901, 50), (0xa01, 50), (0xb01, 50), (0xd01, 50),
                         (3, 250), (0xe03, 250)):
        led = base.clone()
        entered = led.run(quarantine, helper, overrides=dict(d0=reason), full_trace=True)
        regs = entered['registers']
        require(entered['status'] == 'returned' and regs['d0'] == 0 and
                regs['d1'] == mode and regs['sp'] == SP-28 and
                int.from_bytes(led.read(reason_address, 4), 'little') == reason,
                'terminal native arguments/frame/first reason differ for '+hex(reason))
        case = dict(reason=hex(reason), helper_mode=mode,
                    first_reason_stored=True, native_frame_preserved=True)
        if len(cases) < 4:
            events = []
            instructions = entered['completed']
            for _ in range(8):
                row = led.resume(regs, CALLER+7, breakpoints=sorted(pwm),
                                 full_trace=True, limit=300)
                instructions += row['completed']
                require(row['fault'] is None, 'stock AF helper execution faulted')
                regs = row['registers']
                if row['status'] != 'breakpoint':
                    require(row['status'] == 'instruction_limit' and not regs['psw'] & 0x800,
                            'terminal path returned or failed to mask interrupts')
                    break
                entry = regs['pc']
                require(regs['d0'] == 0, 'AF helper changed PWM channel')
                event = dict(boundary=hex(entry), operation=pwm[entry], modeled_return=0)
                if entry == 0x6006c848:
                    event['configuration'] = list(struct.unpack('<4I', led.read(regs['a0'], 16)))
                events.append(event)
                # Original helper's driver CALLs use mask0/frame4, as in 006.
                regs = dict(regs, pc=regs['mdr'], sp=regs['sp']+4, d0=0)
            else:
                raise ValueError('unexpected additional AF driver calls')
            expected = (['initialize', 'stop', 'configure', 'start'] if mode == 255 else
                        ['stop', 'initialize', 'initialize', 'configure', 'start'])
            # Stock 601e7440..601e745a divides 1000 by mode, then 15686 by
            # that quotient, divides by 4 and multiplies by 255. Preserve
            # its integer quantization (100 => 99960; 50 => 49980).
            configuration = ([1, 16065, 100, 0] if mode == 255 else
                             [1, (15686 // (1000 // mode) // 4)*255, 50, 0])
            require([e['operation'] for e in events] == expected and
                    next(e['configuration'] for e in events if e['operation'] == 'configure') == configuration,
                    'stock AF helper sequence/configuration differs for mode '+str(mode)+': '+repr(events))
            repeated = led.run(quarantine, CALLER+7, overrides=dict(d0=0xe04),
                               breakpoints=[helper], full_trace=True, limit=30)
            require(repeated['status'] == 'instruction_limit' and
                    int.from_bytes(led.read(reason_address, 4), 'little') == reason,
                    'reentry repeated AF setup or overwrote the first reason')
            case.update(native_instructions=instructions, driver_boundaries=events,
                        first_reason_retained_on_reentry=True, terminal_hold_retained=True)
        cases.append(case)
    return dict(status='passed', candidate_build_revision=build['source_revision'],
        cases=cases, original_helper=hex(helper), channel=0,
        hardware_executed=False, hash_checks_performed=False,
        limits=['Bootstrap/current-task memory uses the existing fixture; PWM driver returns are modeled.',
                'Four complete stock-helper mode paths and six additional reason selections executed.',
                'Physical blink speed/visibility and camera boot were not tested.',
                '010 changes diagnostic signaling only; it does not fix or reproduce the reported curve-page crash.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--tool-prefix', required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.candidate, args.tool_prefix, args.engine), indent=2))
