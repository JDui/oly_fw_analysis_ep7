#!/usr/bin/env python3
"""Build a bounded type11 command and run the complete native request constructor.

The packet allocation, queue transport and controller dispatch remain explicit
cuts. Only reviewed members exist; postpopulation stops at the next unknown.
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
from ep7_candidate_standby_parameters_sim import standby_parameters_context


PACKET, OBJECT = 0x19c10000, 0x6223d41c


def request_constructor_context(directory,prefix,engine):
    upstream,contexts = standby_parameters_context(directory,prefix,engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    context = contexts['cases'][0]
    original = context['postpopulation_machine']
    machine = context['standby_machine'].clone()
    capture = machine.read(CAPTURE,SIZE)
    machine.regions['stack'] = replace(machine.regions['stack'],data=b'\xcc'*len(machine.regions['stack'].data))
    # Only observed command members exist. The opaque nonzero cookie witnesses
    # copying; no callback is invoked and no76-byte template is invented.
    flags = original.read(0x6223ed28,4)
    admit(machine,'request_command_prefix',PACKET,b'\xa5'*4+struct.pack('<I',0x12345678)+flags)
    admit(machine,'request_command_native_tail',PACKET+44,b'\xa5'*26)
    registry = machine.regions.pop('capture_registry_id1')
    require(registry.address == 0x6223d190 and len(registry.data) == 24 and
            registry.data[:2] == struct.pack('<H',4) and registry.data[18:20] == bytes(2),
            'owned capture registry fixture changed')
    for name,offset,size,permissions in [('before_status',0,18,'r'),('native_status',18,2,'rw'),
                                         ('after_status',20,4,'r')]:
        region = replace(registry,name='capture_registry_'+name,address=registry.address+offset,
            data=registry.data[offset:offset+size],permissions=permissions,capture=permissions=='rw')
        machine.regions[region.name] = region
    # Original sender suffix assembles16B but stops before the send call. ID1
    # comes from the already-owned capture fixture, not an executed allocation.
    produced = machine.run(0x602987f3,0x6029881d,overrides=dict(sp=CALL_SP,a2=PACKET,d2=1),
        full_trace=True,limit=1000)
    result_ok(machine,produced,0x6029881d,CALL_SP)
    expected_event = struct.pack('<4I',204,1,11,PACKET)
    require(machine.read(CALL_SP+16,16) == expected_event and
            machine.read(PACKET,4) == struct.pack('<I',1) and
            produced['registers']['a0'] == CALL_SP+16 and produced['registers']['d1'] == 16,
            'native type11 sender event construction changed')
    received = native_call(machine,base['syms'],0x60289dac,0x30,12,dict(a0=CALL_SP+16),limit=2000)
    require(received['registers']['a0'] == PACKET and
            machine.read(PACKET+44,26) == expected_event+bytes(10) and
            machine.read(registry.address+18,2) == struct.pack('<H',1) and
            sum(t['pc'] == 0x60289db9 for t in received['trace']) == 4 and
            sum(t['pc'] == 0x6029c506 for t in received['trace']) == 1,
            'native command materialization or registry status mark changed')
    admit(machine,'native_request_flag_class',0x6223ed04,b'\xa5'*4)
    region = machine.regions['geometry_controller_flags']
    machine.regions[region.name] = replace(region,permissions='rw',capture=True)
    classified = machine.run(0x602ad8ea,0x602ad8ff,overrides=dict(sp=CALL_SP,a2=PACKET),
        full_trace=True,limit=1000)
    result_ok(machine,classified,0x602ad8ff,CALL_SP)
    require(machine.read(0x6223ed28,4) == flags == bytes(4) and
            machine.read(0x6223ed04,4) == bytes(4), 'native command flags/class changed')
    stores,ranges = map_initializer_storage(machine,directory,prefix,[(0x602a471d,0x602a4a5c)],
        [(0x6223e014,0x6223e015),(0x6223e33c,0x6223e348)],name_prefix='native_request_constructor')
    require(sum(high-low for low,high in ranges) == 13, 'request direct-store extent changed')
    members = [(1676,1),(1679,1),(1706,1),(1998,1),(2000,4),(2392,4),
               (2108,4),(2058,1),(2008,1),(1695,1),(2166,1),(1685,1)]
    gaps = missing_bytes(machine,[OBJECT+offset+i for offset,size in members for i in range(size)],
        0xa5,'native_request_indirect_members')
    require(len(gaps) == 21, 'request indirect-store extent changed')
    # Inactive path does not initialize the previous-count halfword it reads at
    #602a49ce. Explicit first-activation BSS condition; do not borrow an active
    # branch's reset out of context or zero-fill the surrounding record.
    require(machine.read(0x60020068,12) == bytes.fromhex('fccd886879a2fccc00af1c62') and
            0x621caf00 <= OBJECT+2096 < 0x62796888 and
            machine.read(0x602a49df,4) == bytes.fromhex('fa507608'),
            'request previous-count BSS range or native offset2166 writer changed')
    admit(machine,'request_first_activation_previous_count',OBJECT+2096,bytes(2),permissions='r')
    constructed = native_call(machine,base['syms'],0x602a471d,0xf0,32,
        dict(a0=OBJECT,a1=PACKET),limit=20000)
    values = []
    for offset,size in members:
        value = int.from_bytes(machine.read(OBJECT+offset,size),'little')
        require(value == (1 if offset == 1706 else 0), 'native request output member changed')
        values.append(dict(offset=offset,bytes=size,value=value))
    for store in stores:
        executed = [t for t in constructed['trace'] if t['pc'] == store['pc']]
        require(len(executed) == 1 and machine.read(store['address'],store['width']) ==
            (executed[0][store['register']] & ((1 << (8*store['width']))-1)).to_bytes(store['width'],'little'),
            'request direct member differs from its actual native store')
    require(machine.read(0x6223e344,4) == struct.pack('<I',0x12345678) and
            sum(t['pc'] == 0x602a49df for t in constructed['trace']) == 1 and
            not any(t['pc'] in (0x6006776e,0x60061808,0x6040e126) for t in constructed['trace']) and
            machine.read(CAPTURE,SIZE) == capture,
            'request construction changed capture, lost cookie or entered a diagnostic')
    # Restore the waiting consumer's original stack and synthetic caller. The
    # producer work above is an independent preparation/continuation probe,
    # not proof of uninterrupted controller/event execution.
    continued_machine = machine.clone()
    continued_machine.regions['stack'] = original.regions['stack']
    continued_machine.regions['caller'] = original.regions['caller']
    continued = continued_machine.resume(context['postpopulation_result']['registers'],0x602a44ba,
        full_trace=True,limit=60000,breakpoints=[base['syms']['_ep7_gcc_quarantine'],0x60061808,0x6040e126])
    require(continued['status'] == 'memory_fault' and continued['fault'] == dict(
        kind=1,pc=0x602a8ee2,map=0,address=0x6223d61c,size=2,access='read') and
        continued_machine.read(CAPTURE,SIZE) == capture and
        not any(t['pc'] == base['syms']['_ep7cn_population'] for t in continued['trace']),
        'postpopulation no longer stops at the next unproduced format record')
    rows = [stage(name,result) for name,result in (
        ('native_type11_sender_suffix',produced),('native_command_receive_materializer',received),
        ('native_incoming_flag_class_slice',classified),('complete_native_request_constructor',constructed),
        ('second_population_after_request_constructor',continued))]
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],engine=str(engine),
        cases=rows,native_instructions=sum(r['completed'] for r in rows),
        maximum_observed_new_stack_depth=max(r['stack_depth_from_call_sp'] for r in rows),
        native_store_bytes_added=30+4+13+len(gaps),explicit_input_bytes_added=8,conditional_BSS_bytes_added=2,
        existing_registry_bytes_opened_for_native_store=2,existing_flags_bytes_opened_for_native_store=4,
        command=dict(address=hex(PACKET),full_size=76,mapped_bytes=38,owned_capture_id=1,event_kind=11,
            reply_handle=204,opaque_cookie='0x12345678',flags=0,event_data=expected_event.hex(),
            sender_slice_executed=True,receive_materializer_completed=True,allocation_executed=False,
            full_template_copied=False,queue_transport_executed=False,dispatcher_executed=False),
        native_registry_status=dict(address=hex(registry.address+18),bytes=2,value=1,
            allocation_generation_proven=False),
        native_request=dict(entry='0x602a471d',object=hex(OBJECT),completed=True,members=values,
            previous_count_BSS_member_offset=2096,previous_count_bytes=2,capture_unchanged=True),
        frontier=dict(status=continued['status'],fault=continued['fault'],input_object=hex(OBJECT),
            member_offset=512,format_record_offset=496),
        second_population_completed=False,finish_observer_executed=False,
        hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['Only38 of76 command bytes exist. ID1 and zero flags inherit prior explicit fixtures; a nonzero opaque cookie is a copy witness. Allocation, complete template copy and queue transport are not executed.',
                'The original sender suffix assembles the16-byte event, and the complete receive materializer copies it and sets the native registry status halfword. This status is not an allocation-generation proof.',
                'Flag classification is an original handler slice. Its enclosing handler and controller dispatcher are not executed; the original global-current-ID path remains unproven.',
                'The complete request constructor consumes native Standby members and writes offset2166 itself. Its inactive path reads a2-byte previous count under an explicit first-activation BSS condition.',
                'The waiting consumer resumes with its saved stack and registers only after this independent preparation branch. It stops at object+512; no unknown format record is fabricated.',
                'Second population/finish, valid COLOR capture, relay/worker lifecycle, hardware residency and backup/recovery remain unresolved.'])
    return report,dict(upstream=contexts,upstream_report=upstream,cases=[dict(context,
        request_machine=machine,request_result=constructed,postpopulation_machine=continued_machine,
        postpopulation_result=continued)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(request_constructor_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
