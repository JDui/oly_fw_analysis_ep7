#!/usr/bin/env python3
"""Construct native Standby parameters without resuming the waiting population.

The original parameter helpers, argument publication and entry callback execute.
Controller dispatch/event ordering and a live incoming command remain separate.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import CALLER, require
from ep7_candidate_state_sim import CALL_SP
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_message_sim import native_call, result_ok
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_device_state_sim import admit
from ep7_candidate_format_record_sim import missing_bytes, coalesce_record
from ep7_candidate_geometry_sim import map_initializer_storage
from ep7_candidate_postpopulation_clock_sim import postpopulation_clock_context


def standby_parameters_context(directory,prefix,engine):
    upstream,contexts = postpopulation_clock_context(directory,prefix,engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    context = contexts['cases'][0]
    original = context['postpopulation_machine']
    machine = original.clone()
    capture = machine.read(CAPTURE,SIZE)
    machine.regions['stack'] = replace(machine.regions['stack'],data=b'\xcc'*len(machine.regions['stack'].data))
    require(machine.read(0x6042d64c,20) == struct.pack('<5I',11,0x6042d470,0x6029c6c3,0x6042bf2c,0x6042bf8c) and
            machine.read(0x6042d470,8) == b'Standby\0' and
            machine.read(0x602aeb0e,15) == bytes.fromhex('00fc81c0ec2362ca08fc80c0ec2362'),
            'native Standby callback binding changed')
    # Complete original service initializer, including its real18-byte FIFO
    # header. Queue payloads and all unwritten surrounding bytes stay unmapped.
    camera_stores,camera_ranges = map_initializer_storage(machine,directory,prefix,
        [(0x6020aedb,0x6020b00c),(0x6020b344,0x6020b373),(0x6020b373,0x6020b3b3)],
        [(0x622350e8,0x62235308)],[(0x622352e4,0x622352ec),(0x622351d0,0x622351e2)],
        name_prefix='native_request_camera_service')
    require(sum(high-low for low,high in camera_ranges) == 139, 'camera service write extent changed')
    camera = native_call(machine,base['syms'],0x6020aedb,0,8,limit=2000)
    require(machine.read(0x622350f0,4) == bytes(4) and
            machine.read(0x622351b6,2) == bytes(2) and
            machine.read(0x622351d0,18) == struct.pack('<IHHIHHH',1028,4,16,0x622351e4,0,0,0) and
            machine.read(0x622352e4,8) == bytes(8),
            'complete native camera service initialization changed')
    # This member has no store in that initializer. It explicitly inherits the
    # original startup BSS clear before the first asynchronous status publish.
    require(machine.read(0x60020068,12) == bytes.fromhex('fccd886879a2fccc00af1c62') and
            0x621caf00 <= 0x622351bc < 0x62796888,
            'prepublication status byte is outside the native BSS range')
    admit(machine,'request_prepublication_camera_status',0x622351bc,bytes(1),permissions='r')
    admit(machine,'native_controller_device_flag',0x6223ed0c,b'\xa5')
    flag_reset = machine.run(0x602ada71,0x602ada78,overrides=dict(sp=CALL_SP),full_trace=True,limit=100)
    result_ok(machine,flag_reset,0x602ada78,CALL_SP)
    flag_update = machine.run(0x602ada92,0x602adaa6,overrides=dict(sp=CALL_SP),full_trace=True,limit=2000)
    result_ok(machine,flag_update,0x602adaa6,CALL_SP)
    require(machine.read(0x6223ed0c,1) == b'\0' and
            sum(t['pc'] == 0x6054c475 for t in flag_update['trace']) == 1 and
            not any(t['pc'] == 0x602adaa0 for t in flag_update['trace']),
            'native controller flag gate no longer retains its reset value')
    gaps = missing_bytes(machine,range(0x6223eca0,0x6223ecb0),0xa5,'native_request_parameter_source')
    require(len(gaps) == 15, 'upstream controller variant mapping changed')
    coalesce_record(machine,0x6223eca0,16,'native_request_parameter_source')
    flags = original.read(0x6223ed28,4)
    require(flags == bytes(4), 'inherited controller request flags changed')
    # Isolate only the two observed reads of incoming-message+8. The other72
    # bytes of a hypothetical command packet are not fabricated or mapped.
    admit(machine,'request_flags_projection',0x19c00008,flags,permissions='r')
    initial = native_call(machine,base['syms'],0x602af4c7,0x20,8,
        dict(a0=0x19c00000,a1=0x6223eca0),limit=10000)
    selected = machine.run(0x602ae0c5,0x602ae0d6,overrides=dict(sp=CALL_SP),full_trace=True,limit=2000)
    result_ok(machine,selected,0x602ae0d6,CALL_SP)
    refreshed = native_call(machine,base['syms'],0x602af50c,0x20,8,limit=20000)
    parameter = machine.read(0x6223eca0,16)
    require(parameter == bytes.fromhex('01000000000000000200000000000000'),
            'complete native parameter record changed')
    admit(machine,'native_standby_parameter_record',0x6223ecb0,b'\xa5'*16)
    admit(machine,'native_standby_parameter_pair',0x6223ecc0,b'\xa5'*8)
    arguments = machine.run(0x602aeb0e,0x602aeb36,overrides=dict(sp=CALL_SP),full_trace=True,limit=1000)
    result_ok(machine,arguments,0x602aeb36,CALL_SP)
    expected = parameter[:10]+parameter[13:14]+parameter[10:13]+parameter[14:]
    require(machine.read(0x6223ecb0,16) == expected and
            machine.read(0x6223ecc0,8) == struct.pack('<2I',0,0x6223ecb0) and
            arguments['registers']['d0'] == 11 and arguments['registers']['d1'] == 0x6223ecc0,
            'native Standby argument copy, permutation or null command branch changed')
    stores,ranges = map_initializer_storage(machine,directory,prefix,[(0x6029c6c3,0x6029c809)],
        [(0x6223d414,0x6223d41c),(0x6223da98,0x6223dd70),(0x6223e44c,0x6223e44d),
         (0x6223e674,0x6223e680)],name_prefix='native_standby_object')
    require(sum(high-low for low,high in ranges) == 44, 'native Standby member extent changed')
    entered = native_call(machine,base['syms'],0x6029c6c3,0,0,dict(d0=11,d1=0x6223ecc0),limit=10000)
    values = []
    for store in stores:
        executed = [t for t in entered['trace'] if t['pc'] == store['pc']]
        require(len(executed) == 1, 'Standby direct member store did not execute exactly once')
        value = executed[0][store['register']] & ((1 << (8*store['width']))-1)
        require(machine.read(store['address'],store['width']) == value.to_bytes(store['width'],'little'),
                'Standby member differs from actual native store')
        values.append(dict(pc=hex(store['pc']),address=hex(store['address']),width=store['width'],value=value))
    require(machine.read(0x6223d414,8) == bytes(8) and
            machine.read(CAPTURE,SIZE) == capture and
            not any(r.address <= 0x6223dc92 < r.address+len(r.data) for r in machine.regions.values()),
            'Standby preparation changed capture or supplied the still-unproduced request member')
    rows = [stage(name,result) for name,result in (
        ('native_camera_service_initialize',camera),('native_controller_device_flag_reset',flag_reset),
        ('native_controller_device_flag_selection',flag_update),('native_parameter_flags_and_properties',initial),
        ('native_parameter_mode_selection_slice',selected),('native_parameter_record_refresh',refreshed),
        ('native_standby_argument_publication',arguments),('native_standby_entry_callback',entered))]
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],
        engine=str(engine),cases=rows,native_instructions=sum(r['completed'] for r in rows),
        maximum_observed_new_stack_depth=max(r['stack_depth_from_call_sp'] for r in rows),
        native_store_bytes_added=139+1+len(gaps)+24+44,conditional_BSS_bytes_added=1,
        incoming_flags_projection=dict(address='0x19c00008',bytes=4,source='0x6223ed28',value=0,
            inherited_input_fixture=True,complete_message_constructed=False),
        complete_native_camera_service_initializer=True,native_fifo_header_bytes=18,
        native_parameter_record=dict(source='0x6223eca0',published='0x6223ecb0',bytes=16,
            source_data=parameter.hex(),published_data=expected.hex(),all_fields_written_natively=True),
        native_standby=dict(table_row='0x6042d64c',state_id=11,name='Standby',entry='0x6029c6c3',
            argument_pair='0x6223ecc0',command_pointer=0,parameter_pointer='0x6223ecb0',
            callback_completed=True,dispatcher_executed=False,member_stores=values),
        capture_unchanged=True,postpopulation_resumed=False,
        still_unmapped_request_member=dict(address='0x6223dc92',object='0x6223d41c',offset=2166),
        hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['This is an independent parameter-preparation branch cloned from the postpopulation context; it does not resume the waiting consumer or assert whole controller state/event ordering.',
                'A4-byte projection reuses the already-declared zero controller request flags. It is not a76-byte incoming command, allocation, serialization or queue-delivery proof.',
                'Only camera status member622351bc assumes the original BSS clear before first status publication. The service initializer writes139 reviewed bytes, including an18-byte FIFO header; its backing payload and unrelated fields stay unmapped.',
                'Controller device-flag reset/selection and parameter mode/publication are original slices. Their enclosing callbacks, source-command release and dispatcher60289c18 are not executed.',
                'The complete Standby entry callback takes the actual published null-command branch. It does not construct an active capture request, supply offset2166, create a capture allocation generation or establish COLOR eligibility.',
                'Second population/finish, relay/worker lifecycle, actual hardware residency and backup/recovery remain unresolved.'])
    return report,dict(upstream=contexts,upstream_report=upstream,cases=[dict(context,standby_machine=machine,
        standby_result=entered)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(standby_parameters_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
