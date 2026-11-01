#!/usr/bin/env python3
"""Execute the native invalid-format reset before resuming the cold snapshot.

The original reset writes ffff selectors and bounded zeroed arrays. This is an
unconfigured format scenario, not a selected live camera format.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import require
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_message_sim import native_call
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_geometry_sim import map_initializer_storage
from ep7_candidate_device_state_sim import admit
from ep7_candidate_format_record_sim import missing_bytes
from ep7_candidate_optics_cold_sim import optics_cold_context


def initialize_device_defaults(machine, directory, prefix, syms):
    device = 0xa2682d00
    witnesses = [(0x601ecdb7, bytes.fromhex('cd41580004')),
                 (0x601f2634, bytes.fromhex('fcdd98cb1960fcdce0c571a22df1fe')),
                 (0x601f264a, bytes.fromhex('fcddd4cf1960fcdc1cca71a285ef')),
                 (0x601f265f, bytes.fromhex('fcdd18d01960fcdc60ca71a285f8')),
                 (0x601f2690, bytes.fromhex('fa50d824')),
                 (0x601f29cc, bytes.fromhex('fca070ca71a2fcdde0c571a2502df1fe')),
                 (0x601f29ea, bytes.fromhex('fc70148b0000')),
                 (0x601f4705, bytes.fromhex('fcdde0c571a2fcdc50fc1c622df1fe'))]
    require(all(machine.read(pc, len(code)) == code for pc, code in witnesses),
            'native device-default copy loops, destinations or stores changed')
    _, ranges = map_initializer_storage(machine, directory, prefix,
        [(0x601f25f8, 0x601f26af), (0x601f658d, 0x601f6596)],
        [(0x621cf8b8, 0x621cf8bc), (0xa271ca70, 0xa271ca80),
         (0x621d008c, 0x621d008d), (0x621d0144, 0x621d0154),
         (0x621d012c, 0x621d012d)],
        [(0xa271c5e0, 0xa271ca70), (device+4, device+1088),
         (device+9432, device+9433), (device+35604, device+35606),
         (0x621cfc50, 0x621d008c)], name_prefix='native_device_defaults')
    initialized = native_call(machine, syms, 0x601f25f8, 0, 4, limit=10000)
    copies = [(0x6019cb98, 0xa271c5e0, 1084), (0x6019cfd4, 0xa271ca1c, 68),
              (0x6019d018, 0xa271ca60, 16), (0xa271c5e0, device+4, 1084),
              (0xa271c5e0, 0x621cfc50, 1084)]
    require(all(machine.read(source, size) == machine.read(destination, size)
                for source, destination, size in copies) and
            machine.read(0x621cf8b8, 4) == machine.read(0xa271ca70, 4) == struct.pack('<I', device) and
            machine.read(0xa271ca78, 8) == struct.pack('<2I', 0xa268daa0, 0xa268db40) and
            machine.read(device+9432, 1) == b'\0' and machine.read(device+35604, 2) == bytes(2),
            'native device-default copies, aligned object pointers or state resets differ')
    # Two communication-state bytes are outside the native ROM copy. Their
    # cold value is conditional on startup BSS, not an attached device response.
    require(machine.read(0x60020068, 12) == bytes.fromhex('fccd886879a2fccc00af1c62') and
            0x621caf00 <= device+1092-0x40000000 < device+1094-0x40000000 <= 0x62796888,
            'cold communication-state bytes escaped original BSS')
    admit(machine, 'device_communication_conditional_BSS', device+1092, bytes(2), 'r')
    return initialized, dict(native_store_bytes=sum(high-low for low, high in ranges),
        conditional_BSS_bytes=2, device_pointer=hex(device),
        copies=[dict(source=hex(s), destination=hex(d), bytes=n) for s,d,n in copies],
        all_copied_bytes_equal=True)


def refresh_full_mode(machine, syms):
    state = 0xa2788cb0
    # This helper reads the previous295 byte before refreshing it from a
    # property. Use exactly that pre-refresh cold byte, not an invented result.
    require(0x621caf00 <= state+295-0x40000000 < 0x62796888 and
            machine.read(0x606d48a6, 4) == bytes.fromhex('fa402701'),
            'native pre-refresh mode read or BSS range changed')
    admit(machine, 'mode_previous_295_conditional_BSS', state+295, b'\0')
    fields = [(0x606d48ee, 11, 1), (0x606d490c, 12, 1), (0x606d491c, 295, 1),
              (0x606d494f, 296, 1), (0x606d4962, 298, 1), (0x606d4973, 300, 4),
              (0x606d497e, 291, 1)]
    for pc, offset, size in fields:
        code = (bytes([0xf8, 0x50, offset]) if offset < 256 else
                bytes([0xfa, 0x50 if size == 1 else 0x10])+struct.pack('<H', offset))
        require(machine.read(pc, len(code)) == code, 'native mode refresh store changed')
    gaps = missing_bytes(machine, {state+offset+i for _,offset,size in fields for i in range(size)},
                         0xa5, 'native_full_mode_fields')
    refreshed = native_call(machine, syms, 0x606d47fc, 0, 4, limit=5000)
    writes = []
    for pc, offset, size in fields:
        observed = [r for r in refreshed['trace'] if r['pc'] == pc]
        require(len(observed) == 1 and observed[0]['a0'] == state and
                machine.read(state+offset, size) == observed[0]['d0'].to_bytes(4, 'little')[:size],
                'complete native mode refresh did not publish its actual query/store values')
        writes.append(dict(pc=hex(pc), address=hex(state+offset), bytes=size, value=observed[0]['d0']))
    communication = [r['d0'] for r in refreshed['trace'] if r['pc'] == 0x606d4927]
    require(communication == [1], 'native cold communication predicate result changed')
    return refreshed, dict(native_store_bytes=len(gaps), conditional_BSS_bytes=1, writes=writes,
        native_communication_predicate=communication,
        property_query_keys=[hex(r['d0'] & 0xffff) for r in refreshed['trace'] if r['pc'] == 0x6005e971])


def format_snapshot_context(directory, prefix, engine):
    upstream, contexts = optics_cold_context(directory, prefix, engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    syms = base['syms']
    rows, outputs = [], []
    for index, context in enumerate(contexts['cases']):
        machine = context['machine']
        capture, parameters = machine.read(CAPTURE, SIZE), machine.read(0xa2788aa4, 10)
        producer_stack, producer_caller = machine.regions['stack'], machine.regions['caller']
        machine.regions['stack'] = replace(producer_stack, data=b'\xcc'*len(producer_stack.data))
        witnesses = [(0x6065c09a, b'\xdd'+struct.pack('<i', 0x606a4a09-0x6065c09a)+bytes([0, 4])),
                     (0x606a4a0e, bytes.fromhex('fcdcd08a78a200851c')),
                     (0x606a4a5a, bytes.fromhex('fcdcdc472c62857b')),
                     (0x606a4a6b, bytes.fromhex('fcdcec8a78a2')),
                     (0x606a4a74, bytes.fromhex('f46044841da579d0'))]
        require(all(machine.read(pc, len(code)) == code for pc, code in witnesses),
                'native format reset caller, bounded arrays or loop changed')
        stores, ranges = map_initializer_storage(machine, directory, prefix,
            [(0x606a4a09, 0x606a4a38), (0x606a4a41, 0x606a4a7f)],
            [(0xa2788ab0, 0xa2788b68)],
            [(0xa2788ad0, 0xa2788aec), (0xa2788aec, 0xa2788b65),
             (0x622c47dc, 0x622c4857)], name_prefix='native_invalid_format_reset')
        reset = native_call(machine, syms, 0x606a4a09, 0, 4, limit=5000)
        expected = bytearray(28)
        expected[0] = 1
        struct.pack_into('<2h', expected, 20, -32768, -32768)
        require(machine.read(0xa2788ab0, 4) == b'\xff'*4 and
                machine.read(0xa2788b67, 1) == b'\0' and
                machine.read(0x622c47dc, 123) == bytes(123) and
                machine.read(0xa2788aec, 121) == bytes(121) and
                machine.read(0xa2788ad0, 28) == bytes(expected) and
                machine.read(0xa2788aa4, 10) == parameters,
                'native invalid selectors, bounded clears, signed minima or prior parameters differ')
        machine.regions['stack'], machine.regions['caller'] = producer_stack, producer_caller
        produced = machine.resume(context['producer_result']['registers'], 0x60409ecb,
            full_trace=True, limit=80000,
            breakpoints=[syms['_ep7_gcc_quarantine'], 0x60061808, 0x6040e126])
        fault = produced['fault'] or {}
        require(produced['status'] == 'memory_fault' and
                (fault.get('pc'), fault.get('address'), fault.get('size'), fault.get('access')) ==
                (0x606d6a41, 0xa2788dd7, 1, 'read') and
                produced['registers']['mdr'] == 0x6065e97a,
                'format producer did not reach the unrefreshed mode295 getter')
        stages = [stage('native_invalid_format_full_reset', reset),
                  stage('native_snapshot_resume_after_format_reset', produced)]
        producer_stack, producer_caller = machine.regions['stack'], machine.regions['caller']
        machine.regions['stack'] = replace(producer_stack, data=b'\xcc'*len(producer_stack.data))
        defaults, default_metadata = initialize_device_defaults(machine, directory, prefix, syms)
        modes, mode_metadata = refresh_full_mode(machine, syms)
        machine.regions['stack'], machine.regions['caller'] = producer_stack, producer_caller
        produced = machine.resume(produced['registers'], 0x60409ecb, full_trace=True, limit=80000,
            breakpoints=[syms['_ep7_gcc_quarantine'], 0x60061808, 0x6040e126])
        fault = produced['fault'] or {}
        format_returns = [hex(r['pc']) for r in produced['trace'] if r['pc'] == 0x60427f7d]
        require(produced['status'] == 'memory_fault' and
                (fault.get('pc'), fault.get('address'), fault.get('size'), fault.get('access')) ==
                (0x60427f9c, 0x6229fb98, 2, 'write') and
                produced['registers']['mdr'] == 0x60427f86 and format_returns == ['0x60427f7d'],
                'complete native format getter did not return before its first output-record store')
        format_record = machine.read(produced['registers']['sp']+8, 150)
        require(format_record[6:127] == bytes(121) and
                format_record[146:148] == struct.pack('<H', 2),
                'original unconfigured-format output did not retain its blank payload and invalid status')
        stages.extend([stage('native_device_defaults_full_initialize', defaults),
                       stage('native_complete_format_mode_refresh', modes),
                       stage('native_snapshot_resume_after_mode_refresh', produced)])
        require(machine.read(CAPTURE, SIZE) == capture, 'format snapshot trace changed partial capture')
        rows.append(dict(gpio80_input_bit4=index, cases=stages,
            native_initializer_storage_bytes=sum(high-low for low, high in ranges),
            native_reset_selectors=[65535, 65535], native_reset_arrays_bytes=[123, 121],
            native_reset_record=bytes(expected).hex(), parameter_record_unchanged=True,
            device_defaults=default_metadata, complete_mode_refresh=mode_metadata,
            format_getter_return_pcs=format_returns, native_format_record=format_record.hex(),
            native_format_record_bytes=150, invalid_format_status=2,
            frontier=dict(status=produced['status'], fault=produced['fault'],
                pc=hex(produced['registers']['pc']), native_return_pc=hex(produced['registers']['mdr'])),
            snapshot_producer_completed=produced['status']=='returned', capture_unchanged=True))
        outputs.append(dict(context, producer_result=produced))
    report = dict(scope=__doc__, candidate_build_revision=upstream['candidate_build_revision'],
        engine=str(engine), cases=rows,
        native_instructions=sum(c['completed'] for row in rows for c in row['cases']),
        maximum_observed_new_stack_depth=max(c['stack_depth_from_call_sp'] for row in rows for c in row['cases']),
        hash_checks_performed=False, native_api_success_stubs=False,
        firmware_files_modified=False, hardware_executed=False, installable=False,
        limits=['Original606a4a09 and nested606a4a41 execute completely with only their reviewed write destinations. Their enclosing core initializer and real task ordering are not established.',
                'The ffff selector is produced by native reset, not a forced zero or valid format. Live format selection and frame publication remain unproven.',
                'Original601f25f8 device-default initialization and606d47fc mode refresh complete independently. Two device communication bytes and the previous mode295 byte assume cold BSS; active device replies and lifecycle ordering remain unproven.',
                'Upstream cold BSS, device-input and task-handoff assumptions remain. The independent geometry/population consumers are not resumed here.'])
    return report, dict(upstream=contexts, upstream_report=upstream, cases=outputs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--tool-prefix', required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(format_snapshot_context(args.candidate, args.tool_prefix, args.engine)[0], indent=2))
