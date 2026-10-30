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

# Additional bounded profile entry evidence.
WINDOWS.update({
 'profile_entry_reset_producer': (0x60cd49b6, 0x60cd4a71),
 'profile_entry_remember_producer': (0x60cf0896, 0x60cf0907),
 'profile_entry_switch': (0x60cf0796, 0x60cf07c6),
 'app_state_commit': (0x60cf318c, 0x60cf31d4),
 'app_state_family_lookup': (0x60cf6824, 0x60cf6877),
 'app_profile_table_lookup': (0x60cf695e, 0x60cf6980),
 'app_state_event_dispatch': (0x60cf5c4e, 0x60cf5c7f),
 'normalizer_enum_guard': (0x60cd52e1, 0x60cd5313),
 'packet_normalizer': (0x60cf665d, 0x60cf6690),
 'profile_info_override': (0x60ceb328, 0x60ceb37e),
})
WITNESSES.update({
 0x60cd5305: ('mov', '(32,a2),d1'),
 0x60cd5308: ('cmp', '174,d1'),
 0x60cd530c: ('bne', '0x60cd530f'),
 0x60cf6661: ('call', '0x60cd52e1,[d2,a2],12'),
 0x60cf666a: ('bne', '0x60cf667e'),
 0x60cf6685: ('cmp', '1,d0'),
 0x60cf6687: ('bne', '0x60cf668d'),
 0x60cd4a1d: ('mov', '22276,d0'),
 0x60cd4a20: ('mov', 'd0,(192,a2)'),
 0x60cd4a24: ('add', '32,a2'),
 0x60cd4a26: ('mov', '183,d0'),
 0x60cd4a29: ('mov', 'd0,(a2)'),
 0x60cd4a2a: ('mov', '4,d0'),
 0x60cd4a2c: ('mov', 'd0,(4,a2)'),
 0x60cf08e6: ('mov', '22276,d0'),
 0x60cf08e9: ('mov', 'd0,(192,a2)'),
 0x60cf08ed: ('mov', '32,a0'),
 0x60cf08ef: ('add', 'a2,a0'),
 0x60cf08f1: ('mov', '183,d0'),
 0x60cf08f4: ('mov', 'd0,(a0)'),
 0x60cf08f5: ('mov', '5,d0'),
 0x60cf08f7: ('mov', 'd0,(4,a0)'),
 0x60cf08fa: ('cmp', '1,d2'),
 0x60cf08fe: ('mov', '238,d0'),
 0x60cf0901: ('mov', 'd0,(32,a2)'),
 0x60cf07a5: ('clr', 'd2'),
 0x60cf07a6: ('mov', '(76,a1),a1'),
 0x60cf07a9: ('calls', '(a1)'),
 0x60cf07b9: ('add', '-3,d0'),
 0x60cf07bc: ('mov', '1626668500,a0'),
 0x60cf318c: ('mov', '192,a0'),
 0x60cf3190: ('mov', '(a0),d0'),
 0x60cf3197: ('mov', '172,a3'),
 0x60cf319b: ('mov', 'd0,(a3)'),
 0x60cf31d4: ('mov', '32,a1'),
 0x60cf31de: ('mov', '(4,a1),d0'),
 0x60cf31e3: ('mov', 'd0,(4,a0)'),
 0x60cf682a: ('mov', '65280,d2'),
 0x60cf6830: ('and', 'd3,d2'),
 0x60cf6844: ('add', '-20479,d2'),
 0x60cf684f: ('mov', '1626782204,a1'),
 0x60cf6975: ('mov', '1626727996,a1'),
 0x60cf697b: ('mov', '11,d1'),
 0x60cf5c75: ('mov', '(24,sp),a1'),
 0x60cf5c77: ('mov', '(32,sp),d1'),
 0x60cf5c79: ('call', '0x60cf304c,[d2,d3,a2,a3],36'),
 0x60ceb344: ('mov', '280,d0'),
 0x60ceb350: ('bne', '0x60ceb37b'),
 0x60ceb363: ('cmp', '1,d0'),
 0x60ceb365: ('bne', '0x60ceb37b'),
 0x60ceb36b: ('mov', '157,d0'),
 0x60ceb36e: ('mov', 'd0,(a0)'),
 0x60ceb36f: ('mov', '17,d0'),
 0x60ceb371: ('mov', 'd0,(4,a0)'),
 0x60ceb374: ('mov', '22537,d0'),
 0x60ceb377: ('mov', 'd0,(192,a3)'),
})
ROWS += (
 ('profile state descriptor', 0x60f5e66c, (0x5704, 0x60f5d06c, 90,)),
 ('profile state hash', 0x60f6ba3c, (1793, 0x60cf695e,)),
 ('profile UP', 0x60f5d0ac, (0x100000a, 8, 1, 0,)),
 ('profile DOWN', 0x60f5d0dc, (0x100000e, 11, 1, 0,)),
 ('profile OK', 0x60f5d16c, (0x100001a, 20, 1, 0x60cd4238,)),
 ('profile Delete', 0x60f5d1dc, (0x1000026, 39, 1, 0,)),
 ('profile INFO', 0x60f5d1fc, (0x100002a, 37, 1, 0x60ceb328,)),
 ('profile touch entry callback', 0x60f578c8, (0x2000023, 1, 1, 0x60cf0713,)),
 ('GUI profile enum', 0x6113eef0, (183, 0x9715,)),
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
 return dict(scope='Exact stock static bridge, conditional on selected app FSM state; not live routing qualification',source_sha256=identity['source_sha256'],objdump_version=version,objdump_sha256=sha256(objdump.read_bytes()),tables=facts,windows=reports,instruction_witness_count=len(WITNESSES),limitations=['B7 producers request APP state 0x5704 and GUI 0x9715 argument 4/5; eventual simultaneous runtime state is not device-qualified. APP higher-priority table and normalization remain conditional.','Non-null state callbacks may override packet enum.','GUI INFO maps to9014 under demonstrated forwarding table, not9012.','Event posting does not establish eventual delivery to selected GUI object.'],camera_accessed=False,firmware_executed=False,flash_ready=False)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock',required=True,type=Path);p.add_argument('--objdump',required=True,type=Path);a=p.parse_args()
 print(json.dumps(inspect(a.stock.read_bytes(),a.objdump.resolve()),indent=2))
