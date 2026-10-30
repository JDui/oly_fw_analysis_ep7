#!/usr/bin/env python3
"""Read-only descriptor stack ownership and equal-width expansion plan."""
import argparse,json,re,struct,subprocess,tempfile
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows

# entry, end-exclusive, local bytes, buffer offset, allocation instruction,
# deallocation instruction (None for the nonreturning relay), task row/id/stack.
FRAMES=[
    ('command_owner',0x603df803,0x603df93a,320,20,0x603df805,0x603df933,0x60038d50,0x20,4096),
    ('dual_queue_relay',0x603ef892,0x603ef94a,312,12,0x603ef894,None,0x60038d6c,0x21,4752),
    ('kind19_relay',0x603ef94a,0x603ef9bb,304,4,0x603ef94c,0x603ef9b4,0x60039354,0x57,4096),
    ('kind19_worker',0x603f26a1,0x603f2799,304,4,0x603f26a3,0x603f2792,0x600395a0,0x6c,8192),
    ('command_drain',0x603e0546,0x603e05e9,312,12,0x603e0546,0x603e05e2,None,None,None),
]
WINDOWS=[(f[1],f[2]) for f in FRAMES]+[(0x603dfb76,0x603dfb84),(0x603dfc7a,0x603dfca9),(0x603e0521,0x603e052d)]
W={
    0x603df803:('movm','[d2,d3,a2,a3],(sp)'),
    0x603df812:('mov','sp,a3'),0x603df813:('add','20,a3'),
    0x603df8ba:('mov','a3,a0'),0x603df8bb:('call','0x603dfb10,[d2,d3,a2,a3],48'),
    0x603df92e:('call','0x603e0546,[d2,a2],8'),0x603df937:('ret','[d2,d3,a2,a3],16'),
    0x603ef892:('movm','[a2,a3],(sp)'),0x603ef898:('mov','sp,a2'),0x603ef899:('add','12,a2'),
    0x603ef8b5:('call','0x603eeb57,[d2,d3,a2,a3],44'),
    0x603ef8d2:('call','0x603eeb57,[d2,d3,a2,a3],44'),
    0x603ef8fd:('call','0x603eeb57,[d2,d3,a2,a3],44'),
    0x603ef91a:('call','0x603eeb57,[d2,d3,a2,a3],44'),
    0x603ef937:('call','0x603dfa41,[d2,a2],20'),0x603ef93e:('jmp','0x603ef8a1'),
    0x603ef94a:('movm','[d2,a2],(sp)'),0x603ef951:('mov','sp,a2'),0x603ef952:('inc4','a2'),
    0x603ef95b:('call','0x603df9f1,[a2],16'),0x603ef98c:('call','0x603dfa41,[d2,a2],20'),
    0x603ef9b8:('ret','[d2,a2],8'),
    0x603f26a1:('movm','[d2,d3,a2],(sp)'),0x603f26a7:('mov','sp,a2'),0x603f26a8:('inc4','a2'),
    0x603f26b4:('call','0x603df9f1,[a2],16'),0x603f2796:('ret','[d2,d3,a2],12'),
    0x603e058a:('mov','sp,a2'),0x603e058b:('add','12,a2'),
    0x603e058d:('mov','a2,a0'),0x603e058f:('call','0x603dfc7a,[d2,d3,a2,a3],16'),
    0x603e05cb:('mov','a2,a0'),0x603e05cd:('call','0x603dfc7a,[d2,d3,a2,a3],16'),
    0x603e05e6:('ret','[d2,a2],8'),
    0x603dfb76:('mov','a2,a0'),0x603dfb78:('call','0x603dfc7a,[d2,d3,a2,a3],16'),
    0x603dfc7a:('add','-424,sp'),0x603dfc7e:('mov','a0,(12,sp)'),
    0x603dfc8d:('mov','sp,a0'),0x603dfc8f:('add','152,a0'),0x603dfc93:('mov','16,d1'),
    0x603dfc9b:('call','0x603eeb57,[d2,d3,a2,a3],44'),
    0x603e0526:('add','424,sp'),0x603e052a:('ret','[d2,d3,a2,a3],16'),
}
CHECKS=[]
for name,start,end,local,offset,alloc,free,row,tid,stack in FRAMES:
    W[alloc]=('add',f'-{local},sp')
    if free:W[free]=('add',f'{local},sp')
    if row:
        priority={0x20:54,0x21:55,0x57:46,0x6c:26}[tid]
        CHECKS.append((row,'<7I',(tid,0,0,start,priority,stack,0)))

