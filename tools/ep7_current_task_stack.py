#!/usr/bin/env python3
"""Current-task TCB stack extent provenance, read-only without SHA."""
import argparse,json
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
WINDOWS=[(0x600317ac,0x600317f0),(0x6003069f,0x600306ba),(0x600329c5,0x600329e2),
         (0x60030afa,0x60030b25),(0x6003221e,0x60032287),(0x60035925,0x6003593f),
         (0x600312f3,0x60031306)]
W={
    0x600317ac:('mov','(0x8050),d0'),0x600317af:('mov','-1880096764,a2'),
    0x600317b5:('asl2','d0'),0x600317b6:('mov','(d0,a2),a1'),
    0x600317b8:('mov','(28,a1),a1'),0x600317bb:('movbu','(a1),d1'),
    0x600317d1:('movbu','(1,a1),d0'),0x600317d8:('mov','-25,d0'),
    0x600317dc:('mov','(0x8050),d0'),0x600317e0:('mov','(d0,a2),a1'),
    0x600317e2:('mov','(96,a1),a1'),0x600317e5:('mov','(a1),a1'),
    0x600317e7:('movhu','(16,a1),d0'),0x600317ea:('movhu','d0,(a0)'),
    0x600317ec:('clr','d0'),0x600317ed:('retf','[a2],4'),
    0x600306a3:('movhu','d0,(16,a0)'),0x600306a8:('mov','68,a0'),
    0x600306aa:('add','d0,a0'),0x600306ad:('mov','(a2),d0'),0x600306af:('mov','d0,(a0)'),
    0x600306b5:('call','0x60030afa,[d2,a2,a3],16'),
    0x600329ca:('movhu','d0,(16,a0)'),0x600329d0:('add','68,a0'),
    0x600329d2:('mov','-6,d1'),0x600329d5:('mov','(a1),d0'),0x600329d7:('mov','d0,(a0)'),
    0x600329dd:('call','0x60030afa,[d2,a2,a3],16'),
    0x60030afa:('mov','a0,a3'),0x60030afb:('mov','68,a2'),0x60030afd:('add','a3,a2'),
    0x60030aff:('mov','20,d2'),0x60030b01:('add','a2,d2'),
    0x60030b0a:('mov','(16,a2),d0'),0x60030b0d:('call','0x60035edc,[d2,d3,a2,a3],16'),
    0x60030b1a:('mov','d2,a1'),0x60030b1c:('mov','a0,(a1)'),
    0x60032221:('mov','68,a2'),0x60032223:('add','a0,a2'),
    0x6003224c:('mov','(20,a2),d2'),0x6003224f:('mov','(16,a2),d1'),
    0x60032252:('add','d1,d2'),0x60032253:('mov','20,d1'),0x60032255:('sub','d1,d2'),
    0x60032259:('mov','d2,(24,a0)'),0x6003225f:('mov','(8,a2),d1'),
    0x60032262:('mov','d1,(4,a1)'),0x60032271:('and','28672,d3'),
    0x60032275:('asr','12,d3'),0x60032278:('cmp','d1,d3'),
    0x60035925:('add','68,a2'),0x60035927:('mov','(20,a2),d1'),
    0x6003592a:('mov','(16,a2),d0'),0x6003592d:('mov','(8,a2),a0'),0x60035930:('add','d0,d1'),
    0x600312f3:('mov','68,a3'),0x600312f5:('add','a2,a3'),
    0x600312fe:('mov','(20,a3),a0'),0x60031301:('call','0x60035ffa,[d2,a2,a3],12'),
}
def inspect(stock,objdump):
    evidence=inspect_windows(stock,objdump,WINDOWS,W)
    return dict(scope=__doc__,objdump_version=evidence['objdump_version'],input_structure=evidence['input_structure'],
        checked_instructions=evidence['checked_instructions'],current_task_api='0x600317ac',core_word='0x8050',
        per_core_context_table='0x8ff00004',current_cell_context_offset=96,current_tcb_id_offset=16,
        tcb_creation_spec_offset=68,creation_spec_bytes=24,tcb_entry_offset=76,tcb_stack_bytes_offset=84,tcb_stack_base_offset=88,
        fresh_stack_initializer='0x60030afa',initial_saved_sp='stack_base + stack_bytes - 20',
        actual_stack_base_retained_in_tcb=True,current_view_is_task_generation_lease=False,
        task_cancellation_migration_qualified=False,provider_installation_ready=False,
        hash_checks_performed=False,firmware_modified=False,target_executed=False,flash_ready=False)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock',type=Path,required=True);parser.add_argument('--objdump',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(inspect(args.stock,args.objdump),indent=2))
