#!/usr/bin/env python3
"""Deliver the newly selected node through the original event4b mailbox path.

The original selected cold heap, mailbox, fixed block pool and event flag recipes
run with sparse store capacity. Normal callback status and sequential task calls
remain explicit inputs; generic engine dispatch and controller scheduling do not run.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import CALLER, require
from ep7_candidate_state_sim import CALL_SP, objects, ready_lock
from ep7_candidate_capture_allocation_sim import NEW_CAPTURE
from ep7_candidate_node_factory_sim import NEW_NODE, sparse_read
from ep7_candidate_capture_sim import CAPTURE, ASSOCIATED, NODE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_format_record_sim import missing_bytes
from ep7_candidate_message_sim import native_call, result_ok
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_node_selection_sim import node_selection_context


ROOT = 0x600411a4
HEAP, HEAP_BASE, HEAP_SIZE = 0x621a63c0,0x6203c940,0xb1000
MAILBOX, POOL, FLAG = 0x6219fb74,0x621a3e90,0x6219d2e8
ARENA_HEADER = HEAP_BASE+HEAP_SIZE-468
ARENA = ARENA_HEADER+20
BLOCK_HEADER = ARENA+15*28
MESSAGE = BLOCK_HEADER+8
OUTPUT = 0x19c11000


def selected_mailbox_context(directory,prefix,engine):
    upstream,contexts = node_selection_context(directory,prefix,engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    syms = base['syms']
    context = contexts['cases'][0]
    machine = context['selection_machine'].clone()
    sidecar = syms['_ep7_controller_sidecar_unresolved']
    sealed = machine.read(sidecar,664)
    capture,old_capture = machine.read(NEW_CAPTURE,SIZE),machine.read(CAPTURE,SIZE)
    u32 = lambda address: int.from_bytes(machine.read(address,4),'little')
    require(machine.read(ROOT+40,12) == struct.pack('<3I',HEAP,HEAP_BASE,HEAP_SIZE) and
            u32(ROOT+136) == 0x6003a1ec and u32(ROOT+144) == 0x6003ad58 and
            u32(ROOT+164) == 0x6003c0d4 and u32(ROOT+212) == 0x6003e39c and
            u32(ROOT+220) == 0x6003e89c and u32(ROOT+236) == 0x6003eda0 and
            u32(0x6003e89c) == MAILBOX and u32(0x6003eda0) == POOL and
            u32(0x6003e39c+73*4) == FLAG and
            machine.read(0x6003ad58,24) == struct.pack('<6I',1,0,0,0,0,0) and
            machine.read(0x6003c0d4,20) == struct.pack('<5I',1,0,16,20,0) and
            machine.read(0x6003a564,12) == struct.pack('<3I',74,4,0) and
            all(machine.read(a,2) == struct.pack('<H',v) for a,v in
                ((0x60040cdc,1),(0x60040eb6,1),(0x60040b8e,74))) and
            u32(0x6223d134+13*4) == 0x602a3042 and
            machine.read(0x602a3042,16) == bytes.fromhex('f8fefc1c854bdda890f6ff0010df0004'),
            'original mailbox/heap/pool/flag recipes or selected callback binding changed')
    extents = [(HEAP,20),(HEAP_BASE,20),(ARENA_HEADER,20),(POOL,36),(MAILBOX,28),
               (MESSAGE,20),(FLAG,24)] + [(ARENA+i*28,8) for i in range(16)]
    added = missing_bytes(machine,[a+i for a,n in extents for i in range(n)],
        0xa5,'native_selected_mailbox_dependencies')
    require(len(added) == 296,'selected original mailbox dependencies overlap prior storage')
    heap_init = native_call(machine,syms,0x600360b5,0x30,8)
    require(machine.read(HEAP,20) == struct.pack('<5I',*[HEAP_BASE]*4,HEAP_SIZE) and
            machine.read(HEAP_BASE,20) == struct.pack('<5I',*[HEAP]*4,HEAP_SIZE),
            'original cold heap root/base initialization changed')
    mailbox_init = native_call(machine,syms,0x60032b6c,0xb0,16)
    mailbox_idle = struct.pack('<2H6I',1,64,MAILBOX+4,MAILBOX+4,0,0,MAILBOX+20,MAILBOX+20)
    require(machine.read(MAILBOX,28) == mailbox_idle,'original static mailbox initialization changed')
    pool_init = machine.run(0x60032ce1,0x60032d1c,
        overrides=dict(sp=CALL_SP,d2=0x6003eda0,a2=0x6003c0d4),full_trace=True,limit=2000)
    result_ok(machine,pool_init,0x60032d1c,CALL_SP)
    pool_idle = struct.pack('<2H8I',1,8192,POOL+4,POOL+4,128,16,20,ARENA,BLOCK_HEADER,16)
    require(machine.read(POOL,36) == pool_idle and
            machine.read(ARENA_HEADER,20) == struct.pack('<5I',HEAP,HEAP_BASE,0,0,468) and
            u32(HEAP_BASE+16) == HEAP_SIZE-468 and u32(HEAP+4) == ARENA_HEADER and
            all(machine.read(ARENA+i*28,8) == struct.pack('<I2H',ARENA+(i-1)*28 if i else POOL+28,1,0)
                for i in range(16)), 'native fixed pool heap allocation or free chain changed')
    flag_init = machine.run(0x60032ace,0x60032b09,
        overrides=dict(sp=CALL_SP,d2=0x6003e39c,a2=0x6003a564),full_trace=True,limit=1000)
    result_ok(machine,flag_init,0x60032b09,CALL_SP)
    require(machine.read(FLAG,24) == struct.pack('<2H5I',74,8,FLAG+4,FLAG+4,4,0,0),
            'selected original event flag initialization changed')
    # Initializers operate on the same scratch stack. Its dead contents are not
    # message fields: the callback defines a status halfword and two words only.
    machine.regions['stack'] = replace(machine.regions['stack'],data=b'\xcc'*len(machine.regions['stack'].data))
    task_cell = machine.regions['task_cell'].data
    sent = native_call(machine,syms,0x602a3042,0,0,dict(d0=0,a0=NEW_NODE))
    payload = machine.read(MESSAGE+8,12)
    require(sent['registers']['d0'] == 0 and payload[:2] == bytes(2) and
            payload[4:] == struct.pack('<2I',0x4b,NEW_NODE) and
            machine.read(MAILBOX+20,8) == struct.pack('<2I',MESSAGE,MESSAGE) and
            machine.read(MESSAGE,8) == struct.pack('<2I',MAILBOX+20,MAILBOX+20) and
            machine.read(BLOCK_HEADER+4,4) == struct.pack('<2H',1,0x73) and
            u32(POOL+28) == ARENA+14*28 and u32(POOL+32) == 15 and u32(FLAG+20) == 1,
            'original selected event was not enqueued/notified with the actual node')
    for address,d0 in ((0x6003364a,1),(0x60035db7,1),(0x6020c15c,74),
                       (0x60051078,74),(0x60035a5e,74)):
        calls = [t for t in sent['trace'] if t['pc'] == address]
        require(len(calls) == 1 and calls[0]['d0'] == d0,
                'original task mailbox allocation/send/notification path changed')
    require(len(missing_bytes(machine,range(OUTPUT,OUTPUT+12),0xa5,'native_selected_message_output')) == 12,
            'selected message output overlaps existing storage')
    received = native_call(machine,syms,0x6020c101,0x20,28,dict(a0=OUTPUT))
    require(received['registers']['d0'] == 0 and machine.read(OUTPUT,12) == payload and
            machine.read(MAILBOX,28) == mailbox_idle and machine.read(POOL,36) == pool_idle and
            machine.read(BLOCK_HEADER+4,4) == struct.pack('<2H',1,0) and u32(FLAG+20) == 1 and
            sum(t['pc'] == 0x60033732 for t in received['trace']) == 1 and
            sum(t['pc'] == 0x60034d18 for t in received['trace']) == 1,
            'native mailbox receive/copy/free did not return the original pool and message')
    empty = machine.clone()
    empty_result = native_call(empty,syms,0x6020c101,0x20,28,dict(a0=OUTPUT))
    require(empty_result['registers']['d0'] == 0xffffffff and empty.read(OUTPUT,12) == payload and
            empty.read(MAILBOX,28) == mailbox_idle and empty.read(POOL,36) == pool_idle and
            not any(t['pc'] == 0x60034d18 for t in empty_result['trace']),
            'empty mailbox poll did not return -1 without copying/freeing another message')
    require(machine.read(sidecar,664) == sealed and machine.read(NEW_CAPTURE,SIZE) == capture and
            machine.read(CAPTURE,SIZE) == old_capture and
            sparse_read(machine,ASSOCIATED+8,4) == struct.pack('<I',NODE) and
            machine.regions['task_cell'].data[:4] == task_cell[:4] and
            machine.regions['task_cell'].data[8:] == task_cell[8:] and
            machine.regions['dispatch_enabled'].data == b'\0' and
            (received['registers']['psw']&0xf00) == (machine.initial['psw']&0xf00),
            'sealed capture, old backlink or released task/kernel state changed')
    _,_,_,provider = objects(machine,syms)
    ready_lock(machine,provider)
    cases = [stage(name,result) for name,result in (
        ('original_cold_kernel_heap_initializer',heap_init),('original_static_mailbox_initializer',mailbox_init),
        ('selected_original_fixed_pool_recipe',pool_init),('selected_original_flag74_recipe',flag_init),
        ('complete_selected_event4b_sender',sent),('complete_mailbox1_receiver_and_free',received),
        ('empty_mailbox1_receive',empty_result))]
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],engine=str(engine),
        cases=cases,native_instructions=sum(r['completed'] for r in cases),
        maximum_observed_new_stack_depth=max(r['stack_depth_from_call_sp'] for r in cases),
        native_store_capacity_added=296,explicit_receive_output_capacity_added=12,
        cold_BSS_bytes_added=0,
        kernel_heap=dict(root=hex(HEAP),base=hex(HEAP_BASE),size=HEAP_SIZE,
                         allocated_total_bytes=468,allocated_payload_bytes=448,allocation=hex(ARENA)),
        fixed_pool=dict(id=1,object=hex(POOL),ROM_row='0x6003c0d4',count=16,payload_bytes=20,
                        slot_bytes=28,message=hex(MESSAGE),free_count_before=16,after_send=15,after_receive=16),
        mailbox=dict(id=1,object=hex(MAILBOX),ROM_row='0x6003ad58',initialized_empty=True,empty_after_receive=True),
        notification=dict(flag_id=74,object=hex(FLAG),ROM_row='0x6003a564',mask=1,remains_set_after_receive=True),
        event=dict(status=0,number='0x4b',node=hex(NEW_NODE),output=hex(OUTPUT),
                   padding_hex=payload[2:4].hex(),padding_is_opaque_stack_residue=True),
        native_callback_entry='0x602a3042',native_receiver_entry='0x6020c101',
        empty_poll_return=-1,sealed_capture_sidecar_unchanged=True,kernel_and_provider_released=True,
        generic_engine_dispatcher_executed=False,selected_handler_executed=False,associated_backlink_still_old=True,
        native_api_success_stubs=False,hash_checks_performed=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['The native heap initializer is a selected cold-context construction, not an authorized reset of a live production heap. Other heap allocations and complete kernel startup have not run.',
                'Only fixed pool1 and flag74 selected ROM recipe iterations run. The full static mailbox recipe is executed; unrelated static pools/flags remain outside this test.',
                'Only headers and the one consumed message payload are mapped. Other15 payloads and the remaining heap are unmapped; this is not a whole-memory or exhaustion test.',
                'Normal callback status0 is explicit input. The registered callback runs at its complete entry with the node returned by the actual selector; generic engine completion dispatch has not run.',
                'The message copies12 bytes but defines only a2-byte status and two4-byte words. Its2 padding bytes are opaque stack residue, not asserted initialized fields.',
                'Send and poll-receive execute sequentially with the inherited task-context model. Receiver wakeup, notification clear, task handover, concurrency and dynamic mailbox deletion/recreation are not proved.',
                'The selected event handler and its associated backlink publication remain pending. Request provenance, production kernel configuration, lifetime/code/RAM closure and recovery still block installation.'])
    return report,dict(upstream=contexts,upstream_report=upstream,cases=[dict(context,
        selected_mailbox_machine=machine,selected_mailbox_send_result=sent,
        selected_mailbox_receive_result=received,selected_message_address=OUTPUT)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(selected_mailbox_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
