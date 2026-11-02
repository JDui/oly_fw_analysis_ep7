#!/usr/bin/env python3
"""Check unowned constructor allocation in the actual linked candidate.

The original non-H/L wrapper/constructor CALLs and get_tid API execute. CPU and
task context flags are explicit fixtures, not observed startup state. Native
allocation completion is modeled only after checking its original size/input.
No SHA, camera access or full startup simulation is performed.
"""
import argparse
import json
from pathlib import Path
import struct
import subprocess

from ep7_candidate_startup_sim import STACK, require
from ep7_candidate_static_kernel_sim import inspect as static_kernel
from ep7_offline_candidate import BASE, ELF_NAME, IMAGE_NAME, symbols
from ep7_request_ownership import require_instruction
from ep7_sim_probe import brief
from penf_emulator import Region

CONSTRUCTOR, ALLOCATE_SITE = 0x603537eb, 0x603537f3
ALLOCATE, ALLOCATE_RETURN, CONSTRUCTOR_CONTINUE = 0x60022700, 0x6002272f, 0x603537fa
UNOWNED_START, UNOWNED_CALL = 0x603e6d39, 0x603e6d3e
CALL_SP, STOCK_BYTES, MODELED_POINTER = STACK+1024, 15488, 0x61bd6d40
# Short windows begin on the native parameter-setup instructions independently
# decoded during the caller review. These are local CALL witnesses, not a CFG.
CALLER_WINDOWS = (
    (0x60321ea2,0x60321ea8,0x60321eb4,('mov','sp,a1')),
    (0x603e39b1,0x603e39c7,0x603e39d3,('mov','d0,a0')),
    (0x603e6d39,0x603e6d3e,0x603e6d4b,('mov','sp,a1')),
    (0x603ebca7,0x603ebcac,0x603ebcb9,('mov','sp,a1')),
    (0x603f0e5b,0x603f0e60,0x603f0e6d,('mov','sp,a1')),
    (0x603f2839,0x603f283e,0x603f284b,('mov','sp,a1')),
    (0x603f2bb5,0x603f2bb9,0x603f2bc6,('mov','(12,sp),a0')),
    (0x6060dbcd,0x6060dbe3,0x6060dbef,('clr','d0')),
)


def caller_evidence(directory,prefix,data):
    rows=[]
    for start,site,stop,first in CALLER_WINDOWS:
        require(data[site-BASE]==0xdd and
                site+struct.unpack_from('<i',data,site-BASE+1)[0]==CONSTRUCTOR and
                data[site-BASE+5:site-BASE+7]==bytes.fromhex('f02c'),
                'constructor CALL shape changed at '+hex(site))
        assembly=subprocess.check_output([prefix+'objdump','-b','binary','-m','mn10300',
            '-D','-z','--insn-width=16',f'--adjust-vma={BASE:#x}',
            f'--start-address={start:#x}',f'--stop-address={stop:#x}',
            str(directory/IMAGE_NAME)],text=True)
        require_instruction(assembly,start,*first)
        require_instruction(assembly,site,'call','0x603537eb,[d2,d3,a2,a3],44')
        rows.append(dict(window_start=hex(start),window_end_exclusive=hex(stop),
            call_site=hex(site),target=hex(CONSTRUCTOR),register_mask='0xf0',frame_bytes=44,
            kind19_worker_call=site==0x603f283e,
            local_disassembly=[line.strip() for line in assembly.splitlines()
                               if line and line[0] in '0123456789abcdef' and ':' in line
                               and '\t' in line]))
    return rows


def write_fixture(machine,address,data):
    for name,region in machine.regions.items():
        if region.address<=address and address+len(data)<=region.address+len(region.data):
            machine.mutate(name,address-region.address,data)
            return
    raise ValueError('fixture address is not mapped: '+hex(address))


