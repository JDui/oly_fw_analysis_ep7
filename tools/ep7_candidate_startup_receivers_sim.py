#!/usr/bin/env python3
"""Check 007D receiver task entry to the first native wait boundary.

This isolates immediate layout rejection/poll spinning. It does not run the
scheduler, wake a task, simulate Bluetooth, or reproduce a hardware reset.
Reuses the existing native engine, bootstrap and queue-initialization fixtures.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import BASE, STACK, TCB, candidate_inputs, require
from ep7_candidate_publish_sim import bootstrap_context, publish_runtime, u32
from ep7_candidate_message_sim import initialize_queue
from ep7_gui_isolation_package import isolate
from ep7_sim_probe import brief
from penf_emulator import Region

RAW_RECEIVE = 0x60036c8e
QUEUE_WAIT = 0x600343d7
SEMAPHORE_WRAPPER = 0x603eebf3
TASKS = (
    # ROM row, task ID, entry, priority, actual configured stack bytes.
    (0x60038d6c, 0x21, 0x603ef892, 55, 4752),
    (0x60039354, 0x57, 0x603ef94a, 46, 4096),
    (0x600395a0, 0x6c, 0x603f26a1, 26, 8192),
)


def task_view(base, tid, entry, stack_bytes):
    machine = base.clone()
    # Explicit handover in the existing single-current-task fixture; no claim
    # that the real scheduler allocated/activated this synthetic TCB or stack.
    machine.regions['stack'] = Region('stack', STACK, b'\xcc'*stack_bytes, 'rw', True)
    machine.regions['stack_after'] = Region('stack_after', STACK+stack_bytes, b'\x5a'*64)
    machine.regions['tcb'] = replace(machine.regions['tcb'],
        data=machine.regions['tcb'].data+bytes(8))  # Native receiver stores TCB+100.
    machine.mutate('tcb', 16, struct.pack('<H', tid))
    machine.mutate('tcb', 76, struct.pack('<I', entry))
    machine.mutate('tcb', 84, struct.pack('<2I', stack_bytes, STACK))
    # Task-entry CALLS leaves SP at top-4, as in the existing startup stack review.
    return machine, STACK+stack_bytes-4


def inspect(stock_path, candidate_dir, diagnostic_path, prefix, engine):
    original = stock_path.read_bytes()
    compiled, syms, build = candidate_inputs(candidate_dir, prefix)
    data, _ = isolate(original, compiled, build)
    require(diagnostic_path.read_bytes() == data, '007D differs from the exact GUI-only derivation')
    setup = []

    def prepare(machine, symbols):
        for handle in (0x4c, 0x4d, 0xab, 0x4f):
            row = initialize_queue(machine, symbols, handle)
            setup.append(dict(handle=hex(handle), **brief(row)))

    base, front, _, _, _ = bootstrap_context(None, None, engine, prepare_kernel=prepare,
        candidate_override=(data, syms, build))
    base, _, _, _ = publish_runtime(base, front, syms)
    # Same explicit disabled trace mask as the existing descriptor probe.
    # Original logging instructions still execute on the stock comparison path.
    base.regions['native_trace_enable_mask'] = Region('native_trace_enable_mask',
        0x622930e8, bytes(2), 'r')
    cases = []
    for address, tid, entry, priority, stack_bytes in TASKS:
        require(base.read(address, 28) == struct.pack('<7I', tid, 0, 0, entry, priority, stack_bytes, 0),
                'native task configuration changed')
        expected_handles = [0x4c, 0x4d] if tid == 0x21 else [0xab if tid == 0x57 else 0x4f]
        expected_wait = SEMAPHORE_WRAPPER if tid == 0x21 else QUEUE_WAIT
        outcomes = []
        for label in ('stock', '007D'):
            machine, sp = task_view(base, tid, entry, stack_bytes)
            if label == 'stock':
                machine.regions['candidate'] = replace(machine.regions['candidate'], data=original)
                # Restore the original capacities and matching empty ring cursors.
                # Backing allocation remains an explicit, large-enough fixture.
                for handle in (0x4c, 0xab, 0x4f):
                    name = f'queue_{handle:x}'
                    backing = u32(machine, machine.regions[name].address+32)
                    machine.mutate(name, 24, struct.pack('<2I', 300, 9728))
                    machine.mutate(name, 44, struct.pack('<2I', backing+9728, 9728))
            before_private = machine.regions['private'].data
            result = machine.run(entry, expected_wait, overrides=dict(sp=sp), full_trace=True,
                breakpoints=[syms['_ep7_gcc_quarantine']], limit=30000)
            require(result['status'] == 'returned' and result['registers']['pc'] == expected_wait
                    and result['fault'] is None, f'{label} task {tid:x} stopped: {brief(result)}')
            raw = [r for r in result['trace'] if r['pc'] == RAW_RECEIVE]
            require([r['d0'] for r in raw] == expected_handles,
                    f'{label} task {tid:x} skipped/repeated native receive')
            expected_timeout = 0 if tid == 0x21 else 0xffffffff
            require(all(r['d1'] == expected_timeout for r in raw), 'native timeout changed')
            for handle in expected_handles:
                q = machine.regions[f'queue_{handle:x}'].address
                require(u32(machine, q+52) == 0, 'empty receive invented a message')
            require(machine.regions['private'].data == before_private,
                    'idle startup unexpectedly changed private H/L state')
            regs = result['registers']
            if tid == 0x21:
                require(regs['d0'] == int.from_bytes(machine.read(0x60040b6e, 2), 'little')
                        and regs['d1'] == 0xffffffff,
                        'dual receiver did not request the stock indefinite semaphore wait')
            else:
                queue = machine.regions[f'queue_{expected_handles[0]:x}'].address
                require(regs['d0'] == 0 and regs['d1'] == queue+12 and regs['a0'] == TCB
                        and u32(machine, TCB+100) == raw[0]['a0'],
                        'native queue wait did not retain its destination/current task')
            outcomes.append(dict(image=label, **brief(result),
                raw_receives=[dict(handle=hex(r['d0']), timeout=hex(r['d1']),
                                   destination=hex(r['a0'])) for r in raw],
                wait_boundary=hex(expected_wait),
                observed_stack_depth=sp-min(r['sp'] for r in result['trace']),
                private_state_unchanged=True))
        cases.append(dict(task_id=hex(tid), entry=hex(entry), configured_stack_bytes=stack_bytes,
                          outcomes=outcomes))
    return dict(scope=__doc__, status='passed', compiled_revision=build['source_revision'],
        input_diagnostic='007D', exact_diagnostic_bytes_checked=True,
        native_queue_initialization=setup, cases=cases,
        immediate_receiver_layout_rejection_observed=False,
        hash_checks_performed=False, hardware_executed=False, firmware_modified=False,
        full_boot_executed=False, limits=[
            'The image, actual task entry instructions and original queue APIs execute; tasks stop at their first native wait boundary.',
            'Current TCB, task handover, stacks, kernel roots and ready/lock state remain explicit fixtures.',
            'Bootstrap uses the existing ID1-only semaphore fixture; the prior static-ID133 test is not rerun or substituted.',
            'Queue initialization executes original code against fixture backing; static allocation is not repeated.',
            'The original trace-enable mask is explicitly zero; logging output is not modeled.',
            'Actual task suspension, scheduling, wakeup, messages, cache/multicore behavior and hardware reset causes are outside this check.',
            'A pass rules out immediate layout rejection in these fixture paths only, not a whole-camera boot defect.'])


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--diagnostic', type=Path, required=True)
    p.add_argument('--tool-prefix', required=True)
    p.add_argument('--engine', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(inspect(a.stock, a.candidate, a.diagnostic, a.tool_prefix, a.engine), indent=2))
