#!/usr/bin/env python3
"""Refresh the native snapshot after ID24 propagation, then construct geometry.

Only reviewed native writes receive new storage. The scenario still has no
available device and an unconfigured format; a completed call is not a shot.
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
from ep7_candidate_snapshot_sim import call_prefix, stage
from ep7_candidate_device_state_sim import admit
from ep7_candidate_format_record_sim import missing_bytes
from ep7_candidate_geometry_sim import map_initializer_storage
from ep7_candidate_mode_property_sim import mode_property_context
from ep7_ui_resource_origin import ROM_START, RAM_CACHED


def reconfigured_geometry_context(directory, prefix, engine):
    upstream, contexts = mode_property_context(directory, prefix, engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    context = contexts['cases'][0]
    machine = context['machine'].clone()
    capture = machine.read(CAPTURE, SIZE)
    old_snapshot = machine.read(0x6229fc48, 124)
    machine.regions['stack'] = replace(machine.regions['stack'], data=b'\xcc'*len(machine.regions['stack'].data))
    require(machine.read(0x6040a274,7) == bytes.fromhex('ddbc1afffff018') and
            machine.read(0x60169953,7) == bytes.fromhex('00fc82901d2262') and
            machine.read(0x60427761,27) == bytes.fromhex(
                '3dfad16802fcdc14072a6285eddb7151605044d9fafef802dff010'),
            'native curve initializer, device reset or configuration publication changed')
    by_key = {r['key']:r for r in base['property_records']}
    for address, size in ((0x622959dc,176),(0x62295ab2,104)):
        admit(machine, f'native_geometry_curve_{address:x}', address, b'\xa5'*size)
    curve = native_call(machine,base['syms'],0x603fbd30,0xf0,24,limit=10000)
    x = [1116,1194]+[((14+i-1)//3)*256+((14+i-1)%3)*85 for i in range(2,25)]
    prop = by_key[0x193a]
    require((prop['count'],prop['width']) == (25,2), 'curve source property extent changed')
    y = list(struct.unpack('<25H',machine.read(prop['data'],50)))
    y[-1] = y[-2]  # The native final element repeats source23, not source24.
    offset = struct.unpack('<H',machine.read(by_key[0x1a4a]['data'],2))[0]
    require(machine.read(0x622959dc,176) == bytes(176) and
            machine.read(0x62295ab2,104) == struct.pack('<52H',14,offset,*x,*y),
            'native curve initialization differs from property sources or generated abscissae')
    rows = [stage('native_geometry_curve_initialize',curve)]
    stores, ranges = map_initializer_storage(machine,directory,prefix,
        [(0x6040b635,0x6040b7be),(0x6040b478,0x6040b488),
         (0x603fae7c,0x603fae85),(0x6040e422,0x6040e443)],
        [(0x6229a0f8,0x6229a3a4),(0x622959d8,0x622959d9),(0xa2740fbc,0xa2740fd0)],
        [(0x6229a110,0x6229a130),(0x6229a3a0,0x6229a3a4),(0x6229a168,0x6229a36c)],
        name_prefix='native_geometry_submodule')
    require(sum(high-low for low,high in ranges) == 653, 'submodule initializer write extent changed')
    reset = native_call(machine,base['syms'],0x6040b635,0x80,8,limit=5000)
    require(machine.read(0x6229a110,32) == struct.pack('<8I',*([65535]*8)) and
            machine.read(0x6229a138,2) == bytes(2) and machine.read(0x6229a14d,1) == b'\xa0' and
            machine.read(0x6229a168,516) == bytes(516) and
            machine.read(0x6229a370,7) == struct.pack('<3H',32494,32494,32494)+b'\xff' and
            machine.read(0x622959d8,1) == b'\1' and machine.read(0xa2740fbe,2) == struct.pack('<H',20),
            'complete native submodule reset changed')
    rows.append(stage('native_geometry_submodule_initialize',reset))
    constant_address = 0x61fa0638
    constant_source = ROM_START+constant_address-RAM_CACHED
    constants = machine.read(constant_source,4)
    require(constant_source == 0x602388f8 and constants == struct.pack('<2H',295,85),
            'native initialized-data curve conversion constants changed')
    admit(machine,'geometry_curve_conversion_constants',constant_address,constants,permissions='r')
    admit(machine,'native_geometry_device_reset_member',0x62221d90,b'\xa5')
    device_reset = machine.run(0x60169953,0x6016995a,overrides=dict(sp=CALL_SP),full_trace=True,limit=20)
    result_ok(machine,device_reset,0x6016995a,CALL_SP)
    require(machine.read(0x62221d90,1) == b'\0', 'native device reset member was not cleared')
    rows.append(stage('native_geometry_device_reset_member',device_reset))
    device_gaps = missing_bytes(machine,range(0x62221a28,0x62221a38),0xa5,'native_geometry_device_outputs')
    require(len(device_gaps) == 14, 'native device output extent changed')
    # Catalog direct stores using the established disassembler helper, then
    # admit only missing bytes. Existing native service state is preserved.
    catalog = machine.clone()
    catalog.regions = {}
    output_stores, output_ranges = map_initializer_storage(catalog,directory,prefix,
        [(0x6042857f,0x60428656)],[(0x622a0654,0x622a067c)])
    output_gaps = missing_bytes(machine,
        [a for low,high in output_ranges for a in range(low,high)],0xa5,'native_geometry_output_members')
    require(len(output_gaps) == 38, 'native geometry output member extent changed')
    admit(machine,'native_geometry_published_configuration',0x622a0714,b'\xa5'*76)
    status = machine.regions.pop('geometry_prepublication_status')
    require(status.address == 0x62293d1c and len(status.data) == 34 and status.permissions == 'r',
            'upstream geometry status mapping changed')
    # 603f9f4c updates exactly this known halfword during the snapshot wrapper.
    for name, start, end, permissions in (
            ('geometry_status_before_member',0,12,'r'),
            ('geometry_status_native_member',12,14,'rw'),
            ('geometry_status_after_member',14,34,'r')):
        machine.regions[name] = replace(status,name=name,address=status.address+start,
            data=status.data[start:end],permissions=permissions,capture=permissions=='rw')
    refreshed_task = call_prefix(machine,0x60409e3c,0xf0,68,0x60409e74,limit=2000)
    result_ok(machine,refreshed_task,0x60409e74,CALL_SP-68)
    require(refreshed_task['registers']['a3'] == 0x6229faf8, 'task prefix request pointer changed')
    refreshed = machine.resume(dict(refreshed_task['registers'],pc=0x60409eb6),0x60409ecb,
        full_trace=True,limit=80000,breakpoints=[base['syms']['_ep7_gcc_quarantine'],0x60061808,0x6040e126])
    result_ok(machine,refreshed,0x60409ecb,CALL_SP-68)
    snapshot = machine.read(0x6229fc48,124)
    snapshot_changes = [dict(offset=i,before=a,after=b)
                        for i,(a,b) in enumerate(zip(old_snapshot,snapshot)) if a!=b]
    require(snapshot == machine.read(0x622a084c,124) and
            machine.read(0x6229fb88,4) == struct.pack('<I',0x6229fc48) and
            machine.read(0x6229fc44,2) == bytes([0,2]) and
            snapshot_changes == [dict(offset=9,before=0,after=3)] and
            sum(t['pc'] == 0x60426f83 for t in refreshed['trace']) == 1 and
            sum(t['pc'] == 0x6041a20a for t in refreshed['trace']) == 1,
            'fresh native snapshot did not consume the completed mode update')
    rows += [stage('native_snapshot_task_prefix_again',refreshed_task),
             stage('native_snapshot_callback_after_public_setting',refreshed)]
    machine.regions['stack'] = replace(machine.regions['stack'],data=b'\xcc'*len(machine.regions['stack'].data))
    configured = call_prefix(machine,0x6042760c,0xf0,16,CALLER+7,overrides=dict(d0=0),limit=80000)
    result_ok(machine,configured,CALLER+7,CALL_SP)
    trace = configured['trace']
    require(len(trace) == configured['completed'], 'fresh geometry trace was truncated')
    lookup = [t for t in trace if t['pc'] == 0x603fca0a]
    matched = [t for t in trace if t['pc'] == 0x603fca5f]
    setter = [t for t in trace if t['pc'] == 0x6042805e]
    publication = [t for t in trace if t['pc'] == 0x60427771]
    setup = [t for t in trace if t['pc'] == 0x60427761]
    require(len(lookup) == len(matched) == len(setter) == len(setup) == 1 and
            lookup[0]['d0'] == 3 and matched[0]['d1'] == 4 and matched[0]['a1'] == 0x60541326+70*4+68 and
            len(publication) == 19 and not any(t['pc'] == 0x6040e126 for t in trace),
            'fresh geometry did not match key3, execute its setter and publish19 words')
    configuration = machine.read(0x622a0714,76)
    source_address = setup[0]['sp']+616
    require(configuration == machine.read(source_address,76) and configuration[74] == 3 and
            [t['a0'] for t in publication] == [0x622a0714+4*i for i in range(19)] and
            b''.join(struct.pack('<I',t['d0']) for t in publication) == configuration,
            'native configuration publication differs from its constructed source')
    output_values, skipped_stores = [], []
    for store in output_stores:
        executed = [t for t in trace if t['pc'] == store['pc']]
        if not executed:
            skipped_stores.append(store['pc'])
            continue
        require(len(executed) == 1, 'native output field store was not executed exactly once')
        value = executed[0][store['register']] & ((1 << (8*store['width']))-1)
        require(machine.read(store['address'],store['width']) == value.to_bytes(store['width'],'little'),
                'native output member differs from the executed store')
        output_values.append(dict(pc=hex(store['pc']),address=hex(store['address']),
                                  width=store['width'],value=value))
    require(skipped_stores == [0x604285f5] and len(output_values) == 21,
            'native output member alternative branch changed')
    require(machine.read(CAPTURE,SIZE) == capture, 'fresh geometry modified the partial capture')
    rows.append(stage('native_fresh_geometry_configuration',configured))
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],
        engine=str(engine),gpio80_input_bit4=0,cases=rows,
        native_instructions=sum(r['completed'] for r in rows),
        maximum_observed_new_stack_depth=max(r['stack_depth_from_call_sp'] for r in rows),
        native_store_bytes_added=280+653+1+len(device_gaps)+len(output_gaps)+76,
        conditional_BSS_bytes_added=0,
        conditional_initialized_data=dict(address=hex(constant_address),source=hex(constant_source),
            bytes=4,halfwords=[295,85],physical_startup_copy_executed=False),
        curve=dict(address='0x62295ab2',bytes=104,header=[14,offset],x=x,y=y,
            property_sources=['0x1a4a','0x193a'],native_initialization_completed=True),
        submodule_native_store_ranges=[[hex(low),hex(high)] for low,high in ranges],
        snapshot=dict(address='0x6229fc48',bytes=124,changes=snapshot_changes,
            native_cache_equal=True,callback_and_wrapper_returned=True),
        native_table_lookup=dict(entry='0x603fca0a',requested_key=3,table='0x60541326',
            row_bytes=70,key_offset=68,matched_index=4),
        geometry_dynamic_setter_entries=len(setter),geometry_configuration_completed=True,
        geometry_output_stores=output_values,skipped_alternative_store_pcs=[hex(pc) for pc in skipped_stores],
        configuration_publication=dict(destination='0x622a0714',source=hex(source_address),bytes=76,
            native_word_stores=19,source_equal=True,data=configuration.hex()),
        capture_unchanged=True,population_resumed=False,old_failed_geometry_frame_resumed=False,
        hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['The previous complete public ID24 setting is followed by a new snapshot and fresh6042760c stack. No suspended zero-mode geometry frame is resumed.',
                'The task prefix and snapshot dispatch reuse explicit receive/log scheduling cut points. The enclosing task loop, queue delivery and live mode-event ordering are not executed.',
                'Full curve and submodule initializers execute on poisoned reviewed write storage. Four constant bytes retain the known initialized-data ROM recipe; no physical startup copy or active calibration is claimed.',
                'The inherited format is unconfigured and the native availability state says no device. The complete configuration and dynamic setter return prove this conditional call path, not valid active shot dimensions.',
                'D0 at the final return is the last copied configuration word; it is not interpreted as a success or error code.',
                'The previous capture remains untouched. Fresh capture population, worker ownership/lifecycle, backup/recovery and installability remain pending.'])
    return report,dict(upstream=contexts,upstream_report=upstream,cases=[dict(context,machine=machine,
        configuration_result=configured,configuration_stack=machine.regions['stack'])])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(reconfigured_geometry_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
