#!/usr/bin/env python3
"""Focused 006 regression: unowned capture callbacks and terminal AF-helper ABI.

Uses the existing native engine/bootstrap fixture. It does not reproduce a
complete boot, establish the 005 hardware fault PC, or model physical PWM.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_candidate_publish_sim import bootstrap_context, publish_runtime
from ep7_candidate_startup_sim import CALLER, SP, require
from penf_emulator import Region
from ep7_sim_probe import brief


def call(machine, target, quarantine, **args):
    machine.regions['caller'] = Region('caller', CALLER,
        b'\xdd'+struct.pack('<i', target-CALLER)+bytes(2), 'rx')
    return machine.run(CALLER, CALLER+7, overrides=args,
        breakpoints=[quarantine], full_trace=True)


def inspect(directory, prefix, engine):
    base, front, syms, build, _ = bootstrap_context(directory, prefix, engine)
    machine, *_ = publish_runtime(base, front, syms)
    quarantine = syms['_ep7_gcc_quarantine']
    sidecar = syms['_ep7_controller_sidecar_unresolved']
    before = machine.regions['private'].data
    # Real patched CALL and bridge; stop at the unchanged native pool function.
    native = machine.clone()
    result = native.run(0x6029ce9d, 0x6029acd8,
        breakpoints=[quarantine], full_trace=True)
    require(result['status'] == 'returned' and result['registers']['sp'] == SP-16,
            'unowned native reset did not reach stock')
    require(native.regions['private'].data == before and all(
        result['registers'][r] == native.initial[r]
        for r in ('d0','d1','d2','d3','a0','a1','a2','a3')),
        'unowned reset changed extension state or original inputs')
    cases = [dict(name='unowned_Usr3_reset_reaches_original_pool', **brief(result))]
    rejected = call(machine, syms['_ep7cn_fresh'], quarantine, d0=0)
    require(rejected['status'] == 'returned' and machine.regions['private'].data == before,
            'unowned foreign admission closed or changed the capture sidecar')
    cases.append(dict(name='unowned_foreign_admission_remains_neutral', **brief(rejected)))
    machine.mutate('tcb', 16, struct.pack('<H', 0x73))
    machine.mutate('tcb', 76, struct.pack('<I', 0x60289852))
    chosen = call(machine, syms['_ep7_sidecar_transition_unresolved'], quarantine, d0=0, d1=1)
    require(chosen['status'] == 'returned' and machine.read(sidecar, 8) ==
            b'\x01\0\0\0'+struct.pack('<I',1),
            'a preceding unowned callback prevented the real controller from joining')
    cases.append(dict(name='qualified_controller_can_still_join', **brief(chosen)))
    machine.mutate('state', 0, struct.pack('<H',1))
    machine.mutate('tcb', 16, struct.pack('<H', 0x2d))
    machine.mutate('tcb', 76, struct.pack('<I', 0x601912fb))
    denied = call(machine, syms['_ep7cn_engine_epoch'], quarantine)
    require(denied['status'] == 'breakpoint' and denied['registers']['d0'] == 0xe03,
            'owned foreign destructive callback was allowed to resume')
    cases.append(dict(name='owned_foreign_reset_still_stops_with_e03', **brief(denied)))

    # Execute our entry and the ORIGINAL AF helper. Only the hardware-driver
    # boundaries return modeled zero; do not claim clocks, PWM or LEDs worked.
    led = base.clone()
    reason = 0xf03
    entered = led.run(quarantine, 0x601e73e5, overrides=dict(d0=reason), full_trace=True)
    require(entered['status'] == 'returned' and entered['registers']['d0'] == 0 and
            entered['registers']['d1'] == 250 and entered['registers']['sp'] == SP-28 and
            int.from_bytes(led.read(syms['_ep7_terminal_reason'],4),'little') == reason,
            'terminal helper arguments, native frame or retained reason differ')
    pwm = {0x6006c808:'initialize', 0x6006c888:'stop',
           0x6006c848:'configure', 0x6006c868:'start'}
    regs = entered['registers']
    events = []
    instructions = entered['completed']
    for _ in range(8):
        row = led.resume(regs, CALLER+7, breakpoints=sorted(pwm), full_trace=True, limit=300)
        instructions += row['completed']
        require(row['fault'] is None, 'AF-helper instruction execution faulted')
        regs = row['registers']
        if row['status'] != 'breakpoint':
            require(row['status'] == 'instruction_limit' and not regs['psw'] & 0x800,
                    'terminal path returned or failed to mask interrupts after the helper')
            break
        entry = regs['pc']
        require(regs['d0'] == 0, 'AF helper changed PWM channel')
        event = dict(boundary=hex(entry), operation=pwm[entry], modeled_return=0)
        if entry == 0x6006c848:
            event['configuration'] = list(struct.unpack('<4I', led.read(regs['a0'],16)))
        events.append(event)
        # Each reviewed driver boundary uses native CALL mask0/frame4.
        regs = dict(regs, pc=regs['mdr'], sp=regs['sp']+4, d0=0)
    else:
        raise ValueError('unexpected additional AF driver calls')
    require([r['operation'] for r in events] ==
            ['stop','initialize','initialize','configure','start'] and
            events[3]['configuration'] == [1,249900,50,0],
            'original 250ms AF helper sequence or configuration changed')
    # Recursive terminal entry must retain the first reason and avoid native I/O.
    repeated = led.run(quarantine, CALLER+7, overrides=dict(d0=0xe03),
        breakpoints=[0x601e73e5], full_trace=True, limit=30)
    require(repeated['status'] == 'instruction_limit' and
            int.from_bytes(led.read(syms['_ep7_terminal_reason'],4),'little') == reason,
            'terminal recursion repeated AF setup or overwrote the first reason')
    return dict(status='passed', candidate_build_revision=build['source_revision'],
        cases=cases, terminal_signal=dict(native_instructions=instructions,
            original_helper='0x601e73e5', channel=0, period_argument=250,
            driver_boundaries=events, first_reason_retained=True, terminal_hold_retained=True),
        hardware_executed=False, hash_checks_performed=False,
        limits=['Usr3 reset invocation is a focused counterexample, not a traced physical boot call.',
                'The 005 hardware stopping PC remains unknown; this does not prove its unique cause.',
                'Bootstrap/current-task memory is a fixture; PWM drivers return modeled zero.',
                'Physical AF signaling and successful camera boot require device observation.'])


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--tool-prefix',required=True)
    p.add_argument('--engine',type=Path,required=True)
    a = p.parse_args()
    print(json.dumps(inspect(a.candidate,a.tool_prefix,a.engine),indent=2))
