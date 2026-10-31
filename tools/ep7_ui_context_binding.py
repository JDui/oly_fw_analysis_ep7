#!/usr/bin/env python3
"""Actual GUI service allocator selection and its two leaf ABIs; no hashes."""
import argparse,json
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows

WINDOWS=[(0x60cfd438,0x60cfd46e),(0x60d39f41,0x60d39f58),
    (0x60d43e80,0x60d43e8f),(0x60cff51e,0x60cff52b),(0x60cff571,0x60cff579),
    (0x60d3379b,0x60d337ad),(0x60cfe586,0x60cfe5a0),(0x60cfe5c9,0x60cfe5f6),
    (0x60d02c64,0x60d02c87),(0x60cfcec4,0x60cfceec),(0x60dd5067,0x60dd5083)]
W={
    0x60cfd438:('mov','2880,d0'),0x60cfd43b:('call','0x60cff68e,[],4'),
    0x60cfd440:('mov','a0,a1'),0x60cfd444:('beq','0x60cfd44e'),
    0x60cfd447:('call','0x60d39f41,[],4'),0x60cfd44e:('cmp','0,a0'),
    0x60cfd450:('bne','0x60cfd455'),0x60cfd455:('call','0x60d337a4,[],0'),
    0x60cfd45c:('call','0x60d3379b,[],0'),
    0x60d39f41:('call','0x60d43e80,[d2,a2,a3],16'),
    0x60d39f48:('mov',str(0x60faaab4)+',d0'),0x60d39f4e:('mov','d0,(a0)'),
    0x60d39f4f:('mov','257,d0'),0x60d39f52:('movhu','d0,(4,a0)'),0x60d39f55:('ret','[],4'),
    0x60d43e80:('call','0x60cff51e,[d2,d3,a2,a3],20'),
    0x60d43e88:('mov',str(0x60fac34c)+',d0'),
    0x60cff51e:('call','0x60cfd747,[a2],8'),0x60cff524:('mov',str(0x60f9477c)+',d0'),
    0x60cff572:('call','0x60d337a4,[],0'),
    0x60d3379b:('mov','(0x61fb3138),a0'),0x60d337a1:('retf','[],0'),
    0x60d337a4:('mov','a0,(0x61fb3138)'),0x60d337aa:('retf','[],0'),
    0x60cfe586:('movbu','d0,(28,a0)'),0x60cfe589:('movbu','d1,(29,a0)'),
    0x60cfe58c:('retf','[],0'),0x60cfe58f:('movm','[a2],(sp)'),
    0x60cfe591:('mov','d0,a2'),0x60cfe593:('movbu','(28,a0),d0'),
    0x60cfe596:('movbu','d0,(a1)'),0x60cfe598:('movbu','(29,a0),d0'),
    0x60cfe59b:('movbu','d0,(a2)'),0x60cfe59d:('retf','[a2],4'),
    0x60cfe5c9:('movm','[a2,a3],(sp)'),0x60cfe5cb:('add','-8,sp'),
    0x60cfe5cf:('call','0x60d3379b,[],0'),0x60cfe5d7:('inc4','a1'),
    0x60cfe5db:('add','5,d0'),0x60cfe5df:('mov','(248,a2),a2'),
    0x60cfe5e3:('calls','(a2)'),0x60cfe5e5:('movbu','(4,sp),d0'),
    0x60cfe5e8:('movbu','(5,sp),d1'),0x60cfe5eb:('mov','a3,a0'),
    0x60cfe5ec:('call','0x60d109db,[],4'),0x60cfe5f3:('ret','[a2,a3],16'),
    0x60d02c6c:('mov','(248,a2),a2'),0x60d02c70:('calls','(a2)'),
    0x60d02c72:('call','0x60d3379b,[],0'),0x60d02c79:('movbu','(12,sp),d0'),
    0x60d02c7c:('movbu','(13,sp),d1'),0x60d02c81:('mov','(244,a1),a1'),
    0x60d02c85:('calls','(a1)'),
    0x60cfcec4:('mov',str(0x60dd5067)+',d0'),0x60cfceca:('mov','d0,(12,sp)'),
    0x60cfced0:('mov','16384,d0'),0x60cfced3:('mov','d0,(20,sp)'),
    0x60cfcee5:('call','0x607a791e,[d2,d3,a2,a3],36'),
    0x60dd5079:('call','0x60cfd311,[d2,d3,a2,a3],16')}
CHECKS=[(table+244,'<2I',(0x60cfe586,0x60cfe58f)) for table in
    [0x60faaab4,0x60fac34c,0x60f9477c]]

def inspect(stock,objdump):
    e=inspect_windows(stock,objdump,WINDOWS,W,CHECKS)
    return dict(scope=__doc__,objdump_version=e['objdump_version'],input_structure=e['input_structure'],
        checked_instructions=e['checked_instructions'],checked_context_vtable_pairs=3,
        service_slot='0x61fb3138',service_vtable='0x60faaab4',service_type='0x0101',service_allocation_bytes=2880,
        getter='0x60d3379b',selection_get='0x60cfe58f',selection_set='0x60cfe586',
        context_bytes=[28,29],get_output_registers=['a1','d0'],set_input_registers=['d0','d1'],
        object_register='a0',get_owns_self_frame_bytes=4,select_owns_self_frame_bytes=0,
        gui_entry='0x60dd5067',gui_configured_stack_bytes=16384,gui_domain_static_proved=False,
        base_constructor_publishes_before_final_vtable=True,readiness_requires_admitted_live_gui_service=True,
        native_context_is_global=True,native_context_mutex_or_lifetime_lease_proved=False,
        hash_checks_performed=False,firmware_modified=False,target_executed=False,renderer_ready=False,flash_ready=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True)
    args=p.parse_args();print(json.dumps(inspect(args.stock,args.objdump),indent=2))