def inspect(directory,prefix,engine,expect_rejection=False):
    build=json.loads((directory/'report.json').read_text(encoding='utf-8'))
    data=(directory/IMAGE_NAME).read_bytes()
    require(build['status']=='passed' and len(data)==26214336,'candidate build did not pass')
    syms={k:v['address'] for k,v in symbols(prefix,directory/ELF_NAME).items()}
    callers=caller_evidence(directory,prefix,data)
    base,syms,_,_=static_kernel(None,None,engine,context_only=True,
        candidate_override=(data,syms,build))
    stop=syms['_ep7_gcc_quarantine']
    require(base.read(ALLOCATE_RETURN,3)==bytes.fromhex('df0004'),
            'stock allocator RET[],4 changed')

    def context(name):
        machine=base.clone()
        if name=='native_get_tid_refused':
            # Native600317ac reads the current root+28 context flags and really
            # returns-25 when the first byte is nonzero. Do not stub the API.
            flags=struct.unpack('<I',machine.read(0x600411a4+28,4))[0]
            write_fixture(machine,flags,b'\x01')
        elif name=='other_cpu_original_task':
            # A coherent domain1 root/current-cell/task fixture. Its actual
            # get_tid succeeds; the H/L runtime subsequently rejects domain1.
            machine.mutate('cpu_id',0,struct.pack('<I',1))
            machine.mutate('tcb',16,struct.pack('<H',0x102d))
            root=0x60041330
            flags,cell=(struct.unpack('<I',machine.read(root+off,4))[0] for off in (28,96))
            machine.regions['peer_context_flags']=Region('peer_context_flags',flags,bytes(2),'rw',True)
            machine.regions['peer_current_cell']=Region('peer_current_cell',cell,
                struct.pack('<I',machine.regions['tcb'].address),'rw',True)
        return machine

    cases=[]
    for name in ('ordinary_domain0_original_task','native_get_tid_refused','other_cpu_original_task'):
        machine=context(name)
        before=machine.regions['private'].data
        result=machine.run(UNOWNED_START,ALLOCATE,
            overrides=dict(sp=CALL_SP,a2=STACK+1500),full_trace=True,
            breakpoints=[stop],limit=5000)
        rejected=expect_rejection and name!='ordinary_domain0_original_task'
        require(result['fault'] is None and result['registers']['pc']==(stop if rejected else ALLOCATE),
                'unowned allocation outcome differs: '+name+' '+str(brief(result)))
        require(any(row['pc']==UNOWNED_CALL for row in result['trace']) and
                any(row['pc']==CONSTRUCTOR for row in result['trace']) and
                any(row['pc']==ALLOCATE_SITE for row in result['trace']),
                'probe skipped the original constructor route')
        native_returns=[row['d0'] for row in result['trace'] if row['pc']==0x600317ed]
        require(native_returns and native_returns[-1]==(0xffffffe7 if name=='native_get_tid_refused' else 0),
                'native get_tid did not execute the expected real result')
        row=dict(name=name,**brief(result),quarantine_reached=rejected,
            quarantine_reason=3 if rejected else None,
            native_get_tid_results=[value if value<0x80000000 else value-0x100000000
                                    for value in native_returns],
            native_allocator_reached=not rejected,
            private_state_unchanged=machine.regions['private'].data==before)
        if rejected:
            require(result['status']=='breakpoint' and result['registers']['d0']==3,
                    'retained008 counterexample did not retain fault3')
        else:
            require(result['status']=='returned' and result['registers']['d0']==STOCK_BYTES and
                    row['private_state_unchanged'],'stock allocation size/private state changed')
            # The native allocator's pointer result is an explicit completion
            # fixture. Execute its real RET and every remaining candidate bridge
            # instruction to ensure a0 survives to the original constructor.
            completed=machine.resume(dict(result['registers'],pc=ALLOCATE_RETURN,
                a0=MODELED_POINTER,d0=0x76543210),CONSTRUCTOR_CONTINUE,
                full_trace=True,breakpoints=[stop],limit=5000)
            require(completed['fault'] is None and completed['status']=='returned' and
                    completed['registers']['pc']==CONSTRUCTOR_CONTINUE and
                    completed['registers']['a0']==MODELED_POINTER and
                    completed['registers']['sp']==CALL_SP-44 and
                    machine.regions['private'].data==before,
                    'neutral allocator bridge changed native pointer ABI/private state')
            row.update(original_request_bytes=STOCK_BYTES,allocator_completion_model=True,
                native_pointer_result_preserved=True,modeled_pointer_result=hex(MODELED_POINTER),
                completion=brief(completed))
        cases.append(row)

    # One boundary check: the same unavailable native task context must still
    # stop CLEANUP. Only ALLOCATE has a neutral unowned-delegation policy.
    cleanup=context('native_get_tid_refused')
    # The third GCC word argument is atSP+12. It points to fixture-owned stack
    # storage so the provider can clear its output before consulting get_tid.
    cleanup.mutate('stack',CALL_SP+12-STACK,struct.pack('<I',STACK+1500))
    cleanup.regions['caller']=Region('caller',0x19000000,
        b'\xdd'+struct.pack('<i',syms['_ep7q_worker_context_unresolved']-0x19000000)+bytes(2),'rx')
    checked=cleanup.run(0x19000000,0x19000007,
        overrides=dict(sp=CALL_SP,d0=4,d1=CALL_SP),full_trace=True,
        breakpoints=[stop],limit=5000)
    require(checked['fault'] is None and checked['status']=='breakpoint' and
            checked['registers']['pc']==stop and checked['registers']['d0']==3,
            'owned cleanup context protection was weakened')
    return dict(scope=__doc__,status='passed',input_image=str(directory/IMAGE_NAME),
        candidate_build_revision=build['source_revision'],
        expectation='retained008_unowned_allocation_defect' if expect_rejection else '009_unowned_allocation_fix',
        unowned_allocation_fixed=not expect_rejection,cases=cases,
        owned_cleanup_context_rejection=dict(**brief(checked),quarantine_reason=3),
        constructor_callers=callers,constructor_callers_locally_disassembled=8,
        exercised_original_route=dict(wrapper='0x603e6d04',start=hex(UNOWNED_START),
            constructor_call=hex(UNOWNED_CALL),constructor=hex(CONSTRUCTOR),
            allocation_hook=hex(ALLOCATE_SITE),original_allocator=hex(ALLOCATE)),
        hash_checks_performed=False,hardware_executed=False,full_boot_executed=False,
        limits=[
            'The existing native bootstrap/private semaphore publication executes with explicit task/kernel fixtures.',
            'Eight GNU-decoded local parameter-setup/CALL windows establish shared-constructor uses, not a complete CFG or their startup scheduling.',
            'The exercised non-H/L constructor route uses original CALL frames and native get_tid; CPU1/current task and unavailable-context flags are fixture inputs.',
            'No evidence establishes that the camera boot actually invokes this constructor in these rejected contexts.',
            'Native pool allocation completion is modeled after checking the unchanged15488-byte request; actual RET and candidate pointer-result return execute.',
            'ENTER/PROCESS/CLEANUP admission policies are outside the allocation-only fix; one failed-context CLEANUP check retains fault3.',
            'Full boot, cache/IRQ/multicore timing, reset cause and photo processing require hardware evidence.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    parser.add_argument('--expect-rejection',action='store_true')
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    result=inspect(args.candidate,args.tool_prefix,args.engine,args.expect_rejection)
    output=json.dumps(result,indent=2)+'\n'
    if args.report:args.report.write_text(output,encoding='utf-8')
    print(output,end='')
