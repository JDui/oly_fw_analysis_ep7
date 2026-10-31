#!/usr/bin/env python3
"""Exercise the proposed domain-2 pool bound in memory, using the existing engine.

No output firmware, service stubs, board model, hashing or whole-boot claim.
Original native lock/multiply/bitmap/free instructions execute on explicit data.
"""
import argparse
import json
from pathlib import Path
import struct

from penf_emulator import Region, execute
from ep7_native_stack import BASE, NativeGraph
from ep7_ram_ownership import W as RAM_W
from ep7_sim_probe import brief, capture

CALLER = 0x19000000
STOP = CALLER + 7
STACK = 0x19010000
SP = STACK + 256
STATE = 0x62668c00
STATE_SIZE = 0x348
POOL = 0x61d58540
STRIDE = 0x4040
COUNTER = 8
RECYCLED = 20
RECYCLE_WORDS = 0x2d8
BITMAP = 0x344
ALLOC = 0x600228b6
FREE = 0x60022b23
DIAGNOSTICS = (0x6002247c, 0x60022694, 0x60022dcd)
SEGMENTS = [('pool', ALLOC, 0x60022dcd, 'rx'),
            ('locks', 0x6006a922, 0x6006a9aa, 'rx'),
            ('psw', 0x60054d9f, 0x60054dc7, 'rx'),
            ('tables', 0x60026dd0, 0x60026e44, 'r')]
EDITS = [(0x600229b9, bytes.fromhex('8020'), bytes.fromhex('801f')),
         (0x60022c28, bytes.fromhex('8f20'), bytes.fromhex('8f1f'))]


def put(state, offset, value, fmt='<I'):
    state = bytearray(state)
    struct.pack_into(fmt, state, offset, value)
    return bytes(state)


def state_for(counter, bitmap, recycled=()):
    result = put(bytes(STATE_SIZE), COUNTER, counter)
    result = put(result, BITMAP, bitmap)
    result = put(result, RECYCLED, len(recycled))
    for index, slot in enumerate(recycled):
        result = put(result, RECYCLE_WORDS + 2 * index, slot, '<H')
    return result


def state_brief(state):
    return dict(next_index=struct.unpack_from('<I', state, COUNTER)[0],
                recycled_count=struct.unpack_from('<I', state, RECYCLED)[0],
                first_recycled_index=struct.unpack_from('<H', state, RECYCLE_WORDS)[0],
                allocated_bitmap=hex(struct.unpack_from('<I', state, BITMAP)[0]))


