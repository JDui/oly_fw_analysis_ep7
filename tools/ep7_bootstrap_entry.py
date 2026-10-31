#!/usr/bin/env python3
"""Audit the domain0 startup seam before pipeline tasks are started; no image edits."""
import argparse
import json
import struct
import subprocess
from pathlib import Path

from ep7_request_ownership import require_instruction

BASE = 0x60020020
SEAM = 0x60191371
GROUPS = {
    'kernel_configuration_order': (0x600326a7, 0x600326fc, {
        0x600326b1: ('call', '0x600360b5,[a2,a3],8'),
        0x600326c5: ('call', '0x60032945,[],4'),
        0x600326ed: ('call', '0x600327a2,[d2,a2,a3],16'),
        0x600326f7: ('call', '0x6003271f,[a2],8'),
    }),
    'configured_object_dispatch': (0x60032945, 0x60032998, {
        0x60032945: ('call', '0x60032998,[d2,a2,a3],16'),
        0x60032968: ('call', '0x60032c6b,[d2,a2,a3],16'),
        0x60032995: ('ret', '[],4'),
    }),
    'actual_task_table_consumer': (0x60032998, 0x600329f4, {
        0x60032998: ('mov', '(0x8050),d0'),
        0x6003299b: ('mov', '-1880096764,a1'),
        0x600329a1: ('asl2', 'd0'),
        0x600329a2: ('mov', '(d0,a1),a0'),
        0x600329a4: ('mov', '(124,a0),a2'),
        0x600329ad: ('mov', '(204,a0),d2'),
        0x600329b1: ('movhu', '(a2),d0'),
        0x600329b7: ('and', '4095,d0'),
        0x600329bb: ('asl2', 'd0'),
        0x600329ca: ('movhu', 'd0,(16,a0)'),
        0x600329cf: ('inc4', 'a1'),
        0x600329d0: ('add', '68,a0'),
        0x600329d2: ('mov', '-6,d1'),
        0x600329d5: ('mov', '(a1),d0'),
        0x600329d7: ('mov', 'd0,(a0)'),
        0x600329dd: ('call', '0x60030afa,[d2,a2,a3],16'),
        0x600329ed: ('add', '28,a2'),
    }),
    'actual_queue_table_consumer': (0x60032c6b, 0x60032cc7, {
        0x60032c6b: ('mov', '(0x8050),d0'),
        0x60032c77: ('mov', '(156,a0),a2'),
        0x60032c81: ('mov', '(232,a0),d2'),
        0x60032c85: ('movhu', '(a2),d0'),
        0x60032c8b: ('and', '4095,d0'),
        0x60032c9e: ('movhu', 'd0,(a0)'),
        0x60032ca3: ('add', '20,a0'),
        0x60032ca5: ('mov', '-4,d1'),
        0x60032ca8: ('mov', '(a1),d0'),
        0x60032caa: ('mov', 'd0,(a0)'),
        0x60032cb0: ('call', '0x60030c4c,[d2,a2,a3],16'),
        0x60032cc0: ('add', '20,a2'),
    }),
    'controller_init_before_usr3_start': (0x60190ee7, 0x60190f02, {
        0x60190eee: ('call', '0x602897a8,[],4'),
    }),
    'usr3_start': (0x601911e2, 0x601911f0, {
        0x601911e2: ('movhu', '(0x60040932),d0'),
        0x601911e8: ('exth', 'd0'),
        0x601911e9: ('call', '0x60051873,[d2,d3],24'),
    }),
    'usr3_entry_and_candidate': (0x601912fb, 0x6019137f, {
        0x601912fb: ('movm', '[d2,d3],(sp)'),
        0x601912fd: ('add', '-36,sp'),
        0x6019131a: ('mov', '(0xa272e3e8),d0'),
        0x60191320: ('btst', '4096,d0'),
        0x60191324: ('bne', '0x60191331'),
        0x60191328: ('call', '0x600313ef,[d2,a2,a3],16'),
        0x6019132f: ('bra', '0x6019131a'),
        0x60191345: ('mov', '3,d0'),
        0x60191347: ('call', '0x6004586c,[d2,d3],32'),
        0x6019135b: ('mov', '4,d0'),
        0x6019135d: ('call', '0x6004586c,[d2,d3],32'),
        SEAM: ('call', '0x6011f620,[],4'),
    }),
    'native_start_wrapper': (0x60051873, 0x600518a0, {
        0x60051875: ('call', '0x6005398a,[d2],12'),
        0x6005187b: ('beq', '0x6005188c'),
        0x6005187f: ('call', '0x60053cce,[d2,d3,a2],16'),
        0x6005188e: ('call', '0x6003071f,[d2,d3,a2],16'),
    }),
    'section9_candidate_is_later': (0x60191b74, 0x60191bdc, {
        0x60191b74: ('movm', '[d2],(sp)'),
        0x60191ba0: ('mov', '7,d0'),
        0x60191ba2: ('call', '0x6004586c,[d2,d3],32'),
        0x60191bb6: ('mov', '8,d0'),
        0x60191bb8: ('call', '0x6004586c,[d2,d3],32'),
        0x60191bcc: ('mov', '9,d0'),
        0x60191bce: ('call', '0x6004586c,[d2,d3],32'),
        0x60191bd5: ('call', '0x60cc0e4a,[d2,d3,a2,a3],28'),
    }),
}
# ROM task row, entry, configured ID, priority, stack; row consumer is above.
TASKS = [
    (0x60038ebc, 0x601912fb, 0x2d, 55, 2048),
    (0x60038e68, 0x60191b74, 0x2a, 55, 2048),
    (0x60038ed8, 0x60044d1a, 0x2e, 55, 512),
    (0x6003c4ac, 0x60044f11, 0x1016, 55, 512),
    (0x6003d574, 0x60044f97, 0x2015, 55, 512),
    (0x60038d6c, 0x603ef892, 0x21, 55, 4752),
    (0x60039354, 0x603ef94a, 0x57, 46, 4096),
    (0x600395a0, 0x603f26a1, 0x6c, 26, 8192),
    (0x60038d50, 0x603df803, 0x20, 54, 4096),
    (0x60039664, 0x60289852, 0x73, 25, 4096),
]
# Exact adjacent MOVHU/EXTH/CALL triplets in the Usr3 task.
STARTS = [
    (0x60191554, 0x6004091a, 0x21),
    (0x6019158a, 0x60040986, 0x57),
    (0x60191611, 0x600409b0, 0x6c),
    (0x6019167d, 0x60040918, 0x20),
    (0x60191907, 0x600409be, 0x73),
    (0x60191a18, 0x60040930, 0x2c),
    (0x60191a40, 0x6004092c, 0x2a),
]


