#!/usr/bin/env python3
"""Bind producer event42 to controller queue0x67, separately from mailbox1.

Exact static witnesses and bounded function CFGs; returning-callee control flow
is not a scheduler, queue-lifetime, notification-delivery or exclusion proof.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_native_stack import BASE, NativeGraph
from ep7_deferred_producer import W as DEFERRED_W
from ep7_producer_scope import W as PRODUCER_W

W = {
    # Same selected handler sets the backlink, then passes its associated record.
    0x602a2901: ('mov', '(a3),a0'),
    0x602a2903: ('mov', 'd2,(8,a0)'),
    0x602a291b: ('mov', '(a3),d0'),
    0x602a291c: ('mov', 'd0,a0'),
    0x602a291e: ('call', '0x602ac141,[d2],24'),
    0x602ac147: ('mov', 'a0,d2'),
    0x602ac18e: ('clr', 'd1'), 0x602ac18f: ('mov', 'd2,d0'),
    0x602ac190: ('call', '0x602ac1e1,[d2,d3,a2],36'),
    0x602ac1e1: ('mov', 'd0,a2'),
    0x602ac264: ('call', '0x6020b962,[],0'),
    0x602ac26e: ('bgt', '0x602ac272'),
    0x602ac270: ('bra', '0x602ac2ef'),
    0x602ac278: ('call', '0x6020b962,[],0'),
    0x602ac282: ('ble', '0x602ac2ef'),
    0x602ac2e4: ('mov', '66,d0'),
    0x602ac2e6: ('mov', 'a2,d1'),
    0x602ac2e8: ('call', '0x602ad656,[d2],20'),
    0x602ac2ed: ('bra', '0x602ac2fe'),
    0x602ac2f7: ('call', '0x6020b98b,[],8'),
    0x602ac2fe: ('movbu', '(0x6223e7a8),d1'),
    0x602ac328: ('bne', '0x602ac375'),
    0x602ac37d: ('bne', '0x602ac3ee'),
    0x602ac387: ('bne', '0x602ac3e5'),
    0x602ac38b: ('call', '0x602ac88a,[d2],4'),
    0x602ac393: ('beq', '0x602ac3e5'),
    0x602ac3c9: ('mov', '1,d0'),
    0x602ac3d1: ('mov', 'a2,(0x6223e7b0)'),
    0x602ac40e: ('ret', '[d2,d3,a2],36'),
    # Stack packet {status16, event32, associated32}, destination from60040daa.
    0x602ad656: ('exthu', 'd0'), 0x602ad657: ('clr', 'd2'),
    0x602ad658: ('movhu', 'd2,(4,sp)'),
    0x602ad65b: ('mov', 'd0,(8,sp)'),
    0x602ad65d: ('mov', 'd1,(12,sp)'),
    0x602ad65f: ('movhu', '(0x60040daa),d0'),
    0x602ad665: ('mov', 'sp,a0'), 0x602ad667: ('inc4', 'a0'),
    0x602ad668: ('mov', '12,d1'), 0x602ad66a: ('mov', '-1,a1'),
    0x602ad670: ('call', '0x6020beb4,[d2,d3],48'),
    0x602ad677: ('ret', '[d2],20'),
    # Local named send, followed by event-flag notification, not a handler CALL.
    0x60051527: ('mov', 'd2,d0'),
    0x60051528: ('call', '0x6005393a,[d2,d3],16'),
    0x6005152f: ('beq', '0x60051547'),
    0x60051547: ('mov', '(a2),d3'),
    0x60051548: ('mov', '(4,a2),d1'),
    0x6005154b: ('mov', 'd2,d0'),
    0x6005154d: ('mov', 'd3,a0'),
    0x6005154f: ('mov', 'a3,a1'),
    0x6005155d: ('call', '0x6005378e,[d2],8'),
    0x600515a8: ('mov', 'd1,a1'),
    0x600515aa: ('add', '-1569967244,a1'),
    0x600515ba: ('udfu01', '12,d2'),
    0x600515bd: ('add', 'd2,a0'),
    0x60051078: ('mov', 'd1,d2'),
    0x60051079: ('mov', 'd0,d3'),
    0x6005107c: ('call', '0x6005393a,[d2,d3],16'),
    0x60051083: ('beq', '0x60051095'),
    0x60051095: ('mov', 'd3,d0'),
    0x60051097: ('mov', 'd2,d1'),
    # Initializer registers queue0x67 -> event flag74, bit4.
    0x602897bf: ('movhu', '(0x60040daa),d0'),
    0x602897c5: ('movhu', '(0x60040b8e),d1'),
    0x602897cb: ('exth', 'd0'), 0x602897cc: ('exth', 'd1'),
    0x602897cd: ('mov', '4,a0'),
    0x602897cf: ('call', '0x600515de,[d2,d3,a2],12'),
    0x600515f2: ('add', '-1569967244,a2'),
    0x600515fa: ('and', '4095,d0'),
    0x60051600: ('sub', 'd2,d0'),
    0x60051602: ('udfu01', '12,d0'),
    0x60051605: ('add', 'd0,a1'),
    0x60051607: ('mov', 'd1,(4,a1)'),
    0x6005160e: ('mov', 'a0,(8,a1)'),
    # The task's independent dispatch arms: mailbox bit1, queue0x67 bit4.
    0x6028988d: ('mov', '(40,sp),d0'),
    0x6028988f: ('btst', '1,d0'),
    0x602898ad: ('call', '0x6020c101,[a2],28'),
    0x6028992b: ('calls', '(a1)'),
    0x6028996f: ('call', '0x60289c5e,[d2,d3,a2],16'),
    0x60289979: ('jmp', '0x6028989d'),
    0x602899a5: ('mov', '(40,sp),d0'),
    0x602899a7: ('btst', '2,d0'),
    0x60289add: ('mov', '(40,sp),d0'),
    0x60289adf: ('btst', '4,d0'),
    0x60289ae7: ('movhu', '(0x60040daa),d0'),
    0x60289aee: ('call', '0x6020bfe7,[d2,d3],44'),
    0x60289b0e: ('movhu', '(0x60040daa),d0'),
    0x60289b14: ('mov', '(28,sp),a0'),
    0x60289b17: ('mov', '12,d1'), 0x60289b19: ('mov', '-1,a1'),
    0x60289b1f: ('call', '0x6020bf7a,[d2,d3],48'),
    0x60289b7f: ('mov', '(16,a0),a0'),
    0x60289b83: ('movhu', '(a0),d0'),
    0x60289b8d: ('mov', '(48,sp),d1'),
    0x60289b8f: ('cmp', 'd1,d0'),
    0x60289b92: ('mov', '(4,a0),a1'),
    0x60289b95: ('mov', '(28,sp),a0'),
    0x60289b97: ('calls', '(a1)'),
    0x60289bdc: ('call', '0x60289c5e,[d2,d3,a2],16'),
    0x6020bf84: ('call', '0x600513e6,[d2,d3,a2,a3],44'),
    0x60051467: ('call', '0x60036c8e,[d2,d3,a2,a3],32'),
    # The known event42 receiver obtains the node through the associated object.
    0x602a293c: ('mov', '(8,a0),d2'),
    0x602a2945: ('mov', 'd2,a0'),
    0x602a294a: ('mov', '(8,a0),a3'),
    0x602a29ff: ('mov', 'a3,a0'),
    0x602a2a00: ('call', '0x60022732,[],4'),
    0x602a2a0f: ('call', '0x60297328,[d2,d3,a2,a3],56'),
}
W.update({pc: DEFERRED_W[pc] for pc in (
    0x602ac3d7, 0x602ac3d9, 0x602ac3de, 0x602ac3f4, 0x602ac3f6)})
W.update({pc: PRODUCER_W[pc] for pc in (
    0x6020beb5, 0x6020beb7, 0x6020bebc, 0x6020bebe,
    0x60051550, 0x600515bf, 0x600515ca, 0x600515d1, 0x600515d4, 0x60051098)})
CHECKS = [
    (0x60040daa, '<H', (0x67,)), (0x60040cdc, '<H', (1,)),
    (0x60040b8e, '<H', (74,)),
    (0x6003b638, '<5I', (0x67, 0, 12, 256, 0)),
    (0x6042d814, '<I', (0x6042d28c,)),
    (0x6042d2ac, '<2I', (0x42, 0x602a2937)),
    (0x6042d2dc, '<2I', (0x4b, 0x602a281a)),
    (0x6042d2e4, '<2I', (0x4c, 0x602a2a66)),
]


def inspect(decoded, objdump):
    graph = NativeGraph(decoded, objdump, code_ranges=[
        (0x60289852, 0x60289c18), (0x602ac1e1, 0x602ac411),
        (0x602ad656, 0x602ad67a), (0x600515de, 0x60051615)])
    try:
        for pc, expected in W.items():
            actual = graph.instruction(pc)[2:]
            if actual != expected:
                raise ValueError(('controller event queue witness changed', hex(pc), expected, actual))
        for pc, fmt, expected in CHECKS:
            if struct.unpack_from(fmt, graph.data, pc-BASE) != expected:
                raise ValueError('controller queue data changed '+hex(pc))
        functions = [graph.function(pc) for pc in (0x60289852, 0x602ac1e1, 0x602ad656, 0x600515de)]
        producer = graph.function_instruction_addresses[0x602ac1e1]
        if not {0x602ac2e8, 0x602ac3de, 0x602ac3f6, 0x602ac40e}.issubset(producer):
            raise ValueError('producer no longer reaches send and source branches')
    finally:
        graph.close()
    return dict(scope=__doc__, checked_witnesses=len(W), checked_data_rows=len(CHECKS),
        producer=dict(entry='0x602ac1e1', event42_send='0x602ac2e8',
                      immediate_freeze='0x602ac3de', deferred_freeze='0x602ac3f6',
                      direct_event42_handler_call_at_send=False, callee_effects_are_frontiers=True),
        event_queue=dict(handle='0x67', constant='0x60040daa', boot_row='0x6003b638',
                         maximum_bytes=12, ring_bytes=256, packet=['status16', 'event32', 'associated32'],
                         send='0x60036ede', receive='0x60036c8e',
                         notification_event_flag=74, notification_mask=4,
                         receive_call='0x60289b1f', handler_call='0x60289b97'),
        mailbox=dict(handle=1, notification_mask=1, receive_call='0x602898ad',
                     handler_call='0x6028992b', known_events=['0x4b', '0x4c']),
        single_fifo_for_both_channels=False, normal_handler_call_must_return_before_loop_receive=True,
        event42_node_free='0x602a2a00', event42_associated_return='0x602a2a0f',
        functions=functions, native_executions=0, all_assertions_passed=True,
        source_lifetime_or_global_exclusion_proven=False, hash_checks_performed=False,
        firmware_modified=False, firmware_built=False, hardware_executed=False,
        limits=[
            'The normal controller call stack must return before its loop executes another receive; RTOS switches, exception callbacks and foreign direct calls are not simulated.',
            'No global ordering is inferred between mailbox1 and queue0x67, and boot configuration does not establish an immortal queue instance.',
            'Named send contains status normalization and notification. Neither notification nor a return value is treated as inline execution of event42.',
            'Finite CFGs expose external calls and UDF index instructions without emulating them. This is not an exhaustive alias or callback census.',
            'Already hooked destructive observers still have to revoke or quarantine before native release; unhooked writers and source ownership remain G1 obligations.'
        ])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded', type=Path, required=True)
    parser.add_argument('--objdump', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.decoded, args.objdump), indent=2))
