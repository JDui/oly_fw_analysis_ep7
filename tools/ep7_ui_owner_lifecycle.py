#!/usr/bin/env python3
"""Display-owner population/cleanup, empty navigation tables and shared lookup cursor."""
import argparse,json,struct
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
from ep7_prepare_input import BASE
from ep7_ui_resource_origin import inspect_data as inspect_resources

WINDOWS=[(0x60cfe528,0x60cfe534),(0x60d037a8,0x60d03831),
    (0x60d02439,0x60d02472),(0x60d02cc2,0x60d02d14),
    (0x60d028f9,0x60d02922),(0x60d02af7,0x60d02b06),
    (0x60d7ace2,0x60d7acf0),(0x60d02bbd,0x60d02be6),
    (0x60d42dc1,0x60d42dcd),(0x60d02c64,0x60d02cc2),
    (0x60d7ab79,0x60d7ab8c),(0x60d42c67,0x60d42c77),
    (0x60d0297c,0x60d02995),(0x60d023b2,0x60d023c3),
    (0x60d023df,0x60d023e8),(0x60d0230c,0x60d02314),
    (0x60cfef5a,0x60cfef7b),(0x60d37a6f,0x60d37aa8)]
W={
    0x60cfe528:('mov','a1,(24,a0)'),0x60cfe52b:('retf','[],0'),
    0x60cfe52e:('mov','(24,a0),a0'),0x60cfe531:('retf','[],0'),
    0x60d037b4:('add','120,d0'),0x60d037ba:('mov','(a0),d0'),
    0x60d037bd:('beq','0x60d0382d'),0x60d037bf:('mov','d0,a0'),
    0x60d037c1:('mov','(a0),a1'),0x60d037c3:('mov','(136,a1),a1'),
    0x60d037c7:('calls','(a1)'),0x60d037cd:('beq','0x60d0382d'),
    0x60d037cf:('movhu','(a0),d0'),0x60d037d1:('clr','d2'),
    0x60d037d3:('cmp','d2,d0'),0x60d037d4:('ble','0x60d0382d'),
    0x60d037f9:('movhu','(4,a0),d0'),0x60d037fc:('mov','(12,sp),a0'),
    0x60d03800:('mov','(436,a1),a1'),0x60d03804:('calls','(a1)'),
    0x60d0380d:('mov','a2,(a0)'),0x60d0380f:('call','0x60d3379b,[],0'),
    0x60d03817:('mov','(a0),a2'),0x60d03819:('mov','(580,a2),a2'),
    0x60d0381d:('calls','(a2)'),0x60d0382d:('clr','d0'),
    0x60d0382e:('ret','[d2,d3,a2,a3],40'),
    0x60d02439:('mov','a0,a2'),0x60d0243a:('inc4','a0'),
    0x60d0243b:('call','0x60d02363,[],4'),0x60d02440:('mov','a0,(16,a2)'),
    0x60d02454:('mov','a1,d1'),0x60d02456:('mov','16,a2'),
    0x60d02458:('add','a0,a2'),0x60d0245a:('mov','(a2),d0'),
    0x60d0245f:('call','0x60d0237b,[],4'),0x60d02464:('mov','a0,(a2)'),
    0x60d02cc2:('movm','[d2,d3,a2,a3],(sp)'),0x60d02cc4:('add','-8,sp'),
    0x60d02cc7:('mov','d0,d2'),0x60d02ccd:('mov','(440,a1),a1'),
    0x60d02cd1:('calls','(a1)'),0x60d02cd3:('mov','a0,a3'),
    0x60d02cd4:('call','0x60d02439,[a2],8'),0x60d02cdc:('beq','0x60d02d0f'),
    0x60d02ce6:('call','0x60d02454,[a2],8'),0x60d02cee:('bne','0x60d02d0f'),
    0x60d02cf0:('exthu','d2'),0x60d02cf1:('mov','(4,sp),a0'),
    0x60d02cf5:('mov','(8,a1),a1'),0x60d02cf8:('calls','(a1)'),
    0x60d02cfa:('exthu','d0'),0x60d02cfb:('cmp','d0,d2'),
    0x60d02cfc:('bne','0x60d02d02'),0x60d02cfe:('mov','(4,sp),a0'),
    0x60d02d05:('call','0x60d02454,[a2],8'),0x60d02d0d:('beq','0x60d02cf1'),
    0x60d02d0f:('mov','0,a0'),0x60d02d11:('ret','[d2,d3,a2,a3],24'),
    0x60d028f9:('call','0x60cfd747,[a2],8'),0x60d02906:('mov','92,a0'),
    0x60d02908:('add','a3,a0'),0x60d0290a:('call','0x60d0239e,[a2],8'),
    0x60d02af7:('mov','d2,a0'),0x60d02afb:('mov','(424,a1),a1'),
    0x60d02aff:('calls','(a1)'),0x60d02b01:('exth','d0'),
    0x60d02b04:('beq','0x60d02b2f'),0x60d7ace4:('cmp','58,d0'),
    0x60d7ace6:('bcc','0x60d7aceb'),0x60d7ace8:('jmp','0x60d7ac12'),
    0x60d7aceb:('mov','1,d0'),0x60d7aced:('ret','[d2,d3,a2,a3],48'),
    0x60d02bbd:('mov','a0,a3'),0x60d02bc7:('mov','(432,a1),a1'),
    0x60d02bcb:('calls','(a1)'),0x60d42dc1:('mov','(8,sp),a0'),
    0x60d42dc3:('call','0x60d02c03,[d2,d3,a2,a3],32'),
    0x60d02c64:('mov','(8,sp),a0'),0x60d02c6c:('mov','(248,a2),a2'),
    0x60d02c70:('calls','(a2)'),0x60d02c72:('call','0x60d3379b,[],0'),
    0x60d02c79:('movbu','(12,sp),d0'),0x60d02c7c:('movbu','(13,sp),d1'),
    0x60d02c81:('mov','(244,a1),a1'),0x60d02c85:('calls','(a1)'),
    0x60d02c8b:('mov','(368,a1),a1'),0x60d02c8f:('calls','(a1)'),
    0x60d02c95:('mov','(152,a1),a1'),0x60d02c99:('calls','(a1)'),
    0x60d02ca4:('mov','(a1),a1'),0x60d02ca6:('calls','(a1)'),
    0x60d02ca8:('mov','a0,a1'),0x60d02ca9:('mov','a2,a0'),
    0x60d02caa:('calls','(a1)'),0x60d02caf:('call','0x60d02454,[a2],8'),
    0x60d02cb7:('beq','0x60d02c64'),0x60d02cba:('call','0x60d023df,[],4'),
    0x60d7ab7c:('call','0x60d42c67,[],4'),0x60d7ab83:('mov',str(0x60cfe5c9)+',a0'),
    0x60d42c67:('call','0x60d0297c,[a2],8'),0x60d0297d:('mov','92,a0'),
    0x60d0297f:('add','a2,a0'),0x60d02981:('call','0x60d023b2,[],4'),
    0x60d02987:('call','0x60cfd791,[],0'),0x60d023b9:('call','0x60d023df,[],4'),
    0x60d023df:('inc4','a0'),0x60d023e0:('call','0x60d0230c,[],4'),
    0x60d0230c:('call','0x60cfef5a,[a2,a3],12'),0x60cfef5a:('mov','a0,a3'),
    0x60cfef5b:('mov','(a3),a2'),0x60cfef5e:('beq','0x60cfef72'),
    0x60cfef60:('mov','(a2),a2'),0x60cfef62:('mov','5,d0'),
    0x60cfef64:('mov','(4,a2),a0'),0x60cfef67:('clr','d1'),
    0x60cfef68:('call','0x60d109db,[],4'),0x60cfef70:('bne','0x60cfef60'),
    0x60cfef73:('call','0x60cfef4e,[],0'),0x60cfef78:('ret','[a2,a3],12'),
    0x60d37a6f:('mov','1360,d0'),0x60d37a72:('call','0x60cfe5a0,[d2,a2],16'),
    0x60d37a7e:('call','0x60d7ab3f,[a2],8'),0x60d37a9e:('call','0x60d02a61,[a2,a3],12')}
