#!/usr/bin/env python3
"""Actual local queue table, extent and deletion provenance; bounded read-only evidence."""
import argparse,json
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
from ep7_queue_transport import W as EXISTING
WINDOWS=[(0x60036caf,0x60036ced),(0x60036d14,0x60036d3c),(0x60036f93,0x60036fa7),
         (0x60030c4c,0x60030ca7),(0x60031072,0x60031085),(0x600310de,0x600310f8)]
W={address:instruction for address,instruction in EXISTING.items()
   if any(start<=address<end for start,end in WINDOWS)}
W.update({
    0x60036caf:('mov','28672,d2'),0x60036cb2:('and','d0,d2'),0x60036cb4:('asr','12,d2'),
    0x60036cca:('mov','4095,d3'),0x60036ccd:('and','d0,d3'),0x60036ccf:('cmp','1,d3'),
    0x60036cd3:('asl2','d2'),0x60036cd4:('mov','d2,a3'),0x60036cd6:('add','-1880096764,a3'),
    0x60036cdc:('mov','(a3),a0'),0x60036cde:('mov','(60,a0),a0'),
    0x60036ce1:('movhu','(26,a0),d1'),0x60036ce4:('exth','d1'),0x60036ce5:('cmp','d1,d3'),
    0x60036d16:('asl2','d3'),0x60036d17:('mov','(232,a0),a0'),0x60036d1d:('add','d3,a0'),
    0x60036d1f:('mov','(-4,a0),a0'),0x60036d22:('movhu','(a0),d0'),
    0x60036d24:('cmp','0,d0'),0x60036d26:('beq','0x60036d33'),
    0x60036d2a:('mov','(232,a0),a0'),0x60036d30:('mov','(-4,a0),a2'),
    0x60036d37:('mov','-42,d0'),
    0x60030c70:('movbu','(a0),d0'),0x60030c72:('or','128,d0'),0x60030c75:('movbu','d0,(a0)'),
    0x60031072:('mov','20,a0'),0x60031074:('add','a3,a0'),0x60031076:('movbu','(a0),d0'),
    0x60031078:('btst','128,d0'),0x6003107b:('beq','0x60031085'),
    0x6003107d:('mov','(12,a0),a0'),0x60031080:('call','0x60035ffa,[d2,a2,a3],12'),
    0x600310ea:('mov','(232,a0),a0'),0x600310f2:('mov','(-4,a0),a0'),
    0x600310f5:('clr','d0'),0x600310f6:('movhu','d0,(a0)'),
})
def inspect(stock,objdump):
    evidence=inspect_windows(stock,objdump,WINDOWS,W)
    return dict(scope=__doc__,objdump_version=evidence['objdump_version'],input_structure=evidence['input_structure'],
        checked_instructions=evidence['checked_instructions'],per_core_context_table='0x8ff00004',
        root_limits_pointer_offset=60,limits_queue_count_offset=26,root_queue_table_offset=232,
        index='(handle & 0xfff) - 1',queue_fields=dict(id=0,attributes=20,maximum=24,ring_bytes=28,backing=32),
        allocated_backing_attribute_bit=128,delete_frees_backing_then_clears_id=True,
        double_read_is_lifetime_lease=False,runtime_queue_objects_inspected=False,
        hash_checks_performed=False,firmware_modified=False,target_executed=False,flash_ready=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True)
    args=p.parse_args();print(json.dumps(inspect(args.stock,args.objdump),indent=2))
