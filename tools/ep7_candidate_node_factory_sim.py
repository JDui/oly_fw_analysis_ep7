#!/usr/bin/env python3
"""Complete the actual node factory after native pool/FIFO/associated setup.

The selected original associated reset revokes the inherited old registration.
Fresh CPU0 small-heap metadata is an explicit cold-BSS condition, not a heap stub.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import require
from ep7_candidate_state_sim import CALL_SP, objects, ready_lock
from ep7_candidate_capture_sim import CAPTURE, ASSOCIATED, POOL, NODE
from ep7_candidate_capture_template_sim import SIZE
from ep7_candidate_message_sim import result_ok
from ep7_candidate_snapshot_sim import stage
from ep7_candidate_device_state_sim import admit
from ep7_candidate_format_record_sim import missing_bytes
from ep7_candidate_capture_allocation_sim import capture_allocation_context, NEW_CAPTURE, REGISTRY2, SEM_OBJECT
from ep7_ram_ownership import CACHED, STRIDES


RESOURCE_POOL = 0xa269e9c4
NEW_NODE = 0x61b21fc0


def sparse_read(machine,address,size):
    return bytes(machine.read(address+i,1)[0] for i in range(size))


def open_native_fields(machine,name,fields):
    """Preserve existing bytes; only reviewed store spans become writable."""
    previous = machine.regions.pop(name)
    for low,high,permissions in fields:
        admit(machine,f'{name}_native_{low}',previous.address+low,previous.data[low:high],permissions)
    return previous


def node_factory_context(directory,prefix,engine):
    upstream,contexts = capture_allocation_context(directory,prefix,engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    syms = base['syms']
    context = contexts['cases'][0]
    machine = context['allocation_machine'].clone()
    paused_stack = machine.regions['stack']
    machine.regions['stack'] = replace(paused_stack,data=b'\xcc'*len(paused_stack.data))
    sidecar = syms['_ep7_controller_sidecar_unresolved']
    before = machine.read(sidecar,664)
    old_capture,old_registry = machine.read(CAPTURE,SIZE),sparse_read(machine,0x6223d190,24)
    witnesses = [
        (0x603db2a7,'80044204004208420c42104214fcdcc4e969a2fccc406386aefccd001e2f00250032cd0f1fa00c'),
        (0x6029b4b6,'fcdcecd32362fc80e8d323622cd2004204fcdd00d4236280048502dd7804f7ff8004'),
        (0x6029c66f,'fcdcdce02362fc80d8e02362fccc60e1236242042c2e044208fcddfce0236280198510dcfabae2ff')]
    require(all(machine.read(address,len(bytes.fromhex(code))) == bytes.fromhex(code)
                for address,code in witnesses) and
            machine.read(0x6053a258+50*8,8) == struct.pack('<2I',0x3200,RESOURCE_POOL),
            'native resource/associated constructor callers or actual reset bridge changed')
    resource_capacity = missing_bytes(machine,list(range(RESOURCE_POOL,RESOURCE_POOL+63))+
        list(range(0x6223d3e8,0x6223d3fe))+list(range(0x6223d400,0x6223d402))+
        list(range(REGISTRY2+4,REGISTRY2+6)),0xa5,'native_node_resource')
    require(len(resource_capacity) == 89, 'resource32 constructor/store extent changed')
    pool_init = machine.run(0x603db2a7,0x603db2ce,overrides=dict(sp=CALL_SP),full_trace=True,limit=2000)
    result_ok(machine,pool_init,0x603db2ce,CALL_SP)
    fifo_init = machine.run(0x6029b4b6,0x6029b4d8,overrides=dict(sp=CALL_SP),full_trace=True,limit=1000)
    result_ok(machine,fifo_init,0x6029b4d8,CALL_SP)
    require(machine.read(RESOURCE_POOL,31) == struct.pack('<5I5HB',
                0x6053a7c0,0,0xae866340,3087872,0,4,0x3200,4,0,0,0) and
            machine.read(RESOURCE_POOL+31,32) == bytes(32) and
            machine.read(0x6223d3e8,22) == struct.pack('<IIHHIHHH',
                0x6223d3ec,210,4,2,0x6223d400,0,0,0), 'resource pool/FIFO native layout changed')
    pool = next(r for r in CACHED if r[0:2] == (0,0))
    require(pool[2] == NEW_NODE and pool[3] == 3040 and STRIDES[0] == 192 and
            machine.read(0x8050,4) == bytes(4) and
            machine.read(pool[4],6) == b'\xfc\xdf'+struct.pack('<I',NEW_NODE) and
            machine.read(pool[5],3) == b'\x2c'+struct.pack('<H',3040) and
            machine.read(pool[6],6) == b'\xfc\xdc'+struct.pack('<I',pool[7]) and
            machine.read(0x60026e34,4) == struct.pack('<I',STRIDES[0]) and
            machine.read(0x6002004d,12) == bytes.fromhex('fccd34c90362fccc00810362') and
            all(0x62038100 <= a < a+4 <= 0x6203c934 for a in (0x62038118,pool[7])),
            'reviewed CPU0 small heap/cold BSS provenance changed')
    admit(machine,'cpu0_small_next_conditional_BSS',0x62038118,bytes(4))
    admit(machine,'cpu0_small_bitmap_conditional_BSS',pool[7],bytes(4))
    node_capacity = missing_bytes(machine,[NEW_NODE+offset+i for offset,size in
        ((0,12),(36,8),(46,1),(48,2)) for i in range(size)],0xa5,'native_node_members')
    require(len(node_capacity) == 23, 'native56-byte node store extent changed')
    breakpoints = [0x60061808,0x6040e126,syms['_ep7_gcc_quarantine']]
    # Preserve the empty-FIFO rejection: opening the old fixture does not make
    # its existing active associated slot available to the allocator.
    rejected = machine.clone()
    rejected.regions['stack'] = paused_stack
    guard = rejected.resume(context['allocation_result']['registers'],0x602a4485,
        full_trace=True,limit=20000,breakpoints=breakpoints)
    require(guard['status'] == 'breakpoint' and guard['registers']['pc'] == 0x60061808 and
            guard['registers']['d0'] == 0x25002701 and guard['registers']['mdr'] == 0x60297312 and
            rejected.read(0x62038118,4) == rejected.read(pool[7],4) == struct.pack('<I',1) and
            rejected.read(sidecar,664) == before and
            not any(t['pc'] == syms['_ep7cn_fresh'] for t in guard['trace']),
            'inherited empty associated FIFO no longer rejects before fresh registration')
    old_pool = open_native_fields(machine,'associated_pool',
        ((0,26,'rw'),(26,28,'r'),(28,30,'rw'),(30,32,'r'),(32,36,'rw')))
    old_slot = open_native_fields(machine,'associated',
        ((0,8,'rw'),(8,10,'r'),(10,11,'rw'),(11,16,'r')))
    require(old_pool.address == POOL-4 and len(old_pool.data) == 36 and
            old_slot.address == ASSOCIATED-4 and len(old_slot.data) == 16,
            'inherited associated fixture extents changed')
    # These synthetic canaries overlap real free-list entries and slot1.
    for name,address in (('associated_pool_after',0x6223e0fc),
                         ('associated_before',0x6223e150),('associated_after',0x6223e170)):
        guard_region = machine.regions.pop(name)
        require(guard_region.address == address and guard_region.data == b'\x5a'*16 and
                guard_region.permissions == 'r', 'associated fixture guard changed')
    associated_capacity = missing_bytes(machine,list(range(0x6223e0fc,0x6223e160))+
        [0x6223e160+16*i+j for i in range(25) for j in range(4)],0xa5,'native_associated_fifo_refs')
    require(len(associated_capacity) == 196, 'native associated FIFO/reference extent changed')
    initialized = machine.run(0x6029c66f,0x6029c697,overrides=dict(sp=CALL_SP),
        full_trace=True,limit=20000,breakpoints=breakpoints)
    result_ok(machine,initialized,0x6029c697,CALL_SP)
    after_reset = machine.read(sidecar,664)
    require(after_reset == before[:24]+bytes(640) and
            sum(t['pc'] == syms['_ep7cn_associated_reset'] for t in initialized['trace']) == 1 and
            sum(t['pc'] == 0x602972aa for t in initialized['trace']) == 1 and
            machine.read(0x6223e0fc,100) == struct.pack('<25I',*[0x6223e160+16*i for i in range(25)]) and
            all(machine.read(0x6223e160+16*i,4) == bytes(4) for i in range(25)) and
            sparse_read(machine,POOL+16,6) == struct.pack('<3H',25,0,0) and
            sparse_read(machine,ASSOCIATED,12) == old_slot.data[4:],
            'actual reset failed to revoke first, retain serial or rebuild original free list')
    require(next(i for i,t in enumerate(initialized['trace']) if t['pc'] == syms['_ep7cn_associated_reset']) <
            next(i for i,t in enumerate(initialized['trace']) if t['pc'] == 0x602972aa),
            'sidecar retirement no longer precedes native pool reset')
    machine.regions['stack'] = paused_stack
    completed = machine.resume(context['allocation_result']['registers'],0x602a4485,
        full_trace=True,limit=20000,breakpoints=breakpoints)
    result_ok(machine,completed,0x602a4485,CALL_SP)
    trace = completed['trace']
    header = bytearray(before[:24])
    serial = struct.unpack_from('<Q',before,16)[0]+1
    struct.pack_into('<Q',header,16,serial)
    entry = bytearray(80)
    struct.pack_into('<IIQQ',entry,0,NEW_NODE,ASSOCIATED,serial,struct.unpack_from('<Q',before,8)[0])
    struct.pack_into('<II',entry,36,NEW_CAPTURE,2)
    require(machine.read(sidecar,664) == header+entry+bytes(560) and serial == 2 and
            completed['registers']['a0'] == NEW_NODE and
            machine.read(NEW_NODE,12) == struct.pack('<3I',2,0,ASSOCIATED) and
            machine.read(NEW_NODE+36,8) == bytes(8) and machine.read(NEW_NODE+46,1) == b'\0' and
            machine.read(NEW_NODE+48,2) == bytes(2) and
            machine.read(0x62038118,4) == machine.read(pool[7],4) == struct.pack('<I',1) and
            sparse_read(machine,ASSOCIATED-4,16) == struct.pack('<4I',1,2,0,NODE) and
            sparse_read(machine,POOL+16,6) == struct.pack('<3H',24,0,1) and
            machine.read(REGISTRY2,2) == struct.pack('<H',7) and
            machine.read(REGISTRY2+4,2) == machine.read(0x6223d400,2) == struct.pack('<H',0x3201) and
            machine.read(RESOURCE_POOL+20,2) == struct.pack('<H',3) and
            machine.read(0x6223d3ec+12,6) == struct.pack('<3H',1,1,0),
            'native node/associated allocation, resource ownership or fresh token changed')
    requests = [t for t in trace if t['pc'] == 0x60022700]
    returned_heap = [t for t in trace if t['pc'] == 0x6002272f]
    require(len(requests) == len(returned_heap) == 1 and requests[0]['d0'] == 56 and
            returned_heap[0]['a0'] == NEW_NODE and
            all(sum(t['pc'] == pc for t in trace) == 1 for pc in
                (0x602972e3,syms['_ep7cn_fresh'],syms['_ep7c_register_fresh_capture'])) and
            machine.read(SEM_OBJECT+24,4) == struct.pack('<I',1) and
            machine.read(0xa26a0808,4) == bytes(4) and
            machine.read(CAPTURE,SIZE) == old_capture and sparse_read(machine,0x6223d190,24) == old_registry,
            'native allocator call, lock release or old capture/registry preservation changed')
    _,_,_,provider = objects(machine,syms)
    ready_lock(machine,provider)
    cases = [stage(name,result) for name,result in (
        ('native_resource32_constructor_slice',pool_init),('native_resource_FIFO_constructor_slice',fifo_init),
        ('inherited_empty_associated_FIFO_rejection',guard),
        ('actual_associated_reset_bridge_and_native_initializer',initialized),
        ('remaining_actual_node_factory_and_fresh_registration',completed))]
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],engine=str(engine),
        cases=cases,native_instructions=sum(r['completed'] for r in cases),
        maximum_observed_new_stack_depth=max(r['stack_depth_from_call_sp'] for r in cases),
        store_capacity_added=308,previously_unmapped_store_bytes=272,guard_bytes_reclassified=36,
        existing_readonly_store_bytes_opened=41,conditional_BSS_bytes_added=8,
        synthetic_guard_correction=dict(removed_bytes=48,real_store_bytes=36,now_unmapped_bytes=12),
        resource=dict(selector='0x3200',object=hex(RESOURCE_POOL),backing='0xae866340',stride=3087872,
            capacity=4,remaining=3,handle='0x3201',FIFO_capacity=4,FIFO_element_bytes=2,FIFO_count=1),
        heap=dict(allocator='0x60022700',request_bytes=56,domain=0,slot_class=0,slot_index=0,
            address=hex(NEW_NODE),payload_capacity=128,stride=192,capacity=3040,
            counter='0x62038118',bitmap=hex(pool[7]),counter_after=1,bitmap_after=1,mapped_node_bytes=23),
        associated=dict(pool=hex(POOL),payload=hex(ASSOCIATED),full_initializer_executed=True,
            reset_observer_before_initializer=True,old_registration_revoked=True,serial_preserved_by_reset=True,
            free_count_before=25,free_count_after=24,refcount_after=1,
            stale_backlink_preserved=hex(NODE),backlink_publication_executed=False),
        complete_actual_factory_return=True,return_PC='0x602a4485',return_SP=hex(CALL_SP),
        new_capture_ID=2,new_capture=hex(NEW_CAPTURE),new_token=serial,new_sidecar_flags=[0,0,0,0,0],
        old_capture_and_registry_unchanged=True,logical_and_kernel_locks_released=True,
        new_COLOR_population_completed=False,hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['Selected original pool3200/FIFO setup and complete associated initializer run as independent setup with the paused caller stack restored. Whole startup ordering and live reset legality remain unproved.',
                'The original empty associated fixture is retained as a negative branch: native diagnosis25002701 occurs after heap allocation, before fresh registration. That rejected branch is not reused.',
                'Eight CPU0 allocator metadata bytes assume original cold BSS and first small-slot allocation. Other slots, recycling paths, spare payload and64-byte slot guard remain unmapped.',
                'Actual associated reset retires old sidecar entries before clearing25 refcounts/rebuilding FIFO; it retains serial and native old payload. The old backlink still references the old node until its real publisher executes.',
                'Fresh registration returns token2, with no sampling or seal. This establishes native allocation in the explicit scenario, not asynchronous lifecycle exclusion or active camera operation.',
                'Input provenance, production kernel startup, code/RAM residency and backup/recovery remain unresolved.'])
    return report,dict(upstream=contexts,upstream_report=upstream,cases=[dict(context,
        node_machine=machine,node_result=completed,associated_reset_result=initialized)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(node_factory_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
