#!/usr/bin/env python3
"""Join candidate MVC/editor/text with the production private lock and capture.

Native GUI construction completion, mode inputs and engine delivery are explicit
contracts. Final candidate and original methods execute; no LCD/camera claim.
"""
import argparse
import json
from pathlib import Path
import struct

from ep7_candidate_startup_sim import require
from ep7_candidate_static_kernel_sim import inspect as static_kernel
from ep7_candidate_ui_owner_sim import owner_context, OWNER, SERVICE
from ep7_candidate_state_sim import guarded, CALL_SP
from ep7_candidate_ui_input_sim import (PREP,PREP_RETURN,DISPATCH,DISPATCH_RETURN,
    ENGINE,PACKET,LOGS,SERVICE as WHEEL_SERVICE,VTABLE,WHEEL,GUI)
from penf_boot_emulator import BootState, HOOK_RETURN
from penf_emulator import Region

CONTAINER,PARENT,SELECTOR,VIEWER,MASKS = (0x19400000,0x19401000,0x19402000,0x19403000,0x19404000)
PROP,PROP_TABLE,PROP_GET = 0x19405000,0x19405040,0x19405080
CAPTURE_OUT = 0x19406000
DRAW_BOUNDARIES = {0x60e26c03,0x60ea4c1c,0x60cfeca9}


def virtual_return(m,value=0):
    m.write(HOOK_RETURN,b'\xdf\0\0'+b'\xcb'*5)
    m.regs.update(pc=HOOK_RETURN,d0=value)


def property_input(m):
    require(m.regs['a0']==PROP and m.regs['d0'] in (111,426),'unexpected GUI property input')
    value=m.public_mode if m.regs['d0']==111 else 0
    m.write(m.regs['a1'],struct.pack('<I',value))
    m.events.append(dict(kind='property_input_model',property=m.regs['d0'],value=value))
    virtual_return(m)


def draw_output(m):
    m.events.append(dict(kind='display_output_model',entry=hex(m.regs['pc'])))
    BootState.return_from_model(m,0)


def wheel_input(m):
    require(m.regs['d0']==(1 if m.wheel_event==0x9031 else 0),'unexpected wheel selector')
    m.write(m.regs['a1'],struct.pack('<h',m.wheel_delta))
    m.events.append(dict(kind='wheel_input_model',event=hex(m.wheel_event),delta=m.wheel_delta))
    virtual_return(m)


def log_output(m):
    m.events.append(dict(kind='original_log_model',entry=hex(m.regs['pc'])))
    BootState.return_from_model(m,0)


def engine_delivery(m):
    saved=dict(m.regs)
    scope=m.syms['_ep7_native_ui_input_scope']
    require(m.word(scope+52)==3 and saved['a0']==GUI,'engine did not receive admitted scope')
    nested_sp=saved['sp']-256
    m.write(nested_sp+8,struct.pack('<I',saved['a1']))
    require(m.read(0x60e4d0ff,2)==b'\xf0\xf1' and
            m.word(m.word(PARENT))==m.syms['ep7_native_ui_event_bridge'],
            'actual container CALLS or installed parent target changed')
    parent=m.call_native(m.syms['ep7_native_ui_event_bridge'],
        values=dict(sp=nested_sp,d2=saved['d0'],a3=CONTAINER),entry=0x60e4d0f5,stop=0x60e4d101)
    m.nested_calls.append(parent)
    result=int(parent['d0'],16)
    require(m.word(scope+64)==1,'parent did not consume this event')
    if result==1:
        draw=m.call_native(m.syms['ep7_native_ui_viewer_bridge'],values=dict(sp=nested_sp,a0=VIEWER))
        m.nested_calls.append(draw)
    if m.check_replay:
        replay=m.call_native(m.syms['ep7_native_ui_event_bridge'],
            values=dict(sp=nested_sp,d2=saved['d0'],a3=CONTAINER),entry=0x60e4d0f5,stop=0x60e4d101)
        require(replay['d0']=='0x0','same engine event was applied twice')
        replay['scenario']='same admitted event replay rejected'
        m.nested_calls.append(replay)
    m.events.append(dict(kind='engine_delivery_model',event=hex(saved['d0']),parameter=saved['a1'],
                         actual_parent_call='0x60e4d0ff',result=result,replay_checked=m.check_replay))
    m.regs=saved
    BootState.return_from_model(m,result)


