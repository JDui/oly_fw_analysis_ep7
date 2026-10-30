#!/usr/bin/env python3
"""Read-only exact-stock E-P7 GUI COLOR context. Not proof of all input routes."""
import argparse,json,re,struct,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from ep7_stock_audit import audit,BASE,require
from oly_container import parse,sha256
WINDOWS={
 'selector_mask_allocator':(0x60dde7b3,0x60dde7fd),
 'selector_mask_navigation':(0x60dde355,0x60dde40a),
 'selector_viewer_creator':(0x60e26a3d,0x60e26ab0),
 'selector_viewer_categories':(0x60e26b64,0x60e26bb8),
 'selector_list_handler_lookup':(0x60dde690,0x60dde710),
 'selector_list_loader':(0x60dde754,0x60dde7b3),
 'selector_remembered_index':(0x60de150c,0x60de157e),
 'selector_parent_init':(0x60e26188,0x60e261dc),
 'selector_parent_wrappers':(0x60e261dc,0x60e2622f),
 'GUI_041d_entry':(0x60e4b097,0x60e4b16a),
 'task_registration':(0x60cfd41c,0x60cfd438),
 'task_dequeue_and_engine':(0x60cfd4d9,0x60cfd55f),
 'preprocessor':(0x60e9fa88,0x60e9fdaa),
 'preprocessor_tracking':(0x60ea04fe,0x60ea0670),
 'preprocessor_tracking_guard':(0x60ea0ea2,0x60ea0eb8),
 'preprocessor_state_gates':(0x60ea0b15,0x60ea0d1b),
 'task_diagnostic':(0x60e9eb89,0x60e9ebbd),
 'controller_init':(0x60e5dae9,0x60e5db01),
 'controller_exit':(0x60e5db01,0x60e5db2e),
 'controller_handler':(0x60e5da87,0x60e5dae9),
 'whole_actuator_factory':(0x60dd5146,0x60dd518e),
 'selector_creator':(0x60e260c7,0x60e26130),
 'machine_registration':(0x60dd4b19,0x60dd4b31),
 'machine_dispatch':(0x60d11448,0x60d11566),
 'event_lookup':(0x60d1158b,0x60d115d4),
 'app_callback':(0x60ceac44,0x60ceac59),
 'app_callback_guard':(0x60cd0090,0x60cd00ce),
 'app_callback_global_clear':(0x60cd2330,0x60cd234d),
}
WITNESSES={
 0x60dde7d4:('movhu','(a0),d0'),
 0x60dde7d7:('add','d0,d0'),
 0x60dde7d8:('call','0x60a4ec0d,[],4'),
 0x60dde7f1:('clr','d0'),
 0x60dde7f2:('movhu','d0,(d2,a0)'),
 0x60dde38c:('mov','(88,a0),a1'),
 0x60dde394:('cmp','0,d1'),
 0x60dde396:('beq','0x60dde39e'),
 0x60dde3ec:('mov','(88,a0),a1'),
 0x60dde3f5:('cmp','0,d1'),
 0x60dde3f7:('beq','0x60dde3ff'),
 0x60e26a43:('mov','408,d0'),
 0x60e26a66:('mov','1629002664,d0'),
 0x60e26b68:('cmp','0,d0'),
 0x60e26b6c:('cmp','1,d0'),
 0x60e26b70:('cmp','2,d0'),
 0x60e26b74:('cmp','3,d0'),
 0x60e26b98:('call','0x60e27162,[d2,d3,a2,a3],36'),
 0x60e26ba1:('call','0x60e27289,[d2,d3,a2,a3],44'),
 0x60dde6dc:('add','1628762064,a0'),
 0x60dde6f3:('calls','(a1)'),
 0x60dde786:('add','1628759232,a0'),
 0x60dde794:('movhu','(4,a0),d0'),
 0x60dde79e:('mov','d0,(92,a1)'),
 0x60de1518:('call','0x60dde754,[d2,d3,a2,a3],52'),
 0x60de1520:('movhu','(0x61fc26ae),d1'),
 0x60de1526:('add','-1,d0'),
 0x60de152c:('movhu','d0,(0x61fc26ae)'),
 0x60de1538:('movhu','d0,(86,a2)'),
 0x60de153d:('mov','1625167184,d0'),
 0x60de1544:('mov','1625167207,d0'),
 0x60de1556:('call','0x60dde357,[d2,d3,a2,a3],16'),
 0x60de155e:('movhu','d1,(0x61fc26ae)'),
 0x60de156d:('call','0x60dde3aa,[d2,d3,a2,a3],20'),
 0x60de1575:('movhu','d1,(0x61fc26ae)'),
 0x60e26189:('mov','193,d0'),
 0x60e261c5:('mov','1,d0'),
 0x60e261c9:('call','0x60dd518e,[d2,d3,a2],16'),
 0x60e261d0:('mov','a0,(76,a2)'),
 0x60e261e8:('mov','(48,a0),a1'),
 0x60e2620d:('mov','(52,a0),a1'),
 0x60e4b09d:('cmp','4,a1'),
 0x60e4b0a1:('cmp','5,a1'),
 0x60e4b0a5:('mov','29,d2'),
 0x60e4b0af:('movhu','d0,(0x61fc26ae)'),
 0x60e4b161:('or','1024,d2'),
 0x60cfd41c:('mov','1648781388,a2'),
 0x60cfd423:('call','0x60dd4b19,[],8'),
 0x60cfd42a:('mov','a2,(0x61fb2564)'),
 0x60cfd4e7:('call','0x60d10133,[d2,d3,a2,a3],20'),
 0x60cfd53a:('call','0x60e9fa88,[d2,a2,a3],224'),
 0x60cfd544:('beq','0x60cfd4e4'),
 0x60cfd546:('mov','(396,sp),d0'),
 0x60cfd552:('mov','(0x61fb2564),a0'),
 0x60cfd558:('call','0x60d1144d,[d2,d3,a2,a3],48'),
 0x60e9fb40:('add','-36868,d1'),
 0x60e9fb47:('and','127,d0'),
 0x60e9fb4d:('mov','1629407584,a1'),
 0x60e9fb5e:('jmp','0x60e9fd41'),
 0x60e9fb61:('add','8,a0'),
 0x60e9fd48:('call','0x60ea04fe,[d2,d3,a2,a3],28'),
 0x60e9fd6e:('call','0x60ea0b15,[d2,a2,a3],20'),
 0x60e9fd76:('call','0x60ea0bdd,[a2],8'),
 0x60e9fd7e:('call','0x60ea0c15,[d2,a2],12'),
 0x60e9fd8e:('call','0x60ea0ced,[],4'),
 0x60e9fda5:('mov','d2,d0'),
 0x60ea051a:('mov','1629406092,d0'),
 0x60ea0526:('call','0x60ea0ea2,[d2,d3],12'),
 0x60ea0665:('cmp','41,d3'),
 0x60ea0eb3:('beq','0x60ea0eb8'),
 0x60ea0eb5:('retf','[d2,d3],12'),
 0x60ea0b28:('cmp','3,d0'),
 0x60ea0b2c:('clr','d0'),
 0x60ea0c08:('cmp','41738,d1'),
 0x60ea0c10:('mov','1,d0'),
 0x60ea0c23:('cmp','38401,d1'),
 0x60ea0caa:('mov','1,d2'),
 0x60ea0d11:('call','0x60ea04fe,[d2,d3,a2,a3],28'),
 0x60ea0d16:('mov','1,d0'),
 0x60e9ebad:('cmp','36884,d3'),
 0x60e5daec:('mov','8,d0'),0x60e5daee:('mov','463,d1'),
 0x60e5daf1:('call','0x60e4cea8,[d2,d3,a2,a3],52'),
 0x60e5daf8:('mov','a0,(0x61fc436c)'),
 0x60e5db06:('mov','(0x61fc436c),a2'),
 0x60e5db15:('call','0x60e4ce26,[a2,a3],12'),
 0x60e5db25:('mov','d0,(0x61fc436c)'),
 0x60e5da90:('mov','(0x61fc436c),a0'),
 0x60e5da98:('call','0x60e4d032,[d2,d3,a2,a3],60'),
 0x60dd5162:('mov','1628701172,a0'),
 0x60dd516d:('mov','(4,a0),a1'),0x60dd5171:('calls','(a1)'),
 0x60e26100:('call','0x60e26108,[d2,a2],16'),
 0x60e2611f:('mov','1629001084,d0'),
 0x60dd4b1f:('mov','1628641220,a1'),
 0x60dd4b27:('call','0x60d113d1,[d2,d3,a2,a3],20'),
 0x60d1147e:('call','0x60d1158b,[d2,d3,a2,a3],20'),
 0x60d11486:('movhu','(2,a0),d1'),
 0x60d1148c:('mov','3,d0'),
 0x60d11495:('udf01','d2,d0'),
 0x60d1149b:('add','-1,d1'),
 0x60d114a5:('mov','(8,a0),a0'),
 0x60d114a8:('movbu','(d0,a0),d0'),
 0x60d114bc:('mov','(12,a0),a0'),
 0x60d114c1:('mov','(d0,a0),a2'),
 0x60d114d4:('calls','(a2)'),
 0x60d11510:('mov','(-4,a0),a2'),
 0x60d11551:('mov','(-4,a1),a2'),
 0x60d1158d:('mov','65535,a2'),
 0x60d11599:('movhu','(6,a0),d3'),
 0x60d115ae:('bne','0x60d115b9'),
 0x60d115ce:('mov','(-4,a1),a0'),
 0x60ceac47:('call','0x60cd0090,[],8'),
 0x60ceac4e:('clr','d0'),
 0x60ceac4f:('call','0x60cd2330,[d2],12'),
 0x60cd0091:('cmp','17235970,d0'),
 0x60cd0097:('bne','0x60cd00cb'),
 0x60cd2344:('mov','d2,(0x6233b84c)'),
}
ROWS=(
 ('controller_COLOR_selector',0x6119cb3c,(0x1cf,0x34,0,0x84,0,0)),
 ('whole_actuator_0x34',0x61140354,(0x34,0x60e260c7)),
 ('controller_group8',0x6119fadc,(8,0x6119a31c,429)),
 ('GUI_state29_init',0x611a3b50,(0x60e5dae9,)),
 ('GUI_state29_exit',0x611a3bc4,(0x60e5db01,)),
 ('GUI_machine4',0x611317d0,(0x611a3bc8,)),
 ('machine_descriptor',0x611a3bc8,(0x70001d,0x70008a,0x611a2e30,0x611a2c08,0x611a2888,0x611a3ae0,0x611a3b54,0)),
)
def require_instruction(assembly,address,mnemonic,operands):
 lines=[line for line in assembly.splitlines() if line.startswith(f'{address:x}:')]
 require(len(lines)==1 and re.search(r'\b'+re.escape(mnemonic)+r'\s+'+re.escape(operands)+r'\s*$',lines[0]),f'instruction mismatch at {address:#x}')
