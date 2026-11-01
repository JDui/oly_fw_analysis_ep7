#!/usr/bin/env python3
"""Resume geometry with the original pre-publication 34-byte status record.

The earlier native snapshot wrote its halfword at offset12. Only the other32
bytes use the witnessed original BSS precondition; active construction and
publication are not inferred from this cold continuation.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path

from ep7_candidate_startup_sim import CALLER, require
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_format_record_sim import missing_bytes, coalesce_record
from ep7_candidate_geometry_critical_sim import geometry_critical_context


STATUS = 0x62293d1c


def geometry_status_context(directory, prefix, engine):
    upstream, contexts = geometry_critical_context(directory, prefix, engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    rows, outputs = [], []
    for index, context in enumerate(contexts['cases']):
        machine = context['machine']
        capture = machine.read(CAPTURE, SIZE)
        witnesses = [(0x60020068, 'fccd886879a2fccc00af1c62'),
                     (0x603f9f36, 'fcdd1c3d296285efdbf0612102f070200244d9'),
                     (0x603f9f4c, 'fc83283d2962'),
                     (0x60415945, 'fcdc643374a2'),
                     (0x604155d6, 'fad0e001dd4649feff0000'),
                     (0x6041628e, 'fccc443574a2cdf606f060'),
                     (0x604169ad, '5808a000c905dff060')]
        require(all(machine.read(pc,len(bytes.fromhex(code)))==bytes.fromhex(code)
                    for pc,code in witnesses) and
                0x621caf00 <= STATUS < STATUS+34 <= 0x62796888 and
                machine.read(STATUS+12,2)==bytes(2),
                'status copy/producer/BSS witness or native snapshot field changed')
        gaps = missing_bytes(machine,range(STATUS,STATUS+34),0,'status_prepublication_BSS')
        require(gaps == [STATUS+i for i in range(34) if i not in (12,13)],
                'prepublication status has unexpected unknown fields')
        source = coalesce_record(machine,STATUS,34,'geometry_prepublication_status')
        machine.regions['geometry_prepublication_status'] = replace(
            machine.regions['geometry_prepublication_status'], permissions='r')
        registers = context['configuration_result']['registers']
        destination = registers['a0']
        configured = machine.resume(registers,CALLER+7,full_trace=True,limit=80000,
            breakpoints=[base['syms']['_ep7_gcc_quarantine'],0x60061808,0x6040e126])
        fault = configured['fault'] or {}
        require(configured['status']=='memory_fault' and
                (fault.get('pc'),fault.get('address'),fault.get('size'),fault.get('access'))==
                (0x6041308b,0x621cf64c,2,'read') and
                configured['registers']['mdr']==0x601f2736 and
                sum(r['pc']==0x603f9f43 for r in configured['trace'])==17 and
                machine.read(destination,34)==source and
                not any(r['pc']==0x6042805e for r in configured['trace']),
                'status copy did not finish at the unavailable-device measurement dependency')
        require(machine.read(CAPTURE,SIZE)==capture,'status continuation changed partial capture')
        rows.append(dict(gpio80_input_bit4=index,
            cases=[stage('native_geometry_prepublication_status',configured)],
            conditional_prepublication_BSS_bytes=len(gaps),native_snapshot_field_bytes=2,
            status_source=hex(STATUS),status_destination=hex(destination),
            status_bytes=source.hex(),native_status_halfword_stores=sum(
                r['pc']==0x603f9f43 for r in configured['trace']),
            native_status_copy_equal=machine.read(destination,34)==source,
            geometry_dynamic_setter_entries=[hex(r['pc']) for r in configured['trace'] if r['pc']==0x6042805e],
            frontier=dict(status=configured['status'],fault=configured['fault'],
                pc=hex(configured['registers']['pc']),native_return_pc=hex(configured['registers']['mdr'])),
            geometry_configuration_completed=configured['status']=='returned',
            capture_unchanged=True,population_resumed=False))
        outputs.append(dict(context,configuration_result=configured,
                            configuration_stack=machine.regions['stack']))
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],
        engine=str(engine),cases=rows,
        native_instructions=sum(c['completed'] for row in rows for c in row['cases']),
        maximum_observed_new_stack_depth=max(c['stack_depth_from_call_sp'] for row in rows for c in row['cases']),
        hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['Only the prepublication state is represented. The34-byte active producer6041698a requires real input records; itsNULL branch does not initialize the output.',
                'The earlier snapshot halfword is preserved. Other32bytes are explicit original BSS conditions, not a fabricated active status or a completed native publisher.',
                'Population, active geometry, task ordering and worker execution remain incomplete.'])
    return report,dict(upstream=contexts,upstream_report=upstream,cases=outputs)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(geometry_status_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
