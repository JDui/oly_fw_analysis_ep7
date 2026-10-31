#!/usr/bin/env python3
"""Replay E-P7 early load control with explicit successful/failed storage models.

Reuses the repository's load/execute/reload method and strict GNU runner.
Only RAM fixtures contain sentinels; no patched firmware or hash is produced.
"""
import argparse
import json
from pathlib import Path
import struct

from penf_emulator import Region, execute
from ep7_native_stack import BASE, NativeGraph
from ep7_load_regions import W as LOAD_W
from ep7_early_code_space import RANGES
from ep7_sim_probe import brief, capture

BEGIN = 0x600201db
END = 0x600201fe
LOW = 0x60030000
HIGH = 0x600d0800
FLASH = 0x406b0000
UNCACHED = 0xa0030000
STACK = 0x19010000
SP = STACK + 256
CALLER = 0x19000000
READS = {0x60020ba7: ('page_read', 0x60020cdb),
         0x60020dc0: ('block_read', 0x60020efb)}
EXPECTED_READS = [(0x60020ba7, FLASH, UNCACHED, 0x10000),
                  (0x60020dc0, FLASH+0x10000, UNCACHED+0x10000, 0x80000),
                  (0x60020ba7, FLASH+0x90000, UNCACHED+0x90000, 0x10800)]
SEGMENTS = [('early_call', BEGIN, END), ('loader', 0x6002144e, 0x60021621),
            ('ready', 0x6002067a, 0x600206a0), ('lock_wrappers', 0x6002195b, 0x600219ab),
            ('timer', 0x60022319, 0x60022332),
            ('page_return', 0x60020cdb, 0x60020cde),
            ('block_return', 0x60020efb, 0x60020efe)]


