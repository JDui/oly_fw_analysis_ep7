#!/usr/bin/env python3
"""Additional stock witnesses used by request278 owner capture/retire bridges."""
import argparse,json
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows

# Activation/publication and child cleanup were checked in the two preceding
# milestones. Check only the newly consumed header and complete-entry facts.
WINDOWS=[(0x60cfdff1,0x60cfe008),(0x60d0239e,0x60d023af),
    (0x60d37b53,0x60d37b58),(0x60d38b64,0x60d38b69),
    (0x60d43d4b,0x60d43d50),(0x60d43dc7,0x60d43dd3),
    (0x60d42d69,0x60d42d6e),(0x60d42dc1,0x60d42dcd),
    (0x60d7ab79,0x60d7ab8c)]
W={
    0x60cfdff1:('mov','a1,(8,sp)'),0x60cfdffa:('movhu','(a1),d0'),
    0x60cfdffc:('mov','a0,a3'),0x60cfdffd:('movhu','d0,(4,a3)'),
    0x60cfe000:('mov','(8,sp),a0'),0x60cfe002:('movhu','(2,a0),d0'),
    0x60cfe005:('movhu','d0,(6,a3)'),
    0x60d0239e:('mov','a0,a2'),0x60d0239f:('mov',str(0x60f94aa0)+',d0'),
    0x60d023a5:('mov','d0,(a2)'),0x60d023a6:('call','0x60d023c6,[],4'),
    0x60d023ac:('ret','[a2],8'),
    0x60d37b53:('movm','[d2,d3,a2,a3],(sp)'),0x60d37b55:('add','-48,sp'),
    0x60d38b64:('mov','1,d0'),0x60d38b66:('ret','[d2,d3,a2,a3],64'),
    0x60d43d4b:('movm','[d2,d3,a2,a3],(sp)'),0x60d43d4d:('add','-20,sp'),
    0x60d43dc7:('mov','(12,sp),a0'),0x60d43dc9:('call','0x60d02bbd,[a2,a3],12'),
    0x60d43dd0:('ret','[d2,d3,a2,a3],36'),
    0x60d42d69:('movm','[d2,d3,a2,a3],(sp)'),0x60d42d6b:('add','-16,sp'),
    0x60d42dc1:('mov','(8,sp),a0'),0x60d42dc3:('call','0x60d02c03,[d2,d3,a2,a3],32'),
    0x60d42dca:('ret','[d2,d3,a2,a3],32'),
    0x60d7ab79:('add','-4,sp'),0x60d7ab7c:('call','0x60d42c67,[],4'),
    0x60d7ab83:('mov',str(0x60cfe5c9)+',a0'),0x60d7ab89:('ret','[],4')}
CHECKS=[(base+offset,'<I',(entry,)) for base,offset,entry in [
    (0x60faaab4,784,0x60d37b53),(0x61032f10,152,0x60d43d4b),
    (0x61032f10,432,0x60d42d69),(0x61032f10,0,0x60d7ab79)]]

def inspect(stock,objdump):
    e=inspect_windows(stock,objdump,WINDOWS,W,CHECKS)
    return dict(scope=__doc__,objdump_version=e['objdump_version'],input_structure=e['input_structure'],
        checked_instructions=e['checked_instructions'],checked_data_rows=len(CHECKS),
        owner_header_type_offset=4,owner_header_id_offset=6,child_list_vtable='0x60f94aa0',
        original_methods=[dict(entry=hex(entry),self_frame=frame) for entry,frame in [
            (0x60d37b53,64),(0x60d43d4b,36),(0x60d42d69,32),(0x60d7ab79,4)]],
        bridge_calls_full_self_prologue_entries=True,destructor_returns_deallocator_in_a0=True,
        reused_evidence=['ui-screen-activation-current.json','ui-owner-lifecycle-current.json'],
        full_bypass_and_allocator_lifetime_closure=False,gui_exclusion_proven=False,
        installed=False,target_executed=False,firmware_built=False,hash_checks_performed=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True)
    a=p.parse_args();print(json.dumps(inspect(a.stock,a.objdump),indent=2))
