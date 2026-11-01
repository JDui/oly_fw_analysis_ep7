#!/usr/bin/env python3
"""Allocate native auxiliary resources and complete the request-format producer.

This independent preparation probe retains explicit cold metadata and hardware
lock inputs. It does not establish the enclosing fresh capture generation.
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
from ep7_candidate_format_record_sim import missing_bytes
from ep7_candidate_request_constructor_sim import request_constructor_context, OBJECT, PACKET
from ep7_candidate_request_format_guard_sim import FORMAT, FORMAT_MEMBERS


POOLS = (0xa269cdd4,0xa269cf10,0xa269d0ec)
LOCK_BITS = 0xa26a0808


def request_resources_context(directory,prefix,engine):
    upstream,contexts = request_constructor_context(directory,prefix,engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    context = contexts['cases'][0]
    original = context['postpopulation_machine']
    machine = context['request_machine'].clone()
    capture = machine.read(CAPTURE,SIZE)
    machine.regions['stack'] = replace(machine.regions['stack'],data=b'\xcc'*len(machine.regions['stack'].data))
    # Exact constructor write extents, including actual fill loops. Unwritten
    # alignment gaps and resource backing payloads remain unmapped.
    spans = [(POOLS[0],POOLS[0]+63),(POOLS[0]+88,POOLS[0]+112),(POOLS[0]+304,POOLS[0]+314)]
    for address in POOLS[1:]:
        spans.extend([(address,address+63),(address+64,address+80),(address+88,address+476)])
    gaps = missing_bytes(machine,[a for low,high in spans for a in range(low,high)],0xa5,'native_aux_pools')
    require(len(gaps) == 1031 and machine.read(0x6053a258,24) ==
        struct.pack('<6I',0,POOLS[0],0x100,POOLS[1],0x200,POOLS[2]),
        'native auxiliary pool descriptors or constructor write extents changed')
    initialized = machine.run(0x603dac40,0x603dacc8,overrides=dict(sp=CALL_SP),full_trace=True,limit=10000,
        breakpoints=[0x60061808,0x6040e126])
    result_ok(machine,initialized,0x603dacc8,CALL_SP-36)
    expected = [(0x6053a8a0,0xb0000000,32481280,1,20,0,20),
                (0x6053a868,0xaf42db40,53760,0,20,0x100,20),
                (0x6053a868,0xa43a3ec0,0,0,7,0x200,7)]
    headers = []
    for address,(vtable,backing,stride,lock,count,selector,capacity) in zip(POOLS,expected):
        require(machine.read(address,4) == struct.pack('<I',vtable) and
            machine.read(address+8,18) == struct.pack('<3I3H',backing,stride,lock,count,selector,capacity),
            'original native auxiliary pool configuration changed')
        headers.append(dict(address=hex(address),vtable=hex(vtable),backing=hex(backing),
            stride=stride,lock=lock,capacity=capacity,selector=hex(selector)))
    admit(machine,'native_aux_pool_lock_bits',LOCK_BITS,b'\xa5'*4)
    reset = native_call(machine,base['syms'],0x603dcfe2,0x80,4,limit=2000)
    require(machine.read(LOCK_BITS,4) == bytes(4), 'native pool logical-lock reset changed')
    # The specialized pool0 constructor leaves its allocation bitmap and
    # reference counters to startup BSS. Only the24 bitmap bytes and first
    # counter used by this allocation are admitted, plus the debug gate.
    conditional = [(0xa269cdc8,2,'r'),(POOLS[0]+64,24,'rw'),(POOLS[0]+112,1,'rw')]
    require(machine.read(0x60020068,12) == bytes.fromhex('fccd886879a2fccc00af1c62') and
            all(0x621caf00 <= address-0x40000000 and address-0x40000000+size <= 0x62796888
                for address,size,_ in conditional), 'auxiliary cold metadata is outside original BSS')
    for address,size,permissions in conditional:
        admit(machine,f'aux_pool_cold_metadata_{address:x}',address,bytes(size),permissions)
    # One idle hardware semaphore byte under a single-contender model. Actual
    # original BSET/BCLR execute; this is not hardware atomicity/ordering proof.
    admit(machine,'aux_pool_single_contender_hwlock',0x8fe00018,bytes(1))
    registry = machine.regions.pop('capture_registry_before_status')
    require(registry.address == 0x6223d190 and len(registry.data) == 18 and
            registry.data[:2] == struct.pack('<H',4), 'capture-only registry input changed')
    for name,offset,size,permissions in [('native_aux_flag_handle',0,4,'rw'),
        ('before_aux_second_handle',4,6,'r'),('native_aux_second_handle',10,2,'rw'),
        ('capture_owned_pointer',12,6,'r')]:
        region = replace(registry,name=name,address=registry.address+offset,data=registry.data[offset:offset+size],
            permissions=permissions,capture=permissions=='rw')
        machine.regions[name] = region
    # Original mode0 helper arguments from6029b60d/6029b642. Execute the whole
    # auxiliary allocator; the enclosing registry scan/capture allocation and
    # their publication order are not substituted by this independent branch.
    allocated = native_call(machine,base['syms'],0x6029be82,0xe0,20,
        dict(d0=1,d1=0,a0=0x100),limit=30000)
    require(allocated['registers']['d0'] == 0 and
            machine.read(registry.address,4) == struct.pack('<2H',5,1) and
            machine.read(registry.address+10,2) == struct.pack('<H',0x101) and
            machine.read(POOLS[0]+64,24) == struct.pack('<6I',1,0,0,0,0,0) and
            machine.read(POOLS[0]+112,1) == b'\x01' and
            machine.read(POOLS[1]+64,4) == struct.pack('<I',1) and
            machine.read(POOLS[1]+88,1) == b'\x01' and
            [struct.unpack('<H',machine.read(p+20,2))[0] for p in POOLS] == [19,19,7] and
            machine.read(LOCK_BITS,4) == bytes(4) and machine.read(0x8fe00018,1) == bytes(1),
            'native resource handles, ownership flags, counters or lock release changed')
    entries = [(t['pc'],t['d0']) for t in allocated['trace']]
    require([v for pc,v in entries if pc == 0x603db792] == [0,0x100] and
            all(sum(pc == target for pc,_ in entries) == count for target,count in
                [(0x603dd261,2),(0x60059fcf,2),(0x60059fd9,2),(0x6006a922,2),(0x6006a96b,2),(0x6029befb,1)]) and
            not any(pc in (0x60061808,0x6040e126,0x600313ef) for pc,_ in entries),
            'native allocation entered a diagnostic, wait or unexpected lock path')
    selected = native_call(machine,base['syms'],0x602a65bd,0,0,dict(a0=OBJECT,a1=PACKET),limit=2000)
    format_gaps = missing_bytes(machine,[FORMAT+offset+i for offset,size in FORMAT_MEMBERS for i in range(size)],
        0xa5,'native_completed_request_format')
    require(len(format_gaps) == 84 and selected['registers']['d0'] == 0x10000,
            'native request-format selection or output extent changed')
    stack = machine.regions['stack']
    data = bytearray(stack.data)
    struct.pack_into('<I',data,CALL_SP+8-stack.address,OBJECT)
    struct.pack_into('<I',data,CALL_SP+20-stack.address,PACKET)
    machine.regions['stack'] = replace(stack,data=bytes(data))
    formatted = machine.run(0x602a549b,0x602a54bb,
        overrides=dict(sp=CALL_SP,d0=selected['registers']['d0'],d2=0),full_trace=True,limit=30000,
        breakpoints=[0x60061808,0x6040e126,base['syms']['_ep7_gcc_quarantine']])
    result_ok(machine,formatted,0x602a54bb,CALL_SP)
    require(machine.read(FORMAT+12,8) == bytes.fromhex('700032005014400f') and
            machine.read(FORMAT+80,2) == struct.pack('<H',12) and
            machine.read(FORMAT+88,4) == struct.pack('<I',0xb0000000) and
            all(sum(t['pc'] == pc for t in formatted['trace']) == 1 for pc in
                (0x6029b89e,0x603dba87,0x605556d7)) and machine.read(CAPTURE,SIZE) == capture,
            'complete original format producer, native buffer resolution or capture isolation changed')
    continued_machine = machine.clone()
    continued_machine.regions['stack'] = original.regions['stack']
    continued_machine.regions['caller'] = original.regions['caller']
    continued = continued_machine.resume(context['postpopulation_result']['registers'],0x602a44ba,
        full_trace=True,limit=60000,breakpoints=[0x60061808,0x6040e126,base['syms']['_ep7_gcc_quarantine']])
    changed = [dict(offset=i,before=a,after=z) for i,(a,z) in
        enumerate(zip(capture,continued_machine.read(CAPTURE,SIZE))) if a != z]
    require(continued['status'] == 'memory_fault' and continued['fault'] == dict(
        kind=1,pc=0x602a919e,map=0,address=0x6223dab0,size=1,access='read') and
        [r['offset'] for r in changed] == [24022,24026,24536,24537,24538,24539,24540] and
        continued_machine.read(CAPTURE+24536,5) == struct.pack('<2HB',3904,5200,12),
        'native population format consumption or next request member changed')
    rows = [stage(name,result) for name,result in (
        ('native_first_three_resource_pool_constructors',initialized),('native_pool_logical_lock_reset',reset),
        ('native_complete_auxiliary_resource_allocation',allocated),('native_request_format_class',selected),
        ('complete_native_request_format_producer',formatted),('second_population_after_format',continued))]
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],engine=str(engine),
        cases=rows,native_instructions=sum(r['completed'] for r in rows),
        maximum_observed_new_stack_depth=max(r['stack_depth_from_call_sp'] for r in rows),
        native_store_capacity_added=1031+4+84,conditional_BSS_bytes_added=27,hardware_model_bytes_added=1,
        existing_registry_bytes_opened_for_native_store=6,pools=headers,
        native_auxiliary_allocation=dict(entry='0x6029be82',capture_id=1,selectors=[0,256],handles=[1,257],
            flags_before=4,flags_after=5,remaining_counts=[19,19,7],native_allocate_calls=2,
            native_hardware_lock_acquire_release_pairs=2,logical_and_hardware_locks_released=True),
        complete_native_format=dict(entry='0x6055545e',return_pc='0x602a54bb',record=hex(FORMAT),
            format_class='0x10000',dimensions=[5200,3904],buffer_pointer='0xb0000000',
            pointer_resolved_natively=True,backing_payload_mapped=False,producer_completed=True),
        capture_changes=changed,frontier=dict(status=continued['status'],fault=continued['fault'],
            input_object=hex(OBJECT),member_offset=1684),
        second_population_completed=False,finish_observer_executed=False,
        hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['Three constructors execute actual603dac40 arguments through603dacc8. They are a prefix of whole resource initialization; unused pools and payload backing are not fabricated.',
                '27B explicitly assume original startup BSS:2B debug gate,24B pool0 allocation bitmap and its first1B reference counter. Other unwritten fields remain unmapped.',
                'One8fe00018 byte models an initially idle hardware semaphore with a single contender. Original BSET/BCLR and scheduler lock code execute; physical atomicity, competing cores and cache ordering are not proven.',
                'Complete6029be82 attaches actual auxiliary pool handles to the existing ID1 fixture. Original fresh registry scan, capture allocation, publication order and allocation generation remain unexecuted.',
                'The completed format producer now resolves its buffer pointer natively. ROM-derived dimensions and unmapped backing do not qualify an active sensor format or COLOR shot.',
                'The waiting consumer resumes only after the producer returns. It stops at request member1684; finish, relay/worker lifecycle, residency and backup/recovery remain unresolved.'])
    return report,dict(upstream=contexts,upstream_report=upstream,cases=[dict(context,
        resources_machine=machine,resources_result=allocated,format_result=formatted,
        postpopulation_machine=continued_machine,postpopulation_result=continued)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(request_resources_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