def input_context(m,syms):
    table=bytearray(84)
    struct.pack_into('<I',table,80,WHEEL)
    gui=bytearray(12)
    gui[:2]=bytes([4,29])
    struct.pack_into('<H',gui,8,137)
    rows=[Region('wheel_service_cell',0x61fa9440,struct.pack('<I',WHEEL_SERVICE)),
        Region('wheel_service',WHEEL_SERVICE,struct.pack('<I',VTABLE)),
        Region('wheel_service_table',VTABLE,bytes(table)),
        Region('wheel_input_boundary',WHEEL,b'\xcb','rx'),
        Region('input_mode_flags',0x61fc4dc0,bytes(40),'rw',True),
        Region('last_input_source',0x61fc4fa0,bytes(4),'rw',True),
        Region('native_full_wheel_count',0x61fc4fb8,bytes(2),'rw',True),
        Region('gui_machine_cell',0x61fb2564,struct.pack('<I',GUI)),
        Region('gui_machine',GUI,bytes(gui),'rw',True),
        Region('ui_input_gate',syms['_ep7_stock_ui_input_gate_unresolved'],bytes(4),'rw',True),
        Region('ui_repeat_context',syms['_ep7_stock_ui_repeat_context_unresolved'],bytes(4),'rw',True)]
    for row in rows:
        require(all(row.address+len(row.data)<=r.address or row.address>=r.address+len(r.data)
                    for r in m.regions.values()),'editor input mapping overlaps existing region')
        m.regions[row.name]=row
    m.boundaries.update({WHEEL:wheel_input,ENGINE:engine_delivery,**{p:log_output for p in LOGS}})


def wheel_event(m,syms,event,delta,*,replay=False):
    m.wheel_event,m.wheel_delta,m.check_replay=event,delta,replay
    m.nested_calls=[]
    packet=bytearray(28)
    struct.pack_into('<I',packet,0,event)
    struct.pack_into('<II',packet,12,123,17)
    m.write(PACKET,packet)
    prep=m.call_native(syms['ep7_native_ui_preprocess_bridge'],values=dict(a0=PACKET,a3=PACKET),
                      entry=PREP,stop=PREP_RETURN)
    require(prep['d0']=='0x0' and m.word(syms['_ep7_native_ui_input_scope']+52)==2,
            'real original preprocessor did not produce pending input')
    dispatch=m.call_native(syms['ep7_native_ui_dispatch_bridge'],
        values=dict(a0=GUI,a3=PACKET,d0=m.word(PACKET),a1=m.word(PACKET+12),d1=m.word(PACKET+16)),
        entry=DISPATCH,stop=DISPATCH_RETURN)
    require(m.word(syms['_ep7_native_ui_input_scope']+52)==0,'input scope survived engine completion')
    return [prep,dispatch,*m.nested_calls]


