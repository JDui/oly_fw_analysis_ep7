#!/usr/bin/env python3
"""GUI041d full-entry graph provenance and parent-before-viewer native retirement."""
import argparse,json
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows

WINDOWS=[(0x60e5dae9,0x60e5db2e),(0x60e4cef8,0x60e4cf21),
    (0x60e4cb9e,0x60e4cbc7),(0x60e4cbe4,0x60e4cbf7),
    (0x60e4cc23,0x60e4cc53),(0x60e260e4,0x60e26130),
    (0x60e261c5,0x60e261dc),(0x60e26a3d,0x60e26a9d),
    (0x60e4ce26,0x60e4ce8b),(0x60e26130,0x60e26188)]
W={
    0x60e5dae9:('add','-4,sp'),0x60e5daec:('mov','8,d0'),0x60e5daee:('mov','463,d1'),
    0x60e5daf1:('call','0x60e4cea8,[d2,d3,a2,a3],52'),
    0x60e5daf8:('mov','a0,(0x61fc436c)'),0x60e5dafe:('ret','[],4'),
    0x60e4cef8:('mov','228,d0'),0x60e4cefb:('call','0x60a4ec03,[],4'),
    0x60e4cf06:('beq','0x60e4cf1e'),0x60e4cf19:('call','0x60e4cb5a,[d3,a2,a3],52'),
    0x60e4cb9e:('mov','(4,a0),d0'),0x60e4cba3:('mov','d0,(a0)'),
    0x60e4cbaf:('mov','(12,a0),d0'),0x60e4cbb4:('mov','d0,(a0)'),
    0x60e4cbc0:('mov','(20,a0),a0'),0x60e4cbc5:('beq','0x60e4cbe4'),
    0x60e4cbee:('call','0x60dd5146,[d2,a2,a3],16'),0x60e4cbf5:('mov','a0,(a3)'),
    0x60e4cc27:('mov','(a3),d0'),0x60e4cc28:('mov','d0,(a0)'),
    0x60e4cc2b:('movhu','d0,(4,a0)'),0x60e4cc35:('call','0x60df249e,[d2,a2],12'),
    0x60e4cc3c:('mov','(16,sp),a1'),0x60e4cc40:('mov','a0,(a1)'),
    0x60e4cc42:('beq','0x60e4cc4f'),0x60e4cc49:('mov','(a0),a1'),
    0x60e4cc4b:('mov','(a1),a1'),0x60e4cc4d:('calls','(a1)'),
    0x60e4cc4f:('mov','a3,a0'),0x60e4cc50:('ret','[d3,a2,a3],52'),
    0x60e260e6:('mov','100,d0'),0x60e260f1:('call','0x60a4ec03,[],4'),
    0x60e26100:('call','0x60e26108,[d2,a2],16'),
    0x60e2611f:('mov',str(0x6118957c)+',d0'),0x60e26125:('mov','d0,(a2)'),
    0x60e26127:('call','0x60e26188,[d2,a2],16'),0x60e2612c:('mov','a2,a0'),
    0x60e261c5:('mov','1,d0'),0x60e261c9:('call','0x60dd518e,[d2,d3,a2],16'),
    0x60e261d0:('mov','a0,(76,a2)'),0x60e261d4:('call','0x60e266a9,[d2,d3,a2,a3],28'),
    0x60e26a3d:('movm','[a2,a3],(sp)'),0x60e26a3f:('add','-4,sp'),
    0x60e26a42:('mov','a0,a3'),0x60e26a43:('mov','408,d0'),
    0x60e26a46:('call','0x60a4ec03,[],4'),0x60e26a51:('beq','0x60e26a5a'),
    0x60e26a53:('mov','a3,a1'),0x60e26a55:('call','0x60e26a5d,[a2,a3],12'),
    0x60e26a5d:('mov','a1,a3'),0x60e26a66:('mov',str(0x61189ba8)+',d0'),
    0x60e26a6c:('mov','d0,(a2)'),0x60e26a6d:('mov','(a3),d0'),
    0x60e26a6f:('mov','d0,(384,a2)'),0x60e26a78:('mov','a2,a0'),
    0x60e26a7c:('movm','[a2],(sp)'),0x60e26a7e:('add','-4,sp'),
    0x60e26a89:('call','0x60e9ec14,[],0'),0x60e26a91:('call','0x60df2474,[],4'),
    0x60e26a98:('mov','0,a0'),0x60e26a9a:('ret','[a2],8'),
    0x60e5db01:('movm','[a2],(sp)'),0x60e5db03:('add','-4,sp'),
    0x60e5db06:('mov','(0x61fc436c),a2'),0x60e5db15:('call','0x60e4ce26,[a2,a3],12'),
    0x60e5db1d:('call','0x60a4ec17,[],4'),0x60e5db25:('mov','d0,(0x61fc436c)'),
    0x60e5db2b:('ret','[a2],8'),
    0x60e4ce27:('mov','20,a1'),0x60e4ce30:('mov','(a1),a0'),
    0x60e4ce36:('call','0x60a4ec17,[],4'),
    0x60e4ce42:('mov','(a2),a3'),0x60e4ce4b:('mov','(40,a1),a1'),
    0x60e4ce4e:('calls','(a1)'),0x60e4ce50:('mov','a0,a1'),
    0x60e4ce53:('beq','0x60e4ce5a'),0x60e4ce56:('calls','(a1)'),
    0x60e4ce5b:('call','0x60a4ec17,[],4'),0x60e4ce62:('inc4','a2'),
    0x60e4ce68:('mov','(a2),a2'),0x60e4ce71:('mov','(4,a1),a1'),
    0x60e4ce74:('calls','(a1)'),0x60e4ce76:('mov','a0,a1'),
    0x60e4ce79:('beq','0x60e4ce80'),0x60e4ce7c:('calls','(a1)'),
    0x60e4ce81:('call','0x60a4ec17,[],4'),
    0x60e26130:('movm','[d2,d3,a2,a3],(sp)'),0x60e26132:('add','-12,sp'),
    0x60e26141:('add','76,d0'),0x60e2615a:('mov','(40,a1),a1'),
    0x60e2615d:('calls','(a1)'),0x60e26160:('cmp','0,a0'),
    0x60e26165:('calls','(a1)'),0x60e2616a:('call','0x60a4ec17,[],4'),
    0x60e26176:('cmp','2,d3'),0x60e2617c:('call','0x60dd50d8,[],0'),
    0x60e26183:('mov','0,a0'),0x60e26185:('ret','[d2,d3,a2,a3],28')}
