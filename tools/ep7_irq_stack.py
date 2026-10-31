#!/usr/bin/env python3
"""Locate stock IRQ stack transfers and count one pass of its explicit task-stack effects."""
import argparse
import json
import struct
from pathlib import Path

from ep7_native_stack import BASE, NativeGraph, register_bytes, compose
from ep7_far_call_check import ROOT, REFERENCE

CPU_REFERENCE='https://gnu.googlesource.com/binutils-gdb/+/cbe950e9fe8a56f788bcf985cc51733f18abb45b/sim/mn10300/dv-mn103cpu.c'

W={
    0x60030008:('jmp','0x60055250'),
    0x600552aa:('calls','0x60059a9d'),0x600552b0:('rti',''),
    0x60059a9d:('movm','[d2,d3,a2],(sp)'),0x60059a9f:('add','-4,sp'),
    0x60059ab1:('call','0x600224ff,[d2,d3,a2,a3],28'),
    0x6003004f:('jmp','0x600386f8'),
    0x60030107:('add','-16,sp'),0x6003011a:('jmp','(a3)'),
    0x60030132:('add','16,sp'),0x60030135:('jmp','(a3)'),
    0x60032613:('mov','1610879396,d1'),0x60032619:('mov','d3,a0'),
    0x6003261b:('mov','d1,(d0,a0)'),
    0x600386f8:('movm','[a2,a3,other],(sp)'),0x600386fa:('add','4,sp'),
    0x600386fd:('mov','1610843912,a3'),0x60038703:('jmp','0x60030107'),
    0x60038708:('add','-4,sp'),
    0x60038719:('mov','(260,a2),a0'),0x6003872a:('mov','(276,a2),a0'),
    0x6003872e:('calls','(a0)'),0x60038730:('mov','(28,a2),a0'),
    0x60038733:('movbu','(a0),d0'),0x60038735:('cmp','0,d0'),
    0x60038737:('bne','0x60038748'),
    0x60038739:('mov','(116,a2),a0'),0x6003873c:('mov','(112,a2),a1'),
    0x6003873f:('add','-8,a1'),0x60038741:('add','a1,a0'),
    0x60038743:('mov','sp,(4,a0)'),0x60038746:('mov','a0,sp'),
    0x60038755:('inc','d0'),0x60038756:('mov','(28,a2),a1'),
    0x60038759:('movbu','d0,(a1)'),0x60038765:('calls','(a0)'),
    0x60038767:('and','63487,psw'),0x60038771:('mov','(348,a2),d0'),
    0x60038775:('mov','d0,psw'),0x60038777:('mov','(28,a2),a1'),
    0x6003877a:('movbu','(a1),d1'),0x6003877c:('add','-1,d1'),
    0x6003877e:('beq','0x60038794'),0x60038780:('movbu','d1,(a1)'),
    0x60038791:('jmp','0x60038827'),
    0x600387df:('clr','d0'),0x600387e0:('mov','(28,a2),a0'),
    0x600387e3:('movbu','d0,(a0)'),
    0x600387f9:('mov','(4,sp),a0'),0x600387fb:('mov','a0,sp'),
    0x600387fd:('call','0x60031a76,[d2,d3,a2,a3],20'),
    0x60038802:('call','0x6003593f,[d2,a2,a3],16'),
    0x6003880d:('call','0x60036884,[],4'),
    0x60038812:('call','0x6003434b,[],0'),0x60038817:('cmp','0,d0'),
    0x60038819:('beq','0x60038827'),0x6003881b:('movhu','(56,sp),d1'),
    0x6003881e:('mov','d1,psw'),
    0x60038822:('call','0x6003436e,[d2,d3,a2,a3],36'),
    0x60038827:('add','4,sp'),0x6003882a:('mov','1610844213,a3'),
    0x60038830:('jmp','0x6003011c'),0x60038835:('add','-4,sp'),
    0x60038838:('movm','(sp),[a2,a3,other]'),0x6003883a:('rti',''),
}


