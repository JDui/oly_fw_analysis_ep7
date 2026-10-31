#!/usr/bin/env python3
"""Execute linked controller adapters and native deferred FIFO with frozen H/L.

The source objects, completed population fields and controller task are fixtures.
Lookup, helper relocation/copy, FIFO operations, adapters and locks are real code.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import STACK, require
from ep7_candidate_publish_sim import bootstrap_context,publish_runtime,u32,released
from ep7_candidate_state_sim import (CALL_SP, INPUT, SNAPSHOT, gcc_call, summarize,
                                     objects, guarded, ready_lock)
from ep7_sim_probe import brief
from penf_emulator import Region

NODE,CAPTURE = 0x19510000,0x19700000
ASSOCIATED,POOL,REGISTRY = 0x6223e164,0x6223e0dc,0x6223d190
WAIT,WAIT_BACKING = 0x6223e7e0,0x6223e7f4
LOOKUP,ENQUEUE,POP,COPY = 0x6029b9d1,0x6020b98b,0x6020b9ff,0x47001052
ENGINE_CALLBACKS = (0x602a2d43,0x602a2ec7,0x602a2ef7,0x602a2f57,
    0x602a2f62,0x602a2f91,0x602a2f6d,0x602a2f73,0x602a2f70,0x602a2f7e,0,
    0x602a301b,0x602a2f81,0x602a3042,0x60000,0x602a2edd,0x70000)


def summarize_capture(name,result):
    row = summarize(name,result)
    for key,address in [('native_lookup_entries',LOOKUP),('native_enqueue_entries',ENQUEUE),
                        ('native_pop_entries',POP),('native_copy_entries',COPY)]:
        row[key] = sum(r['pc']==address for r in result['trace'])
    return row


def native_block(machine,syms,start,stop,overrides=None,*,limit=20000):
    result = machine.run(start,stop,overrides=dict(sp=CALL_SP,**(overrides or {})),
        full_trace=True,limit=limit,breakpoints=[syms['_ep7_gcc_quarantine']])
    require(result['status']=='returned' and result['fault'] is None and
            result['registers']['sp']==CALL_SP,
            hex(start)+' did not reach the real continuation: '+str(brief(result)))
    released(machine)
    return result


def controller_fixture(machine):
    require(machine.read(0x60039664,28)==struct.pack('<7I',0x73,0,0,0x60289852,25,4096,0),
            'native controller task configuration changed')
    # Explicit task handover, not a simulated task launch or context switch.
    machine.mutate('tcb',16,struct.pack('<H',0x73))
    machine.mutate('tcb',76,struct.pack('<I',0x60289852))
    machine.mutate('tcb',84,struct.pack('<I',4096))
    machine.regions['stack'] = replace(machine.regions['stack'],data=b'\xcc'*4096)
    machine.regions['stack_after'] = replace(machine.regions['stack_after'],address=STACK+4096)
    pool = bytearray(36)
    struct.pack_into('<I',pool,0,POOL)
    struct.pack_into('<2H',pool,12,25,4)
    struct.pack_into('<I',pool,16,0x6223e0fc)
    struct.pack_into('<H',pool,28,16)
    struct.pack_into('<I',pool,32,ASSOCIATED-4)
    guarded(machine,'associated_pool',POOL-4,bytes(pool),'r')
    guarded(machine,'associated',ASSOCIATED-4,struct.pack('<4I',1,1,0,NODE),'r')
    node = bytearray(56)
    struct.pack_into('<I',node,0,1)
    struct.pack_into('<I',node,8,ASSOCIATED)
    guarded(machine,'capture_node',NODE,bytes(node),'r')
    capture = bytearray(24084)
    capture[24053],capture[24083] = 11,2
    guarded(machine,'capture',CAPTURE,bytes(capture),'r')
    row = bytearray(24)
    struct.pack_into('<H',row,0,4)
    struct.pack_into('<I',row,12,CAPTURE)
    guarded(machine,'capture_registry_id1',REGISTRY,bytes(row),'r')
    guarded(machine,'engine_mask',0x6223d0d8,struct.pack('<I',0xf000f),'r')
    # Ends at registry row0; keep the neighboring fixed ranges nonoverlapping.
    machine.regions['engine_callbacks'] = Region('engine_callbacks',0x6223d134,
                                                struct.pack('<17I',*ENGINE_CALLBACKS))
    guarded(machine,'native_wait_fifo',WAIT-4,b'\xa5'*124)
    guarded(machine,'settings',INPUT,bytes([5]+[0]*11+[-3 & 255]+[0]*11))
    guarded(machine,'snapshot',SNAPSHOT,b'\xcc'*25)


def relocate_helpers(machine,syms):
    # Reuse the exact E-P7 load-regions evidence; source readiness is a fixture.
    source = machine.read(0x6143ca00,6144)
    machine.regions['helper_source_alias'] = Region('helper_source_alias',0xa143ca00,source)
    guarded(machine,'relocated_helpers',0x47000800,b'\xa5'*6144)
    copied = native_block(machine,syms,0x60020297,0x600202af)
    require(machine.read(0x47000800,6144)==source,'native early helper copy differs from source')
    machine.regions['relocated_helpers'] = replace(machine.regions['relocated_helpers'],permissions='rx',capture=False)
    return copied


def inspect(directory,prefix,engine):
    base,front,syms,build,_ = bootstrap_context(directory,prefix,engine)
    machine,_,_,_ = publish_runtime(base,front,syms)
    runtime,_,core,provider = objects(machine,syms)
    controller_fixture(machine)
    cases = []

    def run(name,args=(),wanted=None,m=machine):
        result = gcc_call(m,syms,name,args,wanted=wanted,limit=20000)
        cases.append(summarize_capture(name,result))
        return result

    def block(name,start,stop,registers=None,m=machine):
        result = native_block(m,syms,start,stop,registers)
        cases.append(summarize_capture(name,result))
        return result

    copied = relocate_helpers(machine,syms)
    cases.append(summarize_capture('native_early_helper_copy',copied))
    run('_ep7_sidecar_transition_unresolved',[0,33])
    machine.mutate('state',0,struct.pack('<H',33))  # Original state commit is a fixture boundary.
    block('native_wait_initializer',0x602abe7b,0x602abe9d)
    require(machine.read(WAIT,18)==struct.pack('<IHHIHHH',182,25,4,WAIT_BACKING,0,0,0),
            'native wait initializer did not establish the exact empty FIFO')
    run('_ep7p_edit',[core,1,INPUT],1)
    run('_ep7cn_fresh',[NODE])
    fresh = machine.clone()
    block('patched_population_lookup',0x602a7ea0,0x602a7ea7,dict(d0=1))
    run('_ep7cn_population',[NODE,0])
    machine.mutate('settings',0,bytes([(-3)&255]+[0]*11+[2]+[0]*11))
    run('_ep7p_edit',[core,1,INPUT],1)
    block('patched_postpopulation_lookup',0x602a8dca,0x602a8dd1,dict(d0=1))
    run('_ep7cn_population',[NODE,1])
    run('_ep7q_capture_snapshot_unresolved',[1,ASSOCIATED,SNAPSHOT],1)
    frozen = bytes([1,5]+[0]*11+[(-3)&255]+[0]*11)
    require(machine.read(SNAPSHOT,25)==frozen,'controller resampled changed settings at finish')
    sealed = machine.clone()
    enqueued = block('patched_wait_enqueue',0x602ac3f6,0x602ac3fd,dict(a0=WAIT,d0=ASSOCIATED))
    require(enqueued['registers']['d0']==4 and u32(machine,WAIT_BACKING)==ASSOCIATED and
            machine.read(WAIT+12,6)==struct.pack('<3H',1,1,0),'real enqueue did not append associated')
    queued = machine.clone()

    def pop(m,label):
        # The actual patched CALL constructs W=CALL_SP-24 and W+24 return PC.
        # Ancestor continuation words are the explicit enclosing-stack fixture.
        m.mutate('stack',CALL_SP+8-STACK,struct.pack('<I',syms['_ep7_wait_scope_native_return']))
        m.mutate('stack',CALL_SP+80-STACK,struct.pack('<I',0x602ac502))
        m.mutate('stack',CALL_SP+32-STACK,b'\xcc'*32)
        result = block(label,0x602ac5e8,0x602ac5ef,dict(a0=WAIT),m=m)
        require(result['registers']['d0']==ASSOCIATED and
                m.read(WAIT+12,6)==struct.pack('<3H',0,1,1),'real pop lost FIFO position/value')
        return m.read(CALL_SP+32,32)

    scope = pop(machine,'patched_wait_pop_frozen')
    require(scope==struct.pack('<I',1)+frozen+b'\x01\x00\x00',
            'real FIFO pop did not transfer its frozen value into the owned scope')
    ready_lock(machine,provider)

    # A common prewrite callback revokes the queued snapshot before population
    # reuses its capture, but must not lose the native FIFO entry/order.
    run('_ep7cn_prewrite',[CAPTURE,0],m=queued)
    require(pop(queued,'patched_wait_pop_revoked')==bytes(32),
            'repopulation left a stale frozen snapshot in a deferred producer scope')
    ready_lock(queued,provider)

    # An early producer observation burns this node's single sampling chance.
    run('_ep7q_capture_snapshot_unresolved',[1,ASSOCIATED,SNAPSHOT],0,m=fresh)
    block('early_copy_population_lookup',0x602a7ea0,0x602a7ea7,dict(d0=1),m=fresh)
    run('_ep7cn_population',[NODE,0],m=fresh)
    block('early_copy_postpopulation_lookup',0x602a8dca,0x602a8dd1,dict(d0=1),m=fresh)
    run('_ep7cn_population',[NODE,1],m=fresh)
    run('_ep7q_capture_snapshot_unresolved',[1,ASSOCIATED,SNAPSHOT],0,m=fresh)
    require(fresh.read(SNAPSHOT,25)==b'\xcc'*25,'early unsealed observation later sampled settings')

    run('_ep7cn_free',[NODE],m=sealed)
    del sealed.regions['capture_node']
    sealed.mutate('snapshot',0,b'\xcc'*25)
    run('_ep7q_capture_snapshot_unresolved',[1,ASSOCIATED,SNAPSHOT],0,m=sealed)
    require(sealed.read(SNAPSHOT,25)==b'\xcc'*25,'retired node was dereferenced or copied')

    return dict(scope=__doc__,candidate_build_revision=build['source_revision'],
        actual_elf_code_equals_decoded_candidate=True,all_assertions_passed=True,
        hash_checks_performed=False,engine=str(engine),runtime=hex(runtime),cases=cases,
        controller_task_fixture=dict(tid='0x73',entry='0x60289852',stack_bytes=4096,
            native_configuration_row='0x60039664',task_launched=False),
        helper_copy=dict(source='0x6143ca00',resident_source_alias='0xa143ca00',destination='0x47000800',
            bytes=6144,native_copy_loop_executed=True,stock_copy_helper=hex(COPY),hardware_load_executed=False),
        capture_lookup=dict(actual_native_entry=hex(LOOKUP),id1_registry=hex(REGISTRY),
            registry_stride=24,registry_initialized_by_fixture=True),
        normal_frozen_snapshot=list(struct.unpack('<B24b',frozen)),native_fifo_initialized=True,
        native_enqueue_and_pop_executed=True,owned_stack_scope_correct=True,
        repopulation_revokes_queued_snapshot=True,repopulation_preserves_native_fifo_order=True,
        early_copy_permanently_neutral=True,retired_node_unmapped_no_read=True,
        native_api_success_stubs=False,firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['S2 resident/kernel/shared-lock assumptions are inherited. Task handover, engine table, associated pool/live refcount, node/registry/capture objects and completed native population fields are explicit fixtures.',
                'Fresh/sample/finish adapters, the patched prewrite lookup sites and native waiting-list seams execute; full stock node allocator/population/free/task-start functions do not.',
                'The internal helper is moved by the actual early CPU copy loop from an explicitly resident source alias. Flash transfer, instruction cache and physical alias coherence are not proven.',
                'The actual pop CALL creates its own native frame, while two ancestor return words model the surrounding wait-scope caller. The outer controller service is not executed end to end.',
                'Native queue4b message send, receiver/materializer/worker and ISP consumption are subsequent stages. Successful deferred-list transfer alone does not prove those stages or full native lifetime exclusion.'])


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.candidate,args.tool_prefix,args.engine),indent=2))
