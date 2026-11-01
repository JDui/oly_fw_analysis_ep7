#!/usr/bin/env python3
"""Complete native postpopulation and its finish observer under explicit inputs.

Incoming flags, an unproven request halfword and a serviced sensor sample are
models. Original state/temperature stores execute before their consumer resumes.
The existing non-COLOR/repopulated capture must remain unsealed.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import require
from ep7_candidate_state_sim import CALL_SP, objects, ready_lock
from ep7_candidate_capture_sim import CAPTURE, NODE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_message_sim import result_ok
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_device_state_sim import admit
from ep7_candidate_format_record_sim import missing_bytes
from ep7_candidate_request_constructor_sim import OBJECT, PACKET
from ep7_candidate_request_metadata_sim import request_metadata_context


STATE_OUTPUTS = [(0x6223dbf2,1),(OBJECT+1666,2),(OBJECT+1684,1),(OBJECT+1686,1)]
STATE_EXPECTED = [b'\0',bytes(2),b'\x01',b'\0']


def postpopulation_finish_context(directory,prefix,engine):
    upstream,contexts = request_metadata_context(directory,prefix,engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    syms = base['syms']
    context = contexts['cases'][0]
    original = context['postpopulation_machine']
    prepared = context['metadata_machine']
    capture = prepared.read(CAPTURE,SIZE)
    require(prepared.read(0x6029d0b0,6) == bytes.fromhex('fca9eadb2362') and
            prepared.read(0x6029d10d,6) == bytes.fromhex('fcad96db2362') and
            prepared.read(0x6029d16a,1) == b'\x7d' and
            prepared.read(0x6029dd7a,26) == bytes.fromhex(
                'ddc599dcff0000fc838cdc236200fc838edc2362fc8390dc2362') and
            prepared.read(0x605e61d7,6) == bytes.fromhex('fca4984174a2'),
            'original state inputs, temperature producer or tail debug gate changed')
    require(all(prepared.read(OBJECT+offset,1) == b'\0' for offset in (1678,1696,1998,1695)),
            'native state branch prerequisites changed')
    rows,branches = [],[]
    # One targeted comparison, not a flags/temperature test matrix. Both
    # unproven incoming values remain explicit even when this branch ignores
    # them. Only the original five destination bytes are writable additions.
    for label,flags,halfword in [('zero',0,0),('all_bits',0xffffffff,0xffff)]:
        machine = prepared.clone()
        admit(machine,'modeled_incoming_command_flags',PACKET+72,struct.pack('<I',flags),'r')
        admit(machine,'modeled_unproven_request1914',OBJECT+1914,struct.pack('<H',halfword),'r')
        added = missing_bytes(machine,[address+i for address,size in STATE_OUTPUTS for i in range(size)],
                              0xa5,'native_request_state_outputs')
        require(len(added) == 5, 'native state destination extent changed')
        result = machine.run(0x6029d0b0,0x6029d1cc,overrides=dict(sp=CALL_SP),
            full_trace=True,limit=10000,breakpoints=[0x60061808,0x6040e126,syms['_ep7_gcc_quarantine']])
        result_ok(machine,result,0x6029d1cc,CALL_SP)
        require([machine.read(address,size) for address,size in STATE_OUTPUTS] == STATE_EXPECTED and
                machine.read(CAPTURE,SIZE) == capture and
                [t['d0'] for t in result['trace'] if t['pc'] == 0x6005e971] == [0x8441] and
                all(sum(t['pc'] == pc for t in result['trace']) == 1 for pc in
                    (0x602a71ae,0x602a7060,0x602a709b,0x602a7154)) and
                not any(t['pc'] in (0x602a70d8,0x6029d170,0x602a7182) for t in result['trace']),
                'native state result or current branch input independence changed')
        rows.append(stage('native_state_slice_'+label,result))
        branches.append((machine,result))
    require([t['pc'] for t in branches[0][1]['trace']] == [t['pc'] for t in branches[1][1]['trace']],
            'paired unknown inputs changed the native branch path')
    machine = branches[0][0]
    # 6006773f reads the most recently serviced sample. Supply a named raw
    # value, not a fabricated hardware conversion or a cold-zero assumption.
    admit(machine,'modeled_last_temperature_sample',0xa2716046,struct.pack('<h',25),'r')
    added = missing_bytes(machine,list(range(OBJECT+2160,OBJECT+2166)),0xa5,'native_temperature_members')
    require(len(added) == 6, 'native temperature destination extent changed')
    temperature = machine.run(0x6029dd7a,0x6029dd94,overrides=dict(sp=CALL_SP),full_trace=True,limit=1000)
    result_ok(machine,temperature,0x6029dd94,CALL_SP)
    require(machine.read(OBJECT+2160,6) == struct.pack('<3h',25,0,0) and
            sum(t['pc'] == 0x6006773f for t in temperature['trace']) == 1 and
            machine.read(CAPTURE,SIZE) == capture,
            'native temperature getter/store slice changed')
    rows.append(stage('native_temperature_getter_and_store_slice',temperature))
    # This debug gate is within the original BSS alias, before any debug
    # configuration. The four-byte state is not a logging-success stub.
    require(machine.read(0x60020068,12) == bytes.fromhex('fccd886879a2fccc00af1c62') and
            0x621caf00 <= 0xa2744198-0x40000000 < 0xa274419c-0x40000000 <= 0x62796888,
            'tail debug gate is outside the reviewed native BSS alias')
    admit(machine,'conditional_native_tail_debug_gate',0xa2744198,bytes(4),'r')
    continued_machine = machine.clone()
    continued_machine.regions['stack'] = original.regions['stack']
    continued_machine.regions['caller'] = original.regions['caller']
    sidecar = syms['_ep7_controller_sidecar_unresolved']
    old_entry = continued_machine.read(sidecar,104)
    continued = continued_machine.resume(context['postpopulation_result']['registers'],0x602a44ba,
        full_trace=True,limit=20000,breakpoints=[0x60061808,0x6040e126,syms['_ep7_gcc_quarantine']])
    result_ok(continued_machine,continued,0x602a44ba,CALL_SP)
    rows.append(stage('native_second_population_and_candidate_finish_return',continued))
    trace = continued['trace']
    observer = [t for t in trace if t['pc'] == syms['_ep7cn_population']]
    finish = [t for t in trace if t['pc'] == syms['_ep7c_finish_population']]
    require(len(observer) == len(finish) == 1 and observer[0]['d0'] == NODE and observer[0]['d1'] == 1,
            'real candidate finish observer did not receive the owned node and finish flag')
    returned = next(t for t in trace[trace.index(finish[0])+1:] if t['pc'] == finish[0]['mdr'])
    changed = [dict(offset=i,before=a,after=z) for i,(a,z) in
               enumerate(zip(capture,continued_machine.read(CAPTURE,SIZE))) if a != z]
    require(returned['d0'] == 0 and continued_machine.read(sidecar,104) == old_entry and
            continued_machine.read(sidecar+48,5) == bytes([1,0,0,1,1]) and
            continued_machine.read(CAPTURE+24053,1) == b'\0' and
            continued_machine.read(CAPTURE+24083,1) == b'\0' and
            changed == [dict(offset=14406,before=0,after=25)] and
            continued_machine.read(CAPTURE+13816,512) == bytes(512) and
            all(sum(t['pc'] == pc for t in trace) == 1 for pc in (0x602a9f16,0x605e61d7,0x4700115e)),
            'tail writes or non-COLOR/repopulation rejection changed')
    _,_,_,provider = objects(continued_machine,syms)
    ready_lock(continued_machine,provider)
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],engine=str(engine),
        cases=rows,native_instructions=sum(r['completed'] for r in rows),
        maximum_observed_new_stack_depth=max(r['stack_depth_from_call_sp'] for r in rows),
        native_store_capacity_added=11,conditional_BSS_bytes_added=4,modeled_input_bytes_added=8,
        modeled_inputs=[dict(address=hex(PACKET+72),size=4,values=[0,0xffffffff],meaning='incoming command flags'),
            dict(address=hex(OBJECT+1914),size=2,values=[0,0xffff],meaning='unproven request halfword'),
            dict(address='0xa2716046',size=2,values=[25],meaning='last serviced raw temperature sample')],
        native_state=dict(entry='0x6029d0b0',stop='0x6029d1cc',complete_enclosing_function=False,
            paired_inputs_same_PC_path=True,property_key='0x8441',property_result=0,
            state1666=0,state1684=1,state1686=0,unknown_input_sources_proven=False),
        temperature=dict(getter='0x6006773f',producer_slice=['0x6029dd7a','0x6029dd94'],
            request_halfwords=[25,0,0],hardware_sampling_executed=False),
        second_population_completed=True,normal_return_pc='0x602a44ba',normal_return_SP=hex(CALL_SP),
        finish_observer_entries=1,finish_observer_flag=1,finish_core_return=0,
        old_sidecar_entry_unchanged=True,raw_mode=0,selector=0,sealed=False,
        capture_changes=changed,native_tail_memset_bytes=512,private_lock_released=True,
        full_controller_callback_completed=False,full_request_producer_completed=False,
        hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['Incoming command+72 and request+1914 remain unproven6B modeled inputs. Two paired values take the same path; this is not universal validation across other native states.',
                'Only6029d0b0..d1cc executes, including three complete native helpers. Earlier format preparation and the rest of6029d089 are outside this slice; full command/dispatcher ordering remains unresolved.',
                'The temperature producer is the original6029dd7a..dd94 slice with an explicit most-recent-sample value25. No sensor acquisition, conversion, unit or full surrounding callback is qualified.',
                'The original debug gate has a4B cold-BSS condition. Existing kernel, task handover, registry, node/capture and hardware models remain inherited boundaries.',
                'The actual second population now returns through its real candidate finish observer. Existing raw mode0/selector0 and repopulated token remain unqualified; core finish returns false and does not seal stale data.',
                'Valid COLOR from native settings, fresh allocation generations, asynchronous worker/lifetime, code/RAM residency and backup/recovery remain unresolved.'])
    return report,dict(upstream=contexts,upstream_report=upstream,cases=[dict(context,
        request_state_machine=machine,request_state_result=branches[0][1],temperature_result=temperature,
        postpopulation_machine=continued_machine,postpopulation_result=continued)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(postpopulation_finish_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
