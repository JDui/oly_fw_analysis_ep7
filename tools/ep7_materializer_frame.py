#!/usr/bin/env python3
"""Read-only evidence for the exact materializer receive stack mapper; no hashes."""
import argparse,json
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
from ep7_descriptor_frames import W as FRAME_W

WINDOWS=[(0x603df812,0x603df815),(0x603df8ba,0x603df8c2),
         (0x603dfb76,0x603dfb84),(0x603dfc7a,0x603dfca9),
         (0x603e0526,0x603e052d),(0x603e058a,0x603e059c),
         (0x603e05cb,0x603e05d6),(0x603eeb7c,0x603eeb8a),
         (0x603eeb9f,0x603eeba4)]
W={a:v for a,v in FRAME_W.items() if any(lo<=a<hi for lo,hi in WINDOWS)}
W.update({
    0x603df8c0:('mov','d0,d3'),
    0x603dfb7d:('cmp','0,d0'),
    0x603dfc80:('mov','d0,(4,sp)'),
    0x603dfc87:('movhu','(0x60040d72),d0'),
    0x603dfc8e:('exth','d0'),
    0x603dfca2:('cmp','0,d0'),
    0x603dfca4:('beq','0x603dfca9'),
    0x603dfca6:('jmp','0x603e0525'),
    0x603e0594:('cmp','-1,d0'),
    0x603e05d2:('cmp','-2,d0'),
    0x603eeb81:('mov','(48,sp),d1'),
    0x603eeba1:('ret','[d2,d3,a2,a3],44'),
})
def inspect(stock,objdump):
    evidence=inspect_windows(stock,objdump,WINDOWS,W)
    wrapper=44;locals_=424;incoming=16;router=48
    return dict(scope=__doc__,objdump_version=evidence['objdump_version'],
        input_structure=evidence['input_structure'],checked_instructions=evidence['checked_instructions'],
        wrapper_offsets=dict(return_pc=wrapper,timeout=wrapper+4,descriptor_pointer=wrapper+12,
            command=wrapper+152,materializer_return_pc=wrapper+locals_+incoming,
            normal_owner_return_pc=wrapper+locals_+incoming+router,
            normal_descriptor=wrapper+locals_+incoming+router+20,
            drain_descriptor=wrapper+locals_+incoming+12),
        receiver_return_pc='0x603dfca2',normal_parent_return_pc='0x603dfb7d',
        normal_owner_return_pc='0x603df8c0',drain_parent_return_pcs=['0x603e0594','0x603e05d2'],
        native_receive_save_mask=['d2','d3','a2','a3'],native_receive_frame_bytes=44,
        installer_and_task_stack_provider_required=True,complete_entry_closure_proven=False,
        hash_checks_performed=False,firmware_modified=False,target_executed=False,flash_ready=False)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock',type=Path,required=True)
    parser.add_argument('--objdump',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(inspect(args.stock,args.objdump),indent=2))
