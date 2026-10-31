#!/usr/bin/env python3
"""Focused strict-engine acceptance and two original E-P7 kernel routines.

Reuses the existing GNU runner/protocol and existing MAC extension. Synthetic
data/stack only; no peripherals, full boot, firmware modification or SHA check.
"""
import argparse
import json
from pathlib import Path
import struct

from penf_emulator import Region, execute
from ep7_native_stack import BASE, NativeGraph
from ep7_irq_stack import HELPER_W, span

CALLER=0x19000000
STOP=CALLER+7
STACK=0x19010000
SP=STACK+256
TCB=0x19020000


def run(engine,regions,registers,stop=STOP,limit=100):
    result=execute(regions,registers,stop,limit=limit,trace_limit=limit,timeout=10,
        engine=engine,record_hashes=False)
    if result.get('hash_checks_performed') is not False:
        raise ValueError('unexpected input provenance mode')
    return result


def capture(result,name):
    return bytes.fromhex(next(row['hex'] for row in result['memory'] if row['name']==name))


def brief(result):
    return dict(status=result['status'],completed=result['completed'],fault=result['fault'],
        final_pc=hex(result['registers']['pc']),final_sp=hex(result['registers']['sp']))


def inspect(decoded,objdump,engine):
    graph=NativeGraph(decoded,objdump)
    try:
        helper=span(graph,0x60030107,0x60030137)
        if {pc:(mn,ops) for pc,_,mn,ops in helper}!=HELPER_W:
            raise ValueError('original MAC helper changed')
        query=span(graph,0x6003434b,0x6003436e)
        expected_query=[('mov','(0x8050),d0'),('asl2','d0'),('mov','-1880096764,a0'),
            ('mov','(d0,a0),a0'),('mov','(96,a0),a0'),('mov','(a0),a0'),
            ('movhu','(48,a0),d0'),('cmp','1,d0'),('bne','0x60034366'),
            ('clr','d0'),('bra','0x6003436b'),('add','56,a0'),('mov','(a0),d0'),
            ('clr','d1'),('mov','d1,(a0)'),('retf','[],0')]
        if [row[2:] for row in query]!=expected_query:raise ValueError('task exception query changed')
        data=graph.data
    finally:graph.close()

    # A missing mapping and a syscall must stop instead of supplying board RAM
    # or dispatching a host service. These are engine acceptance, not boot tests.
    missing=run(engine,[],dict(pc=CALLER,sp=SP),limit=4)
    if missing['status']!='memory_fault' or missing['fault']['access']!='execute':
        raise ValueError('unmapped instruction fetch did not stop')
    syscall=run(engine,[Region('syscall',CALLER,b'\xf0\xc0','rx')],
        dict(pc=CALLER,sp=SP),limit=4)
    if syscall['status']!='instruction_fault':raise ValueError('host syscall was not rejected')

    helpers=[]
    code=Region('original_mac_helpers',0x60030107,data[0x60030107-BASE:0x60030137-BASE],'rx')
    for overflow in (0,1):
        stack=bytes([0xa5])*512
        original=dict(extra15=0x12345678,extra16=0x89abcdef,extra17=overflow,mdrq=0x99887766)
        registers=dict(pc=0x60030107,sp=SP,a3=STOP,psw=0x807,**original)
        saved=run(engine,[code,Region('stack',STACK,stack,'rw',True)],registers)
        if saved['status']!='returned' or saved['registers']['sp']!=SP-16:
            raise ValueError('MAC save did not return with the reviewed frame')
        saved_memory=capture(saved,'stack')
        if saved_memory[:240]!=stack[:240] or saved_memory[256:]!=stack[256:]:
            raise ValueError('MAC save wrote outside its 16-byte frame')
        words=struct.unpack_from('<4I',saved_memory,240)
        if words[1:]!=(original['extra16'],original['extra15'],original['mdrq']) or bool(words[0]&8)!=bool(overflow):
            raise ValueError('MAC save slots differ from the reviewed register layout')
        changed=dict(saved['registers'],pc=0x6003011c,a3=STOP,psw=0x80f,
            extra15=0xaaaaaaaa,extra16=0xbbbbbbbb,extra17=1-overflow,mdrq=0xcccccccc)
        restored=run(engine,[code,Region('stack',STACK,saved_memory,'rw',True)],changed)
        if (restored['status']!='returned' or restored['registers']['sp']!=SP or
                any(restored['registers'][name]!=value for name,value in original.items()) or
                restored['registers']['psw']&0xf00!=0x800 or
                capture(restored,'stack')!=saved_memory):
            raise ValueError('MAC context or IRQ mask was not restored as modeled')
        helpers.append(dict(mcvf=overflow,save=brief(saved),restore=brief(restored),
            saved_frame_bytes=16,mac_registers_restored=True,irq_mask_preserved=True,
            no_extra_stack_writes=True))

    queries=[]
    query_code=Region('original_task_exception_query',0x6003434b,
        data[0x6003434b-BASE:0x6003436e-BASE],'rx')
    root=data[0x600411a4-BASE:0x60041208-BASE]
    if struct.unpack_from('<I',root,96)[0]!=0x621a630c:raise ValueError('root current-task cell changed')
    caller=Region('synthetic_caller',CALLER,b'\xdd'+struct.pack('<i',0x6003434b-CALLER)+b'\0\0','rx')
    for flag in (1,0):
        pending=0xa5a50001;task=bytearray(60)
        struct.pack_into('<H',task,48,flag);struct.pack_into('<I',task,56,pending)
        regions=[caller,query_code,Region('stock_root',0x600411a4,root),
            Region('domain_id_fixture',0x8050,bytes(4)),
            Region('root_cell_fixture',0x8ff00004,struct.pack('<I',0x600411a4)),
            Region('current_cell_fixture',0x621a630c,struct.pack('<I',TCB)),
            Region('task_fixture',TCB,bytes(task),'rw',True),Region('stack',STACK,bytes(512),'rw')]
        result=run(engine,regions,dict(pc=CALLER,sp=SP,psw=0x800))
        expected=bytes(task) if flag else bytes(task[:56])+bytes(4)
        if (result['status']!='returned' or result['registers']['sp']!=SP or
                result['registers']['d0']!=(0 if flag else pending) or
                capture(result,'task_fixture')!=expected):
            raise ValueError('native task-exception query disagrees with the static gate')
        queries.append(dict(flag=flag,pending_before=hex(pending),
            pending_after=hex(struct.unpack_from('<I',expected,56)[0]),
            result=brief(result),returned_d0=hex(result['registers']['d0'])))

    return dict(scope=__doc__,engine=str(engine),engine_bytes=engine.stat().st_size,
        strict_stops=dict(unmapped_execute=brief(missing),host_syscall=brief(syscall)),
        original_instruction_witnesses=len(helper)+len(query),mac_helper_cases=helpers,
        task_exception_query_cases=queries,all_assertions_passed=True,
        input_provenance='Current decoded length and exact instruction/ROM-field checks; explicit engine mode without hashes.',
        stock_instructions_executed_in_gnu_model=True,hardware_executed=False,
        firmware_modified=False,firmware_built=False,hash_checks_performed=False,
        limits=['The CPU core, MAC extension and undefined flags are the existing GNU/repository models. No new instruction implementation was introduced.',
                'The current-task cell, TCB, CPU-ID register and stack are synthetic. This does not execute task creation, IRQ entry, scheduling or the full bootstrap.',
                'MAC roundtrip under the model does not validate E-P7 silicon, flag pipeline timing, physical cache or interrupts.',
                'No boot-prefix loader, executable placement or lifetime gate is closed by these focused calls.'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--decoded',type=Path,required=True)
    p.add_argument('--objdump',required=True)
    p.add_argument('--engine',type=Path,required=True)
    a=p.parse_args();print(json.dumps(inspect(a.decoded,a.objdump,a.engine),indent=2))