def inspect(decoded, objdump, engine):
    graph = NativeGraph(decoded, objdump)
    try:
        witnesses = {pc: LOAD_W[pc] for pc in (BEGIN, 0x600201e7, 0x600201ed, 0x600201f3, 0x600201f9)}
        witnesses.update({
            0x600201e1: ('mov', 'd0,(0x6218d980)'),
            0x60021452: ('call', '0x6002195b,[],4'),
            0x60021457: ('call', '0x60022319,[],4'),
            0x6002145e: ('mov', '(0x61b213a4),d0'),
            0x60021499: ('mov', '(0xa26ff938),d0'),
            0x600214c2: ('cmp', '262144,d2'),
            0x600214cf: ('and', '2047,d3'),
            0x60021513: ('and', '131071,d3'),
            0x6002151f: ('call', '0x60020ba7,[d2,d3,a2,a3],44'),
            0x60021524: ('mov', '(4,sp),d0'),
            0x60021531: ('and', '131071,d0'),
            0x60021540: ('call', '0x60020dc0,[d2,d3,a2,a3],44'),
            0x60021545: ('mov', '(4,sp),a3'),
            0x60021552: ('mov', '2047,d0'),
            0x60021559: ('mov', 'a3,d0'),
            0x6002155d: ('call', '0x60020ba7,[d2,d3,a2,a3],44'),
            0x60021567: ('sub', 'd3,d2'),
            0x60021569: ('bne', '0x600215d2'),
            0x600215ea: ('call', '0x60022319,[],4'),
            0x60021618: ('call', '0x60021984,[],4'),
            0x6002161d: ('clr', 'd0'),
            0x6002161e: ('ret', '[d2,d3,a2,a3],32'),
            0x60020cdb: ('ret', '[d2,d3,a2,a3],44'),
            0x60020efb: ('ret', '[d2,d3,a2,a3],44'),
            0x6002195b: ('call', '0x6002067a,[],0'),
            0x60021962: ('bne', '0x60021981'),
            0x60021984: ('call', '0x6002067a,[],0'),
            0x6002198b: ('bne', '0x600219a8'),
            0x60022321: ('mov', '(0x9890014c),d1')})
        for pc, expected in witnesses.items():
            if graph.instruction(pc)[2:] != expected:
                raise ValueError(('instruction changed', hex(pc), expected))
        data = graph.data
    finally:
        graph.close()
    # This word comes from the actual startup .data copy, not a guessed default.
    diagnostic_word_source = 0x6002e020 + (0x61b213a4-0x61b20fe0)
    diagnostic_word = data[diagnostic_word_source-BASE:diagnostic_word_source-BASE+4]
    if diagnostic_word != bytes(4):
        raise ValueError('startup diagnostic switch changed')
    original = data[LOW-BASE:HIGH-BASE]
    source = bytearray(original)
    sentinels = []
    for index, (lo, hi) in enumerate(RANGES, 1):
        if source[lo-LOW:hi-LOW] != b'\xff'*(hi-lo):
            raise ValueError('candidate padding changed')
        source[lo-LOW:hi-LOW] = bytes((i*37+index)&255 for i in range(hi-lo))
        tag = 0x12340000 + index
        code = b'\xfc\xcc' + struct.pack('<I', tag) + b'\xdf\0\0'
        source[lo-LOW:lo-LOW+len(code)] = code
        sentinels.append(dict(start=hex(lo),end_exclusive=hex(hi),tag=hex(tag)))
    source = bytes(source)
    immutable = [Region(name, lo, data[lo-BASE:hi-BASE], 'rx') for name, lo, hi in SEGMENTS]
    immutable += [Region('ready_fixture', 0x8ff00058, bytes(3)),
                  Region('diagnostic_switch', 0x61b213a4, diagnostic_word),
                  Region('saturated_log_count_fixture', 0xa26ff938, struct.pack('<I', 100)),
                  Region('stationary_timer_fixture', 0x9890014c, struct.pack('<I', 0x3fffffff))]
    native_pcs = set()

    def load(initial, failed=False):
        memory = dict(stack=b'\xa5'*512, load_end=bytes(4), loaded=initial)
        registers = dict(pc=BEGIN, sp=SP, psw=0, d2=0x22334455, d3=0x33445566,
                         a2=0x44556677, a3=0x55667788)
        saved = registers.copy()
        reads = []
        chunks = []
        for _ in range(4):
            regions = immutable + [Region('stack', STACK, memory['stack'], 'rw', True),
                Region('load_end', 0x6218d980, memory['load_end'], 'rw', True),
                Region('loaded', LOW, memory['loaded'], 'rx', True),
                Region('uncached_alias', UNCACHED, memory['loaded'], 'rw', False, 'loaded')]
            result = execute(regions, registers, END, limit=500, trace_limit=500,
                breakpoints=tuple(READS), engine=engine, record_hashes=False, timeout=10)
            if result.get('hash_checks_performed') is not False:
                raise ValueError('unexpected provenance mode')
            if result['status'] not in ('breakpoint', 'returned'):
                raise ValueError(('unmodeled loader frontier', brief(result)))
            if len(result['trace']) != result['completed']:
                raise ValueError('native trace truncated')
            native_pcs.update(row['pc'] for row in result['trace'])
            chunks.append(brief(result))
            for name in memory:
                memory[name] = capture(result, name)
            registers = result['registers']
            if result['status'] == 'returned':
                break
            pc = registers['pc']
            request = (pc, registers['d1'], registers['d0'], registers['a0'])
            if len(reads) >= len(EXPECTED_READS) or request != EXPECTED_READS[len(reads)]:
                raise ValueError(('unexpected storage request', [hex(v) for v in request]))
            _, flash, dest, size = request
            if not failed:
                updated = bytearray(memory['loaded'])
                updated[dest-UNCACHED:dest-UNCACHED+size] = source[flash-FLASH:flash-FLASH+size]
                memory['loaded'] = bytes(updated)
            name, native_ret = READS[pc]
            reads.append(dict(entry=hex(pc),operation=name,source=hex(flash),destination=hex(dest),
                              bytes=size,model='failure without transfer' if failed else 'exact logical-source transfer',
                              modeled_d0='0xffffffff' if failed else '0x0',
                              original_return_instruction=hex(native_ret)))
            # Explicit lower-storage boundary. The original native RET restores
            # CALL's saved register mask/frame; do not fake the entire wrapper.
            registers = dict(registers, pc=native_ret, d0=0xffffffff if failed else 0)
        else:
            raise ValueError('loader failed to finish within its three read frontiers')
        if (result['status'] != 'returned' or len(reads) != 3 or registers['d0'] != 0
                or any(registers[r] != saved[r] for r in ('sp','d2','d3','a2','a3'))
                or memory['load_end'] != struct.pack('<I', HIGH)):
            raise ValueError(('native load completion changed', brief(result)))
        expected = initial if failed else source
        if memory['loaded'] != expected:
            raise ValueError('logical image differs from the declared storage contract')
        return memory['loaded'], dict(reads=reads,engine_chunks=chunks,returned_d0=0,
            exact_expected_destination=True,stack_and_callee_registers_restored=True,
            destination_bytes=HIGH-LOW,readiness_fixture=[0,0,0],
            log_count_fixture=100,timer_fixture='stationary',
            destination_unchanged=memory['loaded']==initial)

    loaded, first = load(b'\xa5'*(HIGH-LOW))
    executions = []
    for item in sentinels:
        address = int(item['start'],16)
        caller = b'\xdd' + struct.pack('<i',address-CALLER) + b'\0\0'
        result = execute([Region('caller',CALLER,caller,'rx'),
                          Region('loaded',LOW,loaded,'rx'),
                          Region('stack',STACK,b'\xa5'*512,'rw')],
                         dict(pc=CALLER,sp=SP), CALLER+7, limit=10, trace_limit=10,
                         engine=engine,record_hashes=False,timeout=10)
        if (result['status']!='returned' or result['registers']['d0']!=int(item['tag'],16)
                or result['registers']['sp']!=SP):
            raise ValueError(('sentinel did not return',brief(result)))
        executions.append(dict(**item,result=brief(result),returned_tag=hex(result['registers']['d0'])))
    altered = bytearray(loaded)
    for lo,hi in RANGES:
        altered[lo-LOW:hi-LOW] = b'\x55'*(hi-lo)
    reloaded, second = load(bytes(altered))
    if reloaded != loaded:
        raise ValueError('reload selected different logical source bytes')
    failure_initial = b'\x5a'*(HIGH-LOW)
    _, failed = load(failure_initial, failed=True)

    return dict(scope=__doc__,engine=str(engine),engine_bytes=engine.stat().st_size,
                instruction_witnesses=len(witnesses),different_executed_stock_addresses=len(native_pcs),
                first_load=first,sentinel_executions=executions,reload=second,
                injected_read_failure=failed,all_assertions_passed=True,
                diagnostic_switch_source=hex(diagnostic_word_source),
                early_copy=dict(start=hex(LOW),end_exclusive=hex(HIGH),bytes=HIGH-LOW,
                                flash=hex(FLASH),destination=hex(UNCACHED),
                                exact_native_three_way_split=True),
                conclusion=dict(conditional_logical_load_and_reload=True,
                                zero_return_proves_data_transfer=False,
                                boot_prefix_residency_proven=False,approved_for_placement=False),
                hash_checks_performed=False,firmware_file_modified=False,firmware_built=False,
                in_memory_sentinels_only=True,hardware_executed=False,
                limits=[
                    'The prefix caller and its native wrapper were supplied as already resident. Reset-ROM selection and loading of the prefix remain unproved.',
                    'Only the lower page/block-read bodies are modeled. The reported source bytes are copied by the harness, not by emulated NAND/DMA.',
                    'Readiness flags, stationary timer, saturated log counter and stack are explicit fixtures. Logging, semaphore-active paths and other cores were not executed.',
                    'Cached/uncached aliases and execute permissions are supplied runner mappings, not physical cache or MPU evidence.',
                    'Failure injection proves the wrapper ignores returned errors; it does not establish which hardware failures return or whether a lower diagnostic is nonreturning.',
                    'Candidate padding markers survive this conditional load/reload only. Other references, later writes and ownership remain outside this execution.'])


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded',type=Path,required=True)
    parser.add_argument('--objdump',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(inspect(args.decoded,args.objdump,args.engine),indent=2))
