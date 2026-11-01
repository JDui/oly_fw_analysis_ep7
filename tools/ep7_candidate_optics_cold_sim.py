#!/usr/bin/env python3
"""Execute native unavailable-device initialization and cold coordinate fallback.

The sixteen cache bytes assume startup BSS before any frame publishes parameters.
Active frame publication, attached-device calibration and startup ordering remain
unproven. Device availability/type values come from original native initializers.
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
from ep7_candidate_geometry_sim import map_initializer_storage
from ep7_candidate_history_sim import history_context


CACHE = 0xa271ca80


def optics_cold_context(directory, prefix, engine):
    upstream, contexts = history_context(directory, prefix, engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    syms = base['syms']
    records = {r['key'] >> 4: r for r in base['property_records']}
    rows, outputs = [], []
    for index, context in enumerate(contexts['cases']):
        machine = context['machine']
        capture = machine.read(CAPTURE, SIZE)
        producer_stack, producer_caller = machine.regions['stack'], machine.regions['caller']
        machine.regions['stack'] = replace(producer_stack, data=b'\xcc'*len(producer_stack.data))
        stores, ranges = map_initializer_storage(machine, directory, prefix,
            [(0x600f767d, 0x600f772b)],
            [(0xa2726b60, 0xa2726b64), (0x621d1358, 0x621d13d9)],
            name_prefix='native_device_presence_reset')
        initialized = native_call(machine, syms, 0x600f767d, 0, 4, limit=1000)
        pointers = [(0xf8c1, 0x621d1360), (0xf101, 0x621d1364)]
        require(machine.read(0xa2726b60, 4) == bytes(4) and
                all(machine.read(address, 4) == struct.pack('<I', records[key >> 4]['data'])
                    for key, address in pointers),
                'native device presence reset or registered property pointers differ')
        require(machine.read(0x601f2699, 13) == bytes.fromhex('00cd5001e0108001cd4901e010') and
                machine.read(0x601f27f8, 2) == bytes.fromhex('f4f0') and
                machine.read(0x601f2806, 2) == bytes.fromhex('f072') and
                machine.read(0x601f280f, 3) == bytes.fromhex('f87202') and
                machine.read(0x601f2829, 3) == bytes.fromhex('f85404'),
                'native indexed device-reset callers or indirect stores changed')
        # Only actual indexed stores for the original caller's indices0/1.
        for name, address, size in [('device_type', 0xa271ca74, 4),
                                    ('device_period', 0x621d0090, 8),
                                    ('device_status0', 0x621d0124, 1),
                                    ('device_status1', 0x621d012a, 1)]:
            admit(machine, 'native_'+name, address, b'\xa5'*size)
        reset = machine.run(0x601f2699, 0x601f26a6, overrides=dict(sp=CALL_SP),
            full_trace=True, limit=1000, breakpoints=[syms['_ep7_gcc_quarantine']])
        result_ok(machine, reset, 0x601f26a6, CALL_SP)
        require(machine.read(0xa271ca74, 4) == struct.pack('<2H', 2826, 2826) and
                machine.read(0x621d0090, 8) == struct.pack('<4H', 500, 287, 500, 287) and
                machine.read(0x621d0124, 1) == machine.read(0x621d012a, 1) == b'\0',
                'native two-device reset or original integer period conversion differs')
        require(machine.read(0x60020068, 12) == bytes.fromhex('fccd886879a2fccc00af1c62') and
                0x621caf00 <= CACHE-0x40000000 < CACHE+16-0x40000000 <= 0x62796888,
                'cold prepublication cache is outside the witnessed startup BSS')
        # This is the prepublication BSS scenario, not a fabricated frame record.
        # In particular it does not fill the five unwritten postpublication bytes.
        admit(machine, 'parameter_cache_conditional_prepublication_BSS', CACHE, bytes(16), 'r')
        machine.regions['stack'], machine.regions['caller'] = producer_stack, producer_caller
        copy = machine.resume(context['producer_result']['registers'], 0x601f8982,
            full_trace=True, limit=1000, breakpoints=[syms['_ep7_gcc_quarantine']])
        require(copy['status'] == 'returned' and copy['fault'] is None,
                'original cache getter did not return to its actual caller')
        destination = int(upstream['cases'][index]['native_cache_copy_requests'][0]['destination'], 16)
        require(copy['registers']['a2'] == destination and machine.read(destination, 16) == bytes(16),
                'native cache getter did not copy all sixteen prepublication bytes')
        fallback = machine.resume(copy['registers'], 0x601f89c0, full_trace=True, limit=2000,
            breakpoints=[syms['_ep7_gcc_quarantine']])
        require(fallback['status'] == 'returned' and fallback['fault'] is None,
                'original no-device coordinate fallback did not reach its return')
        device_returns = [r['a0'] for r in fallback['trace'] if r['pc'] == 0x601f8e21]
        type_returns = [r['d0'] for r in fallback['trace'] if r['pc'] == 0x601f8e35]
        transform_returns = [r['d0'] for r in fallback['trace'] if r['pc'] == 0x601f8991]
        registers = fallback['registers']
        point = machine.read(registers['a3'], 4)
        require(device_returns == [0] and type_returns == [0] and transform_returns == [0] and
                machine.read(registers['a2'], 4) == point and
                machine.read(registers['sp']+40, 28) == bytes(24)+struct.pack('<I', 0x3f800000) and
                sum(r['pc'] in (0x601f89b8, 0x601f89bd) for r in fallback['trace']) == 2,
                'native unavailable-device test, identity defaults or two-halfword pass-through differ')
        produced = machine.resume(registers, 0x60409ecb, full_trace=True, limit=80000,
            breakpoints=[syms['_ep7_gcc_quarantine'], 0x60061808, 0x6040e126])
        fault = produced['fault'] or {}
        require(produced['status'] == 'memory_fault' and
                (fault.get('pc'), fault.get('address'), fault.get('size'), fault.get('access')) ==
                (0x6065e79c, 0xa2788ab2, 2, 'read') and
                produced['registers']['mdr'] == 0x6065e77c,
                'snapshot did not stop at the still-uninitialized format-record selector')
        require(machine.read(CAPTURE, SIZE) == capture, 'cold optics trace changed partial capture')
        stages = [stage(name, result) for name, result in (
            ('native_device_presence_initialize', initialized),
            ('native_two_device_type_reset', reset),
            ('native_prepublication_parameter_copy', copy),
            ('native_unavailable_device_coordinate_fallback', fallback),
            ('native_snapshot_resume_after_optics_fallback', produced))]
        rows.append(dict(gpio80_input_bit4=index, cases=stages,
            native_initializer_storage_bytes=sum(high-low for low, high in ranges)+14,
            native_presence_flags=list(machine.read(0xa2726b60, 4)),
            property_bindings=[dict(key=hex(key), slot=hex(address), pointer=hex(records[key >> 4]['data']))
                               for key, address in pointers],
            native_device_types=[2826, 2826], native_period_pairs=[[500, 287], [500, 287]],
            conditional_prepublication_BSS_bytes=16, cache_copy_destination=hex(destination),
            native_device_pointer_returns=device_returns, native_type_returns=type_returns,
            native_transform_returns=transform_returns, passthrough_point_bytes=point.hex(),
            original_halfword_passthrough_verified=True, active_frame_cache_published=False,
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
        limits=['Exactly16 cache bytes assume original BSS clear and cached/uncached alias identity before frame publication. This does not establish any active frame or its five unwritten parameter bytes.',
                'Original600f767d and both indexed601f27ea calls execute completely. Their enclosing startup schedule, attached device and calibrated transform path remain unproven.',
                'The two-halfword coordinate pass-through is the actual unavailable-device branch. It is not active camera geometry or proof that skipping calibration is correct on hardware.',
                'The separate geometry/population consumers remain paused. Code/RAM ownership, full lifecycle, updater and recovery remain open.'])
    return report, dict(upstream=contexts, cases=outputs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--tool-prefix', required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(optics_cold_context(args.candidate, args.tool_prefix, args.engine)[0], indent=2))
