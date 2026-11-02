#!/usr/bin/env python3
"""Check the stock 0x2002 worker cleanup route in actual candidate instructions.

Reuse the native bootstrap/lock engine and task fixture. Original dispatcher and
secondary worker CALLs construct real frames; the old processing bodies remain
explicit completion boundaries. This is not a full boot or message-origin test.
No SHA, peripheral access or firmware modification is performed.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import STACK, require
from ep7_candidate_static_kernel_sim import inspect as static_kernel
from ep7_candidate_relay_sim import task_fixture
from ep7_offline_candidate import BASE, CODE, ELF_NAME, IMAGE_NAME, symbols
from ep7_sim_probe import brief


def inspect(directory, prefix, engine, image=None, expect_rejection=False):
    build = json.loads((directory/'report.json').read_text(encoding='utf-8'))
    compiled = (directory/IMAGE_NAME).read_bytes()
    image = image or directory/IMAGE_NAME
    data = image.read_bytes()
    require(len(data)==len(compiled)==26214336, 'candidate image size changed')
    # Allows the retained GUI-isolated 007D image to be checked after the source
    # fix. Its executable banks must still match its supplied compiled build.
    require(all(data[a-BASE:b-BASE]==compiled[a-BASE:b-BASE] for a,b in CODE),
            'probe image code banks differ from supplied build')
    syms = {k:v['address'] for k,v in symbols(prefix,directory/ELF_NAME).items()}
    base, syms, _, _ = static_kernel(None,None,engine,context_only=True,
        candidate_override=(data,syms,build))
    task_fixture(base,0x6c,0x600395a0,0x603f26a1,26,8192)
    task_sp = STACK+4096
    descriptor = task_sp+4
    neutral = bytearray(312)
    struct.pack_into('<H',neutral,194,0x2002)
    struct.pack_into('<H',neutral,236,1)
    base.mutate('stack',descriptor-STACK,neutral)
    stop = syms['_ep7_gcc_quarantine']

    def legacy_context():
        m=base.clone()
        entry=m.run(0x603f2719,0x603ede1f,
            overrides=dict(sp=task_sp,a2=descriptor),full_trace=True,breakpoints=[stop])
        require(entry['status']=='returned' and entry['registers']['pc']==0x603ede1f,
                'original worker dispatcher CALL did not reach secondary route')
        u=entry['registers']['sp']
        # Explicit old prefix completion: exact stores at603ede1f/603ede5e and
        # temporary code rewrite603ede95..603ede9a; no H/L scope exists here.
        m.mutate('stack',u+12-STACK,struct.pack('<I',descriptor))
        m.mutate('stack',u+24-STACK,struct.pack('<H',0x2002))
        m.mutate('stack',descriptor+194-STACK,struct.pack('<H',0x2001))
        job=m.resume(dict(entry['registers'],pc=0x603edeb1),0x603f2800,
            full_trace=True,breakpoints=[stop])
        require(job['status']=='returned' and job['registers']['pc']==0x603f2800,
                'original unwrapped worker CALL did not reach stock job')
        return m,entry,job

    def cleanup(m, job, must_stop):
        # Old constructor/process completion preserves the native frame/A3.
        # Stop at the original cleanup entry: allocator/ISP/free are not modeled.
        result=m.resume(dict(job['registers'],pc=0x603f28bf,a3=descriptor),0x603e6c8d,
            full_trace=True,breakpoints=[stop])
        wanted=stop if must_stop else 0x603e6c8d
        require(result['fault'] is None and result['registers']['pc']==wanted,
                'unexpected cleanup outcome: '+str(brief(result)))
        if must_stop:
            require(result['status']=='breakpoint' and result['registers']['d0']==5,
                    'invalid ownership did not retain fault5')
        else:
            require(result['status']=='returned' and result['registers']['a0']==descriptor and
                    m.read(result['registers']['sp']+24,4)==struct.pack('<I',0x603f28c7),
                    'stock cleanup input/return frame changed')
        return dict(**brief(result),quarantine_reached=must_stop,
            quarantine_reason=5 if must_stop else None,
            original_cleanup_reached=not must_stop,
            descriptor_trailer=m.read(descriptor+300,12).hex())

    m,entry,job=legacy_context()
    before=m.regions['private'].data
    legal=cleanup(m,job,expect_rejection)
    if not expect_rejection:
        require(m.regions['private'].data==before,'neutral stock path modified H/L state')
    cases=[dict(name='neutral_stock_0x2002',dispatcher=brief(entry),
                secondary_call=brief(job),**legal)]

    # The fallback must not admit a ticket even with all three legacy PCs intact.
    tagged,_,job=legacy_context()
    tagged.mutate('stack',descriptor+300-STACK,b'E7T1'+struct.pack('<II',1,0))
    cases.append(dict(name='legacy_frame_with_nonzero_trailer_rejected',**cleanup(tagged,job,True)))

    # Construct the real owned-route wrapper (neutral descriptor, so no job is
    # registered), then corrupt only its return identity. This tests preservation
    # of layout rejection, not a claim of a complete registered-job lifetime.
    owned=base.clone()
    owned.mutate('stack',descriptor+194-STACK,struct.pack('<H',0x2001))
    job=owned.run(0x603f2721,0x603f2800,
        overrides=dict(sp=task_sp,a2=descriptor),full_trace=True,breakpoints=[stop])
    require(job['status']=='returned' and job['registers']['pc']==0x603f2800,
            'owned-route wrapper did not reach stock job')
    owned.mutate('stack',job['registers']['sp']+56-STACK,
                 struct.pack('<I',syms['_ep7_worker_native_return']+1))
    cases.append(dict(name='corrupted_wrapped_route_return_rejected',**cleanup(owned,job,True)))
    return dict(scope=__doc__,status='passed',input_image=str(image),
        candidate_build_revision=build['source_revision'],
        expectation='retained_007D_defect' if expect_rejection else '008_legacy_cleanup_fix',
        legacy_cleanup_fixed=not expect_rejection,cases=cases,
        stock_route=dict(dispatch_code='0x2002',dispatch_call='0x603f271a',
            secondary_call='0x603edeb3',cleanup_call='0x603f28c0',
            cleanup_frame_return_offsets={'24':'0x603f28c7','80':'0x603edeb8','124':'0x603f271f'},
            saved_descriptor_offset=92,saved_original_code_offset=104,descriptor_offset=128),
        hash_checks_performed=False,hardware_executed=False,full_boot_executed=False,
        limits=[
            'Native static bootstrap/private semaphore creation and publication execute with existing task/kernel fixtures.',
            'Dispatcher and secondary worker CALLs create actual native frames; old preflight/job body completion is explicit model input.',
            'No real 0x2002 startup message, scheduler, ISP, hardware reset cause or full device boot was observed.',
            'The corrupted wrapped-route check has no registered job; the separate worker probe validates owned allocation/revocation.'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--tool-prefix',required=True)
    p.add_argument('--engine',type=Path,required=True)
    p.add_argument('--image',type=Path)
    p.add_argument('--expect-rejection',action='store_true')
    p.add_argument('--report',type=Path)
    a=p.parse_args()
    result=inspect(a.candidate,a.tool_prefix,a.engine,a.image,a.expect_rejection)
    output=json.dumps(result,indent=2)+'\n'
    if a.report:a.report.write_text(output,encoding='utf-8')
    print(output,end='')
