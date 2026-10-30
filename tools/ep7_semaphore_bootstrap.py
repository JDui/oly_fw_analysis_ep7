#!/usr/bin/env python3
"""Pinned raw creation and never-published deletion evidence, read-only."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ep7_private_semaphore as base
WINDOWS=[(0x6003057f,0x60030619),(0x60030b78,0x60030b9c),(0x60031107,0x60031229),(0x60034f31,0x60035023)]
W={0x6003057f:('mov','a0,a2'),0x6003058a:('mov','-11,d2'),0x600305bb:('mov','-25,d2'),0x600305df:('mov','-17,d2'),0x600305ec:('call','0x60034f31,[d2,d3,a2,a3],24'),0x600305f1:('mov','d0,d2'),0x600305f4:('ble','0x60030610'),0x60030603:('mov','(a2),d0'),0x60030605:('mov','d0,(a0)'),0x60030608:('lne',''),0x6003060b:('call','0x60030b78,[],0'),0x60030615:('mov','d2,d0'),0x60030616:('ret','[d2,a2],16'),0x60030b7c:('mov','(8,a1),d0'),0x60030b81:('bne','0x60030b87'),0x60030b83:('mov','-17,d0'),0x60030b8c:('mov','(4,a1),d0'),0x60030b8f:('mov','d0,(24,a0)'),0x60030b92:('inc4','a0'),0x60030b93:('mov','a0,(a0)'),0x60030b95:('mov','a0,(4,a0)'),0x60030b98:('clr','d0'),0x60030b99:('retf','[],0'),0x60034fba:('mov','-34,d0'),0x60034fd6:('mov','(0x8050),d3'),0x60034fdb:('asl','12,d3'),0x60034fde:('or','d3,d1'),0x6003501a:('movhu','d1,(a1)'),0x60035020:('retf','[d2,d3,a2,a3],24'),
0x60031175:('mov','-18,d2'),0x60031177:('jmp','0x60031225'),0x60031188:('mov','-25,d2'),0x6003118a:('jmp','0x60031225'),0x600311b5:('mov','-42,d2'),0x600311b9:('beq','0x60031220'),0x600311be:('mov','(a2),d0'),0x600311bf:('cmp','a2,d0'),0x600311c1:('beq','0x600311d1'),0x600311c5:('mov','-51,d0'),0x600311c7:('call','0x600344b2,[a2,a3],12'),0x600311cf:('bne','0x600311c3'),0x600311fe:('movhu','d0,(a0)'),0x60031217:('clr','d0'),0x60031218:('movhu','d0,(a0)'),0x6003121a:('call','0x6003593f,[d2,a2,a3],16'),0x6003121f:('clr','d2'),0x60031225:('mov','d2,d0'),0x60031226:('ret','[d2,d3,a2,a3],20')}
def inspect(raw,od):
 oldw,oldwindows=base.W,base.WINDOWS
 try:
  base.W,base.WINDOWS=W,WINDOWS;r=base.inspect(raw,od)
 finally:base.W,base.WINDOWS=oldw,oldwindows
 return dict(source_sha256=r['source_sha256'],windows=r['windows'],witness_count=len(W),create_returns_allocated_id_after_initializer=True,initializer_valid_maximum_sets_count_and_empty_queue=True,delete_negative_status_before_handle_clear=[-18,-25,-42],delete_queue_wakeup_status=-51,admitted_delete_scope='caller-private never-published new1/1 semaphore, no users/waiters',published_teardown_qualified=False,all_kernel_helpers_recursively_proven=False,native_api_invoked=False,firmware_executed=False,flash_ready=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True);a=p.parse_args();print(json.dumps(inspect(a.stock.read_bytes(),a.objdump.resolve()),indent=2))
