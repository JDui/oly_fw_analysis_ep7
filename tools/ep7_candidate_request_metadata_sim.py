#!/usr/bin/env python3
"""Claim, initialize and publish native request metadata; observe real slot reuse.

Only original initialized members exist. Unknown incoming command flags still
stop their consumer, and independent slot reuse does not establish quiescence.
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
from ep7_candidate_format_record_sim import missing_bytes
from ep7_candidate_request_constructor_sim import OBJECT, PACKET
from ep7_candidate_request_preparation_sim import request_preparation_context


METADATA = 0x6223e450
MEMBERS = [(0,14),(20,8),(32,4)]


def request_metadata_context(directory,prefix,engine):
    upstream,contexts = request_preparation_context(directory,prefix,engine)
    base = contexts
    while 'syms' not in base:
        base = base['upstream']
    context = contexts['cases'][0]
    machine = context['preparation_machine'].clone()
    capture = machine.read(CAPTURE,SIZE)
    machine.regions['stack'] = replace(machine.regions['stack'],data=b'\xcc'*len(machine.regions['stack'].data))
    headers = missing_bytes(machine,[METADATA+96*i+offset for i in range(4) for offset in (92,93)]+
        [0x6223e5d0],0xa5,'native_metadata_pool_headers')
    contents = missing_bytes(machine,[METADATA+offset+i for offset,size in MEMBERS for i in range(size)],
        0xa5,'native_metadata_record')
    require(len(headers) == 9 and len(contents) == 26 and
            machine.read(0x6029c697,9) == bytes.fromhex('00fc82d0e523628108') and
            machine.read(0x6029cd56,9) == bytes.fromhex('fca114d42362f8313c'),
            'native metadata pool initialization, publication or store extent changed')
    initialized = machine.run(0x6029c697,0x6029c6bb,overrides=dict(sp=CALL_SP),full_trace=True,limit=1000)
    result_ok(machine,initialized,0x6029c6bb,CALL_SP)
    require(machine.read(0x6223e5d0,1) == b'\0' and
            all(machine.read(METADATA+96*i+92,2) == bytes([0,i]) for i in range(4)),
            'native four-slot free flags or indexes changed')
    # Reuse the already-native16B event embedded in the bounded command. The
    # actual receive materializer copies it in place, then the real caller
    # publishes its returned command pointer. No queue receive is asserted.
    event = machine.read(PACKET+44,16)
    require(event == struct.pack('<4I',204,1,11,PACKET), 'native embedded type11 event changed')
    published = machine.run(0x6029c98e,0x6029c99d,
        overrides=dict(sp=CALL_SP,a2=PACKET+44),full_trace=True,limit=1000)
    result_ok(machine,published,0x6029c99d,CALL_SP)
    require(machine.read(PACKET+44,26) == event+bytes(10) and
            machine.read(0x6223d414,4) == struct.pack('<I',PACKET) and
            sum(t['pc'] == 0x60289dac for t in published['trace']) == 1,
            'native materializer return or current-command publication changed')
    # Actual controller suffix claims a slot, stores command+60, selects class
    #10000 from native2348=0, and calls the whole native metadata initializer.
    completed = machine.run(0x6029cd4f,0x6029cd90,overrides=dict(sp=CALL_SP),full_trace=True,limit=3000,
        breakpoints=[0x60061808,0x6040e126,base['syms']['_ep7_gcc_quarantine']])
    result_ok(machine,completed,0x6029cd90,CALL_SP)
    record = {offset:machine.read(METADATA+offset,size) for offset,size in MEMBERS}
    require(record == {0:bytes.fromhex('0001000001000004d90400020000'),20:bytes(8),32:bytes(4)} and
            machine.read(PACKET+60,4) == struct.pack('<I',METADATA) and
            machine.read(0x6223e5d0,1) == b'\x01' and
            all(machine.read(METADATA+96*i+92,2) == bytes([1 if i==0 else 0,i]) for i in range(4)) and
            all(sum(t['pc'] == pc for t in completed['trace']) == 1 for pc in
                (0x602a7556,0x6029cd5c,0x602ab5e4,0x602ab888)) and
            machine.read(CAPTURE,SIZE) == capture,
            'native slot claim, parameter record or command attachment changed')
    # Target one ownership uncertainty: release does not clear payload or its
    # old command reference, and the next native claim may reuse that pointer.
    # Keep this branch separate from the still-owned main metadata context.
    reused = machine.clone()
    released = native_call(reused,base['syms'],0x602a75c3,0,0,dict(a0=METADATA),limit=1000)
    require(reused.read(METADATA+92,2) == bytes(2) and reused.read(0x6223e5d0,1) == b'\0' and
            reused.read(PACKET+60,4) == struct.pack('<I',METADATA) and
            all(reused.read(METADATA+offset,len(data)) == data for offset,data in record.items()),
            'native metadata release no longer retains its old payload and command reference')
    reclaimed = native_call(reused,base['syms'],0x602a7556,0x20,20,limit=1000)
    require(reclaimed['registers']['a0'] == METADATA and reused.read(METADATA+92,2) == b'\x01\0' and
            all(reused.read(METADATA+offset,len(data)) == data for offset,data in record.items()),
            'native same-slot reclaim or old-content preservation changed')
    source = machine.clone()
    frontier = source.run(0x6029d156,0x6029d1cc,overrides=dict(sp=CALL_SP),full_trace=True,limit=1000,
        breakpoints=[0x60061808,0x6040e126,base['syms']['_ep7_gcc_quarantine']])
    require(frontier['status'] == 'memory_fault' and frontier['fault'] == dict(
        kind=1,pc=0x6029d16a,map=0,address=PACKET+72,size=4,access='read') and
        frontier['registers']['d1'] == 1024 and source.read(CAPTURE,SIZE) == capture,
        'request-state producer no longer stops at the unknown incoming flag word')
    rows = [stage(name,result) for name,result in (
        ('native_metadata_four_slot_reset_slice',initialized),('native_current_command_publication_slice',published),
        ('native_metadata_claim_attach_and_initialize_slice',completed),
        ('native_metadata_release_independent_branch',released),('native_metadata_reclaim_independent_branch',reclaimed),
        ('request_state_incoming_flags_frontier',frontier))]
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],engine=str(engine),
        cases=rows,native_instructions=sum(r['completed'] for r in rows),
        maximum_observed_new_stack_depth=max(r['stack_depth_from_call_sp'] for r in rows),
        native_store_capacity_added=35,conditional_BSS_bytes_added=0,
        metadata=dict(address=hex(METADATA),slot_stride=96,slot_count=4,claimed_slot=0,next_slot=1,
            initialized_member_bytes=26,header_bytes=9,fields=dict(flags=256,kind=1,half6=1024,
                half8=1241,half10=512,half12=0,word20=0,word24=0,word32=0),
            initializer_completed=True,current_command=hex(PACKET),command_member_offset=60,
            pointer_published_by_native_code=True),
        reuse=dict(independent_branch=True,native_release_completed=True,same_slot_reclaimed=True,
            old_payload_retained=True,old_command_reference_retained=True,allocation_generation_proven=False),
        source_frontier=dict(status=frontier['status'],fault=frontier['fault'],command_member_offset=72,
            metadata_halfword_read=1024,request_members_still_unproduced=[1684,1686]),
        postpopulation_resumed=False,capture_unchanged=True,
        hash_checks_performed=False,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['Only four2-byte slot headers, one selector and26 actual initialized first-slot bytes are mapped. Other96-byte slot fields and unused slot payloads remain unmapped.',
                'Current-command publication reuses the already-native embedded event for an in-place materializer copy. The original queue receive and full6029c986 dispatcher/lifecycle are not executed.',
                'The actual6029cd4f suffix claims, attaches and initializes slot0. Its outer controller callback and event ordering remain outside this preparation probe.',
                'An independent release/reclaim branch proves pointer reuse and retained old contents/reference. It does not prove use-after-free in the complete firmware or asynchronous quiescence.',
                'The original request-state producer reads the generated metadata halfword, then stops at unmapped command+72. No flag word is fabricated and neither request1684/1686 nor second population/finish is completed.',
                'Valid COLOR, complete capture/metadata generations, worker lifecycle, residency and backup/recovery remain unresolved.'])
    return report,dict(upstream=contexts,upstream_report=upstream,cases=[dict(context,
        metadata_machine=machine,metadata_result=completed,metadata_source_machine=source,metadata_source_result=frontier)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(request_metadata_context(args.candidate,args.tool_prefix,args.engine)[0],indent=2))
