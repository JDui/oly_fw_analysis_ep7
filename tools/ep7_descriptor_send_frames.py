#!/usr/bin/env python3
"""Read-only descriptor send ownership, native arguments and fallback frame evidence."""
import argparse,json
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
from ep7_descriptor_frames import W as FRAME_W

WINDOWS=[(0x603df812,0x603df815),(0x603df8ba,0x603df8c2),
         (0x603dfc25,0x603dfc47),(0x603ef898,0x603ef89b),
         (0x603ef92f,0x603ef94a),(0x603ef951,0x603ef953),
         (0x603ef984,0x603ef995),(0x603dfa41,0x603dfa4e),
         (0x603dfa8d,0x603dfab4),(0x603eebc1,0x603eebd5)]
W={a:v for a,v in FRAME_W.items() if any(lo<=a<hi for lo,hi in WINDOWS)}
W.update({
    0x603df8c0:('mov','d0,d3'),0x603dfc25:('mov','a2,a0'),
    0x603dfc3f:('call','0x603dfa41,[d2,a2],20'),0x603dfc44:('mov','d0,d2'),
    0x603ef92f:('mov','a2,a0'),0x603ef930:('movhu','(0x60040e32),d0'),
    0x603ef984:('movhu','(0x60040d7a),d0'),0x603ef98a:('mov','a2,a0'),
    0x603ef993:('bra','0x603ef998'),
    0x603dfa41:('mov','a0,a2'),0x603dfa47:('mov','d0,d2'),
    0x603dfa8d:('mov','a2,a0'),0x603dfa8e:('mov','-1,d0'),
    0x603dfa90:('mov','d0,(4,sp)'),0x603dfa97:('mov','d2,d0'),
    0x603dfa98:('mov','300,d1'),0x603dfaa1:('call','0x603eeba4,[d2,d3,a2],36'),
    0x603dfaa8:('cmp','0,d0'),0x603dfab1:('ret','[d2,a2],20'),
    0x603eebc8:('mov','(40,sp),d1'),0x603eebd2:('ret','[d2,d3,a2],36'),
})
def inspect(stock,objdump):
    evidence=inspect_windows(stock,objdump,WINDOWS,W)
    return dict(scope=__doc__,objdump_version=evidence['objdump_version'],
        input_structure=evidence['input_structure'],checked_instructions=evidence['checked_instructions'],
        send_call='0x603dfaa1',original_wrapper='0x603eeba4',wrapper_return_pc='0x603dfaa8',
        parent_return_pcs={'normal':'0x603dfc44','dual_relay':'0x603ef93e','kind19_relay':'0x603ef993'},
        wrapper_offsets=dict(return_pc=36,timeout=40,parent_return_pc=56,
            normal_owner_return_pc=104,normal_descriptor=124,dual_descriptor=68,kind19_descriptor=60),
        native_frame_bytes=36,native_save_mask=['d2','d3','a2'],stock_nominal_bytes=300,
        all_send_sites_qualified=False,native_retirement_owner_bound=False,
        hash_checks_performed=False,firmware_modified=False,target_executed=False,flash_ready=False)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock',type=Path,required=True)
    parser.add_argument('--objdump',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(inspect(args.stock,args.objdump),indent=2))
