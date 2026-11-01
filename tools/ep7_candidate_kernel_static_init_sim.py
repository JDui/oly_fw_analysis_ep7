#!/usr/bin/env python3
"""Compare stock/005 domain0 static-object allocation, without running camera tasks.

Reuses the strict native engine and actual image tables. CPU/root selection and
resident memory are explicit fixtures. This is not a whole boot or flash test.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import BASE, CALLER, SP, Machine, require
from ep7_sim_probe import brief
from penf_emulator import Region

ROOT = 0x600411a4
HEAP = 0x621a63c0
HEAP_BASE, HEAP_BYTES = 0x6203c940, 0xb1000
OBJECT_BASE, OBJECT_END = 0x62192000, 0x621a6430
ERROR = 0x6003853d
SELECTED = (0x4b, 0x4c, 0x4d, 0x4f, 0xab)


def u32(machine, address):
    return int.from_bytes(machine.read(address, 4), 'little')


def run_case(path, engine):
    data = path.read_bytes()
    require(len(data) == 26214336, 'unsupported decoded main length')
    machine = Machine(data, engine)
    require(machine.read(ROOT+40, 12) == struct.pack('<3I', HEAP, HEAP_BASE, HEAP_BYTES),
            'domain0 heap recipe changed')
    for name, region in list(machine.regions.items()):
        if OBJECT_BASE <= region.address < OBJECT_END:
            del machine.regions[name]
    machine.regions['kernel_heap'] = Region('kernel_heap', HEAP_BASE,
        b'\xa5'*HEAP_BYTES, 'rw', True)
    machine.regions['kernel_objects'] = Region('kernel_objects', OBJECT_BASE,
        b'\xa5'*(OBJECT_END-OBJECT_BASE), 'rw', True)
    # The original pointer tables place task138, semaphore132 and the shared
    # queue objects here, ending immediately before domain1's pending list.
    machine.regions['domain0_shared_objects'] = Region('domain0_shared_objects',
        0xa2793f90, b'\xa5'*(0xa27942b0-0xa2793f90), 'rw', True)
    steps = []

    def capture(name, result, stop):
        row = dict(name=name, **brief(result), d0=hex(result['registers']['d0']))
        steps.append(row)
        require(result['status'] == 'returned' and result['registers']['pc'] == stop
                and result['fault'] is None, 'native initialization stopped: '+str(row))

    def native(name, target, mask, frame, limit=100000):
        machine.regions['caller'] = Region('caller', CALLER,
            b'\xdd'+struct.pack('<i', target-CALLER)+bytes([mask, frame]), 'rx')
        result = machine.run(CALLER, CALLER+7, limit=limit, breakpoints=[ERROR])
        capture(name, result, CALLER+7)
        require(result['registers']['sp'] == SP, 'native call stack did not return')
        return result

    # These are the stock instructions, rather than host injection of counts or
    # already allocated queue headers/backing. The debug-disable write is also
    # executed, matching its position before all static constructors in stock.
    count = machine.run(0x60032622, 0x60032651, overrides={'d3':0x8ff00004})
    capture('native_all_class_counts', count, 0x60032651)
    debug = machine.run(0x60032651, 0x6003265f, overrides={'d3':0x8ff00004})
    capture('native_boot_debug_disable', debug, 0x6003265f)
    native('native_cold_heap', 0x600360b5, 0x30, 8)
    native('native_all_free_object_IDs', 0x60035617, 0xf0, 16)
    native('native_pre_static_task_setup', 0x60032f63, 0xa0, 12)
    native('native_all_static_objects', 0x60032945, 0, 4)

    free_blocks, seen = [], set()
    node = u32(machine, HEAP+8)
    while node != HEAP:
        require(node not in seen and HEAP_BASE <= node <= HEAP_BASE+HEAP_BYTES-20,
                'invalid native free-list node')
        seen.add(node)
        free_blocks.append(dict(address=hex(node), bytes=u32(machine,node+16)))
        node = u32(machine,node+8)

    queues = []
    table = u32(machine, ROOT+232)
    for handle in SELECTED:
        address = u32(machine, table+4*(handle-1))
        ident = int.from_bytes(machine.read(address,2),'little')
        attributes, maximum, ring, backing = struct.unpack('<4I',machine.read(address+20,16))
        require(ident == handle and attributes == 128 and backing and
                machine.read(address+36,20) == struct.pack('<5I',backing,backing,backing+ring,ring,0),
                'selected native queue was not initialized')
        queues.append(dict(handle=hex(handle), object=hex(address), attributes=attributes,
            maximum=maximum, ring_bytes=ring, backing=hex(backing)))
    task_table = u32(machine, ROOT+204)
    task = u32(machine, task_table+4*(0x2d-1))
    return dict(image=str(path), status='passed', steps=steps,
        executed_instructions=sum(s['completed'] for s in steps),
        free_blocks=free_blocks, free_block_bytes=sum(b['bytes'] for b in free_blocks),
        selected_queues=queues, usr3=dict(tcb=hex(task),
            tid=int.from_bytes(machine.read(task+16,2),'little'),
            exception_flag=int.from_bytes(machine.read(task+48,2),'little'),
            entry=hex(u32(machine,task+76)), stack_bytes=u32(machine,task+84),
            stack_low=hex(u32(machine,task+88))))


def inspect(stock, candidate, engine):
    original = run_case(stock, engine)
    modified = run_case(candidate, engine)
    return dict(status='passed', stock=original, candidate=modified,
        extra_static_heap_bytes=original['free_block_bytes']-modified['free_block_bytes'],
        hardware_executed=False, firmware_modified=False, hash_checks_performed=False,
        limits=[
            'Resident code, CPU ID and root selection are fixtures; physical loading and cache/multicore behavior are not executed.',
            'Only the named original initialization fragments/functions execute. No scheduler, camera task startup, capture or GUI is run.',
            'Passing allocation rules out exhaustion in this domain0 static initialization case, not later allocation failure or a physical boot defect.',
            'Free block sizes include allocator headers and are not a promised largest usable allocation.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.stock,args.candidate,args.engine),indent=2))
