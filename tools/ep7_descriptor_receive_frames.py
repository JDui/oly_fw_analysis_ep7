#!/usr/bin/env python3
"""Read-only descriptor receive call-chain and unchanged alternate-queue evidence."""
import argparse,json
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
from ep7_descriptor_frames import W as FRAME_W

WINDOWS=[(0x603ef892,0x603ef998),(0x603f26a1,0x603f26c5),
         (0x603df9f1,0x603dfa0f),(0x603dfa39,0x603dfa41),
         (0x603eeb7c,0x603eeb8a),(0x603eeb9f,0x603eeba4)]
W={a:v for a,v in FRAME_W.items() if any(lo<=a<hi for lo,hi in WINDOWS)}
W.update({
    0x603ef8a9:('movhu','(0x60040d74),d0'),0x603ef8af:('mov','a2,a0'),
    0x603ef8b2:('mov','300,d1'),0x603ef8ba:('cmp','0,d0'),
    0x603ef8c6:('movhu','(0x60040d76),d0'),0x603ef8cc:('mov','a2,a0'),
    0x603ef8cf:('mov','300,d1'),0x603ef8d7:('cmp','0,d0'),
    0x603ef8f1:('movhu','(0x60040d74),d0'),0x603ef8f7:('mov','a2,a0'),
    0x603ef8fa:('mov','300,d1'),0x603ef902:('cmp','0,d0'),
    0x603ef90e:('movhu','(0x60040d76),d0'),0x603ef914:('mov','a2,a0'),
    0x603ef917:('mov','300,d1'),0x603ef91f:('cmp','0,d0'),
    0x603ef953:('movhu','(0x60040e32),d0'),0x603ef959:('mov','a2,a0'),
    0x603ef962:('cmp','0,d0'),
    0x603f26ac:('movhu','(0x60040d7a),d0'),0x603f26b2:('mov','a2,a0'),
    0x603f26bb:('cmp','0,d0'),
    0x603df9f1:('mov','a0,a2'),0x603df9f2:('mov','-1,d1'),
    0x603df9f4:('mov','d1,(4,sp)'),0x603df9fb:('mov','300,d1'),
    0x603dfa04:('call','0x603eeb57,[d2,d3,a2,a3],44'),
    0x603dfa0b:('cmp','0,d0'),0x603dfa3e:('ret','[a2],16'),
    0x603eeb81:('mov','(48,sp),d1'),0x603eeba1:('ret','[d2,d3,a2,a3],44'),
})
CHECKS=[(0x60040d74,'<H',(0x4c,)),(0x60040d76,'<H',(0x4d,)),
        (0x60040e32,'<H',(0xab,)),(0x60040d7a,'<H',(0x4f,)),
        (0x6003b430,'<5I',(0x4d,0,300,9728,0))]
def inspect(stock,objdump):
    evidence=inspect_windows(stock,objdump,WINDOWS,W,CHECKS)
    return dict(scope=__doc__,objdump_version=evidence['objdump_version'],
        input_structure=evidence['input_structure'],checked_instructions=evidence['checked_instructions'],
        checked_data_rows=len(CHECKS),
        direct_dual_return_pcs=['0x603ef8ba','0x603ef8d7','0x603ef902','0x603ef91f'],
        shared_helper_return_pc='0x603dfa0b',
        shared_helper_parents={'0x603ef962':'0xab','0x603f26bb':'0x4f'},
        wrapper_offsets=dict(return_pc=44,timeout=48,direct_descriptor=56,
                             shared_parent_return_pc=60,shared_descriptor=64),
        alternate_queue=dict(handle='0x4d',row='0x6003b430',maximum=300,ring_bytes=9728),
        all_receive_sites_qualified=False,original_wrapper_fallback_only_for_nonexpanded_queues=True,
        hash_checks_performed=False,firmware_modified=False,target_executed=False,flash_ready=False)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock',type=Path,required=True)
    parser.add_argument('--objdump',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(inspect(args.stock,args.objdump),indent=2))
