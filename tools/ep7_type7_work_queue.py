#!/usr/bin/env python3
"""Execute native TOP queue enqueue/pop and bind type7's three-word carrier.

Explicit preallocated queue/record fixtures, no allocator, RTOS, hardware or
engine object mapping. The real stock queue functions and CALL frames execute.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_native_stack import BASE, NativeGraph
from ep7_sim_probe import run, brief, capture
from penf_emulator import Region

QUEUE = 0x19020000
RECORD = 0x19021000
SOURCE = 0x19022000
OUTPUT = 0x19023000
ENGINE = 0x19024000
STACK = 0x19010000
SP = STACK + 512
WINDOWS = [(0x6011bb99, 0x6011bbf7), (0x6011bc9d, 0x6011bce5),
           (0x6011bdd3, 0x6011be1c), (0x6011be49, 0x6011be90),
           (0x6011bfd9, 0x6011c022), (0x6011c097, 0x6011c0c3)]
W = {
    0x6011f558: ('mov', '1612362452,a0'),
    0x6011f55e: ('mov', '16,d0'),
    0x6011f561: ('call', '0x6011ba77,[d2,d3,a2,a3],32'),
    0x6011f566: ('mov', 'a0,(0x621f31ec)'),
    0x6011fa5d: ('mov', '(0x621f31ec),a3'),
    0x6011fa6f: ('mov', 'a2,(120,sp)'),
    0x6011fa73: ('mov', '2,d0'), 0x6011fa75: ('mov', 'd0,(128,sp)'),
    0x6011fa77: ('call', '0x6011fb76,[d2],4'),
    0x6011fa7c: ('mov', 'd0,(124,sp)'),
    0x6011fa8e: ('cmp', '-1,d0'),
    0x6011fa90: ('bne', '0x6011fa96'),
    0x6011fa92: ('mov', '5,d0'), 0x6011fa94: ('mov', 'd0,(128,sp)'),
    0x6011faa0: ('mov', 'd3,d1'), 0x6011faa1: ('clr', 'd0'),
    0x6011faa2: ('mov', 'a3,a0'),
    0x6011faa3: ('mov', '1612362452,a1'),
    0x6011faa9: ('call', '0x6011bb99,[d2,d3,a2,a3],28'),
    0x6011faae: ('mov', 'd2,d0'),
    0x6011fb3d: ('clr', 'd0'),
    # Enqueue chooses/preallocates a record, copies exactly three words, links it.
    0x6011bb99: ('mov', 'd1,a3'),
    0x6011bb9d: ('call', '0x6011c097,[a2,a3],12'),
    0x6011bbaa: ('call', '0x6011bfd9,[d2,a2],12'),
    0x6011bbb5: ('mov', '-3,d1'),
    0x6011bbb8: ('mov', '(a3),d0'), 0x6011bbba: ('mov', 'd0,(a2)'),
    0x6011bbbe: ('lne', ''),
    0x6011bbc1: ('call', '0x6011bdeb,[a2,a3],8'),
    0x6011bbf2: ('mov', 'd3,d0'),
    # The type135 consumer pops by value, retaining the original engine pointer.
    0x601200aa: ('mov', '(0x621f31ec),d0'),
    0x601e78c5: ('call', '0x601200aa,[d2,d3,a2,a3],48'),
    0x601e78cf: ('call', '0x6012059a,[d2,d3,a2,a3],48'),
    0x601200dd: ('call', '0x6011bc9d,[d2,d3,a2,a3],24'),
    0x601200e2: ('mov', '(28,sp),d0'),
    0x601200e4: ('mov', '(20,sp),a2'),
    0x6012011c: ('mov', '32775,d0'),
    0x60120122: ('mov', 'a2,a0'),
    0x60120123: ('call', '0x60120d73,[d2,d3,a2,a3],32'),
    0x60120137: ('call', '0x6011bb99,[d2,d3,a2,a3],28'),
    0x60120154: ('mov', '14994,d0'),
    0x60120158: ('call', '0x601215a8,[],4'),
    0x601215a8: ('mov', '64,a1'), 0x601215aa: ('add', 'a0,a1'),
    0x601215b1: ('mov', '(a1),a1'), 0x601215b4: ('calls', '(a1)'),
    0x6011bcaa: ('call', '0x6011be64,[a2,a3],8'),
    0x6011bcb9: ('mov', '-3,d1'),
    0x6011bcbc: ('mov', '(a3),d0'), 0x6011bcbe: ('mov', 'd0,(a2)'),
    0x6011bcc2: ('lne', ''),
    0x6011bcc5: ('call', '0x6011bdd3,[a2],4'),
}


def inspect(decoded, objdump, engine):
    graph = NativeGraph(decoded, objdump)
    try:
        for pc, expected in W.items():
            if graph.instruction(pc)[2:] != expected:
                raise ValueError(('TOP witness changed', hex(pc), expected))
        data = graph.data
        if data[0x601ab2d4-BASE:0x601ab2d8-BASE] != b'TOP\0':
            raise ValueError('queue name changed')
        table = [(0x601ecc94, 3, 0x601e785a),
                 (0x601eccac, 131, 0x601e78c4),
                 (0x601ecd04, 145, 0x601e78ce)]
        for at, key, target in table:
            if struct.unpack_from('<2I', data, at-BASE) != (key, target):
                raise ValueError('TOP engine operation dispatch changed')
    finally:
        graph.close()

    manager = bytearray(36)
    struct.pack_into('<II', manager, 12, RECORD, RECORD)
    words = (ENGINE, 3, 2)
    packet = struct.pack('<3I', *words)
    regions = [Region('native_'+hex(lo), lo, data[lo-BASE:hi-BASE], 'rx') for lo, hi in WINDOWS]
    regions += [
        Region('enqueue_call', 0x6011faa9, data[0x6011faa9-BASE:0x6011faae-BASE], 'rx'),
        Region('pop_call', 0x601200dd, data[0x601200dd-BASE:0x601200e2-BASE], 'rx'),
        Region('registry_root_fixture', 0x621dd964, bytes(4)),
        Region('queue_fixture', QUEUE, bytes(manager), 'rw', True),
        Region('record_fixture', RECORD, bytes(20), 'rw', True),
        Region('source_fixture', SOURCE, packet, 'rw', True),
        Region('output_fixture', OUTPUT, bytes(12), 'rw', True),
        Region('stack_fixture', STACK, b'\xa5'*1024, 'rw', True),
    ]
    sent = run(engine, regions, dict(pc=0x6011faa9, sp=SP, a0=QUEUE, a1=0, d0=0, d1=SOURCE),
               stop=0x6011faae, limit=300)
    queued = bytearray(manager)
    struct.pack_into('<4I', queued, 4, RECORD, RECORD, 0, 0)
    struct.pack_into('<H', queued, 24, 1)
    if (sent['status'] != 'returned' or sent['registers']['sp'] != SP
            or sent['registers']['d0'] != 0 or capture(sent, 'queue_fixture') != queued
            or capture(sent, 'record_fixture') != packet+bytes(8)):
        raise ValueError(('native enqueue differs', brief(sent)))
    captured = {r['name']: bytes.fromhex(r['hex']) for r in sent['memory']}
    resumed = [replace(r, data=captured.get(r.name, r.data)) for r in regions]
    # Reuse the caller's temporary source immediately. The queue must return its
    # own copied three words; ENGINE stays unmapped, proving no deep copy occurs.
    resumed = [replace(r, data=b'\xde'*12) if r.name == 'source_fixture' else r for r in resumed]
    popped = run(engine, resumed, dict(pc=0x601200dd, sp=SP, a0=QUEUE, a1=0, d0=OUTPUT),
                 stop=0x601200e2, limit=300)
    if (popped['status'] != 'returned' or popped['registers']['sp'] != SP
            or popped['registers']['d0'] != 0 or capture(popped, 'queue_fixture') != manager
            or capture(popped, 'output_fixture') != packet
            or capture(popped, 'source_fixture') != b'\xde'*12):
        raise ValueError(('native pop differs', brief(popped)))
    return dict(scope=__doc__, checked_witnesses=len(W), checked_data_rows=4,
        queue_pointer_cell='0x621f31ec', queue_name='TOP',
        carrier_words=['engine_pointer', 'helper6011fb76_result', 'operation_mode'],
        copied_bytes=12, normal_mode=2, alternate_mode=5,
        enqueue=brief(sent), dequeue=brief(popped),
        source_overwritten_before_pop=True, packet_copy_survived=True,
        engine_object_unmapped=True, allocator_and_rtos_unmapped=True,
        engine_deep_copy=False, queue_entry_generation_carried=False,
        type7_normal_submit_preserves_enqueue_status=False,
        consumers=[dict(type=135, entry='0x601200aa'), dict(type=149, entry='0x6012059a')],
        completion_dispatch='0x601215a8', completion_field=64,
        callback_domain_or_cancellation_proven=False,
        all_assertions_passed=True, hash_checks_performed=False,
        firmware_modified=False, firmware_built=False, hardware_executed=False,
        limits=[
            'One existing free node, an empty queue and a stable explicit manager form the fixture; constructor, growth, exhaustion and concurrent access are not executed.',
            'The original enqueue/dequeue CALL instructions and callees run; surrounding submit/consumer branches are statically checked only.',
            'A copied pointer does not extend the engine/workrecord/node lifetime. No generation is added by this native twelve-byte carrier.',
            'The type135/type149 callers and processing completion domains, alternate type7 branches, reentry and cancellation remain to qualify.'
        ])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded', type=Path, required=True)
    parser.add_argument('--objdump', type=Path, required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.decoded, args.objdump, args.engine), indent=2))