def native_call(data, engine, state, entry, *, candidate=True, address=0):
    regions = []
    for name, lo, hi, permissions in SEGMENTS:
        code = bytearray(data[lo-BASE:hi-BASE])
        if candidate and name == 'pool':
            for pc, before, after in EDITS:
                if code[pc-lo:pc-lo+len(before)] != before:
                    raise ValueError('reservation operand changed')
                code[pc-lo:pc-lo+len(before)] = after
        regions.append(Region(name, lo, bytes(code), permissions))
    frame = 36 if entry == ALLOC else 40
    caller = b'\xdd' + struct.pack('<i', entry-CALLER) + bytes([0xf0, frame])
    regions += [Region('synthetic_caller', CALLER, caller, 'rx'),
                Region('stack', STACK, b'\xa5'*512, 'rw', True),
                Region('domain_id_fixture', 0x8050, struct.pack('<I', 2)),
                Region('pre_kernel_fixture', 0x8ff006fc, bytes(4)),
                Region('restore_mask_fixture', 0x8ff00040, bytes(4)),
                Region('pool_state_fixture', STATE, state, 'rw', True)]
    registers = dict(pc=CALLER, sp=SP, d0=2, a0=address, psw=0xf00,
                     d2=0x22334455, d3=0x33445566, a2=0x44556677, a3=0x55667788)
    result = execute(regions, registers, STOP, limit=300, trace_limit=300,
                     timeout=10, breakpoints=DIAGNOSTICS,
                     engine=engine, record_hashes=False)
    if result.get('hash_checks_performed') is not False:
        raise ValueError('unexpected provenance mode')
    if result['status'] not in ('returned', 'breakpoint'):
        raise ValueError(('unexpected native stop', brief(result)))
    trace = result['trace']
    if len(trace) != result['completed']:
        raise ValueError('execution trace was truncated')
    # Payload and guards are deliberately unmapped. Any read or write there
    # would stop, rather than being silently accepted by a broad RAM mapping.
    masked = [row for row in trace if entry <= row['pc'] < 0x60022dcd
              and row['pc'] >= (0x600228bf if entry == ALLOC else 0x60022b2e)
              and row['pc'] < (0x60022a56 if entry == ALLOC else 0x60022cbb)]
    if not masked or any(row['psw'] & 0x700 for row in masked):
        raise ValueError('reviewed pool body did not retain LM=0')
    if result['status'] == 'returned':
        if (result['registers']['sp'] != SP or result['registers']['psw'] & 0xf00 != 0xf00
                or any(result['registers'][r] != registers[r] for r in ('d2', 'd3', 'a2', 'a3'))):
            raise ValueError('native return did not restore stack/callee registers/IRQ mask')
    min_sp = min(row['sp'] for row in trace)
    stack = capture(result, 'stack')
    # GNU MN103 CALL stores its return PC at the caller's current SP, then
    # allocates the mask/frame below it. The caller owns that four-byte slot.
    if (stack[:min_sp-STACK] != b'\xa5'*(min_sp-STACK)
            or stack[SP-STACK:SP-STACK+4] != struct.pack('<I', STOP)
            or stack[SP-STACK+4:] != b'\xa5'*(STACK+512-SP-4)):
        raise ValueError(('native call wrote outside observed stack extent', hex(min_sp),
                          [hex(STACK+i) for i, value in enumerate(stack) if value != 0xa5]))
    return result, capture(result, 'pool_state_fixture')


