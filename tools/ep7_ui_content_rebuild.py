#!/usr/bin/env python3
"""Native MVC rebuild CALLs, destructive default branch and owned-content base ABI."""
import argparse,json,struct
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
from ep7_prepare_input import BASE

WINDOWS=[(0x60e261d0,0x60e261dc),(0x60e261f0,0x60e2622f),
    (0x60e266a9,0x60e26789),(0x60e26270,0x60e2627f),
    (0x60e26697,0x60e266a9),(0x60e2698a,0x60e269f9),(0x60de1550,0x60de157e),
    (0x60dd5083,0x60dd50ab),(0x60dd50d8,0x60dd50e1),(0x60dd50f5,0x60dd50fa),
    (0x60a4ec03,0x60a4ec2b)]
W={
    0x60e261d0:('mov','a0,(76,a2)'),0x60e261d3:('mov','a2,a0'),
    0x60e261d4:('call','0x60e266a9,[d2,d3,a2,a3],28'),
    0x60e261f0:('movm','[d2,a2],(sp)'),0x60e261f2:('add','-4,sp'),
    0x60e261fd:('calls','(a1)'),0x60e261ff:('mov','d0,d2'),0x60e26200:('mov','a2,a0'),
    0x60e26201:('call','0x60e266a9,[d2,d3,a2,a3],28'),
    0x60e26206:('mov','d2,d0'),0x60e26207:('ret','[d2,a2],12'),
    0x60e26215:('movm','[d2,a2],(sp)'),0x60e26217:('add','-4,sp'),
    0x60e26222:('calls','(a1)'),0x60e26224:('mov','d0,d2'),0x60e26225:('mov','a2,a0'),
    0x60e26226:('call','0x60e266a9,[d2,d3,a2,a3],28'),
    0x60e2622b:('mov','d2,d0'),0x60e2622c:('ret','[d2,a2],12'),
    0x60e26993:('mov','76,a2'),0x60e26995:('add','a3,a2'),
    0x60e2699f:('calls','(a1)'),0x60e269a1:('movhu','(22,sp),d1'),
    0x60e269c3:('calls','(a1)'),0x60e269ea:('calls','(a1)'),
    0x60e269ef:('mov','a3,a0'),0x60e269f0:('call','0x60e266a9,[d2,d3,a2,a3],28'),
    0x60e269f5:('mov','1,d3'),
    0x60e266a9:('mov','a0,d3'),0x60e266ab:('clr','d0'),
    0x60e266ac:('mov','d0,(4,sp)'),0x60e266ae:('mov','d0,(8,sp)'),
    0x60e266b0:('mov','76,d2'),0x60e266b2:('add','d3,d2'),
    0x60e266b3:('mov','d2,a3'),0x60e266b5:('inc4','a3'),
    0x60e266bb:('mov','(a3),a2'),0x60e266c1:('mov','a2,a0'),
    0x60e266c2:('mov','(a0),a1'),0x60e266c4:('mov','(40,a1),a1'),
    0x60e266c7:('calls','(a1)'),0x60e266c9:('mov','a0,a1'),
    0x60e266cc:('beq','0x60e266d3'),0x60e266ce:('mov','a2,a0'),
    0x60e266cf:('calls','(a1)'),0x60e266d3:('mov','a2,a0'),
    0x60e266d4:('call','0x60a4ec17,[],4'),0x60e266db:('clr','d0'),
    0x60e266dc:('mov','d0,(a3)'),0x60e266e3:('mov','(4,a1),a1'),
    0x60e266e6:('calls','(a1)'),0x60e266e8:('mov','d0,d2'),
    0x60e266fd:('cmp','0,d2'),0x60e266ff:('beq','0x60e26710'),
    0x60e26701:('cmp','1,d2'),0x60e26703:('beq','0x60e2672a'),
    0x60e26705:('cmp','2,d2'),0x60e26707:('beq','0x60e2674e'),
    0x60e26709:('cmp','3,d2'),0x60e2670b:('beq','0x60e26774'),
    0x60e2670d:('ret','[d2,d3,a2,a3],28'),
    0x60e26273:('mov','(80,a0),a0'),0x60e26276:('mov','(a0),a1'),
    0x60e26278:('mov','(a1),a1'),0x60e2627a:('calls','(a1)'),
    0x60e26699:('mov','(80,a0),a0'),0x60e2669e:('mov','(a0),a1'),
    0x60e266a0:('mov','(a1),a1'),0x60e266a2:('calls','(a1)'),
    0x60de155b:('movhu','(86,a2),d1'),0x60de155e:('movhu','d1,(0x61fc26ae)'),
    0x60de1572:('movhu','(86,a2),d1'),0x60de1575:('movhu','d1,(0x61fc26ae)'),
    0x60dd5083:('clr','d0'),0x60dd5084:('mov','d0,(32,a0)'),
    0x60dd5087:('mov','d0,(16,a0)'),0x60dd508a:('mov','d0,(20,a0)'),
    0x60dd508d:('mov','d0,(24,a0)'),0x60dd5090:('movhu','d0,(36,a0)'),
    0x60dd5093:('movhu','d0,(38,a0)'),0x60dd5096:('movhu','d0,(40,a0)'),
    0x60dd5099:('mov','d0,(4,a0)'),0x60dd509c:('mov','d0,(12,a0)'),
    0x60dd509f:('mov','d0,(44,a0)'),0x60dd50a2:('mov','d0,(0x61fc1bbc)'),
    0x60dd50a8:('retf','[],0'),0x60dd50d8:('mov','0,a0'),0x60dd50da:('retf','[],0'),
    0x60dd50dd:('clr','d0'),0x60dd50de:('retf','[],0'),
    0x60dd50f5:('mov','0,a0'),0x60dd50f7:('retf','[],0'),
    0x60a4ec03:('call','0x60022700,[],4'),0x60a4ec0a:('ret','[],4'),
    0x60a4ec17:('call','0x60022732,[],4'),0x60a4ec1e:('ret','[],4')}
