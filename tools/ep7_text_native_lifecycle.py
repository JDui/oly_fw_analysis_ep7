#!/usr/bin/env python3
"""Exact list ownership transfer, text parent binding and normal -1 event result."""
import argparse,json
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
ROOT=Path(__file__).resolve().parents[1]
WINDOWS=[(0x60d02beb,0x60d02bfe),(0x60d037a3,0x60d037a8),
    (0x60d023d2,0x60d023dc),(0x60d02314,0x60d0231d),(0x60cfef7b,0x60cfefa4),
    (0x60d0487a,0x60d048d0),(0x60cfe0f8,0x60cfe104),(0x60cfdfe0,0x60cfdfec),
    (0x60d04b66,0x60d04b9e),(0x60d7ab8c,0x60d7abc9),
    (0x60d7acbc,0x60d7acd7),(0x60d37a6f,0x60d37a86),(0x60d7ab3f,0x60d7ab4e),
    (0x60d04c16,0x60d04c1c),(0x60d4ca05,0x60d4ca36)]
W={
    0x60d02beb:('mov','a1,a2'),0x60d02bec:('mov','(a0),a1'),
    0x60d02bee:('mov','(440,a1),a1'),0x60d02bf2:('calls','(a1)'),
    0x60d02bf4:('mov','a2,a1'),0x60d02bf5:('call','0x60d023d2,[],4'),
    0x60d02bfa:('exth','d0'),0x60d02bfb:('ret','[a2],8'),
    0x60d037a3:('add','92,a0'),0x60d037a5:('retf','[],0'),
    0x60d023d2:('inc4','a0'),0x60d023d3:('call','0x60d02314,[],4'),
    0x60d023d8:('exth','d0'),0x60d023d9:('ret','[],4'),
    0x60d02314:('call','0x60cfef7b,[a2,a3],12'),0x60d02319:('exth','d0'),
    0x60d0231a:('ret','[],4'),0x60cfef7b:('mov','a1,a3'),0x60cfef7c:('mov','a0,a2'),
    0x60cfef7d:('mov','5,d0'),0x60cfef7f:('clr','d1'),0x60cfef80:('mov','12,a0'),
    0x60cfef82:('call','0x60d109d1,[],4'),0x60cfef89:('cmp','0,a0'),
    0x60cfef8b:('bne','0x60cfef90'),0x60cfef8d:('clr','d0'),0x60cfef8e:('bra','0x60cfefa1'),
    0x60cfef90:('mov','a2,(a0)'),0x60cfef92:('inc4','a2'),0x60cfef93:('mov','(a2),a1'),
    0x60cfef95:('mov','1,d0'),0x60cfef97:('mov','a1,(4,a0)'),0x60cfef9a:('mov','a0,(a1)'),
    0x60cfef9c:('mov','a0,(a2)'),0x60cfef9e:('mov','a3,(8,a0)'),0x60cfefa1:('ret','[a2,a3],12'),
    0x60d0487a:('movm','[a2,a3],(sp)'),0x60d0487c:('add','-4,sp'),
    0x60d04880:('call','0x60cfe0f8,[a2],8'),0x60d04885:('exth','d0'),
    0x60d04888:('bne','0x60d0488d'),0x60d0488d:('movbu','(88,a3),d0'),
    0x60d04892:('beq','0x60d0489d'),0x60d048a0:('mov','(452,a1),a1'),
    0x60d048a4:('calls','(a1)'),0x60d048a7:('cmp','1,d0'),0x60d048a9:('bne','0x60d048bd'),
    0x60d048bd:('mov','6144,d0'),0x60d048c0:('clr','d1'),0x60d048c1:('mov','0,a1'),
    0x60d048c6:('mov','(564,a2),a2'),0x60d048ca:('calls','(a2)'),
    0x60d048cc:('exth','d0'),0x60d048cd:('ret','[a2,a3],12'),
    0x60cfe0fa:('mov','(124,a2),a2'),0x60cfe0fd:('calls','(a2)'),
    0x60cfe0ff:('mov','1,d0'),0x60cfe101:('ret','[a2],8'),
    0x60cfdfe0:('mov','a1,(20,a0)'),0x60cfdfe3:('retf','[],0'),
    0x60cfdfe6:('mov','(20,a0),a0'),0x60cfdfe9:('retf','[],0'),
    0x60d04c16:('movbu','(68,a0),d0'),0x60d04c19:('retf','[],0'),
    0x60d04b73:('mov','(128,a1),a1'),0x60d04b77:('calls','(a1)'),
    0x60d04b7a:('cmp','0,a3'),0x60d04b7c:('bne','0x60d04b82'),
    0x60d04b85:('mov','(8,a1),a1'),0x60d04b88:('calls','(a1)'),
    0x60d04b8a:('mov','d0,d1'),0x60d04b91:('mov','d2,d0'),0x60d04b92:('mov','a3,a0'),
    0x60d04b95:('mov','(412,a2),a2'),0x60d04b99:('calls','(a2)'),
    0x60d7ab92:('cmp','6399,d0'),0x60d7ab96:('bne','0x60d7abac'),
    0x60d7abac:('cmp','6146,d0'),0x60d7abb0:('bne','0x60d7abc4'),
    0x60d7abc4:('mov','-1,d0'),0x60d7abc6:('ret','[d2],8'),
    0x60d7acbf:('call','0x60d02beb,[a2],8'),0x60d7accc:('mov','(8,sp),a1'),
    0x60d7acd1:('mov','(148,a2),a2'),0x60d7acd5:('calls','(a2)'),
    0x60d37a6f:('mov','1360,d0'),0x60d37a72:('call','0x60cfe5a0,[d2,a2],16'),
    0x60d37a7e:('call','0x60d7ab3f,[a2],8'),0x60d7ab47:('mov',str(0x61032f10)+',d0'),
    0x60d7ab4d:('mov','d0,(a2)'),0x60d4ca05:('movbu','(28,a3),d0'),
    0x60d4ca08:('movbu','(29,a3),d1'),0x60d4ca0d:('call','0x60d109db,[],4'),
    0x60d4ca1e:('movbu','(28,a3),d0'),0x60d4ca21:('movbu','(29,a3),d1'),
    0x60d4ca29:('call','0x60d109d1,[],4')}
