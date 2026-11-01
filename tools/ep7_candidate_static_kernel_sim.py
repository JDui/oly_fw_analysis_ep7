#!/usr/bin/env python3
"""Check linked H/L bootstrap after the native domain0 static semaphore recipe.

Executes original count copy, all semaphore ID clears and all 132 static
initializations. Other kernel classes, tasks, queues and single-contender locks
retain the existing explicit S2 fixtures; this is not a complete camera boot.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import CALLER, SP, RAM_START, RAM_BYTES, require
from ep7_candidate_publish_sim import (bootstrap_context, u32, released, unpublished,
    summary, COUNTS, SEM_TABLE, ORIGINAL_BOOT, DELETE, CREATE, BOOT_SITE)
from ep7_candidate_state_sim import (CALL_SP, INPUT, SNAPSHOT, guarded, gcc_call, summarize)
from ep7_candidate_message_sim import native_call, result_ok
from ep7_sim_probe import brief
from penf_emulator import Region


def inspect(directory, prefix, engine):
    initialization = []
    static = {}
    dynamic = 0

    def prepare(machine, syms):
        nonlocal dynamic
        require(u32(machine,0x600411a4+52)==0x6003c1f8 and
                u32(machine,0x600411a4+132)==0x6003999c and
                machine.read(0x6003c1fc,4)==struct.pack('<HH',133,132) and
                machine.read(0x6003294f,5)==bytes.fromhex('cd0901b010'),
                'native count source or semaphore initialization CALL changed')
        machine.regions['allocation_counts'] = replace(machine.regions['allocation_counts'],data=b'\xa5'*60)
        del machine.regions['semaphore_slot_1']
        descriptors = []
        for index in range(256):
            row = struct.unpack('<4I',machine.read(0x6003999c+16*index,16))
            if not row[0]:
                break
            descriptors.append(row)
        require(len(descriptors)==132 and {r[0]&0xfff for r in descriptors}==set(range(1,133)),
                'native static semaphore set changed')
        for handle in range(1,256):
            address = u32(machine,SEM_TABLE+(handle-1)*4)
            size = 36 if handle==133 else 28 if handle<=132 else 2
            require(all(address+size<=r.address or address>=r.address+len(r.data)
                        for r in machine.regions.values()), 'semaphore mapping overlaps another object')
            machine.regions[f'static_kernel_sem_{handle}'] = Region(
                f'static_kernel_sem_{handle}',address,b'\xa5'*size,'rw',True)
        dynamic = u32(machine,SEM_TABLE+132*4)
        counts = machine.run(0x60032622,0x60032651,
            overrides=dict(sp=CALL_SP,d3=0x8ff00004),full_trace=True,limit=1000)
        result_ok(machine,counts,0x60032651,CALL_SP)
        require(machine.read(COUNTS,60)==machine.read(0x6003c1f8,60), 'native count copy differs')
        cleared = machine.run(0x60035654,0x6003567f,
            overrides=dict(sp=CALL_SP,d3=0x600410d8,d2=0x8ff00004),full_trace=True,limit=5000)
        result_ok(machine,cleared,0x6003567f,CALL_SP)
        require(all(machine.read(u32(machine,SEM_TABLE+4*i),2)==bytes(2) for i in range(255)),
                'native free-ID initialization missed a slot')
        initialized = native_call(machine,syms,0x60032a58,0xb0,16,limit=15000)
        for handle, attributes, initial, maximum in descriptors:
            address = u32(machine,SEM_TABLE+((handle&0xfff)-1)*4)
            expected = struct.pack('<HH6I',handle,4,address+4,address+4,
                                   attributes,initial,maximum,initial)
            require(machine.read(address,28)==expected, 'native static semaphore differs '+hex(handle))
            static[address] = expected
        require(machine.read(dynamic,2)==bytes(2) and
                machine.read(COUNTS+4,4)==struct.pack('<HH',133,132), 'dynamic slot or counts changed early')
        initialization.extend(dict(name=name,**brief(result)) for name,result in
            [('native_all_object_count_recipe_copy',counts),('native_255_semaphore_ID_clear',cleared),
             ('complete_native_132_static_semaphore_initialize',initialized)])

    base, front, syms, build, queues = bootstrap_context(directory,prefix,engine,prepare_kernel=prepare)
    success = base.clone()
    created = success.resume(front['registers'],front['registers']['mdr'],full_trace=True,limit=3000)
    require(created['status']=='returned' and created['registers']['d0']==133 and
            created['registers']['sp']==front['registers']['sp']+16 and
            success.read(dynamic,2)==struct.pack('<H',133) and
            success.read(COUNTS+4,4)==struct.pack('<HH',133,133),
            'native dynamic semaphore allocation differs: '+str(dict(result=brief(created),
                d0=created['registers']['d0'],counts=success.read(COUNTS+4,4).hex(),
                object=success.read(dynamic,36).hex(),entry_sp=hex(front['registers']['sp']))))
    published = success.resume(created['registers'],ORIGINAL_BOOT,full_trace=True,limit=60000,
        breakpoints=[DELETE,syms['_ep7_gcc_quarantine']])
    require(published['status']=='returned', 'bootstrap refused production static semaphore context')
    expected = dict(success.initial,sp=SP-4,mdr=BOOT_SITE+7)
    require(all(published['registers'][name]==expected[name]
                for name in ('d0','d1','d2','d3','a0','a1','a2','a3','sp','mdr','psw')),
            'bootstrap changed original entry ABI')
    runtime = u32(success,syms['_ep7_native_runtime_slot'])
    boot = u32(success,runtime+4)
    core, provider = u32(success,boot+68),boot+40
    require(RAM_START<=core<boot<runtime<RAM_START+RAM_BYTES and
            u32(success,core)==provider and success.read(provider+16,2)==struct.pack('<H',133),
            'runtime/provider did not retain actual allocated ID133')
    settings = bytes([5]*12+[0xfd]*12)
    guarded(success,'settings',INPUT,settings)
    guarded(success,'snapshot',SNAPSHOT,b'\xcc'*25)
    edited = gcc_call(success,syms,'_ep7p_edit',[core,3,INPUT],wanted=1)
    frozen = gcc_call(success,syms,'_ep7p_capture',[core,11,4,SNAPSHOT],wanted=1)
    require(success.read(SNAPSHOT,25)==b'\x03'+settings and u32(success,dynamic+24)==1 and
            u32(success,provider+20)==0 and success.read(provider+24,1)==b'\0',
            'H/L edit/freeze did not release actual private lock')
    functions = [summarize('_ep7p_edit',edited),summarize('_ep7p_capture',frozen)]
    require(all(call['handle']==133 and call['returned_status']==0
                for row in functions for call in row['native_lock_calls']),
            'H/L path used an unexpected semaphore')
    require(all(success.read(address,len(data))==data for address,data in static.items()),
            'bootstrap or H/L modified an original static semaphore')
    released(success)

    # One decisive rollback case: the failed publication must delete ID133,
    # preserving all 132 original objects and their used-count reservation.
    failed = base.clone()
    failed.mutate('queue_4c',24,struct.pack('<I',300))
    stop = failed.resume(front['registers'],ORIGINAL_BOOT,full_trace=True,limit=60000,
        breakpoints=[DELETE,syms['_ep7_gcc_quarantine']])
    require(stop['status']=='breakpoint' and stop['registers']['pc']==DELETE and
            stop['registers']['d0']==133,'failed publication did not delete its actual owned ID')
    unpublished(failed,syms)
    retired = failed.resume(stop['registers'],ORIGINAL_BOOT,full_trace=True,limit=5000,
        breakpoints=[CREATE,syms['_ep7_gcc_quarantine']])
    require(retired['status']=='breakpoint' and retired['registers']['pc']==syms['_ep7_gcc_quarantine'] and
            retired['registers']['d0']==0xf05 and failed.read(dynamic,2)==bytes(2) and
            struct.unpack('<H',failed.read(COUNTS+6,2))[0]==132 and
            all(failed.read(address,len(data))==data for address,data in static.items()),
            'native rollback failed to preserve original static semaphore ownership')
    unpublished(failed,syms)
    released(failed)
    return dict(scope=__doc__,status='passed',candidate_build_revision=build['source_revision'],
        initialization=initialization,original_static_semaphores=132,free_IDs_initialized=255,
        initial_next_ID=133,private_ID=133,private_object=hex(dynamic),
        bootstrap_prefix=summary(front),native_create=summary(created),published=summary(published),
        runtime=hex(runtime),functions=functions,original_static_objects_unchanged=True,
        failed_publication=dict(to_delete=summary(stop),native_delete_and_quarantine=summary(retired),
            private_ID_cleared=True,original_used_count_restored=132),
        queue_headers=queues,hash_checks_performed=False,native_api_success_stubs=False,
        hardware_executed=False,firmware_files_modified=False,installable=False,
        limits=['Native initialization executes only the original all-class count-copy fragment, semaphore ID-clear fragment and complete static semaphore initializer.',
                'The current task, ready/pending lists, CPU/root cells, queue headers/backing identities and uncontended lock remain S2 fixtures; whole kernel startup is not claimed.',
                'No original static semaphore changes during successful private-lock use or failure rollback. This closes the ID1-only test assumption, not all task/concurrency/loading conditions.',
                'GUI delivery, photo pixels, cache/multicore timing, startup loading and independent recovery require separate evidence.'])


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.candidate,args.tool_prefix,args.engine),indent=2))
