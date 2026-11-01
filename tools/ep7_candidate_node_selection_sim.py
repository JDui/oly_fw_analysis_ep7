#!/usr/bin/env python3
"""Select the real newly sealed node through the complete native queue callback.

Original engine parameters and two resource pools are initialized. Prior special
coordinates/extended flags retain explicit cold-BSS assumptions; this is not
proof of active engine scheduling or a physical frame.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import CALLER, require
from ep7_candidate_state_sim import CALL_SP, objects, ready_lock
from ep7_candidate_capture_allocation_sim import NEW_CAPTURE
from ep7_candidate_node_factory_sim import NEW_NODE, sparse_read
from ep7_candidate_capture_sim import CAPTURE, ASSOCIATED, NODE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_device_state_sim import admit
from ep7_candidate_format_record_sim import missing_bytes
from ep7_candidate_message_sim import native_call, result_ok
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_color_population_sim import color_population_context


ENGINE, FORMAT = 0x6223d8a0,0x6223d60c
POOL59, POOL34 = 0xa269fde4,0x8ff00290
FORMAT_WRITES = ((96,26),(124,1),(126,30),(182,9),(216,1),(228,4),(232,4),(240,4))


def node_selection_context(directory,prefix,engine):
    upstream,contexts = color_population_context(directory,prefix,engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    syms = base['syms']
    context = contexts['cases'][0]
    machine = context['color_capture_machine'].clone()
    machine.regions['stack'] = replace(machine.regions['stack'],data=b'\xcc'*len(machine.regions['stack'].data))
    sidecar = syms['_ep7_controller_sidecar_unresolved']
    sealed = machine.read(sidecar,664)
    capture,old_capture = machine.read(NEW_CAPTURE,SIZE),machine.read(CAPTURE,SIZE)
    task_cell = machine.regions['task_cell'].data
    original_flags = [int.from_bytes(machine.read(FORMAT+o,n),'little') for o,n in ((4,4),(8,2))]
    witnesses = [
        (0x6029d351,'8a07fc8ba0d82362fcdca0d82362dd'),
        (0x6029d3ef,'fccc0cd62362fc81c8d82362'),
        (0x603dc325,'800942040042082c0005420c2cc0034210fcccffff00004214fcdce4fd69a2fccc00c549ddfccd00c01200250059cd850ea00c'),
        (0x603db301,'80144204004208420c4210fcccffff00004214fcdc9002f08ffccc407bdfab2d0001250034cdb21ea00c'),
        (0x602a7ce1,'00fc8388e62362fc838ae62362')]
    require(all(machine.read(address,len(bytes.fromhex(code))) == bytes.fromhex(code)
                for address,code in witnesses) and
            all(machine.read(0x6053a258+(selector>>8)*8,8) == struct.pack('<2I',selector,address)
                for selector,address in ((0x5900,POOL59),(0x3400,POOL34))) and
            machine.read(0x6223d134,4) == struct.pack('<I',0x602a2d43),
            'original engine/pool setup, selector callback or format reset changed')
    engine_bytes = missing_bytes(machine,range(ENGINE,ENGINE+168),0xa5,'native_selector_engine')
    require(len(engine_bytes) == 168, 'native engine parameter clear extent changed')
    engine_init = machine.run(0x6029d351,0x6029d402,overrides=dict(sp=CALL_SP),full_trace=True,limit=2000)
    result_ok(machine,engine_init,0x6029d402,CALL_SP)
    require(machine.read(ENGINE,3) == b'\x07\0\x01' and machine.read(ENGINE+40,4) == struct.pack('<I',FORMAT),
            'native engine type or format pointer changed')
    pool_bytes = missing_bytes(machine,[a+i for a in (POOL59,POOL34) for i in range(63)],
        0xa5,'native_selector_resource_pools')
    require(len(pool_bytes) == 126, 'two original63-byte pool headers overlap existing state')
    initialized = []
    for start,stop in ((0x603dc325,0x603dc358),(0x603db301,0x603db32b)):
        result = machine.run(start,stop,overrides=dict(sp=CALL_SP),full_trace=True,limit=2000)
        result_ok(machine,result,stop,CALL_SP)
        initialized.append(result)
    for address,backing,stride,count,selector,width,height in (
        (POOL59,0xdd49c500,1228800,9,0x5900,1280,960),(POOL34,0xabdf7b40,256,20,0x3400,0,0)):
        require(machine.read(address,31) == struct.pack('<5I5HB',
            0x6053a7c0,0,backing,stride,0xffff,count,selector,count,width,height,0) and
            machine.read(address+31,32) == bytes(32), 'native selector resource configuration changed')
    require(len(missing_bytes(machine,range(0x6223e688,0x6223e68c),0xa5,'native_selector_format_state')) == 4,
            'native selector reset destination changed')
    reset = native_call(machine,syms,0x602a7ce1,0,0)
    format_bytes = missing_bytes(machine,[FORMAT+o+i for o,n in FORMAT_WRITES for i in range(n)],
        0xa5,'native_selector_format_members')
    node_bytes = missing_bytes(machine,range(NEW_NODE+44,NEW_NODE+46),0xa5,'native_selected_node_sequence')
    require(len(format_bytes) == 79 and len(node_bytes) == 2, 'native selector output extent changed')
    require(machine.read(0x60020068,12) == bytes.fromhex('fccd886879a2fccc00af1c62') and
            all(0x621caf00 <= a < a+n <= 0x62796888 for a,n in ((0x6223dd5c,16),(FORMAT+220,8))),
            'selected cold metadata escaped original BSS')
    # These coordinates are produced by special-associated-node/event42 paths,
    # neither of which has run in this scenario. Extended RMW flags also retain
    # the original first-use BSS condition; no active coordinates are invented.
    admit(machine,'selector_prior_special_coordinates_conditional_BSS',0x6223dd5c,bytes(16))
    admit(machine,'selector_extended_format_flags_conditional_BSS',FORMAT+220,bytes(8))
    admit(machine,'selector_pool_single_contender_hwlock',0x8fe00010,b'\0')
    selected = native_call(machine,syms,0x602a2d43,0,0,dict(a0=ENGINE))
    trace = selected['trace']
    row = next(t['a0'] for t in trace if t['pc'] == 0x602a7d67)
    require(row == 0x60079980 and machine.read(row,4) == struct.pack('<I',18) and
            selected['registers']['a0'] == NEW_NODE and
            machine.read(NEW_NODE+36,8) == struct.pack('<4H',0x5901,1280,960,0x3401) and
            machine.read(NEW_NODE+44,2) == machine.read(0x6223da98,2) == struct.pack('<H',1) and
            machine.read(NEW_NODE+48,2) == machine.read(0x6223e688,2) == struct.pack('<H',18) and
            machine.read(0x6223e318+12,6) == struct.pack('<3H',0,1,1) and
            [t['d0'] for t in trace if t['pc'] == 0x603db792] == [0x5900,0x3400] and
            [t['d0'] for t in trace if t['pc'] == 0x603dba87] == [0x5901,0x3401],
            'native queue selection, resources, ROM record or node fields changed')
    copies = [(96,8,2),(98,16,2),(100,12,2),(102,20,2),(124,32,1),(126,72,2),
              (128,60,12),(148,92,2),(150,96,2),(152,94,2),(154,98,2),
              (182,124,2),(184,128,2),(186,126,2),(188,130,2),(216,28,1),(120,24,2)]
    require(all(machine.read(FORMAT+dest,size) == machine.read(row+source,size) for dest,source,size in copies) and
            machine.read(FORMAT+140,8) == struct.pack('<2I',row+36,row+48) and
            machine.read(FORMAT+228,4) == struct.pack('<I',row+76) and
            machine.read(FORMAT+104,16) == bytes(16) and machine.read(FORMAT+190,1) == b'\0' and
            machine.read(FORMAT+4,4) == struct.pack('<I',original_flags[0]|64) and
            machine.read(FORMAT+8,2) == struct.pack('<H',original_flags[1]|20) and
            machine.read(FORMAT+220,8) == struct.pack('<2I',1,512) and
            machine.read(FORMAT+232,4) == struct.pack('<I',0xdd49c500) and
            machine.read(FORMAT+240,4) == struct.pack('<I',0xabdf7b40),
            'original format lookup/copies, inherited coordinates or resource publication changed')
    for pc in (0x6003138f,0x60031477):
        calls = [(i,t) for i,t in enumerate(trace) if t['pc'] == pc]
        require(len(calls) == 2 and all(next(t['d0'] for t in trace[i+1:] if t['pc'] == call['mdr']) == 0
                                      for i,call in calls), 'native dispatch disable/enable pairing changed')
    require(machine.read(POOL59+20,2) == struct.pack('<H',8) and
            machine.read(POOL34+20,2) == struct.pack('<H',19) and
            machine.read(0x8fe00010,1) == b'\0' and
            machine.regions['task_cell'].data[:4] == task_cell[:4] and
            machine.regions['task_cell'].data[8:] == task_cell[8:] and
            (selected['registers']['psw']&0xf00) == (machine.initial['psw']&0xf00) and
            machine.regions['dispatch_enabled'].data == b'\0' and
            machine.read(sidecar,664) == sealed and machine.read(NEW_CAPTURE,SIZE) == capture and
            machine.read(CAPTURE,SIZE) == old_capture and
            sparse_read(machine,ASSOCIATED+8,4) == struct.pack('<I',NODE),
            'pool ownership, kernel release, sealed snapshot or old backlink changed')
    _,_,_,provider = objects(machine,syms)
    ready_lock(machine,provider)
    empty = machine.clone()
    empty_result = native_call(empty,syms,0x602a2d43,0,0,dict(a0=ENGINE))
    require(empty_result['registers']['a0'] == 0 and
            not any(t['pc'] in (0x603db792,0x6020b9ff) for t in empty_result['trace']) and
            empty.read(sidecar,664) == sealed and empty.read(0x6223e318+12,6) == struct.pack('<3H',0,1,1),
            'second callback did not leave the consumed queue empty and return NULL')
    cases = [stage(name,result) for name,result in (
        ('native_engine_parameter_clear_and_bind',engine_init),('native_pool5900_constructor',initialized[0]),
        ('native_pool3400_constructor',initialized[1]),('native_selector_format_reset',reset),
        ('complete_native_node_selector',selected),('native_empty_queue_selector',empty_result))]
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],engine=str(engine),
        cases=cases,native_instructions=sum(r['completed'] for r in cases),
        maximum_observed_new_stack_depth=max(r['stack_depth_from_call_sp'] for r in cases),
        native_store_capacity_added=379,conditional_BSS_bytes_added=24,single_contender_hwlock_bytes_added=1,
        engine_parameters=dict(address=hex(ENGINE),native_clear_bytes=168,type=7,format_pointer=hex(FORMAT)),
        resource_pools=[dict(selector='0x5900',object=hex(POOL59),handle='0x5901',backing='0xdd49c500',
                            stride=1228800,capacity=9,remaining=8),
                        dict(selector='0x3400',object=hex(POOL34),handle='0x3401',backing='0xabdf7b40',
                            stride=256,capacity=20,remaining=19)],
        format=dict(native_function='0x602a7cf1',property='0x18c4',ROM_row=hex(row),kind=18,
                    original_fields_verified=True,coordinate_sources='explicit cold BSS6223dd5c..6223dd6b'),
        node=dict(address=hex(NEW_NODE),sequence=1,format=18,width=1280,height=960),
        pending_queue_count=0,second_callback_returned_NULL=True,sealed_capture_sidecar_unchanged=True,
        dispatch_disable_enable_pairs=2,hardware_and_kernel_locks_released=True,
        engine_dispatcher_executed=False,selected_event_sent=False,associated_backlink_still_old=True,
        hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['The selector is called at its full original entry with a natively constructed engine parameter object. Generic engine workrecord dispatch and its startup/configuration have not executed.',
                'Pool3400 has an original object address in the8ff00290 local region. The simulator supplies strict writable object storage, not a complete board memory/bus or atomicity model.',
                'Sixteen coordinate bytes from prior special-associated/event42 paths and eight extended-format flags assume original first-use BSS. No active sensor geometry or prior special frame is synthesized.',
                'The8fe00010 hardware semaphore byte uses the inherited single-contender model. Real BSET/BCLR and disable/enable dispatch functions run, but multicore ordering is not established.',
                'The existing request/format state keeps its earlier offline provenance; selector completion does not prove a full new request or physical frame. Both allocated image backing areas remain unmapped.',
                'The queue now transfers its one real node to the selector caller. Event4b delivery, new backlink publication and asynchronous downstream ownership remain pending.',
                'Production kernel startup, lifetime closure, code/RAM residency and backup/recovery remain unresolved.'])
    return report,dict(upstream=contexts,upstream_report=upstream,cases=[dict(context,
        selection_machine=machine,selection_result=selected)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(node_selection_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