CHECKS=[(table+offset,'<I',(target,)) for table,offset,target in [
    (0x61032f10,440,0x60d037a3),(0x61032f10,412,0x60d7ab8c),
    (0x60faec7c,124,0x60cfdfe0),(0x60faec7c,128,0x60cfdfe6),
    (0x60faec7c,148,0x60d0487a),(0x60faec7c,452,0x60d04c16),(0x60faec7c,564,0x60d04b66)]]

def inspect(stock,objdump):
    e=inspect_windows(stock,objdump,WINDOWS,W,CHECKS)
    return dict(scope=__doc__,objdump_version=e['objdump_version'],input_structure=e['input_structure'],
        checked_instructions=e['checked_instructions'],checked_vtable_slots=len(CHECKS),
        owner_vtable='0x61032f10',owner_allocation_bytes=1360,owner_child_list_offset=92,
        list_node_bytes=12,list_allocator_context=[5,0],attach_owns_native_frame=8,
        attach_status_0_leaves_membership_unchanged=True,attach_status_1_transfers_ownership=True,
        text_bind_entry='0x60d0487a',bind_self_frame=12,parent_pointer_offset=20,
        normal_parent_notification_event=6144,normal_parent_notification_result=-1,
        raw_bind_result_is_not_success_boolean=True,parent_pointer_and_expected_event_result_checked=True,
        native_setter_uses_child_allocator_bytes=True,
        concrete_owner_lookup_or_publication_hook_qualified=False,all_parent_teardown_paths_hooked=False,
        hash_checks_performed=False,firmware_modified=False,target_executed=False,renderer_ready=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True)
    args=p.parse_args();print(json.dumps(inspect(args.stock,args.objdump),indent=2))