def instructions(asm):
    result=[]
    for line in asm.splitlines():
        m=re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)$',line)
        if m:result.append((int(m[1],16),len(m[2].split()),m[3],m[4].strip()))
    return result

def inspect(stock,objdump,assembler):
    owners=[];patches=[]
    def observe(start,stop,asm):
        frame=next((f for f in FRAMES if f[1]==start),None)
        if frame is None:return
        name,entry,end,local,offset,alloc,free,row,tid,stack=frame
        ins=instructions(asm)
        expected={alloc:-local}
        if free:expected[free]=local
        seen={a:int(op.split(',')[0]) for a,size,mn,op in ins if mn=='add' and op.endswith(',sp')}
        if seen!=expected:raise ValueError('unexpected stack adjustment: '+name)
        if offset+300!=local:raise ValueError('descriptor does not end at old frame boundary')
        direct=sorted(set(int(v) for _,_,_,op in ins for v in re.findall(r'\((-?\d+),sp\)',op)))
        if any(v<0 or v>=local for v in direct):raise ValueError('direct stack operand outside existing locals: '+name)
        for address,old in expected.items():
            size=next(size for a,size,_,_ in ins if a==address)
            if size!=4:raise ValueError('unexpected existing frame instruction width')
            patches.append(dict(address=hex(address),old_immediate=old,
                                new_immediate=old-12 if old<0 else old+12,instruction_bytes=size))
        owners.append(dict(name=name,entry=hex(entry),old_local_bytes=local,new_local_bytes=local+12,
                           descriptor_offset=offset,owned_descriptor_bytes=312,
                           trailer_offset_from_new_sp=local,task_row=hex(row) if row else None,
                           configured_task_id=tid,configured_stack_bytes=stack,
                           direct_sp_offsets=direct,all_direct_sp_operands_within_old_locals=True))
    evidence=inspect_windows(stock,objdump,WINDOWS,W,CHECKS,observe)
    # Assemble self-authored instruction fragments only. Never edit stock bytes.
    with tempfile.TemporaryDirectory(prefix='ep7-frame-width-') as tmp:
        src=Path(tmp)/'fragments.s';obj=Path(tmp)/'fragments.o'
        src.write_text('.text\n'+''.join(f" add {p['new_immediate']},sp\n" for p in patches))
        subprocess.run([str(assembler),'-o',str(obj),str(src)],check=True)
        dis=subprocess.check_output([str(objdump),'-d','--insn-width=16',str(obj)],text=True)
        built=instructions(dis)
        if len(built)!=len(patches):raise ValueError('assembled fragment count changed')
        for (_,size,mn,op),p in zip(built,patches):
            if size!=p['instruction_bytes'] or mn!='add' or op!=f"{p['new_immediate']},sp":
                raise ValueError('replacement frame instruction changed width/meaning')
    return dict(scope=__doc__,objdump_version=evidence['objdump_version'],
        input_structure=evidence['input_structure'],checked_instructions=evidence['checked_instructions'],
        checked_task_rows=len(CHECKS),owners=owners,equal_width_frame_edits=patches,
        materializer_callers=['0x603dfb78','0x603e058f','0x603e05cd'],
        materializer_command_buffer_offset=152,materializer_descriptor_pointer_offset=12,
        materializer_command_receive_needs_separate_scratch=True,
        existing_padding_reused=False,full_indirect_stack_access_audited=False,
        complete_call_chain_stack_budget_proven=False,all_receive_sites_qualified=False,
        hash_checks_performed=False,firmware_modified=False,firmware_executed=False,flash_ready=False)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock',type=Path,required=True)
    parser.add_argument('--objdump',type=Path,required=True)
    parser.add_argument('--assembler',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(inspect(args.stock,args.objdump,args.assembler),indent=2))
