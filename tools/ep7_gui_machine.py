#!/usr/bin/env python3
"""Read-only exact-stock E-P7 GUI COLOR context. Not proof of all input routes."""
import argparse,json,re,struct,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from ep7_stock_audit import audit,BASE,require
from oly_container import parse,sha256
WINDOWS={
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

def inspect(raw,objdump):
 identity=audit(raw);main=parse(raw)[0].payload
 facts,paths=inspect_tables(main)
 version=subprocess.check_output([str(objdump),'--version'],text=True).splitlines()[0]
 reports={}
 with tempfile.TemporaryDirectory(prefix='ep7-gui-machine-') as tmp:
  image=Path(tmp)/'main.bin';image.write_bytes(main)
  for name,(start,stop) in WINDOWS.items():
   asm=subprocess.check_output([str(objdump),'-b','binary','-m','mn10300','-D','-z','--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={start:#x}',f'--stop-address={stop:#x}',str(image)],text=True)
   witnesses=[a for a in WITNESSES if start<=a<stop]
   for address in witnesses:require_instruction(asm,address,*WITNESSES[address])
   reports[name]=dict(start=hex(start),stop_exclusive=hex(stop),sha256=sha256(main[start-BASE:stop-BASE]),witness_count=len(witnesses))
 return dict(scope='COLOR selector GUI machine4/state29 static table route only',source_sha256=identity['source_sha256'],objdump_version=version,objdump_sha256=sha256(objdump.read_bytes()),tables=facts,paths=paths,windows=reports,instruction_witness_count=len(WITNESSES),direct_Delete_event_present=False,event_count=112,limitations=['No claim alternate/pre-dispatch or alias routes are excluded.','No app FSM 0x5701/0x2006 association proven.','Matrix stride opcode disassembles udf01; arithmetic interpretation still needs independent MN103 opcode confirmation.','No physical Delete behavior or live routing qualification.'],camera_accessed=False,firmware_executed=False,flash_ready=False)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock',required=True,type=Path);p.add_argument('--objdump',required=True,type=Path);a=p.parse_args()
 print(json.dumps(inspect(a.stock.read_bytes(),a.objdump.resolve()),indent=2))
