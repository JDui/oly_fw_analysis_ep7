#!/usr/bin/env python3
"""Capture source bridge seams, pool-release pointer and direct callee stack slots; no hashes."""
import argparse,json,re
from pathlib import Path
from ep7_async_aliases import inspect as inspect_windows
from ep7_capture_envelope import W as ENVELOPE_W,WINDOWS as ENVELOPE_WINDOWS,CHECKS,ROOT
from ep7_lifecycle_inventory import inspect as inspect_inventory
FULL=[(0x602a7ea0,0x602a8877),(0x602a8dbd,0x602a91ee)]
WINDOWS=[(a,b) for a,b in ENVELOPE_WINDOWS if not any(start<=a and b<=end for start,end in FULL)]+FULL+[
    (0x6029b9d1,0x6029ba1e),(0x6029be33,0x6029be6c),
    (0x60289c5e,0x60289c63),(0x60289d02,0x60289d07)]
W=dict(ENVELOPE_W)
W.update({
    0x6029b9d1:('cmp','1,d0'),0x6029b9d5:('cmp','26,d0'),0x6029b9d7:('bcc','0x6029b9ec'),
    0x6029b9df:('add','1646514552,a0'),0x6029b9e5:('movhu','(a0),d1'),
    0x6029b9e7:('btst','4,d1'),0x6029b9ea:('bne','0x6029ba18'),
    0x6029ba14:('mov','0,a0'),0x6029ba18:('mov','(12,a0),a0'),0x6029ba1b:('ret','[],24'),
    0x6029be36:('mov','d0,a2'),0x6029be38:('add','1646514552,a2'),
    0x6029be3e:('movhu','(a2),d0'),0x6029be40:('btst','4,d0'),0x6029be43:('beq','0x6029be7f'),
    0x6029be45:('mov','(12,a2),d0'),0x6029be48:('mov','27078,a0'),
    0x6029be53:('call','0x603db89e,[],4'),0x6029be5a:('movhu','(16,a2),d0'),
    0x6029be5d:('call','0x603db89e,[],4'),0x6029be64:('movhu','(a2),d0'),
    0x6029be66:('and','65531,d0'),0x6029be6a:('movhu','d0,(a2)'),
    0x602a857e:('mov','24053,a2'),0x602a8581:('add','d3,a2'),0x602a8583:('movbu','d0,(a2)'),
    0x602a85be:('mov','d3,a0'),0x602a85c0:('movbu','d0,(24083,a0)'),
    0x602a8dbd:('mov','a0,(24,sp)'),0x602a8dc7:('mov','d0,(28,sp)'),
    0x602a8dc9:('mov','(a1),d0'),0x602a8dca:('call','0x6029b9d1,[],24'),
    0x602a8dd1:('mov','a0,(20,sp)'),
    0x60289c5e:('call','0x6028a882,[d2,d3,a2,a3],32'),
    0x60289d02:('call','0x6028a882,[d2,d3,a2,a3],32'),
})

def inspect(stock,objdump):
    inspect_inventory()
    manifest=json.loads((ROOT/'research/ep7/lifecycle-hook-inventory.json').read_text())
    frees=[int(r['address'],16) for r in manifest['free_sites'] if r['object_kind']=='node']
    windows=WINDOWS+[(a,a+7) for a in frees];w=dict(W)
    w.update({a:('call','0x60022732,[],4') for a in frees});stack={}
    def observe(start,stop,asm):
        expected={0x602a3116:([4,8,12,16],28),0x602a7ea0:([],20),0x602a8dbd:([4,8,12,16,20,24,28],48)}
        if start not in expected:return
        slots=sorted({int(v) for v in re.findall(r'\((-?\d+),sp\)',asm)})
        if slots!=expected[start][0] or re.search(r'\b(?:add|sub)\s+[^\n]*,sp',asm):
            raise ValueError('native callee direct frame access changed')
        stack[hex(start)]=dict(direct_sp_offsets=slots,native_frame_bytes=expected[start][1],
            direct_incoming_stack_argument_seen=False,transitive_caller_stack_access_proved=False)
    e=inspect_windows(stock,objdump,windows,w,CHECKS,observe)
    return dict(scope=__doc__,objdump_version=e['objdump_version'],input_structure=e['input_structure'],
        checked_instructions=e['checked_instructions'],checked_task_rows=1,native_callee_stack_views=stack,
        fresh_call='0x602a31c7',sample_call='0x602a31ea',finish_call='0x602a31f7',
        initialization_inline='0x602897d7',initialization_continue='0x602897dd',
        state_service_calls=['0x60289c5e','0x60289d02'],node_free_calls=[hex(a) for a in frees],
        capture_release_call='0x6029be5d',capture_release_original='0x603db89e',
        capture_release_row_register='a2',capture_pointer_offset=12,pool_handle_offset=16,
        reserved_capture_revoked_before_pool_reuse=True,release_flag_clear_is_later=True,
        original_lookup='0x6029b9d1',lookup_result='a0',lookup_frame=24,
        profile_byte_offsets=[24053,24083],udf_index_opcode_emulated=False,
        all_indirect_aliases_or_other_release_paths_qualified=False,controller_exclusion_proved=False,
        source_adapter_installed=False,full_task_stack_budget_proved=False,
        hash_checks_performed=False,firmware_modified=False,target_executed=False,flash_ready=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True)
    args=p.parse_args();print(json.dumps(inspect(args.stock,args.objdump),indent=2))
