#!/usr/bin/env python3
"""Request278 display allocation/publication/bind/old-owner retirement ordering."""
import argparse,json,struct
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
from ep7_prepare_input import BASE
from ep7_ui_resource_origin import inspect_data as inspect_resources

WINDOWS=[(0x60cff6ef,0x60cff6fc),(0x60d37b53,0x60d37bc2),
    (0x60d389ee,0x60d38a02),(0x60d38a14,0x60d38a1d),
    (0x60d38a36,0x60d38a9b),(0x60d38ad2,0x60d38b6c),
    (0x60cffbe0,0x60cffbfe)]
W={
    0x60cff6ef:('mov','d1,d0'),0x60cff6f0:('mov','(a0),a1'),
    0x60cff6f2:('mov','(784,a1),a1'),0x60cff6f6:('calls','(a1)'),
    0x60d37b53:('movm','[d2,d3,a2,a3],(sp)'),0x60d37b55:('add','-48,sp'),
    0x60d37b58:('mov','a0,(8,sp)'),0x60d37b5a:('mov','d0,d3'),
    0x60d37b5d:('add','2032,d0'),0x60d37b6a:('movbu','(a0),d1'),
    0x60d37b6e:('beq','0x60d37b73'),0x60d37b70:('jmp','0x60d38a49'),
    0x60d37b73:('mov','1,d0'),0x60d37b75:('movbu','d0,(a0)'),
    0x60d37b7b:('add','1378,a2'),0x60d37b80:('movbu','(a2),d0'),
    0x60d37b84:('bne','0x60d37b9a'),0x60d37b88:('mov','6,d0'),
    0x60d37b8a:('mov','a3,d1'),0x60d37b8c:('extbu','d1'),
    0x60d37b8d:('call','0x60cfe586,[],0'),0x60d37b96:('movbu','d0,(a2)'),
    0x60d37b9c:('cmp','2,a3'),0x60d37b9f:('cmp','2,a3'),
    0x60d37ba1:('bne','0x60d37ba7'),0x60d37ba4:('jmp','0x60d38a45'),
    0x60d37bae:('cmp','280,d3'),0x60d37bb7:('asl2','d3'),
    0x60d37bb8:('mov',str(0x60fa9e04)+',a0'),0x60d37bbe:('mov','(d3,a0),a0'),
    0x60d37bc0:('jmp','(a0)'),0x60d389ee:('call','0x60d3379b,[],0'),
    0x60d389f3:('mov','a0,d1'),0x60d389f7:('mov','24849,d0'),
    0x60d389fa:('mov',str(0x60fa8cf4)+',a1'),0x60d38a00:('bra','0x60d38a14'),
    0x60d38a14:('call','0x60d337b2,[d2,a2,a3],24'),0x60d38a19:('mov','a0,d2'),
    0x60d38a36:('cmp','0,d2'),0x60d38a38:('bne','0x60d38a4d'),
    0x60d38a49:('clr','d0'),0x60d38a4a:('ret','[d2,d3,a2,a3],64'),
    0x60d38a5c:('mov','d2,a0'),0x60d38a5e:('mov','a3,d1'),
    0x60d38a61:('mov','6,d0'),0x60d38a65:('mov','(244,a1),a1'),
    0x60d38a69:('calls','(a1)'),0x60d38a6b:('mov','(8,sp),a0'),
    0x60d38a6d:('mov','d2,a1'),0x60d38a6f:('call','0x60cffbe0,[a2],4'),
    0x60d38a76:('mov','(8,sp),a1'),0x60d38a78:('mov','a0,a3'),
    0x60d38a79:('mov','d2,a0'),0x60d38a7d:('mov','(148,a2),a2'),
    0x60d38a81:('calls','(a2)'),0x60d38a85:('mov','d2,a0'),
    0x60d38a8e:('mov','(364,a2),a2'),0x60d38a92:('calls','(a2)'),
    0x60d38add:('mov','(248,a2),a2'),0x60d38ae1:('calls','(a2)'),
    0x60d38ae3:('call','0x60d3379b,[],0'),0x60d38ae8:('movbu','(16,sp),d0'),
    0x60d38aeb:('movbu','(17,sp),d1'),0x60d38af0:('mov','(244,a1),a1'),
    0x60d38af4:('calls','(a1)'),0x60d38af6:('mov','a3,a0'),
    0x60d38af9:('mov','(368,a1),a1'),0x60d38afd:('calls','(a1)'),
    0x60d38aff:('mov','a3,a0'),0x60d38b02:('mov','(152,a1),a1'),
    0x60d38b06:('calls','(a1)'),0x60d38b0c:('mov','a3,a0'),
    0x60d38b0f:('mov','(a1),a1'),0x60d38b11:('calls','(a1)'),
    0x60d38b13:('mov','a0,a1'),0x60d38b14:('mov','a3,a0'),
    0x60d38b15:('calls','(a1)'),0x60d38b17:('mov','(8,sp),a0'),
    0x60d38b19:('mov','d2,a1'),0x60d38b1b:('call','0x60cffbe0,[a2],4'),
    0x60d38b25:('mov','(8,sp),a0'),0x60d38b28:('add','1378,a0'),
    0x60d38b2c:('movbu','d1,(d0,a0)'),0x60d38b54:('mov','d2,a0'),
    0x60d38b56:('mov','1,d0'),0x60d38b5a:('mov','(76,a1),a1'),
    0x60d38b5d:('calls','(a1)'),0x60d38b5f:('mov','(12,sp),a0'),
    0x60d38b61:('clr','d0'),0x60d38b62:('movbu','d0,(a0)'),
    0x60d38b64:('mov','1,d0'),0x60d38b66:('ret','[d2,d3,a2,a3],64'),
    0x60cffbe0:('mov','416,a2'),0x60cffbe3:('add','a0,a2'),
    0x60cffbe5:('mov','(a2),d1'),0x60cffbe6:('mov','a1,(a2)'),
    0x60cffbf2:('mov','d1,a0'),0x60cffbf4:('retf','[a2],4'),
    0x60cffbf7:('mov','(416,a0),a0'),0x60cffbfb:('retf','[],0')}
