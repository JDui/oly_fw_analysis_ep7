#!/usr/bin/env python3
"""Read-only timed-delay vs wakeup-consuming sleep evidence for cleanup progress."""
import argparse,json
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
WINDOWS=[(0x600313ef,0x60031477),(0x60033caf,0x60033ce1),
         (0x60036e23,0x60036e8a),(0x60036eca,0x60036ede),(0x612c7307,0x612c732e)]
W={
    0x600313ef:('mov','d0,d2'),0x600313fc:('mov','(16,a0),a0'),
    0x600313ff:('movbu','(a0),d1'),0x6003140c:('mov','-25,d2'),
    0x60031410:('cmp','2147483647,d2'),0x60031418:('mov','-17,d2'),
    0x6003141f:('call','0x60038594,[],0'),0x6003142a:('mov','(96,a0),a0'),
    0x6003142d:('mov','(a0),a2'),0x6003142f:('inc','d2'),0x60031430:('mov','d2,(36,a2)'),
    0x60031439:('mov','(72,a0),d0'),0x6003143c:('mov','28,a1'),0x6003143e:('add','a2,a1'),
    0x60031440:('mov','d0,(a1)'),0x6003144d:('mov','a0,(4,a1)'),
    0x60031450:('mov','a1,(a0)'),0x6003145b:('mov','a1,(4,a0)'),
    0x6003145e:('mov','a2,a0'),0x6003145f:('mov','2,d0'),
    0x60031461:('call','0x60033caf,[a2,a3],12'),0x60031466:('mov','(64,a2),d2'),
    0x60031469:('cmp','-50,d2'),0x6003146d:('clr','d2'),
    0x6003146e:('call','0x6003860b,[],0'),0x60031473:('mov','d2,d0'),
    0x60031474:('ret','[d2,a2,a3],16'),
    0x60033caf:('clr','d1'),0x60033cb0:('mov','d1,(64,a0)'),
    0x60033cb3:('movhu','d0,(14,a0)'),0x60033cbf:('mov','4,d0'),
    0x60033cc1:('movhu','d0,(12,a0)'),0x60033cd9:('call','0x6003593f,[d2,a2,a3],16'),
    0x60036e23:('mov','d0,a3'),0x60036e6b:('mov','21,a0'),0x60036e6d:('add','a2,a0'),
    0x60036e6f:('movbu','(a0),d0'),0x60036e73:('beq','0x60036e7c'),
    0x60036e75:('add','-1,d0'),0x60036e77:('movbu','d0,(a0)'),
    0x60036ecb:('mov','1,d0'),0x60036ecd:('call','0x60033caf,[a2,a3],12'),
    0x612c7311:('call','0x60036e23,[d2,d3,a2,a3],20'),
    0x612c731c:('mov','1630978367,d0'),
}
def inspect(stock,objdump):
    evidence=inspect_windows(stock,objdump,WINDOWS,W)
    return dict(scope=__doc__,objdump_version=evidence['objdump_version'],input_structure=evidence['input_structure'],
        checked_instructions=evidence['checked_instructions'],candidate_delay='0x600313ef',native_frame_bytes=16,
        native_save_mask=['d2','a2','a3'],fixed_input_units=1,timer_counter='input + 1',wait_reason=2,
        normal_timer_expiry_maps_minus50_to_zero=True,other_status_preserved=True,
        rejected_sleep_candidate='0x60036e23',sleep_pending_wakeup_byte=21,sleep_wait_reason=1,
        transitive_scheduler_and_timer_proven=False,unit_duration_proven=False,cleanup_policy_bound=False,
        hash_checks_performed=False,firmware_modified=False,target_executed=False,flash_ready=False)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock',type=Path,required=True);parser.add_argument('--objdump',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(inspect(args.stock,args.objdump),indent=2))
