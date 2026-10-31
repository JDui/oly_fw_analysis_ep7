#!/usr/bin/env python3
"""Carry an actually frozen controller value through native queue4b and its materializer.

Queue backing, an idle event-flag object, enclosing stack words and task handover
are explicit fixtures. Original queue, notification and candidate code execute.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import STACK,CALLER,require
from ep7_candidate_publish_sim import bootstrap_context,publish_runtime,u32,released,signed
from ep7_candidate_state_sim import CALL_SP,guarded,objects,ready_lock
from ep7_candidate_capture_sim import prepare_frozen_fifo,pop_fifo,summarize_capture
from ep7_sim_probe import brief
from penf_emulator import Region

QUEUE,FLAG = 0x4b,203
METADATA = 0x19410000  # Opaque identity; deliberately no metadata buffer mapping.
NOTIFICATION_BASE,NOTIFICATION_ROOTS = 0xa26c2300,0xa26c3374
SEND_SP,RECEIVE_SP = CALL_SP-32,STACK+1024
FLAG_TABLE = 0x6003e39c


def result_ok(machine,result,stop,sp):
    require(result['status']=='returned' and result['registers']['pc']==stop and
            result['registers']['sp']==sp and result['fault'] is None,
            'message path stopped: '+str(brief(result)))
    released(machine)


def native_call(machine,syms,target,mask,frame,overrides=None,*,limit=20000):
    machine.regions['caller'] = Region('caller',CALLER,
        b'\xdd'+struct.pack('<i',target-CALLER)+bytes([mask,frame]),'rx')
    breakpoints=[syms['_ep7_gcc_quarantine']]
    result = machine.run(CALLER,CALLER+7,overrides=dict(sp=CALL_SP,**(overrides or {})),
        full_trace=True,limit=min(limit,100000),breakpoints=breakpoints)
    trace,completed,inputs=list(result['trace']),result['completed'],result['inputs']
    segments=[dict(status=result['status'],completed=result['completed'],pc=hex(result['registers']['pc']))]
    # The runner caps each trace at100000 entries. Resume only a verified
    # instruction-budget stop, retaining all architectural state and captures.
    while result['status']=='instruction_limit' and completed<limit:
        result=machine.resume(result['registers'],CALLER+7,full_trace=True,
            limit=min(limit-completed,100000),breakpoints=breakpoints)
        trace.extend(result['trace'])
        completed+=result['completed']
        segments.append(dict(status=result['status'],completed=result['completed'],pc=hex(result['registers']['pc'])))
    result.update(trace=trace,completed=completed,inputs=dict(inputs,limit=limit),execution_segments=segments)
    result_ok(machine,result,CALLER+7,CALL_SP)
    require(len(trace)==completed,'native call trace was truncated across an instruction-budget resume')
    return result


def initialize_queue(machine,syms,handle=QUEUE):
    """Run before runtime publication, using already supplied independent backing."""
    name = f'queue_{handle:x}'
    region = machine.regions[name]
    backing = u32(machine,region.address+32)
    capacity = u32(machine,region.address+28)
    machine.regions[name] = replace(region,data=region.data+b'\xa5'*24,
                                   permissions='rw',capture=True)
    guarded(machine,name+'_backing',backing,b'\xa5'*capacity)
    result = native_call(machine,syms,0x60030c4c,0xb0,16,dict(a0=region.address))
    require(result['registers']['d0']==0 and
            machine.read(region.address+4,16)==struct.pack('<4I',region.address+4,region.address+4,
                                                         region.address+12,region.address+12) and
            machine.read(region.address+36,20)==struct.pack('<5I',backing,backing,backing+capacity,capacity,0),
            'native queue initializer did not create empty wait lists and ring cursors')
    return result


def setup_notification(machine,syms):
    # Original fixed arrays: domain0 255 rows, domain1 64, domain2 32, each 12B.
    guarded(machine,'notification_tables_and_roots',NOTIFICATION_BASE,b'\xa5'*(4224))
    initialized = native_call(machine,syms,0x6005134a,0,4)
    require(machine.read(NOTIFICATION_ROOTS,12)==struct.pack('<3I',0xa26c2300,0xa26c2ef4,0xa26c31f4),
            'native notification table roots changed')
    require(machine.read(0x60040c90,2)==struct.pack('<H',FLAG) and
            machine.read(0x60040d72,2)==struct.pack('<H',QUEUE),
            'materializer notification constants changed')
    registered = machine.run(0x603df7c9,0x603df7e0,overrides=dict(sp=CALL_SP),full_trace=True,limit=5000)
    result_ok(machine,registered,0x603df7e0,CALL_SP)
    entry = NOTIFICATION_BASE+12*(QUEUE-1)
    require(machine.read(entry+4,8)==struct.pack('<2I',FLAG,1),'native queue4b notification registration changed')
    # A pre-existing idle flag, from its real ROM pointer/spec rows. This test
    # executes setting the flag, not its allocation or a waiting receiver task.
    flag_object = u32(machine,FLAG_TABLE+4*(FLAG-1))
    require(u32(machine,0x600411a4+212)==FLAG_TABLE and
            machine.read(0x6003ab70,12)==struct.pack('<3I',FLAG,4,0),
            'native event-flag pointer/spec binding changed')
    flag = bytearray(40)
    struct.pack_into('<H',flag,0,FLAG)
    struct.pack_into('<2I',flag,4,flag_object+4,flag_object+4)
    struct.pack_into('<3I',flag,12,4,0,0)
    guarded(machine,'notification_flag_203',flag_object,bytes(flag))
    return initialized,registered,flag_object


def summarize_message(name,result,sp):
    row = summarize_capture(name,result)
    row['stack_depth_from_call_sp'] = sp-min(result['registers']['sp'],min(r['sp'] for r in result['trace']))
    for key,address in [('native_raw_send_entries',0x60036ede),('native_raw_receive_entries',0x60036c8e),
                        ('native_receive_index_block_entries',0x60036caf),
                        ('named_send_entries',0x600514b6),('notification_entries',0x60051078),
                        ('native_flag_set_entries',0x60035a5e)]:
        row[key] = sum(r['pc']==address for r in result['trace'])
    return row


def message_context(directory,prefix,engine,expect_legacy_entry=False,*,prepare_kernel=None):
    queue_setup = []
    def prepare(machine,syms):
        queue_setup.append(initialize_queue(machine,syms))
        if prepare_kernel:
            prepare_kernel(machine,syms)
    base,front,syms,build,_ = bootstrap_context(directory,prefix,engine,prepare_kernel=prepare)
    machine,_,_,_ = publish_runtime(base,front,syms)
    runtime,_,_,provider = objects(machine,syms)
    capture_cases,frozen,_,_ = prepare_frozen_fifo(machine,syms)
    popped,scope = pop_fifo(machine,syms)
    require(scope==struct.pack('<I',1)+frozen+b'\x01\0\0','upstream actual frozen scope missing')
    tables,registered,flag_object = setup_notification(machine,syms)
    cases = [summarize_message('native_queue4b_initialize_before_publish',queue_setup[0],CALL_SP),
             summarize_message('native_notification_tables_initialize',tables,CALL_SP),
             summarize_message('native_queue4b_flag203_registration',registered,CALL_SP)]

    command = struct.pack('<4I',0,68,19,METADATA)
    # Same live physical scope produced by the actual FIFO pop at CALL_SP+32.
    # Original metadata frame32 plus send frame48 put it at send-W+112.
    w = SEND_SP-48
    require(w+112==CALL_SP+32,'deferred producer scope frame relation changed')
    machine.mutate('stack',w+52-STACK,command)
    machine.mutate('stack',w+80-STACK,struct.pack('<I',0x602ac613))
    sent = machine.run(0x602ac869,0x602ac870,overrides=dict(sp=SEND_SP,d0=QUEUE,d1=16,
        a0=w+52,a1=0xffffffff,d2=1),full_trace=True,limit=40000,
        breakpoints=[syms['_ep7_gcc_quarantine']])
    result_ok(machine,sent,0x602ac870,SEND_SP)
    require(sent['registers']['d0']==0,'candidate named send returned failure')
    sent_summary = summarize_message('patched_deferred_producer_send',sent,SEND_SP)
    cases.append(sent_summary)
    require(sent_summary['named_send_entries']==sent_summary['native_raw_send_entries']==
            sent_summary['notification_entries']==sent_summary['native_flag_set_entries']==1,
            'candidate send skipped native queue or post-send notification')
    backing = u32(machine,machine.regions['queue_4b'].address+32)
    wire = machine.read(backing+4,28)
    require(u32(machine,backing)==28 and wire[:16]==command and wire[16:20]==b'E7T1' and
            int.from_bytes(wire[20:],'little')!=0,'native ring did not contain command plus published ticket')
    require(u32(machine,flag_object+20)==1 and machine.read(CALL_SP+32+29,1)==b'\x02',
            'notification flag/single-use producer scope state changed')
    ready_lock(machine,provider)

    # Explicit handover to the actual queue4b materializer task configuration.
    require(machine.read(0x60038d50,28)==struct.pack('<7I',0x20,0,0,0x603df803,54,4096,0),
            'materializer task row changed')
    machine.mutate('tcb',16,struct.pack('<H',0x20))
    machine.mutate('tcb',76,struct.pack('<I',0x603df803))
    rw = RECEIVE_SP-44
    descriptor,command_out = rw+552,rw+196
    for offset,value in ((48,0),(56,descriptor),(484,0x603dfb7d),(532,0x603df8c0)):
        machine.mutate('stack',rw+offset-STACK,struct.pack('<I',value))
    machine.mutate('stack',descriptor-STACK,b'\x5a'*312)
    machine.mutate('stack',command_out-STACK,b'\xcc'*16)
    received = machine.run(0x603dfc9b,0x603dfca2,overrides=dict(sp=RECEIVE_SP,d0=QUEUE),
        full_trace=True,limit=20000,breakpoints=[syms['_ep7_gcc_quarantine']])
    result_ok(machine,received,0x603dfca2,RECEIVE_SP)
    receive_summary = summarize_message('patched_materializer_receive',received,RECEIVE_SP)
    cases.append(receive_summary)
    observation = dict(linked_native_entry=hex(syms['ep7_stock_queue_receive_local_unresolved']),
        status=signed(received['registers']['d0']),command=machine.read(command_out,16).hex(),
        descriptor_prefix_preserved=machine.read(descriptor,300)==b'\x5a'*300,
        trailer=machine.read(descriptor+300,12).hex(),expected_trailer=wire[16:].hex(),
        native_return_values=[signed(r['d0']) for r in received['trace']
                              if r['pc']==syms['_ep7_queue_receive_native_return']],
        queue_message_count_after_receive=u32(machine,machine.regions['queue_4b'].address+52),
        queue_free_bytes_after_receive=u32(machine,machine.regions['queue_4b'].address+48))
    require(observation['descriptor_prefix_preserved'],'materializer overwrote the stock descriptor prefix')
    if expect_legacy_entry:
        require(observation['linked_native_entry']=='0x60036caf' and observation['status']==-1 and
                observation['native_return_values']==[-17] and observation['queue_message_count_after_receive']==1 and
                observation['queue_free_bytes_after_receive']==4832 and
                observation['command']==('cc'*16) and observation['trailer']==('00'*12) and
                receive_summary['native_raw_receive_entries']==0 and
                receive_summary['native_receive_index_block_entries']==1,
                'known skipped-prologue defect did not reproduce: '+json.dumps(observation))
    else:
        require(observation['linked_native_entry']=='0x60036c8e' and observation['status']==0 and
                observation['native_return_values']==[28] and observation['queue_message_count_after_receive']==0 and
                observation['queue_free_bytes_after_receive']==4864 and
                machine.read(command_out,16)==command and machine.read(descriptor+300,12)==wire[16:] and
                receive_summary['native_raw_receive_entries']==1,
                'actual materializer receive failed: '+json.dumps(observation))
        entry = next(r for r in received['trace'] if r['pc']==0x60036c8e)
        index = next(r for r in received['trace'] if r['pc']==0x60036caf)
        require(machine.read(0x60036c8e,4)==b'\x43\x08\x46\x04' and
                entry['d1']==0 and entry['sp']==index['sp'] and
                sum(r['pc']==0x60036c90 for r in received['trace'])==1,
                'receive did not preserve its input timeout and destination in the native frame')
        observation.update(native_input_timeout=entry['d1'],native_input_destination=hex(entry['a0']),
                           both_native_parameter_save_instructions_executed=True)
        # The same timeout=0 must also reach the native empty-poll path. Reuse
        # a clone so later stages can retain the successfully received ticket.
        empty = machine.clone()
        empty.mutate('stack',command_out-STACK,b'\xcc'*16)
        header = empty.read(empty.regions['queue_4b'].address,60)
        polled = empty.run(0x603dfc9b,0x603dfca2,overrides=dict(sp=RECEIVE_SP,d0=QUEUE),
            full_trace=True,limit=20000,breakpoints=[syms['_ep7_gcc_quarantine']])
        result_ok(empty,polled,0x603dfca2,RECEIVE_SP)
        raw_returns = [signed(r['d0']) for r in polled['trace']
                       if r['pc']==syms['_ep7_queue_receive_native_return']]
        require(signed(polled['registers']['d0'])==-2 and raw_returns==[-50] and
                empty.read(command_out,16)==b'\xcc'*16 and empty.read(descriptor,300)==b'\x5a'*300 and
                empty.read(descriptor+300,12)==bytes(12) and
                empty.read(empty.regions['queue_4b'].address,60)==header,
                'empty native poll did not reject cleanly and clear the stale ticket')
        ready_lock(empty,provider)
        poll_summary = summarize_message('patched_materializer_empty_poll',polled,RECEIVE_SP)
        require(poll_summary['native_raw_receive_entries']==1 and poll_summary['context_switch_entries']==0,
                'empty poll skipped native receive or tried switching tasks')
        poll_summary.update(native_return_values=raw_returns,stale_ticket_cleared=True,
                            command_descriptor_prefix_and_queue_header_unchanged=True)
        cases.append(poll_summary)
    ready_lock(machine,provider)
    report = dict(scope=__doc__,candidate_build_revision=build['source_revision'],
        actual_elf_code_equals_decoded_candidate=True,all_assertions_passed=True,
        expectation='known_skipped_receive_prologue' if expect_legacy_entry else 'native_message_carriage',
        message_carriage_passed=not expect_legacy_entry,receive=observation,
        hash_checks_performed=False,engine=str(engine),runtime=hex(runtime),
        capture_upstream_instructions=sum(r['completed'] for r in capture_cases)+popped['completed'],
        cases=cases,wire_command=list(struct.unpack('<4I',command)),wire_bytes=28,
        ticket_serial=int.from_bytes(wire[20:],'little'),frozen_snapshot=list(struct.unpack('<B24b',frozen)),
        notification=dict(flag_id=FLAG,mask=1,object=hex(flag_object),actual_flags_after_send=1,
                          native_table_initializer_executed=True,native_registration_executed=True),
        metadata_object_unmapped=True,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['Upstream S2/controller single-task, resident-code, shared-lock and owned-capture fixtures remain explicit; no full boot or actual task launch/switch occurs.',
                'Native queue initialization uses independent synthetic backing supplied before publication. Heap allocation and earlier real storage reservation remain untested.',
                'Notification arrays and registration execute original code, and native flag-set changes an explicit idle flag203 object from its original ROM binding. No waiter/task wakeup is modeled.',
                'Producer and materializer CALLs execute their actual candidate bridges, using reviewed ancestor stack words and task TCB fields as fixtures. Outer metadata constructor/router loops do not execute.',
                'Metadata remains an unmapped identity label. This stage proves native command/ticket carriage; stock descriptor materialization, downstream queues, worker allocator/job/cleanup and ISP are later stages.'])
    return report,dict(machine=machine,syms=syms,build=build,descriptor=descriptor,
                       command_out=command_out,received=received,wire=wire,frozen=frozen)


def inspect(directory,prefix,engine,expect_legacy_entry=False):
    return message_context(directory,prefix,engine,expect_legacy_entry)[0]


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    parser.add_argument('--expect-legacy-entry',action='store_true',
                        help='record the identified old-candidate entry defect, never a readiness pass')
    args = parser.parse_args()
    print(json.dumps(inspect(args.candidate,args.tool_prefix,args.engine,args.expect_legacy_entry),indent=2))