def inspect(decoded, objdump, engine):
    graph = NativeGraph(decoded, objdump)
    try:
        # Reuse established instruction witnesses, adding only the previously
        # untested recycle/PSW branch. Each check disassembles at its exact PC.
        witnesses = {pc: ins for pc, ins in RAM_W.items()
                     if ALLOC <= pc < 0x60022cc5}
        witnesses.update({
            0x60022a0d: ('ble', '0x60022a2f'),
            0x60022a10: ('udf00', '12,d2'),
            0x60022a15: ('mov', 'd0,(a1)'),
            0x60022a16: ('add', '1610771920,d2'),
            0x60022a1f: ('mov', '(d3,a1),a1'),
            0x60022a2b: ('add', 'a3,d3'),
            0x60022a33: ('bne', '0x60022a42'),
            0x60022a3b: ('call', '0x6002247c,[a2,a3],28'),
            0x60022c81: ('call', '0x60022694,[d2,a2],24'),
            0x6006a922: ('mov', '(0x8ff006fc),d1'),
            0x6006a92f: ('bne', '0x6006a960'),
            0x6006a961: ('call', '0x60054d9f,[],0'),
            0x6006a96c: ('mov', '(0x8ff00040),d0'),
            0x6006a977: ('call', '0x60054dc0,[],0'),
            0x60054d9f: ('mov', 'psw,d1'),
            0x60054db7: ('mov', 'd1,psw'),
            0x60054dc0: ('mov', 'd0,psw')})
        for pc, expected in witnesses.items():
            if graph.instruction(pc)[2:] != expected:
                raise ValueError(('instruction changed', hex(pc), expected))
        data = graph.data
        if struct.unpack_from('<I', data, 0x60026df0-BASE)[0] != STATE+RECYCLE_WORDS:
            raise ValueError('domain-2 big-slot recycle table changed')
        if struct.unpack_from('<I', data, 0x60026e3c-BASE)[0] != STRIDE:
            raise ValueError('big-slot stride changed')
    finally:
        graph.close()

    cases = []
    executed_pcs = set()

    def check(name, before, entry, expected, *, candidate=True, address=0, pointer=None, stop=STOP):
        result, after = native_call(data, engine, before, entry, candidate=candidate, address=address)
        if (after != expected or result['registers']['pc'] != stop
                or result['status'] != ('returned' if stop == STOP else 'breakpoint')):
            raise ValueError((name, brief(result), state_brief(after), state_brief(expected)))
        if pointer is not None and result['registers']['a0'] != pointer:
            raise ValueError((name, 'wrong pointer', hex(result['registers']['a0'])))
        executed_pcs.update(row['pc'] for row in result['trace'] if row['pc'] != CALLER)
        cases.append(dict(name=name,mode='two in-memory operand edits' if candidate else 'stock',
                          result=brief(result),before=state_brief(before),after=state_brief(after),
                          returned_pointer=hex(pointer) if pointer is not None else None,
                          expected_stop=hex(stop),pool_payload_and_guards_unmapped=True,
                          minimum_sp=hex(min(row['sp'] for row in result['trace'])),
                          reviewed_body_lm_zero=True,exact_state_transition=True))
        return after

    check('stock-last-slot-control', state_for(31, 0x7fffffff), ALLOC,
          state_for(32, 0xffffffff), candidate=False, pointer=POOL+31*STRIDE)
    full = check('candidate-last-retained-slot', state_for(30, 0x3fffffff), ALLOC,
                 state_for(31, 0x7fffffff), pointer=POOL+30*STRIDE)
    check('candidate-exhaustion-stops-before-diagnostic', full, ALLOC, full, stop=0x6002247c)
    recycled = check('candidate-free-last-retained-slot', full, FREE,
                     state_for(31, 0x3fffffff, (30,)), address=POOL+30*STRIDE)
    # Pop leaves the old halfword beyond the now-empty recycle stack intact.
    popped = put(state_for(31, 0x7fffffff), RECYCLE_WORDS, 30, '<H')
    check('candidate-reuses-last-retained-slot', recycled, ALLOC, popped, pointer=POOL+30*STRIDE)
    invalid = state_for(32, 0xffffffff)
    check('candidate-rejects-free-of-reserved-slot', invalid, FREE, invalid,
          address=POOL+31*STRIDE, stop=0x60022694)
    stale = state_for(31, 0x7fffffff, (31,))
    stale_after = put(state_for(31, 0xffffffff), RECYCLE_WORDS, 31, '<H')
    check('stale-recycle-index-bypasses-new-count', stale, ALLOC, stale_after,
          pointer=POOL+31*STRIDE)

    return dict(scope=__doc__,engine=str(engine),engine_bytes=engine.stat().st_size,
                instruction_witnesses=len(witnesses),different_executed_stock_addresses=len(executed_pcs),
                cases=cases,all_assertions_passed=True,
                reservation=dict(start=hex(POOL+31*STRIDE),payload_bytes=0x4000,
                                 count_change_effective_for_fresh_allocation=True,
                                 free_bound_rejects_reserved_index=True,
                                 recycled_index_is_revalidated=False,
                                 late_installation_safe=False,approved_for_placement=False),
                fixture=dict(cpu_id=2,pre_kernel_state_word=0,restore_mask_state_word=0,
                             initial_psw='0xf00',counter=hex(STATE+COUNTER),
                             recycled_count=hex(STATE+RECYCLED),recycle_words=hex(STATE+RECYCLE_WORDS),
                             bitmap=hex(STATE+BITMAP),native_services_stubbed=[]),
                hash_checks_performed=False,firmware_file_modified=False,firmware_built=False,
                in_memory_operand_edits_only=True,hardware_executed=False,
                limits=[
                    'The state words and stack are explicit synthetic fixtures. Startup zeroing and the upstream prefix loader were not executed.',
                    'Pre-kernel native PSW lock helpers ran; scheduler-active locking, cross-core exclusion, IRQ delivery and physical cache are not modeled here.',
                    'Exhaustion and invalid free stop before their native diagnostic entry. Return, fault policy and caller capacity handling remain unproven.',
                    'The stale-recycle case is a counterexample to late installation, not evidence that stock boot produces such state.',
                    'Executed paths touch only mapped allocator state/stack. Guard initialization, other owners and whole-lifecycle reservation remain open.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded', type=Path, required=True)
    parser.add_argument('--objdump', required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.decoded, args.objdump, args.engine), indent=2))
