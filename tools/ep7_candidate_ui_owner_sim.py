#!/usr/bin/env python3
"""Run final E-P7 screen-owner hooks and original text membership/setter methods.

Screen-manager completion, allocation and display notification are explicit
boundaries. This is an offline GUI contract, not LCD or physical-camera proof.
"""
import argparse
import copy
from dataclasses import replace
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import (candidate_inputs, STACK, CALLER, CLEAR_SITE,
                                     CLEAR_RESUME, require)
from ep7_candidate_state_sim import CALL_SP, guarded
from ep7_candidate_ui_input_sim import UiMachine
from ep7_sim_probe import brief
from penf_boot_emulator import BootState, HOOK_RETURN
from penf_emulator import Region

SERVICE, OWNER = 0x19200000,0x19210000
ALLOC_BASE, TEXT = 0x19300000,0x19220000
GENERATION = 0x19220100
MANAGER, NEW, ALLOC, FREE, REDRAW = 0x60d37b53,0x60cfe5a0,0x60d109d1,0x60d109db,0x60d04feb
GUI_LOCKS = {0x60d14c70,0x60d14c94,0x60d14cb1,0x60d14cd9}
NATIVE_ENTRIES = dict(factory=0x60d337b2,attach=0x60d02beb,find=0x60d02cc2,
    bind=0x60d0487a,set_text=0x60d4c9df,cleanup=0x60d43d4b,
    bulk=0x60d42d69,destructor=0x60d7ab79,child_bulk=0x60d02c03)


