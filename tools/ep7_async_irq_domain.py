#!/usr/bin/env python3
"""Join the known type39 scheduler route to domain0's class5 IRQ dispatch.

One native dispatcher-prefix execution with explicit pending-source/register
fixtures. No physical interrupt injection, nested scheduling or callback body.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_native_stack import BASE, NativeGraph
from ep7_async_dispatch import W as ASYNC_W
from ep7_irq_stack import W as IRQ_W
from ep7_sim_probe import run, brief, capture
from penf_emulator import Region

W = {
    # Register source29, priority class5, same consumer for selectors0/1/2.
    0x600683dd: ('mov', '1611040266,a2'),
    0x600683e3: ('mov', '29,d0'), 0x600683e5: ('mov', '5,d1'),
    0x600683e7: ('mov', 'a2,a0'), 0x600683e8: ('mov', '0,a1'),
    0x600683ea: ('call', '0x6006aa25,[d2],16'),
    0x600683ef: ('mov', '29,d0'), 0x600683f1: ('mov', '5,d1'),
    0x600683f3: ('mov', 'a2,a0'), 0x600683f4: ('mov', '1,a1'),
    0x600683f6: ('call', '0x6006aa25,[d2],16'),
    0x600683fb: ('mov', '29,d0'), 0x600683fd: ('mov', '5,d1'),
    0x600683ff: ('mov', '2,a1'), 0x60068401: ('mov', 'a2,a0'),
    0x60068402: ('call', '0x6006aa25,[d2],16'),
    0x6006aa25: ('mov', 'a1,d2'),
    0x6006aa27: ('mov', 'd1,(4,sp)'),
    0x6006aa29: ('mov', 'a0,(8,sp)'),
    0x6006aa2b: ('mov', 'sp,a0'), 0x6006aa2c: ('inc4', 'a0'),
    0x6006aa2e: ('mov', 'd2,d1'),
    0x6006aa2f: ('call', '0x60054fce,[d2,d3,a2,a3],24'),
    0x60054fce: ('mov', 'd0,d3'),
    0x60054fd8: ('mov', 'd1,d0'),
    0x60055025: ('asl2', 'd3'),
    0x60055034: ('mov', 'a0,a1'), 0x60055035: ('inc4', 'a1'),
    0x60055036: ('mov', '(a1),d0'),
    0x60055040: ('mov', '-1569937476,a1'),
    0x60055058: ('mov', '-1569936748,a1'),
    0x60055070: ('mov', '-1569936020,a1'),
    0x60055076: ('mov', 'd0,(d3,a1)'),
    0x60055078: ('mov', '(a0),d2'),
    0x60055081: ('asl', 'd0,d2'),
    0x600550ba: ('mov', 'd2,(a0)'),
    # Kernel reads its ROM class table and installs the configured callback.
    0x60032e45: ('mov', '(184,a0),a2'),
    0x60032e49: ('mov', 'a2,a0'), 0x60032e4a: ('inc4', 'a0'),
    0x60032e52: ('movhu', '(a2),d0'),
    0x60032e55: ('call', '0x600331e4,[a2],4'),
    0x60032e65: ('add', '12,a2'),
    0x60033238: ('mov', '(88,a1),a1'),
    0x6003323b: ('mov', '(4,a0),d1'),
    0x6003323e: ('asl2', 'd0'),
    0x6003323f: ('mov', 'd1,(d0,a1)'),
    # The existing IRQ entry reaches the handler through PSW class bits.
    0x60038748: ('mov', 'psw,d1'), 0x6003874a: ('lsr', '6,d1'),
    0x6003874d: ('and', '28,d1'),
    0x60038750: ('mov', '(88,a2),a0'),
    0x60038753: ('mov', '(d1,a0),a0'),
    0x60038765: ('calls', '(a0)'),
    # Domain0 class5 high-source branch explicitly reenables interrupts.
    0x60054e14: ('movhu', '(0x8a00),d0'),
    0x60054e17: ('cmp', '52,d0'), 0x60054e19: ('bhi', '0x60054e22'),
    0x60054e22: ('or', '2048,psw'),
    0x60054e26: ('mov', '-1725955308,a2'),
    0x60054e2c: ('mov', '(a2),d0'),
    0x60054e31: ('mov', '1,d2'),
    0x60054e33: ('mov', 'd0,d1'),
    0x60054e34: ('lsr', '2,d1'),
    0x60054e37: ('sub', 'd2,d1'), 0x60054e39: ('asl2', 'd1'),
    0x60054e3a: ('mov', '-1569937476,a0'),
    0x60054e40: ('mov', '(d1,a0),a0'),
    0x60054e42: ('calls', '(a0)'),
    # Source29 consumer selects the same ring as publication using8050.
    0x6006860d: ('mov', '(0x8050),d0'),
    0x60068610: ('mov', 'd0,(4,sp)'),
    0x60068614: ('mov', '29,d0'),
    0x60068617: ('call', '0x6006aa60,[],4'),
    0x6006861e: ('cmp', '0,d0'),
    0x60068622: ('mov', '1644412512,a0'),
    0x6006862c: ('cmp', '1,d0'),
    0x60068630: ('mov', '-1569627976,a0'),
    0x60068638: ('mov', '-1569625624,a0'),
    0x6006863e: ('call', '0x600686e2,[d2,d3,a2,a3],24'),
}
# Reuse previously reviewed witnesses only where the joined chain consumes them.
W.update({pc: ASYNC_W[pc] for pc in (
    0x6011213b, 0x60112142, 0x60112143,
    0x600684ce, 0x600684da, 0x600684e9, 0x600684f2,
    0x60068503, 0x60068506, 0x6006850d,
    0x60068702, 0x60068704, 0x60068707, 0x6006870a)})
W.update({pc: IRQ_W[pc] for pc in (0x60038743, 0x60038746)})
CHECKS = [(0x600411a4 + 184, '<I', (0x6003c13c,)),
          (0x600411a4 + 88, '<I', (0x621a6410,)),
          (0x6003c148, '<3I', (5, 0, 0x60054e0f))]


def inspect(decoded, objdump, engine):
    graph = NativeGraph(decoded, objdump)
    try:
        for pc, expected in W.items():
            if graph.instruction(pc)[2:] != expected:
                raise ValueError(('IRQ domain witness changed', hex(pc), expected))
        data = graph.data
        for pc, fmt, expected in CHECKS:
            if struct.unpack_from(fmt, data, pc - BASE) != expected:
                raise ValueError('IRQ class table changed '+hex(pc))
    finally:
        graph.close()

    # Execute the actual class5 dispatcher to source29's consumer entry. These
    # source/register values select the reviewed branch; no device is emulated.
    stack = bytes([0xa5]) * 256
    sp = 0x19010080
    regions = [
        Region('stock_class5', 0x60054e0f, data[0x60054e0f-BASE:0x60054e52-BASE], 'rx'),
        Region('irq_code_fixture', 0x8a00, struct.pack('<H', 53)),
        Region('pending_source_fixture', 0x99200314, struct.pack('<I', 4*(29+1))),
        Region('registered_callback_fixture', 0xa26ca7bc+29*4, struct.pack('<I', 0x6006860a)),
        Region('stack_fixture', 0x19010000, stack, 'rw', True),
    ]
    result = run(engine, regions, dict(pc=0x60054e0f, sp=sp, psw=0x500),
                 stop=0x6006860a, limit=50)
    if (result['status'] != 'returned' or result['registers']['a0'] != 0x6006860a
            or result['registers']['psw'] & 0xf00 != 0xd00
            or result['trace'][-1]['pc'] != 0x60054e42):
        raise ValueError(('class5 did not dispatch source29', brief(result)))
    changed = [i for i, (a, b) in enumerate(zip(stack, capture(result, 'stack_fixture'))) if a != b]
    if any(not sp-16 <= 0x19010000+i < sp for i in changed):
        raise ValueError('dispatcher wrote outside its reviewed local/call frame')
    return dict(scope=__doc__, checked_witnesses=len(W), checked_data_rows=len(CHECKS),
        source_number=29, priority_class=5, consumer='0x6006860a', reader='0x600686e2',
        rings={'0':'0x6203be60','1':'0xa27160b8','2':'0xa27169e8'},
        callback_tables={'0':'0xa26ca7bc','1':'0xa26caa94','2':'0xa26cad6c'},
        domain0_root='0x600411a4', class_table='0x6003c13c',
        class5_handler='0x60054e0f', execution=brief(result),
        final_psw=hex(result['registers']['psw']),
        irq_handler_reenables_interrupts_before_queue_consumer=True,
        type39_first_stage_is_controller_task_callback=False,
        writer_and_reader_use_same_selector_mapping=True,
        other_core_handler_paths_qualified=False,
        type39_second_stage_same_context_proven=False,
        type7_type39_completion_serialization_proven=False,
        all_assertions_passed=True, hash_checks_performed=False,
        firmware_modified=False, firmware_built=False, hardware_executed=False,
        limits=[
            'Only initialized stock domain0 bindings join the ROM/kernel/interrupt route; alternate table writers and other core dispatchers remain outside this check.',
            'The single native execution begins in the dispatcher with synthetic registers/pending-source/table values and stops at the consumer entry.',
            'Physical IRQ delivery, source acknowledgement, preemption and reentrancy are not simulated. The reader/callback bodies are not executed.',
            'The conditional second stage and type7 completion have separate contexts still to qualify; this result is not a global serialization proof.'
        ])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded', type=Path, required=True)
    parser.add_argument('--objdump', type=Path, required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.decoded, args.objdump, args.engine), indent=2))
