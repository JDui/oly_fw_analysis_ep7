#!/usr/bin/env python3
"""Static E-P7 request-to-slot callback/event10 witnesses; no hardware safety claim."""
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from ep7_stock_audit import audit,BASE,require
from ep7_request_ownership import require_instruction
from oly_container import parse,sha256
WINDOWS={
 'request_type_zero':(0x60354ce4,0x60354d01),
 'request_dispatch':(0x60334ba8,0x60334bba),
 'driver_entry':(0x60334db4,0x60334e63),
 'driver_translate_and_id':(0x60344975,0x603449bd),
 'operation_id_allocator':(0x6034ed4c,0x6034ed9a),
 'slot_selector':(0x60345194,0x603451d3),
 'slot_callback_install':(0x60347378,0x60347397),
 'callback_router':(0x6034442b,0x60344442),
 'slot0_event_handler':(0x6034ee6d,0x6034ef7b),
 'handler_registration':(0x6034f429,0x6034f47f),
 'abort_status_writer':(0x60345a59,0x60345af8),
}
WITNESSES={
 0x60354cfd:('clr','d0'),
 0x60354cfe:('movbu','d0,(16,a2)'),
 0x60334ba8:('movbu','(16,a0),d0'),
 0x60334bab:('mov','1615744216,a1'),
 0x60334bb2:('mov','(d0,a1),a1'),
 0x60334bb4:('calls','(a1)'),
 0x60334dcb:('call','0x60344975,[d2,d3,a2,a3],40'),
 0x60334e1b:('call','0x603450dd,[d2,d3,a2,a3],28'),
 0x6034497b:('mov','a2,(a0)'),
 0x6034497d:('call','0x6034ed4c,[d2,d3,a2,a3],20'),
 0x6034499c:('cmp','11,d0'),
 0x6034499e:('bne','0x603449aa'),
 0x603449a3:('or','-2147483648,d0'),
 0x603449af:('mov','1,d0'),
 0x603449b1:('call','0x6034442b,[a2,a3],12'),
 0x6034ed6d:('cmp','32,d0'),
 0x6034ed78:('asl','8,d3'),
 0x6034ed7b:('or','d0,d3'),
 0x6034ed7d:('or','32768,d3'),
 0x6034ed88:('cmp','8,d3'),
 0x603451b5:('mov','2,d0'),
 0x603451bc:('clr','d0'),
 0x603451bf:('mov','1,d0'),
 0x603451c5:('mov','(4,a3),a1'),
 0x603451c8:('mov','(a3),d1'),
 0x603451cb:('call','0x60347378,[d2,d3,a2,a3],28'),
 0x6034737f:('call','0x603459a8,[],0'),
 0x60347385:('mov','d3,(a3)'),
 0x60347387:('inc4','a1'),
 0x60347388:('mov','(a2),d1'),
 0x60347389:('mov','(4,a2),d0'),
 0x6034738c:('mov','d1,(a1)'),
 0x6034738d:('mov','d0,(4,a1)'),
 0x60344435:('mov','(a0),a3'),
 0x60344437:('mov','(4,a0),a1'),
 0x6034443b:('mov','a2,a0'),
 0x6034443c:('calls','(a3)'),
 0x6034ee74:('clr','d0'),
 0x6034ee75:('call','0x603459a8,[],0'),
 0x6034eebd:('btst','2,d1'),
 0x6034eec2:('jmp','0x6034ef4b'),
 0x6034eec5:('btst','1,d1'),
 0x6034eedb:('bra','0x6034ef5a'),
 0x6034ef4b:('movhu','(44,a0),d0'),
 0x6034ef4e:('inc4','a0'),
 0x6034ef4f:('mov','d0,a1'),
 0x6034ef51:('mov','10,d0'),
 0x6034ef53:('bra','0x6034ef71'),
 0x6034ef5a:('inc4','a0'),
 0x6034ef5b:('mov','10,d0'),
 0x6034ef5d:('mov','0,a1'),
 0x6034ef71:('call','0x6034442b,[a2,a3],12'),
 0x6034f429:('mov','1614081645,a2'),
 0x6034f42f:('mov','148,d0'),
 0x6034f437:('call','0x6006aa25,[d2],16'),
 0x6034f451:('call','0x6006aa25,[d2],16'),
 0x6034f46c:('call','0x6006aa25,[d2],16'),
 0x60345a87:('movhu','d2,(44,a0)'),
 0x60345ab0:('movhu','d2,(44,a0)'),
 0x60345aba:('cmp','40449,d2'),
}
def inspect(raw,objdump):
 identity=audit(raw);main=parse(raw)[0].payload
 require(main[0x604e4cd8-BASE:0x604e4cdc-BASE]==(0x60334db4).to_bytes(4,'little'),'request type0 dispatcher mismatch')
 version=subprocess.check_output([str(objdump),'--version'],text=True).splitlines()[0];windows={}
 with tempfile.TemporaryDirectory(prefix='ep7-event10-') as temp:
  image=Path(temp)/'main.bin';image.write_bytes(main)
  for name,(start,stop) in WINDOWS.items():
   asm=subprocess.check_output([str(objdump),'-b','binary','-m','mn10300','-D','-z','--insn-width=16',f'--adjust-vma={BASE:#x}',f'--start-address={start:#x}',f'--stop-address={stop:#x}',str(image)],text=True)
   addresses=[a for a in WITNESSES if start<=a<stop]
   for a in addresses:require_instruction(asm,a,*WITNESSES[a])
   windows[name]=dict(start=hex(start),stop_exclusive=hex(stop),sha256=sha256(main[start-BASE:stop-BASE]),witness_count=len(addresses))
 return dict(source_sha256=identity['source_sha256'],objdump_version=version,objdump_sha256=sha256(objdump.read_bytes()),windows=windows,instruction_witness_count=len(WITNESSES),
  request_type_zero=dict(driver='0x60334db4',id_base=32768,id_bank_limit=8,id_index_limit=32,bit31_added_only_for_type11_in_reviewed_translator=True),
  callback_transport=dict(slot_callback_offset=4,slot_context_offset=8,slot_id_offset=0,router='0x6034442b'),
  event10=dict(handler='0x6034ee6d',slot_index=0,registration_selector=148,zero_status_path='0x6034ef5a',stored_status_path='0x6034ef4b',stored_status_halfword_offset=44,abort_writer='0x60345a59',cancel_status='0x9e01',event10_alone_is_not_success=True),
  limitations=['Slot0 is a statically connected conditional path, not a measured slot selection for every kind16/0x100d operation.','Hardware status bits and absence of outstanding DMA/readers remain unqualified.','Error/cancel status may use event10 too; receipt is not a proven universal quiescence fence.','No generation-safe extension ownership or flash-ready patch established.'],camera_accessed=False,firmware_executed=False,flash_ready=False)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock',required=True,type=Path);p.add_argument('--objdump',required=True,type=Path);a=p.parse_args();print(json.dumps(inspect(a.stock.read_bytes(),a.objdump.resolve()),indent=2))