def inspect_tables(main):
 def words(a,n):return struct.unpack_from('<'+'I'*n,main,a-BASE)
 facts=[]
 for name,address,expected in ROWS:
  require(words(address,len(expected))==expected,'table mismatch: '+name)
  facts.append(dict(label=name,address=hex(address),words=[hex(x) for x in expected]))
 events=dict(words(0x611a2888+i*8,2) for i in range(112))
 require(len(events)==112,'event keys not unique')
 require(0x9016 not in events and 0x903e not in events,'unexpected direct Delete/reset event row')
 paths=[]
 for event in (0x900c,0x9014,0x9015):
  require(event in events,'missing expected event')
  idx=events[event];require(idx<112,'event index out of bounds')
  cell=0x611a2e30+idx*29+28;handler=main[cell-BASE]
  require(handler==137 and words(0x611a2c08+4*handler,1)==(0x60e5da87,),'state29 handler mismatch')
  paths.append(dict(event=hex(event),event_index=idx,matrix_cell=hex(cell),handler_index=handler,handler='0x60e5da87'))
 return facts,paths

def inspect_preprocessor(main):
 slots=[struct.unpack_from('<II',main,0x611ec960+i*8-BASE) for i in range(128)]
 require(all(key != 0x12 for key,_ in slots),'unexpected Delete-specific preprocessing row')
 path=[]
 for n in range(128):
  index=(0x12+n)%128;key,target=slots[index]
  require(0x60e9fb74 <= target <= 0x60e9fd41,'preprocessor target outside reviewed dispatcher')
  path.append(dict(slot=index,address=hex(0x611ec960+index*8),key=hex(key),target=hex(target)))
  if key==0:break
 else:raise ValueError('unterminated preprocessing probe')
 require(len(path)==21 and path[-1]['slot']==38 and slots[38]==(0,0x60e9fd41),'Delete probe termination mismatch')
 tracked=struct.unpack_from('<41H',main,0x611ec38c-BASE)
 require(0x9016 not in tracked,'unexpected Delete tracking row')
 return dict(event='0x9016',key='0x12',slot_count=128,probe_path=path,tracking_event_count=41,
  task_engine_call='0x60cfd558',engine_entry='0x60d1144d',
  normal_route_result='Reviewed task preprocessing has no Delete rewrite/direct-actuator branch; it may consume the event or pass unchanged to the GUI machine.',
  limitation='Not a whole-program exclusion of other producers/alias paths; local timer reset is unaffected.')

