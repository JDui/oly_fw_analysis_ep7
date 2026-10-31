#!/usr/bin/env python3
"""Bind one conditional TOP trigger chain and its borrowed engine completion.

Static exact-instruction/table checks only. No scheduling, allocator, resource
release, callback execution or whole-program lifetime claim.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_native_stack import BASE, NativeGraph
from ep7_type7_work_queue import W as QUEUE_W

W = {
    # Lower type92 -> sensor command71, inside the existing priority wrapper.
    0x6014dc6c: ('add', '-4,d1'),
    0x6014dc6e: ('mov', '1612490664,a2'),
    0x6014dc97: ('mov', '(4,a1),a1'),
    0x6014dc9a: ('jmp', '(a1)'),
    0x6014dccd: ('call', '0x6014dfb8,[],4'),
    0x6014dfb8: ('mov', '71,d0'),
    0x6014dfba: ('mov', '1611983652,a1'),
    0x6014dfc0: ('call', '0x6014e67c,[d2,d3,a2,a3],36'),
    0x6014e683: ('mov', 'd0,d2'),
    0x6014e684: ('mov', '28,d0'),
    0x6014e686: ('call', '0x6011cc05,[d2,d3,a2],28'),
    0x6014e69c: ('movhu', 'd2,(a0)'),
    0x6014e6c9: ('mov', 'd0,(12,a0)'),
    0x6014e6d0: ('mov', 'd0,(16,a0)'),
    0x6014e6d3: ('mov', '2,d0'),
    0x6014e6d5: ('call', '0x6006a922,[d2],8'),
    0x6014e6dc: ('mov', 'd0,(16,sp)'),
    0x6014e703: ('mov', '(4,sp),a0'),
    0x6014e705: ('call', '0x6013015a,[a2],16'),
    0x6014e726: ('mov', '(16,sp),d0'),
    0x6014e728: ('call', '0x6006a96b,[d2],8'),
    0x6014e731: ('ret', '[d2,d3,a2,a3],36'),
    # Sensor command71 -> helper -> conditional lower type85 operation.
    0x60130179: ('add', '-2,d1'),
    0x6013017b: ('mov', '1612424988,a1'),
    0x601301a6: ('mov', '(4,a0),a1'),
    0x601301a9: ('jmp', '(a1)'),
    0x60130226: ('mov', 'a2,a0'),
    0x60130227: ('call', '0x601307b3,[a2,a3],12'),
    0x601307b3: ('mov', 'a0,a3'),
    0x601307b4: ('mov', '24,d0'),
    0x601307b9: ('call', '0x6011cc05,[d2,d3,a2],28'),
    0x601307cb: ('mov', '1611859937,d0'),
    0x601307d1: ('mov', 'd0,(16,a2)'),
    0x601307d4: ('mov', 'a3,(20,a2)'),
    0x601307d7: ('mov', 'a2,a0'),
    0x601307d8: ('call', '0x60137df6,[],4'),
    0x60137df6: ('mov', '1,d0'),
    0x60137df8: ('call', '0x60136337,[d2,d3,a2,a3],112'),
    0x60136347: ('mov', '(0x621f4a7c),a1'),
    0x6013634e: ('movhu', '(4,a1),d0'),
    0x60136351: ('cmp', '3,d0'),
    0x60136353: ('bne', '0x60136358'),
    0x60136355: ('jmp', '0x601363f9'),
    0x60136362: ('bne', '0x601363b5'),
    0x6013636a: ('bne', '0x601363b5'),
    0x60136374: ('bne', '0x601363b5'),
    0x601363b5: ('mov', '136,d0'),
    0x601363bb: ('call', '0x6011cc05,[d2,d3,a2],28'),
    0x601363c3: ('mov', '85,d0'),
    0x601363c5: ('movhu', 'd0,(a2)'),
    0x601363c7: ('call', '0x6014dbfb,[d2,d3,a2,a3],20'),
    0x601363d5: ('bne', '0x601363df'),
    0x601363d7: ('mov', 'a2,a0'),
    0x601363d8: ('call', '0x6014dc5a,[d2,a2],20'),
    # Lower type85 creates a stack request of upper type135, then dispatches it.
    0x6014dcbf: ('call', '0x6014def0,[d2,a2],188'),
    0x6014def0: ('mov', 'sp,a2'),
    0x6014def1: ('add', '12,a2'),
    0x6014def3: ('mov', '135,d0'),
    0x6014def6: ('movhu', 'd0,(12,sp)'),
    0x6014defa: ('call', '0x601e77c0,[d2,a2],12'),
    0x6014df05: ('bne', '0x6014df0f'),
    0x6014df07: ('mov', 'a2,a0'),
    0x6014df08: ('call', '0x601e77d8,[d2,d3,a2],32'),
    0x601e780b: ('cmp', '135,d1'),
    0x601e780f: ('beq', '0x601e7817'),
    0x601e7829: ('add', '-4,d1'),
    0x601e782b: ('mov', '1612631164,a1'),
    0x601e7855: ('mov', '(4,a0),a0'),
    0x601e7858: ('jmp', '(a0)'),
    # Threshold helper changes only the LM field, conditionally. This is not a
    # proof that nested callees preserve that field or exclude every IRQ/domain.
    0x6006a950: ('mov', 'd2,d0'),
    0x6006a951: ('call', '0x60054d9f,[],0'),
    0x6006a960: ('mov', 'd2,d0'),
    0x6006a961: ('call', '0x60054d9f,[],0'),
    0x60054d9f: ('mov', 'psw,d1'),
    0x60054da1: ('mov', 'd1,a1'),
    0x60054da3: ('and', '1792,d1'),
    0x60054da7: ('asl', '8,d0'),
    0x60054dab: ('bls', '0x60054dbb'),
    0x60054daf: ('and', '-1793,d1'),
    0x60054db5: ('or', 'd0,d1'),
    0x60054db7: ('mov', 'd1,psw'),
    # The type135 consumer submits a new descriptor borrowing the old engine.
    0x601200fd: ('mov', '98311,d0'),
    0x60120d73: ('mov', 'a0,a2'),
    0x60120d74: ('mov', 'd0,(12,sp)'),
    0x60120d77: ('mov', '136,d0'),
    0x60120d7d: ('call', '0x6011cc05,[d2,d3,a2],28'),
    0x60120d82: ('mov', 'a0,a3'),
    0x60120d8b: ('mov', '136,d1'),
    0x60120d8e: ('call', '0x4700115e,[d2,a2],8'),
    0x60120d95: ('mov', '(12,sp),d0'),
    0x60120d98: ('and', '-32769,d0'),
    0x60120da0: ('and', '-65537,d0'),
    0x60120da6: ('movhu', 'd0,(a3)'),
    0x60120da8: ('call', '0x6014dbfb,[d2,d3,a2,a3],20'),
    0x60120db8: ('mov', '(12,sp),d0'),
    0x60120dba: ('btst', '65536,d0'),
    0x60120dc0: ('beq', '0x60120dcb'),
    0x60120dc2: ('mov', '1611795628,d0'),
    0x60120dc8: ('mov', 'd0,(64,a2)'),
    0x60120dcb: ('mov', 'a2,a1'),
    0x60120dcc: ('inc4', 'a1'),
    0x60120dd2: ('mov', 'a1,(8,a3)'),
    0x60120dd9: ('mov', 'a2,(20,a3)'),
    0x60120ddc: ('mov', '1611796654,d0'),
    0x60120de2: ('mov', 'd0,(24,a3)'),
    0x60120df0: ('cmp', '7,d0'),
    0x60120df4: ('cmp', '139,d0'),
    0x60120dfa: ('mov', '1611796928,d0'),
    0x60120e03: ('mov', 'd0,(28,a3)'),
    0x60120ea1: ('call', '0x6014dc5a,[d2,a2],20'),
    0x60120ead: ('bne', '0x60120eb7'),
    0x60120eaf: ('mov', '(12,sp),d0'),
    0x60120eb1: ('btst', '32768,d0'),
    0x60120eb5: ('bne', '0x60120eec'),
    0x60120eba: ('mov', 'a3,a0'),
    0x60120ebb: ('call', '0x6011ce6a,[d2,d3,a2],24'),
    # Completion fetches the engine's CURRENT callback from engine+64.
    0x601210b3: ('mov', 'a0,a3'),
    0x601210b4: ('mov', '(20,a3),a2'),
    0x601210b9: ('cmp', '0,d1'),
    0x601210bd: ('cmp', '14994,d1'),
    0x601210c3: ('call', '0x6014dc2d,[a2],8'),
    0x601210ca: ('movhu', '(a3),d1'),
    0x601210cc: ('cmp', '6,d1'),
    0x601210ce: ('bne', '0x601210ef'),
    0x601210ef: ('mov', '64,a1'),
    0x601210f1: ('add', 'a2,a1'),
    0x601210f3: ('mov', '(a1),d1'),
    0x601210f6: ('beq', '0x601210fe'),
    0x601210f8: ('mov', '(a1),a1'),
    0x601210fa: ('exthu', 'd0'),
    0x601210fb: ('mov', 'a2,a0'),
    0x601210fc: ('calls', '(a1)'),
    0x601211af: ('mov', '(28,a3),a1'),
    0x601211b4: ('bne', '0x601211bd'),
    0x601211b8: ('call', '0x6011ce6a,[d2,d3,a2],24'),
    # Resource-release-dependent descriptor cleanup is a separate frontier.
    0x6014dc3a: ('mov', '(112,a2),a0'),
    0x6014dc3d: ('call', '0x6014fb57,[d2,d3,a2],24'),
    0x6014dc45: ('bne', '0x6014dc56'),
    0x6014dc47: ('mov', '28,a1'),
    0x6014dc49: ('add', 'a2,a1'),
    0x6014dc53: ('mov', 'a2,a0'),
    0x6014dc54: ('calls', '(a1)'),
    0x601211c6: ('call', '0x6011ce6a,[d2,d3,a2],24'),
}
W.update({pc: QUEUE_W[pc] for pc in (
    0x601e78c5, 0x601200dd, 0x601200e2, 0x601200e4,
    0x6012011c, 0x60120122, 0x60120123)})

ROWS = [
    (0x601ca7c8, 81, 0x6014dcbf),  # lower85
    (0x601ca7e8, 88, 0x6014dccd),  # lower92
    (0x601ba774, 69, 0x60130226),  # sensor71
    (0x601eccac, 131, 0x601e78c4), # upper135
]


def inspect(decoded, objdump):
    graph = NativeGraph(decoded, objdump)
    try:
        for pc, expected in W.items():
            actual = graph.instruction(pc)[2:]
            if actual != expected:
                raise ValueError(('type7 completion witness changed', hex(pc), expected, actual))
        for pc, key, target in ROWS:
            if struct.unpack_from('<2I', graph.data, pc-BASE) != (key, target):
                raise ValueError('type7 trigger dispatch row changed '+hex(pc))
    finally:
        graph.close()
    return dict(scope=__doc__, checked_witnesses=len(W), checked_dispatch_rows=len(ROWS),
        trigger_route=[
            'lower92:6014dc5a -> 6014dfb8 -> 6014e67c',
            'sensor71:6013015a -> 601307b3 -> 60137df6 -> 60136337',
            'conditional lower85:601363d8 -> 6014dc5a -> 6014def0',
            'upper135:6014df08 -> 601e77d8 -> 601200aa -> TOP pop'],
        trigger_conditions=[
            'Original allocations, initializers and returning callees succeed.',
            'The object reached through621f4a7c has halfword+4 !=3.',
            'Optional preceding lower141 call returns to the reviewed branch.'],
        wrapper=dict(entry='0x6014e67c', priority_argument=2,
                     enter='0x6014e6d5', restore='0x6014e728',
                     leaf='0x60054d9f', conditional_psw_mask='0x0700',
                     all_callees_preserve_threshold_proven=False,
                     fixed_task_or_exclusive_completion_proven=False),
        processing_descriptor=dict(bytes=136, constructor='0x60120d73',
            fields={'8':'engine+4', '20':'original engine pointer',
                    '24':'0x601210ae', '28':'0x601211c0 for type7/type139'},
            normal_mode2_flags='0x8007', alternate_mode5_flags='0x18007',
            alternate_overwrites_engine_callback='0x60120cac',
            normal_preserves_engine_callback=True,
            engine_generation_carried=False, engine_deep_copy=False),
        completion=dict(entry='0x601210ae', engine_field=20,
            callback_read_from_engine_offset=64, call='0x601210fc',
            callback_argument='original engine pointer',
            current_callback_read=True, callback_captured_at_submission=False,
            resource_release_frontier='0x6014fb57',
            cleanup_or_cancellation_closed=False),
        static_checks_passed=True, native_executions=0,
        hash_checks_performed=False, firmware_modified=False,
        firmware_built=False, hardware_executed=False,
        limits=[
            'This is one conditional call chain, not a census of all type135/type149 producers or origins of lower92.',
            'The priority wrapper is observed at entry/restore only; helpers and callback bodies have no transitive PSW/exclusion proof.',
            'Raw engine pointers and late callback reads require native lifetime/identity contracts; no new H/L observer is added to these callbacks.',
            'Resource release and allocator semantics are not closed. The observed cleanup calls do not establish an original-firmware use-after-free.',
            'G1/G2/G3/G6/G8 remain open; use the introduced-read obligations to scope subsequent research.'
        ])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded', type=Path, required=True)
    parser.add_argument('--objdump', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.decoded, args.objdump), indent=2))
