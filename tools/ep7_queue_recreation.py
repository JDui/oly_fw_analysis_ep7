#!/usr/bin/env python3
"""Queue auto-allocation can reuse deleted pipeline IDs; read-only current-input evidence."""
import argparse,json
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
WINDOWS=[(0x60030269,0x600302e8),(0x6003541e,0x6003551c),(0x600310de,0x600310f8)]
CHECKS=[(0x600411e0,'<I',(0x600410d8,)),(0x600410f0,'<2H',(0,255))]
W={
    0x60030269:('mov','a0,a2'),0x600302aa:('mov','(4,a2),d0'),0x600302ad:('cmp','0,d0'),
    0x600302b1:('mov','-17,d2'),0x600302b6:('call','0x60038594,[],0'),
    0x600302bd:('clr','d0'),0x600302be:('mov','sp,a0'),0x600302bf:('inc4','a0'),
    0x600302c0:('call','0x6003541e,[d2,d3,a2,a3],24'),0x600302c5:('mov','d0,d2'),
    0x600302c8:('ble','0x60030324'),0x600302cc:('mov','-4,d1'),
    0x600302ce:('movhu','d0,(a0)'),0x600302d2:('mov','20,a0'),
    0x600302d7:('mov','(a2),d0'),0x600302d9:('mov','d0,(a0)'),
    0x600302dc:('lne',''),0x600302df:('call','0x60030c4c,[d2,a2,a3],16'),
    0x6003541e:('mov','a0,(4,sp)'),0x60035420:('mov','d0,a3'),
    0x6003542e:('mov','(60,a1),a2'),0x60035437:('mov','(232,a1),d0'),
    0x6003543f:('and','4095,d1'),0x60035443:('beq','0x60035448'),
    0x60035445:('jmp','0x600354dd'),0x60035451:('mov','24,a3'),
    0x6003545b:('mov','(56,a1),d0'),0x6003545e:('mov','24,a0'),
    0x6003546e:('mov','(232,a1),d3'),0x60035472:('movhu','(2,a0),d2'),
    0x60035475:('mov','2,a2'),0x60035477:('add','a3,a2'),
    0x60035479:('movhu','(a2),d0'),0x6003547c:('movhu','(a3),d1'),
    0x6003547f:('sub','d1,d0'),0x60035481:('cmp','d0,d2'),
    0x60035482:('blt','0x60035487'),0x60035487:('movhu','(a0),d0'),
    0x6003548a:('mov','d0,d2'),0x6003548d:('asl2','d1'),
    0x60035492:('mov','(-4,a1),a1'),0x60035495:('movhu','(a1),d1'),
    0x60035497:('cmp','0,d1'),0x60035499:('bne','0x6003549f'),
    0x6003549d:('bra','0x600354ad'),0x6003549f:('inc','d2'),
    0x600354a1:('movhu','(a2),d2'),0x600354a6:('cmp','d2,d1'),
    0x600354a7:('lle',''),0x600354a8:('movhu','(a3),d0'),
    0x600354ab:('inc','d0'),0x600354ac:('lra',''),
    0x600354b3:('mov','-34,d0'),0x600354ca:('movhu','(a1),d1'),
    0x600354cc:('inc','d1'),0x600354cd:('movhu','d1,(a1)'),
    0x600354dd:('movhu','(24,a2),d2'),0x600354e2:('ble','0x600354e8'),
    0x600354e4:('mov','-18,d0'),0x60035513:('movhu','d1,(a1)'),
    0x60035518:('mov','d1,(a0)'),0x60035519:('retf','[d2,d3,a2,a3],24'),
    0x600310ea:('mov','(232,a0),a0'),0x600310f2:('mov','(-4,a0),a0'),
    0x600310f5:('clr','d0'),0x600310f6:('movhu','d0,(a0)'),
}
def inspect(stock,objdump):
    evidence=inspect_windows(stock,objdump,WINDOWS,W,CHECKS)
    return dict(scope=__doc__,objdump_version=evidence['objdump_version'],input_structure=evidence['input_structure'],
        checked_instructions=evidence['checked_instructions'],checked_data_rows=len(CHECKS),
        queue_create='0x60030269',allocation_helper='0x6003541e',create_passes_auto_id_zero=True,
        configured_limits_pointer='0x600410d8',fixed_id_limit=0,total_id_limit=255,
        automatic_id_range=[1,255],pipeline_ids=[0x4b,0x4c,0x4d,0xab,0x4f],
        automatic_selection_uses_zero_object_id=True,deletion_clears_object_id=True,
        initializer_copies_new_maximum_and_ring=True,same_handle_implies_same_instance=False,
        runtime_recreation_observed=False,all_creation_deletion_callers_qualified=False,
        hash_checks_performed=False,firmware_modified=False,target_executed=False,flash_ready=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True)
    args=p.parse_args();print(json.dumps(inspect(args.stock,args.objdump),indent=2))
