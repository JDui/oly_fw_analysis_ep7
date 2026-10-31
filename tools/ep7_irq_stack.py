#!/usr/bin/env python3
"""Locate stock IRQ stack transfers and count one pass of its explicit task-stack effects."""
import argparse
import json
import struct
from pathlib import Path

from ep7_native_stack import BASE, BRANCHES, LOOPS, NativeGraph, register_bytes, compose
from ep7_far_call_check import ROOT, REFERENCE

CPU_REFERENCE='https://gnu.googlesource.com/binutils-gdb/+/cbe950e9fe8a56f788bcf985cc51733f18abb45b/sim/mn10300/dv-mn103cpu.c'
EXTENSION_REFERENCE='https://www.manualshelf.com/manual/panasonic/personal-computer-mn103001g-f01k/user-manual-english.html'
MASK_REFERENCE='https://www.manualslib.com/manual/119167/Panasonic-Mn103001g-F01k.html?page=50'

# Manufacturer instruction names, not new implementations of these opcodes.
# The documented operations touch D registers, MAC state and condition flags;
# they have no memory operand, SP update, call or trap in their defined operation.
EXTENSIONS={
    0x6003010a:('udf13','d0,d0','GETCLX','MCRL to D0; MCVF to V',65),
    0x60030112:('udf12','d0,d0','GETCHX','MCRH to D0; MCVF to V',64),
    0x60030116:('udf15','d0,d0','GETX','MDRQ to D0',63),
    0x6003012c:('udf21','d0,d1','PUTCX','D0 to MCRH; D1 to MCRL; V to MCVF',62),
    0x60030130:('udf20','d0,d0','PUTX','D0 to MDRQ',61),
}

HELPER_W={
    0x60030107:('add','-16,sp'),0x6003010c:('mov','psw,d1'),
    0x6003010e:('mov','d1,(sp)'),0x60030110:('mov','d0,(4,sp)'),
    0x60030114:('mov','d0,(8,sp)'),0x60030118:('mov','d0,(12,sp)'),
    0x6003011a:('jmp','(a3)'),0x6003011c:('mov','(sp),d0'),
    0x6003011e:('and','8,d0'),0x60030121:('nop',''),
    0x60030122:('mov','psw,d1'),0x60030124:('or','d0,d1'),
    0x60030126:('mov','d1,psw'),0x60030128:('mov','(4,sp),d1'),
    0x6003012a:('mov','(8,sp),d0'),0x6003012e:('mov','(12,sp),d0'),
    0x60030132:('add','16,sp'),0x60030135:('jmp','(a3)'),
    **{pc:row[:2] for pc,row in EXTENSIONS.items()},
}

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
    0x600387b1:('mov','d0,psw'),0x600387b3:('call','0x600360f5,[d2,d3,a2,a3],32'),
    0x600387b8:('and','63487,psw'),0x600387bd:('mov','(348,a2),d0'),
    0x600387c1:('mov','d0,psw'),0x600387c3:('bra','0x60038794'),
    0x600387d2:('calls','(a0)'),
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
    0x6003435c:('movhu','(48,a0),d0'),0x6003435f:('cmp','1,d0'),
    0x60034361:('bne','0x60034366'),0x60034363:('clr','d0'),
    0x60034364:('bra','0x6003436b'),0x6003436b:('retf','[],0'),
}


def span(graph,start,end):
    result=[];pc=start
    while pc<end:
        row=graph.instruction(pc);result.append(row);pc+=row[1]
    if pc!=end:raise ValueError('window ends inside an instruction '+hex(end))
    return result


