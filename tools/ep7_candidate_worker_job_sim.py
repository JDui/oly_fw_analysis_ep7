#!/usr/bin/env python3
"""Execute final worker allocation/register/revoke/ACK seams with native pool code.

Old constructor/conversion/processing completions are explicit bounded inputs.
This checks candidate lifetime ordering, not original ISP or image correctness.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import STACK,require
from ep7_candidate_static_kernel_sim import inspect as static_kernel
from ep7_candidate_state_sim import guarded,job_fixture,STOCK,EXTENT,OUTPUT_BYTES
from ep7_candidate_ui_owner_sim import OwnerMachine
from ep7_candidate_relay_sim import task_fixture
from penf_boot_emulator import BootState,HOOK_RETURN
from penf_emulator import Region
from ep7_sim_probe import brief

WORK_SP=STACK+4096
DESCRIPTOR=WORK_SP+4
SCOPE=WORK_SP-104
METADATA=0x19500000
SETTINGS,SNAPSHOT,TICKET,NATIVE,WIRE,WRITTEN,SETUP,OUTPUT=(0x19501000,0x19501100,
    0x19501200,0x19502000,0x19503000,0x19504000,0x19505000,0x19506000)
POOL=0x61bd6d40
POOL_COUNTS,RECYCLE,BITMAP=0x62038118,0x62039c70,0x62039ea4
ALLOCATE,ALLOCATE_RETURN,FREE,FREE_RETURN=0x60022700,0x6002272f,0x60022732,0x60353cf0
CONSTRUCTOR_COMPLETED=0x603537fa
PROCESS,CLEANUP=0x603e61b8,0x603e6c8d
LOGS={0x603e2c0d,0x603e4e82}
COMPLETIONS={0x603e611e:0,0x603e62d1:0,0x603ed4bd:1,
             0x603e6b83:0,0x603ed7e2:0,0x603f2ad0:0,0x603eebe9:0}


def original_instruction(m,stop):
    result=m.advance(stop,set())
    m.nested.append(dict(entry=hex(result['trace'][0]['pc']),execution=[brief(result)],
        instructions=result['completed'],minimum_sp=hex(min(t['sp'] for t in result['trace'])),
        native_private_lock_calls=[]))


def boundary_return(m):
    pc=m.regs['pc']
    m.events.append(dict(kind='original_completion_model',entry=hex(pc)))
    BootState.return_from_model(m,COMPLETIONS.get(pc,0))


def allocation_enter(m):
    require(m.regs['d0']==EXTENT and m.word(SCOPE)==4,
            'qualified worker did not request expanded extent exactly once')
    m.events.append(dict(kind='native_allocation_entry',requested=m.regs['d0']))
    original_instruction(m,ALLOCATE+4)


def allocation_return(m):
    require(m.regs['a0']==POOL and m.word(POOL_COUNTS+8)==1 and m.word(BITMAP)==1,
            'actual pool did not allocate its fresh class2 slot')
    guarded(m,'worker_job',POOL,b'\xa5'*EXTENT)
    m.events.append(dict(kind='native_allocation_return',address=hex(POOL),owned_extent=EXTENT))
    # Internal native calls clobber MDR; RET[],4 consumes its saved stack RA.
    original_instruction(m,m.word(m.regs['sp']+4))


def constructor_completion(m):
    require(m.regs['a0']==POOL and m.word(SCOPE)==2 and
            m.word(SCOPE+32)==POOL and m.word(SCOPE+36)==EXTENT and
            m.read(POOL,STOCK)==b'\xa5'*STOCK and m.read(POOL+STOCK,24)==bytes(24),
            'allocator bridge did not preserve stock bytes/zero its new trailer')
    # Reuse the existing bounded direct-reader fixture, relocating its three
    # self-pointers. This is explicitly the old constructor/conversion contract.
    job=bytearray(job_fixture()[:STOCK])
    struct.pack_into('<I',job,11368,POOL+14576)
    struct.pack_into('<I',job,14576,POOL)
    struct.pack_into('<I',job,14584,POOL+11364)
    m.write(POOL,job)
    result=m.word(m.regs['sp']+16)
    m.write(result,bytes(2))
    m.events.append(dict(kind='constructor_completion_model',stock_bytes=STOCK,
                         trailer_untouched=True,result=hex(POOL)))
    m.regs.update(pc=0x603537eb,mdr=0x603f2845)
    BootState.return_from_model(m,POOL)


def process_completion(m):
    require(m.regs['a0']==DESCRIPTOR and m.word(SCOPE)==3 and
            m.read(SCOPE+40,8)!=bytes(8) and m.read(POOL+STOCK,24)==m.frozen[1:],
            'actual process bridge did not register matching frozen allocation')
    saved=dict(m.regs)
    m.events.append(dict(kind='original_process_completion_model',job=hex(POOL),
                         registered_token=m.read(SCOPE+40,8).hex()))
    observed=m.call_native(m.syms['ep7_native_postbuilder_bridge'],
        values=dict(sp=saved['sp']-256,a2=SETUP),entry=0x603b02d9,stop=0x603b02de)
    require(tuple(m.regs[k] for k in ('d0','d1','a0','a1'))==
            (0x77887788,0x55665566,0x11221122,0x33443344),
            'installed postbuilder veneer changed original volatile results')
    m.nested.append(observed)
    held=m.call_native(m.syms['_ep7_gcc_raw_sem_poll'],values=dict(sp=saved['sp']-256,d0=133))
    require(held['d0']=='0x0' and m.word(m.setup['private_object']+24)==0,
            'could not establish native busy-lock input')
    m.nested.append(held)
    m.cleanup_waits=0
    m.events.append(dict(kind='cleanup_contention_injected_by_native_poll',handle=133))
    m.regs=saved
    # This is a tail-delegated native frame, so the preceding C observer may
    # have clobbered MDR. The real return is W+24, not a direct CALL to PROCESS.
    require(m.word(saved['sp']+24)==0x603f2897,'native process return frame changed')
    m.write(HOOK_RETURN,bytes.fromhex('dfb018')+b'\xcb'*5)
    m.regs.update(pc=HOOK_RETURN,d0=0)


def cleanup_progress(m):
    require(m.regs['d0']==1 and m.cleanup_waits==0 and m.word(SCOPE)==4 and
            m.read(SCOPE+40,8)!=bytes(8) and 'worker_job' in m.regions and
            not any(e['kind']=='native_cleanup_after_revoke' for e in m.events) and
            m.word(m.setup['provider']+20)==0,
            'busy cleanup released storage or waited while owning provider lock')
    saved=dict(m.regs)
    m.cleanup_waits+=1
    signalled=m.call_native(m.syms['_ep7_gcc_raw_sem_signal'],
                            values=dict(sp=saved['sp']-256,d0=133))
    require(signalled['d0']=='0x0','contention-release model could not signal native lock')
    m.nested.append(signalled)
    m.events.append(dict(kind='ordinary_task_progress_model',delay_units=1,
        live_job_retained=True,token_retained=True,native_signal_released_contention=True))
    m.regs=saved
    BootState.return_from_model(m,0)


def builder_completion(m):
    require(m.regs['a2']==SETUP,'postbuilder lost original setup register')
    m.events.append(dict(kind='original_color_builder_completion_model',output=hex(OUTPUT)))
    # Distinct original volatile results must survive the candidate observer.
    m.regs.update(a0=0x11221122,a1=0x33443344,d1=0x55665566)
    BootState.return_from_model(m,0x77887788)


def cleanup_enter(m):
    require(m.regs['a0']==DESCRIPTOR and m.word(SCOPE)==4 and m.read(SCOPE+40,8)==bytes(8),
            'candidate entered native cleanup before releasing its registered job')
    m.events.append(dict(kind='native_cleanup_after_revoke',job_token_zero=True))
    original_instruction(m,CLEANUP+1)


def free_enter(m):
    require(m.regs['a0']==POOL and m.read(SCOPE+40,8)==bytes(8),
            'original pool free reached with live registered job')
    m.events.append(dict(kind='native_free_after_revoke',address=hex(POOL)))
    original_instruction(m,FREE+2)


def free_return(m):
    require(m.word(BITMAP)==0 and m.word(POOL_COUNTS+20)==1 and m.read(RECYCLE,2)==bytes(2),
            'native pool did not recycle the exact job slot')
    del m.regions['worker_job']
    m.events.append(dict(kind='native_free_completed',payload_unmapped=True))
    original_instruction(m,FREE_RETURN+1)


def ack_output(m):
    require(m.read(DESCRIPTOR+300,12)==bytes(12) and 'worker_job' not in m.regions,
            'original ACK preceded candidate ticket retirement/job free')
    require(m.regs['d1']==12,'original ACK changed its message extent')
    m.events.append(dict(kind='ack_queue_output_model',handle=m.regs['d0'],
                         packet=m.read(m.regs['a0'],12).hex()))
    BootState.return_from_model(m,0)


def worker_return(m):
    require(m.regs['sp']==WORK_SP and m.regs['d0']==0 and m.regs['d2']==8124 and
            m.regs['d3']==0x2006 and m.regs['a2']==DESCRIPTOR and
            m.regs['a3']==m.initial['a3'],'actual worker wrapper changed original return ABI')
    m.events.append(dict(kind='native_worker_wrapper_return',status=0,original_abi_preserved=True))
    original_instruction(m,0x603f272a)


def worker_context(directory,prefix,engine,*,runtime_context=None):
    if runtime_context is None:
        base,syms,build,setup=static_kernel(directory,prefix,engine,context_only=True)
    else:
        base,syms,build,setup=runtime_context
    m=object.__new__(OwnerMachine)
    m.engine,m.regions,m.initial=base.engine,dict(base.regions),dict(base.initial)
    m.configure(syms)
    m.nested=[]
    m.setup=setup
    task_fixture(m,0x6c,0x600395a0,0x603f26a1,26,8192)
    code=m.regions['candidate'].data
    m.regions['native_helper']=Region('native_helper',0x47000800,
        code[0x6143ca00-0x60020020:0x6143e200-0x60020020],'rx')
    m.regions['boundary_return']=Region('boundary_return',HOOK_RETURN,b'\xcb'*8,'rx')
    for name,address,data in (
        ('worker_settings',SETTINGS,bytes([3,0,254]+[0]*9+[0,0,252]+[0]*9)),
        ('worker_snapshot',SNAPSHOT,b'\xcc'*25),('worker_ticket',TICKET,b'\xcc'*12),
        ('worker_native_descriptor',NATIVE,bytes(300)),('worker_wire_descriptor',WIRE,b'\xcc'*312),
        ('worker_written',WRITTEN,b'\xcc'*4),('worker_setup',SETUP,struct.pack('<4I',0,POOL+11364,0,OUTPUT)),
        ('worker_output',OUTPUT,b'\x5a'*OUTPUT_BYTES)):
        guarded(m,name,address,data)
    rows=[Region('pool_counts',POOL_COUNTS,bytes(24),'rw',True),
        Region('pool_bitmap',BITMAP,bytes(8),'rw',True),
        Region('pool_recycle',RECYCLE,b'\xa5'*128,'rw',True),
        Region('pool_kernel_marker',0x8ff006fc,struct.pack('<I',0x77777777)),
        Region('pool_restore_mask',0x8ff00040,bytes(4))]
    for row in rows:
        require(all(row.address+len(row.data)<=r.address or row.address>=r.address+len(r.data)
                    for r in m.regions.values()),'worker fixture overlaps existing region '+row.name)
        m.regions[row.name]=row
    calls=[m.gcc('_ep7p_edit',[setup['core'],0,SETTINGS]),
           m.gcc('_ep7p_capture',[setup['core'],11,1,SNAPSHOT])]
    m.frozen=m.read(SNAPSHOT,25)
    calls.append(m.gcc('_ep7t_prepare',[setup['runtime']+8,METADATA,SNAPSHOT,TICKET]))
    ticket=struct.unpack('<3I',m.read(TICKET,12))
    require(ticket==(METADATA,1,0),'fresh transport ticket differs')
    # MN103 GCC passes this by-value aggregate via an invisible reference.
    calls.append(m.gcc('_ep7t_publish',[setup['runtime']+8,TICKET]))
    m.write(NATIVE+48,struct.pack('<II',METADATA,19))
    m.write(NATIVE+194,struct.pack('<H',0x2001))
    m.write(NATIVE+32,struct.pack('<I',0x55))
    calls.append(m.gcc('_ep7w_encode',[300,NATIVE,TICKET,WIRE,312,WRITTEN]))
    require(all(r['d0']=='0x1' for r in calls) and m.word(WRITTEN)==312,
            'core freeze/transport prepare/publish/wire encoding failed')
    m.write(DESCRIPTOR,m.read(WIRE,312))
    m.boundaries={**{p:boundary_return for p in LOGS|set(COMPLETIONS)},
        ALLOCATE:allocation_enter,ALLOCATE_RETURN:allocation_return,
        CONSTRUCTOR_COMPLETED:constructor_completion,PROCESS:process_completion,
        syms['ep7_stock_color_builder_unresolved']:builder_completion,
        CLEANUP:cleanup_enter,FREE:free_enter,FREE_RETURN:free_return,0x603eeba4:ack_output}
    m.boundaries.update({syms['ep7_stock_task_delay_unresolved']:cleanup_progress,0x603f2727:worker_return})
    return m,syms,build,setup,calls


def inspect(directory,prefix,engine):
    m,syms,build,setup,calls=worker_context(directory,prefix,engine)
    work=m.call_native(syms['ep7_native_worker_scope_bridge'],
        values=dict(sp=WORK_SP,a2=DESCRIPTOR,d0=0,d2=8124,d3=0x2006),
        entry=0x603f2721,stop=0x603f2770,preserved=('d3','a2','a3'))
    worker_calls=[work,*m.nested]
    calls+=worker_calls
    require(work['d0']=='0x1' and m.regs['d2']==0 and
            m.regs['psw']&0xf00==m.initial['psw']&0xf00 and m.cleanup_waits==1,
            'worker/ACK status, IRQ level or bounded cleanup retry differs')
    expected=bytearray(b'\x5a'*OUTPUT_BYTES)
    coefficients=[dict(axis='H',sector=0,offset=706,value=-3000),
                  dict(axis='H',sector=2,offset=730,value=2000),
                  dict(axis='L',sector=2,offset=734,value=-150)]
    for patch in coefficients:
        struct.pack_into('<h',expected,patch['offset'],patch['value'])
    require(m.read(OUTPUT,OUTPUT_BYTES)==expected,'registered worker produced wrong CPU coefficient bytes')
    require(m.read(DESCRIPTOR+300,12)==bytes(12) and
            m.read(setup['runtime']+8+28,44*8)==bytes(44*8) and
            m.word(setup['runtime']+8+20)==1 and 'worker_job' not in m.regions,
            'ACK left a ticket/transport entry or job lifetime behind')
    sequence=['native_allocation_entry','native_allocation_return','constructor_completion_model',
        'original_process_completion_model','cleanup_contention_injected_by_native_poll',
        'ordinary_task_progress_model','native_cleanup_after_revoke','native_free_after_revoke',
        'native_free_completed','native_worker_wrapper_return','ack_queue_output_model']
    positions=[]
    for kind in sequence:
        matches=[i for i,e in enumerate(m.events) if e['kind']==kind]
        require(len(matches)==1,'worker lifecycle boundary missing/repeated '+kind)
        positions+=matches
    require(positions==sorted(positions),'native lifecycle ordering differs')
    ack=next(e for e in m.events if e['kind']=='ack_queue_output_model')
    packet=bytes.fromhex(ack['packet'])
    require(packet[:2]==bytes(2) and packet[4:]==struct.pack('<II',0,METADATA),
            'original ACK lost its status/identity fields')
    m.write(OUTPUT,b'\x5a'*OUTPUT_BYTES)
    late=m.call_native(syms['ep7_native_postbuilder_bridge'],values=dict(sp=WORK_SP,a2=SETUP),
                       entry=0x603b02d9,stop=0x603b02de)
    require(m.read(OUTPUT,OUTPUT_BYTES)==b'\x5a'*OUTPUT_BYTES,
            'retired/unmapped job still supplied H/L to late observer')
    calls.append(late)
    lock_calls=[c for row in calls for c in row['native_private_lock_calls']]
    require(all(c['handle']==133 for c in lock_calls) and
            sum(c['status']==(0xffffffff-49) for c in lock_calls)==1 and
            all(c['status'] in (0,0xffffffff-49) for c in lock_calls) and
            m.word(setup['private_object']+24)==1 and m.word(setup['provider']+20)==0 and
            m.read(setup['provider']+24,1)==b'\0','worker private lock did not recover cleanly')
    return dict(scope=__doc__,status='passed',candidate_build_revision=build['source_revision'],
        instructions_including_boundary_returns=sum(r['instructions'] for r in calls),
        maximum_observed_worker_stack=WORK_SP-min(int(r['minimum_sp'],16) for r in worker_calls),
        calls=calls,runtime_setup=setup,events=m.events,cpu_coefficient_writes=coefficients,
        native_private_lock_operations=len(lock_calls),cleanup_busy_status=-50,cleanup_progress_calls=1,
        allocation=dict(address=hex(POOL),requested=EXTENT,stock_bytes_preserved_before_completion_model=True,
                        newly_requested_trailer_zeroed=True,original_pool_allocated=True,original_pool_recycled=True),
        original_ack=ack,transport_entries_empty_after_ack=True,late_observer_after_free_unchanged=True,
        historical_probe_fixes=['By-value ep7t_ticket uses an invisible-reference argument, not three scalar ABI words.',
            'At allocator RET, use saved stack RA rather than callee-clobbered MDR.',
            'Process is a tail-delegated native frame; completion RET uses original b0/24 frame and603f2897.',
            'Whole task slice changes D2 to completion status; separately verify full wrapper ABI at603f2727.'],
        boundaries=['Production static semaphore initialization/create/publication reused; task6c/8KiB stack is an explicit handover fixture.',
            'Snapshot/transport/wire APIs execute; descriptor delivery here is modeled, with opaque metadata and ACK handle55.',
            'Worker preflight success and old parameter/conversion/postprocess completions modeled; no original image/metadata construction claim.',
            'Original constructor starts and reaches actual allocator; remaining stock15488 bytes supplied by existing bounded decoder fixture.',
            'Original processor completion invokes actual installed postbuilder site; old COLOR builder output completion modeled.',
            'Fresh domain0 class2 pool counters/bitmap and recycled storage are explicit inputs; allocator/free and active-kernel lock instructions execute.',
            'One real poll133 injects contention; ordinary delay completion models another participant releasing it via actual signal133.',
            'Original job destructor/descriptor cleanup/ACK message construction execute; original ACK queue handoff is intercepted.',
            'Observed stack includes a chosen256B processing boundary frame, excluding original processing/ISP/IRQ upper bounds.',
            'No full photo pixels, multicore scheduling, residency ownership or recovery qualification is inferred.'],
        hash_checks_performed=False,hardware_executed=False,installable=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--tool-prefix',required=True)
    p.add_argument('--engine',type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(inspect(args.candidate,args.tool_prefix,args.engine),indent=2))
