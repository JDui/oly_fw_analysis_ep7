#!/usr/bin/env python3
"""Execute candidate bootstrap with real native semaphore create/delete and explicit kernel fixtures.

The original queue pointer tables are used; queue headers/TCB/pending state and
the single-contender shared-lock byte are fixtures, not a whole-board model.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import (BASE, SP, TCB, RAM_START, RAM_BYTES, CALLER, Machine,
    candidate_inputs, require, returned, CLEAR_SITE, CLEAR_RESUME, INIT_SITE, INIT_RESUME,
    BOOT_SITE, ORIGINAL_BOOT, CREATE)
from ep7_sim_probe import brief
from penf_emulator import Region

ROOT = 0x600411a4
PEER_ROOTS = ((0x60041330,0xa27942b0),(0x600414bc,0xa27944d8))
ROOT_LOADS = ((0x60032613,ROOT),(0x60033506,PEER_ROOTS[0][0]),(0x600335b6,PEER_ROOTS[1][0]))
COUNTS = 0x621a63d4
SEM_TABLE = 0x6003df9c
SEM_OBJECT = 0x62199fd0
QUEUE_TABLE = 0x6003e99c
DELETE = 0x60031107
QUEUES = ((0x4b,148,4864),(0x4c,312,10112),(0x4d,300,9728),(0xab,312,10112),(0x4f,312,10112))
ROOT_WORDS = {16:0x621a6320,28:0x621a631c,56:COUNTS,60:0x600410d8,
    64:0x62192400,68:0x621a63ac,96:0x621a630c,100:0x621a6334,
    208:SEM_TABLE,232:QUEUE_TABLE,272:0x60073215,276:0x60073218,280:0x6007321b,
    316:0x600300a1,320:64,328:0x621a63b0,332:0xa2793e80,344:0,348:0x800,352:0,356:0,380:3}


def u32(machine,address):
    return struct.unpack('<I',machine.read(address,4))[0]


def signed(value):
    return value if value < 0x80000000 else value-0x100000000


def summary(result):
    require(len(result['trace'])==result['completed'],'native/bootstrap trace truncated')
    pcs = [row['pc'] for row in result['trace']]
    return dict(**brief(result),returned_d0=signed(result['registers']['d0']),
        observed_stack_depth_from_hook_sp=SP-min(result['registers']['sp'],min(row['sp'] for row in result['trace'])),
        native_get_tid_entries=pcs.count(0x600317ac),native_create_entries=pcs.count(CREATE),
        native_delete_entries=pcs.count(DELETE),native_slot_allocator_entries=pcs.count(0x60034f31),
        shared_bset_entries=pcs.count(0x60038582),shared_bclr_entries=pcs.count(0x6003858f),
        context_switch_entries=pcs.count(0x6003853e),task_exception_callback_entries=pcs.count(0x600343b1))


def fixture(machine):
    for offset,value in ROOT_WORDS.items():
        require(u32(machine,ROOT+offset)==value,'original domain0 root field changed '+str(offset))
    require(machine.read(0x600410dc,4)==struct.pack('<2H',0,255),
            'native semaphore automatic ID bounds changed')
    require(u32(machine,SEM_TABLE)==SEM_OBJECT,'semaphore slot1 pointer changed')
    for pc,root in ROOT_LOADS:
        require(machine.read(pc,6)==b'\xfc\xcd'+struct.pack('<I',root),
                'native initializer root-address instruction changed')
    counts = bytearray(32)
    struct.pack_into('<H',counts,4,1)  # Next candidate1, used0; other object classes unused here.
    rows = [Region('shared_bit_single_contender',0x8fe00000,bytes(1),'rw',True),
        Region('empty_pending_list',0xa2793e80,b'\xff'*4,'r'),
        Region('selected_task',0x621a6334,struct.pack('<I',TCB),'rw',True),
        Region('allocation_counts',COUNTS,bytes(counts),'rw',True),
        Region('semaphore_slot_1',SEM_OBJECT,bytes(36),'rw',True),
        Region('peer_root_cells',0x8ff00008,struct.pack('<2I',*(r for r,_ in PEER_ROOTS))),
        Region('dispatch_enabled',0x621a6320,bytes(1),'rw',True),
        Region('highest_ready_head',0x621a63ac,struct.pack('<I',0x62192400)),
        Region('only_ready_task',0x62192400,struct.pack('<2I',TCB,TCB))]
    # One running task is linked into the first native ready-list header.
    # This supplies a coherent no-switch path instead of disabling scheduling.
    machine.mutate('tcb',0,struct.pack('<2I',0x62192400,0x62192400))
    machine.mutate('tcb',12,struct.pack('<H',1))
    for index,(root,pending) in enumerate(PEER_ROOTS,1):
        require(u32(machine,root+332)==pending and u32(machine,root+380)==3,
                'peer root pending-list fields changed')
        rows.append(Region(f'peer_{index}_pending_empty',pending,b'\xff'*4))
    queues = []
    for handle,maximum,ring in QUEUES:
        address = u32(machine,QUEUE_TABLE+4*(handle-1))
        header = bytearray(36)
        backing = 0x19800000+handle*0x4000
        struct.pack_into('<H',header,0,handle)
        struct.pack_into('<4I',header,20,128,maximum,ring,backing)
        rows.append(Region(f'queue_{handle:x}',address,bytes(header),'r'))
        queues.append(dict(handle=hex(handle),object=hex(address),attributes=128,maximum=maximum,
                           ring_bytes=ring,backing=hex(backing),backing_mapped=False))
    for row in rows:
        require(row.name not in machine.regions,'fixture name collision')
        machine.regions[row.name] = row
    return queues


def released(machine):
    require(machine.regions['shared_bit_single_contender'].data==bytes(1) and
            machine.regions['lock_cell'].data==bytes(4),'native critical path retained its shared/local lock')


def unpublished(machine,syms):
    require(u32(machine,syms['_ep7_native_runtime_slot'])==0,'failed bootstrap published a runtime')


def bootstrap_context(directory,prefix,engine,prepare_kernel=None,*,candidate_override=None):
    """Reach the real create boundary, then supply the explicit S2 kernel fixture."""
    data,syms,build = candidate_inputs(directory,prefix) if candidate_override is None else candidate_override
    base = Machine(data,engine)
    if prepare_kernel is not None:
        queues = fixture(base)
        prepare_kernel(base,syms)
    returned(base.run(CLEAR_SITE,CLEAR_RESUME),CLEAR_RESUME)
    returned(base.run(INIT_SITE,INIT_RESUME,overrides={'d0':0}),INIT_RESUME)
    front = base.run(BOOT_SITE,ORIGINAL_BOOT,breakpoints=[CREATE,syms['_ep7_gcc_quarantine']],full_trace=True)
    require(front['status']=='breakpoint' and front['registers']['pc']==CREATE,
            'candidate no longer reaches the actual native-create boundary')
    if prepare_kernel is None:
        queues = fixture(base)
    return base,front,syms,build,queues


def publish_runtime(base,front,syms):
    """Return the machine initialized by candidate/native code, without failure probes."""
    create_return = front['registers']['mdr']
    success = base.clone()
    created = success.resume(front['registers'],create_return,full_trace=True,
                             breakpoints=[syms['_ep7_gcc_quarantine']],limit=3000)
    require(created['status']=='returned' and created['registers']['d0']==1 and
            created['registers']['sp']==front['registers']['sp']+16,'native create did not return owned ID1')
    require(struct.unpack('<H',success.read(SEM_OBJECT,2))[0]==1 and
            struct.unpack('<4I',success.read(SEM_OBJECT+12,16))==(0,1,1,1) and
            struct.unpack('<2I',success.read(SEM_OBJECT+4,8))==(SEM_OBJECT+4,SEM_OBJECT+4) and
            struct.unpack('<H',success.read(COUNTS+6,2))[0]==1,
            'native create did not allocate and initialize the expected semaphore')
    released(success)
    published = success.resume(created['registers'],ORIGINAL_BOOT,full_trace=True,
        breakpoints=[DELETE,syms['_ep7_gcc_quarantine']],limit=60000)
    require(published['status']=='returned','successful bootstrap did not tail-transfer to the original entry')
    runtime = u32(success,syms['_ep7_native_runtime_slot'])
    require(RAM_START<=runtime<RAM_START+RAM_BYTES,'published runtime is outside private storage')
    expected = dict(success.initial,sp=SP-4,mdr=BOOT_SITE+7)
    checked = ('d0','d1','d2','d3','a0','a1','a2','a3','sp','mdr','psw')
    require(all(published['registers'][name]==expected[name] for name in checked),
            'bootstrap bridge changed the original callee entry register/frame contract')
    # LIR/LAR are deliberately not asserted: native create uses its real SETLB
    # loop, and the reviewed Usr3 prefix has no live native loop dependency.
    queries = []
    for name,argument,wanted in [('_ep7r_get',syms['_ep7_native_runtime_slot'],runtime),
                                ('_ep7r_accepting',runtime,1),('_ep7r_io_open',runtime,1)]:
        result = success.call(syms[name],overrides={'d0':argument})
        returned(result,CALLER+7)
        require(result['registers']['d0']==wanted,'published runtime query rejected current actual state '+name)
        queries.append(dict(symbol=name,result=brief(result),returned_d0=hex(wanted)))
    released(success)
    return success,created,published,queries


def inspect(directory,prefix,engine):
    base,front,syms,build,queues = bootstrap_context(directory,prefix,engine)
    success,created,published,queries = publish_runtime(base,front,syms)
    runtime = u32(success,syms['_ep7_native_runtime_slot'])
    checked = ('d0','d1','d2','d3','a0','a1','a2','a3','sp','mdr','psw')
    create_return = front['registers']['mdr']
    exhausted = base.clone()
    exhausted.mutate('allocation_counts',6,struct.pack('<H',255))
    # Exhaustion must return from the count guard; no semaphore slot is mapped.
    del exhausted.regions['semaphore_slot_1']
    exhausted_create = exhausted.resume(front['registers'],create_return,full_trace=True,limit=3000)
    require(exhausted_create['status']=='returned' and signed(exhausted_create['registers']['d0'])==-34,
            'native exhausted allocator did not return -34 without touching an object')
    exhausted_end = exhausted.resume(exhausted_create['registers'],ORIGINAL_BOOT,full_trace=True,
        breakpoints=[CREATE,DELETE,syms['_ep7_gcc_quarantine']],limit=3000)
    require(exhausted_end['status']=='breakpoint' and
            exhausted_end['registers']['pc']==syms['_ep7_gcc_quarantine'] and
            exhausted_end['registers']['d0']==0xf04,'create failure did not quarantine without delete/retry')
    unpublished(exhausted,syms)
    released(exhausted)

    bad_queue = base.clone()
    bad_queue.mutate('queue_4c',24,struct.pack('<I',300))
    bad_created = bad_queue.resume(front['registers'],create_return,full_trace=True,limit=3000)
    require(bad_created['status']=='returned' and bad_created['registers']['d0']==1,
            'queue-rejection case did not acquire its own native semaphore')
    cleanup = bad_queue.resume(bad_created['registers'],ORIGINAL_BOOT,full_trace=True,
        breakpoints=[DELETE,syms['_ep7_gcc_quarantine']],limit=60000)
    require(cleanup['status']=='breakpoint' and cleanup['registers']['pc']==DELETE and
            cleanup['registers']['d0']==1,'failed queue publication did not delete its owned ID1')
    unpublished(bad_queue,syms)
    delete_return = cleanup['registers']['mdr']
    deleted = bad_queue.resume(cleanup['registers'],delete_return,full_trace=True,limit=3000)
    require(deleted['status']=='returned' and deleted['registers']['d0']==0 and
            bad_queue.read(SEM_OBJECT,2)==bytes(2) and bad_queue.read(COUNTS+6,2)==bytes(2),
            'native delete did not retire ID1 and decrement its allocation count')
    failed_end = bad_queue.resume(deleted['registers'],ORIGINAL_BOOT,full_trace=True,
        breakpoints=[CREATE,DELETE,syms['_ep7_gcc_quarantine']],limit=3000)
    require(failed_end['status']=='breakpoint' and failed_end['registers']['pc']==syms['_ep7_gcc_quarantine'] and
            failed_end['registers']['d0']==0xf05,'publication failure did not terminate after native rollback')
    unpublished(bad_queue,syms)
    released(bad_queue)

    parts = [summary(front),summary(created),summary(published)]
    return dict(scope=__doc__,candidate_build_revision=build['source_revision'],
        candidate_object_revision=build.get('object_source_revision',build['source_revision']),
        actual_elf_code_equals_decoded_candidate=True,all_assertions_passed=True,
        hash_checks_performed=False,engine=str(engine),
        root_fields_checked={str(offset):hex(value) for offset,value in ROOT_WORDS.items()},
        root_address_instruction_checks=[dict(pc=hex(pc),root=hex(root)) for pc,root in ROOT_LOADS],
        peer_pending_list_fixtures=[dict(root=hex(root),pending=hex(pending),first_word='0xffffffff')
                                   for root,pending in PEER_ROOTS],
        queue_header_fixtures=queues,
        native_create_success=dict(result=summary(created),handle=1,object=hex(SEM_OBJECT),
            attributes_initial_maximum_count=[0,1,1,1],empty_native_wait_list=True,used_count=1,locks_released=True),
        successful_bootstrap=dict(prefix=summary(front),after_create=summary(published),
            total_instructions=sum(row['completed'] for row in parts),
            executed_path_stack_depth_from_hook_sp=max(row['observed_stack_depth_from_hook_sp'] for row in parts),
            runtime_address=hex(runtime),original_entry=hex(ORIGINAL_BOOT),
            original_entry_registers_checked=list(checked),runtime_queries=queries,
            original_stock_initializer_executed=False),
        native_exhaustion=dict(create=summary(exhausted_create),candidate_rejection=summary(exhausted_end),
            native_status=-34,quarantine_reason='0xf04',semaphore_object_unmapped=True,runtime_unpublished=True),
        queue_mismatch_rollback=dict(handle='0x4c',fixture_maximum=300,required_maximum=312,
            created=summary(bad_created),to_delete=summary(cleanup),native_delete=summary(deleted),
            candidate_rejection=summary(failed_end),quarantine_reason='0xf05',
            native_semaphore_id_cleared=True,native_used_count_after=0,locks_released=True,runtime_unpublished=True),
        api_success_stubs=False,firmware_files_modified=False,hardware_executed=False,
        full_boot_executed=False,installable=False,
        limits=['The shared byte at 8fe00000 is ordinary read/write fixture storage with one contender. Real bus atomicity, peers, IRQ timing and physical locking are unproven.',
                'Task, its single-node ready list, all three empty pending-list sentinels, root cells, allocator counters and five already-initialized queue headers are explicit fixtures; their earlier real boot initialization is not executed.',
                'Semaphore and queue object addresses come from the original unchanged ROM pointer tables. Queue backing addresses are synthetic and deliberately unmapped: no queue I/O runs here.',
                'All semaphore creation/deletion and critical helpers execute original candidate/native instructions, including their failure returns; no API body or return value is replaced.',
                'The normal run ends at the original initializer entry after restoring its call frame. It does not execute that initializer, task startup, the capture/worker chain or hardware.',
                'Observed stack depth is only for these executed paths; full IRQ/alternate-context bounds, placement/load ownership and recovery remain open.'])


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.candidate,args.tool_prefix,args.engine),indent=2))
