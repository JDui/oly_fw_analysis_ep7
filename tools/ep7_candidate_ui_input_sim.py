#!/usr/bin/env python3
"""Run candidate GUI preprocessing, five installed wheel veneers and dispatch scope.

The original wheel service receives explicit count/status inputs. Its physical
producer, GUI engine body, widget ownership/rendering and pixels are not tested.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import (Machine, candidate_inputs, STACK, CALLER,
    CLEAR_SITE, CLEAR_RESUME, require)
from ep7_candidate_state_sim import CALL_SP
from ep7_sim_probe import brief
from penf_boot_emulator import BootState, HOOK_RETURN
from penf_emulator import Region, execute

PREP, PREP_RETURN = 0x60cfd53a,0x60cfd541
DISPATCH, DISPATCH_RETURN, ENGINE = 0x60cfd558,0x60cfd55f,0x60d1144d
SERVICE, VTABLE, WHEEL, GUI = 0x19110000,0x19110020,0x19120000,0x19130000
PACKET = CALL_SP+396
SITES = (0x60ea0070,0x60ea00f7,0x60ea0d70,0x60ea0deb,0x60ea0e66)
EVENTS = (0x9031,0x9032,0x904f,0x9051,0x9050)
SELECTORS = (1,0,2,4,3)
OUTPUTS = (0x9031,0x9032,0x9031,0x9031,0x9032)
LOGS = {0x60e9e127,0x60e9e050,0x60e9eb89}


class UiMachine(Machine):
    def write(self,address,data):
        for name,r in self.regions.items():
            if r.address<=address and address+len(data)<=r.address+len(r.data):
                self.mutate(name,address-r.address,data)
                return
        raise ValueError('boundary write outside explicit mapping '+hex(address))

    def word(self,address):
        return struct.unpack('<I',self.read(address,4))[0]

    def advance(self,stop,hooks):
        r = execute(list(self.regions.values()),self.regs,stop,limit=30000,
            trace_limit=30000,trace_tail=False,breakpoints=hooks,timeout=20,
            engine=self.engine,record_hashes=False)
        for row in r['memory']:
            self.regions[row['name']] = replace(self.regions[row['name']],data=bytes.fromhex(row['hex']))
        self.regs = r['registers']
        require(r['status'] in ('returned','breakpoint'), 'unexpected GUI stop '+str(brief(r)))
        return r


def inspect(directory,prefix,engine):
    code,syms,build = candidate_inputs(directory,prefix)
    m = UiMachine(code,engine)
    clear = m.run(CLEAR_SITE,CLEAR_RESUME)
    require(clear['status']=='returned','actual candidate cold clear failed')
    # Native constructor60cfceba specifies this entry and16KiB stack; the
    # dynamic ID/TCB ownership is an explicit single-GUI-task fixture.
    require(m.read(0x60cfcec4,20)==bytes.fromhex('fccc6750dd60420c8a014a102c00404214004218'),
            'GUI task entry constructor witness changed')
    m.mutate('tcb',16,struct.pack('<H',254))
    m.mutate('tcb',76,struct.pack('<I',0x60dd5067))
    m.mutate('tcb',84,struct.pack('<II',16384,STACK))
    m.regions['stack'] = replace(m.regions['stack'],data=b'\xcc'*16384)
    m.regions['stack_after'] = replace(m.regions['stack_after'],address=STACK+16384)
    table = bytearray(84)
    struct.pack_into('<I',table,80,WHEEL)
    rows = [Region('wheel_service_cell',0x61fa9440,struct.pack('<I',SERVICE)),
            Region('wheel_service',SERVICE,struct.pack('<I',VTABLE)),
            Region('wheel_service_table',VTABLE,bytes(table)),
            Region('wheel_input_boundary',WHEEL,b'\xcb','rx'),
            Region('input_mode_flags',0x61fc4dc0,bytes(40),'rw',True),
            Region('last_input_source',0x61fc4fa0,bytes(4),'rw',True),
            Region('native_full_wheel_count',0x61fc4fb8,bytes(2),'rw',True),
            Region('gui_machine_cell',0x61fb2564,struct.pack('<I',GUI)),
            Region('gui_machine',GUI,bytes([4,29])+bytes(10),'rw',True),
            Region('boundary_return',HOOK_RETURN,b'\xcb'*8,'rx')]
    for row in rows:
        require(all(row.address+len(row.data)<=r.address or row.address>=r.address+len(r.data)
                    for r in m.regions.values()),'GUI fixture overlaps existing mapping')
        m.regions[row.name] = row
    scope = syms['_ep7_native_ui_input_scope']
    results = []
    # Five independently installed origins, both count signs, one out-of-range
    # count and one service failure. No unchanged host suite is replayed.
    cases = [(i,7 if i!=1 else -4,0) for i in range(5)]+[(1,65,0),(1,3,1)]
    for index,delta,status in cases:
        packet = bytearray(28)
        struct.pack_into('<I',packet,0,EVENTS[index])
        struct.pack_into('<II',packet,12,123,17)
        m.write(PACKET,packet)
        m.regs = dict(m.initial,pc=PREP,sp=CALL_SP,a0=PACKET,a3=PACKET)
        initial = dict(m.regs)
        hooks = LOGS|{WHEEL,syms['_ep7_gcc_quarantine'],*SITES,*(p+5 for p in SITES)}
        stages,services,veneer = [],[],[]
        before = None
        resume_past = None
        for _ in range(30):
            r = m.advance(PREP_RETURN,hooks-({resume_past} if resume_past is not None else set()))
            resume_past = None
            stages.append(r)
            if r['status']=='returned':
                break
            pc = m.regs['pc']
            require(pc!=syms['_ep7_gcc_quarantine'],'candidate quarantined GUI input: '+hex(m.regs['d0']))
            if pc==WHEEL:
                require(m.regs['d0']==SELECTORS[index],'original preprocessor called wrong wheel selector')
                output = m.regs['a1']
                require(STACK<=output<STACK+16384-2,'wheel service output outside GUI stack')
                m.write(output,struct.pack('<h',delta))
                # CALLS uses its actual pushed return word; this synthetic RET
                # models only the hardware-facing virtual method completion.
                ret = m.word(m.regs['sp'])
                require(ret in (0x60ea0055,0x60ea00dd,0x60ea0d57,0x60ea0dd2,0x60ea0e4d),
                        'unexpected wheel virtual-call return')
                services.append(dict(selector=SELECTORS[index],count=delta,status=status,return_pc=hex(ret)))
                m.write(HOOK_RETURN,bytes.fromhex('df0000')+b'\xcb'*5)
                m.regs.update(pc=HOOK_RETURN,d0=status)
            elif pc in SITES:
                require(pc==SITES[index] and before is None,'wrong or repeated installed wheel origin')
                before = dict(m.regs)
                resume_past = pc
            elif pc in tuple(p+5 for p in SITES):
                require(before is not None and pc==SITES[index]+5,'unexpected wheel return')
                require(all(m.regs[k]==before[k] for k in ('d0','d1','d2','d3','a0','a1','a2','a3','sp')) and
                        m.regs['mdr']==pc,'wheel veneer changed original register/return ABI')
                require(m.read(0x61fc4fb8,2)==struct.pack('<h',delta) and
                        m.word(scope+48)==delta&0xffffffff,'full wheel count lost at installed veneer')
                veneer.append(dict(site=hex(SITES[index]),return_pc=hex(pc),full_count=delta,
                                   original_registers_preserved=True))
                resume_past = pc
            else:
                BootState.return_from_model(m,0)
        require(m.regs['pc']==PREP_RETURN and m.regs['sp']==CALL_SP and len(services)==1 and len(veneer)==1,
                'candidate full preprocess bridge did not complete')
        require(all(m.regs[k]==initial[k] for k in ('d2','d3','a2','a3')),
                'preprocess bridge changed preserved GUI registers')
        native_result = m.regs['d0']
        pending = m.word(scope+52)
        valid = status==0 and abs(delta)<=64
        require(pending==(2 if valid else 0),'input scope accepted/rejected wrong native result')
        normalized = 2 if OUTPUTS[index]==0x9031 and delta>=2 else 1 if delta>0 else 0xffffffff
        if not status:
            require(m.word(PACKET)==OUTPUTS[index] and m.word(PACKET+12)==normalized,
                    'native event normalization differs')
        scope_after_preprocess = m.read(scope,68).hex()
        dispatch_stages,engine_inputs = [],[]
        if native_result!=1:
            m.regs = dict(m.initial,pc=DISPATCH,sp=CALL_SP,a0=GUI,a3=PACKET,
                          d0=m.word(PACKET),a1=m.word(PACKET+12),d1=m.word(PACKET+16))
            dispatch_initial = dict(m.regs)
            for _ in range(4):
                r = m.advance(DISPATCH_RETURN,{ENGINE,syms['_ep7_gcc_quarantine']})
                dispatch_stages.append(r)
                if r['status']=='returned':
                    break
                require(m.regs['pc']==ENGINE and m.word(scope+52)==(3 if valid else 0),
                        'dispatch bridge did not retain matching pending scope')
                require(all(m.regs[k]==dispatch_initial[k] for k in ('d0','d1','a0','a1')),
                        'dispatch changed actual engine arguments')
                engine_inputs.append(dict(event=hex(m.regs['d0']),parameter=m.regs['a1'],
                                          extra=m.regs['d1'],machine=hex(m.regs['a0']),admitted=valid))
                m.regs.update(d1=0x11112222,a0=0x33334444,a1=0x55556666)
                BootState.return_from_model(m,0x1234)
            require(m.regs['pc']==DISPATCH_RETURN and m.regs['sp']==CALL_SP and
                    (m.regs['d0'],m.regs['d1'],m.regs['a0'],m.regs['a1'])==
                    (0x1234,0x11112222,0x33334444,0x55556666) and
                    all(m.regs[k]==dispatch_initial[k] for k in ('d2','d3','a2','a3')),
                    'dispatch bridge changed original engine return ABI')
        require(m.word(scope+52)==0,'completed/rejected event left a usable pending scope')
        all_stages = stages+dispatch_stages
        results.append(dict(source_event=hex(EVENTS[index]),delta=delta,service_status=status,
            native_preprocessor_result=native_result,admitted=valid,services=services,veneer=veneer,
            scope_after_preprocess=scope_after_preprocess,engine_inputs=engine_inputs,
            execution=[brief(r) for r in all_stages],
            instructions=sum(r['completed'] for r in all_stages),
            maximum_stack_below_loop_sp=CALL_SP-min(t['sp'] for r in all_stages for t in r['trace']),
            final_scope_idle=True))
    return dict(scope=__doc__,status='passed',candidate_build_revision=build['source_revision'],
                cases=results,executed_instructions_including_boundary_returns=sum(r['instructions'] for r in results),
                maximum_observed_stack_below_loop_sp=max(r['maximum_stack_below_loop_sp'] for r in results),
                native_preprocessing_executed=True,native_wheel_setter_executed=True,
                GUI_engine_body_executed=False,hash_checks_performed=False,hardware_executed=False,installable=False,
                limits=['The initialized GUI task is an explicit domain0/ID254/16KiB-stack fixture. Native current-task reads and candidate installation cohorts execute; dynamic task creation and scheduler ownership are not proved.',
                        'Original preprocessors, event normalization, five final installed JMP veneers, native count setter and candidate scope methods execute. Only the wheel virtual service count/status and logs are modeled.',
                        'The nonmodal GUI flags are explicit zero inputs; alternate modal/filter paths are not covered.',
                        'The original engine entry receives real candidate arguments, then returns a modeled result. Widget ownership, H/L editing, drawing and LCD acceptance need separate evidence.',
                        'Observed stack depth is this executed chain only; it is not a whole GUI task/IRQ upper bound.',
                        'No firmware rebuild, package change, SHA or camera operation.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--tool-prefix',required=True)
    parser.add_argument('--engine',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(inspect(args.candidate,args.tool_prefix,args.engine),indent=2))
