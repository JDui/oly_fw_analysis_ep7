#!/usr/bin/env python3
"""Follow native semaphore/critical CFG stack deltas, stopping at explicit stack-switch boundaries."""
import argparse
from collections import deque
import json
import re
import struct
import subprocess
import tempfile
from pathlib import Path

from ep7_descriptor_frames import instructions
from ep7_far_call_check import ROOT, REFERENCE, PRELUDE, body
from ep7_native_bindings import bindings

BASE = 0x60020020
KERNEL = (0x60030000,0x60039000)
BRANCHES = {'beq','bne','bgt','bge','blt','ble','bhi','bhs','bls','blo','bcc','bcs','bvc','bvs','bnc','bns'}
LOOPS = {'leq','lne','lgt','lge','llt','lle','lhi','lcc','lls','lcs','lvc','lvs','lra'}

# These are instruction witnesses, not arbitrary entry points inferred from a
# linear sweep through data. The graph still follows both branch destinations.
CONTEXT_WITNESSES = {
    0x60032243: ('mov','1,d1'), 0x60032245: ('movhu','d1,(48,a0)'),
    0x60032248: ('clr','d1'), 0x60032249: ('mov','d1,(56,a0)'),
    0x6003224c: ('mov','(20,a2),d2'), 0x6003224f: ('mov','(16,a2),d1'),
    0x60032252: ('add','d1,d2'), 0x60032253: ('mov','20,d1'),
    0x60032255: ('sub','d1,d2'), 0x60032257: ('mov','d2,a1'),
    0x60032259: ('mov','d2,(24,a0)'), 0x6003225c: ('mov','d0,(12,a1)'),
    0x6003225f: ('mov','(8,a2),d1'), 0x60032262: ('mov','d1,(4,a1)'),
    0x60032265: ('mov','1610818983,d0'), 0x6003226b: ('mov','d0,(16,a1)'),
    0x600325a7: ('call','0x6003860b,[],0'),
    0x600325ac: ('mov','d2,d0'), 0x600325ad: ('calls','(a2)'),
    0x600359be: ('mov','(96,a0),a0'), 0x600359c1: ('mov','a2,(a0)'),
    0x600359dc: ('mov','(260,a0),a0'), 0x600359eb: ('mov','(272,a0),a1'),
    0x60035a01: ('calls','(a1)'), 0x60035a0f: ('add','24,a2'),
    0x60035a11: ('mov','24,a1'), 0x60035a13: ('add','d2,a1'),
    0x60035a15: ('mov','a2,a0'), 0x60035a16: ('call','0x6003853e,[d2,d3,a2,a3],16'),
    0x60035a2c: ('mov','(100,a0),a0'), 0x60035a2f: ('cmp','a0,a2'),
    0x60035a30: ('bne','0x60035a56'), 0x60035a38: ('mov','(356,a0),d0'),
    0x60035a3c: ('cmp','1,d0'), 0x60035a3e: ('bne','0x60035a56'),
    0x6003853e: ('mov','sp,(0,a1)'), 0x60038541: ('mov','(0,a0),sp'),
    0x60038544: ('ret','[d2,d3,a2,a3],16'),
    0x60038547: ('mov','a1,sp'),
    0x60038562: ('movm','[a3],(sp)'), 0x60038564: ('mov','1610843518,a3'),
    0x60038578: ('mov','(316,a1),a0'), 0x6003857c: ('jmp','(a0)'),
    0x6003857e: ('movm','(sp),[a3]'), 0x60038580: ('rets',''),
    0x6003435c: ('movhu','(48,a0),d0'), 0x6003435f: ('cmp','1,d0'),
    0x60034361: ('bne','0x60034366'), 0x60034363: ('clr','d0'),
    0x60034364: ('bra','0x6003436b'),
    0x6003862c: ('call','0x6003434b,[],0'), 0x60038631: ('cmp','0,d0'),
    0x60038633: ('beq','0x60038646'),
    0x6003863f: ('call','0x6003436e,[d2,d3,a2,a3],36'),
}


