#!/usr/bin/env python3
"""Complete native request preparation and mode classification before metadata.

Camera status inputs retain the explicit prepublication cold scenario. Native
state stores replace an overbroad synthetic FIFO guard, not firmware memory.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import require
from ep7_candidate_state_sim import CALL_SP
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_message_sim import native_call, result_ok
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_device_state_sim import admit
from ep7_candidate_format_record_sim import missing_bytes
from ep7_candidate_geometry_sim import map_initializer_storage
from ep7_candidate_request_constructor_sim import OBJECT, PACKET
from ep7_candidate_request_resources_sim import request_resources_context


def request_preparation_context(directory,prefix,engine):
    upstream,contexts = request_resources_context(directory,prefix,engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    context = contexts['cases'][0]
    original = context['postpopulation_machine']
    machine = original.clone()
    capture = machine.read(CAPTURE,SIZE)
    machine.regions['stack'] = replace(machine.regions['stack'],data=b'\xcc'*len(machine.regions['stack'].data))
    members = [(1940,1),(1941,1),(1996,1),(1698,2),(2388,1),(2389,1),(1668,2),(1682,2),(1702,2)]
    gaps = missing_bytes(machine,[OBJECT+offset+i for offset,size in members for i in range(size)]+
        list(range(0x6223dbae,0x6223dbb0)),0xa5,'native_request_prepare_members')
    require(len(gaps) == 15, 'native request preparation member extent changed')
    # These fields, like inherited camera status622351bc, have not yet received
    # an asynchronous status publication. Do not map the rest of the records.
    cold = [(0x622351a5,1),(0x62235104,1),(0x62235124,1),(0x62235108,12),(0x622351c0,1)]
    require(machine.read(0x60020068,12) == bytes.fromhex('fccd886879a2fccc00af1c62') and
            all(0x621caf00 <= address < address+size <= 0x62796888 for address,size in cold),
            'prepublication sample fields are outside original BSS')
    for address,size in cold:
        admit(machine,f'request_prepublication_sample_{address:x}',address,bytes(size),permissions='r')
    # Original direct stores602ac0a5..602ac0e7 prove that13 bytes of this older
    # probe's synthetic guard are real state. Retain the remaining3-byte guard
    # immediately before the FIFO and keep its124-byte object untouched.
    guard = machine.regions.pop('native_wait_fifo_before')
    require(guard.address == 0x6223e7cc and guard.data == b'\x5a'*16 and
            machine.regions['native_wait_fifo'].address == 0x6223e7dc,
            'inherited FIFO fixture boundary changed')
    machine.regions[guard.name] = replace(guard,address=0x6223e7d9,data=guard.data[13:])
    fifo = {name:machine.regions[name].data for name in
        ('native_wait_fifo_before','native_wait_fifo','native_wait_fifo_after')}
    stores,ranges = map_initializer_storage(machine,directory,prefix,[(0x602abfa1,0x602ac0f7)],
        [(0x6223e798,0x6223e7d9)],[(0x6223d408,0x6223d410)],name_prefix='native_request_preparation_state')
    require(sum(high-low for low,high in ranges) == 68 and len(stores) == 34,
            'native request staging record or four counters changed')
    service_gaps = missing_bytes(machine,[0x622351b8,0x622351ba,0x622351bb]+
        list(range(0x622351c8,0x622351cc)),0xa5,'native_request_service_refresh')
    require(len(service_gaps) == 7, 'native service-refresh output extent changed')
    prepared = native_call(machine,base['syms'],0x602a4a5c,0xf0,104,
        dict(a0=OBJECT,a1=PACKET),limit=20000)
    values = []
    for store in stores:
        executed = [t for t in prepared['trace'] if t['pc'] == store['pc']]
        require(len(executed) == 1, 'native staging store did not execute exactly once')
        value = executed[0][store['register']] & ((1 << (8*store['width']))-1)
        require(machine.read(store['address'],store['width']) == value.to_bytes(store['width'],'little'),
                'native staging member differs from its actual store')
        values.append(dict(pc=hex(store['pc']),address=hex(store['address']),bytes=store['width'],value=value))
    require(all(int.from_bytes(machine.read(OBJECT+offset,size),'little') == (1 if offset == 1682 else 0)
                for offset,size in members) and machine.read(0x6223d408,8) == bytes(8) and
            all(sum(t['pc'] == pc for t in prepared['trace']) == 1 for pc in
                (0x6054c22a,0x6054c12c,0x6028f547,0x602abfa1,0x6029bd16)),
            'complete request preparation or native helper sequence changed')
    # Use original reset slices for mode-classification inputs, not new BSS.
    require(machine.read(0x6011158c,13) == bytes.fromhex('00fc837cae1d62fc837eae1d62') and
            machine.read(0x6010b06a,19) == bytes.fromhex('00fc821c971d62fc821d971d62fc83729f1d62'),
            'original device-mode reset slices changed')
    admit(machine,'native_device_mode_status_reset',0x621dae7c,b'\xa5'*4)
    reset = machine.run(0x6011158c,0x60111599,overrides=dict(sp=CALL_SP),full_trace=True,limit=100)
    result_ok(machine,reset,0x60111599,CALL_SP)
    fallback_gaps = missing_bytes(machine,[0x621d971c,0x621d971d,0x621d9f72,0x621d9f73],
        0xa5,'native_mode_fallback_reset')
    fallback = machine.run(0x6010b06a,0x6010b07d,overrides=dict(sp=CALL_SP),full_trace=True,limit=100)
    result_ok(machine,fallback,0x6010b07d,CALL_SP)
    mode_gaps = missing_bytes(machine,range(OBJECT+1672,OBJECT+1675),0xa5,'native_request_mode_outputs')
    require(len(fallback_gaps) == 4 and len(mode_gaps) == 3, 'mode reset/output extent changed')
    classified = native_call(machine,base['syms'],0x602a6630,0x20,8,dict(a0=OBJECT),limit=10000)
    require(machine.read(OBJECT+1672,3) == bytes.fromhex('000001') and
            machine.read(0x621dae7c,4) == bytes(4) and machine.read(0x621d9f72,2) == bytes(2) and
            machine.read(0x621d971c,2) == bytes(2) and machine.read(CAPTURE,SIZE) == capture and
            all(machine.regions[name].data == data for name,data in fifo.items()) and
            machine.read(PACKET+60,4) == bytes(4) and
            not any(r.address <= OBJECT+1684 < r.address+len(r.data) for r in machine.regions.values()),
            'mode classification changed capture/FIFO or invented unproduced metadata')
    rows = [stage(name,result) for name,result in (
        ('complete_native_request_preparation',prepared),('native_device_mode_reset_slice',reset),
        ('native_mode_fallback_reset_slice',fallback),('complete_native_request_mode_classification',classified))]
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],engine=str(engine),
        cases=rows,native_instructions=sum(r['completed'] for r in rows),
        maximum_observed_new_stack_depth=max(r['stack_depth_from_call_sp'] for r in rows),
        native_store_capacity_added=101,newly_unmapped_store_bytes=88,former_synthetic_guard_bytes_reclassified=13,
        conditional_BSS_bytes_added=16,cold_inputs=[dict(address=hex(a),bytes=n) for a,n in cold],
        complete_request_preparation=True,native_staging_member_stores=values,
        four_native_counters_reset=True,native_mode_outputs=dict(offset1672_halfword=0,offset1674_byte=1),
        FIFO=dict(address='0x6223e7dc',bytes=124,unchanged=True,remaining_before_guard_address='0x6223e7d9',
            remaining_before_guard_bytes=3,after_guard_bytes=16,guards_unchanged=True),
        capture_unchanged=True,postpopulation_resumed=False,
        pending_metadata=dict(command_pointer_offset=60,command_pointer_value=0,request_members=[1684,1686],
            original_metadata_claim='0x602a7556',original_metadata_initialize='0x602ab5e4'),
        hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['16 status/sample bytes retain the already-declared first-publication BSS condition. They are not sensor measurements or active camera parameters; neighboring fields remain unmapped.',
                'Complete602a4a5c and its real service refresh/staging helpers run, followed by complete602a6630. Two original mode reset slices supply8 bytes; their enclosing device tasks and lifecycle are not executed.',
                '13 bytes of an older16-byte FIFO-before canary overlap proven original staging stores. Only those bytes become writable native state;3 remaining bytes, the124-byte FIFO and its16-byte after-guard remain unchanged.',
                'Preparation starts from the latest paused consumer context, preserving its already-written capture fields, but does not resume it or execute whole controller dispatch.',
                'Command+60 remainsNULL and request1684/1686 remain unproduced. Native metadata claim/initialization and publication, second population/finish, valid COLOR, residency and recovery remain unresolved.'])
    return report,dict(upstream=contexts,upstream_report=upstream,cases=[dict(context,
        preparation_machine=machine,preparation_result=prepared,mode_result=classified)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(request_preparation_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
