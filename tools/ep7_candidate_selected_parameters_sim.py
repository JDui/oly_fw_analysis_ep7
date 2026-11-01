#!/usr/bin/env python3
"""Construct native selected-event parameters and preserve the next source frontier.

Original sequence/scene initialization and the complete descriptor constructor
execute. The actual selected handler finishes its first parameter helper, then
stops on unproduced request metadata; no exposure result is synthesized.
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
from ep7_candidate_request_constructor_sim import OBJECT, PACKET
from ep7_candidate_request_metadata_sim import METADATA
from ep7_candidate_selected_mailbox_sim import selected_mailbox_context, OUTPUT


DESCRIPTOR_A,DESCRIPTOR_B = OBJECT+108,OBJECT+164
A_MEMBERS = ((0,5),(12,4),(24,6))
B_MEMBERS = ((0,10),(12,17),(30,10),(64,3),(68,3),(72,18))


def selected_parameters_context(directory,prefix,engine):
    upstream,contexts = selected_mailbox_context(directory,prefix,engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    syms = base['syms']
    context = contexts['cases'][0]
    machine = context['selected_mailbox_machine'].clone()
    sidecar = syms['_ep7_controller_sidecar_unresolved']
    sealed = machine.read(sidecar,664)
    capture,old_capture = machine.read(NEW_CAPTURE,SIZE),machine.read(CAPTURE,SIZE)
    require(machine.read(0x602979f8,26) == bytes.fromhex(
                '00fc83acce2362fc83b0ce2362fc83aece2362fc82b2ce2362de') and
            machine.read(0x6029cf81,37) == bytes.fromhex(
                'fca848dd2362a001c90afccc19000100ca08fccc00000100fcdcd4db2362dde5e02a00f014') and
            machine.read(0x6223d414,4) == struct.pack('<I',PACKET) and
            machine.read(PACKET,4) == struct.pack('<I',2) and
            machine.read(PACKET+60,4) == struct.pack('<I',METADATA) and
            machine.read(OBJECT+2348,1) == b'\0', 'native initialization or current request inputs changed')
    added = missing_bytes(machine,range(0x6223ceac,0x6223ceb3),0xa5,'native_selected_sequence_state')
    require(len(added) == 7,'selected sequence state overlaps prior storage')
    sequence_init = native_call(machine,syms,0x602979f8,0,0)
    require(machine.read(0x6223ceac,7) == bytes(7),'original sequence initializer did not reset its members')
    require(len(missing_bytes(machine,[OBJECT+1976],0xa5,'native_selected_scene_status')) == 1,
            'native scene status overlaps prior storage')
    scene_init = machine.run(0x6029cf81,0x6029cfa6,overrides=dict(sp=CALL_SP),full_trace=True,limit=3000)
    result_ok(machine,scene_init,0x6029cfa6,CALL_SP)
    require(machine.read(OBJECT+1976,1) == b'\0' and
            sum(t['pc'] == 0x6054b084 and t['d0'] == 0x10000 for t in scene_init['trace']) == 1 and
            sum(t['pc'] == 0x6005e971 and t['d0'] == 0x85c1 for t in scene_init['trace']) == 1,
            'original property-based scene gate changed')
    extents = [(base+o,n) for base,members in ((DESCRIPTOR_A,A_MEMBERS),(DESCRIPTOR_B,B_MEMBERS))
               for o,n in members]
    require(len(missing_bytes(machine,[a+i for a,n in extents for i in range(n)],
        0xa5,'native_selected_descriptors')) == 76,'native descriptor store extent changed')
    # This actual caller loads both pointers from original globals and invokes
    # the complete constructor. The outer controller callback is not replayed.
    descriptor_init = machine.run(0x6029d09c,0x6029d0af,overrides=dict(sp=CALL_SP),full_trace=True,limit=3000,
        breakpoints=[0x60061808,0x6040e126,syms['_ep7_gcc_quarantine']])
    result_ok(machine,descriptor_init,0x6029d0af,CALL_SP)
    trace = descriptor_init['trace']
    row = next(t['a0'] for t in trace if t['pc'] == 0x605558d3)
    copies = ((16,6,12),(28,28,1),(30,26,2),(32,18,8),(66,28,1),(70,28,1),(74,36,16))
    require(row == 0x6055d290 and
            machine.read(DESCRIPTOR_A,5) == struct.pack('<IB',10,0) and
            all(machine.read(DESCRIPTOR_A+o,n) == bytes(n) for o,n in ((12,4),(24,6))) and
            machine.read(DESCRIPTOR_B,10) == struct.pack('<2IH',
                int.from_bytes(machine.read(row+32,4),'little')|1,0xffffffff,1) and
            all(machine.read(DESCRIPTOR_B+dest,size) == machine.read(row+source,size)
                for dest,source,size in copies) and
            machine.read(DESCRIPTOR_B+64,2) == struct.pack('<H',0x3fff) and
            machine.read(DESCRIPTOR_B+68,2) == struct.pack('<H',2048) and
            machine.read(DESCRIPTOR_B+72,2) == struct.pack('<H',3) and
            machine.read(DESCRIPTOR_B+12,4) == struct.pack('<I',0xaf43ad40) and
            [(t['d0'],t['a0']) for t in trace if t['pc'] == 0x6029b986] == [(2,DESCRIPTOR_B)] and
            [t['d0'] for t in trace if t['pc'] == 0x603dba87] == [0x102],
            'native descriptors, selected ROM row or actual capture2 resource pointer changed')
    require(machine.read(NEW_CAPTURE,SIZE) == capture and machine.read(sidecar,664) == sealed,
            'parameter preparation changed the previously sealed capture')
    prepared = machine.clone()
    machine.regions['caller'] = replace(machine.regions['caller'],
        data=b'\xdd'+struct.pack('<i',0x602a281a-CALLER)+bytes([0,0]))
    machine.regions['stack'] = replace(machine.regions['stack'],data=b'\xcc'*len(machine.regions['stack'].data))
    frontier = machine.run(CALLER,CALLER+7,overrides=dict(sp=CALL_SP,a0=OUTPUT),full_trace=True,limit=3000,
        breakpoints=[0x60061808,0x6040e126,syms['_ep7_gcc_quarantine']])
    trace = frontier['trace']
    require(frontier['status'] == 'memory_fault' and frontier['fault'] == dict(
                kind=1,pc=0x602a92df,map=0,address=METADATA+50,size=2,access='read') and
            frontier['registers']['a0'] == METADATA+48 and
            [(t['d0'],t['a0']) for t in trace if t['pc'] == 0x602a8877] == [(2,OBJECT)] and
            sum(t['pc'] == 0x602a2838 for t in trace) == 1 and
            sum(t['pc'] == 0x602a91ee for t in trace) == 1 and
            not any(t['pc'] in (0x602a2841,0x602a2903,0x602ac141) for t in trace),
            'actual selected handler no longer stops at the unproduced request metadata')
    after = machine.read(NEW_CAPTURE,SIZE)
    changed = [(i,x,y) for i,(x,y) in enumerate(zip(capture,after)) if x != y]
    require(changed == [(3708,0,5),(3712,0,16),(3718,0,1),(24177,0,4),(24184,0,217),
                        (24185,0,4),(24191,0,2),(24212,0,85)] and
            machine.read(sidecar,664) == sealed and machine.read(CAPTURE,SIZE) == old_capture and
            sparse_read(machine,ASSOCIATED+8,4) == struct.pack('<I',NODE),
            'native partial capture writes, sealed snapshot or old backlink changed')
    _,_,_,provider = objects(machine,syms)
    ready_lock(machine,provider)
    cases = [stage(name,result) for name,result in (
        ('complete_native_sequence_state_reset',sequence_init),('native_scene_status_producer',scene_init),
        ('actual_caller_and_complete_descriptor_constructor',descriptor_init),
        ('selected_handler_request_metadata_frontier',frontier))]
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],engine=str(engine),
        cases=cases,native_instructions=sum(r['completed'] for r in cases),
        maximum_observed_new_stack_depth=max(r['stack_depth_from_call_sp'] for r in cases),
        native_store_capacity_added=84,conditional_BSS_bytes_added=0,
        sequence_state=dict(initializer='0x602979f8',address='0x6223ceac',bytes=7),
        scene_state=dict(caller='0x6029cf81..0x6029cfa6',initializer='0x6054b084',
                         address=hex(OBJECT+1976),property='0x85c1',active=False),
        descriptors=dict(caller='0x6029d09c..0x6029d0af',constructor='0x602a6583',
            class_value='0x10000',first_address=hex(DESCRIPTOR_A),first_kind=10,
            second_address=hex(DESCRIPTOR_B),ROM_row=hex(row),capture_id=2,
            resource_handle='0x102',resource_pointer='0xaf43ad40',native_store_bytes=76),
        selected_handler=dict(entry='0x602a281a',message=hex(OUTPUT),node=hex(NEW_NODE),
            first_helper='0x602a8877',first_helper_return='0x602a2838',first_helper_completed=True,
            first_helper_return_trace_index=next(i for i,t in enumerate(trace) if t['pc'] == 0x602a2838),
            pending_helper='0x602a91ee',metadata=hex(METADATA),unproduced_metadata_offsets=[48,50,52],
            fault=frontier['fault'],completed=False),
        partial_capture_changes=[dict(offset=i,before=x,after=y) for i,x,y in changed],
        sidecar_sealed_snapshot_unchanged=True,associated_backlink_still_old=True,
        native_api_success_stubs=False,hash_checks_performed=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['The selected sequence reset, scene caller suffix and descriptor caller suffix construct independent context at original native entries. The complete controller startup/request callback and its temporal legality are not executed.',
                'Both descriptor helpers run completely with the actual current command/capture2 and ROM data. Their backing image is unmapped; descriptor construction is not engine completion or a sensor frame.',
                'The selected handler runs from its complete entry on the actual mailbox output. Only602a8877 finishes;602a91ee stops at the first unknown metadata halfword. No arbitrary zero/default/exposure value is supplied.',
                'The8 changed capture bytes are real partial native post-selection stores, not a completed handler or finished output. The sealed sidecar remains unchanged; the continuation retains its live stack/registers.',
                'Metadata slot0 remains the earlier native claimed request record, whose48/50/52 result fields have not been produced. Full new-request provenance and device inputs remain unresolved.',
                'Backlink publication, async consumption/release, scheduling, complete kernel initialization, code/RAM ownership and recovery still block installation.'])
    return report,dict(upstream=contexts,upstream_report=upstream,cases=[dict(context,
        selected_parameters_machine=prepared,selected_parameters_result=descriptor_init,
        selected_handler_machine=machine,selected_handler_result=frontier)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(selected_parameters_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