def register_bytes(operands):
    values = re.search(r'\[([^]]*)\]',operands)
    if not values:
        raise ValueError('missing MOVM register set')
    names = values[1].split(',') if values[1] else []
    costs = dict(d2=4,d3=4,a2=4,a3=4,other=32)
    if any(name not in costs for name in names) or len(names) != len(set(names)):
        raise ValueError('unreviewed MOVM set '+operands)
    return sum(costs[name] for name in names)


class NativeGraph:
    def __init__(self, decoded, objdump):
        self.decoded = decoded
        self.objdump = objdump
        self.data = decoded.read_bytes()
        if len(self.data) != 26214336:
            raise ValueError('unsupported decoded main length')
        self.decoded_instructions = {}
        self.functions = {}
        self.function_instruction_addresses = {}
        self.temp = tempfile.TemporaryDirectory(prefix='ep7-native-instruction-')
        self.window = Path(self.temp.name)/'instruction.bin'

    def close(self):
        self.temp.cleanup()

    def instruction(self, pc):
        if pc not in self.decoded_instructions:
            # Explicit evidence witnesses may live outside the CFG search range.
            # function()/push() still restrict graph exploration to KERNEL.
            if not BASE <= pc <= BASE+len(self.data)-16:
                raise ValueError('instruction outside decoded input '+hex(pc))
            # Objdump only needs the reached instruction and its longest possible
            # suffix, not a new read of the entire 25 MiB input for every PC.
            self.window.write_bytes(self.data[pc-BASE:pc-BASE+16])
            asm = subprocess.check_output([self.objdump,'-D','-z','-b','binary','-m','mn10300',
                '--insn-width=16',f'--adjust-vma={pc:#x}',str(self.window)],text=True)
            rows = instructions(asm)
            if not rows or rows[0][0] != pc:
                raise ValueError('cannot decode reached instruction '+hex(pc))
            # Decode from each reached boundary; never linear-sweep through a
            # return/data island and pretend its later instruction alignment is proven.
            self.decoded_instructions[pc] = rows[0]
        return self.decoded_instructions[pc]

    def function(self, entry):
        if entry in self.functions:
            return self.functions[entry]
        if not KERNEL[0] <= entry < KERNEL[1]:
            raise ValueError('function outside reviewed kernel search interval '+hex(entry))
        seen = {}; work = deque([(entry,0,None)]); calls = {}; returns = {}; boundaries = {}; stack_ops = {}
        high = 0; reached = set(); loop_sites = {}; direct_memory_low = 0
        while work:
            pc,depth,loop = work.popleft()
            state = (pc,loop)
            if state in seen:
                if seen[state] != depth:
                    raise ValueError(f'inconsistent/unbounded SP at {pc:#x}: {seen[state]} vs {depth}')
                continue
            if len(seen)>4000:
                raise ValueError('function CFG exceeds review budget '+hex(entry))
            seen[state] = depth; reached.add(pc)
            _,size,mn,ops = self.instruction(pc)
            high = max(high,depth); next_pc = pc+size

            def boundary(kind):
                boundaries[(pc,kind)] = dict(site=hex(pc),kind=kind,depth=depth,mnemonic=mn,operands=ops)

            def push(address, new_depth=depth, lar=loop):
                if not KERNEL[0] <= address < KERNEL[1]:
                    boundary('control_leaves_reviewed_kernel_range')
                else:
                    work.append((address,new_depth,lar))

            if mn in ('ret','retf','rets'):
                restore = 0 if mn == 'rets' else int(ops.rsplit(',',1)[-1])
                returns[(pc,depth)] = dict(site=hex(pc),mnemonic=mn,operands=ops,
                    local_depth=depth,inferred_incoming_frame=restore-depth)
                continue
            if mn in ('rti','break','syscall'):
                boundary('exception_or_interrupt_control'); continue
            if mn in ('call','calls'):
                match = re.fullmatch(r'(0x[0-9a-f]+),\[([^]]*)\],(\d+)',ops) if mn == 'call' else re.fullmatch(r'(0x[0-9a-f]+)',ops)
                if not match:
                    boundary('indirect_call')
                else:
                    target = int(match[1],16); frame = int(match[3]) if mn == 'call' else 0
                    save_bytes=register_bytes(ops) if mn == 'call' else 0
                    direct_memory_low=max(direct_memory_low,depth+save_bytes)
                    if not KERNEL[0] <= target < KERNEL[1]:
                        boundary('call_leaves_reviewed_kernel_range')
                    else:
                        calls[(pc,target,depth)] = dict(site=hex(pc),target=hex(target),
                            frame=frame,register_save_bytes=save_bytes,
                            caller_local_depth=depth,mnemonic=mn,operands=ops)
                        high = max(high,depth+frame)
                # A returning native CALL must restore its input SP. This is
                # checked against all decoded normal returns when composing.
                # The called body may change hardware-loop registers.
                push(next_pc,lar=None); continue
            if mn in ('bra','jmp'):
                if not re.fullmatch(r'0x[0-9a-f]+',ops):
                    boundary('indirect_jump'); continue
                push(int(ops,16)); continue
            if mn in BRANCHES:
                if not re.fullmatch(r'0x[0-9a-f]+',ops):
                    raise ValueError('unreviewed conditional branch '+hex(pc))
                push(int(ops,16)); push(next_pc); continue
            if mn == 'setlb':
                # GNU OP_DB sets LAR=pc+5; loop instructions branch to LAR-4.
                push(next_pc,lar=next_pc); continue
            if mn in LOOPS:
                if loop is None:
                    boundary('hardware_loop_target_unknown')
                else:
                    loop_sites[pc] = loop; push(loop)
                if mn != 'lra':
                    push(next_pc)
                continue
            if mn == 'movm':
                count = register_bytes(ops)
                if ops.endswith(',(sp)'):
                    new_depth = depth+count
                elif ops.startswith('(sp),'):
                    new_depth = depth-count
                else:
                    boundary('unreviewed_movm_base'); continue
                stack_ops[pc] = dict(site=hex(pc),mnemonic=mn,operands=ops,before=depth,after=new_depth)
                high = max(high,new_depth); push(next_pc,new_depth); continue
            if re.search(r',sp$',ops):
                match = re.fullmatch(r'(-?\d+),sp',ops)
                if mn == 'add' and match:
                    new_depth = depth-int(match[1])
                    stack_ops[pc] = dict(site=hex(pc),mnemonic=mn,operands=ops,before=depth,after=new_depth)
                    high=max(high,new_depth); push(next_pc,new_depth); continue
                boundary('sp_replaced_from_register_or_memory'); continue
            # Direct negative-SP offsets can touch below the current SP without
            # an ADD. Retain that known lower address; pointer aliases are not
            # a general memory-safety proof made by this stack-delta analysis.
            offsets = [int(v) for v in re.findall(r'\((-?\d+),sp\)',ops)]
            direct_memory_low=max([direct_memory_low,depth]+[depth-x for x in offsets])
            if mn.startswith('b') and mn not in {'btst','bset','bclr'}:
                raise ValueError('unclassified branch/trap '+mn+' '+hex(pc))
            push(next_pc)
        result = dict(entry=hex(entry),instruction_count=len(reached),
            reached_extent=[hex(min(reached)),hex(max(reached)+self.instruction(max(reached))[1])],
            maximum_own_sp_depth=high,maximum_direct_stack_address_depth=direct_memory_low,
            stack_operations=list(stack_ops.values()),calls=list(calls.values()),returns=list(returns.values()),
            boundaries=list(boundaries.values()),hardware_loop_edges=[dict(site=hex(p),target=hex(t)) for p,t in loop_sites.items()])
        self.functions[entry] = result
        self.function_instruction_addresses[entry] = frozenset(reached)
        return result

    def collect(self, roots):
        pending = list(roots); completed = set()
        while pending:
            entry=pending.pop()
            if entry in completed:
                continue
            if len(completed)>=100:
                raise ValueError('native call graph exceeds bounded review')
            result=self.function(entry); completed.add(entry)
            pending.extend(int(row['target'],16) for row in result['calls'])
        mismatches=[]
        for result in self.functions.values():
            for edge in result['calls']:
                callee=self.functions[int(edge['target'],16)]
                for ret in callee['returns']:
                    if ret['inferred_incoming_frame'] != edge['frame']:
                        mismatches.append(dict(caller=result['entry'],call_site=edge['site'],
                            callee=callee['entry'],caller_frame=edge['frame'],return_site=ret['site'],
                            inferred_frame=ret['inferred_incoming_frame']))
        return mismatches


