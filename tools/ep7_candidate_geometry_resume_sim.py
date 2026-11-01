#!/usr/bin/env python3
"""Resume original geometry configuration after the cold snapshot callback.

Restore its real suspended stack/registers; do not substitute a configuration
object or active camera dimensions. Capture population remains separate.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import CALLER, require
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_snapshot_output_sim import snapshot_output_context
from penf_emulator import Region


def geometry_resume_context(directory, prefix, engine):
    upstream, contexts = snapshot_output_context(directory, prefix, engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    rows, outputs = [], []
    for index, context in enumerate(contexts['cases']):
        machine = context['machine']
        capture = machine.read(CAPTURE, SIZE)
        require(context['producer_result']['status'] == 'returned' and
                context['producer_result']['registers']['pc'] == 0x60409ecb,
                'geometry must not consume an unfinished snapshot producer')
        machine.regions['stack'] = context['configuration_stack']
        machine.regions['caller'] = Region('caller', CALLER,
            b'\xdd'+struct.pack('<i', 0x6042760c-CALLER)+bytes([0xf0, 16]), 'rx')
        configured = machine.resume(context['configuration_result']['registers'], CALLER+7,
            full_trace=True, limit=80000,
            breakpoints=[base['syms']['_ep7_gcc_quarantine'], 0x60061808, 0x6040e126])
        fault = configured['fault'] or {}
        snapshot_returns = [r['a0'] for r in configured['trace'] if r['pc'] == 0x60419f58]
        require(configured['status'] == 'memory_fault' and
                (fault.get('pc'), fault.get('address'), fault.get('size'), fault.get('access')) ==
                (0x60427ec6, 0x622a06b4, 2, 'read') and
                configured['registers']['mdr'] == 0x6005c8df and
                snapshot_returns and all(pointer == 0x6229fc48 for pointer in snapshot_returns) and
                not any(r['pc'] == 0x6042805e for r in configured['trace']),
                'geometry did not consume the original snapshot and stop at the unknown transform field')
        require(machine.read(CAPTURE, SIZE) == capture, 'geometry resume changed partial capture')
        rows.append(dict(gpio80_input_bit4=index,
            cases=[stage('native_geometry_resume_after_complete_cold_snapshot', configured)],
            actual_suspended_stack_restored=True, snapshot_callback_completed_before_resume=True,
            native_snapshot_pointer_returns=[hex(pointer) for pointer in snapshot_returns],
            geometry_dynamic_setter_entries=[hex(r['pc']) for r in configured['trace'] if r['pc']==0x6042805e],
            frontier=dict(status=configured['status'], fault=configured['fault'],
                pc=hex(configured['registers']['pc']), native_return_pc=hex(configured['registers']['mdr'])),
            geometry_configuration_completed=configured['status']=='returned',
            capture_unchanged=True, population_resumed=False))
        outputs.append(dict(context, configuration_result=configured,
                            configuration_stack=machine.regions['stack']))
    report = dict(scope=__doc__, candidate_build_revision=upstream['candidate_build_revision'],
        engine=str(engine), cases=rows,
        native_instructions=sum(c['completed'] for row in rows for c in row['cases']),
        maximum_observed_new_stack_depth=max(c['stack_depth_from_call_sp'] for row in rows for c in row['cases']),
        hash_checks_performed=False, native_api_success_stubs=False,
        firmware_files_modified=False, hardware_executed=False, installable=False,
        limits=['The completed producer uses the explicitly unconfigured/no-device cold scenario. It does not supply valid active shot geometry.',
                'Only the previously suspended configuration resumes. Population, capture allocation, task ordering and worker execution are not completed by this probe.'])
    return report, dict(upstream=contexts, upstream_report=upstream, cases=outputs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--tool-prefix', required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(geometry_resume_context(args.candidate, args.tool_prefix, args.engine)[0], indent=2))
