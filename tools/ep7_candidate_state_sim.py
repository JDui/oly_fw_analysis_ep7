#!/usr/bin/env python3
"""Run linked H/L state and frozen CPU-reader paths with the real native private lock.

Reuses the S2 candidate-published runtime. Direct API callers, owned input/job
buffers and a single-task kernel are explicit fixtures, not camera execution.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import CALLER, STACK, SP, RAM_START, RAM_BYTES, require
from ep7_candidate_publish_sim import (bootstrap_context, publish_runtime, u32, signed,
                                     released, SEM_OBJECT)
from ep7_sim_probe import brief
from penf_emulator import Region

CALL_SP = SP-64  # Room for GCC outgoing arguments within the existing guarded stack.
INPUT, SNAPSHOT, TOKEN, OUTPUT, JOB, SETUP = (0x19100000,0x19100100,0x19100200,
                                          0x19101000,0x19600000,0x19100300)
STOCK, EXTENT, OUTPUT_BYTES = 15488,15512,976
POLL, SIGNAL, GET_TID = 0x600370af,0x60035b62,0x600317ac


def gcc_call(machine,syms,name,args=(),*,wanted=None,limit=15000):
    """GCC word ABI: D0/D1, then SP+12; CALL [],0 does not change SP."""
    words = [value & 0xffffffff for value in args]
    if len(words)>2:
        machine.mutate('stack',CALL_SP+12-STACK,struct.pack('<'+'I'*(len(words)-2),*words[2:]))
    machine.regions['caller'] = Region('caller',CALLER,
        b'\xdd'+struct.pack('<i',syms[name]-CALLER)+bytes(2),'rx')
    registers = dict(sp=CALL_SP)
    registers.update({reg:value for reg,value in zip(('d0','d1'),words)})
    result = machine.run(CALLER,CALLER+7,overrides=registers,full_trace=True,limit=limit,
                         breakpoints=[syms['_ep7_gcc_quarantine']])
    require(result['status']=='returned' and result['fault'] is None and
            result['registers']['sp']==CALL_SP,
            name+' did not return normally: '+str(brief(result)))
    require(all(result['registers'][r]==machine.initial[r] for r in ('d2','d3','a2','a3')),
            name+' changed a GCC callee-saved register')
    if wanted is not None:
        require(result['registers']['d0']==wanted & 0xffffffff,name+' returned unexpected D0')
    require(len(result['trace'])==result['completed'],'state trace truncated')
    released(machine)
    return result


def summarize(name,result):
    trace = result['trace']
    calls = []
    for index,row in enumerate(trace):
        if row['pc'] not in (POLL,SIGNAL):
            continue
        after = next((r for r in trace[index+1:] if r['pc']==row['mdr']),None)
        require(after is not None,'native lock call did not return to its real adapter')
        calls.append(dict(api='poll' if row['pc']==POLL else 'signal',
            handle=row['d0'],timeout=row['d1'] if row['pc']==POLL else None,
            returned_status=signed(after['d0'])))
    return dict(symbol=name,**brief(result),returned_d0=signed(result['registers']['d0']),
        stack_depth_from_call_sp=CALL_SP-min(result['registers']['sp'],min(r['sp'] for r in trace)),
        native_lock_calls=calls,native_get_tid_entries=sum(r['pc']==GET_TID for r in trace),
        context_switch_entries=sum(r['pc']==0x6003853e for r in trace))


def objects(machine,syms):
    runtime = u32(machine,syms['_ep7_native_runtime_slot'])
    boot = u32(machine,runtime+4)
    core = u32(machine,boot+68)
    provider = u32(machine,core)
    # 32-bit layouts are corroborated by the live initialized pointer chain,
    # the bootstrap's core/provider adjacency and final GCC op-table pointers.
    require(RAM_START<=core<boot<runtime<RAM_START+RAM_BYTES and
            boot-core==5052 and runtime-boot==72 and provider==boot+40 and
            machine.read(core+16,1)==b'\x01' and
            struct.unpack('<H',machine.read(provider+16,2))[0]==1,
            'initialized core/bootstrap/provider layout changed')
    return runtime,boot,core,provider


def ready_lock(machine,provider):
    require(u32(machine,SEM_OBJECT+24)==1 and u32(machine,provider+20)==0 and
            machine.read(provider+24,1)==b'\0','private lock not healthy and released')


def guarded(machine,name,address,data,permissions='rw'):
    for row in (Region(name+'_before',address-16,b'\x5a'*16),
                Region(name,address,data,permissions,permissions=='rw'),
                Region(name+'_after',address+len(data),b'\x5a'*16)):
        require(row.name not in machine.regions,'buffer name collision')
        machine.regions[row.name] = row


def job_fixture():
    """Reuse test_direct.c's exact bounded decoder fixture; no native constructor claim."""
    data = bytearray(EXTENT)
    struct.pack_into('<2H',data,11312,2,3)
    struct.pack_into('<2I',data,10984+24,0x6036884d,0)
    struct.pack_into('<2I',data,11364,0x60355fd4,JOB+14576)
    struct.pack_into('<H',data,11364+10,11)
    struct.pack_into('<H',data,11364+28,0x100)
    struct.pack_into('<I',data,14576,JOB)
    struct.pack_into('<I',data,14576+8,JOB+11364)
    data[STOCK:] = b'\x7e'*(EXTENT-STOCK)
    return bytes(data)