CHECKS=[(0x6119fadc,'<3I',(8,0x6119a31c,429)),
    (0x6119cb3c,'<6I',(463,0x34,0,0x84,0,0)),
    (0x61140354,'<2I',(0x34,0x60e260c7)),(0x6115cafc,'<2I',(0x84,0x60e26a3d)),
    (0x611a3b50,'<I',(0x60e5dae9,)),(0x611a3bc4,'<I',(0x60e5db01,)),
    (0x6118957c+40,'<I',(0x60e26130,)),(0x61189ba8+4,'<I',(0x60e26a7c,))]

def inspect(stock,objdump):
    e=inspect_windows(stock,objdump,WINDOWS,W,CHECKS)
    return dict(scope=__doc__,objdump_version=e['objdump_version'],input_structure=e['input_structure'],
        checked_instructions=e['checked_instructions'],checked_data_rows=len(CHECKS),
        original_entry='0x60e5dae9',original_exit='0x60e5db01',container_global='0x61fc436c',
        allocation_bytes=dict(container=228,parent=100,selector=124,viewer=408),
        container_fields=dict(parent=0,viewer=4,parent_factory=8,viewer_factory=12),
        viewer_parent_field=384,parent_selector_field=76,
        initial_viewer_draw_precedes_global_publication=True,
        original_retirement_order=['argument block deallocator','parent destructor','parent deallocator','viewer destructor',
            'viewer deallocator','container deallocator','clear global'],
        destructor_method_performs_destruction_before_returning_deallocator=True,
        null_returned_deallocator_uses='0x60a4ec17',
        reused_selector_evidence='ui-selector-storage-current.json',
        other_constructors_and_direct_teardown_bypass_closure=False,gui_exclusion_proven=False,
        renderer_ready=False,installed=False,target_executed=False,firmware_built=False,hash_checks_performed=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True)
    a=p.parse_args();print(json.dumps(inspect(a.stock,a.objdump),indent=2))
