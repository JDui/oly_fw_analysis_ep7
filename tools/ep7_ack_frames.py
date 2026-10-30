#!/usr/bin/env python3
"""Read-only ACK/drain ownership and notification seam evidence, without SHA."""
import argparse,json
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
WINDOWS=[(0x603df812,0x603df815),(0x603df8ba,0x603df8c2),
         (0x603dfc5f,0x603dfc7a),(0x603e058a,0x603e0594),
         (0x603e05be,0x603e05d6),(0x603f26a1,0x603f2770),(0x603df97d,0x603df9f1),
         (0x603e6c8d,0x603e6d04)]
W={
    0x603df812:('mov','sp,a3'),0x603df813:('add','20,a3'),
    0x603df8ba:('mov','a3,a0'),0x603df8bb:('call','0x603dfb10,[d2,d3,a2,a3],48'),
    0x603dfc5f:('mov','a2,a0'),0x603dfc63:('mov','a2,a0'),
    0x603dfc67:('call','0x603df97d,[a2,a3],32'),0x603dfc77:('ret','[d2,d3,a2,a3],48'),
    0x603e058a:('mov','sp,a2'),0x603e058b:('add','12,a2'),
    0x603e058f:('call','0x603dfc7a,[d2,d3,a2,a3],16'),
    0x603e05be:('mov','a2,a0'),0x603e05c2:('mov','a2,a0'),
    0x603e05c6:('call','0x603df97d,[a2,a3],32'),0x603e05cb:('mov','a2,a0'),
    0x603e05cd:('call','0x603dfc7a,[d2,d3,a2,a3],16'),0x603e05d2:('cmp','-2,d0'),
    0x603f26a7:('mov','sp,a2'),0x603f26a8:('inc4','a2'),
    0x603f2769:('call','0x603df97d,[a2,a3],32'),
    0x603df97d:('mov','a0,a2'),0x603df97e:('movhu','d0,(12,sp)'),
    0x603df981:('mov','(44,a2),d0'),0x603df986:('mov','d0,(16,sp)'),
    0x603df988:('mov','(48,a2),d0'),0x603df98d:('mov','d0,(20,sp)'),
    0x603df9ac:('mov','(32,a2),d0'),0x603df9af:('mov','sp,a0'),0x603df9b0:('add','12,a0'),
    0x603df9bb:('mov','12,d1'),0x603df9c3:('call','0x603eeba4,[d2,d3,a2],36'),
    0x603df9ee:('ret','[a2,a3],32'),
    0x603e6c8d:('mov','a0,a3'),0x603e6c8e:('mov','40,a2'),
    0x603e6c90:('add','a3,a2'),0x603e6c9f:('mov','d1,(a2)'),
    0x603e6ccb:('mov','(36,a3),d0'),0x603e6cce:('call','0x60353cb7,[d2,a2],12'),
}
def inspect(stock,objdump):
    evidence=inspect_windows(stock,objdump,WINDOWS,W)
    return dict(scope=__doc__,objdump_version=evidence['objdump_version'],input_structure=evidence['input_structure'],
        checked_instructions=evidence['checked_instructions'],original_ack='0x603df97d',native_frame_bytes=32,
        layouts=dict(normal=dict(return_pc='0x603dfc6c',owner_pc_offset=80,descriptor_offset=100),
                     drain=dict(return_pc='0x603e05cb',descriptor_offset=44),
                     worker=dict(return_pc='0x603f2770',descriptor_offset=36)),
        ack_packet_bytes=12,ack_sends_original_metadata_field=48,retire_before_original_notification=True,
        reviewed_cleanup_direct_store_descriptor_offset=40,transitive_descriptor_identity_preservation_proven=False,
        native_retirement_progress_policy_bound=False,all_ack_callers_qualified=False,
        hash_checks_performed=False,firmware_modified=False,target_executed=False,flash_ready=False)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock',type=Path,required=True);parser.add_argument('--objdump',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(inspect(args.stock,args.objdump),indent=2))