def editor_graph(m,syms):
    m.public_mode=54
    m.boundaries.update({PROP_GET:property_input,**{p:draw_output for p in DRAW_BOUNDARIES}})
    objects=[('mvc_container',CONTAINER,228),('mvc_parent',PARENT,100),
        ('mvc_selector',SELECTOR,124),('mvc_viewer',VIEWER,408),('mvc_masks',MASKS,12)]
    for name,address,size in objects:
        guarded(m,name,address,bytes(size))
    m.write(CONTAINER,struct.pack('<4I',PARENT,VIEWER,0x34,0x84))
    m.write(PARENT,struct.pack('<I',0x6118957c))
    m.write(PARENT+76,struct.pack('<I',SELECTOR))
    m.write(VIEWER,struct.pack('<I',0x61189ba8))
    m.write(VIEWER+384,struct.pack('<I',PARENT))
    m.write(SELECTOR,struct.pack('<I',0x6114f7e4))
    m.write(SELECTOR+80,struct.pack('<IHHII',193,6,2,MASKS,syms['_ep7s_categories']))
    rows=[Region('property_service_cell',0x61fa96ac,struct.pack('<I',PROP)),
        Region('property_service',PROP,struct.pack('<I',PROP_TABLE)),
        Region('property_service_table',PROP_TABLE,struct.pack('<3I',0,0,PROP_GET)),
        Region('property_input',PROP_GET,b'\xcb','rx'),
        Region('selector_remembered',0x61fc26ae,struct.pack('<H',2),'rw',True),
        Region('stop535_state',0x61fc1bbc,bytes(4),'rw',True),
        Region('current_screen_request',0x61fc28c8,struct.pack('<I',278),'rw',True)]
    for row in rows:
        m.regions[row.name]=row
    calls=[m.gcc('_ep7m_gui_begin')]
    m.write(0x61fc436c,struct.pack('<I',CONTAINER))
    calls.append(m.gcc('_ep7m_gui_complete',[CONTAINER]))
    return calls


def select_category(m,syms,category):
    m.write(SELECTOR+86,struct.pack('<H',category))
    rebuilt=m.call_native(syms['ep7_native_content_rebuild_bridge'],0xf0,28,dict(a0=PARENT))
    drawn=m.call_native(syms['ep7_native_ui_viewer_bridge'],values=dict(a0=VIEWER))
    return [rebuilt,drawn]


def rendered(m,syms,category,label):
    content=m.word(PARENT+80)
    receipt=struct.unpack('<8I',m.read(syms['_ep7_native_ui_receipt'],32))
    require(receipt==(VIEWER,content,1,1,1,54,category,1),'matching editor receipt not published')
    require(m.word(content)==syms['ep7_native_content_vtable'] and
            m.read(content+48,8)==struct.pack('<II',1,category),
            'H/L content not owned by current MVC generation')
    require(m.read(VIEWER+388,20)==struct.pack('<IIHHII',SELECTOR,content,category,0,54,0),
            'original viewer did not cache current selector/content/category/mode')
    require(m.read(MASKS+8,4)==bytes(4),'ready H/L categories were masked')
    text_child=m.word(syms['_ep7_native_ui_owner']+56)
    text=(label+'\0').encode('utf-16le')
    require(m.read(m.word(text_child+156),len(text))==text,'native displayed text differs '+label)
    require(m.read(SERVICE+28,2)==b'\x81\xfe','GUI failed to restore service context')
    return dict(category=category,label=label,content=hex(content),receipt=list(receipt))


