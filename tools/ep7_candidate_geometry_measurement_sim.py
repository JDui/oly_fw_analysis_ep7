#!/usr/bin/env python3
"""Execute the original unavailable-device measurement refresh and continue.

The refresh reads already-native ROM default copies, not invented measurements.
Its enclosing periodic callback and hardware event ordering remain cut points.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import CALLER, require
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_message_sim import native_call
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_geometry_sim import map_initializer_storage
from ep7_candidate_geometry_status_sim import geometry_status_context


def geometry_measurement_context(directory,prefix,engine):
    upstream,contexts=geometry_status_context(directory,prefix,engine)
    base=contexts
    while 'syms' not in base:
        base=base['upstream']
    rows,outputs=[],[]
    for index,context in enumerate(contexts['cases']):
        machine=context['machine']
        capture=machine.read(CAPTURE,SIZE)
        witnesses=[(0x600f8014,'dd4a5e0f002008'),
                   (0x601ede97,'cd07490000'),
                   (0x601edea4,'cdfa480000'),
                   (0x601edeb7,'f8610cfc834cf61c62'),
                   (0x601edec0,'f060fc834ef61c62f86002fc8350f61c62'),
                   (0x6041308b,'f062f073f062ca0a')]
        require(all(machine.read(pc,len(bytes.fromhex(code)))==bytes.fromhex(code)
                    for pc,code in witnesses),
                'native periodic refresh, ROM fallback or measurement consumer changed')
        _,ranges=map_initializer_storage(machine,directory,prefix,[(0x601ede5e,0x601eded4)],
            [(0x621cf640,0x621cf648),(0x621cf64c,0x621cf652)],name_prefix='native_device_measurement')
        require(sum(high-low for low,high in ranges)==14,'measurement store extent changed')
        configuration_stack,configuration_caller=machine.regions['stack'],machine.regions['caller']
        machine.regions['stack']=replace(configuration_stack,data=b'\xcc'*len(configuration_stack.data))
        refreshed=native_call(machine,base['syms'],0x601ede5e,0x20,8,limit=1000)
        expected=machine.read(0xa271c5ec,2)+machine.read(0xa271ca62,4)
        require(machine.read(0x621cf640,8)==struct.pack('<2I',0xa271c5e0,0xa271ca60) and
                machine.read(0x621cf64c,6)==expected and
                sum(r['pc']==0x601ede96 for r in refreshed['trace'])==1 and
                not any(r['pc']==0x601ede68 for r in refreshed['trace']),
                'unavailable-device refresh did not copy its three native default halfwords')
        machine.regions['stack'],machine.regions['caller']=configuration_stack,configuration_caller
        configured=machine.resume(context['configuration_result']['registers'],CALLER+7,
            full_trace=True,limit=80000,
            breakpoints=[base['syms']['_ep7_gcc_quarantine'],0x60061808,0x6040e126])
        lookup=[r for r in configured['trace'] if r['pc']==0x603fca0a]
        consumer_stores=[r for r in configured['trace'] if r['pc']==0x6041308d]
        table_keys=[struct.unpack('<H',machine.read(0x60541326+70*i+68,2))[0] for i in range(66)]
        diagnostic_args=list(struct.unpack('<3I',machine.read(configured['registers']['sp']+100,12)))
        require(configured['status']=='breakpoint' and configured['fault'] is None and
                configured['registers']['pc']==0x6040e126 and
                configured['registers']['mdr']==0x603fca5b and
                configured['registers']['d0']==0x0e004504 and
                configured['registers']['d1']==1350 and
                len(lookup)==1 and lookup[0]['d0']==0 and
                table_keys[-1]==0 and all(table_keys[:-1]) and diagnostic_args==[2,0,65] and
                [r['d0'] for r in consumer_stores]==[512] and
                not any(r['pc'] in (0x603fca5f,0x603fc6d7,0x6042805e) for r in configured['trace']),
                'native default measurement or zero-mode table rejection changed')
        mode=next(r for r in base['property_records'] if r['key']==0xc011)
        mode_returns=[r['d0'] for r in base['geometry_configuration']['trace'] if r['pc']==0x60427795]
        require(mode['count']==1 and mode['width']==1 and
                machine.read(0x622a0aec,4)==struct.pack('<I',mode['data']) and
                machine.read(mode['data'],1)==machine.read(mode['header']+4,1)==bytes(1) and
                mode_returns==[0],
                'zero geometry type is no longer the unchanged native c011 default')
        require(machine.read(CAPTURE,SIZE)==capture,'measurement continuation changed partial capture')
        rows.append(dict(gpio80_input_bit4=index,
            cases=[stage('native_unavailable_device_measurement_refresh',refreshed),
                   stage('native_geometry_after_measurement_refresh',configured)],
            native_store_bytes=14,conditional_BSS_bytes_added=0,
            measurement_halfwords=list(struct.unpack('<3h',expected)),
            measurement_sources=['0xa271c5ec','0xa271ca62','0xa271ca64'],
            measurement_destination='0x621cf64c',native_values_equal=True,
            configuration_type=dict(property_key='0xc011',ROM_value_address=hex(mode['header']+4),
                registered_value_address=hex(mode['data']),value=0,native_getter_returns=mode_returns),
            native_table_lookup=dict(entry='0x603fca0a',requested_key=0,table='0x60541326',
                row_bytes=70,key_offset=68,nonzero_keys=table_keys[:-1],terminator_index=65,
                match_found=False,success_path_entered=False),
            native_diagnostic=dict(entry='0x6040e126',code='0x0e004504',source_line=1350,
                argument_count=diagnostic_args[0],arguments=diagnostic_args[1:],
                stopped_before_logger_body=True,caller_would_return_error1_after_logger=True),
            geometry_dynamic_setter_entries=[hex(r['pc']) for r in configured['trace'] if r['pc']==0x6042805e],
            frontier=dict(status=configured['status'],fault=configured['fault'],
                pc=hex(configured['registers']['pc']),native_return_pc=hex(configured['registers']['mdr'])),
            geometry_configuration_completed=configured['status']=='returned',
            capture_unchanged=True,population_resumed=False))
        outputs.append(dict(context,configuration_result=configured,configuration_stack=machine.regions['stack']))
    report=dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],
        engine=str(engine),cases=rows,native_instructions=sum(c['completed'] for row in rows for c in row['cases']),
        maximum_observed_new_stack_depth=max(c['stack_depth_from_call_sp'] for row in rows for c in row['cases']),
        hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['The complete601ede5e refresh runs after the established native ROM default copy. Its original caller600f8014 and enclosing periodic/event task are not executed.',
                'The startup initializer601ed42e precedes the ROM default copy at601ecdb7. It is not reordered and called against later defaults to manufacture a startup claim.',
                'Native c011 default0 is absent from the65-row geometry table. Execution stops at its real diagnostic entry; no logger skip, success return, replacement key or dynamic setter is supplied.',
                'Device availability remains the original cold reset. No attached-device measurement, active shot, population or worker lifecycle is claimed.'])
    return report,dict(upstream=contexts,upstream_report=upstream,cases=outputs)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(geometry_measurement_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