def inspect_selector(main):
 def w(address,n):return struct.unpack_from('<'+'I'*n,main,address-BASE)
 require(w(0x6115cafc,2)==(0x84,0x60e26a3d),'selector viewer factory mismatch')
 require(w(0x61189ba8,3)==(0x60e26ab0,0x60e26a7c,0x60df2641),'selector viewer vtable mismatch')
 require(w(0x6114f330,2)==(193,0x60de150c),'selector special initializer mismatch')
 require(w(0x6114efa0,4)==(193,4,0x6114e050,0),'selector list descriptor mismatch')
 require(struct.unpack_from('<4H',main,0x6114e050-BASE)==(0,1,2,3),'selector values mismatch')
 require(w(0x611895a8,2)==(0x60e261e5,0x60e2620a),'parent navigation vtable mismatch')
 require(w(0x611992c4,8)==(0x59000e,0x590053,0x61198d74,0x61198c28,0x61198960,0x61199254,0x6119928c,0),'machine1 descriptor mismatch')
 require(w(0x61198cb0,1)==(0x60e4b097,),'GUI entry handler mismatch')
 events=[w(0x61198960+i*8,2) for i in range(89)]
 require([index for event,index in events if event==0x9715]==[27],'entry event mapping mismatch')
 states=[state+1 for state in range(14) if main[0x61198d74+27*14+state-BASE]==34]
 require(states==[2,3,4,5,8,9,11],'GUI9715 entry states mismatch')
 require(w(0x6113ee40,2)==(0xa1,0x9715) and w(0x6113eef0,2)==(0xb7,0x9715),'GuiCaller entry enums mismatch')
 return dict(list_id=193,count=4,values=[0,1,2,3],list_descriptor='0x6114efa0',
  viewer=dict(factory_id=132,creator='0x60e26a3d',draw='0x60e26ab0',COLOR_category1_draw='0x60e27289',hardcoded_categories=[0,1,2,3]),
  mask=dict(pointer_offset=88,element_bytes=2,initial_value=0,nonzero_skipped_by_navigation=True),
  remembered_index=dict(address='0x61fc26ae',storage='RAM halfword, not established persistent property',object_index_offset=86),
  GUI_entry=dict(event='0x9715',source_machine=1,source_states=states,handler='0x60e4b097',arguments=[4,5],target_machine=4,target_state=29,argument4_clears_category=True,argument5_retains_category=True),
  limits=['App FSM/physical origin of A1/B7 plus argument4/5 remains unproven.',
   'ROM callback table6025bb34 to RAM61fc3874 initialization relationship not yet verified.',
   'Four list categories are occupied; adding H/L requires parent switch/viewer support and separate state design.'])