def span(graph,start,end):
    result=[];pc=start
    while pc<end:
        row=graph.instruction(pc);result.append(row);pc+=row[1]
    if pc!=end:raise ValueError('window ends inside an instruction '+hex(end))
    return result


def inspect(decoded,objdump):
    g=NativeGraph(decoded,objdump)
    try:
        witnesses=dict(W)
        vector_entries=[0x60030020]+list(range(0x60030058,0x60030081,8))
        for i,target in enumerate(vector_entries):
            witnesses[0x6002008c+9*i]=('mov',f'{target},d3')
            witnesses[0x60020092+9*i]=('movhu',f'd3,({0x8000+4*i:#x})')
            if i:witnesses[target]=('jmp','0x600386f8')
        for pc,expected in witnesses.items():
            if g.instruction(pc)[2:]!=expected:
                raise ValueError('IRQ witness changed '+hex(pc))
        root=0x600411a4
        fields={28:0x621a631c,88:0x621a6410,112:0x6218f200,116:8192,
                276:0x60073218,280:0x6007321b,348:0x800}
        for offset,value in fields.items():
            if struct.unpack_from('<I',g.data,root+offset-BASE)[0]!=value:
                raise ValueError('IRQ root field changed '+str(offset))
        for offset in [276,280]:
            if g.instruction(fields[offset])[2:]!=('retf','[],0'):
                raise ValueError('IRQ hook no longer stock zero-stack leaf')

        # On the outermost path (context byte==0), the prefix has only a fixed
        # optional hook. The custom A3 round trip is checked in W above. Calls
        # into the IRQ handler after the SP switch are deliberately not followed.
        prefix=[]
        for start,end in [(0x600386f8,0x60038708),(0x60030107,0x6003011c),
                          (0x60038708,0x60038746)]:
            prefix.extend(span(g,start,end))
        depth=0;maximum=0;effects=[];udf=[]
        allowed={'movm','add','mov','movbu','movhu','asl2','cmp','beq','bne',
                 'lsr','and','calls','jmp','udf12','udf13','udf15'}
        for pc,_,mn,ops in prefix:
            before=depth
            if mn not in allowed:raise ValueError('new IRQ entry instruction '+hex(pc))
            if mn=='movm':depth+=register_bytes(ops)
            elif ops.endswith(',sp'):
                if mn!='add':raise ValueError('SP replaced before reviewed transfer')
                depth-=int(ops.split(',')[0])
            if depth!=before:effects.append(dict(pc=hex(pc),mnemonic=mn,operands=ops,before=before,after=depth))
            maximum=max(maximum,depth)
            if mn.startswith('udf'):udf.append(dict(pc=hex(pc),mnemonic=mn,operands=ops))
            if mn=='calls' and pc!=0x6003872e:raise ValueError('new pre-switch callback')
        if depth!=56 or maximum!=56:raise ValueError('IRQ explicit save frame changed')

        # Once original SP is restored, ordinary native callees again consume
        # the task stack. Reuse the native CFG/frame analysis without following
        # the unrelated IRQ-handler stack or treating unknown calls as bounded.
        mismatches=g.collect([0x600387fd])
        if mismatches:raise ValueError('IRQ exit native CALL/RET mismatch '+str(mismatches))
        post=compose(g,{'post_restore':0x600387fd})['post_restore']
        epilogue=[]
        for start,end in [(0x60038827,0x60038835),(0x6003011c,0x60030137),
                          (0x60038835,0x6003883c)]:
            epilogue.extend(span(g,start,end))
        remaining=depth;restore=[]
        for pc,_,mn,ops in epilogue:
            before=remaining
            if mn=='movm' and ops.startswith('(sp),'):remaining-=register_bytes(ops)
            elif mn=='add' and ops.endswith(',sp'):remaining-=int(ops.split(',')[0])
            if before!=remaining:restore.append(dict(pc=hex(pc),mnemonic=mn,operands=ops,before=before,after=remaining))
            if mn.startswith('udf'):udf.append(dict(pc=hex(pc),mnemonic=mn,operands=ops))
        if remaining!=0:raise ValueError('IRQ explicit software frame does not unwind')
        if g.instruction(0x60030020)[2:]!=('mov','d0,(-4,sp)') or g.instruction(0x60030026)[2:]!=('mov','a0,(-8,sp)'):
            raise ValueError('level0 diagnostic scratch changed')
        irq_top=fields[112]+fields[116]
        result=dict(scope=__doc__,instruction_witness_count=len(witnesses),
            decoded_instruction_count=len(g.decoded_instructions),
            vector_setup=[dict(register=hex(0x8000+4*i),written_low_halfword=hex(target&0xffff),
                intended_stock_entry=hex(target)) for i,target in enumerate(vector_entries)],
            vector_hardware_base_and_boot_loader_proven=False,
            domain0_irq_stack=dict(base=hex(fields[112]),bytes=fields[116],end_exclusive=hex(irq_top),
                initial_working_sp=hex(irq_top-8),saved_task_sp_word=hex(irq_top-4),
                entry_store='0x60038743',entry_switch='0x60038746',
                restore_load='0x600387f9',restore_switch='0x600387fb',
                capacity_proven=False),
            outermost_condition='Byte at *(domain0_root+28) equals 0 at 60038735; nonzero means use the already-active IRQ stack.',
            entry_explicit_stack_operations=effects,entry_explicit_stack_bytes=depth,
            level0_pre_entry_scratch_bytes=8,
            entry_optional_callback=dict(site='0x6003872e',root_offset=276,
                target=hex(fields[276]),own_stack_bytes=0,requires_stock_binding=True),
            exit_optional_callback=dict(root_offset=280,target=hex(fields[280]),own_stack_bytes=0,requires_stock_binding=True),
            native_post_restore_function_count=len(g.functions),
            native_post_restore_stack=post,
            exit_explicit_restore_operations=restore,software_frame_unwound_bytes=depth,
            unexecuted_udf_helpers=udf,
            single_irq_pass=dict(gnu_cpu_model_entry_bytes=8,software_saved_task_bytes=depth,
                post_restore_known_stack_effects_bytes=post['known_stack_effect_envelope_bytes'],
                known_stack_effects_below_interrupted_sp_bytes=8+depth+post['known_stack_effect_envelope_bytes'],
                complete_stack_bound_bytes=None),
            separate_diagnostic_path=dict(vector_branch='0x60030008',entry='0x60055250',
                called_diagnostic_function='0x60059a9d',observed_prologue_bytes=16,
                observed_format_call_frame_bytes=28,complete_stack_bound_bytes=None,
                hardware_break_or_nmi_vector_mapping_proven=False),
            references=dict(gnu_interrupt_entry=CPU_REFERENCE,gnu_rti_and_movm=REFERENCE),
            limits=[
                'The 8-byte hardware frame is the referenced GNU MN10300 model and matches the stock PSW+PC/RTI layout; E-P7 interrupt hardware is not executed or independently qualified.',
                'Vector writes store only low halfwords. The hardware vector base and upstream loading remain prerequisites, not proven by matching these software instructions.',
                'The fixed IRQ hook pointers and domain0 root must retain their reviewed values.',
                '56 bytes counts explicit save operations. UDF12/13/15/20/21 custom-register behavior is not executed or independently qualified here.',
                'Post-restore callbacks, native BREAK and nested entry near task-exception PSW restoration still prevent a complete task-stack bound.',
                'The independent IRQ stack handler graph, its 8 KiB capacity, NMI/debug/BREAK vectors and arbitrary fault nesting remain outside this check.',
                'No new C object compilation, firmware link/patch, CPU run, host application test suite or hardware operation.'],
            returning_call_frame_mismatches=mismatches,
            firmware_modified=False,firmware_built=False,target_executed=False,hash_checks_performed=False)
    finally:g.close()
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--decoded',type=Path,required=True);p.add_argument('--objdump',required=True)
    args=p.parse_args();print(json.dumps(inspect(args.decoded,args.objdump),indent=2))