CHECKS=[(0x60fa9754,'<2I',(0x6111,0x60d37a6f))]+[
    (table+offset,'<I',(target,)) for table,offset,target in [
    (0x60faec7c,132,0x60cfe528),(0x60faec7c,136,0x60cfe52e),
    (0x61032f10,0,0x60d7ab79),(0x61032f10,148,0x60d42d46),
    (0x61032f10,152,0x60d43d4b),(0x61032f10,208,0x60d037a8),
    (0x61032f10,424,0x60d7abf6),(0x61032f10,432,0x60d42d69),
    (0x61032f10,436,0x60d02cc2),(0x61032f10,440,0x60d037a3),
    (0x60faaab4,580,0x60d0107d)]]

def inspect(stock,objdump):
    data_report={}
    def examine(data):
        resource=inspect_resources(data)
        pointers=struct.unpack_from('<58I',data,0x6024f330-BASE)
        ids=[struct.unpack_from('<H',data,pointer+2-BASE)[0] for pointer in pointers[1:]]
        candidate=0x7e10
        if candidate in ids:raise ValueError('candidate ID collides with stock owner resources')
        data_report.update(stock_owner_factory_type='0x6111',stock_owner_allocation_bytes=1360,
            stock_immediate_child_ids=ids,proposed_private_text_id=hex(candidate),
            proposed_id_absent_from_stock_descriptors=True,runtime_id_availability_proven=False,
            empty_navigation_resources=[dict(descriptor=x['descriptor'],table=x['opaque12_pointer'],
                count=0,empty_branch='0x60d0382d') for x in resource['text_descriptors']])
    e=inspect_windows(stock,objdump,WINDOWS,W,CHECKS,observe_data=examine)
    return dict(scope=__doc__,objdump_version=e['objdump_version'],input_structure=e['input_structure'],
        checked_instructions=e['checked_instructions'],checked_data_rows=len(CHECKS),**data_report,
        object_navigation_pointer_offset=24,navigation_accessor_vtable_offset=136,
        navigation_consumer='0x60d037a8',empty_navigation_count_skips_entry_access=True,
        arbitrary_navigation_table_or_null_replacement_qualified=False,
        nonempty_branch_decoder_gaps=e['unknown_instruction_addresses'],
        child_find_entry='0x60d02cc2',child_find_native_self_frame=24,
        child_list_offset=92,shared_iterator_in_list=16,shared_iterator_in_owner=108,
        native_lookup_mutates_iterator=True,lookup_is_recursive=False,
        child_population_callback='0x60d7abf6',population_called_by_parent_bind='0x60d02aff',
        population_return_one_is_not_per_child_allocation_success_proof=True,
        bulk_child_cleanup_entry='0x60d02c03',bulk_cleanup_child_vtable_order=[368,152,0],
        destructor_only_releases_list_nodes_not_owned_children=True,
        revoke_must_precede_bulk_cleanup_and_destructor=True,
        installed_owner_capture_and_revoke_hooks=False,gui_serialization_proven=False,
        hash_checks_performed=False,firmware_modified=False,target_executed=False,renderer_ready=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True)
    args=p.parse_args();print(json.dumps(inspect(args.stock,args.objdump),indent=2))
