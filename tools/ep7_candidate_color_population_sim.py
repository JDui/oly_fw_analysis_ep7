#!/usr/bin/env python3
"""Complete native COLOR4 population on a newly allocated capture and freeze H/L.

The actual caller enqueues its node, copies the original template, and executes
both population functions and candidate observers. Request/hardware inputs keep
their inherited explicit offline assumptions; no active camera claim is made.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import require
from ep7_candidate_state_sim import CALL_SP, INPUT, SNAPSHOT, gcc_call, objects, ready_lock
from ep7_candidate_capture_sim import CAPTURE, ASSOCIATED, NODE
from ep7_candidate_capture_template_sim import SIZE, TEMPLATE
from ep7_candidate_message_sim import result_ok
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_format_record_sim import missing_bytes, coalesce_record
from ep7_candidate_capture_allocation_sim import NEW_CAPTURE
from ep7_candidate_node_factory_sim import node_factory_context, NEW_NODE, sparse_read


def color_population_context(directory,prefix,engine):
    upstream,contexts = node_factory_context(directory,prefix,engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    syms = base['syms']
    context = contexts['cases'][0]
    machine = context['node_machine'].clone()
    sidecar = syms['_ep7_controller_sidecar_unresolved']
    old_capture = machine.read(CAPTURE,SIZE)
    old_registry = sparse_read(machine,0x6223d190,24)
    template = machine.read(TEMPLATE,SIZE)
    caller_stack,caller_code = machine.regions['stack'],machine.regions['caller']
    machine.regions['stack'] = replace(caller_stack,data=b'\xcc'*len(caller_stack.data))
    require(machine.read(0x6029c64e,33) == bytes.fromhex(
                'fcdc18e32362fc8014e323622c2b044204fcdd2ce32362800481dde1f2f6ff8004') and
            machine.read(0x60300055,10) == bytes.fromhex('fcdd2c8825622d4fe5db') and
            machine.read(0x6223e33c,2) == struct.pack('<H',1) and
            machine.read(0x6223dd4c,4) == bytes(4),
            'native pending-node FIFO, template-copy bound or inherited admission state changed')
    fifo_bytes = missing_bytes(machine,list(range(0x6223e314,0x6223e32a))+
        list(range(0x6223e32c,0x6223e330)),0xa5,'native_pending_node_FIFO')
    require(len(fifo_bytes) == 26, 'pending-node FIFO store extent changed')
    fifo = machine.run(0x6029c64e,0x6029c66f,overrides=dict(sp=CALL_SP),full_trace=True,limit=1000)
    result_ok(machine,fifo,0x6029c66f,CALL_SP)
    require(machine.read(0x6223e314,22) == struct.pack('<IIHHIHHH',
        0x6223e318,1067,4,4,0x6223e32c,0,0,0), 'native pending-node FIFO initialization changed')
    capture_bytes = missing_bytes(machine,range(NEW_CAPTURE,NEW_CAPTURE+SIZE),
        0xa5,'native_new_capture_template_copy')
    require(len(capture_bytes) == SIZE-2 and
            machine.read(NEW_CAPTURE+27078,2) == bytes(2), 'new capture copy capacity changed')
    coalesce_record(machine,NEW_CAPTURE,SIZE,'native_new_capture')
    _,_,core,provider = objects(machine,syms)
    original_hl = [5]+[0]*11+[-3]+[0]*11
    later_hl = [-3]+[0]*11+[2]+[0]*11
    frozen = struct.pack('<B24b',3,*original_hl)
    later = struct.pack('<B24b',3,*later_hl)
    machine.mutate('settings',0,struct.pack('<24b',*original_hl))
    edited = gcc_call(machine,syms,'_ep7p_edit',[core,3,INPUT],wanted=1)
    machine.regions['stack'],machine.regions['caller'] = caller_stack,caller_code
    stops = [0x60061808,0x6040e126,syms['_ep7_gcc_quarantine']]
    copied = machine.resume(context['node_result']['registers'],0x602a7eb0,
        full_trace=True,limit=70000,breakpoints=stops)
    result_ok(machine,copied,0x602a7eb0,CALL_SP-40)
    require(machine.read(NEW_CAPTURE,SIZE) == template and
            sum(t['pc'] == 0x60300061 for t in copied['trace']) == 6833 and
            sum(t['pc'] == 0x602a3204 for t in copied['trace']) == 1 and
            machine.read(0x6223e318+12,6) == struct.pack('<3H',1,1,0) and
            machine.read(0x6223e32c,4) == struct.pack('<I',NEW_NODE),
            'actual caller did not enqueue the new node and copy all6833 template words')
    first = machine.resume(copied['registers'],0x602a44a8,
        full_trace=True,limit=50000,breakpoints=stops)
    result_ok(machine,first,0x602a44a8,CALL_SP)
    after_first = machine.read(sidecar,664)
    records = {r['key']:r for r in base['property_records']}
    require(machine.read(NEW_CAPTURE+24053,1) == machine.read(records[0x9481]['data'],1) == b'\x0b' and
            machine.read(NEW_CAPTURE+24083,1) == machine.read(records[0xf6b1]['data'],1) == b'\x04' and
            after_first[48:53] == bytes([1,1,0,1,0]) and after_first[76:101] == frozen and
            struct.unpack_from('<5I',after_first,56) == (ASSOCIATED,NEW_CAPTURE,2,11,4) and
            sum(t['pc'] == 0x6005d924 for t in first['trace']) == 99 and
            sum(t['pc'] == syms['_ep7p_capture'] for t in first['trace']) == 1,
            'complete native COLOR4 population did not sample the configured H/L once')
    first_machine = machine.clone()
    population_stack,population_caller = machine.regions['stack'],machine.regions['caller']
    machine.mutate('settings',0,struct.pack('<24b',*later_hl))
    changed = gcc_call(machine,syms,'_ep7p_edit',[core,3,INPUT],wanted=1)
    readback = gcc_call(machine,syms,'_ep7p_capture',[core,11,4,SNAPSHOT],wanted=1)
    require(machine.read(SNAPSHOT,25) == later and machine.read(sidecar,664) == after_first,
            'the intervening real settings edit failed to change live profile or changed the sampled sidecar')
    machine.regions['stack'],machine.regions['caller'] = population_stack,population_caller
    finished = machine.resume(first['registers'],0x602a44ba,
        full_trace=True,limit=50000,breakpoints=stops)
    result_ok(machine,finished,0x602a44ba,CALL_SP)
    expected = bytearray(after_first)
    expected[48:53] = bytes([1,0,1,1,1])
    finish_entries = [(i,t) for i,t in enumerate(finished['trace'])
                      if t['pc'] == syms['_ep7c_finish_population']]
    require(len(finish_entries) == 1, 'core finish must execute exactly once')
    index,entry = finish_entries[0]
    finish_return = next(t for t in finished['trace'][index+1:] if t['pc'] == entry['mdr'])
    require(finish_return['d0'] == 1 and machine.read(sidecar,664) == expected and
            machine.read(sidecar+76,25) == frozen and machine.read(SNAPSHOT,25) == later and
            not any(t['pc'] == syms['_ep7p_capture'] for t in finished['trace']) and
            machine.read(NEW_CAPTURE+13816,512) == bytes(512) and
            machine.read(NEW_CAPTURE+24053,1) == b'\x0b' and machine.read(NEW_CAPTURE+24083,1) == b'\x04',
            'native finish failed to seal the original sampled H/L or resampled changed settings')
    all_population = copied['trace']+first['trace']+finished['trace']
    require([(t['d0'],t['d1']) for t in all_population if t['pc'] == syms['_ep7cn_prewrite']] ==
                [(NEW_CAPTURE,0),(NEW_CAPTURE,1)] and
            [(t['d0'],t['d1']) for t in all_population if t['pc'] == syms['_ep7cn_population']] ==
                [(NEW_NODE,0),(NEW_NODE,1)] and
            machine.read(CAPTURE,SIZE) == old_capture and sparse_read(machine,0x6223d190,24) == old_registry and
            machine.read(TEMPLATE,SIZE) == template and
            sparse_read(machine,ASSOCIATED+8,4) == struct.pack('<I',NODE),
            'actual observer identity/order or preserved old data changed')
    ready_lock(machine,provider)
    cases = [stage(name,result) for name,result in (
        ('native_pending_node_FIFO_constructor',fifo),('candidate_COLOR4_HL_edit_before_population',edited),
        ('actual_caller_node_enqueue_prewrite_and_template_copy',copied),
        ('native_COLOR4_first_population_and_sample',first),('candidate_COLOR4_HL_edit_after_sample',changed),
        ('candidate_live_COLOR4_readback_after_edit',readback),('native_second_population_and_sealed_finish',finished))]
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],engine=str(engine),
        cases=cases,native_instructions=sum(r['completed'] for r in cases),
        maximum_observed_new_stack_depth=max(r['stack_depth_from_call_sp'] for r in cases),
        native_copy_store_bytes_added=len(fifo_bytes)+len(capture_bytes),conditional_BSS_bytes_added=0,
        pending_node_FIFO=dict(address='0x6223e318',capacity=4,element_bytes=4,count=1,queued_node=hex(NEW_NODE)),
        capture=dict(id=2,address=hex(NEW_CAPTURE),native_template_words=6833,
            first_population_completed=True,second_population_completed=True,raw_mode=11,selector=4,
            first_population_property_calls=99,tail512_native_clear_verified=True),
        sidecar=dict(token=2,sample_calls=1,finish_calls=1,finish_return=1,sealed=True,
            original_profile_index=3,frozen_HL=original_hl,later_live_HL=later_hl,
            intervening_native_edit_and_readback=True,finish_resampled=False,
            flags_after_first=list(after_first[48:53]),flags_after_finish=list(expected[48:53])),
        population_envelope_continuation_PC='0x602a44ba',return_SP=hex(CALL_SP),
        old_capture_registry_template_unchanged=True,associated_backlink_still_old=True,
        whole_new_request_constructed=False,asynchronous_capture_consumption_completed=False,
        hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['Native pending-node FIFO setup is an independent original constructor slice; inherited admission inputs remain flag6223e33c=1 and pointer6223dd4c=0. This is not proof of live queue startup/reset ordering.',
                'The complete actual caller path from602a4485 through602a44ba executes around the two population calls. Its enclosing request dispatcher and later outer-function suffix have not executed.',
                'Existing request/format/metadata state comes from earlier explicit-input simulations, originally prepared for ID1. The factory updates the command ID to2, but no whole new request producer or active sensor/format lifecycle is established here.',
                'The fixed clock/register/temperature inputs, unavailable-device/unconfigured-format scenarios and single-task kernel conditions remain inherited. Passing COLOR snapshot admission does not establish a valid physical exposure.',
                'Two H/L values are explicit trusted API inputs. Candidate edit/readback use actual native private-lock routines; GUI input delivery and NVM persistence are not exercised.',
                'The selected event has not published the new associated backlink. It still points to the old node and cannot yet authorize immediate source copy or a downstream asynchronous job.',
                'Production kernel startup, full lifecycle exclusion, code/RAM residency and backup/recovery remain unresolved.'])
    return report,dict(upstream=contexts,upstream_report=upstream,cases=[dict(context,
        color_first_machine=first_machine,color_first_result=first,
        color_capture_machine=machine,color_capture_result=finished)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(color_population_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