def inspect(directory,prefix,engine):
    base,syms,build,setup=static_kernel(directory,prefix,engine,context_only=True)
    m,syms,build,calls=owner_context(None,None,None,runtime_context=(base,syms,build))
    calls+=editor_graph(m,syms)
    require(m.word(syms['_ep7_native_ui_model'])==setup['runtime'],
            'GUI attached to a different worker/capture runtime')
    calls+=select_category(m,syms,4)
    displays=[rendered(m,syms,4,'H 01 +0')]
    content=m.word(PARENT+80)
    input_context(m,syms)
    for event,delta,label,replay in ((0x9032,3,'H 01 +3',True),
            (0x9031,2,'H 03 +0',False),(0x9032,-2,'H 03 -2',False)):
        calls+=wheel_event(m,syms,event,delta,replay=replay)
        displays.append(rendered(m,syms,4,label))
    calls+=select_category(m,syms,5)
    require(m.word(PARENT+80)==content,'H-to-L transition replaced owned content unnecessarily')
    displays.append(rendered(m,syms,5,'L 03 +0'))
    calls+=wheel_event(m,syms,0x9032,-4)
    displays.append(rendered(m,syms,5,'L 03 -4'))
    guarded(m,'editor_capture_out',CAPTURE_OUT,b'\xcc'*25)
    calls.append(m.gcc('_ep7p_capture',[setup['core'],11,1,CAPTURE_OUT]))
    hue=[3,0,-2]+[0]*9
    lightness=[0,0,-4]+[0]*9
    snapshot=bytes([0]+[n&255 for n in hue+lightness])
    require(calls[-1]['d0']=='0x1' and m.read(CAPTURE_OUT,25)==snapshot,
            'capture did not freeze exactly the GUI-edited COLOR1 values')

    calls.append(m.gcc('_ep7m_before_gui_exit'))
    require(m.word(syms['_ep7_native_ui_receipt']+28)==0 and
            m.word(syms['_ep7_native_ui_model']+56)==0 and
            m.read(syms['_ep7_native_mvc']+44,32)==bytes(32),
            'GUI exit retained receipt/session/graph references')
    # Graph/parent teardown is the explicit completion contract. Execute the
    # actual owned content destructor/free and original text-owner cleanup.
    calls.append(m.gcc('_ep7_gcc_mvc_dispose',[content]))
    calls.append(m.call_native(syms['ep7_native_ui_owner_cleanup_bridge'],values=dict(a0=OWNER)))
    for name in ('mvc_container','mvc_parent','mvc_selector','mvc_viewer','mvc_masks'):
        del m.regions[name]
    late=m.gcc('_ep7v_refresh')
    require(not late['events'] and not any(a['live'] for a in m.allocations) and
            m.read(CAPTURE_OUT,25)==snapshot,'late refresh accessed retired graph or changed frozen settings')
    calls.append(late)
    lock_calls=[c for r in calls for c in r['native_private_lock_calls']]
    require(lock_calls and all(c['handle']==133 and c['status']==0 for c in lock_calls) and
            m.word(setup['private_object']+24)==1 and m.word(setup['provider']+20)==0 and
            m.read(setup['provider']+24,1)==b'\0','editor/capture failed to release production private lock')
    return dict(scope=__doc__,status='passed',candidate_build_revision=build['source_revision'],
        gui_instructions_including_modeled_returns=sum(r['instructions'] for r in calls),
        maximum_observed_stack_below_loop_sp=CALL_SP-min(int(r['minimum_sp'],16) for r in calls),
        calls=calls,runtime_setup=setup,displays=displays,
        capture=dict(raw_mode=11,selector=1,profile=0,hue=hue,lightness=lightness,bytes=snapshot.hex()),
        native_private_lock_operations=len(lock_calls),private_lock_id=133,
        shared_runtime=True,replay_rejected=True,late_refresh_after_graph_unmap=True,live_allocations=0,
        boundaries=['GUI task/TCB and request278 owner completion retain the preceding owner contract',
            'MVC construction boundary supplies container/parent/selector/viewer graph with category2/contentNULL; stock content creation/disposal not run; no direct private-state injection',
            'property111=54 and property426=0 are explicit service inputs, not a measured camera mode',
            'wheel count service/logs modeled; original preprocess/hash dispatch/normalization/installed veneer executed',
            'engine body modeled to deliver at actual container callsite60e4d0f5..101 and then draw when changed',
            'original viewer caches and branch execute; header formatting60e26c03 and two display output helpers modeled',
            'allocation/free and two GUI locks modeled; private core lock ID133 executes original poll/signal',
            'graph teardown completion modeled; owned content destructor, text owner cleanup and late revocation execute',
            'observed stack includes the explicit256B engine-delivery frame, not the real engine/renderer/IRQ upper bound',
            'capture here is the shared core freeze API; capture association, worker, photo pixels and residency retain separate evidence'],
        hash_checks_performed=False,hardware_executed=False,installable=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--tool-prefix',required=True)
    p.add_argument('--engine',type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(inspect(args.candidate,args.tool_prefix,args.engine),indent=2))