CHECKS=[(0x6118957c,'<18I',(0x60dd5250,0x60dd50dd,0x60dd50e1,0x60dd50e9,
    0x60dd50e5,0x60dd50ed,0x60dd50f1,0x60e261dc,0x60dd50fa,0x60dd50fe,
    0x60e26130,0x60e261e5,0x60e2620a,0x60e2622f,0x60e2627f,0x60e262cf,0x60e263a6,0x60e26439))]

def inspect(stock,objdump):
    candidates=[];absolute=[]
    def observe_data(data):
        # Same finite raw CALL candidate method as metadata-allocation research,
        # without invoking its legacy SHA guard. This is not a CFG/indirect proof.
        for opcode,width in [(0xcd,2),(0xdd,4)]:
            start=0
            while (i:=data.find(bytes([opcode]),start))>=0:
                start=i+1
                if i+width+3<=len(data) and BASE+i+int.from_bytes(data[i+1:i+1+width],'little',signed=True)==0x60e266a9:
                    candidates.append(BASE+i)
        start=0;needle=struct.pack('<I',0x60e266a9)
        while (i:=data.find(needle,start))>=0:
            absolute.append(BASE+i);start=i+1
        candidates.sort()
        if candidates!=[0x60e261d4,0x60e26201,0x60e26226,0x60e269f0]:
            raise ValueError('rebuild direct CALL inventory changed: '+repr(candidates))
        if absolute:raise ValueError('unexpected absolute rebuild reference')
    e=inspect_windows(stock,objdump,WINDOWS,W,CHECKS,observe_data=observe_data)
    return dict(scope=__doc__,objdump_version=e['objdump_version'],input_structure=e['input_structure'],
        checked_instructions=e['checked_instructions'],checked_data_rows=len(CHECKS),
        full_main_direct_CALL_candidates=[hex(a) for a in candidates],absolute_entry_word_candidates=absolute,
        raw_reference_scan_is_control_flow_proof=False,all_indirect_or_computed_callers_proven=False,
        original_rebuild='0x60e266a9',caller_allocated_frame_bytes=28,saved_registers=['d2','d3','a2','a3'],
        content_pointer_field=80,selector_index_field=86,remembered_index='0x61fc26ae',
        native_default_category_clears_content_without_replacement=True,forwarders_require_nonnull_content=True,
        scalar_new='0x60a4ec03',scalar_delete='0x60a4ec17',allocator_caller_frames=[4,4],
        base_init='0x60dd5083',base_init_object_last_written_byte=47,base_init_also_clears='0x61fc1bbc',
        base_destructor='0x60dd50d8',base_destructor_return_register='a0',base_destructor_return_value=0,
        private_child_allocation_bytes=56,private_vtable_words=18,
        hl_masks_enabled=False,renderer_ready=False,gui_exclusion_proven=False,
        installed=False,target_executed=False,firmware_built=False,hash_checks_performed=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True)
    a=p.parse_args();print(json.dumps(inspect(a.stock,a.objdump),indent=2))
