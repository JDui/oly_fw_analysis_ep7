#!/usr/bin/env python3
"""Read-only worker allocation/process/cleanup seams; no target execution or SHA."""
import argparse,json
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
WINDOWS=[(0x603f26a1,0x603f2799),(0x603f2800,0x603f28da),
         (0x603537eb,0x60353812),(0x60353906,0x60353915),
         (0x60022700,0x60022732),(0x603e6c8d,0x603e6d04),(0x60353cb7,0x60353cf5)]
W={
    0x603f26a1:('movm','[d2,d3,a2],(sp)'),0x603f26a3:('add','-304,sp'),
    0x603f26a7:('mov','sp,a2'),0x603f26a8:('inc4','a2'),
    0x603f2722:('call','0x603f2800,[a2,a3],56'),
    0x603f2769:('call','0x603df97d,[a2,a3],32'),
    0x603f2792:('add','304,sp'),0x603f2796:('ret','[d2,d3,a2],12'),
    0x603f2800:('mov','a0,a3'),0x603f2802:('movhu','d0,(12,sp)'),
    0x603f2809:('mov','sp,a2'),0x603f2810:('add','16,a2'),
    0x603f2832:('call','0x603e611e,[d2,d3,a2,a3],24'),
    0x603f2839:('mov','sp,a1'),0x603f283a:('add','12,a1'),0x603f283c:('mov','a2,a0'),
    0x603f283e:('call','0x603537eb,[d2,d3,a2,a3],44'),
    0x603f2845:('mov','d0,(36,a3)'),0x603f2848:('movhu','(12,sp),d1'),
    0x603f284d:('bne','0x603f285c'),0x603f2850:('call','0x603e62d1,[d2,d3,a2,a3],72'),
    0x603f287d:('movhu','(12,sp),d0'),0x603f2882:('bne','0x603f28b0'),
    0x603f2885:('call','0x603ed4bd,[d2],8'),0x603f288d:('beq','0x603f289c'),
    0x603f288f:('mov','a3,a0'),0x603f2890:('call','0x603e61b8,[d2,a2,a3],24'),
    0x603f2897:('movhu','d0,(12,sp)'),0x603f28b8:('call','0x603e6b83,[d2,d3,a2,a3],52'),
    0x603f28bf:('mov','a3,a0'),0x603f28c0:('call','0x603e6c8d,[a2,a3],24'),
    0x603f28c8:('call','0x603ed7e2,[a2],16'),0x603f28d0:('movhu','d0,(192,a3)'),
    0x603f28d7:('ret','[a2,a3],56'),
    0x603537eb:('mov','d0,(24,sp)'),0x603537ed:('mov','a0,a2'),
    0x603537ee:('mov','a1,(16,sp)'),0x603537f0:('mov','15488,d0'),
    0x603537f3:('call','0x60022700,[],4'),0x603537fa:('mov','a0,a3'),
    0x603537fd:('bne','0x60353812'),0x6035380f:('jmp','0x60353caf'),
    0x60353906:('mov','15472,a0'),0x6035390c:('mov','16,d1'),
    0x6035390e:('call','0x4700115e,[d2,a2],8'),
    0x60022700:('cmp','128,d0'),0x60022709:('cmp','2048,d0'),0x60022713:('cmp','16384,d0'),
    0x60022719:('mov','2,d0'),0x6002271b:('call','0x600228b6,[d2,d3,a2,a3],36'),
    0x603e6cce:('call','0x60353cb7,[d2,a2],12'),
    0x60353cdd:('mov','(13248,a2),a0'),0x60353ce9:('call','0x60022732,[],4'),
}
def inspect(stock,objdump):
    evidence=inspect_windows(stock,objdump,WINDOWS,W,[(0x60026e34,'<3I',(192,2112,16448))])
    return dict(scope=__doc__,objdump_version=evidence['objdump_version'],
        input_structure=evidence['input_structure'],checked_instructions=evidence['checked_instructions'],
        checked_data_items=1,stock_job_bytes=15488,qualified_requested_job_bytes=15512,
        both_requests_in_pool_class=2,scope_bytes=48,own_wrapper_bytes=80,additional_native_frame_bytes=56,
        wrapper_additional_live_stack_bytes=136,worker_descriptor_frame_plan_unchanged=True,
        enter_offsets=dict(scope=32,descriptor=140,original_return=136,saved_descriptor=24),
        allocate_offsets=dict(return_pc=4,constructor_return=48,wrapper_label=104,scope=136,descriptor=244,original_return=240,saved_descriptor=128),
        process_cleanup_offsets=dict(return_pc=24,wrapper_label=80,scope=112,descriptor=220,original_return=216,saved_descriptor=104),
        stock_process_and_cleanup_preserved=True,context_wait_policy_bound=False,
        metadata_identity_preservation_closed=False,complete_stack_budget_proven=False,
        hash_checks_performed=False,firmware_modified=False,target_executed=False,flash_ready=False)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock',type=Path,required=True);parser.add_argument('--objdump',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(inspect(args.stock,args.objdump),indent=2))
