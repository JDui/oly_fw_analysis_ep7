#!/usr/bin/env python3
"""Continue geometry through the real post-startup kernel critical section.

Reuse the existing single-task kernel model. The startup marker and no-interrupt
inputs are explicit fixtures; native dispatch and PSW operations still execute.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import CALLER, require
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_state_sim import CALL_SP
from ep7_candidate_message_sim import result_ok
from ep7_candidate_publish_sim import released
from ep7_candidate_device_state_sim import admit
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_geometry_array_sim import geometry_array_context


def geometry_critical_context(directory, prefix, engine):
    upstream, contexts = geometry_array_context(directory, prefix, engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    rows, outputs = [], []
    for index, context in enumerate(contexts['cases']):
        machine = context['machine']
        capture = machine.read(CAPTURE, SIZE)
        # Execute the original controller's zero-input publication slice. The
        # outer controller branch/queue is still an explicit lifecycle cut.
        witnesses = [(0x602ad983, '00f89310f892123c2010dd7e461700a010'),
                     (0x60422016, 'dd48f1bde6a008'),
                     (0x6042203f, 'dd0319fdff0004'),
                     (0x6041c689, 'fcdca6042a62'),
                     (0x6041c68f, 'ddc349bee6f01c'),
                     (0x6005a1c6, 'fccc77777777fc81fc06f08f'),
                     (0x6041c70d, 'fc82a2042a62'),
                     (0x6041c714, 'fc82a3042a62'),
                     (0x6041c71d, 'fc83a0042a62'),
                     (0x6041c85f, 'fc82a4042a62')]
        require(all(machine.read(pc, len(bytes.fromhex(code))) == bytes.fromhex(code)
                    for pc, code in witnesses) and machine.read(0x622a063e, 1) == bytes(1),
                'original controller publication/native critical result stores changed')
        admit(machine, 'geometry_native_critical_parameter', 0x622a04a6, b'\xa5'*4)
        admit(machine, 'geometry_native_critical_result', 0x622a04a0, b'\xa5'*4)
        require(0x621caf00 <= 0x622a04a4 < 0x62796888,
                'previous critical result escaped original startup BSS')
        admit(machine, 'geometry_critical_previous_result_conditional_BSS', 0x622a04a4, bytes(1))
        saved_stack = machine.regions['stack']
        machine.regions['stack'] = replace(saved_stack, data=b'\xcc'*len(saved_stack.data))
        published = machine.run(0x602ad983, 0x602ad994, overrides=dict(sp=CALL_SP),
            full_trace=True, limit=2000, breakpoints=[base['syms']['_ep7_gcc_quarantine'], 0x60061808, 0x6040e126])
        result_ok(machine, published, 0x602ad994, CALL_SP)
        require(machine.read(0x622a04a6, 4) == bytes(4) and
                sum(r['pc']==0x6041c686 for r in published['trace']) == 1,
                'original controller did not publish its native four-byte parameter')
        machine.regions['stack'] = saved_stack
        require(machine.read(0x600411a4+28, 4) == struct.pack('<I', 0x621a631c) and
                machine.read(0x600411a4+16, 4) == struct.pack('<I', 0x621a6320) and
                machine.read(0x8050, 4) == bytes(4) and
                machine.read(0x621a631c, 3) == bytes(3) and
                machine.read(0x621a6320, 1) == bytes(1),
                'existing native CPU0/single-task kernel model changed')
        admit(machine, 'geometry_kernel_started_input', 0x8ff006fc, struct.pack('<I', 0x77777777), 'r')
        admit(machine, 'geometry_restore_mask_input', 0x8ff00040, bytes(4), 'r')
        configured = machine.resume(context['configuration_result']['registers'], CALLER+7,
            full_trace=True, limit=80000,
            breakpoints=[base['syms']['_ep7_gcc_quarantine'], 0x60061808, 0x6040e126])
        fault = configured['fault'] or {}
        acquired = [r for r in configured['trace'] if r['pc'] == 0x6041c6d2]
        restored = [r for r in configured['trace'] if r['pc'] == 0x6041c6eb]
        require(configured['status'] == 'memory_fault' and
                (fault.get('pc'), fault.get('address'), fault.get('size'), fault.get('access')) ==
                (0x603f9f3f, 0x62293d1c, 2, 'read') and
                configured['registers']['mdr'] == 0x603fbece and
                sum(r['pc']==0x604276b3 for r in configured['trace']) == 1 and
                not any(r['pc'] in (0x6042805e, 0x603fe72d, 0x6003853e)
                        for r in configured['trace']),
                'native cold critical helper did not return into the next geometry dependency')
        require(len(acquired) == len(restored) == 1 and acquired[0]['d0'] & 0x80000000 and
                (restored[0]['psw'] & 0xf00) ==
                (context['configuration_result']['registers']['psw'] & 0xf00) and
                machine.read(0x621a631c, 3) == bytes(3) and
                machine.read(0x621a6320, 1) == bytes(1) and
                machine.read(0x622a04a0, 4) == bytes(4) and
                machine.read(0x622a04a4, 1) == bytes(1),
                'native dispatch/PSW restore or disabled-record output changed')
        released(machine)
        require(machine.read(CAPTURE, SIZE) == capture, 'critical-section probe changed partial capture')
        rows.append(dict(gpio80_input_bit4=index,
            cases=[stage('native_controller_zero_parameter_publication_slice', published),
                   stage('native_geometry_post_startup_critical_section', configured)],
            native_published_parameter=machine.read(0x622a04a6, 4).hex(),
            native_critical_result=machine.read(0x622a04a0, 4).hex(),
            kernel_lock_token=hex(acquired[0]['d0']),
            irq_mask_before=hex(context['configuration_result']['registers']['psw'] & 0xf00),
            irq_mask_restored=hex(restored[0]['psw'] & 0xf00),
            native_critical_helper_return='0x604276b3',
            active_parameter_calculation_entered=False,
            previous_result_conditional_BSS_bytes=1,
            kernel_marker_input='0x77777777', restore_mask_input=0,
            task_mode_flags=machine.read(0x621a631c, 3).hex(),
            dispatch_flags=machine.read(0x621a6320, 1).hex(),
            native_dispatch_disable_entries=sum(r['pc']==0x6003138f for r in configured['trace']),
            native_dispatch_enable_entries=sum(r['pc']==0x60031477 for r in configured['trace']),
            frontier=dict(status=configured['status'], fault=configured['fault'],
                pc=hex(configured['registers']['pc']), native_return_pc=hex(configured['registers']['mdr'])),
            geometry_configuration_completed=configured['status']=='returned',
            geometry_dynamic_setter_entries=[hex(r['pc']) for r in configured['trace'] if r['pc']==0x6042805e],
            capture_unchanged=True, population_resumed=False))
        outputs.append(dict(context, configuration_result=configured,
                            configuration_stack=machine.regions['stack']))
    report = dict(scope=__doc__, candidate_build_revision=upstream['candidate_build_revision'],
        engine=str(engine), cases=rows,
        native_instructions=sum(c['completed'] for row in rows for c in row['cases']),
        maximum_observed_new_stack_depth=max(c['stack_depth_from_call_sp'] for row in rows for c in row['cases']),
        hash_checks_performed=False, native_api_success_stubs=False,
        firmware_files_modified=False, hardware_executed=False, installable=False,
        limits=['Kernel startup marker and restore-mask inputs are explicit CPU0 single-task fixtures. Existing task-mode flags and ready lists are reused. Real startup, IRQ delivery, concurrency and task handoff are not executed.',
                '602ad983..602ad994 is the actual zero-input publication slice, including6042200b and6041c686. The enclosing controller branch, request delivery and task ordering are not executed.',
                'Only the previous-result byte622a04a4 assumes original BSS zero. The four-byte parameter comes from native publication and four result bytes start A5 before original stores.',
                'All upstream cold geometry, format and array conditions remain. No valid active shot geometry is supplied.'])
    return report, dict(upstream=contexts, upstream_report=upstream, cases=outputs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--tool-prefix', required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(geometry_critical_context(args.candidate, args.tool_prefix, args.engine)[0], indent=2))
