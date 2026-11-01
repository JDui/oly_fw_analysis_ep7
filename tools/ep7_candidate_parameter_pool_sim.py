#!/usr/bin/env python3
"""Execute the original four-slot parameter pool and its reset publication.

Only native store destinations are mapped from A5. This independent pool branch
does not replace the paused geometry inputs or claim a completed active callback.
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
from ep7_candidate_message_sim import native_call
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_geometry_sim import map_initializer_storage
from ep7_candidate_format_record_sim import missing_bytes
from ep7_candidate_device_state_sim import admit
from ep7_candidate_geometry_critical_sim import geometry_critical_context


POOL, STRIDE = 0x62293d98, 480
FLAGS, SELECTORS = 0x62293d44, 0x62293d40


def parameter_pool_context(directory, prefix, engine):
    upstream, contexts = geometry_critical_context(directory, prefix, engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    # The pool has no board/GPIO dependency; run this independent branch once.
    context = contexts['cases'][0]
    machine = context['machine'].clone()
    capture = machine.read(CAPTURE, SIZE)
    configuration_stack = machine.regions['stack']
    configuration_caller = machine.regions['caller']
    machine.regions['stack'] = replace(configuration_stack, data=b'\xcc'*len(configuration_stack.data))
    witnesses = [(0x6040a2b1, 'dde902ffffe010'), (0x6041d1ec, 'cd08840004'),
                 (0x604155f4, 'dd6850feff800cdd4e48fefff0148007ddaf51feffc010df0004'),
                 (0x603fa5bb, 'fb14e001'), (0x603fa615, '89fb158802'),
                 (0x603fa62d, '88f8c004fcc058592962'),
                 (0x603f9e49, '2f0003'), (0x603f9e71, 'a531d0'),
                 (0x603f9e86, 'fac94401d0'), (0x603f9e9d, 'f4f2f4f3'),
                 (0x603f9ea7, 'aa08d0'),
                 (0x603f9eb6, '2eff7ff4e22e0080f4e1'),
                 (0x603f9ec3, 'a508d0'), (0x603fa651, '8007fc81443d2962')]
    require(all(machine.read(pc, len(bytes.fromhex(code))) == bytes.fromhex(code)
                for pc, code in witnesses), 'native parameter-pool binding or reset loop changed')
    fields = [(0,128), (205,2), (212,8)]
    ranges = [(FLAGS, FLAGS+16)] + [(POOL+slot*STRIDE+offset, POOL+slot*STRIDE+offset+size)
              for slot in range(4) for offset, size in fields]
    _, mapped = map_initializer_storage(machine, directory, prefix,
        [(0x603fa59a,0x603fa65c),(0x603fa4f6,0x603fa506)],
        [(SELECTORS,POOL+4*STRIDE),(0xa2740f9c,0xa2740fa4)], ranges,
        name_prefix='native_parameter_pool_initialize')
    initialized = native_call(machine, base['syms'], 0x603fa59a, 0xe0, 16, limit=5000)
    require(machine.read(SELECTORS, 2) == bytes(2) and
            machine.read(FLAGS, 16) == struct.pack('<4I',7,0,0,0) and
            machine.read(0x62293d54, 4) == struct.pack('<2H',1792,1792),
            'native four-slot initialization did not establish selector0 and mask7')
    pool_rows = []
    for slot in range(4):
        address = POOL+slot*STRIDE
        first = machine.read(address,128)
        expected = (struct.pack('<6h',*([1792]*6))+struct.pack('<h',-768)+
                    struct.pack('<49h',*([768]*49))+
                    struct.pack('<3I',0x62294518+slot*648,0x62294f38+slot*648,0x62295958+slot*16)+
                    struct.pack('<2H',1792,1792))
        require(first == expected and machine.read(address+205,2)==bytes([1,4]) and
                machine.read(address+212,8)==struct.pack('<2HI',1792,1792,0),
                'native parameter initial fields differ from their exact stores')
        pool_rows.append(dict(slot=slot,address=hex(address),initial_written_bytes=138,
            curve_a=hex(0x62294518+slot*648),curve_b=hex(0x62294f38+slot*648),
            auxiliary_pointer=hex(0x62295958+slot*16)))
    selected = POOL+STRIDE
    # The native allocator starts at the next free slot. Admit only reset
    # writes in that slot and the two648-byte arrays its pointers already name.
    extra = missing_bytes(machine, set(range(selected+128,selected+192)) |
        set(range(selected+196,selected+205)) | {selected+224}, 0xa5, 'native_parameter_reset')
    require(len(extra)==74, 'selected reset store coverage changed')
    for label, address in [('a',0x62294518+648),('b',0x62294f38+648)]:
        admit(machine,f'native_parameter_curve_{label}',address,b'\xa5'*648)
    reset = native_call(machine, base['syms'], 0x604155f4, 0, 4, limit=15000)
    looked_up = native_call(machine, base['syms'], 0x603fa833, 0, 4, dict(d0=1), limit=1000)
    require(machine.read(SELECTORS, 2) == bytes([1,1]) and
            machine.read(FLAGS, 16) == struct.pack('<4I',0,7,0,0) and
            looked_up['registers']['a0'] == selected,
            'original reserve/reset/publish/lookup did not move mask7 from slot0 to slot1')
    require(machine.read(selected, 14) == struct.pack('<7h',*([768]*6+[-768])) and
            machine.read(selected+14,98) == struct.pack('<49h',*([768]*49)) and
            all(machine.read(a,648) == struct.pack('<324h',*([768]*324))
                for a in (0x62294518+648,0x62294f38+648)) and
            machine.read(selected+128,64) == struct.pack('<32h',*([768]*16+[32767]*8+[-32768]*8)) and
            machine.read(selected+196,9) == bytes(9) and machine.read(selected+224,1)==b'\1' and
            machine.read(0xa2740f9c,8)==bytes(8),
            'native reset did not produce its nonzero defaults and cleared status')
    reserve = [r for r in reset['trace'] if r['pc']==0x604155fb]
    publish = [r for r in reset['trace'] if r['pc']==0x603fa7b3]
    loop_counts = {hex(pc):sum(r['pc']==pc for r in reset['trace'])
                   for pc in (0x603f9e6c,0x603f9e7c,0x603f9e82,0x603f9e9d,
                              0x603f9e9f,0x603f9ea2,0x603f9eb9,0x603f9ebe)}
    require(len(reserve)==len(publish)==1 and reserve[0]['a0']==selected and publish[0]['d0']==7 and
            list(loop_counts.values()) == [49,324,324,8,8,8,8,8],
            'native reset/publication entry or array write counts changed')
    gaps = (list(range(selected+192,selected+196))+[selected+207]+
            list(range(selected+208,selected+212))+list(range(selected+220,selected+224)))
    require(all(not any(r.address<=a<r.address+len(r.data) for r in machine.regions.values()) for a in gaps),
            'unknown selected parameter fields became readable')
    require(machine.read(CAPTURE,SIZE)==capture, 'independent pool execution changed partial capture')
    stages = [stage('native_parameter_pool_initialize',initialized),
              stage('native_parameter_reserve_reset_publish',reset),
              stage('native_parameter_lookup_mask1',looked_up)]
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],engine=str(engine),
        cases=stages,native_instructions=sum(r['completed'] for r in stages),
        maximum_observed_new_stack_depth=max(r['stack_depth_from_call_sp'] for r in stages),
        initial_slots=pool_rows,selected_slot=1,selected_pointer=hex(selected),
        selectors_after=[1,1],slot_masks_after=[0,7,0,0],native_reset_store_counts=loop_counts,
        arrays_halfword_values=[768,768,32767,-32768],array_byte_values=[0]*8,
        curve_elements_each=324,curve_element_value=768,
        mapped_native_store_bytes=sum(high-low for low,high in mapped)+len(extra)+1296,
        selected_unwritten_fields_unmapped=[hex(a) for a in gaps],
        conditional_BSS_bytes_added=0,native_callback_executed=False,
        active_array_publication_executed=False,geometry_resumed=False,capture_unchanged=True,
        hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['One independent branch runs the complete pool initializer and reserve/reset/publish helper. The outer startup/event/task wrappers remain unexecuted.',
                'Only reviewed native stores receive A5 destination memory; unknown480-byte record members and unselected curve payloads remain unmapped.',
                'The native reset record is not a valid active shot claim. The actual callback/writer, property9121 enable transition, active processing and lifetime remain open.',
                'The paused geometry stack and inputs are preserved. Its current62293d1c dependency is not closed by this independent pool branch.'])
    machine.regions['stack'] = configuration_stack
    machine.regions['caller'] = configuration_caller
    return report,dict(upstream=contexts,machine=machine,syms=base['syms'],
        configuration_result=context['configuration_result'],configuration_stack=configuration_stack,
        parameter_pointer=selected)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(parameter_pool_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
