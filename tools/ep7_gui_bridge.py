#!/usr/bin/env python3
"""Exact E-P7 1100 stock application/GUI bridge witnesses; no firmware execution.

Supply a trusted MN10300 objdump. Emits metadata only; not a patch builder.
"""
import argparse,json,re,struct,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from ep7_stock_audit import audit,BASE,require
from oly_container import parse,sha256
WINDOWS={
 'color_info_all_toggle':(0x60e22579,0x60e228e9),
 'app_to_oly':(0x60cf91d8,0x60cf920f),
 'state_table_consumer':(0x60cf304c,0x60cf30cd),
 'context_to_packet':(0x60cf31d4,0x60cf31fe),
 'packet_getters':(0x60cf2f20,0x60cf2f2f),
 'main_packet_send':(0x60cc82b2,0x60cc82f5),
 'interface_binding':(0x60cc7348,0x60cc7359),
 'interface_setter':(0x60cfccc8,0x60cfccce),
 'packet_adapter':(0x60cfcb2a,0x60cfcb89),
 'gui_enum_lookup':(0x60dd4ba9,0x60dd4bf2),
 'gui_event_send':(0x60dd500c,0x60dd505c),
}
WITNESSES={
 0x60cf91f7:('mov','1626791080,a0'),
 0x60cf9202:('mov','(4,a0),d2'),
 0x60cf3056:('mov','(a1),d2'),
 0x60cf305c:('mov','(12,a1),a2'),
 0x60cf3077:('mov','(4,a1),d1'),
 0x60cf307c:('mov','d1,(32,a0)'),
 0x60cf30b5:('calls','(a2)'),
 0x60cf31d4:('mov','32,a1'),
 0x60cf31d9:('mov','12,a0'),
 0x60cf31dd:('mov','d0,(a0)'),
 0x60cf2f20:('add','12,a0'),
 0x60cf2f25:('add','36,a0'),
 0x60cc82ba:('call','0x60cf310b,[d2,d3,a2,a3],44'),
 0x60cc82ce:('call','0x60cf2f20,[],0'),
 0x60cc82d8:('call','0x60cfcb2a,[d2,d3,a2,a3],52'),
 0x60cc7348:('call','0x60dd4b59,[],4'),
 0x60cc7352:('call','0x60cfccc8,[],0'),
 0x60cfccc8:('mov','a1,(32,a0)'),
 0x60cfcb73:('calls','(a2)'),
 0x60dd4bd7:('asl','3,d0'),
 0x60dd4bdc:('mov','1628694840,d3'),
 0x60dd4be4:('movhu','(4,a0),d0'),
 0x60dd5032:('movhu','(4,a2),d0'),
 0x60dd503d:('call','0x60d0ffb4,[d2,d3,a2,a3],44'),
 0x60dd5052:('call','0x60d0ffe0,[d2,d3,a2,a3],24'),
}
ROWS=(
 ('OK app to OLY',0x60f6dd78,(0x43,0x0100001a)),
 ('Delete app to OLY',0x60f6ddd8,(0x53,0x01000026)),
 ('INFO app to OLY',0x60f6ddf8,(0x57,0x0100002a)),
 ('state0x2006 OK',0x60f50edc,(0x0100001a,0x14,1,0)),
 ('state0x2006 Delete',0x60f50f5c,(0x01000026,0x27,1,0)),
 ('state0x2006 INFO',0x60f50f8c,(0x0100002a,0x25,1,0)),
 ('state0x2006 descriptor',0x60f522f4,(0x2006,0x60f50dcc,70)),
 ('state0x5701 descriptor',0x60f5e648,(0x5701,0x60f5c95c,106)),
 ('GUI OK enum',0x6113e9d8,(0x14,0x900c)),
 ('GUI INFO enum',0x6113ea60,(0x25,0x9014)),
 ('GUI Delete enum',0x6113ea70,(0x27,0x9016)),
 ('GuiCaller vtable sendEvent',0x611401c4,(0x60dd4ba9,)),
)
def require_instruction(assembly,address,mnemonic,operands):
 lines=[line for line in assembly.splitlines() if line.startswith(f'{address:x}:')]
 require(len(lines)==1 and re.search(r'\b'+re.escape(mnemonic)+r'\s+'+re.escape(operands)+r'\s*$',lines[0]),f'instruction mismatch at {address:#x}')
def inspect(raw,objdump):
 identity=audit(raw) # reject unknown images before launching a tool
 main=parse(raw)[0].payload
 facts=[]
 for label,address,values in ROWS:
  require(struct.unpack_from('<'+'I'*len(values),main,address-BASE)==values,'table mismatch: '+label)
  facts.append(dict(label=label,address=hex(address),words=[hex(v) for v in values]))
 version=subprocess.check_output([str(objdump),'--version'],text=True).splitlines()[0]
 reports={}
 with tempfile.TemporaryDirectory(prefix='ep7-gui-') as tmp:
  image=Path(tmp)/'main.bin';image.write_bytes(main)
  for name,(start,stop) in WINDOWS.items():
   asm=subprocess.check_output([str(objdump),'-b','binary','-m','mn10300','-D','-z','--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={start:#x}',f'--stop-address={stop:#x}',str(image)],text=True)
   witnesses=[a for a in WITNESSES if start<=a<stop]
   for address in witnesses:require_instruction(asm,address,*WITNESSES[address])
   reports[name]=dict(start=hex(start),stop_exclusive=hex(stop),sha256=sha256(main[start-BASE:stop-BASE]),witness_count=len(witnesses))
 return dict(scope='Exact stock static bridge, conditional on selected app FSM state; not live routing qualification',source_sha256=identity['source_sha256'],objdump_version=version,objdump_sha256=sha256(objdump.read_bytes()),tables=facts,windows=reports,instruction_witness_count=len(WITNESSES),limitations=['States 0x2006/0x5701 not proven active while COLOR editor is selected.','Non-null state callbacks may override packet enum.','GUI INFO maps to9014 under demonstrated forwarding table, not9012.','Event posting does not establish eventual delivery to selected GUI object.'],camera_accessed=False,firmware_executed=False,flash_ready=False)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock',required=True,type=Path);p.add_argument('--objdump',required=True,type=Path);a=p.parse_args()
 print(json.dumps(inspect(a.stock.read_bytes(),a.objdump.resolve()),indent=2))