class OwnerMachine(UiMachine):
    def configure(self,syms):
        self.syms=syms
        self.next_allocation=ALLOC_BASE
        self.allocations=[]
        self.events=[]
        self.fail_allocation=False
        self.gui_locks=set()

    def clone(self):
        other=copy.copy(self)
        other.regions=dict(self.regions)
        other.initial=dict(self.initial)
        other.allocations=copy.deepcopy(self.allocations)
        other.events=copy.deepcopy(self.events)
        other.gui_locks=set(self.gui_locks)
        return other

    def call_native(self,target,mask=0,frame=0,values=None):
        self.regions['caller']=Region('caller',CALLER,
            b'\xdd'+struct.pack('<i',target-CALLER)+bytes([mask,frame]),'rx')
        self.regs=dict(self.initial,pc=CALLER,sp=CALL_SP,**(values or {}))
        original=dict(self.regs)
        hooks={MANAGER,NEW,ALLOC,FREE,REDRAW,self.syms['_ep7_gcc_quarantine']}|GUI_LOCKS
        pieces=[]
        first_event=len(self.events)
        retiring=target in [self.syms['ep7_native_ui_owner_'+n+'_bridge']
                           for n in ('cleanup','bulk','destructor')]
        for _ in range(100):
            result=self.advance(CALLER+7,hooks)
            pieces.append(result)
            if result['status']=='returned':
                break
            pc=self.regs['pc']
            require(pc!=self.syms['_ep7_gcc_quarantine'],
                    'owner quarantined '+hex(self.regs['d0']))
            if pc==MANAGER:
                require(self.regs['a0']==SERVICE and self.regs['d0']==278,
                        'unexpected screen-manager contract')
                self.write(SERVICE+416,struct.pack('<I',OWNER))
                self.write(SERVICE+1378,b'\1')
                original_return=dict(d0=1,**{k:self.regs[k] for k in ('d1','a0','a1')})
                self.events.append(dict(kind='screen_completion_model',owner=hex(OWNER),
                                        return_registers=original_return))
                BootState.return_from_model(self,1)
            elif pc in (NEW,ALLOC):
                size=self.regs['d0'] if pc==NEW else self.regs['a0']
                require(0<size<=1024,'unexpected UI allocation size '+str(size))
                address=0 if self.fail_allocation else self.next_allocation
                if address:
                    self.next_allocation+=((size+15)//16)*16+32
                    name='gui_allocation_'+hex(address)
                    guarded(self,name,address,b'\xa5'*size)
                    self.allocations.append(dict(address=address,bytes=size,live=True))
                self.events.append(dict(kind='allocation_model',entry=hex(pc),bytes=size,
                                        address=hex(address),context=self.read(SERVICE+28,2).hex()))
                self.regs['a0']=address
                BootState.return_from_model(self,0)
            elif pc==FREE:
                if retiring:
                    require(self.word(self.syms['_ep7_native_ui_owner']+28)==0 and
                            self.read(self.syms['_ep7_native_ui_owner']+40,44)==bytes(44),
                            'native free reached before candidate owner/text revocation')
                address=self.regs['a0']
                found=[a for a in self.allocations if a['address']==address and a['live']]
                require(len(found)==1,'free outside live modeled allocation '+hex(address))
                found[0]['live']=False
                del self.regions['gui_allocation_'+hex(address)]
                self.events.append(dict(kind='free_model',address=hex(address)))
                BootState.return_from_model(self,0)
            elif pc==REDRAW:
                self.events.append(dict(kind='redraw_notification_model',child=hex(self.regs['a0']),
                                        mode=self.regs['d0']))
                BootState.return_from_model(self,0)
            elif pc in GUI_LOCKS:
                lock=0 if pc in (0x60d14c70,0x60d14c94) else 1
                if pc in (0x60d14c70,0x60d14cb1):
                    require(lock not in self.gui_locks,'recursive modeled GUI lock')
                    self.gui_locks.add(lock)
                else:
                    require(lock in self.gui_locks,'unpaired modeled GUI unlock')
                    self.gui_locks.remove(lock)
                self.events.append(dict(kind='single_gui_lock_model',entry=hex(pc)))
                BootState.return_from_model(self,1)
        require(self.regs['pc']==CALLER+7 and self.regs['sp']==CALL_SP and
                all(self.regs[k]==original[k] for k in ('d2','d3','a2','a3')),
                'owner native call failed return ABI')
        require(not self.gui_locks,'modeled GUI lock retained after return')
        for event in self.events[first_event:]:
            if event['kind']=='screen_completion_model':
                require(all(self.regs[k]==v for k,v in event['return_registers'].items()),
                        'screen bridge changed original completion return registers')
        require(all(len(r['trace'])==r['completed'] for r in pieces),'owner trace truncated')
        return dict(entry=hex(target),execution=[brief(r) for r in pieces],
                    instructions=sum(r['completed'] for r in pieces),
                    stack_below_call_sp=CALL_SP-min(t['sp'] for r in pieces for t in r['trace']),
                    d0=hex(self.regs['d0']),a0=hex(self.regs['a0']),events=self.events[first_event:],
                    native_entries={n:sum(t['pc']==a for r in pieces for t in r['trace'])
                                    for n,a in NATIVE_ENTRIES.items()})

    def gcc(self,name,args=()):
        if len(args)>2:
            self.write(CALL_SP+12,struct.pack('<'+'I'*(len(args)-2),*(v&0xffffffff for v in args[2:])))
        return self.call_native(self.syms[name],values={r:v&0xffffffff for r,v in zip(('d0','d1'),args)})


def owner_context(directory,prefix,engine):
    code,syms,build=candidate_inputs(directory,prefix)
    m=OwnerMachine(code,engine)
    m.configure(syms)
    cleared=m.run(CLEAR_SITE,CLEAR_RESUME)
    require(cleared['status']=='returned','candidate cold clear failed')
    m.mutate('tcb',16,struct.pack('<H',254))
    m.mutate('tcb',76,struct.pack('<I',0x60dd5067))
    m.mutate('tcb',84,struct.pack('<II',16384,STACK))
    m.regions['stack']=replace(m.regions['stack'],data=b'\xcc'*16384)
    m.regions['stack_after']=replace(m.regions['stack_after'],address=STACK+16384)
    service=bytearray(2880)
    struct.pack_into('<IH',service,0,0x60faaab4,0x101)
    struct.pack_into('<H',service,28,0xfe81)
    struct.pack_into('<H',service,80,2)
    owner=bytearray(1360)
    struct.pack_into('<IHH',owner,0,0x61032f10,0x6111,0x112)
    struct.pack_into('<I',owner,20,SERVICE)
    owner[28]=6
    struct.pack_into('<I',owner,92,0x60f94aa0)
    for name,address,data in (('ui_service',SERVICE,service),('display_owner',OWNER,owner),
                              ('text_input',TEXT,b'\xcc'*20),('generation_output',GENERATION,b'\xa5'*4)):
        guarded(m,name,address,bytes(data))
    m.regions['service_cell']=Region('service_cell',0x61fb3138,struct.pack('<I',SERVICE))
    m.regions['color_container_cell']=Region('color_container_cell',0x61fc436c,bytes(4),'rw',True)
    # No pending original GUI messages/timers in this single-task scenario.
    m.regions['gui_queue_empty']=Region('gui_queue_empty',0x6246a6f0,bytes(4),'rw',True)
    m.regions['gui_timers_empty']=Region('gui_timers_empty',0x61fb281c,bytes(280),'rw',True)
    m.regions['boundary_return']=Region('boundary_return',HOOK_RETURN,b'\xcb'*8,'rx')
    # Exact helper source from the reviewed startup copy, supplied resident.
    m.regions['native_helper']=Region('native_helper',0x47000800,
        code[0x6143ca00-0x60020020:0x6143e200-0x60020020],'rx')
    initialized=m.call_native(0x60cfef4e,values=dict(a0=OWNER+96))
    screen=m.call_native(syms['ep7_native_ui_screen_bridge'],values=dict(a0=SERVICE,d0=278))
    return m,syms,build,[initialized,screen]


def inspect(directory,prefix,engine):
    m,syms,build,rows=owner_context(directory,prefix,engine)
    state=syms['_ep7_native_ui_owner']
    child=m.word(state+56)
    node=m.word(OWNER+96)
    require(m.word(state+28)==OWNER and m.word(state+32)==1 and
            m.word(state+40)==m.word(state+44)==m.word(state+64)==1 and
            m.word(state+60)==m.word(state+76)==OWNER and m.word(state+80)==0,
            'completed request278 did not establish ready owner/text membership')
    require(m.read(child,8)==struct.pack('<IHH',0x60faec7c,0x8010,0x7e10) and
            m.word(child+20)==OWNER and m.read(child+28,2)==b'\6\0',
            'original factory/bind produced the wrong text object')
    require(m.read(node,12)==struct.pack('<3I',OWNER+96,OWNER+96,child) and
            m.word(OWNER+100)==node and m.read(m.word(child+156),2)==b'\0\0',
            'native list/text initialization differs')
    require(all(rows[1]['native_entries'][n]>=1 for n in ('factory','attach','find','bind','set_text')),
            'original factory/membership/setter path was not executed')
    require(m.read(SERVICE+28,2)==b'\x81\xfe','factory changed prior service context')
    for label in ('H 01 +3','L ALL -2','L ALL -2'):
        data=(label+'\0').encode('utf-16le')
        m.write(TEXT,data)
        row=m.gcc('_ep7u_present',[TEXT,GENERATION])
        row['label']=label
        require(row['d0']=='0x1' and m.word(GENERATION)==1 and
                m.read(m.word(child+156),len(data))==data and
                m.read(SERVICE+28,2)==b'\x81\xfe' and m.word(state+80)==0,
                'native text update, generation, hold release or context restore failed')
        rows.append(row)
    require(rows[-1]['events']==[],'same native text was unnecessarily reallocated/redrawn')
    healthy=m.clone()

    # Setter OOM after freeing the old string must close admission permanently
    # for this owner; parent membership is retained for normal native cleanup.
    failed=healthy.clone()
    failed.fail_allocation=True
    failed.write(TEXT,'H 02 -7\0'.encode('utf-16le'))
    failed.write(GENERATION,b'\xa5'*4)
    oom=failed.gcc('_ep7u_present',[TEXT,GENERATION])
    oom['scenario']='text allocation failure'
    require(oom['d0']=='0x0' and failed.word(child+156)==0 and
            failed.read(state+40,8)==bytes(8) and failed.word(state+56)==child and
            failed.word(state+64)==1 and failed.word(state+80)==0 and
            failed.read(GENERATION,4)==b'\xa5'*4 and failed.read(SERVICE+28,2)==b'\x81\xfe',
            'failed setter left admission active or lost parent-owned child/context')
    rows.append(oom)
    denied=failed.gcc('_ep7u_present',[TEXT,GENERATION])
    denied['scenario']='update after allocation failure'
    require(denied['d0']=='0x0' and not denied['events'],'failed owner retried widget allocation')
    rows.append(denied)

    retirements=[]
    # Two distinct native retirement implementations plus destructor after the
    # cleanup path. Original queue/timer lists are explicitly empty inputs.
    for method,case in (('cleanup',healthy.clone()),('bulk',failed.clone())):
        row=case.call_native(syms['ep7_native_ui_owner_'+method+'_bridge'],values=dict(a0=OWNER))
        row['scenario']=method
        require(case.word(state+28)==0 and case.word(state+32)==2 and
                case.read(state+40,44)==bytes(44) and not any(a['live'] for a in case.allocations),
                'native retirement leaked modeled allocations or retained candidate owner')
        require(case.word(OWNER+96)==case.word(OWNER+100)==OWNER+96,
                'original child list not empty after retirement')
        require(row['native_entries'][method]==1 and row['native_entries']['child_bulk']==1,
                'original retirement path bypassed')
        rows.append(row)
        stale=case.gcc('_ep7u_present',[TEXT,GENERATION])
        stale['scenario']='valid text update after '+method
        require(stale['d0']=='0x0' and not stale['events'],'retired owner accepted stale update')
        rows.append(stale)
        if method=='cleanup':
            destructor=case.call_native(syms['ep7_native_ui_owner_destructor_bridge'],values=dict(a0=OWNER))
            require(destructor['native_entries']['destructor']==1 and
                    destructor['a0']=='0x60cfe5c9' and not destructor['events'],
                    'owner destructor did not preserve original deallocator return')
            rows.append(destructor)
        retirements.append(dict(method=method,live_allocations=0,generation=case.word(state+32),
                                freed_payloads_unmapped=True,stale_update_rejected=True))
    return dict(scope=__doc__,status='passed',candidate_build_revision=build['source_revision'],
                total_instructions=sum(r['instructions'] for r in rows),
                maximum_observed_stack_below_call_sp=max(r['stack_below_call_sp'] for r in rows),
                calls=rows,retirements=retirements,original_child=hex(child),
                boundaries=['request278 completed native service/owner graph supplied explicitly',
                    'GUI task identity/16KiB stack and resident copy are explicit existing contracts',
                    'allocation/free, redraw notification and single-GUI lock operations modeled',
                    'original GUI queue/timer arrays empty; display renderer and concurrent producers not run',
                    'MVC is unregistered here; no editing receipt, LCD pixels or physical input qualification'],
                historical_frontier=['first cleanup stopped at original GUI lock cell61fb2a28 before explicit lock/empty-queue model',
                    'first CLI rejected a probe counter aimed at prologue60d02bfe; native CALL actually targets inner entry60d02c03 with frame32'],
                hash_checks_performed=False,hardware_executed=False,installable=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--tool-prefix',required=True)
    p.add_argument('--engine',type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(inspect(args.candidate,args.tool_prefix,args.engine),indent=2))
