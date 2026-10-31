#!/usr/bin/env python3
"""Bound peer-core startup to its release wait and classify its printing calls.

Explicit local-register/UART-ready fixtures; no allocator, heap, NAND, IRQ or
coherence model. The original code executes in the existing strict GNU engine.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from penf_emulator import Region, execute
from ep7_native_stack import BASE, NativeGraph
from ep7_irq_stack import span
from ep7_sim_probe import brief, capture
from ep7_cold_start_order import GROUPS
from ep7_ram_ownership import W as RAM_W

PRINT = 0x60054a7a
PUTCHAR = 0x60020429
LOG = 0x60023637
HELPERS = [(PUTCHAR,0x60020461),(LOG,0x60023663),(PRINT,0x60054aa3)]
STACK = 0x47000000
SP = 0x470007fc
PEERS = [(1,0x60027117,0x600271b6,0x60027209,0x60027219,0x60027223,0x60074b64,0x98100408),
         (2,0x60027575,0x60027614,0x60027614,0x60027624,0x6002762e,0x60074b8c,0x98100808)]


def run(engine, regions, registers, stop, limit):
    result=execute(regions,registers,stop,limit=limit,trace_limit=limit,
                   engine=engine,record_hashes=False,timeout=10)
    if result.get('hash_checks_performed') is not False or len(result['trace'])!=result['completed']:
        raise ValueError('unexpected provenance or truncated execution trace')
    return result


def inspect(decoded,objdump,engine):
    graph=NativeGraph(decoded,objdump,code_ranges=HELPERS)
    try:
        mismatches=graph.collect([PRINT])
        if mismatches or set(graph.functions)!={PRINT,PUTCHAR,LOG}:
            raise ValueError('peer print call/frame closure changed')
        if any(row['boundaries'] for row in graph.functions.values()):
            raise ValueError('print closure has unreviewed control flow')
        if any(not any(lo<=pc and pc+graph.instruction(pc)[1]<=hi for lo,hi in HELPERS)
               for reached in graph.function_instruction_addresses.values() for pc in reached):
            raise ValueError('helper instruction crosses its explicit review window')
        expected_edges={(0x60054a89,PUTCHAR),(0x60054a92,PUTCHAR),(0x60020459,LOG)}
        if {(int(edge['site'],16),int(edge['target'],16)) for fn in graph.functions.values()
            for edge in fn['calls']}!=expected_edges:
            raise ValueError('print helper call inventory changed')
        # Both branches of the optional logger belong to the static review;
        # only its disabled branch is executed in the cold-state fixtures.
        extra={0x60023637:('mov','(0xa26a4a58),d1'),0x6002363f:('beq','0x60023660'),
               0x60023641:('mov','(0xa26a4b40),a0'),
               0x60023647:('movhu','(0xa26a4b44),d1'),
               0x6002364d:('movbu','d0,(d1,a0)'),
               0x60023656:('and','8191,d0'),
               0x6002365a:('movhu','d0,(0xa26a4b44)')}
        extra.update({pc:RAM_W[pc] for pc in (0x60020068,0x6002006e,0x60020074)})
        for name,(_,_,witnesses) in GROUPS.items():
            if name in ('secondary_one_transfer','secondary_two_transfer'):
                extra.update(witnesses)
        for peer,entry,entry_end,body,wait,after,text_at,reg_at in PEERS:
            extra[entry]=('and','61695,psw')
            extra[body]=('add','-4,sp')
            extra[body+3]=('mov',str(text_at)+',a0')
            extra[body+9]=('call','0x60054a7a,[a2],8')
            extra[wait]=('mov','(0xa26c3388),d0')
            extra[wait+6]=('cmp','0,d0')
            extra[wait+8]=('beq',hex(wait))
            entry_rows=span(graph,entry,entry_end)
            if any(mn not in ('and','nop','mov','movhu','jmp') for _,_,mn,_ in entry_rows):
                raise ValueError('peer register setup acquired another operation')
            if [(pc,ops) for pc,_,mn,ops in entry_rows if mn=='jmp']!=[(entry_end-2,'(a0)')]:
                raise ValueError('peer setup control flow changed')
        for pc,expected in extra.items():
            if graph.instruction(pc)[2:]!=expected:
                raise ValueError(('instruction changed',hex(pc),expected))
        data=graph.data
        if struct.unpack_from('<2I',data,0x60023e30-BASE)!=(0x9870001c,0x98700018):
            raise ValueError('UART selector-zero table changed')
        logger_in_clear_span=0x621caf00 <= 0xa26a4a58-0x40000000 < 0x62796888
        helper_functions=list(graph.functions.values())
        decoded_count=len(graph.decoded_instructions)
    finally:
        graph.close()

    cases=[]
    for peer,entry,entry_end,body,wait,after,text_at,reg_at in PEERS:
        if data[text_at-BASE:text_at-BASE+2]!=str(peer).encode()+b'\0':
            raise ValueError('peer startup string changed')
        regions=[Region('entry',entry,data[entry-BASE:entry_end-BASE],'rx'),
                 Region('pre_wait',body,data[body-BASE:after-BASE],'rx')]
        regions += [Region('helper_'+hex(lo),lo,data[lo-BASE:hi-BASE],'rx') for lo,hi in HELPERS]
        regions += [Region('startup_text',text_at,data[text_at-BASE:text_at-BASE+2]),
                    Region('uart_table',0x60023e30,data[0x60023e30-BASE:0x60023e38-BASE]),
                    Region('uart_selection_fixture',0x8ff0005c,bytes(2)),
                    Region('uart_ready_fixture',0x9870001c,struct.pack('<I',1)),
                    Region('logger_disabled_fixture',0xa26a4a58,bytes(4)),
                    Region('release_fixture',0xa26c3388,bytes(4)),
                    Region('stack',STACK,b'\xa5'*2048,'rw',True),
                    Region('vectors',0x8000,bytes(32),'rw',True),
                    Region('control_8070',0x8070,bytes(2),'rw',True),
                    Region('control_8940',0x8940,bytes(26),'rw',True),
                    Region('control_8a80',0x8a80,bytes(2),'rw',True),
                    Region('peer_control',reg_at,bytes(4),'rw',True),
                    Region('uart_output',0x98700018,bytes(4),'rw',True)]
        result=run(engine,regions,dict(pc=entry,psw=0xf00),wait,500)
        if result['status']!='returned' or result['registers']['sp']!=SP-4:
            raise ValueError(('peer did not reach wait',brief(result)))
        trace=result['trace']
        if any(row['psw']&0xf00 for row in trace[1:]):
            raise ValueError('peer reenabled interrupts before wait')
        output=[row['d0']&255 for row in trace if row['pc']==0x60020457]
        if output!=list(str(peer).encode()) or capture(result,'uart_output')!=struct.pack('<I',48+peer):
            raise ValueError('native startup print differs from reviewed string')
        if capture(result,'peer_control')!=struct.pack('<I',16):
            raise ValueError('peer local-control store changed')
        # Resume the identical resulting CPU/memory state, once with the real
        # branch's zero input and once with an explicit synthetic release.
        captured={row['name']:bytes.fromhex(row['hex']) for row in result['memory']}
        resumed=[replace(region,data=captured.get(region.name,region.data)) for region in regions]
        waiting=run(engine,resumed,result['registers'],after,3)
        if (waiting['status']!='instruction_limit' or waiting['registers']['pc']!=wait
                or [row['pc'] for row in waiting['trace']]!=[wait,wait+6,wait+8]):
            raise ValueError(('zero release did not loop',brief(waiting)))
        released=[replace(region,data=struct.pack('<I',1)) if region.name=='release_fixture'
                  else region for region in resumed]
        release=run(engine,released,result['registers'],after,4)
        if release['status']!='returned' or release['completed']!=3:
            raise ValueError(('nonzero release did not leave wait',brief(release)))
        # The parent restores SP from a constant; minimum only has meaning after
        # that store (entry+35). The initial caller SP is deliberately absent.
        established=[row['sp'] for row in trace if STACK<=row['sp']<=SP]
        if min(established)!=SP-20:
            raise ValueError('peer pre-wait native stack requirement changed')
        cases.append(dict(peer=peer,entry=hex(entry),wait=hex(wait),after_wait=hex(after),
            startup=brief(result),uart_output=bytes(output).decode(),
            zero_release=brief(waiting),nonzero_release=brief(release),
            minimum_established_sp=hex(min(established)),known_pre_wait_stack_depth=20,
            helper_stack_or_uart_only_with_logger_disabled=True,
            heap_and_private_payload_unmapped=True,interrupt_enable_and_level_zero=True))

    return dict(scope=__doc__,engine=str(engine),engine_bytes=engine.stat().st_size,
        exact_decoded_instruction_addresses=decoded_count,helper_functions=helper_functions,
        helper_call_frame_mismatches=mismatches,cases=cases,all_assertions_passed=True,
        logger=dict(enable='0xa26a4a58',buffer_pointer='0xa26a4b40',index='0xa26a4b44',
                    ring_mask=8191,flag_in_reviewed_startup_clear_span=logger_in_clear_span,
                    enabled_branch_has_computed_buffer_write=True,enabled_branch_executed=False),
        concluded=dict(print_call_closure_has_no_allocator_call=True,
                       explicit_cold_peer_prefix_accesses_no_heap=True,
                       global_cross_core_quiescence_proven=False,
                       boot_prefix_residency_proven=False,approved_for_placement=False),
        hash_checks_performed=False,firmware_modified=False,firmware_built=False,hardware_executed=False,
        limits=['Native peripheral stores, UART readiness and release inputs use explicit local memory fixtures. Physical reset/release/coherence are not modeled.',
                'The logger-disabled value lies in a known startup clear interval but actual DMA completion and absence of other writers have not been proved here.',
                'The enabled logger branch writes through a stored pointer. It is retained as a conditional memory-ownership frontier, not hidden by an absence of allocator calls.',
                'Execution stops before the post-release helper copy. IRQ/NMI, kernel startup, pool initialization and whole-boot ownership are outside this probe.'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--decoded',type=Path,required=True)
    p.add_argument('--objdump',required=True)
    p.add_argument('--engine',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(inspect(a.decoded,a.objdump,a.engine),indent=2))
