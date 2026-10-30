#!/usr/bin/env python3
"""Read-only capture producer and command-input evidence for an owned stack scope."""
import argparse,json
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows

WINDOWS=[(0x602ac3d7,0x602ac3e5),(0x602ac748,0x602ac75d),
         (0x602ac80c,0x602ac873),(0x6020beb4,0x6020beca),(0x6020beec,0x6020bef0),
         (0x600514e4,0x60051514),(0x60051547,0x60051570),
         (0x600515b0,0x600515de),(0x60051095,0x6005109f)]
W={
    0x602ac3d7:('mov','a2,d0'),0x602ac3d9:('call','0x602ac8d0,[],0'),
    0x602ac3de:('call','0x602ac748,[d2,a2,a3],32'),0x602ac3e3:('bra','0x602ac3fd'),
    0x602ac748:('mov','d0,d2'),0x602ac749:('mov','148,d0'),
    0x602ac74c:('call','0x60022700,[],4'),0x602ac753:('mov','a0,a3'),
    0x602ac754:('mov','d2,(8,a3)'),0x602ac757:('mov','8193,d0'),0x602ac75a:('movhu','d0,(72,a3)'),
    0x602ac80c:('mov','sp,a0'),0x602ac816:('inc4','a0'),0x602ac820:('mov','16,d1'),
    0x602ac82b:('mov','-1,a1'),0x602ac84f:('mov','19,d0'),0x602ac851:('mov','d0,(12,sp)'),
    0x602ac853:('mov','68,d0'),0x602ac855:('mov','d0,(8,sp)'),
    0x602ac85e:('mov','d0,(4,sp)'),0x602ac860:('mov','a3,(16,sp)'),
    0x602ac862:('movhu','(0x60040d72),d0'),
    0x602ac869:('call','0x6020beb4,[d2,d3],48'),0x602ac870:('ret','[d2,a2,a3],32'),
    0x6020beb4:('mov','d0,d3'),0x6020beb5:('mov','a0,(24,sp)'),
    0x6020beb7:('mov','d1,(28,sp)'),0x6020bebc:('mov','a1,d1'),
    0x6020bebe:('call','0x600514b6,[d2,d3,a2,a3],48'),
    0x6020beec:('mov','d2,d0'),0x6020beed:('ret','[d2,d3],48'),
    0x600514ec:('call','0x60036ede,[d2,d3,a2,a3],40'),
    0x60051505:('mov','-2,d1'),0x60051509:('cmp','-50,d0'),0x60051510:('mov','-1,d0'),
    0x60051550:('call','0x60036ede,[d2,d3,a2,a3],40'),0x60051566:('mov','-2,d1'),
    0x6005156a:('cmp','-50,d0'),0x6005156e:('mov','a3,(24,sp)'),
    0x600515bf:('mov','(4,a0),a0'),0x600515c2:('cmp','0,a0'),0x600515c4:('beq','0x600515d9'),
    0x600515ca:('mov','(4,a0),d0'),0x600515d1:('mov','(8,a0),d1'),
    0x600515d4:('call','0x60051078,[d2,d3,a2],40'),
    0x600515d9:('mov','(24,sp),d0'),0x600515db:('ret','[d2,d3,a2,a3],48'),
    0x60051098:('call','0x60035a5e,[d2,d3,a2,a3],20'),
}
def inspect(stock,objdump):
    evidence=inspect_windows(stock,objdump,WINDOWS,W)
    return dict(scope=__doc__,objdump_version=evidence['objdump_version'],
        input_structure=evidence['input_structure'],checked_instructions=evidence['checked_instructions'],
        supported_producer_call='0x602ac3de',metadata_entry='0x602ac748',metadata_allocation_unchanged_bytes=148,
        command_send_call='0x602ac869',command_native_bytes=16,
        proposed_scope_own_frame_bytes=64,proposed_additional_metadata_call_frame_bytes=32,
        command_bridge_offsets=dict(saved_capture_id=44,return_pc=48,command=52,
            scope_wrapper_return_pc=80,original_capture_id=96,scope=104,original_producer_return_pc=176),
        scope_bytes=32,scope_return_label='linked _ep7_capture_scope_native_return',
        send_wrapper_must_preserve='0x600514b6',post_send_notification_call='0x600515d4',
        notification_wrapper='0x60051078',production_senders_use_named_wrapper=True,
        snapshot_source_provider_bound=False,all_native_lifetime_hooks_bound=False,
        hash_checks_performed=False,firmware_modified=False,target_executed=False,flash_ready=False)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock',type=Path,required=True)
    parser.add_argument('--objdump',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(inspect(args.stock,args.objdump),indent=2))