def inspect(raw,objdump):
 identity=audit(raw);main=parse(raw)[0].payload
 facts,paths=inspect_tables(main)
 selector=inspect_selector(main)
 preprocessor=inspect_preprocessor(main)
 version=subprocess.check_output([str(objdump),'--version'],text=True).splitlines()[0]
 reports={}
 with tempfile.TemporaryDirectory(prefix='ep7-gui-machine-') as tmp:
  image=Path(tmp)/'main.bin';image.write_bytes(main)
  for name,(start,stop) in WINDOWS.items():
   asm=subprocess.check_output([str(objdump),'-b','binary','-m','mn10300','-D','-z','--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={start:#x}',f'--stop-address={stop:#x}',str(image)],text=True)
   witnesses=[a for a in WITNESSES if start<=a<stop]
   for address in witnesses:require_instruction(asm,address,*WITNESSES[address])
   reports[name]=dict(start=hex(start),stop_exclusive=hex(stop),sha256=sha256(main[start-BASE:stop-BASE]),witness_count=len(witnesses))
 return dict(scope='COLOR selector GUI machine4/state29 static table route only',source_sha256=identity['source_sha256'],objdump_version=version,objdump_sha256=sha256(objdump.read_bytes()),tables=facts,paths=paths,selector=selector,preprocessor=preprocessor,windows=reports,instruction_witness_count=len(WITNESSES),direct_Delete_event_present=False,event_count=112,limitations=['Reviewed normal task preprocessing only; alternate producers or alias/direct paths are not globally excluded.','No app FSM 0x5701/0x2006 association proven.','Matrix stride opcode disassembles udf01; arithmetic interpretation still needs independent MN103 opcode confirmation.','No physical Delete behavior or live routing qualification.'],camera_accessed=False,firmware_executed=False,flash_ready=False)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock',required=True,type=Path);p.add_argument('--objdump',required=True,type=Path);a=p.parse_args()
 print(json.dumps(inspect(a.stock.read_bytes(),a.objdump.resolve()),indent=2))