def inspect(directory,prefix,engine):
    base,front,syms,build,_ = bootstrap_context(directory,prefix,engine)
    machine,_,_,_ = publish_runtime(base,front,syms)
    runtime,boot,core,provider = objects(machine,syms)
    ready_lock(machine,provider)
    # Covers both axes and sector permutation, includes zero/negative/positive
    # values and endpoints. The four profile values remain independent.
    settings = bytes(v & 255 for v in [1,-2,0,3,-4,5,-6,7,0,-1,2,-3,
                                     -1,2,0,-3,4,-5,6,-7,0,1,-2,3])
    guarded(machine,'settings',INPUT,settings)
    guarded(machine,'snapshot',SNAPSHOT,b'\xcc'*25)
    guarded(machine,'token',TOKEN,b'\xcc'*8)
    guarded(machine,'output',OUTPUT,b'\x5a'*OUTPUT_BYTES)
    guarded(machine,'job',JOB,job_fixture())
    guarded(machine,'setup',SETUP,struct.pack('<4I',0,JOB+11364,0,OUTPUT),'r')
    cases = []

    def run(name,args,wanted=None,m=machine):
        result = gcc_call(m,syms,name,args,wanted=wanted)
        row = summarize(name,result)
        cases.append(row)
        return row

    run('_ep7p_edit',[core,2,INPUT],1)
    ready_lock(machine,provider)
    run('_ep7p_capture',[core,11,3,SNAPSHOT],1)
    frozen = b'\x02'+settings
    require(machine.read(SNAPSHOT,25)==frozen,'capture did not freeze selected COLOR3 settings')
    run('_ep7p_capture',[core,11,2,SNAPSHOT],1)
    require(machine.read(SNAPSHOT,25)==b'\x01'+bytes(24),'edit leaked into adjacent COLOR2')
    run('_ep7p_capture',[core,11,3,SNAPSHOT],1)
    machine.mutate('settings',0,bytes(24))
    run('_ep7p_edit',[core,2,INPUT],1)
    require(machine.read(SNAPSHOT,25)==frozen,'later UI settings changed the frozen snapshot')

    # Use the real poll bridge to hold the semaphore. No count or return-value
    # injection: the next provider acquire must execute native timeout0 failure.
    run('_ep7_gcc_raw_sem_poll',[1],0)
    require(u32(machine,SEM_OBJECT+24)==0,'native poll did not consume the private count')
    old_core = machine.read(core,5052)
    machine.mutate('settings',0,settings)
    busy = run('_ep7p_edit',[core,2,INPUT],0)
    require(busy['native_lock_calls']==[dict(api='poll',handle=1,timeout=0,returned_status=-50)] and
            machine.read(core,5052)==old_core and machine.read(SNAPSHOT,25)==frozen and
            machine.read(provider+24,1)==b'\0','busy poll mutated core or poisoned a valid lock')
    run('_ep7_gcc_raw_sem_signal',[1],0)
    ready_lock(machine,provider)

    run('_ep7p_capture',[core,10,3,SNAPSHOT],0)
    require(machine.read(SNAPSHOT,25)==frozen,'unsupported profile mode changed prior snapshot')
    ready_lock(machine,provider)

    # Register independently-owned job storage using the frozen value. This
    # exercises the final registry/copy path, not worker allocator provenance.
    job_before = machine.read(JOB,STOCK)
    run('_ep7p_register_job',[core,JOB,EXTENT,SNAPSHOT,TOKEN],1)
    token = struct.unpack('<Q',machine.read(TOKEN,8))[0]
    require(token!=0 and machine.read(JOB,STOCK)==job_before and
            machine.read(JOB+STOCK,24)==settings,'job registration changed stock bytes or lost frozen H/L')
    run('_ep7_gcc_postbuilder_observer',[SETUP])
    expected = bytearray(b'\x5a'*OUTPUT_BYTES)
    hue = [7000,6000,5000,4000,3000,2000,1000,0,-1000,-2000,-3000,-4000,-5000,-6000,-7000]
    lum = [-300,-250,-200,-150,-100,-50,-25,0,25,50,100,150,200,250,300]
    signed_settings = struct.unpack('<24b',settings)
    patches = []
    for index,band in enumerate([0,2,4,6,8,10,1,3,5,7,9,11]):
        for axis,offset,table in [('H',706,hue),('L',710,lum)]:
            value = signed_settings[band+(12 if axis=='L' else 0)]
            if value:
                position = offset+24*index
                struct.pack_into('<h',expected,position,table[value+7])
                patches.append(dict(axis=axis,sector=band,offset=position,value=table[value+7]))
    require(machine.read(OUTPUT,OUTPUT_BYTES)==expected,'final observer wrote unexpected CPU coefficients/bytes')
    ready_lock(machine,provider)

    run('_ep7p_release_job',[core,token & 0xffffffff,token>>32],1)
    del machine.regions['job']  # Prove retired request is not dereferenced, even when unmapped.
    machine.mutate('output',0,b'\x5a'*OUTPUT_BYTES)
    run('_ep7_gcc_postbuilder_observer',[SETUP])
    require(machine.read(OUTPUT,OUTPUT_BYTES)==b'\x5a'*OUTPUT_BYTES,'retired/unmapped job changed output')
    ready_lock(machine,provider)

    return dict(scope=__doc__,candidate_build_revision=build['source_revision'],
        actual_elf_code_equals_decoded_candidate=True,all_assertions_passed=True,
        hash_checks_performed=False,engine=str(engine),
        runtime=hex(runtime),bootstrap=hex(boot),core=hex(core),provider=hex(provider),
        input_hl=list(signed_settings),frozen_profile=2,job_token=token,
        cases=cases,cpu_coefficient_writes=patches,
        busy_poll_status=-50,busy_core_unchanged=True,busy_provider_not_poisoned=True,
        adjacent_profile_unchanged=True,frozen_survives_later_edit=True,
        unsupported_mode_output_unchanged=True,retired_job_unmapped=True,retired_output_unchanged=True,
        readonly_buffer_guards=True,native_api_success_stubs=False,
        firmware_files_modified=False,hardware_executed=False,installable=False,
        limits=['S2 resident code/kernel/task/queue/header/shared-lock fixtures are inherited. No board, multicore race or actual task launch is modeled.',
                'Calls use an explicit GCC caller on the guarded task stack. This does not execute native UI/controller capture hook envelopes or queue/worker ownership transfer.',
                'Job bytes and allocation lifetime are independently supplied from the existing direct-reader fixture, not created by the real native constructor/allocator.',
                'The final postbuilder observer executes cohort validation, runtime lookup, native-lock-backed registry decode and coefficient writes. Stock ISP builder/hardware is not executed.',
                'Retirement proves no read of an unmapped old job; it does not solve stale naked request address reuse, which still requires native lifetime exclusion.',
                'LUT values are inherited comparative H/L coefficients, not E-P7 pixel calibration or image-quality acceptance.'])


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.candidate,args.tool_prefix,args.engine),indent=2))