def context_contracts(graph):
    cold_source=re.sub(r'\s+','',(ROOT/'prototypes/ep7_volatile_hl/runtime/cold_bootstrap.c').read_text())
    guard_source=re.sub(r'\s+','',(ROOT/'prototypes/ep7_volatile_hl/runtime/cold_cohort.c').read_text())
    guarded=('if(!ep7r_native_cold_context(task.tcb))ep7_gcc_quarantine(0xf06u);' in cold_source and
             '*(constvolatileuint16_t*)(uintptr_t)(tcb+48u)!=1u' in guard_source)
    for pc,expected in CONTEXT_WITNESSES.items():
        if graph.instruction(pc)[2:] != expected:
            raise ValueError('native context witness changed '+hex(pc))
    root=0x600411a4
    expected={96:0x621a630c,100:0x621a6334,272:0x60073215,
              316:0x600300a1,328:0x621a63b0,344:0,356:0}
    for offset,value in expected.items():
        if struct.unpack_from('<I',graph.data,root+offset-BASE)[0] != value:
            raise ValueError('domain0 root field changed '+str(offset))
    if graph.instruction(expected[272])[2:] != ('retf','[],0'):
        raise ValueError('stock scheduler callback no longer a zero-stack leaf')
    # Inspect the full fixed doorbell function, including its custom A3 return.
    pc=expected[316]; doorbell=[]
    while pc<0x600300c3:
        row=graph.instruction(pc); doorbell.append(row); pc+=row[1]
    allowed={'cmp','beq','bra','mov','jmp'}
    if pc!=0x600300c3 or doorbell[-1][2:]!=('jmp','(a3)'):
        raise ValueError('doorbell return shape changed')
    for pc,_,mn,ops in doorbell:
        if mn not in allowed or re.search(r'\bsp\b',ops):
            raise ValueError('doorbell has unreviewed stack/control effects')
        if mn in {'beq','bra'} and not expected[316]<=int(ops,16)<0x600300c3:
            raise ValueError('doorbell branch leaves its reviewed body')
        if mn=='jmp' and pc!=0x600300c1:
            raise ValueError('additional doorbell indirect control')
        if mn=='mov' and ops.endswith(',a3'):
            raise ValueError('doorbell clobbers its return register')
    return dict(
        instruction_witness_count=len(CONTEXT_WITNESSES),
        domain0_root=hex(root),stock_root_fields={str(k):hex(v) for k,v in expected.items()},
        scheduler_callback=dict(site='0x60035a01',stock_target=hex(expected[272]),
            extra_stack_bytes=0,condition='domain0 root+272 retains its stock value'),
        doorbell=dict(site='0x6003857c',stock_target=hex(expected[316]),
            checked_body_instructions=len(doorbell),body_extra_stack_bytes=0,
            wrapper_save_bytes=4,return_via_a3='0x6003857e',
            condition='domain0 root+316 retains its stock value'),
        context_switch=dict(save_site='0x6003853e',replace_site='0x60038541',
            outgoing_tcb_saved_sp_offset=24,caller_frame_bytes=16,
            meaning='Outgoing stack is saved before incoming SP is loaded; the next RET runs on the incoming stack. The outgoing continuation assumes later restoration of that saved context.'),
        restart=dict(replace_site='0x60038547',
            meaning='Discards the current SP. Work after replacement belongs to the new task stack, not the outgoing stack.',
            cold_exclusion='The restart requires root+356==1; the stock domain0 value is 0. Runtime immutability is not proven here.'),
        task_exception_gate=dict(flag_offset=48,pending_offset=56,initial_flag=1,
            skip_condition='Current TCB halfword+48==1 makes 6003434b return 0 and skips the task exception callback.',
            cold_admission_observation_implemented=guarded,live_device_condition_observed=False,
            condition_lifetime_proven=False,
            reason='The cold bootstrap now observes the live flag before native semaphore calls. The observation is not a TCB lease or proof against a later writer, cancellation, or IRQ before admission.'),
        witnesses=[dict(pc=hex(pc),mnemonic=mn,operands=ops) for pc,(mn,ops) in CONTEXT_WITNESSES.items()],
        fixed_root_runtime_immutability_proven=False,
        cold_context_admission_evidence='research/ep7/cold-context.json' if guarded else None)