CHECKS=[(0x60faaab4+784,'<I',(0x60d37b53,)),
    (0x60fa9e04+278*4,'<I',(0x60d389ee,)),
    (0x60fa8cf4,'<HHII',(0x6111,0x112,0x60fa5dd8,7))]

def inspect(stock,objdump):
    resource={}
    def examine(data):
        rows=inspect_resources(data)['text_descriptors']
        source=next(row for row in rows if row['table_index']==53)
        if source['descriptor']!='0x61032ea8' or source['layout_pointer']!='0x61031b84':
            raise ValueError('selected text source moved')
        layouts=struct.unpack_from('<8h',data,0x61031b84-BASE)
        if layouts!=(20,435,600,40,20,435,680,40):raise ValueError('selected rectangles changed')
        resource.update(selected_text_source=source,
            native_resource_extent=112,descriptor_extent=94,padded_descriptor_extent=96,
            owned_layout_offset=96,owned_layout_bytes=16,changed_descriptor_offsets=[2,3,4,5,6,7],
            candidate_id='0x7e10',stock_navigation_pointer_preserved='0x61030a5c',
            link_data_symbols={'_ep7_stock_hl_text_descriptor_unresolved':'0x61032ea8',
                '_ep7_stock_hl_text_layouts_unresolved':'0x61031b84'})
    e=inspect_windows(stock,objdump,WINDOWS,W,CHECKS,observe_data=examine)
    return dict(scope=__doc__,objdump_version=e['objdump_version'],input_structure=e['input_structure'],
        checked_instructions=e['checked_instructions'],checked_data_rows=len(CHECKS),**resource,
        display_request=278,owner_factory_type='0x6111',owner_descriptor_id='0x112',
        screen_manager='0x60d37b53',screen_manager_self_frame=64,service_vtable_offset=784,
        busy_byte_offset=2032,busy_byte_is_not_a_cross_task_lock=True,
        allocation_context_family=6,allocation_context_slot_count=2,occupied_bytes_offset=1378,
        current_owner_field_in_service=416,new_owner_live_register='d2',old_owner_live_register='a3',
        order=['factory','publish new owner','bind/populate new owner','initial draw',
            'old owner cleanup','old owner destructor and free','restore new owner',
            'release old allocator slot','visibility','clear busy and return 1'],
        capture_before_old_owner_retirement_requires_distinct_records=True,
        proposed_capture='after full request278 manager return1, with pre-change revocation and teardown hooks',
        fresh_allocation_and_bind_status_not_individually_checked_by_stock_manager=True,
        complete_native_owner_provider_implemented=False,manager_wrapper_or_teardown_hook_installed=False,
        text_layout_visual_acceptance=False,hash_checks_performed=False,firmware_modified=False,
        target_executed=False,renderer_ready=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True)
    args=p.parse_args();print(json.dumps(inspect(args.stock,args.objdump),indent=2))
