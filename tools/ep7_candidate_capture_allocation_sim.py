#!/usr/bin/env python3
"""Allocate a new native capture ID and buffer through the patched node factory.

The selected native registry reset preserves ID1. Complete admission and capture
allocation return ID2, then node construction stops at the next unprovided pool.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import require
from ep7_candidate_state_sim import CALL_SP, objects, ready_lock
from ep7_candidate_capture_sim import CAPTURE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_publish_sim import SEM_TABLE
from ep7_candidate_message_sim import result_ok
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_device_state_sim import admit
from ep7_candidate_format_record_sim import missing_bytes
from ep7_candidate_color_property_sim import color_property_context


CAPTURE_POOL = 0xa269d980
NEW_CAPTURE = 0xaf6037c0
REGISTRY2 = 0x6223d1a8
SEM_SOURCE, SEM_OBJECT = 0x60039b2c,0x6219a390


def capture_allocation_context(directory,prefix,engine):
    upstream,contexts = color_property_context(directory,prefix,engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    syms = base['syms']
    context = contexts['cases'][0]
    machine = context['color_machine'].clone()
    capture = machine.read(CAPTURE,SIZE)
    sidecar = syms['_ep7_controller_sidecar_unresolved']
    old_sidecar = machine.read(sidecar,104)
    old_registry = bytes(machine.read(0x6223d190+i,1)[0] for i in range(24))
    machine.regions['stack'] = replace(machine.regions['stack'],data=b'\xcc'*len(machine.regions['stack'].data))
    require(machine.read(0x60040a26,2) == struct.pack('<H',0x19) and
            machine.read(SEM_SOURCE,16) == struct.pack('<4I',0x19,0,1,1) and
            machine.read(SEM_TABLE+24*4,4) == struct.pack('<I',SEM_OBJECT) and
            machine.read(0x6053a258+21*8,8) == struct.pack('<2I',0x1500,CAPTURE_POOL) and
            machine.read(0x602a4480,5) == bytes.fromhex('dc663de2ff') and
            machine.read(0x603daf36,39) == bytes.fromhex(
                '80194204004208420c42104214fcdc80d969a2fcccc03760affccd00a40000250015cdb62aa020'),
            'original semaphore19, capture pool descriptor/caller or patched node entry changed')
    capacity = missing_bytes(machine,list(range(SEM_OBJECT,SEM_OBJECT+28))+
        [address for low,high in ((CAPTURE_POOL,CAPTURE_POOL+63),(CAPTURE_POOL+64,CAPTURE_POOL+80),
                                 (CAPTURE_POOL+88,CAPTURE_POOL+476)) for address in range(low,high)],
        0xa5,'native_capture_allocation_dependencies')
    require(len(capacity) == 495, 'selected semaphore/pool constructor store extent changed')
    semaphore = machine.run(0x60032a72,0x60032aad,
        overrides=dict(sp=CALL_SP,d2=SEM_TABLE,a2=SEM_SOURCE),full_trace=True,limit=1000)
    result_ok(machine,semaphore,0x60032aad,CALL_SP)
    initialized = machine.run(0x603daf36,0x603daf5d,overrides=dict(sp=CALL_SP),
        full_trace=True,limit=3000,breakpoints=[0x60061808,0x6040e126])
    result_ok(machine,initialized,0x603daf5d,CALL_SP)
    require(machine.read(CAPTURE_POOL,4) == struct.pack('<I',0x6053a868) and
            machine.read(CAPTURE_POOL+8,18) == struct.pack('<3I3H',NEW_CAPTURE,41984,0,25,0x1500,25) and
            machine.read(CAPTURE_POOL+64,16) == bytes(16),
            'native25-slot capture pool initialization changed')
    # The old single-row fixture's synthetic after-canary occupies real row2.
    # Remove only that guard; map ten overlapped actual store bytes and two new
    # row bytes. Six old guard bytes become unmapped holes, not writable zeros.
    guard = machine.regions.pop('capture_registry_id1_after')
    require(guard.address == REGISTRY2 and guard.data == b'\x5a'*16 and guard.permissions == 'r',
            'the single-row fixture guard no longer overlaps the selected native row2')
    registry_bytes = missing_bytes(machine,[REGISTRY2+offset+i for offset,size in ((0,4),(10,8))
                                           for i in range(size)],0xa5,'native_capture_registry_id2')
    require(len(registry_bytes) == 12, 'actual ID2 registry store extent changed')
    reset = machine.run(0x6029b4a9,0x6029b4b0,
        overrides=dict(sp=CALL_SP,d0=2,a0=0x6223d178),full_trace=True,limit=50)
    result_ok(machine,reset,0x6029b4b0,CALL_SP)
    require(machine.read(REGISTRY2,2) == bytes(2), 'selected native ID2 flag reset changed')
    # The complete allocator writes only this halfword in its real newly
    # allocated payload. Its41984-byte slot is not declared initialized.
    admit(machine,'native_capture2_initial_halfword',NEW_CAPTURE+27078,b'\xa5\xa5')
    # Specialized auxiliary pool0 leaves per-slot references to startup BSS.
    # Its already-owned first reference is preserved; only the unused second
    # reference receives this explicit first-allocation condition.
    require(machine.read(0x60020068,12) == bytes.fromhex('fccd886879a2fccc00af1c62') and
            0x621caf00 <= 0xa269ce45-0x40000000 < 0x62796888 and
            machine.read(0xa269ce44,1) == b'\x01', 'auxiliary slot reference precondition changed')
    admit(machine,'aux_pool_second_ref_conditional_BSS',0xa269ce45,b'\0')
    # Execute the actual candidate bridge. Stop after the complete stock
    # admission and capture allocator returned, before the next resource pool.
    allocated = machine.run(0x602a4480,0x602a3151,overrides=dict(sp=CALL_SP),full_trace=True,limit=20000,
        breakpoints=[0x60061808,0x6040e126,syms['_ep7_gcc_quarantine']])
    result_ok(machine,allocated,0x602a3151,CALL_SP-56)
    trace = allocated['trace']
    available = []
    for index,row in enumerate(trace):
        if row['pc'] == 0x603dbd17:
            returned = next(t for t in trace[index+1:] if t['pc'] == row['mdr'])
            available.append(dict(selector=hex(row['d0']),returned=returned['d0']))
    require(available == [dict(selector='0x0',returned=10),dict(selector='0x100',returned=19),
                          dict(selector='0x1500',returned=25)] and
            allocated['registers']['d0'] == allocated['registers']['d2'] == 2 and
            machine.read(REGISTRY2,4) == struct.pack('<2H',5,2) and
            machine.read(REGISTRY2+10,8) == struct.pack('<HIH',0x102,NEW_CAPTURE,0x1501) and
            machine.read(NEW_CAPTURE+27078,2) == bytes(2) and
            [int.from_bytes(machine.read(address+20,2),'little') for address in
                (0xa269cdd4,0xa269cf10,CAPTURE_POOL)] == [18,18,24] and
            machine.read(0xa269ce14,24) == struct.pack('<6I',3,0,0,0,0,0) and
            machine.read(0xa269ce44,1) == machine.read(0xa269ce45,1) == b'\x01' and
            machine.read(CAPTURE_POOL+64,4) == struct.pack('<I',1) and
            machine.read(CAPTURE_POOL+88,1) == b'\x01',
            'native admission, new capture allocation or per-pool ownership changed')
    require([t['d0'] for t in trace if t['pc'] == 0x603db792] == [0,0x100,0x1500] and
            all(sum(t['pc'] == pc for t in trace) == 1 for pc in
                (0x602a3116,0x6029ba1e,0x6029b4e7,0x6029b512,0x6029be82,0x6029bdec)) and
            not any(t['pc'] in (0x60022700,syms['_ep7cn_fresh']) for t in trace) and
            machine.read(SEM_OBJECT+24,4) == struct.pack('<I',1) and
            machine.read(0xa26a0808,4) == bytes(4) and
            machine.read(CAPTURE,SIZE) == capture and machine.read(sidecar,104) == old_sidecar and
            bytes(machine.read(0x6223d190+i,1)[0] for i in range(24)) == old_registry,
            'actual factory prefix, lock release or preservation of old ID1 changed')
    _,_,_,provider = objects(machine,syms)
    ready_lock(machine,provider)
    following = machine.clone()
    frontier = following.resume(allocated['registers'],0x602a4485,full_trace=True,limit=10000,
        breakpoints=[0x60061808,0x6040e126,syms['_ep7_gcc_quarantine']])
    require(frontier['status'] == 'memory_fault' and frontier['fault'] == dict(
        kind=1,pc=0x603dbd40,map=0,address=0xa269e9c4,size=4,access='read') and
        frontier['registers']['d3'] == 0x3200 and frontier['registers']['mdr'] == 0x6029bf8a and
        following.read(SEM_OBJECT+24,4) == bytes(4) and following.read(sidecar,104) == old_sidecar,
        'next pool3200 frontier or still-held factory semaphore changed')
    rows = [stage(name,result) for name,result in (
        ('native_static_semaphore19_initialize_iteration',semaphore),
        ('native_capture_pool1500_constructor_slice',initialized),('native_unused_registry2_flag_reset',reset),
        ('actual_candidate_node_factory_through_capture_allocation',allocated),
        ('node_factory_additional_resource_frontier',frontier))]
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],engine=str(engine),
        cases=rows,native_instructions=sum(r['completed'] for r in rows),
        maximum_observed_new_stack_depth=max(r['stack_depth_from_call_sp'] for r in rows),
        native_store_capacity_added=509,newly_unmapped_store_bytes_admitted=499,
        conditional_BSS_bytes_added=1,
        synthetic_guard_correction=dict(address=hex(REGISTRY2),removed_bytes=16,
            actual_store_bytes_reclassified=10,old_guard_bytes_now_unmapped=6,firmware_boundary_changed=False),
        capture_pool=dict(address=hex(CAPTURE_POOL),selector='0x1500',backing=hex(NEW_CAPTURE),
            stride=41984,slots=25,remaining_after=24,new_handle='0x1501',payload_bytes_mapped=2),
        allocation=dict(actual_patched_call_site='0x602a4480',complete_admission=True,availability=available,
            complete_registry_allocator=True,new_id=2,registry=hex(REGISTRY2),flags=5,
            auxiliary_handles=['0x2','0x102'],capture_pointer=hex(NEW_CAPTURE),
            real_return_to_factory='0x602a314a',checkpoint='0x602a3151',checkpoint_SP=hex(CALL_SP-56),
            node_heap_allocation_entered=False,candidate_fresh_registration_entered=False),
        old_ID1_capture_sidecar_unchanged=True,allocation_checkpoint_locks_released=True,
        frontier=dict(status=frontier['status'],fault=frontier['fault'],selector='0x3200',
            object='0xa269e9c4',semaphore19_count=0,logical_ownership_retained_in_paused_simulation=True),
        full_node_factory_completed=False,new_COLOR_population_completed=False,
        hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['Only the original selected semaphore19 row and pool1500 constructor slice execute. Whole static kernel/pool startup and inherited single-contender hardware assumptions remain unqualified.',
                'The single-row test canary overlapped real registry row2. Only its16 synthetic bytes are removed; ten become actual native stores, six return to unmapped holes, and old ID1 remains unchanged.',
                'The selected unused ID2 flag is reset by its real native store. The full26-entry registry reset and production temporal ownership of that reset are not established.',
                'One auxiliary second-slot reference byte assumes original cold BSS. The existing first reference and all allocated handles are preserved; no complete multi-owner allocator lifetime is claimed.',
                'The actual patched factory enters complete admission and registry allocation, returning real ID2 and a newly claimed capture buffer. Only its original27078 halfword is initialized; the remaining payload stays unmapped.',
                'Node heap allocation, associated-object allocation and candidate fresh registration have not run. A separate continuation stops inside pool3200 lookup with semaphore19 still held in that paused simulator state.',
                'Full COLOR population, input provenance, asynchronous worker/lifetime, production kernel IDs, code/RAM residency and backup/recovery remain unresolved.'])
    return report,dict(upstream=contexts,upstream_report=upstream,cases=[dict(context,
        allocation_machine=machine,allocation_result=allocated,
        node_factory_machine=following,node_factory_result=frontier)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(capture_allocation_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
