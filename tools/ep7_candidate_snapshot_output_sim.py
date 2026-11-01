#!/usr/bin/env python3
"""Admit only native geometry-output stores and continue its actual producer.

Output starts A5; unwritten holes remain unmapped. No active format or populated
camera record is supplied by this probe.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import require
from ep7_candidate_state_sim import CALL_SP
from ep7_candidate_message_sim import result_ok
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_format_record_sim import missing_bytes
from ep7_candidate_device_state_sim import admit
from ep7_candidate_geometry_sim import map_initializer_storage
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_format_snapshot_sim import format_snapshot_context


OUTPUT = 0x6229fb98


def output_storage(machine):
    require(machine.read(0x60419529, 12) == bytes.fromhex('fccc98fb2962fc818cfb2962') and
            machine.read(0x6229fb8c, 4) == struct.pack('<I', OUTPUT) and
            machine.read(0x60427f9c, 2) == bytes.fromhex('f073') and
            machine.read(0x60427faa, 2) == bytes.fromhex('8079') and
            machine.read(0x60428050, 4) == bytes.fromhex('fad39000'),
            'native output pointer, first store,121-byte copy or subrecord binding changed')
    fields = [(0x60427f9f, 124, 4), (0x60427fb8, 132, 2), (0x60427fc1, 134, 2),
              (0x60427fc9, 141, 1), (0x60427fd1, 142, 1), (0x60427fd8, 143, 1),
              (0x60427fe2, 136, 2), (0x60427fec, 138, 1), (0x60427ff6, 139, 1),
              (0x60428000, 140, 1), (0x60428007, 168, 1), (0x6042803b, 166, 2)]
    for pc, offset, width in fields:
        code = (bytes([0xf8, 0x13, offset]) if width == 4 else
                bytes([0xfa, 0x73 if width == 2 else 0x53])+struct.pack('<H', offset))
        require(machine.read(pc, len(code)) == code, 'native geometry-output direct member store changed')
    witnesses = [(0x60428013, 'f052'), (0x60428018, 'f87204'), (0x6042801e, 'f87206'),
                 (0x60428024, 'f85202'), (0x6042802f, 'f85201'), (0x6042804a, 'fa378000'),
                 (0x60428d67, 'f050'), (0x60428d73, 'f87002'), (0x60428d7e, 'f87c04'),
                 (0x60428d8f, 'f85006'), (0x60428d97, 'f85007')]
    require(all(machine.read(pc, len(bytes.fromhex(code))) == bytes.fromhex(code)
                for pc,code in witnesses), 'native output subrecord stores changed')
    # Two-byte header +121-byte native copy; all other reviewed member stores.
    offsets = set(range(123))
    for _, offset, width in fields:
        offsets.update(range(offset, offset+width))
    for offset, width in [(128,4),(152,3),(156,4),(144,1),(146,6)]:
        offsets.update(range(offset, offset+width))
    gaps = missing_bytes(machine, {OUTPUT+i for i in offsets}, 0xa5, 'native_geometry_output')
    require(len(gaps) == len(offsets) == 160,
            'geometry-output store coverage overlaps old state or changed extent')
    return sorted(offsets)


def snapshot_output_context(directory, prefix, engine):
    upstream, contexts = format_snapshot_context(directory, prefix, engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    rows, outputs = [], []
    for index, context in enumerate(contexts['cases']):
        machine = context['machine']
        capture = machine.read(CAPTURE, SIZE)
        registers = context['producer_result']['registers']
        source = machine.read(registers['sp']+14, 121)
        offsets = output_storage(machine)
        copied = machine.resume(registers, 0x60427fb3, full_trace=True, limit=2000,
            breakpoints=[base['syms']['_ep7_gcc_quarantine']])
        require(copied['status'] == 'returned' and copied['fault'] is None and
                machine.read(OUTPUT, 2) == struct.pack('<H', 1) and
                machine.read(OUTPUT+2, 121) == source and machine.read(OUTPUT+124, 4) == bytes(4),
                'native output header, zero word or121-byte copy differs from its actual format source')
        produced = machine.resume(copied['registers'], 0x60409ecb, full_trace=True, limit=80000,
            breakpoints=[base['syms']['_ep7_gcc_quarantine'], 0x60061808, 0x6040e126])
        fault = produced['fault'] or {}
        require(produced['status'] == 'memory_fault' and
                (fault.get('pc'), fault.get('address'), fault.get('size'), fault.get('access')) ==
                (0x60428046, 0xa2788df8, 4, 'read') and
                produced['registers']['mdr'] == 0x60556f15 and
                produced['registers']['a0'] == 0xa2788dec,
                'output constructor did not reach the native fallback-record pointer')
        stages = [stage('native_geometry_output_header_and_copy', copied),
                  stage('native_geometry_output_to_fallback_pointer', produced)]
        require(machine.read(0x606d5f1a, 13) == bytes.fromhex('fca0ac8c78a2f84035a000c90a') and
                machine.read(0xa2788ce5, 1) == b'\0' and
                machine.read(0xa2788dec, 1) == b'\1' and
                machine.read(0xa2788e00, 4) == struct.pack('<2h', -32768, -32768) and
                0x621caf00 <= 0x62788df8 < 0x62788dfc <= 0x62796888,
                'original fallback selector, native default members or pointer BSS provenance changed')
        # The original getter chose the cold fallback object, not state+104's
        # active record. Only its untouched pointer word assumes startup BSS.
        admit(machine, 'format_fallback_pointer_conditional_BSS', 0xa2788df8, bytes(4), 'r')
        produced = machine.resume(produced['registers'], 0x60409ecb, full_trace=True, limit=80000,
            breakpoints=[base['syms']['_ep7_gcc_quarantine'], 0x60061808, 0x6040e126])
        stages.append(stage('native_geometry_output_with_cold_fallback_pointer', produced))
        fault = produced['fault'] or {}
        require(produced['status'] == 'memory_fault' and
                (fault.get('pc'), fault.get('address'), fault.get('size'), fault.get('access')) ==
                (0x60428b6f, 0x622a094c, 2, 'read') and
                produced['registers']['mdr'] == 0x6005c8df,
                'native output did not reach the unpublished coordinate-record copy')
        position_witnesses = [(0x60428b63, 'fcdd4c092a62'), (0x60428b6c, '80fc'),
                              (0x60428937, 'fc8a4c092a62'), (0x6042893d, 'fc8f4e092a62'),
                              (0x60428945, 'fc8350092a62'), (0x6042894d, 'fc8352092a62')]
        require(all(machine.read(pc, len(bytes.fromhex(code))) == bytes.fromhex(code)
                    for pc,code in position_witnesses) and
                0x621caf00 <= 0x622a094c < 0x622a0954 <= 0x62796888,
                'original coordinate-record producer, four-halfword consumer or BSS provenance changed')
        admit(machine, 'coordinate_record_conditional_prepublication_BSS', 0x622a094c, bytes(8), 'r')
        _, helper_ranges = map_initializer_storage(machine, directory, prefix,
            [(0x60428c95, 0x60428d9d)], [(0x622a0954, 0x622a0960)],
            name_prefix='native_coordinate_conversion_outputs')
        produced = machine.resume(produced['registers'], 0x60409ecb, full_trace=True, limit=80000,
            breakpoints=[base['syms']['_ep7_gcc_quarantine'], 0x60061808, 0x6040e126])
        stages.append(stage('native_geometry_output_with_unpublished_coordinate_record', produced))
        position_copies = [r for r in produced['trace'] if r['pc'] == 0x60428b73]
        require(len(position_copies) == 4 and all(r['d1'] == 0 for r in position_copies) and
                machine.read(0x622a095c, 4) == struct.pack('<2H', 83, 74),
                'native four-halfword copy or cold integer coordinate conversion changed')
        constructor_returns = [r['pc'] for r in produced['trace'] if r['pc'] == 0x6042705e]
        callback_returns = [r['pc'] for r in produced['trace'] if r['pc'] == 0x6041a224]
        fault = produced['fault'] or {}
        require(produced['status'] == 'memory_fault' and
                (fault.get('pc'), fault.get('address'), fault.get('size'), fault.get('access')) ==
                (0x603f9f4c, 0x62293d28, 2, 'write') and
                produced['registers']['mdr'] == 0x6041a232 and
                constructor_returns == [0x6042705e] and callback_returns == [0x6041a224],
                'native output constructor/callback did not return before the wrapper status store')
        require(machine.read(0x603f9f4c, 9) == bytes.fromhex('fc83283d2962de0000'),
                'original wrapper status setter changed')
        wrapper_value = produced['registers']['d0'] & 0xffff
        admit(machine, 'native_snapshot_wrapper_status', 0x62293d28, b'\xa5'*2)
        produced = machine.resume(produced['registers'], 0x60409ecb, full_trace=True, limit=80000,
            breakpoints=[base['syms']['_ep7_gcc_quarantine'], 0x60061808, 0x6040e126])
        result_ok(machine, produced, 0x60409ecb, CALL_SP-68)
        require(machine.read(0x62293d28, 2) == struct.pack('<H', wrapper_value),
                'original wrapper status setter did not publish its actual value')
        stages.append(stage('native_snapshot_wrapper_after_output_callback', produced))
        require(machine.read(CAPTURE, SIZE) == capture, 'snapshot output trace changed partial capture')
        rows.append(dict(gpio80_input_bit4=index, cases=stages,
            writable_native_output_bytes=len(offsets), native_output_address=hex(OUTPUT),
            writable_output_offsets=offsets,
            unmapped_hole_offsets=[i for i in range(169) if i not in offsets],
            native_header=1, native_copied_bytes=121, native_copy_matches_actual_source=True,
            conditional_fallback_pointer_BSS_bytes=4,
            conditional_coordinate_record_BSS_bytes=8,
            additional_native_conversion_output_bytes=sum(high-low for low,high in helper_ranges),
            coordinate_conversion_outputs={hex(r.address):r.data.hex() for key,r in machine.regions.items()
                                           if key.startswith('native_coordinate_conversion_outputs_')},
            native_wrapper_status=wrapper_value, native_wrapper_status_bytes=2,
            coordinate_record_native_halfword_copies=len(position_copies),
            native_integer_conversion_coordinates=[83, 74],
            snapshot_selectors=machine.read(0x6229fc44, 2).hex(),
            snapshot_pointer=hex(struct.unpack('<I', machine.read(0x6229fb88, 4))[0]),
            output_fields={str(i):machine.read(OUTPUT+i,1).hex() for i in offsets},
            output_constructor_returned=bool(constructor_returns),
            callback_return_pcs=[hex(pc) for pc in callback_returns],
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
        limits=['Only160 bytes targeted by reviewed native output stores are writable and start A5. Nine holes before the last output member remain unmapped; the complete object is not declared initialized.',
                'The source format is the upstream unconfigured/no-device cold scenario. Active frames, true geometry and real task ordering remain unproven.',
                'The native getter selected fallbacka2788dec using its actual reset flag. Only that fallback record pointer+12 uses an additional4B cold BSS condition; no active record pointer is invented.',
                'The8B coordinate record assumes prepublication BSS; its active writer604288f9 and enclosing caller6028f3ef remain unexecuted. The original four-halfword copy and conversion code execute with that explicit cold input.',
                'Separate geometry/population consumers remain paused; native producer completion is reported only at the real callback-wrapper stop.'])
    return report, dict(upstream=contexts, upstream_report=upstream, cases=outputs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--tool-prefix', required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(snapshot_output_context(args.candidate, args.tool_prefix, args.engine)[0], indent=2))
