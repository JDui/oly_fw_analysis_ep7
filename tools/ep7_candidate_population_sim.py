#!/usr/bin/env python3
"""Execute the original capture population from its patched prewrite boundary.

The owned capture prefix and controller handover are explicit fixtures. Template
and property values come from the preceding original initialization; unprovided
property or hardware state must stop native execution rather than become zero.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import CALLER,require
from ep7_candidate_state_sim import CALL_SP
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_capture_template_sim import TEMPLATE,SIZE
from ep7_candidate_message_sim import summarize_message,result_ok
from ep7_candidate_property_sim import property_context,initialize_configuration_defaults,BASE_INDEX
from ep7_candidate_relay_sim import task_fixture
from penf_emulator import Region


def population_context(directory,prefix,engine,without_capture_defaults=False):
    upstream,context=property_context(directory,prefix,engine)
    machine,syms=context['machine'],context['syms']
    require(upstream['template']['usable_default_fixture'],
            'capture population requires an initialized conditional-BSS template')
    setup,extra_records=[],[]
    records=context['property_records']
    if not without_capture_defaults:
        setup,extra_records=initialize_configuration_defaults(machine,syms,capture_defaults=True)
        records=context['property_records']+extra_records
        indices={r['key']>>4 for r in records}
        require(len(indices)==len(records)==2293 and
                all(machine.read(BASE_INDEX+8*i+4,4)==bytes(4) for i in range(4096) if i not in indices),
                'capture property bank overlaps an existing property or fills another index')
    task_fixture(machine,0x73,0x60039664,0x60289852,25,4096)
    # Only the witnessed27332-byte template prefix is admitted, not the whole
    # 41984-byte pool slot. A5 must be overwritten by the original copy loop.
    machine.regions['capture']=replace(machine.regions['capture'],
        data=b'\xa5'*SIZE,permissions='rw',capture=True)
    machine.regions['capture_after']=replace(machine.regions['capture_after'],address=CAPTURE+SIZE)
    require(machine.read(0x60300055,10)==bytes.fromhex('fcdd2c8825622d4fe5db'),
            'native capture template pointer or copy count changed')
    machine.regions['caller']=Region('caller',CALLER,
        b'\xdd'+struct.pack('<i',0x602a7ea0-CALLER)+bytes([0xf0,20]),'rx')
    copied=machine.run(CALLER,0x602a7eb0,overrides=dict(sp=CALL_SP,d0=1),
        full_trace=True,limit=70000,breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808])
    result_ok(machine,copied,0x602a7eb0,CALL_SP-20)
    require(machine.read(CAPTURE,SIZE)==machine.read(TEMPLATE,SIZE) and
            sum(r['pc']==0x60300055 for r in copied['trace'])==1 and
            sum(r['pc']==syms['_ep7cn_prewrite'] for r in copied['trace'])==1 and
            sum(r['pc']==0x60300061 for r in copied['trace'])==6833,
            'native template copy differs from its initialized source or word count')
    copy_row=summarize_message('native_prewrite_and_template_copy',copied,CALL_SP)
    copy_row['candidate_prewrite_entries']=1
    populated=machine.resume(copied['registers'],CALLER+7,full_trace=True,limit=80000,
        breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808])
    row=summarize_message('native_capture_population_after_template_copy',populated,CALL_SP)
    if populated['status']!='returned':
        row['d0_at_stop']=row.pop('returned_d0')
    lookups=[dict(key=hex(r['d0']&0xffff),return_pc=hex(r['mdr']))
             for r in populated['trace'] if r['pc']==0x6005d924]
    row['native_property_lookups']=lookups
    if without_capture_defaults:
        require(populated['status']=='breakpoint' and populated['registers']['pc']==0x60061808 and
                [r['key'] for r in lookups]==['0x810a'],
                'missing capture-default property frontier changed: '+str(row))
        frontier=dict(kind='missing_capture_default_property',property_key='0x810a')
    else:
        require(populated['status']=='memory_fault' and populated['fault']==dict(
            kind=1,pc=0x604288d5,map=0,address=0x622a064a,size=2,access='read') and
            len(lookups)==40 and lookups[-1]['key']=='0xc36a',
            'native geometry-state frontier changed: '+str(row))
        require(machine.read(0x604288d5,6)==bytes.fromhex('fcac4a062a62') and
                machine.read(0x6042134c,12)==bytes.fromhex('fc8348062a62fc834a062a62') and
                machine.read(0x6042847b,6)==bytes.fromhex('fc834a062a62'),
                'original geometry getter/reset/setter witnesses changed')
        registers=populated['registers']
        frontier=dict(kind='unmapped_dynamic_geometry_state',getter='0x604288d5',
            getter_native_return_pc=hex(registers['mdr']),global_halfwords=['0x622a064a','0x622a0648'],
            capture_destination_offsets=[registers[r]-CAPTURE for r in ('a0','a1')],
            original_reset_slice=['0x6042133f','0x60421364'],
            original_dynamic_setter_slice=['0x6042844e','0x60428481'],
            state_default_or_shot_values_supplied=False)
    report=dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],
        engine=str(engine),template_copy_passed=True,
        population_passed=populated['status']=='returned',
        frontier=frontier,
        cases=setup+[copy_row,row],capture=dict(address=hex(CAPTURE),mapped_prefix_bytes=SIZE,
            allocation_executed=False,initial_fill='a5',template_words_copied=6833),
        upstream_registered_properties=upstream['registered_records'],
        additional_capture_defaults=len(extra_records),
        capture_default_bank=None if without_capture_defaults else dict(
            ROM='0x60096f98',terminator='0x600be008',RAM='0x624ea400',packed_extent=153008,
            native_endpoint_cell='0xa2715ab8',imported_camera_NVM=False),
        template_BSS_DMA_executed=False,hash_checks_performed=False,
        native_api_success_stubs=False,firmware_files_modified=False,
        hardware_executed=False,installable=False,
        limits=['Original population executes in a cloned post-materializer context after an explicit controller TCB handover; it is not a complete boot or first-capture schedule.',
                'The capture/node/registry remain owned fixtures. Only the original template prefix is writable; no pool allocation or unknown extension initialization is claimed.',
                'Native prewrite executes before the original template copy. Existing capture state may be revoked, and no completion/seal observer is forged at a frontier.',
                'Conditional BSS initialization and original ROM/default properties are inherited; camera NVM, calibration and actual shot geometry remain unverified.',
                'Full second population, relay preprocessing, worker allocation/processing/cleanup and ACK remain separate stages.'])
    context.update(population_result=populated,property_records=records)
    return report,context


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    parser.add_argument('--without-capture-defaults',action='store_true',help='reproduce the missing810a frontier')
    args=parser.parse_args()
    print(json.dumps(population_context(args.candidate,args.tool_prefix,args.engine,args.without_capture_defaults)[0],indent=2))