def initial_context_semantics(reference):
    """Reuse GNU RET/CALLS bodies for the one newly uncertain frame arithmetic."""
    source=reference.read_text()
    ret=body(source,'OP_DF0000'); calls=body(source,'OP_F0F0')
    driver=PRELUDE+'''
static void ret16(void) {
 uint32_t cia=PC,nia=0,REGS=0xf0,IMM8=16;
'''+ret+'''
 PC=nia;
}
static void call_task(void) {
 uint32_t cia=PC,nia=0,AN0=2;
'''+calls+'''
 PC=nia;
}
int main(void) {
 const uint32_t top=RAM+480u, saved=top-20u;
 memset(&State,0,sizeof State);lowest=UINT32_MAX;
 store_word(saved,0x33333333u);store_word(saved+4,0x601912fbu);
 store_word(saved+8,0xddddddddu);store_word(saved+12,0x12345678u);
 store_word(saved+16,0x600325a7u);State.regs[REG_SP]=saved;
 ret16();assert(State.regs[REG_SP]==top-4u && PC==0x600325a7u);
 assert(State.regs[6]==0x601912fbu && State.regs[2]==0x12345678u);
 /* The intervening critical-leave call must return with its incoming SP and
  * preserve A2/D2, as required by its stock ABI. It is not executed here. */
 PC=0x600325adu;call_task();assert(PC==0x601912fbu);
 assert(State.regs[REG_SP]==top-4u && load_word(top-4u)==0x600325afu);
 assert(State.regs[REG_MDR]==0x600325afu);
 puts("{\\\"initial_restore_checks\\\":1,\\\"task_entry_calls_checks\\\":1,\\\"entry_below_stack_top_bytes\\\":4}");
 return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix='ep7-native-context-') as temp:
        c=Path(temp)/'context.c'; binary=Path(temp)/'context'; c.write_text(driver)
        subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(c),'-o',str(binary)],check=True)
        result=json.loads(subprocess.check_output([str(binary)],text=True))
    result.update(gnu_bodies_reused=['OP_DF0000','OP_F0F0'],
        stock_api_executed=False,task_initializer_executed=False,
        initial_frame_values_derived_from_checked_stock_instructions=True)
    return result


def compose(graph,roots):
    memo={}; active=set()
    # These closures are conditional stock-domain0 contracts, not permission to
    # erase the still-visible raw CFG boundaries or assert callback immutability.
    classified={
        '0x60035a01':'stock_domain0_scheduler_callback',
        '0x6003857c':'stock_domain0_doorbell_custom_return',
        '0x60038541':'outgoing_stack_saved_before_context_transfer',
        '0x60038547':'outgoing_stack_discarded_at_restart',
    }
    def visit(entry):
        if entry in active: raise ValueError('recursive native stack edge '+hex(entry))
        if entry in memo: return memo[entry]
        active.add(entry); row=graph.functions[entry]
        high=max(row['maximum_own_sp_depth'],row['maximum_direct_stack_address_depth'])
        path=[hex(entry)]; frontier=[]
        for b in row['boundaries']:
            frontier.append(dict(function=hex(entry),**b,
                known_stack_effect_bytes=b['depth'],path=[hex(entry)],
                conditional_classification=classified.get(b['site'])))
        for call in row['calls']:
            child=visit(int(call['target'],16)); prefix=call['caller_local_depth']+call['frame']
            if prefix+child['known_stack_effect_envelope_bytes']>high:
                high=prefix+child['known_stack_effect_envelope_bytes'];path=[hex(entry)]+child['path']
            for b in child['frontier']:
                frontier.append(dict(b,known_stack_effect_bytes=prefix+b['known_stack_effect_bytes'],
                    path=[hex(entry)]+b['path']))
        active.remove(entry)
        result=dict(known_stack_effect_envelope_bytes=high,path=path,frontier=frontier,
            complete_stack_bound_bytes=None)
        memo[entry]=result;return result
    return {name:visit(entry) for name,entry in roots.items()}


def inspect(decoded,objdump,reference):
    native=bindings(); roots={
        'create':native['ep7_stock_raw_sem_create_unresolved']['address'],
        'delete':native['ep7_stock_raw_sem_delete_unresolved']['address']}
    graph=NativeGraph(decoded,objdump)
    try:
        mismatches=graph.collect(roots.values())
        if mismatches:
            raise ValueError('returning native call frame mismatch '+str(mismatches))
        contracts=context_contracts(graph)
        stack_effects=compose(graph,roots)
    finally:
        graph.close()
    initial=initial_context_semantics(reference)
    previous=json.loads((ROOT/'research/ep7/bootstrap-stack.json').read_text(encoding='utf-8-sig'))
    prefix=previous['usr3_own_prologue_bytes']+previous['original_call_frame_bytes']+previous['cold_bridge_bytes']+initial['entry_below_stack_top_bytes']
    combined=[]
    for row in previous['unknown_native_boundaries']:
        native_name={'native_sem_create_body_unknown':'create','native_sem_delete_body_unknown':'delete'}.get(row['boundary'])
        if native_name:
            native=stack_effects[native_name]
            combined.append(dict(native_root=native_name,c_path=row['path'],
                c_and_bridge_prefix=row['known_prefix_bytes'],
                native_known_stack_effect_envelope_bytes=native['known_stack_effect_envelope_bytes'],
                known_stack_effects_below_usr3_stack_top_bytes=prefix+row['known_prefix_bytes']+native['known_stack_effect_envelope_bytes']))
    known_max=max([prefix+previous['root_stack']['prefix_bytes']]+[
        r['known_stack_effects_below_usr3_stack_top_bytes'] for r in combined])
    return dict(scope=__doc__,root_entries={name:hex(pc) for name,pc in roots.items()},
        functions={hex(pc):row for pc,row in sorted(graph.functions.items())},
        reached_function_count=len(graph.functions),unique_instructions_decoded=len(graph.decoded_instructions),
        returning_call_frame_mismatches=mismatches,
        native_stack_effects=stack_effects,context_contracts=contracts,initial_context_semantics=initial,
        bootstrap_integration=dict(prior_c_graph='research/ep7/bootstrap-stack.json',
            usr3_initial_entry_overhead_bytes=4,usr3_prologue_call_and_bridge_bytes=prefix-4,
            native_paths=combined,known_stack_effect_envelope_below_stack_top_bytes=known_max,
            complete_stack_bound_bytes=None,remaining_stack_bytes=None),
        unresolved_boundaries=[dict(function=row['entry'],**b) for row in graph.functions.values() for b in row['boundaries']],
        gnu_instruction_reference=REFERENCE,
        stack_model='CALL save/frame, MOVM integer save sets, immediate ADD SP, in-function conditional edges and local hardware loops',
        complete_stack_bound_proven=False,
        limits=['Static control flow follows both sides of conditional branches; no register/value feasibility pruning.',
                'A direct call continuation assumes normal return; decoded return-frame mismatches remain explicit failures.',
                'Indirect control, exception control and SP replacement remain explicit boundaries; four have conditional stock-domain0 contracts.',
                'Known stack-effect envelopes are not complete upper bounds. Unknown callbacks, BREAK/IRQ and context restoration still need qualification.',
                'The initial frame fixture executes only reused GNU RET/CALLS bodies; it does not run the stock task initializer, scheduler or critical leave.',
                'The earlier C graph is reused unchanged. No C implementation is modified or recompiled in this check.',
                'Native opcode behavior beyond reviewed explicit stack/control effects is not executed.',
                'No general alias-store, arbitrary interruption, DMA, scheduler correctness or real device claim.'],
        firmware_modified=False,firmware_built=False,target_executed=False,hash_checks_performed=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded',type=Path,required=True)
    parser.add_argument('--objdump',required=True)
    parser.add_argument('--reference',type=Path,default=ROOT/'generated/ep7/mn10300-call-reference.igen')
    args=parser.parse_args()
    print(json.dumps(inspect(args.decoded,args.objdump,args.reference),indent=2))
