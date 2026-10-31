#!/usr/bin/env python3
"""ID193 selector storage, array ownership and native mask navigation boundaries."""
import argparse,json
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows

WINDOWS=[(0x60a4ec0d,0x60a4ec17),(0x60a4ec21,0x60a4ec2b),
    (0x60dde1b9,0x60dde1d8),(0x60dde2fa,0x60dde315),
    (0x60dde248,0x60dde260),(0x60dde690,0x60dde6ab),(0x60dde6e8,0x60dde6f7),
    (0x60de150c,0x60de154d+3),(0x60dde794,0x60dde7a9),
    (0x60dde7d1,0x60dde7fd),(0x60dde7ff,0x60dde819),
    (0x60dde357,0x60dde367),(0x60dde38c,0x60dde3a5),
    (0x60dde3b2,0x60dde3c3),(0x60dde3ec,0x60dde40a)]
W={
    0x60a4ec0d:('call','0x60022700,[],4'),0x60a4ec14:('ret','[],4'),
    0x60a4ec21:('call','0x60022732,[],4'),0x60a4ec28:('ret','[],4'),
    0x60dde1bb:('mov','124,d0'),0x60dde1c1:('call','0x60a4ec03,[],4'),
    0x60dde1cc:('beq','0x60dde1d5'),0x60dde1d0:('call','0x60dde2fa,[d2,a2],12'),
    0x60dde2fa:('mov','d0,d2'),0x60dde303:('mov',str(0x6114f7e4)+',d0'),
    0x60dde309:('mov','d0,(a2)'),0x60dde30c:('call','0x60dde690,[d2,d3,a2,a3],32'),
    0x60dde695:('mov','80,a0'),0x60dde697:('add','a2,a0'),
    0x60dde69c:('mov','d0,(a0)'),0x60dde69e:('mov','d1,(92,a2)'),
    0x60dde6a1:('mov','d1,(88,a2)'),0x60dde6eb:('mov','d0,(a3)'),
    0x60dde6ee:('mov','d0,a1'),0x60dde6f0:('mov','(a0),d0'),
    0x60dde6f1:('mov','a2,a0'),0x60dde6f3:('calls','(a1)'),
    0x60de150c:('movm','[a2],(sp)'),0x60de150e:('add','-8,sp'),
    0x60de1518:('call','0x60dde754,[d2,d3,a2,a3],52'),
    0x60de151d:('movhu','(84,a2),d0'),0x60de1520:('movhu','(0x61fc26ae),d1'),
    0x60de1526:('add','-1,d0'),0x60de1529:('ble','0x60de1532'),
    0x60de152c:('movhu','d0,(0x61fc26ae)'),0x60de1538:('movhu','d0,(86,a2)'),
    0x60de153b:('add','48,a2'),0x60de153d:('mov',str(0x60de1550)+',d0'),
    0x60de1543:('mov','d0,(a2)'),0x60de1544:('mov',str(0x60de1567)+',d0'),
    0x60de154a:('mov','d0,(4,a2)'),0x60de154d:('ret','[a2],12'),
    0x60dde794:('movhu','(4,a0),d0'),0x60dde797:('movhu','d0,(a1)'),
    0x60dde799:('mov','(8,a0),d0'),0x60dde79e:('mov','d0,(92,a1)'),
    0x60dde7a6:('mov','a0,(96,a1)'),
    0x60dde7d4:('movhu','(a0),d0'),0x60dde7d7:('add','d0,d0'),
    0x60dde7d8:('call','0x60a4ec0d,[],4'),0x60dde7e1:('mov','a0,(a1)'),
    0x60dde7e3:('mov','(12,sp),a0'),0x60dde7e5:('movhu','(a0),d0'),
    0x60dde7e8:('ble','0x60dde7fd'),0x60dde7ee:('mov','(a0),a0'),
    0x60dde7f2:('movhu','d0,(d2,a0)'),
    0x60dde800:('add','104,d0'),0x60dde807:('movhu','d0,(a0)'),
    0x60dde80f:('add','106,d1'),0x60dde813:('add','-1,d0'),
    0x60dde817:('movhu','d0,(a0)'),
    0x60dde248:('mov','88,a2'),0x60dde24a:('add','a3,a2'),
    0x60dde251:('mov','(a2),a0'),0x60dde257:('call','0x60a4ec21,[],4'),
    0x60dde25f:('mov','d0,(a2)'),
    0x60dde357:('mov','84,a2'),0x60dde35b:('movhu','(a2),d0'),
    0x60dde38c:('mov','(88,a0),a1'),0x60dde392:('movhu','(d1,a1),d1'),
    0x60dde394:('cmp','0,d1'),0x60dde396:('beq','0x60dde39e'),
    0x60dde398:('movhu','(a2),d1'),0x60dde39c:('cmp','d1,d2'),
    0x60dde39d:('llt',''),0x60dde39e:('movhu','d3,(a3)'),
    0x60dde3b2:('mov','84,a3'),0x60dde3b8:('movhu','(a3),d0'),
    0x60dde3ec:('mov','(88,a0),a1'),0x60dde3f3:('movhu','(d1,a1),d1'),
    0x60dde3f5:('cmp','0,d1'),0x60dde3f7:('beq','0x60dde3ff'),
    0x60dde3f9:('movhu','(a3),d1'),0x60dde3fd:('cmp','d1,d2'),
    0x60dde3fe:('llt',''),0x60dde403:('movhu','d0,(a0)')}
CHECKS=[(0x61140364,'<2I',(1,0x60dde1b4)),(0x6114f330,'<2I',(193,0x60de150c)),
    (0x6114efa0,'<4I',(193,4,0x6114e050,0)),(0x6114e050,'<4H',(0,1,2,3)),
    (0x6114f7e4+40,'<I',(0x60dde221,))]

def inspect(stock,objdump):
    e=inspect_windows(stock,objdump,WINDOWS,W,CHECKS)
    return dict(scope=__doc__,objdump_version=e['objdump_version'],input_structure=e['input_structure'],
        checked_instructions=e['checked_instructions'],checked_data_rows=len(CHECKS),
        selector_allocation_bytes=124,list_id=193,initializer_word='0x6114f334',
        original_initializer='0x60de150c',original_initializer_self_frame=12,
        fields=dict(count=84,index=86,masks=88,values=92,auxiliary=96,first=104,last=106),
        original_mask_bytes=8,new_mask_bytes=12,net_owned_heap_increase=4,
        new_values=[0,1,2,3,4,5],new_categories_initially_disabled=True,
        mask_allocator='0x60a4ec0d',mask_deallocator='0x60a4ec21',
        original_loader_checks_mask_allocation_null=False,
        only_additional_allocation_failure_is_handled=True,stock_navigation_reused=True,
        stock_list_descriptor_modified=False,constructor_reload_bypass_closure=False,
        gui_exclusion_proven=False,renderer_ready=False,installed=False,
        target_executed=False,firmware_built=False,hash_checks_performed=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True)
    a=p.parse_args();print(json.dumps(inspect(a.stock,a.objdump),indent=2))
