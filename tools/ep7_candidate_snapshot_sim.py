#!/usr/bin/env python3
"""Follow the original geometry request and snapshot producer on a cold scenario.

Request delivery and task scheduling are explicit cut points, not success stubs.
Do not resume the waiting geometry consumer until its producer is established.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import CALLER, STACK, require
from ep7_candidate_state_sim import CALL_SP
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_message_sim import native_call, result_ok, summarize_message
from ep7_candidate_service_state_sim import service_state_context
from ep7_candidate_device_state_sim import admit
from ep7_candidate_geometry_sim import map_initializer_storage
from penf_emulator import Region


REQUEST, SELECTOR, SNAPSHOT = 0x6229faf8, 0x6229fc44, 0x6229fc48


def call_prefix(machine, target, mask, frame, stop, sp=CALL_SP, overrides=None, limit=60000):
    machine.regions['caller'] = Region('caller', CALLER,
        b'\xdd'+struct.pack('<i',target-CALLER)+bytes([mask,frame]), 'rx')
    return machine.run(CALLER, stop, overrides=dict(sp=sp, **(overrides or {})),
        full_trace=True, limit=limit, breakpoints=[0x60061808,0x6040e126])


def stage(name, result, sp=CALL_SP):
    row = summarize_message(name, result, sp)
    if result['status'] != 'returned':
        row['d0_at_stop'] = row.pop('returned_d0')
    row['stop_registers'] = {key:hex(value) for key,value in result['registers'].items()}
    return row


def prepare_empty_property_slots(machine, syms):
    low, high = 0x622a09a4, 0x622a0c18
    # The zero-mode helper is exactly157 consecutive u32 clears. Its one-mode
    # branch only registers148 keys into147 slots; intentional empty slots are
    # not failed registrations and must remain null for the native fallback.
    clear_code = b'\0'+b''.join(b'\xfc\x81'+struct.pack('<I',a) for a in range(low,high,4))+b'\xdf\0\4'
    require(machine.read(0x6020daec,len(clear_code)) == clear_code,
            'original property-cache reset extent or stores changed')
    existing, added = {}, []
    for address in range(low,high,4):
        if any(r.address<=address and address+4<=r.address+len(r.data) for r in machine.regions.values()):
            existing[address] = machine.read(address,4)
        else:
            admit(machine,f'native_null_property_cache_{address:x}',address,b'\xa5'*4)
            added.append(address)
    reset = native_call(machine,syms,0x6020d024,0,4,dict(d0=0),limit=1000)
    require(all(machine.read(a,4) == bytes(4) for a in range(low,high,4)),
            'original cache reset missed a slot')
    registered = native_call(machine,syms,0x6020d024,0,4,dict(d0=1),limit=10000)
    require(all(machine.read(a,4) == value for a,value in existing.items()) and
            all(machine.read(a,4) == bytes(4) for a in added),
            'cache re-registration changed prior pointers or populated a new supposedly null slot')
    return [stage('native_property_cache_reset',reset),stage('native_property_cache_register',registered)], added


def snapshot_context(directory, prefix, engine, without_camera_status=False, without_empty_cache=False,
                     without_ring=False):
    upstream, contexts = service_state_context(directory, prefix, engine)
    rows, outputs = [], []
    for index, context in enumerate(contexts['cases']):
        machine = context['machine']
        syms = contexts['upstream']['upstream']['syms']
        original_capture = machine.read(CAPTURE, SIZE)
        configuration_stack = machine.regions['stack']
        machine.regions['stack'] = replace(configuration_stack, data=b'\xcc'*len(configuration_stack.data))
        require(machine.read(0x6040a266,7) == b'\xdd'+struct.pack('<i',0x60419529-0x6040a266)+bytes([0,4]) and
                machine.read(0x60422143,10) == bytes.fromhex('2c01059000cd673df094') and
                machine.read(0x60419d35,3) == bytes.fromhex('2c8000') and
                machine.read(0x60426173,8) == bytes.fromhex('fccc836f42604208') and
                machine.read(0x6041a528,3) == bytes.fromhex('f9147c') and
                machine.read(0x60020068,12) == bytes.fromhex('fccd886879a2fccc00af1c62'),
                'original request/callback/snapshot/BSS witnesses changed')
        stores, ranges = map_initializer_storage(machine, directory, prefix,
            [(0x60419529,0x604195c3),(0x604053e4,0x604053f6)],
            [(0x6229fb00,0x6229fd78),(0x62299740,0x62299760)],
            [(REQUEST,REQUEST+128),(0x6229fd70,0x6229fd78)], name_prefix='native_snapshot_service')
        initialized = native_call(machine, syms, 0x60419529, 0, 4, limit=1000)
        require(machine.read(0x6229fb88,4) == bytes(4) and
                machine.read(0x6229fb8c,4) == struct.pack('<I',0x6229fb98) and
                machine.read(0x62299748,4) == struct.pack('<I',0x60419ab4) and
                machine.read(0x62299754,4) == struct.pack('<I',0x60419afc),
                'native snapshot service initializer did not publish its pointers/callbacks')
        cases = [stage('native_snapshot_service_initialize', initialized)]
        empty_slots = []
        if not without_empty_cache:
            cache_cases,empty_slots = prepare_empty_property_slots(machine,syms)
            cases.extend(cache_cases)
        if not without_camera_status:
            require(machine.read(0x6054c732,7) == bytes.fromhex('00fc82af6e2362') and
                    machine.read(0x6054c751,6) == bytes.fromhex('fc8352722362') and
                    machine.read(0x6054c79f,6) == bytes.fromhex('fc826e722362'),
                    'camera-status cold reset suffix changed')
            map_initializer_storage(machine,directory,prefix,[(0x6054c732,0x6054c7a5)],
                [(0x62236e00,0x62237300)],name_prefix='native_camera_status')
            status = machine.run(0x6054c732,0x6054c7a5,overrides=dict(sp=CALL_SP),
                full_trace=True,limit=200)
            result_ok(machine,status,0x6054c7a5,CALL_SP)
            require(machine.read(0x62237252,2) == bytes(2),'native camera status is not cold-reset')
            cases.append(stage('native_camera_status_RAM_reset_suffix',status))
        if not without_ring:
            require(machine.read(0x603f3a5b,7) ==
                    b'\xdd'+struct.pack('<i',0x603fe086-0x603f3a5b)+bytes([0x80,4]) and
                    machine.read(0x603fe09d,6) == bytes.fromhex('fcdc925a2962') and
                    machine.read(0x603fe0ab,2) == bytes.fromhex('a510'),
                    'native16-entry geometry history initializer changed')
            map_initializer_storage(machine,directory,prefix,[(0x603fe086,0x603fe0b1)],
                [(0x62295a8c,0x62295ab2)],[(0x62295a92,0x62295ab2)],name_prefix='native_geometry_history')
            history = native_call(machine,syms,0x603fe086,0x80,4,limit=1000)
            require(machine.read(0x62295a8c,5) == bytes.fromhex('0080008000') and
                    machine.read(0x62295a92,32) == struct.pack('<16h',*([-32768]*16)),
                    'native history reset did not set its signed minima')
            cases.append(stage('native_geometry_history_initialize',history))
        # Actual original caller supplies command0501 and null optional context.
        # Stop at the real generic dispatcher before queue operations/logging.
        request = machine.run(0x60422143,0x603f3344,overrides=dict(sp=CALL_SP),
            full_trace=True,limit=60000,breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808,0x6040e126])
        cases.append(stage('native_0501_request_to_dispatch', request))
        require(request['status'] == 'returned' and request['fault'] is None and
                request['registers']['pc'] == 0x603f3344,
                'native request construction did not reach the reviewed dispatcher cut')
        produced = None
        if request['status'] == 'returned':
            source = request['registers']['a0']
            request_bytes = machine.read(source,128)
            require(struct.unpack_from('<I',request_bytes,4)[0] == 0x60426f83 and
                    struct.unpack_from('<H',request_bytes,20)[0] == 0x501,
                    'original request did not select the expected snapshot callback/command')
            # Use an independent lower stack so the original128-byte request
            # remains live while the native request-copy helper reads it.
            copied = call_prefix(machine,0x60419d34,0x20,8,CALLER+7,
                sp=STACK+512,overrides=dict(a0=source),limit=2000)
            result_ok(machine,copied,CALLER+7,STACK+512)
            require(machine.read(REQUEST,128) == request_bytes,
                    'native request handoff did not preserve all128 bytes')
            cases.append(stage('native_request_copy_to_service',copied,STACK+512))
            # Only the first snapshot and two selectors use the reviewed cold
            # BSS-clear precondition. They are not admitted as an active result.
            require(0x621caf00 <= SELECTOR < SNAPSHOT+124 <= 0x62796888,
                    'cold snapshot storage escaped original BSS range')
            admit(machine,'snapshot_selectors_conditional_BSS',SELECTOR,bytes(2))
            admit(machine,'snapshot0_conditional_BSS',SNAPSHOT,bytes(124))
            task = call_prefix(machine,0x60409e3c,0xf0,68,0x60409e74,limit=2000)
            require(task['status'] == 'returned' and task['fault'] is None and
                    task['registers']['a3'] == REQUEST and
                    machine.read(task['registers']['sp']+12,4) == struct.pack('<I',REQUEST+23),
                    'native task prefix did not prepare its request field pointer')
            cases.append(stage('native_geometry_task_prefix_before_receive',task))
            # The receive/log interval is an explicit scheduling cut. The real
            # dispatch slice resets the snapshot and fetches callback/mode from
            # the natively copied request before CALLS through6041a20a.
            produced = machine.resume(dict(task['registers'],pc=0x60409eb6),0x60409ecb,
                full_trace=True,limit=80000,breakpoints=[syms['_ep7_gcc_quarantine'],0x60061808,0x6040e126])
            cases.append(stage('native_snapshot_dispatch_and_producer',produced))
        require(machine.read(CAPTURE,SIZE) == original_capture,'snapshot probe changed partial capture')
        last = produced if produced is not None else request
        if without_camera_status:
            pc, address, width, return_pc = 0x6029246f,0x62237252,2,0x6029bb6c
        elif without_empty_cache:
            pc, address, width, return_pc = 0x60429368,0x622a0bcc,4,0x6005c8df
        elif without_ring:
            pc, address, width, return_pc = 0x603fe0b1,0x62295a90,1,0x603f3a6d
        else:
            pc, address, width, return_pc = 0x60556934,0xa2788ca8,1,0x60427f7d
        require(last['status'] == 'memory_fault' and last['fault'] == dict(
                kind=1,pc=pc,map=0,address=address,size=width,access='read') and
                last['registers']['mdr'] == return_pc,
                'native snapshot frontier changed: '+str(last['fault']))
        constructor_returns = [r for r in last['trace'] if r['pc'] == 0x60427013]
        cache_returns = [r for r in last['trace'] if r['pc'] == 0x60427025]
        constructed = not without_camera_status and not without_empty_cache
        require(len(constructor_returns) == len(cache_returns) == int(constructed),
                'native124-byte constructor/cache-copy return evidence changed')
        snapshot = machine.read(SNAPSHOT,124)
        if constructed:
            require(snapshot == machine.read(0x622a084c,124) and
                    machine.read(0x622a0848,4) == b'\xff'*4 and
                    machine.read(0x6229fb88,4) == struct.pack('<I',SNAPSHOT) and
                    machine.read(SELECTOR,2) == b'\0\2',
                    'native snapshot reset/constructor/cache copy differs')
        rows.append(dict(gpio80_input_bit4=index,cases=cases,
            initializer_direct_stores=len(stores),initializer_mapped_bytes=sum(b-a for a,b in ranges),
            native_cleared_empty_property_slots=[hex(a) for a in empty_slots],
            request_bytes=128,request_source=hex(source),request=request_bytes.hex(),
            request_callback='0x60426f83',request_command='0x0501',
            request_copied_byte_identically=True,
            snapshot_field_constructor_returned=constructed,
            snapshot_field_bytes=124,snapshot_fields=snapshot.hex(),
            snapshot_cache_copy_byte_identical=constructed,
            snapshot_wrapper_returned=False,format_module_readiness_established=False,
            request_produced=request['status']=='returned',snapshot_producer_completed=bool(
                produced is not None and produced['status']=='returned'),
            frontier=dict(status=last['status'],fault=last['fault'],
                pc=hex(last['registers']['pc']),native_return_pc=hex(last['registers']['mdr'])),
            capture_unchanged=True,geometry_consumer_resumed=False))
        outputs.append(dict(machine=machine,configuration_result=context['configuration_result'],
            configuration_stack=configuration_stack,request_result=request,producer_result=produced))
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],
        engine=str(engine),cases=rows,native_camera_status_reset=not without_camera_status,
        native_empty_cache_slots_initialized=not without_empty_cache,
        native_history_initialized=not without_ring,
        native_instructions=sum(c['completed'] for row in rows for c in row['cases']),
        maximum_observed_new_stack_depth=max(c['stack_depth_from_call_sp'] for row in rows for c in row['cases']),
        population_resumed=False,hash_checks_performed=False,
        native_api_success_stubs=False,firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['Original service initialization and request construction run independently on a cold scenario; the complete service/task lifecycle is not established.',
            'If reached, native request copy and task-prefix dispatch use an explicit handoff across unexecuted queue receive/logging; no scheduler or queue acceptance is claimed.',
            'Only first-snapshot124 bytes and two selector bytes assume original BSS clear success. Native production must precede use as active geometry.',
            'Optional6054c732..6054c7a5 is the original camera-status RAM reset suffix only; its enclosing initialization and following hardware helpers remain unexecuted.',
            'Optional property-cache reset/re-registration calls the original zero/one modes independently, preserving every prior registered pointer and supplying only the originally null slots.',
            'The124-byte field constructor and its cache copy can finish before the enclosing producer callback: format-module readiness, service-output construction and wrapper completion remain unestablished.',
            'The16-entry history initializer executes independently before its first original history update; the complete task startup order is not proven.',
            'Waiting geometry configuration, capture population and worker chain are not resumed by this probe.'])
    return report,dict(upstream=contexts,cases=outputs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    parser.add_argument('--without-camera-status',action='store_true')
    parser.add_argument('--without-empty-cache',action='store_true')
    parser.add_argument('--without-ring',action='store_true')
    args = parser.parse_args()
    print(json.dumps(snapshot_context(args.candidate,args.tool_prefix,args.engine,args.without_camera_status,
                                     args.without_empty_cache,args.without_ring)[0],indent=2))