def conditional_exit_contract(graph,fields,software_bytes,udf):
    """Reuse the exact CFG, retaining transfers/faults as unresolved boundaries."""
    helper=span(graph,0x60030107,0x60030137)
    if {pc:(mn,ops) for pc,_,mn,ops in helper}!=HELPER_W:
        raise ValueError('extension save/restore helper changed')
    if {int(row['pc'],16):(row['mnemonic'],row['operands']) for row in udf}!={
            pc:row[:2] for pc,row in EXTENSIONS.items()}:
        raise ValueError('unexpected extension opcode on IRQ task-stack path')

    # These four calls happen after the original task SP is restored and before
    # the optional task-exception dispatcher. Traverse their already-decoded
    # direct callees, not the unrelated dispatcher or an interval linear sweep.
    sites=[0x600387fd,0x60038802,0x6003880d,0x60038812]
    roots={};frames={}
    for site in sites:
        _,_,mn,ops=graph.instruction(site)
        if mn!='call':raise ValueError('post-restore native call changed')
        roots[hex(site)]=int(ops.split(',',1)[0],16)
        frames[hex(site)]=int(ops.rsplit(',',1)[-1])
    calls=compose(graph,roots);reachable=set();pending=list(roots.values())
    while pending:
        entry=pending.pop()
        if entry in reachable:continue
        reachable.add(entry)
        pending.extend(int(row['target'],16) for row in graph.functions[entry]['calls'])
    pcs=set().union(*(graph.function_instruction_addresses[entry] for entry in reachable))
    writes=[hex(pc) for pc in sorted(pcs) if graph.instruction(pc)[3].endswith(',psw')]
    custom=[hex(pc) for pc in sorted(pcs) if graph.instruction(pc)[2].startswith('udf')]
    if writes or custom:raise ValueError('new PSW writer/custom opcode before task-exception decision')
    known=max(frames[name]+row['known_stack_effect_envelope_bytes'] for name,row in calls.items())
    if known!=32:raise ValueError('conditional native post-restore stack changed')

    # Both exits from deferred processing reapply root+348 while still on the
    # IRQ stack. The only remaining explicit pre-RTI write on the skipped-tex
    # tail is (current PSW | saved V), which cannot enable a masked IRQ.
    before_restore=span(graph,0x60038771,0x600387fd)
    controls={pc:(mn,ops) for pc,_,mn,ops in before_restore
        if mn in BRANCHES|LOOPS|{'bra','jmp','call','calls','ret','retf','rets','rti','break','syscall'}}
    if controls!={0x6003877e:('beq','0x60038794'),0x60038789:('beq','0x60038791'),
            0x6003878f:('calls','(a0)'),0x60038791:('jmp','0x60038827'),
            0x6003879b:('bne','0x600387c5'),0x600387a4:('bcc','0x600387c5'),
            0x600387b3:('call','0x600360f5,[d2,d3,a2,a3],32'),
            0x600387c3:('bra','0x60038794'),0x600387cc:('beq','0x600387df'),
            0x600387d2:('calls','(a0)')}:
        raise ValueError('IRQ-stack exit control flow changed')
    mask_writes={pc:(mn,ops) for pc,_,mn,ops in before_restore if ops.endswith(',psw')}
    if mask_writes!={0x60038775:('mov','d0,psw'),0x600387a8:('and','63487,psw'),
            0x600387b1:('mov','d0,psw'),0x600387b8:('and','63487,psw'),
            0x600387c1:('mov','d0,psw')}:
        raise ValueError('IRQ-stack exit PSW sequence changed')
    return dict(
        extension_register_transfers=[dict(pc=hex(pc),mnemonic=row[0],operands=row[1],
            manufacturer_macro=row[2],documented_register_transfer=row[3],manual_page=row[4],
            documented_extra_stack_bytes=0) for pc,row in EXTENSIONS.items()],
        extension_helper_instruction_count=len(helper),
        extension_stack_model='Documented MN103001G/F01K register-transfer behavior; exact stock helper matched. No custom CPU emulation or E-P7 silicon execution.',
        extension_psw_pipeline_and_register_roundtrip_tested=False,
        exit_mask=dict(value=hex(fields[348]),ie_bit=1,mask_level=0,
            ordinary_interrupt_acceptance='IE && pending_level < mask_level; no ordinary level is below zero.',
            initial_write='0x60038775',deferred_return_write='0x600387c1',
            checked_irq_stack_exit_control_edges=len(controls),
            irq_stack_reenable_window='0x600387b1..0x600387b8',
            optional_task_stack_reenable='0x6003881e, only when 6003434b returns nonzero',
            skipped_exception_tail_psw='0x60030126 ORs only saved V (bit 3) into current PSW; IE/LM are retained.'),
        conditional_no_task_exception_pass=dict(
            condition='Current TCB halfword+48 equals 1 when 6003434b reads it; stock root/callback bindings and normal return contracts remain valid.',
            query_returns_zero=True,skipped_sites=['0x6003881e','0x60038822'],
            direct_native_function_count=len(reachable),direct_native_instruction_count=len(pcs),
            direct_native_psw_writes=writes,direct_native_custom_opcodes=custom,
            native_calls={name:dict(entry=hex(roots[name]),incoming_frame=frames[name],
                own_and_callee_known_bytes=row['known_stack_effect_envelope_bytes'],
                unresolved_frontier=row['frontier']) for name,row in calls.items()},
            post_restore_known_stack_effects_bytes=known,
            known_stack_effects_below_interrupted_sp_bytes=8+software_bytes+known,
            complete_stack_bound_bytes=None,condition_lifetime_proven=False,
            context_transfer_psw_preservation_proven=False,
            ordinary_reentry_excluded_for_continuous_reviewed_return_path=True),
        references=dict(extension_manual=EXTENSION_REFERENCE,interrupt_priority_manual=MASK_REFERENCE,
            gnu_interrupt_acceptance=CPU_REFERENCE),
        limits=[
            'The manufacturer manual describes MN103001G/F01K, not the E-P7 SoC. Matching opcodes and the stock save/restore pattern support this static model; silicon identity, pipeline flags and actual IRQ timing are not established.',
            'The task-exception flag is observed at bootstrap admission, but its lifetime through other tasks/IRQs is not proven. This conditional path must not replace the unpruned 104-byte result.',
            'A scheduler transfer, restart, BREAK or changed callback is not a continuously returning path; its existing frontier remains explicit.',
            'The deferred-service reenable window is before the task-SP restore, on the IRQ stack. Its handlers and IRQ-stack capacity are not bounded here.',
            'NMI/reset/fault paths and arbitrary foreign writes are not excluded by IE/LM masking.'])


def inspect(decoded,objdump):
    g=NativeGraph(decoded,objdump)
    try:
        witnesses={**W,**HELPER_W}
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
                272:0x60073215,276:0x60073218,280:0x6007321b,348:0x800}
        for offset,value in fields.items():
            if struct.unpack_from('<I',g.data,root+offset-BASE)[0]!=value:
                raise ValueError('IRQ root field changed '+str(offset))
        for offset in [272,276,280]:
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
        exit_contract=conditional_exit_contract(g,fields,depth,udf)
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
            conditional_exit_contract=exit_contract,
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
                '56 bytes counts explicit save operations. A manufacturer-documented zero-extra-stack UDF model and conditional masked exit are recorded separately; neither is real E-P7 CPU execution.',
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
