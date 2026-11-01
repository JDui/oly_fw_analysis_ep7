#!/usr/bin/env python3
"""Continue native geometry from the explicitly pre-publication array state.

The five arrays have a conditional original BSS source. Their active writer,
callback transport and shot inputs are not replaced with synthetic geometry.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import CALLER, require
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_device_state_sim import admit
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_geometry_resume_sim import geometry_resume_context


ARRAYS = [(0x622a06b4, 128, 16), (0x622a06c4, 144, 16),
          (0x622a06d4, 160, 16), (0x622a06e4, 176, 16),
          (0x622a06f4, 196, 8)]


def geometry_array_context(directory, prefix, engine):
    upstream, contexts = geometry_resume_context(directory, prefix, engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    rows, outputs = [], []
    for index, context in enumerate(contexts['cases']):
        machine = context['machine']
        capture = machine.read(CAPTURE, SIZE)
        registers = context['configuration_result']['registers']
        obj = struct.unpack('<I', machine.read(registers['sp']+4, 4))[0]
        witnesses = [(0x60020068, 'fccd886879a2fccc00af1c62'),
                     (0x60425ccf, 'fccc21910000'), (0x60425ce2, '14a001c967'),
                     (0x60425cfd, 'fcdfb4062a62'), (0x60425d03, 'f4e3'),
                     (0x60425d07, 'fcdfc4062a62'), (0x60425d0d, 'f4e3'),
                     (0x60425d15, 'fcdcf4062a62'), (0x60425d1b, 'f444'),
                     (0x60425d34, 'fcded4062a62'), (0x60425d3a, 'f4d2'),
                     (0x60425d3e, 'fcdee4062a62'), (0x60425d44, 'f4d2'),
                     (0x60427ee3, 'af08d0'), (0x60427f0a, 'aa08d0')]
        require(all(machine.read(pc, len(bytes.fromhex(code))) == bytes.fromhex(code)
                    for pc, code in witnesses), 'native array reader/writer/BSS witnesses changed')
        for address, offset, size in ARRAYS:
            require(0x621caf00 <= address < address+size <= 0x62796888,
                    'geometry array escaped original startup BSS')
            admit(machine, f'geometry_array_prepublication_BSS_{address:x}', address, bytes(size), 'r')
        configured = machine.resume(registers, CALLER+7, full_trace=True, limit=80000,
            breakpoints=[base['syms']['_ep7_gcc_quarantine'], 0x60061808, 0x6040e126])
        fault = configured['fault'] or {}
        require(configured['status'] == 'memory_fault' and
                (fault.get('pc'), fault.get('address'), fault.get('size'), fault.get('access')) ==
                (0x6006a922, 0x8ff006fc, 4, 'read') and
                configured['registers']['mdr'] == 0x6041c6d2 and
                sum(r['pc'] == 0x604276a7 for r in configured['trace']) == 1 and
                not any(r['pc'] == 0x6042805e for r in configured['trace']),
                'native array getter did not return into the original critical-section wrapper')
        copies = {hex(pc): [dict(d0=r['d0'], d1=r['d1'], d2=r['d2'],
                                a0=hex(r['a0']), a1=hex(r['a1']), a2=hex(r['a2']))
                            for r in configured['trace'] if r['pc'] == pc]
                  for pc in (0x60427ece, 0x60427ed8, 0x60427ede, 0x60427f01, 0x60427f06)}
        require(all(len(items) == 8 for items in copies.values()) and
                all(machine.read(obj+offset, size) == machine.read(address, size)
                    for address, offset, size in ARRAYS),
                'native geometry getter did not copy all five eight-element arrays')
        require(machine.read(CAPTURE, SIZE) == capture, 'array probe changed partial capture')
        rows.append(dict(gpio80_input_bit4=index,
            cases=[stage('native_geometry_with_prepublication_arrays', configured)],
            conditional_prepublication_BSS_bytes=sum(size for _, _, size in ARRAYS),
            arrays=[dict(source=hex(a), destination=hex(obj+o), bytes=s, elements=8)
                    for a, o, s in ARRAYS], native_array_copies=copies,
            native_arrays_copied_byte_exact=True,
            native_parameter_getter_return='0x604276a7',
            geometry_dynamic_setter_entries=[dict(pc=hex(r['pc']), a0=hex(r['a0']), a1=hex(r['a1']))
                for r in configured['trace'] if r['pc'] == 0x6042805e],
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
        limits=['The72-byte arrays assume successful original BSS clearing and no prior publication. Zero is not an active shot geometry claim.',
                '60425ba3 copies these arrays only when property9121 equals1. Its480-byte source record and callback lifetime remain unexecuted.',
                'Population, capture allocation, real task ordering and worker execution remain incomplete.'])
    return report, dict(upstream=contexts, upstream_report=upstream, cases=outputs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--tool-prefix', required=True)
    parser.add_argument('--engine', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(geometry_array_context(args.candidate, args.tool_prefix, args.engine)[0], indent=2))
