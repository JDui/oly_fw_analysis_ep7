#!/usr/bin/env python3
"""Run stock or experimental tone input on a private decoded 015 model."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct
import subprocess
from tempfile import TemporaryDirectory

from ep7_candidate_ui_owner_sim import OwnerMachine, SERVICE
from ep7_candidate_startup_sim import BASE, STACK
from ep7_candidate_state_sim import guarded
from ep7_candidate_ui_editor_sim import virtual_return, CONTAINER, VIEWER
from ep7_offline_candidate import replacement
from penf_boot_emulator import BootState, HOOK_RETURN
from penf_emulator import Region

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--gui-core', type=int, choices=(0,1,2), default=0)
parser.add_argument('--out', type=Path)
variants=parser.add_mutually_exclusive_group()
variants.add_argument('--experiment', action='store_true',
                    help='link and apply test-only veneer bytes in emulator memory')
variants.add_argument('--staged', action='store_true',
                      help='link real UI and volatile settings code in emulator memory')
variants.add_argument('--candidate', type=Path,
                      help='use a directly linked NON-INSTALLABLE candidate directory')
args=parser.parse_args()
mapping_only=False
staged=args.staged or bool(args.candidate)
experiment=args.experiment or staged

engine=Path('/work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu')
baseline=Path('/repo/generated/ep7/flash-build-015')
prefix='/work/install/bin/mn10300-elf-'
if args.candidate:
    report=json.loads((args.candidate/'report.json').read_text())
    assert report['status']=='NON-INSTALLABLE laboratory decoded image'
    mapping_only=report.get('strategy')=='highlight_mapping_only'
    data=(args.candidate/report['image']).read_bytes()
else:
    data=(baseline/'EP7HSL-NONINSTALLABLE.decoded-main.bin').read_bytes()
m=OwnerMachine(data,engine)
m.regions['cpu_id']=replace(m.regions['cpu_id'],data=struct.pack('<I',args.gui_core))
m.configure({'_ep7_gcc_quarantine':0xdeadbeef,**{f'ep7_native_ui_owner_{s}_bridge':0xdeadbeef for s in ('cleanup','bulk','destructor')}})
m.regions['stack']=replace(m.regions['stack'],data=bytes(16384))
m.regions['stack_after']=replace(m.regions['stack_after'],address=STACK+16384)
m.regions['ui_service']=Region('ui_service',SERVICE,bytes(64),'rw',True)
m.regions['boundary_return']=Region('boundary_return',HOOK_RETURN,bytes(8),'rx')
m.regions['native_helper']=Region('native_helper',0x47000800,m.read(0x6143ca00,0x1800),'rx')
m.regions['native_init']=Region('native_init',0x61f98540,m.read(0x60230800,0x2e350),'rw',True)

HDR_OWNER, HDR_LEVEL=0x18f00000,0x18f00004
ACTIVE, ACTIVE_PART, COLOR1_CELL=0x6250ba00,1769,963
ACTIVE_LEVELS={0:0,0x445201fe:1,0x445202fd:2}


def read_symbols(elf):
    return {fields[2]:int(fields[0],16)
            for line in subprocess.check_output([prefix+'nm',elf],text=True).splitlines()
            if len(fields:=line.split())==3}


if args.candidate:
    linked=read_symbols(args.candidate/report['image'].replace('.decoded-main.bin','.elf'))
elif experiment:
    code_start=0x18e00000
    source=Path(__file__).with_name('single-dr-curve-ui-experiment.s')
    stock=dict(child_redraw=0x60defe80,info=0x60defcd8,dial_9031=0x60def91e,
               dial_9032=0x60def75a,reset=0x60defc4b,child_return=0x60defe91,
               touch=0x60defe88,viewer_publish=0x60e26bb8,curve_draw=0x60e27639,
               factory=0x60dd518e,ctor_restore=0x60df01e1,ctor_first_page=0x60df01c6)
    if staged:
        stock.update(rebuild_resume=0x60e266ae,destroy=0x60e26130)
        definitions=[f'--defsym=ep7dr_stock_ui_{name}_unresolved={address:#x}'
                     for name,address in stock.items()]
        symbols=json.loads((baseline/'symbols.json').read_text())
        definitions += [f"--defsym=_ep7h_stock_value={symbols['_ep7h_stock_value']['address']}",
                        '--defsym=_ep7dr_stock_key=0x19502040']
    else:
        definitions=[f'--defsym=stock_{name}={address:#x}' for name,address in stock.items()]
    with TemporaryDirectory(prefix='single-dr-curve-ui-') as tmp:
        obj,elf,code=(Path(tmp)/name for name in ('veneer.o','veneer.elf','veneer.bin'))
        objects=[obj]
        if staged:
            directory=Path('/repo/prototypes/ep7_volatile_hl/native_single_dr')
            source=directory/'ui.s'
            for name in ('ui','settings'):
                output=Path(tmp)/(name+'.o')
                subprocess.run([prefix+'gcc','-std=c11','-O2','-ffreestanding','-fno-builtin',
                                '-mno-setlb','-mno-liw','-Wall','-Wextra','-Werror','-c',
                                '-DEP7DR_LAB_STAGING',
                                directory/(name+'.c'),'-o',output],check=True)
                objects.append(output)
        subprocess.run([prefix+'as','-o',obj,source],check=True)
        entry='ep7dr_ui_info_bridge' if staged else 'experiment_info'
        subprocess.run([prefix+'ld','-Ttext',hex(code_start),'-Tbss',hex(HDR_OWNER),'-e',entry,
                        *definitions,'-o',elf,*objects],check=True)
        subprocess.run([prefix+'objcopy','-O','binary','-j','.text','-j','.rodata',elf,code],check=True)
        linked=read_symbols(elf)
        m.regions['experiment_code']=Region('experiment_code',code_start,code.read_bytes(),'rx')

if experiment:
    if staged:
        for name in ('info','reset','touch','dial_9031','dial_9032','draw','rebuild','destroy',
                     'content_factory','restore_page'):
            symbol={'content_factory':'factory','restore_page':'restore'}.get(name,name)
            linked['experiment_'+name]=linked['ep7dr_ui_'+symbol+'_bridge']
        HDR_OWNER=linked['_ep7dr_ui_child']
        if not args.candidate:
            HDR_LEVEL=linked['_staged_levels']+4
        else:
            assert '_staged_levels' not in linked, 'candidate needs the real ACTIVE setting'
    syms={name:{'address':address} for name,address in linked.items()}
    if not args.candidate:
        state_start=min(HDR_OWNER,linked['_ep7dr_ui_building_curve'],HDR_LEVEL-4) if staged else HDR_OWNER
        state_end=linked['_end'] if staged else HDR_OWNER+12
        m.regions['experiment_state']=Region('experiment_state',state_start,bytes(state_end-state_start),'rw',True)

    def patch(site,old,target,encoding,**options):
        row=dict(site=hex(site),bytes=len(old),
                 replacement=dict(encoding=encoding,target_symbol='experiment_'+target,**options))
        after=replacement(row,syms)[0]
        if args.candidate:
            assert m.read(site,len(old))==after, f'linked UI edge mismatch at {site:#x}'
        else:
            assert m.read(site,len(old))==old, f'015 preimage changed at {site:#x}'
            m.mutate('candidate',site-BASE,after)

    for site,old,target in (
            (0x61159e74,0x60defcd8,'info'),(0x61159e44,0x60defc4b,'reset'),
            (0x61159e7c,0x60defe88,'touch'),(0x61159ee4,0x60def75a,'dial_9032'),
            (0x61159ee8,0x60def91e,'dial_9031')):
        patch(site,struct.pack('<I',old),target,'absolute_le32')
    patch(0x60e26bb1,bytes.fromhex('9c91cd860af034'),'draw','JMP32_NOP_suffix',nop_count=2)
    patch(0x60e2677d,bytes.fromhex('dd11eafaffe010'),'content_factory','CALL32',mask=0xe0,frame=16)
    patch(0x60df01be,bytes.fromhex('5818fac8800c'),'restore_page','JMP32_NOP_suffix',nop_count=1)
    if staged:
        patch(0x60e266a9,bytes.fromhex('f1d3004204'),'rebuild','JMP32_NOP_suffix',nop_count=0)
        patch(0x611895a4,struct.pack('<I',0x60e26130),'destroy','absolute_le32')
        m.regions['settings_service_ready']=Region('settings_service_ready',0x62253594,
                                                   struct.pack('<I',(ACTIVE+(0x40000000 if args.gui_core else 0)) if args.candidate else 1),'rw',True)
        for addr,size in ((0x62257b04,1),(0x622484fa,1),(0x6223daa2,1),
                          (0xa2715c8c,4)):
            m.regions[f'setting_gate_{addr:x}']=Region(f'setting_gate_{addr:x}',addr,bytes(size),'rw',True)
    if args.candidate:
        m.regions['typed_payload']=Region('typed_payload',0xa2715acc,bytes(448),'rw',True)
        active=m.read(0x600b90cc,3560*4)
        m.regions['active']=Region('active',ACTIVE,active,'rw',True)
        m.regions['active_alias']=Region('active_alias',ACTIVE+0x40000000,active,'rw',True,
                                          alias_of='active')
        m.regions['readonly_bank_root']=Region('readonly_bank_root',0xa2711a88,
                                                struct.pack('<I',0x60078e2c),'rw',True)


def selected_level(cell=COLOR1_CELL):
    if not args.candidate:
        return m.word(HDR_LEVEL)
    addr=ACTIVE+4*(ACTIVE_PART+cell)
    value=m.word(addr)
    assert value==m.word(addr+0x40000000)
    return ACTIVE_LEVELS.get(value,0)

MACHINE, ARGS=0x19407000,0x19407100
for name,a,size in [('container',CONTAINER,228),('viewer',VIEWER,408),('machine',MACHINE,12),('args',ARGS,6)]:
    guarded(m,name,a,bytes(size))
def word(a,v):m.write(a,struct.pack('<I',v))
def half(a,v):m.write(a,struct.pack('<H',v))
def u16(a):return struct.unpack('<H',m.read(a,2))[0]

PROP,PVT,GET,SET,DEFAULT=0x19500000,0x19501000,0x19502000,0x19503000,0x19504000
LOOKUP,LVT,LOOKUP_GET=0x19505000,0x19506000,0x19507000
TIMER,TVT,TLIST=0x19508000,0x19509000,0x1950a000
for name,a,d in [('prop',PROP,struct.pack('<I',PVT)),('property_vtable',PVT,bytes(156)),('lookup',LOOKUP,struct.pack('<I',LVT)),('lookup_vtable',LVT,bytes(380)),('timer',TIMER,struct.pack('<I',TVT)),('timer_vtable',TVT,bytes(48))]:
    m.regions[name]=Region(name,a,d,'rw',True)
for a in [GET,SET,DEFAULT,LOOKUP_GET,TLIST]:
    m.regions['stub_'+hex(a)]=Region('stub_'+hex(a),a,b'\xcb','rx')
word(0x61fa96ac,PROP)
word(PVT+8,GET)
word(PVT+0,SET)
word(PVT+120,LOOKUP_GET)
word(PVT+152,DEFAULT)
word(LVT+0,LOOKUP_GET)
word(LVT+20,LOOKUP_GET)
word(LVT+376,LOOKUP_GET)
word(TVT+44,TLIST)
properties={111:54,1088:383,963:2,964:1,965:-1,384:2,694:1,383:-1}
raw_properties={0x810a:2048,0x9481:11,0xf6b1:1,0x8141:1}
updates=[]
def getter(m):word(m.regs['a1'],properties.get(m.regs['d0'],0)&0xffffffff);virtual_return(m)
def setter(m):
    p,v=m.regs['d0'],m.regs['a1']
    if m.regs['d1']==0:
        properties[p]=v if v<0x80000000 else v-0x100000000
    updates.append((p,v))
    virtual_return(m)
def default(m):word(m.regs['a1'],0);virtual_return(m)
def neutral(m):virtual_return(m)
def timer(m):m.write(m.regs['a1'],bytes(192));virtual_return(m)
def boundary(m):BootState.return_from_model(m,0)
def lookup(m):m.regs['a0']=LOOKUP;BootState.return_from_model(m,0)
def timer_service(m):m.regs['a0']=TIMER;BootState.return_from_model(m,0)
def drop(m):m.events.append({'kind':'drop','event':hex(m.regs['d0'])});BootState.return_from_model(m,0)
touch_button=0
def touch_packet(m):
    packet=bytearray(22)
    struct.pack_into('<H',packet,2,12)
    struct.pack_into('<H',packet,18,touch_button)
    m.write(m.regs['a0'],packet)
    BootState.return_from_model(m,0)
def array_new(m):
    size=m.regs['d0']
    address=m.next_allocation
    m.next_allocation+=((size+15)//16)*16+32
    guarded(m,'gui_allocation_'+hex(address),address,bytes(size))
    m.allocations.append(dict(address=address,bytes=size,live=True))
    m.regs['a0']=address
    BootState.return_from_model(m,0)
def array_delete(m):
    address=m.regs['a0']
    allocation=next(item for item in m.allocations if item['address']==address and item['live'])
    allocation['live']=False
    del m.regions['gui_allocation_'+hex(address)]
    m.events.append(dict(kind='free_model',address=hex(address)))
    BootState.return_from_model(m,0)
def viewer_desc(m):m.events.append({'kind':'descriptor','type':m.word(m.regs['a0'])});BootState.return_from_model(m,0)
def viewer_props(m):
    a=m.regs['a0']-4
    labels=[]
    for offset in (186,260):
        if u16(a+offset)==5:
            labels.append(m.read(a+offset+8,52).decode('utf-16le').split('\0',1)[0])
    m.events.append({'kind':'render_properties','tone_flags':m.read(a+174,8).hex(),'labels':labels})
    BootState.return_from_model(m,0)
m.boundaries.update({GET:getter,SET:setter,DEFAULT:default,LOOKUP_GET:neutral,TLIST:timer,
    0x60a4ec0d:array_new,0x60a4ec21:array_delete,0x607b3c32:lookup,0x607af9ce:lookup,
    0x60cf779d:timer_service,0x60d1050a:drop,
    0x60ea4c1c:viewer_desc,0x60cfeca9:viewer_props,0x60ea4c56:touch_packet})
if staged:
    def raw_mode(m):
        assert m.regs['d0']==111
        BootState.return_from_model(m,properties[111])
    # The actual 015 bridge executes; its settings database lives below this boundary.
    m.boundaries[0x602afa81]=raw_mode
    def raw_key(m):
        if args.candidate and m.regs['a0']:
            # Preserve the native explicit-pointer accessor used for ACTIVE.
            m.regs.update(d3=m.regs['d1'],d2=m.regs['d0'],pc=0x6005e987)
            return
        BootState.return_from_model(m,raw_properties.get(m.regs['d0'],0))
    m.boundaries[0x6005e971 if args.candidate else 0x19502040]=raw_key
for a in [0x60e9e085,0x60ea15a3,0x60ea15ca,0x60cfec91,0x60e26c03,0x60ea12ca,0x60ea26fb,0x60ea114b,0x60ea4bef]:
    m.boundaries[a]=boundary

queued_callbacks=[]
color_refreshes=[]
if args.candidate and report.get('color_refresh_after_hdr_edit'):
    # Execute the original 015 adapter and per-profile native callback.
    # Property database lookup and effective-settings publication are service
    # boundaries, as in the existing HSL model; do not claim live pixels here.
    m.boundaries[0x602b0b48]=raw_mode
    def color_refresh(m):
        assert m.regs['d0']==0
        head,tail=u16(0xa2715c8c),u16(0xa2715c8e)
        if args.gui_core:
            assert head!=tail and queued_callbacks, 'refresh preceded HDR enqueue'
            slot=(head-1)&15
            assert u16(0xa2715acc+28*slot+4)==ACTIVE_PART+COLOR1_CELL
            value=m.word(0xa2715acc+28*slot+12)
        else:
            assert head==tail, 'direct refresh with pending writes'
            value=m.word(ACTIVE+4*(ACTIVE_PART+COLOR1_CELL))
        assert value in ACTIVE_LEVELS
        color_refreshes.append(ACTIVE_LEVELS[value])
        m.events.append(dict(kind='color_refresh',level=ACTIVE_LEVELS[value]))
        BootState.return_from_model(m,0)
    m.boundaries[0x602b8916]=color_refresh
if args.gui_core:
    # Kernel lock/IRQ primitives and cross-core scheduling are boundaries.
    # The original typed producer and consumer both execute their real code.
    for address in (0x60038521,0x6006a922,0x6006a96b,0x60059fdd,0x6005a126):
        m.boundaries[address]=boundary
    def dispatch(m):
        assert m.regs['d0']==0 and m.regs['a0']==0x6005e676
        queued_callbacks.append(m.regs['a1'])
        BootState.return_from_model(m,0)
    m.boundaries[0x60056716]=dispatch

word(VIEWER,0x61189ba8)
word(CONTAINER+4,VIEWER);word(CONTAINER+8,0x34);word(CONTAINER+12,0x84)
word(0x61fc436c,CONTAINER)
m.write(MACHINE,bytes([4,29]))
word(MACHINE+4,0x611317c4)
word(0x61fb2564,MACHINE)
word(0x61fc1ba8,0);word(0x61fc1bac,0)
word(0x61fc28c8,278)
half(0x61fc26ae,3)
half(ARGS,193)
original_advance=m.advance
trace=[]
def advance(*a,**kw):
    try:
        r=original_advance(*a,**kw)
    except ValueError:
        print('fault regs', {k:hex(v) for k,v in m.regs.items()}, 'events',m.events[-10:],flush=True);raise
    trace.extend(r['trace']);return r
m.advance=advance
def call(a,**kw):
    r=m.call_native(a,**kw)
    print('call',hex(a),r['instructions'],r['d0'],r['a0'],[x['kind'] for x in r['events'][-3:]],flush=True)
    return r

session_evidence={}
if args.candidate:
    # Execute the actual native outer enter/re-enter/leave routines. Their
    # property notifications and inner mode body are explicit boundaries;
    # the native flag stores, branches and returns are not replaced.
    epoch=linked['_bank_epochs']+8*args.gui_core
    session_calls=[]
    inner_result=0
    inputs={'d0':3,'d1':7,'a0':0x5a,'a1':0x6b}

    def session_callback(m):
        assert m.word(epoch)==1, 'outer native callback escaped transaction'
        session_calls.append(m.regs['pc'])
        BootState.return_from_model(m,0)

    def session_inner(m):
        assert m.word(epoch)==2, 'inner bank operation lost nested epoch'
        assert {key:m.regs[key] for key in inputs}==inputs
        assert m.read(m.regs['sp']+5,1)==b'\x5a'
        assert m.word(m.regs['sp']+32)==0, 'native bank stack argument changed'
        session_calls.append(m.regs['pc'])
        # Tail resume after replayed native prologue, original CALL frame.
        m.write(HOOK_RETURN,bytes.fromhex('dff01c')+b'\xcb'*5)
        m.regs.update(pc=HOOK_RETURN,d0=inner_result)

    def session_reenter(m):
        assert {key:m.regs[key] for key in inputs}==inputs
        session_callback(m)

    callbacks=(0x602cbc0a,0x602b65fb,0x602b662c,0x602b4687,
        0x602b4273,0x602b45a8,0x602b4c6e,0x602b4cb6,0x602b0686,
        0x602b186c,0x602b536e,0x602b4f78,0x602b25a2,0x602b470f,
        0x602b467c,0x602b4658,0x602b464b,0x602b4700,0x602b25ab)
    handlers={address:session_callback for address in callbacks}
    handlers.update({0x602b3368:session_inner,0x602b36f1:session_reenter})
    previous={address:m.boundaries.get(address) for address in handlers}
    m.boundaries.update(handlers)
    for entry,mask,frame,latch,sequence in (
            (0x602b35a4,0xf0,32,1,2),  # first entry, inner result zero
            (0x602b35a4,0xf0,32,1,3),  # already entered, alternate branch
            (0x602b36d7,0,4,0,4),     # separate leave actually clears latch
            (0x602b35a4,0xf0,32,1,6)): # first entry, inner nonzero result
        inner_result=int(sequence==6)
        result=call(entry,mask=mask,frame=frame,values=inputs)
        assert result['d0']=='0x0'
        assert m.read(0x622484fa,1)==bytes([latch])
        assert m.word(epoch)==0 and m.word(epoch+4)==sequence
    assert set(handlers)<=set(session_calls), 'native session branch coverage missing'
    for address,handler in previous.items():
        if handler is None:
            del m.boundaries[address]
        else:
            m.boundaries[address]=handler
    # Leave the real native first-entry flag set throughout the entire UI flow.
    session_evidence=dict(native_outer_enter_reenter_leave_executed=True,
        native_first_entry_latch_retained=1,nested_epoch_depths=[1,2],
        both_inner_result_branches_executed=True,
        boundaries=['Native property notifications and inner mode body.'])

# Execute original factory/parent constructor and its selector + curve rebuild.
r=call(0x60e260c7,values={'a0':ARGS})
parent=int(r['a0'],16)
word(CONTAINER,parent)
word(VIEWER+384,parent)
selector=m.word(parent+76)
child=m.word(parent+80)
print('selector/child',hex(selector),u16(selector+86),hex(child),'vtable',hex(m.word(child)),'row',hex(m.word(child+216)),'page',u16(child+222),'updates',updates,flush=True)
assert (u16(selector+86), m.word(child), m.word(child+216), u16(child+222)) == (
    3, 0x61159ea8, 0x611595e0, 0)

def event(code, argument=0):
    trace.clear()
    updates.clear()
    refresh_before=len(color_refreshes)
    hdr_before=selected_level() if args.candidate else 0
    row=call(0x60d11448,values={'a0':MACHINE,'d0':code,'d1':0,'a1':argument})
    entries={point['pc'] for point in trace}
    assert 0x60e5da87 in entries and 0x60e4d032 in entries
    print(hex(code),'page',u16(child+222),'parent-held',m.word(parent+16),
          'pending',hex(m.word(parent+20)),'cursor',properties[1088],'updates',updates)
    if queued_callbacks:
        # Deliberately drain only after the GUI has rendered the queued value.
        # Capture must decline pending settings before this point.
        pending=m.call_native(linked['_ep7dr_selected_level'],values={'d0':54})
        assert pending['d0']=='0xffffffff'
        m.regions['cpu_id']=replace(m.regions['cpu_id'],data=bytes(4))
        for pointer in queued_callbacks:
            m.call_native(0x6005e676,values={'a0':pointer})
        queued_callbacks.clear()
        m.regions['cpu_id']=replace(m.regions['cpu_id'],data=struct.pack('<I',args.gui_core))
    if args.candidate and report.get('color_refresh_after_hdr_edit'):
        # Every accepted level change requests one native COLOR publication;
        # INFO, blocked edits and a dial at its endpoint do not request any.
        changed=selected_level()!=hdr_before
        assert len(color_refreshes)-refresh_before==int(changed)
    return entries, row['events']


def native_guide_from_published_record():
    render, style, widgets = 0x19408000,0x19409000,0x1940a000
    guarded(m,'guide_renderer',render,bytes(1024)+m.read(VIEWER+4,334))
    guarded(m,'guide_style',style,bytes(12))
    word(0x61fc4474,style)
    text,visibility=[],{}

    def resolve(m):
        assert m.regs['a0']==render
        m.regs['a0']=widgets+4*m.regs['d0']
        BootState.return_from_model(m,0)

    def set_text(m):
        data=m.read(m.regs['a1'],52).decode('utf-16le').split('\0',1)[0]
        text.append((m.regs['a0'],data))
        BootState.return_from_model(m,1)

    def visible(m):
        visibility[m.regs['a0']]=m.regs['d0']
        BootState.return_from_model(m,0)

    handlers={0x60d7abe1:resolve,0x60d4c9df:set_text,0x60e84549:visible}
    m.boundaries.update(handlers)
    trace.clear()
    call(0x60d7b6b3,mask=0xf0,frame=64,values={'a0':render})
    assert {0x60d7b7a8,0x60d7b7e4,0x60e85186} <= {point['pc'] for point in trace}
    assert text==[(widgets+4*53,'HDR [OFF] 200 400'+(' V00 P00' if mapping_only else ''))]
    assert visibility[widgets+4*52]==0 and visibility[widgets+4*53]==1
    for address in handlers:
        del m.boundaries[address]
    print('passed stock guide parser to native text setter and visibility boundary')

entries,_=event(0x9014)
assert {0x60dd55bb,0x60e26439,0x60defafe,0x60defcd8} <= entries
assert u16(child+222)==1 and updates==[(1088,694)]
entries,_=event(0x9015)
assert 0x60defcd8 not in entries and u16(child+222)==1 and not updates
if experiment:
    if args.candidate:
        m.write(0x62257b04,b'\1')
    entries,events=event(0x9014)
    assert syms['experiment_info']['address'] in entries and 0x60defcd8 not in entries
    assert m.word(HDR_OWNER)==child and selected_level()==0
    assert u16(child+222)==1 and properties[1088]==694 and not updates
    assert syms['experiment_draw']['address'] in entries and 0x60e27639 not in entries
    if args.candidate:
        assert any(e.get('labels')==['HDR unavailable: 0008'] for e in events)
        _,busy_events=event(0x9031,1)
        assert selected_level()==0 and not updates and not queued_callbacks
        m.write(0x62257b04,b'\0')
        # Genuine busy conditions still block. The persistent session latch
        # remains 1 from actual native entry, including while operating dials.
        epochs=linked['_bank_epochs']
        for address,fixture,code in (
                (0x61fa7538,struct.pack('<I',1),'0020'),
                (epochs,struct.pack('<I',1),'0040'),
                (epochs+8,struct.pack('<I',1),'0080'),
                (epochs+16,struct.pack('<I',1),'0100'),
                (0xa2715c8c,struct.pack('<2H',1,0),'0400')):
            previous=m.read(address,len(fixture))
            m.write(address,fixture)
            rendered=call(0x60e26ab0,values={'a0':VIEWER})['events']
            assert any(e.get('labels')==['HDR unavailable: '+code] for e in rendered)
            m.write(address,previous)
        events=call(0x60e26ab0,values={'a0':VIEWER})['events']
    assert any(e['kind']=='render_properties' and e['tone_flags']==bytes(8).hex()
               for e in events)
    if staged:
        assert any(e.get('labels')==['HDR [OFF] 200 400'+(' V00 P00' if mapping_only else '')] for e in events)
        native_guide_from_published_record()
        if mapping_only:
            # Both hexadecimal fields fit in the stock 26-code-unit guide,
            # including its terminating NUL; no extra widget or timer.
            word(linked['_observations']+8,0x42)
            word(linked['_observations']+20,0xa0)
            rendered=call(0x60e26ab0,values={'a0':VIEWER})['events']
            assert any(e.get('labels')==['HDR [OFF] 200 400 V42 PA0'] for e in rendered)
            call(linked['_ep7dr_highlight_clear_observations'])
    entries,_=event(0x9015)
    assert m.word(HDR_OWNER)==child and not updates

    touch_button=1
    entries,_=event(0xf855)
    assert syms['experiment_touch']['address'] in entries and 0x60df0222 not in entries
    assert m.word(HDR_OWNER)==child and u16(child+222)==1 and not updates

    for code,argument,level,iso,label in (
            (0x9031,1,1,1792,'HDR OFF [200] 400'),
            (0x9032,0xffffffff,2,1792,'HDR OFF 200 [400]' if mapping_only else 'HDR OFF 200 [400] ISO800+'),
            (0x9031,1,2,2048,None),
            (0x9031,0xffffffff,1,1877,'HDR OFF [200] 400'),
            (0x9031,1,2,0,'HDR OFF 200 [400]' if mapping_only else 'HDR OFF 200 [400] N/A'),
            (0x9032,1,1,2048,'HDR OFF [200] 400'),
            (0x9032,1,0,2048,'HDR [OFF] 200 400'),
            (0x9031,1,1,2048,'HDR OFF [200] 400')):
        raw_properties[0x810a]=iso
        entries,events=event(code,argument)
        assert {0x60def75a,0x60def91e}.isdisjoint(entries)
        assert selected_level()==level and not updates
        if staged:
            labels=[e['labels'] for e in events if e['kind']=='render_properties']
            if mapping_only and label:
                label += ' V00 P00'
            assert labels==([[label]] if label else [])

    entries,_=event(0x900c)
    assert m.word(parent+16)==3 and m.word(parent+20)==0x903e
    entries,_=event(0xf802)
    assert {0x60dd5623,syms['experiment_reset']['address']} <= entries
    assert 0x60defc4b not in entries and not updates
    assert m.word(HDR_OWNER)==child and selected_level()==0

entries,_=event(0x9014)
assert 0x60defcd8 in entries and u16(child+222)==0 and updates==[(1088,384)]
if experiment:
    assert m.word(HDR_OWNER)==0
    if staged:
        render=call(0x60e26ab0,values={'a0':VIEWER})
        assert any(e['kind']=='render_properties' and not e['labels'] and
                   e['tone_flags']!=bytes(8).hex() for e in render['events'])
    touch_button=2
    entries,_=event(0xf855)
    assert {0x60df0222,0x60df0332} <= entries
    assert u16(child+222)==1 and updates==[(1088,694)]
    event(0x9014)
    event(0x9014)
    assert m.word(HDR_OWNER)==0 and u16(child+222)==0

for code, handler, property_id in ((0x9031,0x60def91e,963),(0x9032,0x60def75a,965)):
    entries,events=event(code,1)
    assert {handler,0x60e26ab0,0x60e27639} <= entries
    assert [key for key,_ in updates]==[property_id]
    assert any(e['kind']=='descriptor' and e['type']==13 for e in events)

entries,_=event(0x900c)
assert 0x60defc4b not in entries and not updates
assert m.word(parent+16)==3 and m.word(parent+20)==0x903e
entries,_=event(0xf802)
assert {0x60dd5623,0x60defc4b,0x60e27639} <= entries
assert m.word(parent+16)==0 and updates==[(965,0),(963,0),(964,0)]
print('passed stock tone UI route')
if experiment:
    event(0x9014)
    event(0x9014)
    event(0x9031,1)
    assert m.word(HDR_OWNER)==child and properties[1088]==694 and selected_level()==1
    updates.clear()
    call(0x60e266a9,mask=0xf0,frame=28,values={'a0':parent})
    old_child,child=child,m.word(parent+80)
    assert not next(a for a in m.allocations if a['address']==old_child)['live']
    assert child!=old_child and m.word(HDR_OWNER)==0 and selected_level()==1
    assert u16(child+222)==0 and properties[1088]==384 and updates==[(1088,384)]
    event(0x9014)
    assert m.word(HDR_OWNER)==0 and u16(child+222)==1 and properties[1088]==694
    if staged:
        event(0x9014)
        assert m.word(HDR_OWNER)==child
        target=m.word(m.word(parent)+40)
        assert target==syms['experiment_destroy']['address']
        call(target,values={'a0':parent})
        assert m.word(HDR_OWNER)==0 and selected_level()==1
        assert m.word(parent+80)==0
        assert not next(a for a in m.allocations if a['address']==child)['live']
    print('passed staged HDR UI with native profile selection' if staged else
          'passed noninstallable HDR input experiment')
if args.out:
    if args.candidate:
        assert m.read(0x622484fa,1)==b'\1'
    args.out.write_text(json.dumps(dict(status='passed',gui_core=args.gui_core,
        native_info_cycle=True,native_typed_queue_executed=bool(args.gui_core),
        pending_capture_declined=bool(args.gui_core),native_render_text_boundary=True,
        busy_settings_do_not_hide_hdr_page=True,
        unavailable_reason_codes=True,
        color_refresh_levels=color_refreshes,
        color_refresh_after_committed_or_queued_edit=bool(color_refreshes),
        color_publication_service_boundary=True,
        native_session=session_evidence,
        hardware_executed=False,hash_checks_performed=False),indent=2)+'\n')
