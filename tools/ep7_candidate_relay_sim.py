#!/usr/bin/env python3
"""Carry the materialized ticket through native 4c/ab/4f queues and worker claim.

Queue/notification initialization and each send/receive execute original code.
Task handovers and intervening preprocessing are explicit boundaries: this is a
transport/claim probe, not complete relay-task or native worker execution.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import STACK,require
from ep7_candidate_publish_sim import u32,signed
from ep7_candidate_state_sim import CALL_SP,guarded,objects,ready_lock
from ep7_candidate_message_sim import (initialize_queue,native_call,result_ok,
    summarize_message,NOTIFICATION_BASE,FLAG_TABLE)
from ep7_candidate_descriptor_sim import descriptor_context

RELAY_SP = STACK+2048
FLAG = 58


def task_fixture(machine,task,row,entry,priority,stack_bytes):
    require(machine.read(row,28)==struct.pack('<7I',task,0,0,entry,priority,stack_bytes,0),
            'downstream task ROM configuration changed')
    machine.mutate('tcb',16,struct.pack('<H',task))
    machine.mutate('tcb',76,struct.pack('<I',entry))
    machine.mutate('tcb',84,struct.pack('<I',stack_bytes))
    stack = machine.regions['stack']
    machine.regions['stack'] = replace(stack,data=stack.data[:stack_bytes].ljust(stack_bytes,b'\xcc'))
    machine.regions['stack_after'] = replace(machine.regions['stack_after'],address=STACK+stack_bytes)


def relay_notification(machine,syms):
    # Preserve the already initialized tables and queue4b registration. Run the
    # original initializer that registers both 4c and 4d to event flag58/bit1.
    require(machine.read(0x60040b6e,2)==struct.pack('<H',FLAG) and
            machine.read(0x6003a4a4,12)==struct.pack('<3I',FLAG,4,0),
            'dual relay notification ROM binding changed')
    result = native_call(machine,syms,0x603ef864,0,4)
    for handle in (0x4c,0x4d):
        require(machine.read(NOTIFICATION_BASE+12*(handle-1)+4,8)==struct.pack('<2I',FLAG,1),
                'native dual relay notification registration failed')
    for handle in (0xab,0x4f):
        require(u32(machine,NOTIFICATION_BASE+12*(handle-1)+4)==0,
                'unregistered relay queue unexpectedly acquired a notification hook')
    flag_object = u32(machine,FLAG_TABLE+4*(FLAG-1))
    flag = bytearray(40)
    struct.pack_into('<H',flag,0,FLAG)
    struct.pack_into('<2I',flag,4,flag_object+4,flag_object+4)
    struct.pack_into('<3I',flag,12,4,0,0)
    guarded(machine,'notification_flag_58',flag_object,bytes(flag))
    return result,flag_object


def relay_context(directory,prefix,engine):
    setups = []
    def prepare(machine,syms):
        for handle in (0x4c,0xab,0x4f):
            setups.append((handle,initialize_queue(machine,syms,handle)))
    upstream,context = descriptor_context(directory,prefix,engine,prepare_kernel=prepare)
    machine,syms = context['machine'],context['syms']
    _,_,_,provider = objects(machine,syms)
    registered,flag_object = relay_notification(machine,syms)
    cases = [summarize_message(f'native_queue{handle:x}_initialize_before_publish',result,CALL_SP)
             for handle,result in setups]
    cases.append(summarize_message('native_queue4c_4d_flag58_registration',registered,CALL_SP))
    ticket = context['wire'][16:]
    materialized = machine.read(context['descriptor'],312)
    transfers = []

    def send(handle,descriptor,start,stop,sp):
        expected = machine.read(descriptor,312)
        require(expected[300:]==ticket,'relay lost the upstream ticket before send')
        result = machine.run(start,stop,overrides=dict(sp=sp,a2=descriptor),
            full_trace=True,limit=30000,breakpoints=[syms['_ep7_gcc_quarantine']])
        result_ok(machine,result,stop,sp)
        require(result['registers']['d0']==1,'native descriptor send helper returned failure')
        queue = machine.regions[f'queue_{handle:x}'].address
        backing,capacity = u32(machine,queue+32),u32(machine,queue+28)
        require(u32(machine,backing)==312 and machine.read(backing+4,312)==expected and
                u32(machine,queue+52)==1 and u32(machine,queue+48)==capacity-316 and
                machine.read(descriptor+300,12)==bytes(12),
                'native relay send changed the payload or did not consume its local ticket')
        row = summarize_message(f'native_descriptor_send_queue{handle:x}',result,sp)
        hooks = [r['a0'] for r in result['trace'] if r['pc']==0x600515c2]
        row.update(native_notification_lookup_entries=sum(r['pc']==0x6005159f for r in result['trace']),
                   native_notification_hook_values=hooks)
        require(row['native_raw_send_entries']==row['named_send_entries']==row['native_notification_lookup_entries']==1 and
                hooks==[FLAG if handle==0x4c else 0] and
                row['notification_entries']==row['native_flag_set_entries']==(1 if handle==0x4c else 0),
                'native relay send or registered notification was skipped: '+json.dumps(row))
        ready_lock(machine,provider)
        cases.append(row)
        transfers.append(dict(queue=hex(handle),wire_bytes=312,sender_descriptor=hex(descriptor),
            sender_ticket_cleared=True,native_notification_lookup_executed=True,
            native_notification_executed=handle==0x4c,
            registered_flag=FLAG if handle==0x4c else None))
        return expected

    def receive(handle,descriptor,start,stop,expected,helper=False):
        machine.mutate('stack',descriptor-STACK,b'\xcc'*312)
        if not helper:
            machine.mutate('stack',RELAY_SP+4-STACK,struct.pack('<2I',0,254))
        result = machine.run(start,stop,overrides=dict(sp=RELAY_SP,a2=descriptor,a3=0x6053de0c),
            full_trace=True,limit=30000,breakpoints=[syms['_ep7_gcc_quarantine']])
        result_ok(machine,result,stop,RELAY_SP)
        queue = machine.regions[f'queue_{handle:x}'].address
        raw_returns = [signed(r['d0']) for r in result['trace']
                       if r['pc']==syms['_ep7_queue_receive_native_return']]
        require(result['registers']['d0']==(1 if helper else 0) and raw_returns==[312] and
                machine.read(descriptor,312)==expected and u32(machine,queue+52)==0 and
                u32(machine,queue+48)==u32(machine,queue+28),
                'native relay receive did not restore the exact descriptor and ticket')
        row = summarize_message(f'native_descriptor_receive_queue{handle:x}',result,RELAY_SP)
        require(row['native_raw_receive_entries']==1 and row['context_switch_entries']==0,
                'native relay receive skipped the kernel or tried switching fixture tasks')
        row.update(native_return_values=raw_returns,descriptor_bytes_preserved=True)
        cases.append(row)
        transfers[-1].update(receiver_descriptor=hex(descriptor),queue_empty_after_receive=True,
                             ticket_preserved=True)
        ready_lock(machine,provider)
        return result

    expected = send(0x4c,context['descriptor'],0x603dfc25,0x603dfc44,context['descriptor']-68)
    require(u32(machine,flag_object+20)==1,'queue4c notification did not set flag58')
    task_fixture(machine,0x21,0x60038d6c,0x603ef892,55,4752)
    dual_descriptor = RELAY_SP+12
    receive(0x4c,dual_descriptor,0x603ef8a9,0x603ef8ba,expected)
    # The native preprocessing call603ef924 is a separate unresolved frontier.
    # Execute its following send slice with the actual received bytes retained.
    expected = send(0xab,dual_descriptor,0x603ef92f,0x603ef93e,RELAY_SP)
    task_fixture(machine,0x57,0x60039354,0x603ef94a,46,4096)
    relay_descriptor = RELAY_SP+4
    receive(0xab,relay_descriptor,0x603ef953,0x603ef962,expected,helper=True)
    # Likewise do not claim to have executed preprocess603f04b9 or its log calls.
    expected = send(0x4f,relay_descriptor,0x603ef984,0x603ef993,RELAY_SP)
    task_fixture(machine,0x6c,0x600395a0,0x603f26a1,26,8192)
    worker_descriptor = RELAY_SP+4
    received = receive(0x4f,worker_descriptor,0x603f26ac,0x603f26bb,expected,helper=True)
    require(machine.read(worker_descriptor,312)==materialized,
            'full queue route changed the materialized descriptor')

    scope = RELAY_SP-104
    # The worker preflight/dispatch slice is not executed here. D0=0 records its
    # successful branch as a fixture; A0 comes from the original mov a2,a0.
    def enter_worker(target,name):
        registers = dict(received['registers'],pc=0x603f2721,sp=RELAY_SP,a2=worker_descriptor,d0=0)
        result = target.resume(registers,0x603f2800,full_trace=True,limit=15000,
            breakpoints=[syms['_ep7_gcc_quarantine']])
        result_ok(target,result,0x603f2800,RELAY_SP-192)
        require(result['registers']['a0']==worker_descriptor and result['registers']['d0']==0,
                'worker wrapper changed the saved native inputs')
        row = summarize_message(name,result,RELAY_SP)
        row.update(scope_address=hex(scope),scope_state=u32(target,scope),
                   scope_snapshot=target.read(scope+4,25).hex(),
                   descriptor_marker=target.read(worker_descriptor+300,4).decode('ascii'))
        ready_lock(target,provider)
        cases.append(row)
        return result

    worker = enter_worker(machine,'native_worker_scope_claim')
    require(machine.read(scope,48)==struct.pack('<I',1)+context['frozen']+bytes(19) and
            machine.read(worker_descriptor+300,12)==b'E7C1'+ticket[4:],
            'actual worker did not acquire the original frozen snapshot exactly once')
    replay = machine.clone()
    # Deliberately replay the previously valid full descriptor after consumption;
    # clearing only its local marker would be a weaker duplicate-claim test.
    replay.mutate('stack',worker_descriptor-STACK,materialized)
    enter_worker(replay,'replayed_valid_ticket_after_worker_claim')
    require(replay.read(scope,48)==bytes(48) and
            replay.read(worker_descriptor+300,12)==b'E7C1'+ticket[4:],
            'replayed ticket acquired a second worker snapshot')
    report = dict(scope=__doc__,candidate_build_revision=upstream['candidate_build_revision'],
        engine=str(engine),all_assertions_passed=True,transport_and_claim_passed=True,
        cases=cases,transfers=transfers,worker_scope=hex(scope),
        worker_snapshot=list(struct.unpack('<B24b',context['frozen'])),
        duplicate_ticket_claim_rejected=True,native_worker_body_executed=False,
        original_flag58=dict(object=hex(flag_object),flags_after_send=1),
        upstream_materializer_case=upstream['case'],
        upstream_message_cases=upstream['upstream_message_cases'],
        upstream_capture_fifo_instructions=upstream['upstream_capture_fifo_instructions'],
        hash_checks_performed=False,native_api_success_stubs=False,firmware_files_modified=False,
        hardware_executed=False,installable=False,
        limits=['Upstream startup/kernel/residency/capture/metadata fixtures remain; no full boot or actual task creation/switch.',
                'Three downstream queues initialize before runtime publication using independent backing, not native heap allocation.',
                'Original dual-queue registration and flag58 set execute against an idle flag fixture; no waiter wakeup. ab/4f have no registered hook in this scenario, not a proof of all dynamic registrations.',
                'Task TCB fields and bounded stack handovers are explicit fixtures corroborated against ROM rows. Caller slices execute, not complete task loops or IRQ paths.',
                'Dual preprocessing603efb6d, kind19 preprocessing603f04b9, outer router selection and worker preflight603f28da are not executed. Descriptor bytes remain unchanged across these explicit gaps.',
                'Worker wrapper executes claim then stops at original603f2800. Native job allocation/construction/process/cleanup, CPU/ISP and ACK remain.',
                'Replay is a cloned adversarial injection of the old valid descriptor after actual claim; it proves this ticket cannot supply a second snapshot, not concurrent task scheduling.'])
    context.update(descriptor=worker_descriptor,worker=worker,worker_scope=scope)
    return report,context


def inspect(directory,prefix,engine):
    return relay_context(directory,prefix,engine)[0]


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.candidate,args.tool_prefix,args.engine),indent=2))