def inspect(decoded, objdump):
    main = decoded.read_bytes()
    if len(main) != 26214336:
        raise ValueError('unsupported decoded main length')
    groups = dict(GROUPS)
    for pc, cell, tid in STARTS:
        if struct.unpack_from('<H', main, cell-BASE)[0] != tid:
            raise ValueError('task ID cell changed')
        groups['start_'+hex(tid)] = (pc, pc+14, {
            pc: ('movhu', f'({cell:#x}),d0'), pc+6: ('exth', 'd0'),
            pc+7: ('call', '0x60051873,[d2,d3],24')})
    witnesses = []
    for name, (start, end, rows) in groups.items():
        asm = subprocess.check_output([str(objdump), '-D', '-z', '-b', 'binary', '-m', 'mn10300',
            '--insn-width=16', f'--adjust-vma={BASE:#x}', f'--start-address={start:#x}',
            f'--stop-address={end:#x}', str(decoded)], text=True)
        for pc, (mnemonic, operands) in rows.items():
            require_instruction(asm, pc, mnemonic, operands)
            witnesses.append(dict(group=name, address=hex(pc), mnemonic=mnemonic, operands=operands))
    tasks = []
    for row, entry, tid, priority, stack in TASKS:
        if struct.unpack_from('<7I', main, row-BASE) != (tid, 0, 0, entry, priority, stack, 0):
            raise ValueError('configured task row changed: '+hex(row))
        tasks.append(dict(row=hex(row), entry=hex(entry), tid=hex(tid), domain=tid>>12,
                          priority=priority, configured_stack_bytes=stack))
    # root0+124 really names this task table; root0+156 names the queue table.
    pointers = {0x60041220: 0x600389d0, 0x60041240: 0x6003ad78}
    for address, value in pointers.items():
        if struct.unpack_from('<I', main, address-BASE)[0] != value:
            raise ValueError('kernel configuration pointer changed')
    seam_bytes = bytes.fromhex('ddafe2f8ff0004')
    if main[SEAM-BASE:SEAM-BASE+7] != seam_bytes:
        raise ValueError('bootstrap CALL bytes changed')
    return dict(scope=__doc__, checked_instruction_count=len(witnesses), instructions=witnesses,
        configured_tasks=tasks,
        kernel_root0='0x600411a4', task_table='0x600389d0', queue_table='0x6003ad78',
        tcb_copy=dict(source_offsets=[4, 8, 12, 16, 20, 24],
                      destination_offsets=[68, 72, 76, 80, 84, 88]),
        candidate=dict(site=hex(SEAM), original_target='0x6011f620', original=seam_bytes.hex(),
            save_mask=0, native_frame_bytes=4, continuation='0x60191378',
            task_entry='0x601912fb', task_id='0x2d', configured_stack_bytes=2048,
            locally_after_section_initializers=[3, 4], approved_for_installation=False),
        subsequent_starts=[dict(load_site=hex(pc), call_site=hex(pc+7), id_cell=hex(cell), tid=hex(tid))
                           for pc, cell, tid in STARTS],
        rejected_publication_candidates=[
            dict(site='0x600451f2', reason='Domain2 loader; private runtime requires domain0; 512-byte stack.'),
            dict(site='0x60191bd5', reason='Usr5 is started after pipeline tasks; existing receive bridges require publication.')],
        publication_phases=dict(early_resident_sections=[1, 2, 3, 4],
            early_groups=['kernel inline gates', 'capture initialization and calls', 'pipeline calls/frames/queues', 'CPU COLOR'],
            later_section6_groups=['UI owner', 'MVC/content', 'selector', 'input'],
            later_ui_bytes_must_not_be_read_by_early_publication=True),
        limits=['Local native order and configured rows; transitive calls, alternate task starts and cancellation are not closed.',
            '6005b447 is not used as the creation proof; the kernel initialization consumer is60032998.',
            'Loader/initializer flags are attempts/local completion, not transfer integrity or cache visibility.',
            'Live task/queue views, full stack, early code/RAM ownership and whole cold installation remain required.',
            'No bootstrap implementation is installed or executed by this static probe.'],
        firmware_modified=False, firmware_built=False, camera_executed=False, hash_checks_performed=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded', type=Path, required=True)
    parser.add_argument('--objdump', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.decoded, args.objdump), indent=2))
