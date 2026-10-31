#!/usr/bin/env python3
"""Check two node-writing callbacks against the H/L ID/associated read fields.

Two complete native callback bodies on explicit live fixtures; no scheduler,
allocator, event delivery, concurrent execution or lifetime qualification.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_native_stack import BASE, NativeGraph
from ep7_sim_probe import run, brief, capture
from penf_emulator import Region

STACK, SP = 0x19010000, 0x19010200
NODE, ASSOCIATED, ENGINE = 0x19020000, 0x19021000, 0x19022000
PARAMETERS, DESCRIPTOR, AUX = 0x19023000, 0x19024000, 0x19025000
GLOBALS = 0x6223dd50
WINDOWS = [(0x602a334f, 0x602a33b3), (0x60555123, 0x60555155),
           (0x6029e8f1, 0x6029e956), (0x602a302b, 0x602a3042)]
W = {
    0x602a2f76: ('call', '0x602a334f,[d2,d3,a2,a3],20'),
    0x6010c059: ('calls', '(a1)'),
    0x602a334f: ('mov', 'a1,d3'),
    0x602a3351: ('cmp', '0,d3'),
    0x602a3353: ('beq', '0x602a33b0'),
    0x602a3355: ('clr', 'd0'), 0x602a3356: ('clr', 'd1'),
    0x602a3357: ('mov', '24,a3'), 0x602a3359: ('add', 'a0,a3'),
    0x602a335b: ('mov', '12,a2'), 0x602a335d: ('add', 'a1,a2'),
    0x602a335f: ('setlb', ''),
    0x602a3360: ('mov', '(a3),a1'), 0x602a3362: ('exthu', 'd0'),
    0x602a3363: ('add', 'd0,d0'), 0x602a3364: ('add', '292,a1'),
    0x602a3368: ('movhu', '(d0,a1),d2'),
    0x602a336a: ('inc', 'd1'), 0x602a336b: ('movhu', 'd2,(d0,a2)'),
    0x602a336d: ('mov', 'd1,d0'), 0x602a336e: ('exthu', 'd1'),
    0x602a336f: ('cmp', '8,d1'), 0x602a3371: ('llt', ''),
    0x602a3372: ('mov', '(24,a0),a1'),
    0x602a3375: ('mov', '28,a2'), 0x602a3377: ('add', 'd3,a2'),
    0x602a3379: ('mov', 'a2,a0'),
    0x602a337a: ('call', '0x60555123,[],0'),
    0x602a3381: ('mov', 'd3,a0'), 0x602a3383: ('mov', '(8,a0),a0'),
    0x602a3386: ('movbu', '(6,a0),d0'),
    0x602a3389: ('cmp', '1,d0'), 0x602a338b: ('bne', '0x602a33b0'),
    0x602a338f: ('movhu', 'd0,(0x6223dd5c)'),
    0x602a3398: ('movhu', 'd0,(0x6223dd5e)'),
    0x602a33a1: ('movhu', 'd0,(0x6223dd60)'),
    0x602a33aa: ('movhu', 'd0,(0x6223dd62)'),
    0x602a33b0: ('ret', '[d2,d3,a2,a3],20'),
    0x60555123: ('add', '164,a1'),
    0x60555128: ('mov', '131072,d1'),
    0x6055512f: ('lsr', '18,d0'),
    0x60555132: ('movhu', 'd0,(a0)'),
    0x6055513b: ('movhu', 'd0,(2,a0)'),
    0x60555145: ('movhu', 'd0,(4,a0)'),
    0x6055514f: ('movhu', 'd0,(6,a0)'),
    0x60555152: ('retf', '[],0'),
    0x6029e8f6: ('mov', '(8,a0),a2'),
    0x6029e8f9: ('mov', '(12,a0),a0'),
    0x6029e8fc: ('mov', '36,a1'), 0x6029e8fe: ('add', 'a2,a1'),
    0x6029e900: ('movhu', '(8,a1),d1'),
    0x6029e903: ('mov', '2,d2'), 0x6029e907: ('div', 'd2,d1'),
    0x6029e909: ('mov', 'mdr,d1'),
    0x6029e90d: ('beq', '0x6029e92c'),
    0x6029e90f: ('inc4', 'a0'),
    0x6029e913: ('movhu', '(0x6223dd6e),d2'),
    0x6029e919: ('add', '14,a1'),
    0x6029e91c: ('movhu', 'd1,(2,a1)'),
    0x6029e921: ('movhu', '(0x6223dd6c),d1'),
    0x6029e928: ('movhu', 'd2,(a1)'),
    0x6029e930: ('movhu', 'd1,(0x6223dd6e)'),
    0x6029e938: ('movhu', 'd1,(0x6223dd6c)'),
    0x6029e93e: ('mov', 'a2,a0'), 0x6029e93f: ('inc4', 'a0'),
    0x6029e942: ('or', '4,d1'), 0x6029e945: ('mov', 'd1,(a0)'),
    0x6029e946: ('mov', 'a2,a0'),
    0x6029e947: ('call', '0x602a302b,[],4'),
    0x6029e94d: ('movbu', 'd0,(0x6223dd51)'),
    0x6029e953: ('ret', '[d2,a2],12'),
    0x602a302b: ('mov', '(4,a0),d1'),
    0x602a302e: ('and', '36,d1'),
    0x602a3031: ('cmp', '36,d1'),
    0x602a3033: ('bne', '0x602a303f'),
    0x602a3038: ('call', '0x6020c0f0,[],16'),
}


def inspect(decoded, objdump, engine):
    graph = NativeGraph(decoded, objdump, code_ranges=WINDOWS)
    try:
        for pc, expected in W.items():
            if graph.instruction(pc)[2:] != expected:
                raise ValueError('node callback witness changed '+hex(pc))
        functions = [graph.function(entry) for entry in (0x602a334f, 0x60555123, 0x6029e8f1, 0x602a302b)]
        # Keep the finite body/frontier distinction visible, including the event
        # delivery branch that the selected completion fixture does not take.
        boundaries = [b for f in functions for b in f['boundaries']]
        if [(b['site'], b['operands']) for b in boundaries] != [('0x602a3038', '0x6020c0f0,[],16')]:
            raise ValueError('node callback control frontier changed')
        data = graph.data
    finally:
        graph.close()
    code = [Region('code_'+hex(lo), lo, data[lo-BASE:hi-BASE], 'rx') for lo, hi in WINDOWS]
    code += [Region('stage_call', 0x602a2f76, data[0x602a2f76-BASE:0x602a2f7b-BASE], 'rx'),
             Region('completion_call', 0x6010c059, data[0x6010c059-BASE:0x6010c05b-BASE], 'rx')]
    node = bytearray(b'\x5a'*56)
    struct.pack_into('<3I', node, 0, 7, 0, ASSOCIATED)
    struct.pack_into('<H', node, 44, 1)
    associated = bytearray(12); associated[6] = 1
    stock_engine = bytearray(28); struct.pack_into('<I', stock_engine, 24, PARAMETERS)
    parameters = bytearray(308)
    scalars = (0, 131072, 393216, (17 << 18)+1)
    struct.pack_into('<4I', parameters, 164, *scalars)
    coordinates = tuple(range(101, 109))
    struct.pack_into('<8H', parameters, 292, *coordinates)
    globals_before = bytearray(b'\xa5'*32)
    struct.pack_into('<2H', globals_before, 28, 100, 200)

    def regions(node_bytes, global_bytes):
        return code + [Region('node', NODE, bytes(node_bytes), 'rw', True),
            Region('associated', ASSOCIATED, bytes(associated)),
            Region('engine', ENGINE, bytes(stock_engine)),
            Region('parameters', PARAMETERS, bytes(parameters)),
            Region('globals', GLOBALS, bytes(global_bytes), 'rw', True),
            Region('stack', STACK, b'\xa5'*1024, 'rw', True)]

    stage = run(engine, regions(node, globals_before),
                dict(pc=0x602a2f76, sp=SP, a0=ENGINE, a1=NODE), stop=0x602a2f7b, limit=250)
    expected_node = bytearray(node)
    rounded = tuple((v+131072) >> 18 for v in scalars)
    struct.pack_into('<12H', expected_node, 12, *coordinates, *rounded)
    expected_globals = bytearray(globals_before)
    struct.pack_into('<4H', expected_globals, 12, *rounded)
    if (stage['status'] != 'returned' or stage['registers']['sp'] != SP
            or capture(stage, 'node') != expected_node or capture(stage, 'globals') != expected_globals):
        raise ValueError(('stage callback changed unexpected bytes', brief(stage)))

    descriptor = bytearray(16); struct.pack_into('<2I', descriptor, 8, NODE, AUX)
    aux = bytearray(8); struct.pack_into('<2H', aux, 4, 7, 11)
    completion_regions = regions(node, globals_before) + [
        Region('descriptor', DESCRIPTOR, bytes(descriptor)), Region('aux', AUX, bytes(aux))]
    completion = run(engine, completion_regions,
        dict(pc=0x6010c059, sp=SP, a0=DESCRIPTOR, a1=0x6029e8f1, d0=0),
        stop=0x6010c05b, limit=100)
    expected_node = bytearray(node)
    struct.pack_into('<I', expected_node, 4, 4)
    struct.pack_into('<2H', expected_node, 50, 107, 211)
    expected_globals = bytearray(globals_before); expected_globals[1] = 0
    if (completion['status'] != 'returned' or completion['registers']['sp'] != SP
            or capture(completion, 'node') != expected_node or capture(completion, 'globals') != expected_globals):
        raise ValueError(('type39 callback changed unexpected bytes', brief(completion)))
    return dict(scope=__doc__, checked_witnesses=len(W), functions=functions,
        introduced_node_reads=[dict(offset=0, bytes=4), dict(offset=8, bytes=4)],
        stage=dict(entry='0x602a334f', node_writes=[dict(offset=12, bytes=16), dict(offset=28, bytes=8)],
                   associated_flag=1, execution=brief(stage)),
        type39=dict(entry='0x6029e8f1', node_writes=[dict(offset=4, bytes=4), dict(offset=50, bytes=4)],
                    sequence=1, event4c_emitted=False, execution=brief(completion)),
        all_other_node_bytes_unchanged=True, native_source_regions_read_only=True,
        private_hl_or_capture_region_unmapped=True, instructions_emulated=True,
        allocator_and_scheduler_unmapped=True, all_assertions_passed=True,
        native_lifetime_or_exclusion_proven=False, hash_checks_performed=False,
        firmware_modified=False, firmware_built=False, hardware_executed=False,
        limits=[
            'Each explicit node and associated allocation stays live throughout its execution. No concurrent interrupt or retirement is injected.',
            'The stage execution selects associated flag1; the type39 execution selects odd sequence1 and flags without0x20, so event4c delivery is not entered.',
            'Other static branches remain in the recorded finite CFG; its event-delivery boundary is not a lifetime or cancellation proof.',
            'Only these two callbacks and the named helper are classified. Other writers, engine callbacks, release aliases and source ownership remain separate obligations.'
        ])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded', type=Path, required=True)
    parser.add_argument('--objdump', type=Path, required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.decoded, args.objdump, args.engine), indent=2))
